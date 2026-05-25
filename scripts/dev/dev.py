import concurrent.futures
import getpass
import os
import re
import subprocess  # nosec B404
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "apps" / "web"

_tty = sys.stdout.isatty()
YELLOW = "\033[93m" if _tty else ""
RED = "\033[91m" if _tty else ""
RESET = "\033[0m" if _tty else ""


def run(cmd, cwd=ROOT):
    """Run shell command safely."""
    print(f"\n>>> {cmd}\n")
    result = subprocess.run(cmd, shell=True, cwd=cwd)  # nosec B602

    if result.returncode != 0:
        print(f"{RED}\nCommand failed: {cmd}{RESET}")

    return result.returncode


def pause():
    input("\nPlease enter to continue...")


def clean_pycache():
    print("\nCleaning __pycache__...")

    for path in ROOT.rglob("__pycache__"):
        if path.is_dir():
            for child in path.rglob("*"):
                try:
                    if child.is_file():
                        child.unlink()
                    else:
                        child.rmdir()
                except Exception:  # nosec B110
                    pass

            try:
                path.rmdir()
            except Exception:  # nosec B110
                pass

    print("Cache cleaned")
    pause()


def run_precommit():
    print("\nRunning pre-commit (all files)...")
    run("pre-commit run --all-files")
    pause()


def manage(cmd):
    return run(f"python manage.py {cmd}", cwd=WEB_DIR)


def _discover_app_labels():
    """Return project app labels from INSTALLED_APPS in settings.py."""
    settings_file = WEB_DIR / "config" / "settings.py"
    text = settings_file.read_text(encoding="utf-8")
    return re.findall(r'"apps\.(\w+)\.apps\.\w+"', text)


def makemigrations():
    labels = _discover_app_labels()
    if labels:
        print(f"\n  Apps: {', '.join(labels)}")
        manage("makemigrations " + " ".join(labels))
    else:
        manage("makemigrations")
    pause()


def migrate():
    manage("migrate")
    pause()


def _install_requirements():
    req_base = ROOT / "requirements" / "base.txt"
    req_dev = ROOT / "requirements" / "dev.txt"
    parts = ["pip", "install"]
    if req_base.exists():
        parts += ["-r", str(req_base)]
    if req_dev.exists():
        parts += ["-r", str(req_dev)]
    if len(parts) == 2:
        return 0
    return run(" ".join(parts))


def runserver():
    print("\nRunning postcss, build-js and requirements in parallel...")

    tasks = {
        "postcss": lambda: run("npm run build:css"),
        "build-js": lambda: run("npm run build:js"),
        "requirements": _install_requirements,
    }

    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fn): name for name, fn in tasks.items()}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            rc = future.result()
            if rc != 0:
                failed.append(name)

    if failed:
        print(f"{RED}\nPre-server tasks failed: {', '.join(failed)}{RESET}")
        pause()
        return

    manage("runserver")


def reset_setup():
    print(f"\n{YELLOW}Resetting setup...{RESET}")
    full_clean = (
        input(f"{YELLOW}Full clean? Also wipes OAuth and SAML records. (y/N): {RESET}")
        .strip()
        .lower()
        == "y"
    )
    reset_script = ROOT / "scripts" / "dev" / "reset.py"
    cmd = f"python {reset_script}"
    if full_clean:
        cmd += " --full-clean"
    run(cmd)
    pause()


# ---------------------------------------------------------------------------
# SQL query runner
# ---------------------------------------------------------------------------


def _load_env_defaults():
    """Parse .env and return a dict of key→value pairs (best-effort)."""
    env_file = WEB_DIR / ".env"
    defaults = {}
    if not env_file.exists():
        return defaults
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            defaults[key.strip()] = val.strip()
    except Exception:  # nosec B110
        pass
    return defaults


def _prompt(label, default=""):
    """Prompt with an optional default shown in brackets."""
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def _print_table(cursor):
    """Pretty-print query results."""
    rows = cursor.fetchall()
    if cursor.description is None:
        return 0
    cols = [d[0] for d in cursor.description]
    str_rows = [[str(v) if v is not None else "NULL" for v in row] for row in rows]
    widths = [
        max(len(c), max((len(r[i]) for r in str_rows), default=0))
        for i, c in enumerate(cols)
    ]
    sep = "-+-".join("-" * w for w in widths)
    header = " | ".join(c.ljust(w) for c, w in zip(cols, widths, strict=False))
    print(header)
    print(sep)
    for row in str_rows:
        print(" | ".join(v.ljust(w) for v, w in zip(row, widths, strict=False)))
    count = len(rows)
    print(f"\n({count} row{'s' if count != 1 else ''})")
    return count


