import collections
import os
import re
import subprocess  # nosec B404
import sys

from ..constants import RED, RESET, ROOT, WEB_DIR, YELLOW
from ..core.cache import _needs_run, _record_run
from ..core.env import _env_remove, _env_write
from ..core.parallel import (
    _ANSI_RE,
    _run_cmd_buffered,
    _run_parallel_columns,
    _run_tab_view,
)
from ..core.shell import pause, run
from ..modules.docker import (
    _DOCKER_CONTAINER_LOCALSTACK,
    _DOCKER_CONTAINER_MAILPIT,
    _DOCKER_CONTAINER_PG,
    _LOCALSTACK_ENDPOINT,
    _compose_down_profile,
    _compose_up_profile_buffered,
    _docker_container_status,
    _get_keycloak_docker_config,
    _get_localstack_docker_config,
    _get_postgres_docker_config,
    _get_smtp_docker_config,
)
from ..modules.keycloak import (
    _DOCKER_CONTAINER_KEYCLOAK,
    _generate_realm_export,
    _get_local_ip,
)


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


def install_requirements():
    print("\nInstalling requirements...")
    rc = _install_requirements()
    if rc == 0:
        print("Requirements installed successfully.")
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

    from ..constants import TEST_TRACKER_DIR, TEST_TRACKER_PORT

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


def django_menu():
    from ..modules.keycloak import configure_keycloak
    from ..modules.sql import sql_query_runner

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
