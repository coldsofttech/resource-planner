import collections
import concurrent.futures
import getpass
import hashlib
import json
import os
import re
import shutil
import subprocess  # nosec B404
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "apps" / "web"
PACKAGES_DIR = ROOT / "packages"
REPORTS_DIR = ROOT / ".pytest-reports"
CACHE_DIR = ROOT / ".dev-cache"
TEST_TRACKER_DIR = ROOT / "tools" / "test-tracker"
TEST_TRACKER_PORT = 8001

_tty = sys.stdout.isatty()
YELLOW = "\033[93m" if _tty else ""
GREEN = "\033[92m" if _tty else ""
RED = "\033[91m" if _tty else ""
RESET = "\033[0m" if _tty else ""


def run(cmd, cwd=ROOT):
    """Run shell command safely."""
    print(f"\n>>> {cmd}\n")
    result = subprocess.run(cmd, shell=True, cwd=cwd)  # nosec B602

    if result.returncode != 0:
        print(f"{RED}\nCommand failed: {cmd}{RESET}")

    return result.returncode


_PYTEST_NO_TESTS = 5  # pytest exit code when no tests are collected


def _run_pytest(cmd: str) -> int:
    """Run a pytest command; exit code 5 (no tests collected) is treated as success."""
    print(f"\n>>> {cmd}\n")
    result = subprocess.run(cmd, shell=True, cwd=ROOT)  # nosec B602
    rc = result.returncode
    if rc == _PYTEST_NO_TESTS:
        print(f"{YELLOW}No tests collected — skipping.{RESET}")
        return 0
    if rc != 0:
        print(f"{RED}\nCommand failed: {cmd}{RESET}")
    return rc


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
    run("git add -A")
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


def _enable_ansi_windows() -> None:
    """Enable VT100 ANSI processing on Windows so escape codes render correctly."""
    if os.name != "nt":
        return
    try:
        import ctypes

        k32 = ctypes.windll.kernel32
        h = k32.GetStdHandle(-11)
        m = ctypes.c_ulong()
        if k32.GetConsoleMode(h, ctypes.byref(m)):
            k32.SetConsoleMode(h, m.value | 0x0004)
    except Exception:  # nosec B110
        pass


def _hash_paths(paths: list[Path]) -> str:
    """Return a SHA-256 hex digest over the sorted contents of the given files."""
    h = hashlib.sha256()
    for p in sorted(paths, key=str):
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


def _needs_run(task_name: str, watch_paths: list[Path]) -> bool:
    """Return True when any watched file changed since the last successful run."""
    cache_file = CACHE_DIR / f"{task_name}.hash"
    if not cache_file.exists():
        return True
    return cache_file.read_text(encoding="utf-8").strip() != _hash_paths(watch_paths)


def _record_run(task_name: str, watch_paths: list[Path]) -> None:
    """Persist the current hash so the next run can skip if nothing changed."""
    CACHE_DIR.mkdir(exist_ok=True)
    (CACHE_DIR / f"{task_name}.hash").write_text(
        _hash_paths(watch_paths), encoding="utf-8"
    )


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mKHJABCDEFGsu]")


