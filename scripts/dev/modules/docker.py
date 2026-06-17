import collections
import getpass
import os
import subprocess  # nosec B404
import time

from ..constants import GREEN, RED, RESET, ROOT, YELLOW
from ..core.env import _env_remove, _env_write, _load_env_defaults, _prompt
from ..core.parallel import _ANSI_RE
from ..modules.keycloak import (
    _DOCKER_CONTAINER_KEYCLOAK,
    _KEYCLOAK_URL,
    _display_keycloak_oauth_config,
    _display_keycloak_saml_config,
    _generate_realm_export,
    _get_local_ip,
    _sync_keycloak_providers_in_db,
    _wait_for_keycloak_ready,
)

_DOCKER_CONTAINER_PG = "resource-planner-dev-pg"
_DOCKER_CONTAINER_MAILPIT = "resource-planner-dev-mailpit"
_DOCKER_CONTAINER_LOCALSTACK = "resource-planner-dev-localstack"
_LOCALSTACK_ENDPOINT = "http://localhost:4566"
_COMPOSE_ENV_FILE = str(ROOT / "apps" / "web" / ".env")


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
    from ..constants import WEB_DIR

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


def _docker_wait_and_cleanup(started_services: list) -> None:
    """Block until Ctrl+C, then stop any services we started."""
    from ..core.shell import pause

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


def docker_postgres() -> None:
    os.system("cls" if os.name == "nt" else "clear")  # nosec B605
    print("=== DOCKER: PostgreSQL ===\n")

    if not _docker_available():
        print(f"{RED}Docker not found. Install Docker Desktop and try again.{RESET}")
        from ..core.shell import pause

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
        from ..core.shell import pause

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
        from ..core.shell import pause

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
        from ..core.shell import pause

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
        from ..core.shell import pause

        pause()
        return

    started = _compose_up_profile("aws", _DOCKER_CONTAINER_LOCALSTACK, "LocalStack")
    already_running = (
        started is None
        and _docker_container_status(_DOCKER_CONTAINER_LOCALSTACK) == "running"
    )

    if started is None and not already_running:
        from ..core.shell import pause

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
        from ..core.shell import pause

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
        from ..core.shell import pause

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
        from ..core.shell import pause

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
        from ..core.shell import pause

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
    from ..core.shell import pause

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
