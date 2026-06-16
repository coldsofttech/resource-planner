import getpass
import os
from pathlib import Path

from ..constants import RESET, YELLOW
from ..core.env import _load_env_defaults, _prompt
from ..core.shell import pause


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
    from ..constants import WEB_DIR

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