def _run_sql_session(conn, db_label):
    """Interactive SQL REPL against an open connection."""
    print(f"\nConnected to {db_label}.")
    print("Commands: 'exit' to quit | 'tables' to list tables | any SQL statement")

    while True:
        try:
            query = input("\nSQL> ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not query:
            continue

        if query.lower() in ("exit", "quit", "\\q"):
            break

        if query.lower() in ("tables", "\\dt"):
            if "SQLite" in db_label:
                query = (
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
            else:
                query = (
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' ORDER BY table_name"
                )

        try:
            cur = conn.cursor()
            cur.execute(query)
            if cur.description:
                _print_table(cur)
            else:
                conn.commit()
                affected = cur.rowcount if cur.rowcount >= 0 else 0
                print(f"OK  ({affected} row{'s' if affected != 1 else ''} affected)")
        except Exception as exc:
            print(f"Error: {exc}")
            try:
                conn.rollback()
            except Exception:  # nosec B110
                pass

    try:
        conn.close()
    except Exception:  # nosec B110
        pass
    print(f"Disconnected from {db_label}.")
    pause()


def _connect_sqlite():
    default_path = str(WEB_DIR / "db.sqlite3")
    db_path = _prompt("SQLite file path", default_path)

    if not Path(db_path).exists():
        print(f"File not found: {db_path}")
        pause()
        return

    try:
        import sqlite3

        conn = sqlite3.connect(db_path)
        _run_sql_session(conn, f"SQLite ({db_path})")
    except Exception as exc:
        print(f"Connection failed: {exc}")
        pause()


def _connect_postgresql():
    env = _load_env_defaults()

    host = _prompt("Host", env.get("DB_HOST", "127.0.0.1"))
    port = _prompt("Port", env.get("DB_PORT", "5432"))
    db_name = _prompt("Database name", env.get("DB_NAME", "resourceplanner"))
    user = _prompt("User", env.get("DB_USER", "postgres"))
    password = getpass.getpass(
        f"Password [{('*' * 6) if env.get('DB_PASSWORD') else ''}]: "
    ).strip() or env.get("DB_PASSWORD", "")

    try:
        import psycopg2
    except ImportError:
        print("psycopg2 is not installed (add psycopg2-binary to requirements).")
        pause()
        return

    try:
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            dbname=db_name,
            user=user,
            password=password,
            connect_timeout=5,
        )
        conn.autocommit = False
        _run_sql_session(conn, f"PostgreSQL ({user}@{host}:{port}/{db_name})")
    except Exception as exc:
        print(f"Connection failed: {exc}")
        pause()


def sql_query_runner():
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605
        print("=== SQL QUERY RUNNER ===")
        print("1. SQLite")
        print("2. PostgreSQL")
        print("0. Back")

        choice = input("\nSelect database: ").strip()

        if choice == "1":
            _connect_sqlite()
        elif choice == "2":
            _connect_postgresql()
        elif choice == "0":
            return
        else:
            print(f"{YELLOW}Invalid choice{RESET}")
            pause()


# ---------------------------------------------------------------------------
# Menus
# ---------------------------------------------------------------------------


def django_menu():
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605

        print("=== DJANGO MENU ===")
        print("1. Make Migrations")
        print("2. Migrate")
        print("3. Run Server")
        print("4. Reset Setup")
        print("5. SQL Query Runner")
        print("0. Back")

        choice = input("\nSelect: ")

        if choice == "1":
            makemigrations()
        elif choice == "2":
            migrate()
        elif choice == "3":
            runserver()
        elif choice == "4":
            reset_setup()
        elif choice == "5":
            sql_query_runner()
        elif choice == "0":
            return
        else:
            print(f"{YELLOW}Invalid choice{RESET}")
            pause()


def main_menu():
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605

        print("=================================")
        print("        DEV CONTROL PANEL        ")
        print("=================================")
        print("1. Clean Python Cache")
        print("2. Pre-Commit (all files)")
        print("3. Django Tools")
        print("0. Exit")

        choice = input("\nSelect: ")

        if choice == "1":
            clean_pycache()
        elif choice == "2":
            run_precommit()
        elif choice == "3":
            django_menu()
        elif choice == "0":
            sys.exit(0)
        else:
            print(f"{YELLOW}Invalid choice{RESET}")
            pause()


if __name__ == "__main__":
    main_menu()