def _run_cmd_buffered(cmd: str, buf: "collections.deque[str]", cwd: Path = ROOT) -> int:
    """Run a shell command, streaming each output line into buf. Returns exit code."""
    buf.append(f"$ {cmd}")
    proc = subprocess.Popen(  # nosec B602
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.stdout is not None
    for line in iter(proc.stdout.readline, ""):
        buf.append(_ANSI_RE.sub("", line.rstrip()))
    proc.wait()
    return proc.returncode


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


def _install_requirements_buffered(buf: "collections.deque[str]") -> int:
    """Buffered variant of _install_requirements for the parallel column display."""
    req_base = ROOT / "requirements" / "base.txt"
    req_dev = ROOT / "requirements" / "dev.txt"
    parts = ["pip", "install"]
    if req_base.exists():
        parts += ["-r", str(req_base)]
    if req_dev.exists():
        parts += ["-r", str(req_dev)]
    if len(parts) == 2:
        buf.append("No requirements files found.")
        return 0
    return _run_cmd_buffered(" ".join(parts), buf)


_DOCKER_CONTAINER_PG = "resource-planner-dev-pg"
_DOCKER_CONTAINER_MAILPIT = "resource-planner-dev-mailpit"
_DOCKER_CONTAINER_LOCALSTACK = "resource-planner-dev-localstack"
_DOCKER_CONTAINER_KEYCLOAK = "resource-planner-dev-keycloak"
_LOCALSTACK_ENDPOINT = "http://localhost:4566"
_KEYCLOAK_REALM = "resource-planner"
_KEYCLOAK_URL = "http://localhost:8080"
_KEYCLOAK_REALM_EXPORT = ROOT / "scripts" / "dev" / "keycloak" / "realm-export.json"


def _generate_realm_export(
    lan_ip: str,
    oauth_client_id: str = "resource-planner-oauth",
    oauth_client_secret: str = "dev-oauth-secret",
    sp_entity_id: str = "http://localhost:8000/sp",
    sp_assertion_url: str = "http://localhost:8000/api/v1/auth/saml/acs/",
) -> None:
    """Regenerate realm-export.json with the current LAN IP and OAuth/SAML config."""
    base_lan = f"http://{lan_ip}:8000"
    realm = {
        "realm": "resource-planner",
        "displayName": "Resource Planner Dev",
        "enabled": True,
        "sslRequired": "external",
        "loginWithEmailAllowed": True,
        "duplicateEmailsAllowed": False,
        "resetPasswordAllowed": True,
        "bruteForceProtected": False,
        "clients": [
            {
                "clientId": oauth_client_id,
                "name": "Resource Planner OAuth",
                "description": "OIDC / OAuth 2.0 client for local dev testing",
                "enabled": True,
                "protocol": "openid-connect",
                "publicClient": False,
                "secret": oauth_client_secret,
                "standardFlowEnabled": True,
                "directAccessGrantsEnabled": False,
                "serviceAccountsEnabled": False,
                "redirectUris": [
                    "http://localhost:8000/*",
                    "http://127.0.0.1:8000/*",
                    "http://resourceplanner.test:8000/*",
                    "http://resourceplanner.local:8000/*",
                    "http://resourceplanner.home:8000/*",
                    f"{base_lan}/*",
                ],
                "webOrigins": [
                    "http://localhost:8000",
                    "http://127.0.0.1:8000",
                    "http://resourceplanner.test:8000",
                    "http://resourceplanner.local:8000",
                    "http://resourceplanner.home:8000",
                    base_lan,
                ],
            },
            {
                "clientId": sp_entity_id,
                "name": "Resource Planner SAML",
                "description": "SAML 2.0 SP for local dev testing",
                "enabled": True,
                "protocol": "saml",
                "fullScopeAllowed": True,
                "attributes": {
                    "saml.authnstatement": "true",
                    "saml.server.signature": "true",
                    "saml.assertion.signature": "true",
                    "saml.encrypt": "false",
                    "saml.client.signature": "false",
                    "saml.force.post.binding": "false",
                    "saml_assertion_consumer_url_post": sp_assertion_url,
                    "saml_name_id_format": (
                        "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
                    ),
                    "saml_force_name_id_format": "true",
                },
                "protocolMappers": [
                    {
                        "name": "email",
                        "protocol": "saml",
                        "protocolMapper": "saml-user-property-mapper",
                        "config": {
                            "attribute.nameformat": "Basic",
                            "user.attribute": "email",
                            "friendly.name": "email",
                            "attribute.name": "email",
                        },
                    },
                    {
                        "name": "first_name",
                        "protocol": "saml",
                        "protocolMapper": "saml-user-property-mapper",
                        "config": {
                            "attribute.nameformat": "Basic",
                            "user.attribute": "firstName",
                            "friendly.name": "first_name",
                            "attribute.name": "first_name",
                        },
                    },
                    {
                        "name": "last_name",
                        "protocol": "saml",
                        "protocolMapper": "saml-user-property-mapper",
                        "config": {
                            "attribute.nameformat": "Basic",
                            "user.attribute": "lastName",
                            "friendly.name": "last_name",
                            "attribute.name": "last_name",
                        },
                    },
                ],
                "redirectUris": [
                    "http://localhost:8000/*",
                    "http://127.0.0.1:8000/*",
                    "http://resourceplanner.test:8000/*",
                    "http://resourceplanner.local:8000/*",
                    "http://resourceplanner.home:8000/*",
                    f"{base_lan}/*",
                ],
            },
        ],
        "users": [
            {
                "username": "sso@example.com",
                "email": "sso@example.com",
                "firstName": "SSO",
                "lastName": "User",
                "enabled": True,
                "emailVerified": True,
                "credentials": [
                    {"type": "password", "value": "Test1234!", "temporary": False}
                ],
            }
        ],
    }
    _KEYCLOAK_REALM_EXPORT.parent.mkdir(parents=True, exist_ok=True)
    _KEYCLOAK_REALM_EXPORT.write_text(json.dumps(realm, indent=2), encoding="utf-8")
    print(f"  Realm export updated  →  LAN: {base_lan}  |  SP: {sp_entity_id}")


# ---------------------------------------------------------------------------
# .env helpers (mirrors pycore.DotEnv without needing the package import)
# ---------------------------------------------------------------------------


def _env_write(key, value):
    """Write or update a single key in apps/web/.env."""
    env_file = WEB_DIR / ".env"
    lines: list[str] = []
    if env_file.exists():
        lines = env_file.read_text(encoding="utf-8").splitlines(keepends=True)
    updated = False
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k, _, _ = stripped.partition("=")
            if k.strip() == key:
                new_lines.append(f"{key}={value}\n")
                updated = True
                continue
        new_lines.append(line)
    if not updated:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(f"{key}={value}\n")
    env_file.write_text("".join(new_lines), encoding="utf-8")


def _env_remove(key):
    """Remove a key from apps/web/.env (no-op if absent)."""
    env_file = WEB_DIR / ".env"
    if not env_file.exists():
        return
    lines = env_file.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines = [
        line
        for line in lines
        if not (
            line.strip()
            and not line.strip().startswith("#")
            and "=" in line
            and line.strip().partition("=")[0].strip() == key
        )
    ]
    env_file.write_text("".join(new_lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Docker config detection
# ---------------------------------------------------------------------------


def _get_postgres_docker_config():
    """Return DB config dict if .env configures PostgreSQL, else None."""
    env = _load_env_defaults()
    if "postgresql" not in env.get("DB_ENGINE", "").lower():
        return None
    return {
        "port": env.get("DB_PORT", "5432"),
        "user": env.get("DB_USER", "postgres"),
        "password": env.get("DB_PASSWORD", ""),
        "db_name": env.get("DB_NAME", "resourceplanner"),
    }


def _read_configs_from_db(codes):
    """Read config_code→value rows from the DB without loading Django."""
    env = _load_env_defaults()
    try:
        if "postgresql" in env.get("DB_ENGINE", "").lower():
            return _read_configs_postgresql(env, codes)
        return _read_configs_sqlite(codes)
    except Exception:  # nosec B110
        return {}


def _read_configs_postgresql(env, codes):
    try:
        import psycopg2
    except ImportError:
        return {}
    try:
        conn = psycopg2.connect(
            host=env.get("DB_HOST", "127.0.0.1"),
            port=int(env.get("DB_PORT", "5432")),
            dbname=env.get("DB_NAME", "resourceplanner"),
            user=env.get("DB_USER", "postgres"),
            password=env.get("DB_PASSWORD", ""),
            connect_timeout=3,
        )
        placeholders = ",".join(["%s"] * len(codes))
        cur = conn.cursor()
        cur.execute(  # nosec B608
            "SELECT config_code, value FROM configurations_configuration"
            f" WHERE config_code IN ({placeholders})",
            list(codes),
        )
        result = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()
        return result
    except Exception:  # nosec B110
        return {}


def _read_configs_sqlite(codes):
    db_path = WEB_DIR / "db.sqlite3"
    if not db_path.exists():
        return {}
    try:
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        placeholders = ",".join(["?"] * len(codes))
        cur = conn.cursor()
        cur.execute(  # nosec B608
            "SELECT config_code, value FROM configurations_configuration"
            f" WHERE config_code IN ({placeholders})",
            list(codes),
        )
        result = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()
        return result
    except Exception:  # nosec B110
        return {}


def _try_fernet_decrypt(value):
    """Decrypt an enc:<ciphertext> DB value using FERNET_KEY from .env."""
    if not value.startswith("enc:"):
        return value
    fernet_key = _load_env_defaults().get("FERNET_KEY", "")
    if not fernet_key:
        return ""
    try:
        from cryptography.fernet import Fernet

        return Fernet(fernet_key.encode()).decrypt(value[4:].encode()).decode()
    except Exception:  # nosec B110
        return ""


def _get_smtp_docker_config():
    """Return Mailpit config dict if the DB has EMAIL_TYPE=smtp, else None."""
    configs = _read_configs_from_db(
        [
            "EMAIL_TYPE",
            "EMAIL_SMTP_PORT",
            "EMAIL_SMTP_AUTH_ENABLED",
            "EMAIL_SMTP_USERNAME",
            "EMAIL_SMTP_PASSWORD",
        ]
    )
    if configs.get("EMAIL_TYPE", "").lower() != "smtp":
        return None

    auth_enabled = configs.get("EMAIL_SMTP_AUTH_ENABLED", "false").lower() == "true"
    username = configs.get("EMAIL_SMTP_USERNAME", "")
    password_raw = configs.get("EMAIL_SMTP_PASSWORD", "")
    password = (
        _try_fernet_decrypt(password_raw) if auth_enabled and password_raw else ""
    )

    return {
        "smtp_port": configs.get("EMAIL_SMTP_PORT", "1025"),
        "auth_enabled": auth_enabled,
        "username": username,
        "password": password,
    }


def _get_localstack_docker_config():
    """Return an empty config dict if the DB has DEPLOYMENT_TYPE=aws, else None."""
    configs = _read_configs_from_db(["DEPLOYMENT_TYPE"])
    if configs.get("DEPLOYMENT_TYPE", "").lower() != "aws":
        return None
    return {}


def _get_keycloak_docker_config():
    """Return an empty config dict if DEV_KEYCLOAK=true in .env, else None."""
    env = _load_env_defaults()
    if env.get("DEV_KEYCLOAK", "").lower() != "true":
        return None
    return {}


# ---------------------------------------------------------------------------
# Docker lifecycle helpers (docker compose)
# ---------------------------------------------------------------------------

_COMPOSE_ENV_FILE = str(WEB_DIR / ".env")


def _docker_available():
    try:
        result = subprocess.run(  # nosec B603 B607
            ["docker", "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _docker_container_status(name):
    """Return 'running', 'stopped', or None if the container does not exist."""
    result = subprocess.run(  # nosec B603 B607
        ["docker", "inspect", "-f", "{{.State.Status}}", name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return "running" if result.stdout.strip() == "running" else "stopped"


def _compose_up_profile(profile, container_name, label, force_recreate: bool = False):
    """Start a docker compose profile's service.

    When force_recreate is False (default): if the container is already running
    it is left untouched and None is returned so the caller knows not to stop it
    on exit.

    When force_recreate is True: the container is always (re)created with the
    current env-file settings. Use this when the caller has just updated config
    (e.g. a port change) and needs the new settings to take effect.

    Returns the profile string when we brought the service up ourselves.
    """
    if not _docker_available():
        print(f"{YELLOW}  Docker not found; skipping {label}.{RESET}")
        return None

    if not force_recreate and _docker_container_status(container_name) == "running":
        print(f"  Container '{container_name}' already running — using it as-is.")
        return None

    print(f"  Starting {label} (compose profile: {profile})...")
    cmd = [
        "docker",
        "compose",
        "--env-file",
        _COMPOSE_ENV_FILE,
        "--profile",
        profile,
        "up",
        "-d",
    ]
    if force_recreate:
        cmd.append("--force-recreate")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)  # nosec B603 B607
    if result.returncode == 0:
        print(f"  {label} started.")
        return profile

    print(f"{RED}  Failed to start {label}: {result.stderr.strip()}{RESET}")
    return None


def _compose_up_profile_buffered(
    profile: str,
    container_name: str,
    label: str,
    buf: "collections.deque[str]",
    force_recreate: bool = False,
) -> int:
    """Buffered docker compose up for the parallel column display."""
    if not _docker_available():
        buf.append("Docker not found.")
        return 1
    if not force_recreate and _docker_container_status(container_name) == "running":
        buf.append("Already running — using as-is.")
        return 0
    buf.append(f"Starting {label}...")
    cmd = [
        "docker",
        "compose",
        "--env-file",
        _COMPOSE_ENV_FILE,
        "--profile",
        profile,
        "up",
        "-d",
    ]
    if force_recreate:
        cmd.append("--force-recreate")
    proc = subprocess.Popen(  # nosec B603
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.stdout is not None
    for line in iter(proc.stdout.readline, ""):
        buf.append(_ANSI_RE.sub("", line.rstrip()))
    proc.wait()
    if proc.returncode == 0:
        buf.append("Started.")
    else:
        buf.append(f"Failed (exit {proc.returncode}).")
    return proc.returncode


def _compose_down_profile(profile, label):
    """Stop and remove a docker compose profile's service."""
    print(f"\nStopping {label} (compose profile: {profile})...")
    subprocess.run(  # nosec B603 B607
        [
            "docker",
            "compose",
            "--env-file",
            _COMPOSE_ENV_FILE,
            "--profile",
            profile,
            "down",
        ],
        capture_output=True,
        cwd=ROOT,
    )
    print(f"  {label} stopped.")


def _run_parallel_columns(tasks: dict) -> dict:
    """
    Run tasks concurrently and display live output in a columnar terminal layout.

    tasks: {name: callable(buf: deque) -> int}
    Returns: {name: exit_code}
    """
    names = list(tasks.keys())
    n = len(names)
    bufs: dict = {nm: collections.deque(maxlen=500) for nm in names}
    status: dict = {nm: "running" for nm in names}
    results: dict = {nm: None for nm in names}
    lock = threading.Lock()

    def _run_one(nm: str) -> None:
        rc = tasks[nm](bufs[nm])
        with lock:
            results[nm] = rc if rc is not None else 0
            status[nm] = "ok" if results[nm] == 0 else "fail"

    if not _tty:
        with concurrent.futures.ThreadPoolExecutor(max_workers=n) as ex:
            futs = [ex.submit(_run_one, nm) for nm in names]
            for f in concurrent.futures.as_completed(futs):
                try:
                    f.result()
                except Exception as exc:
                    print(f"Task error: {exc}")
        for nm in names:
            for line in bufs[nm]:
                print(f"[{nm.upper():<12}] {line}")
        return results

    COL_LINES = 10
    TOTAL_LINES = COL_LINES + 4
    REFRESH = 0.15

    tw = shutil.get_terminal_size((120, 24)).columns
    cw = max(26, (tw - n - 1) // n)

    _BADGE = {"running": "RUNNING", "ok": "  DONE ", "fail": "FAILED "}
    _BADGE_COL = {"running": YELLOW, "ok": GREEN, "fail": RED}

    def _pad(s: str, w: int) -> str:
        s = _ANSI_RE.sub("", s).expandtabs(4)
        return (s[: w - 1] + "~") if len(s) > w else s.ljust(w)

    def _header(nm: str) -> str:
        label = nm.upper()
        badge = _BADGE[status[nm]]
        col = _BADGE_COL[status[nm]]
        inner = cw - 2
        max_label = inner - len(badge) - 1
        if len(label) > max_label:
            label = label[:max_label]
        gap = " " * max(1, inner - len(label) - len(badge))
        return f" {label}{gap}{col}{badge}{RESET} "

    def _sep(left: str, mid: str, right: str, fill: str) -> str:
        seg = fill * cw
        return left + (seg + mid) * (n - 1) + seg + right

    def _frame() -> str:
        rows = [
            _sep("┌", "┬", "┐", "─"),
            "│" + "│".join(_header(nm) for nm in names) + "│",
            _sep("├", "┼", "┤", "─"),
        ]
        for i in range(COL_LINES):
            parts = []
            for nm in names:
                snap = list(bufs[nm])
                idx = len(snap) - COL_LINES + i
                line = snap[idx] if 0 <= idx < len(snap) else ""
                parts.append(" " + _pad(line, cw - 2) + " ")
            rows.append("│" + "│".join(parts) + "│")
        rows.append(_sep("└", "┴", "┘", "─"))
        return "\n".join(rows) + "\n"

    _enable_ansi_windows()
    sys.stdout.write("\n" + _frame())
    sys.stdout.flush()

    stop_ev = threading.Event()

    def _display_loop() -> None:
        while not stop_ev.is_set():
            with lock:
                sys.stdout.write(f"\033[{TOTAL_LINES}A\r" + _frame())
                sys.stdout.flush()
            time.sleep(REFRESH)
        with lock:
            sys.stdout.write(f"\033[{TOTAL_LINES}A\r" + _frame())
            sys.stdout.flush()

    disp = threading.Thread(target=_display_loop, daemon=True)
    disp.start()

    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as ex:
        fut_map = {ex.submit(_run_one, nm): nm for nm in names}
        for f in concurrent.futures.as_completed(fut_map):
            try:
                f.result()
            except Exception as exc:
                nm = fut_map[f]
                with lock:
                    bufs[nm].append(f"Error: {exc}")
                    results[nm] = 1
                    status[nm] = "fail"

    stop_ev.set()
    disp.join()
    print()
    return results


def _print_status_table(columns: "dict[str, tuple[str, list[str]]]") -> None:
    """
    Print a static columnar status table using the same aesthetic
    as _run_parallel_columns.
    """
    if not columns:
        return

    names = list(columns.keys())
    n = len(names)
    _enable_ansi_windows()

    tw = shutil.get_terminal_size((120, 24)).columns
    cw = max(24, (tw - n - 1) // n)

    _STATUS_BADGE = {
        "ok": "  DONE ",
        "fail": "FAILED ",
        "starting": "STARTING",
        "running": "RUNNING",
    }
    _STATUS_COL = {
        "ok": GREEN,
        "fail": RED,
        "starting": YELLOW,
        "running": YELLOW,
    }

    def _pad(s: str, w: int) -> str:
        s = _ANSI_RE.sub("", s).expandtabs(4)
        return (s[: w - 1] + "~") if len(s) > w else s.ljust(w)

    def _header(nm: str) -> str:
        st = columns[nm][0]
        label = nm.upper()
        badge = _STATUS_BADGE.get(st, "       ")
        col = _STATUS_COL.get(st, "")
        inner = cw - 2
        max_label = inner - len(badge) - 1
        if len(label) > max_label:
            label = label[:max_label]
        gap = " " * max(1, inner - len(label) - len(badge))
        return f" {label}{gap}{col}{badge}{RESET} "

    def _sep(left: str, mid: str, right: str, fill: str) -> str:
        seg = fill * cw
        return left + (seg + mid) * (n - 1) + seg + right

    col_lines = max((len(v[1]) for v in columns.values()), default=0)
    col_lines = max(col_lines, 3)

    rows = [
        _sep("┌", "┬", "┐", "─"),
        "│" + "│".join(_header(nm) for nm in names) + "│",
        _sep("├", "┼", "┤", "─"),
    ]
    for i in range(col_lines):
        parts = []
        for nm in names:
            lines = columns[nm][1]
            line = lines[i] if i < len(lines) else ""
            parts.append(" " + _pad(line, cw - 2) + " ")
        rows.append("│" + "│".join(parts) + "│")
    rows.append(_sep("└", "┴", "┘", "─"))

    print("\n" + "\n".join(rows))


# ---------------------------------------------------------------------------
# Tab view TUI
# ---------------------------------------------------------------------------


def _enter_raw_mode() -> object:
    """Put stdin into cbreak mode (raw input, but Ctrl+C still sends SIGINT)."""
    if os.name == "nt":
        return None
    try:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)  # type: ignore[attr-defined]
        tty.setcbreak(fd)  # type: ignore[attr-defined]
        return old
    except Exception:  # nosec B110
        return None


def _exit_raw_mode(old_settings: object) -> None:
    """Restore stdin from cbreak mode."""
    if os.name == "nt" or old_settings is None:
        return
    try:
        import termios

        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)  # type: ignore[attr-defined]
    except Exception:  # nosec B110
        pass


def _read_key_nonblocking() -> "str | None":
    """Return the next keypress without blocking, or None if no key is ready."""
    if os.name == "nt":
        import msvcrt  # nosec B404

        if not msvcrt.kbhit():
            return None
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ext = msvcrt.getwch()
            return {"K": "left", "M": "right", "H": "up", "P": "down"}.get(ext)
        return ch
    else:
        import select

        if not select.select([sys.stdin], [], [], 0)[0]:
            return None
        ch = sys.stdin.read(1)
        if ch == "\x1b" and select.select([sys.stdin], [], [], 0.02)[0]:
            seq = sys.stdin.read(2)
            return {"[D": "left", "[C": "right", "[A": "up", "[B": "down"}.get(seq)
        return ch


def _run_tab_view(tasks: dict) -> dict:
    """
    Run tasks concurrently and display their output in a switchable tab terminal view.

    Press [1]/[2]/... or Tab/arrow keys to switch tabs.
    tasks: {name: callable(buf: deque) -> int}
    Returns: {name: exit_code}
    """
    if not _tty:
        return _run_parallel_columns(tasks)

    names = list(tasks.keys())
    bufs: dict = {nm: collections.deque(maxlen=5000) for nm in names}
    status: dict = {nm: "running" for nm in names}
    results: dict = {nm: None for nm in names}
    lock = threading.Lock()
    done_ev = threading.Event()
    active = [0]
    scroll_offsets: dict = {nm: 0 for nm in names}

    def _run_one(nm: str) -> None:
        rc = tasks[nm](bufs[nm])
        with lock:
            results[nm] = rc if rc is not None else 0
            status[nm] = "ok" if results[nm] == 0 else "fail"
            if all(status[n] != "running" for n in names):
                done_ev.set()

    for nm in names:
        threading.Thread(target=_run_one, args=(nm,), daemon=True).start()

    _BADGE = {"running": "RUNNING", "ok": "  DONE ", "fail": "FAILED "}
    _BADGE_COL = {"running": YELLOW, "ok": GREEN, "fail": RED}
    _BOLD = "\033[1m" if _tty else ""

    initialized = [False]

    def _draw() -> None:
        tw, th = shutil.get_terminal_size((120, 24))
        content_h = max(th - 6, 4)
        inner_w = tw - 4

        # Tab bar
        tab_parts = []
        for i, nm in enumerate(names):
            st = status[nm]
            badge = _BADGE.get(st, "       ")
            bc = _BADGE_COL.get(st, "")
            arrow = (
                f"{_BOLD}▶ {nm.upper()}{RESET}" if i == active[0] else f"  {nm.upper()}"
            )
            tab_parts.append(f"{arrow} [{bc}{badge}{RESET}]")
        tab_bar_raw = "  │  ".join(tab_parts)
        tab_pad = max(0, tw - 2 - len(_ANSI_RE.sub("", tab_bar_raw)))

        # Content: active tab buffer, respecting scroll offset
        nm = names[active[0]]
        snap = list(bufs[nm])
        offset = scroll_offsets[nm]
        if offset == 0:
            display = snap[-content_h:] if len(snap) >= content_h else snap
        else:
            end = max(0, len(snap) - offset)
            start = max(0, end - content_h)
            display = snap[start:end]
        content_lines: list[str] = []
        for raw in display:
            clean = _ANSI_RE.sub("", raw).expandtabs(4)
            if len(clean) > inner_w:
                clean = clean[: inner_w - 1] + "~"
            content_lines.append(clean.ljust(inner_w))
        while len(content_lines) < content_h:
            content_lines.append(" " * inner_w)

        # Footer
        hints = "  ".join(f"[{i + 1}] {n}" for i, n in enumerate(names))
        hints += "  [Tab] cycle  [↑↓] scroll"
        active_offset = scroll_offsets[names[active[0]]]
        if active_offset > 0:
            hints += f"  [+{active_offset} lines]"
        hints += "  Ctrl+C to stop"
        if len(hints) > inner_w:
            hints = hints[: inner_w - 1] + "~"
        hints = hints.ljust(inner_w)

        sep = "─" * (tw - 2)
        rows = [
            "┌" + sep + "┐",
            "│" + tab_bar_raw + " " * tab_pad + "│",
            "├" + sep + "┤",
            *("│ " + cl + " │" for cl in content_lines),
            "├" + sep + "┤",
            "│ " + hints + " │",
            "└" + sep + "┘",
        ]

        # Use absolute cursor positioning for every row so that no \n is
        # emitted — \n at the terminal bottom causes scrolling and frame drift.
        out: list[str] = []
        if not initialized[0]:
            out.append("\033[2J")  # clear screen once on first paint
            initialized[0] = True
        for idx, row in enumerate(rows):
            out.append(f"\033[{idx + 1};1H{row}\033[K")
        # Erase anything below the frame from a previous (taller) draw.
        out.append(f"\033[{len(rows) + 1};1H\033[J")
        sys.stdout.write("".join(out))
        sys.stdout.flush()

    _enable_ansi_windows()
    old_term = _enter_raw_mode()
    try:
        sys.stdout.write("\033[?25l")  # hide cursor to suppress render flicker
        sys.stdout.flush()
        REFRESH = 0.12
        while not done_ev.is_set():
            ch = _read_key_nonblocking()
            if ch is not None:
                if ch.isdigit() and 1 <= int(ch) <= len(names):
                    active[0] = int(ch) - 1
                    scroll_offsets[names[active[0]]] = 0
                elif ch in ("\t", "right"):
                    active[0] = (active[0] + 1) % len(names)
                    scroll_offsets[names[active[0]]] = 0
                elif ch == "left":
                    active[0] = (active[0] - 1) % len(names)
                    scroll_offsets[names[active[0]]] = 0
                elif ch == "up":
                    nm_active = names[active[0]]
                    _, th_cur = shutil.get_terminal_size((120, 24))
                    ch_cur = max(th_cur - 6, 4)
                    max_off = max(0, len(bufs[nm_active]) - ch_cur)
                    scroll_offsets[nm_active] = min(
                        scroll_offsets[nm_active] + 1, max_off
                    )
                elif ch == "down":
                    nm_active = names[active[0]]
                    scroll_offsets[nm_active] = max(0, scroll_offsets[nm_active] - 1)
            _draw()
            time.sleep(REFRESH)
        _draw()
    except KeyboardInterrupt:
        raise
    finally:
        sys.stdout.write("\033[?25h")  # restore cursor
        _exit_raw_mode(old_term)
        sys.stdout.write("\n")
        sys.stdout.flush()

    return results


def _get_local_ip() -> str:
    """
    Return the primary LAN IP address.
    """
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually send traffic.
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def _fetch_keycloak_oauth_saml_config(
    oauth_client_id: str = "resource-planner-oauth",
    oauth_client_secret: str = "dev-oauth-secret",
):
    """
    Return (oauth_config, saml_config) fetched from the running local Keycloak,
    or None on error.
    """
    import json
    import urllib.request
    import xml.etree.ElementTree as ET

    discovery_url = (
        f"{_KEYCLOAK_URL}/realms/{_KEYCLOAK_REALM}/.well-known/openid-configuration"
    )
    metadata_url = f"{_KEYCLOAK_URL}/realms/{_KEYCLOAK_REALM}/protocol/saml/descriptor"

    try:
        with urllib.request.urlopen(discovery_url, timeout=5) as resp:  # nosec B310
            oidc = json.loads(resp.read())
    except Exception as exc:
        print(f"{RED}  Failed to fetch OIDC discovery: {exc}{RESET}")
        return None

    try:
        with urllib.request.urlopen(metadata_url, timeout=5) as resp:  # nosec B310
            saml_xml = resp.read().decode()
    except Exception as exc:
        print(f"{RED}  Failed to fetch SAML metadata: {exc}{RESET}")
        return None

    root = ET.fromstring(saml_xml)
    ns = {
        "md": "urn:oasis:names:tc:SAML:2.0:metadata",
        "ds": "http://www.w3.org/2000/09/xmldsig#",
    }

    idp_cert = ""
    for key_desc in root.findall(".//md:KeyDescriptor[@use='signing']", ns):
        cert_el = key_desc.find(".//ds:X509Certificate", ns)
        if cert_el is not None and cert_el.text:
            idp_cert = cert_el.text.strip()
            break

    idp_sso_url = ""
    sso_el = root.find(
        ".//md:SingleSignOnService"
        "[@Binding='urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect']",
        ns,
    )
    if sso_el is not None:
        idp_sso_url = sso_el.get("Location", "")

    oauth_config = {
        "name": "Keycloak (Dev)",
        "client_id": oauth_client_id,
        "client_secret": oauth_client_secret,
        "auth_endpoint": oidc.get("authorization_endpoint", ""),
        "token_endpoint": oidc.get("token_endpoint", ""),
        "userinfo_endpoint": oidc.get("userinfo_endpoint", ""),
        "scope": "openid email profile",
    }

    saml_config = {
        "name": "Keycloak (Dev)",
        "idp_entity_id": root.get("entityID", ""),
        "idp_sso_url": idp_sso_url,
        "idp_x509_cert": idp_cert,
        "sp_entity_id": "http://localhost:8000/sp",
        "sp_assertion_url": "http://localhost:8000/api/v1/auth/saml/acs/",
    }

    return oauth_config, saml_config


def _sync_keycloak_providers_in_db(oauth_config: dict, saml_config: dict) -> None:
    """
    Update OAuth/SAML providers in DB whose endpoints point to the local
    Keycloak realm.
    """
    env = _load_env_defaults()
    try:
        if "postgresql" in env.get("DB_ENGINE", "").lower():
            _sync_keycloak_postgresql(env, oauth_config, saml_config)
        else:
            _sync_keycloak_sqlite(oauth_config, saml_config)
    except Exception as exc:  # nosec B110
        print(f"  {YELLOW}Could not auto-sync providers: {exc}{RESET}")
        print(
            "  Update idp_entity_id, idp_sso_url, idp_x509_cert and OAuth "
            "endpoints manually."
        )


def _sync_keycloak_sqlite(oauth_config: dict, saml_config: dict) -> None:
    import sqlite3

    db_path = WEB_DIR / "db.sqlite3"
    if not db_path.exists():
        print(f"  {YELLOW}No SQLite DB found — skipping provider sync.{RESET}")
        return
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute(  # nosec B608
            "UPDATE oauth_oauth"
            " SET auth_endpoint=?, token_endpoint=?, userinfo_endpoint=?"
            " WHERE auth_endpoint LIKE ?",
            (
                oauth_config["auth_endpoint"],
                oauth_config["token_endpoint"],
                oauth_config["userinfo_endpoint"],
                "%/realms/resource-planner%",
            ),
        )
        oauth_count = cur.rowcount
        saml_count = 0
        if saml_config.get("idp_x509_cert"):
            cur.execute(  # nosec B608
                "UPDATE saml_saml"
                " SET idp_entity_id=?, idp_sso_url=?, idp_x509_cert=?"
                " WHERE idp_entity_id LIKE ?",
                (
                    saml_config["idp_entity_id"],
                    saml_config["idp_sso_url"],
                    saml_config["idp_x509_cert"],
                    "%/realms/resource-planner%",
                ),
            )
            saml_count = cur.rowcount
        conn.commit()
    finally:
        conn.close()
    _print_sync_result(oauth_count, saml_count)


def _sync_keycloak_postgresql(env: dict, oauth_config: dict, saml_config: dict) -> None:
    try:
        import psycopg2
    except ImportError:
        print(f"  {YELLOW}psycopg2 not available — skipping provider sync.{RESET}")
        return
    conn = psycopg2.connect(
        host=env.get("DB_HOST", "127.0.0.1"),
        port=int(env.get("DB_PORT", "5432")),
        dbname=env.get("DB_NAME", "resourceplanner"),
        user=env.get("DB_USER", "postgres"),
        password=env.get("DB_PASSWORD", ""),
        connect_timeout=3,
    )
    try:
        cur = conn.cursor()
        cur.execute(  # nosec B608
            "UPDATE oauth_oauth"
            " SET auth_endpoint=%s, token_endpoint=%s, userinfo_endpoint=%s"
            " WHERE auth_endpoint LIKE %s",
            (
                oauth_config["auth_endpoint"],
                oauth_config["token_endpoint"],
                oauth_config["userinfo_endpoint"],
                "%/realms/resource-planner%",
            ),
        )
        oauth_count = cur.rowcount
        saml_count = 0
        if saml_config.get("idp_x509_cert"):
            cur.execute(  # nosec B608
                "UPDATE saml_saml"
                " SET idp_entity_id=%s, idp_sso_url=%s, idp_x509_cert=%s"
                " WHERE idp_entity_id LIKE %s",
                (
                    saml_config["idp_entity_id"],
                    saml_config["idp_sso_url"],
                    saml_config["idp_x509_cert"],
                    "%/realms/resource-planner%",
                ),
            )
            saml_count = cur.rowcount
        conn.commit()
    finally:
        conn.close()
    _print_sync_result(oauth_count, saml_count)


def _print_sync_result(oauth_count: int, saml_count: int) -> None:
    if oauth_count:
        print(
            f"  {GREEN}OAuth providers synced with updated Keycloak endpoints.{RESET}"
        )
    else:
        print(
            f"  {YELLOW}No OAuth provider found — update endpoints manually if needed."
            f"{RESET}"
        )
    if saml_count:
        print(
            f"  {GREEN}SAML providers synced with new Keycloak cert/endpoints.{RESET}"
        )
    else:
        print(
            f"  {YELLOW}No SAML provider found — update IDP fields manually if needed."
            f"{RESET}"
        )


def _display_keycloak_oauth_config(
    client_id: str,
    auth_endpoint: str,
    token_endpoint: str,
    userinfo_endpoint: str,
    scope: str,
    label_width: int = 26,
    name: str = "",
) -> None:
    w = label_width
    if name:
        print(f"  {'Provider Name':<{w}}: {name}")
    print(f"  {'Client ID':<{w}}: {client_id}")
    print(f"  {'Client Secret':<{w}}: [hidden]")
    print(f"  {'Auth Endpoint':<{w}}: {auth_endpoint}")
    print(f"  {'Token Endpoint':<{w}}: {token_endpoint}")
    print(f"  {'User Info Endpoint':<{w}}: {userinfo_endpoint}")
    print(f"  {'Scope':<{w}}: {scope}")


def _display_keycloak_saml_config(
    entity_id: str,
    sso_url: str,
    signing_data: str,
    label_width: int = 26,
    name: str = "",
    sp_entity_id: str = "",
    sp_assertion_url: str = "",
    show_cert_markers: bool = False,
    cert_indent: str = "    ",
) -> None:
    w = label_width
    preview = (signing_data[:68] + "...") if len(signing_data) > 68 else signing_data
    if name:
        print(f"  {'Provider Name':<{w}}: {name}")
    print(f"  {'IDP Entity ID':<{w}}: {entity_id}")
    print(f"  {'IDP SSO URL':<{w}}: {sso_url}")
    print(f"  {'IDP X.509 Cert':<{w}}: {preview}")
    if sp_entity_id:
        print(f"  {'SP Entity ID':<{w}}: {sp_entity_id}")
    if sp_assertion_url:
        print(f"  {'Assertion Consumer URL':<{w}}: {sp_assertion_url}")
    if signing_data:
        print("\n  Full IDP X.509 Certificate:")
        if show_cert_markers:
            print("  -----BEGIN CERTIFICATE-----")
        for i in range(0, len(signing_data), 64):
            print(f"{cert_indent}{signing_data[i : i + 64]}")
        if show_cert_markers:
            print("  -----END CERTIFICATE-----")


def configure_keycloak():
    """
    Print ready-to-use OAuth and SAML configuration values from the local Keycloak.
    """
    env = _load_env_defaults()
    if env.get("DEV_KEYCLOAK", "").lower() != "true":
        print(f"\n{YELLOW}DEV_KEYCLOAK is not enabled.{RESET}")
        print("  Add DEV_KEYCLOAK=true to apps/web/.env and start the dev server.")
        pause()
        return

    print(f"\nFetching Keycloak configuration from {_KEYCLOAK_URL} ...")
    result = _fetch_keycloak_oauth_saml_config()

    if result is None:
        print(f"\n{YELLOW}Keycloak is not reachable.{RESET}")
        print("  It may still be starting — wait ~60 s and try again.")
        print(f"  Admin console: {_KEYCLOAK_URL}/admin  (admin / admin)")
        pause()
        return

    oauth_config, saml_config = result
    sep = "=" * 64

    print(f"\n{sep}")
    print("  KEYCLOAK DEV CONFIGURATION")
    print(sep)
    print(f"  Admin console  :  {_KEYCLOAK_URL}/admin")
    print("  Credentials    :  admin / admin")
    print(f"  Realm          :  {_KEYCLOAK_REALM}")
    print("  Test user      :  sso@example.com / Test1234!")

    print("\n--- OAuth 2.0 (OIDC) ---")
    _display_keycloak_oauth_config(
        name=str(oauth_config.get("name", "")),
        client_id=str(oauth_config.get("client_id", "")),
        auth_endpoint=str(oauth_config.get("auth_endpoint", "")),
        token_endpoint=str(oauth_config.get("token_endpoint", "")),
        userinfo_endpoint=str(oauth_config.get("userinfo_endpoint", "")),
        scope=str(oauth_config.get("scope", "")),
        label_width=22,
    )

    print("\n--- SAML 2.0 ---")
    _display_keycloak_saml_config(
        name=str(saml_config.get("name", "")),
        entity_id=str(saml_config.get("idp_entity_id", "")),
        sso_url=str(saml_config.get("idp_sso_url", "")),
        signing_data=str(saml_config.get("idp_x509_cert", "")),
        sp_entity_id=str(saml_config.get("sp_entity_id", "")),
        sp_assertion_url=str(saml_config.get("sp_assertion_url", "")),
        label_width=22,
        show_cert_markers=True,
        cert_indent="  ",
    )

    print(f"\n{sep}")
    pause()


def runserver():
    css_paths = list(
        (ROOT / "apps" / "web" / "static" / "css" / "styles").rglob("*.css")
    ) + [ROOT / "package.json"]
    js_paths = [
        p
        for p in (ROOT / "apps" / "web" / "static" / "js").rglob("*.js")
        if "dist" not in p.parts
    ] + [ROOT / "package.json", ROOT / "build-js.mjs"]
    req_paths = [
        ROOT / "requirements" / "base.txt",
        ROOT / "requirements" / "dev.txt",
    ]
    icons_script = ROOT / "scripts" / "build" / "generate_icons_json.py"
    icons_json = (
        ROOT / "apps" / "web" / "static" / "js" / "data" / "bootstrap-icons.json"
    )

    watch = {
        "postcss": css_paths,
        "build-js": js_paths,
        "requirements": req_paths,
        "icons-json": [icons_script],
    }
    task_cmds = {"postcss": "npm run build:css", "build-js": "npm run build:js"}

    tasks_to_run: dict = {}
    skipped: list[str] = []

    for name in ("postcss", "build-js", "requirements", "icons-json"):
        if name == "icons-json":
            # Regenerate only when the script itself changed or JSON is missing.
            if not icons_json.exists() or _needs_run(name, watch[name]):
                cmd = f'"{sys.executable}" "{icons_script}"'
                tasks_to_run[name] = lambda buf, c=cmd: _run_cmd_buffered(c, buf)
            else:
                skipped.append(name)
            continue
        if _needs_run(name, watch[name]):
            if name == "requirements":
                tasks_to_run[name] = _install_requirements_buffered
            else:
                cmd = task_cmds[name]
                tasks_to_run[name] = lambda buf, c=cmd: _run_cmd_buffered(c, buf)
        else:
            skipped.append(name)

    if skipped:
        print(f"\nSkipping (no changes detected): {', '.join(skipped)}")

    failed: list[str] = []
    if tasks_to_run:
        print(f"\nRunning: {', '.join(tasks_to_run)}")
        results = _run_parallel_columns(tasks_to_run)
        for name, rc in results.items():
            if rc != 0:
                failed.append(name)
            else:
                _record_run(name, watch[name])

    if failed:
        print(f"{RED}\nPre-server tasks failed: {', '.join(failed)}{RESET}")
        pause()
        return

    # Each entry: (profile, label, [env_keys written by us that must be
    # removed on exit])
    started_services: list[tuple[str, str, list[str]]] = []

    pending_docker: dict[str, tuple] = {}  # name → (profile, container, label)
    docker_pre_env_keys: dict[
        str, list[str]
    ] = {}  # env keys written before docker start

    pg_config = _get_postgres_docker_config()
    if pg_config:
        pending_docker["postgresql"] = ("postgres", _DOCKER_CONTAINER_PG, "PostgreSQL")

    smtp_config = _get_smtp_docker_config()
    if smtp_config:
        smtp_env_keys: list[str] = []
        if (
            smtp_config["auth_enabled"]
            and smtp_config["username"]
            and smtp_config["password"]
        ):
            _env_write(
                "MP_SMTP_AUTH", f"{smtp_config['username']}:{smtp_config['password']}"
            )
            _env_write("MP_SMTP_AUTH_ALLOW_INSECURE", "true")
            smtp_env_keys = ["MP_SMTP_AUTH", "MP_SMTP_AUTH_ALLOW_INSECURE"]
        pending_docker["mailpit"] = ("smtp", _DOCKER_CONTAINER_MAILPIT, "Mailpit")
        docker_pre_env_keys["mailpit"] = smtp_env_keys

    aws_config = _get_localstack_docker_config()
    if aws_config is not None:
        pending_docker["localstack"] = (
            "aws",
            _DOCKER_CONTAINER_LOCALSTACK,
            "LocalStack",
        )

    keycloak_config = _get_keycloak_docker_config()
    if keycloak_config is not None:
        kc_lan_ip = _get_local_ip()
        _generate_realm_export(lan_ip=kc_lan_ip)
        _env_write("KEYCLOAK_HOSTNAME", kc_lan_ip)
        docker_pre_env_keys["keycloak"] = ["KEYCLOAK_HOSTNAME"]
        pending_docker["keycloak"] = (
            "keycloak",
            _DOCKER_CONTAINER_KEYCLOAK,
            "Keycloak",
        )

    docker_results: dict[str, int] = {}
    if pending_docker:
        docker_pre_running = {
            name: _docker_container_status(container) == "running"
            for name, (profile, container, label) in pending_docker.items()
        }
        docker_task_fns: dict = {
            name: (
                lambda buf, p=profile, c=container, lbl=label: (
                    _compose_up_profile_buffered(p, c, lbl, buf)
                )
            )
            for name, (profile, container, label) in pending_docker.items()
        }
        print(f"\nDocker: {', '.join(pending_docker)}")
        docker_results = _run_parallel_columns(docker_task_fns)

        for name, rc in docker_results.items():
            profile, container, label = pending_docker[name]
            was_running = docker_pre_running.get(name, False)
            if rc == 0 and not was_running:
                env_keys: list[str] = []
                if name == "localstack":
                    _env_write("AWS_ENDPOINT", _LOCALSTACK_ENDPOINT)
                    env_keys = ["AWS_ENDPOINT"]
                elif name == "mailpit":
                    env_keys = docker_pre_env_keys.get("mailpit", [])
                elif name == "keycloak":
                    env_keys = docker_pre_env_keys.get("keycloak", [])
                started_services.append((profile, label, env_keys))
            elif rc != 0:
                for key in docker_pre_env_keys.get(name, []):
                    _env_remove(key)

    live_procs: list = []
    try:
        host = _get_local_ip()
        _env_write("DEV_LAN_IP", host)

        def _tracker_task(buf: "collections.deque[str]") -> int:
            buf.append(f"http://localhost:{TEST_TRACKER_PORT}")
            buf.append(f"http://{host}:{TEST_TRACKER_PORT}")
            tracker_env = {**os.environ, "PYTHONUNBUFFERED": "1"}
            proc = subprocess.Popen(  # nosec B603
                [sys.executable, "-u", str(TEST_TRACKER_DIR / "server.py")],
                cwd=TEST_TRACKER_DIR,
                env=tracker_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            live_procs.append(proc)
            assert proc.stdout is not None
            for line in iter(proc.stdout.readline, ""):
                buf.append(_ANSI_RE.sub("", line.rstrip()))
            proc.wait()
            return proc.returncode

        def _django_task(buf: "collections.deque[str]") -> int:
            buf.append("http://localhost:8000")
            buf.append(f"http://{host}:8000")
            proc = subprocess.Popen(  # nosec B603
                [sys.executable, "manage.py", "runserver", "0.0.0.0:8000"],
                cwd=WEB_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            live_procs.append(proc)
            assert proc.stdout is not None
            for line in iter(proc.stdout.readline, ""):
                buf.append(_ANSI_RE.sub("", line.rstrip()))
            proc.wait()
            return proc.returncode

        _run_tab_view({"django app": _django_task, "test tracker": _tracker_task})
    except KeyboardInterrupt:
        pass
    finally:
        for proc in live_procs:
            if proc.poll() is None:
                proc.terminate()
        _env_remove("DEV_LAN_IP")
        for profile, label, env_keys in started_services:
            _compose_down_profile(profile, label)
            for key in env_keys:
                _env_remove(key)


def _html_flags(report_name: str) -> str:
    REPORTS_DIR.mkdir(exist_ok=True)
    return f"--html={REPORTS_DIR / report_name} --self-contained-html"


def _discover_package_test_dirs() -> list[Path]:
    """Return test directories for packages that have tests."""
    dirs = []
    for pkg in sorted(PACKAGES_DIR.iterdir()):
        if pkg.is_dir() and not pkg.name.startswith("."):
            tests_dir = pkg / "tests"
            if tests_dir.exists() and any(tests_dir.rglob("test_*.py")):
                dirs.append(tests_dir)
    return dirs


def _run_django_tests(path: str = "", report: str = "django-report.html") -> int:
    # --override-ini=addopts= clears the root pyproject.toml addopts (which sets
    # its own --html flag) so our explicit report name is the only one used.
    # --no-migrations creates tables directly from model state (syncdb-style) instead
    # of replaying every migration per worker — significantly faster for large schemas.
    cmd = (
        f"pytest -v -n auto --dist=loadfile --no-migrations --durations=30 "
        f"--override-ini=addopts= {_html_flags(report)}"
    )
    if path:
        cmd += f" {path}"
    return _run_pytest(cmd)


def _run_django_unit_tests(
    path: str = "", report: str = "django-unit-report.html"
) -> int:
    # Unit tests use SimpleTestCase (no DB) — dist=load gives pure load-balancing
    # without the file-grouping constraint that loadfile adds for DB isolation.
    cmd = (
        f"pytest -v -n auto --dist=load -m unit --durations=30 "
        f"--override-ini=addopts= {_html_flags(report)}"
    )
    if path:
        cmd += f" {path}"
    return _run_pytest(cmd)


def _run_django_integration_tests(
    path: str = "", report: str = "django-integration-report.html"
) -> int:
    # Integration tests hit the DB — loadfile keeps tests in the same file on the
    # same worker so they share DB state correctly.
    # --no-migrations creates tables directly from model state (syncdb-style) instead
    # of replaying every migration per worker — significantly faster for large schemas.
    cmd = (
        f"pytest -v -n auto --dist=loadfile -m integration --no-migrations "
        f"--durations=30 --override-ini=addopts= {_html_flags(report)}"
    )
    if path:
        cmd += f" {path}"
    return _run_pytest(cmd)


def _pkg_base_cmd(marker: str = "", report: str = "packages-report.html") -> str:
    # -p no:django disables pytest-django so packages can be collected in a single
    # pytest call regardless of which pyproject.toml becomes the rootdir.
    # --rootdir ensures packages/conftest.py is always discovered.
    html = _html_flags(report)
    marker_flag = f"-m {marker} " if marker else ""
    return (
        f"pytest -v -n auto --dist=loadfile {marker_flag}"
        f"-p no:django --override-ini=addopts= "
        f'--rootdir="{ROOT}" --import-mode=importlib {html}'
    )


def _run_package_tests(path: str = "", report: str = "packages-report.html") -> int:
    base = _pkg_base_cmd(report=report)
    if path:
        return _run_pytest(f"{base} {path}")
    test_dirs = _discover_package_test_dirs()
    if not test_dirs:
        print("No package test directories found.")
        return 0
    paths = " ".join(str(d) for d in test_dirs)
    return _run_pytest(f"{base} {paths}")


def _run_package_unit_tests(
    path: str = "", report: str = "packages-unit-report.html"
) -> int:
    # Unit tests have no external dependencies — use dist=load
    # (no file grouping needed).
    html = _html_flags(report)
    base = (
        f"pytest -v -n auto --dist=load -m unit "
        f"-p no:django --override-ini=addopts= "
        f'--rootdir="{ROOT}" --import-mode=importlib {html}'
    )
    if path:
        return _run_pytest(f"{base} {path}")
    test_dirs = _discover_package_test_dirs()
    if not test_dirs:
        print("No package test directories found.")
        return 0
    paths = " ".join(str(d) for d in test_dirs)
    return _run_pytest(f"{base} {paths}")


def _run_package_integration_tests(
    path: str = "", report: str = "packages-integration-report.html"
) -> int:
    html = _html_flags(report)
    base = (
        f"pytest -v -n auto --dist=loadfile -m integration "
        f"-p no:django --override-ini=addopts= "
        f'--rootdir="{ROOT}" --import-mode=importlib {html}'
    )
    if path:
        return _run_pytest(f"{base} {path}")
    test_dirs = _discover_package_test_dirs()
    if not test_dirs:
        print("No package test directories found.")
        return 0
    paths = " ".join(str(d) for d in test_dirs)
    return _run_pytest(f"{base} {paths}")


def _write_all_report_index(django_rc: int, packages_rc: int) -> None:
    """Write all-report.html — a simple index linking to both suite reports."""
    REPORTS_DIR.mkdir(exist_ok=True)
    django_status = "PASSED" if django_rc == 0 else "FAILED"
    packages_status = "PASSED" if packages_rc == 0 else "FAILED"
    overall = "PASSED" if django_rc == 0 and packages_rc == 0 else "FAILED"
    colour = "#2a9d2a" if overall == "PASSED" else "#c0392b"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>All Tests — {overall}</title>
  <style>
    body {{ font-family: sans-serif; padding: 2rem; background: #fafafa; }}
    h1 {{ color: {colour}; margin-bottom: 1.5rem; }}
    ul {{ list-style: none; padding: 0; }}
    li {{ margin: 0.6rem 0; }}
    a {{ font-size: 1.05rem; text-decoration: none; color: #1a73e8; }}
    a:hover {{ text-decoration: underline; }}
    .badge {{
      display: inline-block; margin-left: 0.6rem; padding: 0.15rem 0.5rem;
      border-radius: 3px; font-size: 0.8rem; font-weight: bold; color: #fff;
    }}
    .PASSED {{ background: #2a9d2a; }}
    .FAILED {{ background: #c0392b; }}
  </style>
</head>
<body>
  <h1>All Tests — {overall}</h1>
  <ul>
    <li>
      <a href="django-report.html">Django (apps/web)</a>
      <span class="badge {django_status}">{django_status}</span>
    </li>
    <li>
      <a href="packages-report.html">Packages</a>
      <span class="badge {packages_status}">{packages_status}</span>
    </li>
  </ul>
</body>
</html>"""
    report_path = REPORTS_DIR / "all-report.html"
    report_path.write_text(html, encoding="utf-8")
    print(f"\nReports written to {REPORTS_DIR}")
    print(f"  all-report.html      ({overall})")
    print(f"  django-report.html   ({django_status})")
    print(f"  packages-report.html ({packages_status})")


def _run_django_tests_menu() -> None:
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605
        print("=== RUN TESTS: DJANGO ===")
        print("1. All")
        print("2. Unit")
        print("3. Integration")
        print("0. Back")

        choice = input("\nSelect: ").strip()

        if choice == "1":
            path = input("Test path (blank = full suite): ").strip()
            _run_django_tests(path)
            pause()
        elif choice == "2":
            path = input("Test path (blank = all unit tests): ").strip()
            _run_django_unit_tests(path)
            pause()
        elif choice == "3":
            path = input("Test path (blank = all integration tests): ").strip()
            _run_django_integration_tests(path)
            pause()
        elif choice == "0":
            return
        else:
            print(f"{YELLOW}Invalid choice{RESET}")
            pause()


def _run_packages_tests_menu() -> None:
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605
        print("=== RUN TESTS: PACKAGES ===")
        print("1. All")
        print("2. Unit")
        print("3. Integration")
        print("0. Back")

        choice = input("\nSelect: ").strip()

        if choice == "1":
            path = input("Test path (blank = full suite): ").strip()
            _run_package_tests(path)
            pause()
        elif choice == "2":
            path = input("Test path (blank = all unit tests): ").strip()
            _run_package_unit_tests(path)
            pause()
        elif choice == "3":
            path = input("Test path (blank = all integration tests): ").strip()
            _run_package_integration_tests(path)
            pause()
        elif choice == "0":
            return
        else:
            print(f"{YELLOW}Invalid choice{RESET}")
            pause()


def run_tests():
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605
        print("=== RUN TESTS ===")
        print("1. All")
        print("2. Django  (apps/web)")
        print("3. Packages")
        print("0. Back")

        choice = input("\nSelect: ").strip()

        if choice == "1":
            django_rc = _run_django_tests()
            packages_rc = _run_package_tests()
            _write_all_report_index(django_rc, packages_rc)
            pause()
        elif choice == "2":
            _run_django_tests_menu()
        elif choice == "3":
            _run_packages_tests_menu()
        elif choice == "0":
            return
        else:
            print(f"{YELLOW}Invalid choice{RESET}")
            pause()


def install_requirements():
    print("\nInstalling requirements...")
    rc = _install_requirements()
    if rc == 0:
        print("Requirements installed successfully.")
    pause()


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
# Docker standalone menu
# ---------------------------------------------------------------------------


def _docker_wait_and_cleanup(started_services: list) -> None:
    """Block until Ctrl+C, then stop any services we started."""
    if not started_services:
        pause()
        return

    print(f"\n{GREEN}Running. Press Ctrl+C to stop...{RESET}\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
    finally:
        for profile, label, env_keys in started_services:
            _compose_down_profile(profile, label)
            for key in env_keys:
                _env_remove(key)


def _wait_for_keycloak_ready(
    timeout: int = 120,
    interval: int = 5,
    oauth_client_id: str = "resource-planner-oauth",
    oauth_client_secret: str = "dev-oauth-secret",
):
    """
    Poll until Keycloak's realm endpoint responds, then return OAuth+SAML
    config or None.
    """
    import urllib.request

    url = f"{_KEYCLOAK_URL}/realms/{_KEYCLOAK_REALM}"
    print("\n  Waiting for Keycloak to be ready", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3):  # nosec B310
                pass
            print(f" {GREEN}ready{RESET}")
            return _fetch_keycloak_oauth_saml_config(
                oauth_client_id=oauth_client_id,
                oauth_client_secret=oauth_client_secret,
            )
        except Exception:
            print(".", end="", flush=True)
            time.sleep(interval)
    print(f" {YELLOW}timed out{RESET}")
    return None


def docker_postgres() -> None:
    os.system("cls" if os.name == "nt" else "clear")  # nosec B605
    print("=== DOCKER: PostgreSQL ===\n")

    if not _docker_available():
        print(f"{RED}Docker not found. Install Docker Desktop and try again.{RESET}")
        pause()
        return

    env = _load_env_defaults()
    port = _prompt("Port", env.get("DB_PORT", "5432"))
    user = _prompt("User", env.get("DB_USER", "postgres"))
    password = getpass.getpass(
        f"Password [{('*' * 6) if env.get('DB_PASSWORD') else '(none)'}]: "
    ).strip() or env.get("DB_PASSWORD", "")
    db_name = _prompt("Database name", env.get("DB_NAME", "resourceplanner"))

    _env_write("DB_PORT", port)
    _env_write("DB_USER", user)
    _env_write("DB_PASSWORD", password)
    _env_write("DB_NAME", db_name)

    print()
    started = _compose_up_profile(
        "postgres", _DOCKER_CONTAINER_PG, "PostgreSQL", force_recreate=True
    )

    if started is None:
        pause()
        return

    sep = "─" * 44
    print(f"\n  {sep}")
    print(f"  {'PostgreSQL Connection Details':^42}")
    print(f"  {sep}")
    print(f"  {'Host':<20}: localhost")
    print(f"  {'Port':<20}: {port}")
    print(f"  {'Database':<20}: {db_name}")
    print(f"  {'Username':<20}: {user}")
    print(f"  {'Password':<20}: {'[set]' if password else '(none)'}")
    print(f"  {sep}")

    started_services: list[tuple[str, str, list[str]]] = []
    if started:
        # DB_* keys are persistent setup config — don't remove on exit.
        started_services.append(("postgres", "PostgreSQL", []))

    _docker_wait_and_cleanup(started_services)


def docker_email() -> None:
    os.system("cls" if os.name == "nt" else "clear")  # nosec B605
    print("=== DOCKER: Email (Mailpit) ===\n")

    if not _docker_available():
        print(f"{RED}Docker not found. Install Docker Desktop and try again.{RESET}")
        pause()
        return

    env = _load_env_defaults()
    smtp_port = _prompt("SMTP port", env.get("EMAIL_SMTP_PORT", "1025"))
    auth_enabled = input("Enable SMTP auth? (y/N): ").strip().lower() == "y"

    _env_write("EMAIL_SMTP_PORT", smtp_port)

    username = ""
    password = ""
    runtime_env_keys: list[str] = []
    if auth_enabled:
        username = _prompt("SMTP username", env.get("EMAIL_SMTP_USERNAME", ""))
        password = getpass.getpass("SMTP password: ").strip()
        if username and password:
            _env_write("MP_SMTP_AUTH", f"{username}:{password}")
            _env_write("MP_SMTP_AUTH_ALLOW_INSECURE", "true")
            runtime_env_keys = ["MP_SMTP_AUTH", "MP_SMTP_AUTH_ALLOW_INSECURE"]

    print()
    started = _compose_up_profile(
        "smtp", _DOCKER_CONTAINER_MAILPIT, "Mailpit", force_recreate=True
    )

    if started is None:
        for key in runtime_env_keys:
            _env_remove(key)
        pause()
        return

    sep = "─" * 44
    print(f"\n  {sep}")
    print(f"  {'SMTP Configuration (Mailpit)':^42}")
    print(f"  {sep}")
    print(f"  {'SMTP Host':<20}: localhost")
    print(f"  {'Encryption':<20}: None")
    print(f"  {'Port':<20}: {smtp_port}")
    print(f"  {'Username':<20}: {username or '(none)'}")
    print(f"  {'Password':<20}: {'[set]' if password else '(none)'}")
    print(f"  {sep}")
    print("  Web UI   : http://localhost:8025")

    started_services = []
    if started:
        started_services.append(("smtp", "Mailpit", runtime_env_keys))

    _docker_wait_and_cleanup(started_services)


def docker_localstack() -> None:
    os.system("cls" if os.name == "nt" else "clear")  # nosec B605
    print("=== DOCKER: LocalStack ===\n")

    if not _docker_available():
        print(f"{RED}Docker not found. Install Docker Desktop and try again.{RESET}")
        pause()
        return

    started = _compose_up_profile("aws", _DOCKER_CONTAINER_LOCALSTACK, "LocalStack")
    already_running = (
        started is None
        and _docker_container_status(_DOCKER_CONTAINER_LOCALSTACK) == "running"
    )

    if started is None and not already_running:
        pause()
        return

    runtime_env_keys: list[str] = []
    if started:
        _env_write("AWS_ENDPOINT", _LOCALSTACK_ENDPOINT)
        runtime_env_keys = ["AWS_ENDPOINT"]

    print(f"\n  Endpoint : {_LOCALSTACK_ENDPOINT}")
    print("  Services : secretsmanager, s3, logs")

    started_services = []
    if started:
        started_services.append(("aws", "LocalStack", runtime_env_keys))
    else:
        print(f"\n{YELLOW}  Container already running — not managed here.{RESET}")

    _docker_wait_and_cleanup(started_services)


def _keycloak_start() -> "tuple[str | None, bool]":
    """Ensure the Keycloak container is running.

    Returns (started, already_running) where:
      started        — the profile string if we brought it up, else None
      already_running — True if it was already running before we were called
    """
    _env_write("DEV_KEYCLOAK", "true")
    started = _compose_up_profile("keycloak", _DOCKER_CONTAINER_KEYCLOAK, "Keycloak")
    already_running = (
        started is None
        and _docker_container_status(_DOCKER_CONTAINER_KEYCLOAK) == "running"
    )
    return started, already_running


def docker_keycloak_oauth() -> None:
    os.system("cls" if os.name == "nt" else "clear")  # nosec B605
    print("=== DOCKER: Keycloak (OAuth) ===\n")

    if not _docker_available():
        print(f"{RED}Docker not found. Install Docker Desktop and try again.{RESET}")
        pause()
        return

    provider_name = _prompt("Provider name", "Keycloak (Dev)")
    oauth_client_id = _prompt("OAuth Client ID", "resource-planner-oauth")
    oauth_client_secret = _prompt("OAuth Client Secret", "dev-oauth-secret")

    lan_ip = _get_local_ip()
    _generate_realm_export(
        lan_ip=lan_ip,
        oauth_client_id=oauth_client_id,
        oauth_client_secret=oauth_client_secret,
    )
    _env_write("KEYCLOAK_HOSTNAME", lan_ip)

    print()
    if _docker_container_status(_DOCKER_CONTAINER_KEYCLOAK) == "running":
        _compose_down_profile("keycloak", "Keycloak")

    started, already_running = _keycloak_start()

    if started is None and not already_running:
        _env_remove("DEV_KEYCLOAK")
        _env_remove("KEYCLOAK_HOSTNAME")
        pause()
        return

    kc_result = _wait_for_keycloak_ready(
        oauth_client_id=oauth_client_id,
        oauth_client_secret=oauth_client_secret,
    )

    if kc_result:
        _sync_keycloak_providers_in_db(*kc_result)

    sep = "─" * 62
    print(f"\n  {sep}")
    print(f"  {'OAuth Configuration (Keycloak)':^60}")
    print(f"  {sep}")

    if kc_result:
        oauth, _ = kc_result
        _display_keycloak_oauth_config(
            name=provider_name,
            client_id=str(oauth.get("client_id", "")),
            auth_endpoint=str(oauth.get("auth_endpoint", "")),
            token_endpoint=str(oauth.get("token_endpoint", "")),
            userinfo_endpoint=str(oauth.get("userinfo_endpoint", "")),
            scope=str(oauth.get("scope", "")),
        )
    else:
        print(f"  {YELLOW}Config unavailable — Keycloak may still be starting.{RESET}")
        print("  Use Django Tools → Keycloak Dev Config once it is ready.")

    print(f"  {sep}")
    print(f"  Admin Console : {_KEYCLOAK_URL}/admin  (admin / admin)")
    print("  Test User     : sso@example.com / Test1234!")

    started_services = []
    if started:
        started_services.append(
            ("keycloak", "Keycloak", ["DEV_KEYCLOAK", "KEYCLOAK_HOSTNAME"])
        )
    else:
        _env_remove("DEV_KEYCLOAK")
        _env_remove("KEYCLOAK_HOSTNAME")
        print(f"\n{YELLOW}  Container already running — not managed here.{RESET}")

    _docker_wait_and_cleanup(started_services)


def docker_keycloak_saml() -> None:
    os.system("cls" if os.name == "nt" else "clear")  # nosec B605
    print("=== DOCKER: Keycloak (SAML) ===\n")

    if not _docker_available():
        print(f"{RED}Docker not found. Install Docker Desktop and try again.{RESET}")
        pause()
        return

    provider_name = _prompt("Provider name", "Keycloak (Dev)")
    sp_entity_id = _prompt("SP Entity ID", "http://localhost:8000/sp")
    sp_assertion_url = _prompt(
        "Assertion Consumer URL",
        "http://localhost:8000/api/v1/auth/saml/acs/",
    )

    lan_ip = _get_local_ip()
    _generate_realm_export(
        lan_ip=lan_ip,
        sp_entity_id=sp_entity_id,
        sp_assertion_url=sp_assertion_url,
    )
    _env_write("KEYCLOAK_HOSTNAME", lan_ip)

    print()
    # Always bring the container down before starting so Keycloak reimports
    # realm-export.json on next boot. --import-realm is a no-op when the realm
    # already exists in the container's embedded storage, meaning redirectUri
    # and other realm changes are silently ignored without this step.
    if _docker_container_status(_DOCKER_CONTAINER_KEYCLOAK) == "running":
        _compose_down_profile("keycloak", "Keycloak")

    _env_write("DEV_KEYCLOAK", "true")
    started = _compose_up_profile("keycloak", _DOCKER_CONTAINER_KEYCLOAK, "Keycloak")

    if started is None:
        _env_remove("DEV_KEYCLOAK")
        pause()
        return

    kc_result = _wait_for_keycloak_ready()

    if kc_result:
        _sync_keycloak_providers_in_db(*kc_result)

    sep = "─" * 62
    print(f"\n  {sep}")
    print(f"  {'SAML Configuration (Keycloak)':^60}")
    print(f"  {sep}")

    if kc_result:
        _, saml = kc_result
        _display_keycloak_saml_config(
            name=provider_name,
            entity_id=str(saml.get("idp_entity_id", "")),
            sso_url=str(saml.get("idp_sso_url", "")),
            signing_data=str(saml.get("idp_x509_cert", "")),
            sp_entity_id=sp_entity_id,
            sp_assertion_url=sp_assertion_url,
        )
    else:
        print(f"  {YELLOW}Config unavailable — Keycloak may still be starting.{RESET}")
        print("  Use Django Tools → Keycloak Dev Config once it is ready.")

    print(f"\n  {sep}")
    print(f"  Admin Console : {_KEYCLOAK_URL}/admin  (admin / admin)")
    print("  Test User     : sso@example.com / Test1234!")

    _docker_wait_and_cleanup(
        [("keycloak", "Keycloak", ["DEV_KEYCLOAK", "KEYCLOAK_HOSTNAME"])]
    )


def docker_menu() -> None:
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605

        print("=== DOCKER ===")
        print("1. PostgreSQL")
        print("2. Email (Mailpit)")
        print("3. LocalStack")
        print("4. Keycloak (OAuth)")
        print("5. Keycloak (SAML)")
        print("0. Back")

        choice = input("\nSelect: ").strip()

        if choice == "1":
            docker_postgres()
        elif choice == "2":
            docker_email()
        elif choice == "3":
            docker_localstack()
        elif choice == "4":
            docker_keycloak_oauth()
        elif choice == "5":
            docker_keycloak_saml()
        elif choice == "0":
            return
        else:
            print(f"{YELLOW}Invalid choice{RESET}")
            pause()


# ---------------------------------------------------------------------------
# Menus
# ---------------------------------------------------------------------------


def run_test_tracker():
    host = _get_local_ip()
    print("\nTest Tracker available at:")
    print(f"  http://localhost:{TEST_TRACKER_PORT}")
    print(f"  http://{host}:{TEST_TRACKER_PORT}")
    run("python server.py", cwd=TEST_TRACKER_DIR)
    pause()


def _venv_ruff() -> str:
    if os.name == "nt":
        return str(ROOT / "venv" / "Scripts" / "ruff.exe")
    return str(ROOT / "venv" / "bin" / "ruff")


def run_ruff_fix():
    print("\nRunning ruff check --fix...")
    run(f'"{_venv_ruff()}" check . --fix')
    print("\nRunning ruff format...")
    run(f'"{_venv_ruff()}" format .')
    pause()


def auto_fix_menu():
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605

        print("=== AUTO-FIX ===")
        print("1. Ruff")
        print("0. Back")

        choice = input("\nSelect: ").strip()

        if choice == "1":
            run_ruff_fix()
        elif choice == "0":
            return
        else:
            print(f"{YELLOW}Invalid choice{RESET}")
            pause()


def django_menu():
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605

        print("=== DJANGO MENU ===")
        print("1. Make Migrations")
        print("2. Migrate")
        print("3. Run Server")
        print("4. Reset Setup")
        print("5. SQL Query Runner")
        print("6. Keycloak Dev Config")
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
        elif choice == "6":
            configure_keycloak()
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
        print("4. Install Requirements")
        print("5. Run Tests")
        print("6. Tools / Test Tracker")
        print("7. Docker")
        print("8. Auto-Fix")
        print("0. Exit")

        choice = input("\nSelect: ")

        if choice == "1":
            clean_pycache()
        elif choice == "2":
            run_precommit()
        elif choice == "3":
            django_menu()
        elif choice == "4":
            install_requirements()
        elif choice == "5":
            run_tests()
        elif choice == "6":
            run_test_tracker()
        elif choice == "7":
            docker_menu()
        elif choice == "8":
            auto_fix_menu()
        elif choice == "0":
            sys.exit(0)
        else:
            print(f"{YELLOW}Invalid choice{RESET}")
            pause()


if __name__ == "__main__":
    main_menu()
