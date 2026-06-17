from ..constants import WEB_DIR


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


def _prompt(label, default=""):
    """Prompt with an optional default shown in brackets."""
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default
