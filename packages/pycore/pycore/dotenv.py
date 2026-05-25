from __future__ import annotations

import os
from pathlib import Path


class DotEnv:
    """Read/write a .env file rooted at a given folder."""

    def __init__(self, folder: Path | str):
        self._path = Path(folder) / ".env"

    def list(self) -> dict[str, str]:
        """Return all key-value pairs from the .env file."""
        if not self._path.exists():
            return {}
        result: dict[str, str] = {}
        with open(self._path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                result[key.strip()] = val.strip().strip('"').strip("'")
        return result

    def read(self, key: str) -> str | None:
        """Return the value for *key*, or None if absent."""
        return self.list().get(key)

    def write(self, key: str, value: str) -> None:
        """Set or update *key* in the .env file (creates the file if needed)."""
        lines: list[str] = []
        if self._path.exists():
            with open(self._path, encoding="utf-8") as fh:
                lines = fh.readlines()

        updated = False
        new_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                new_lines.append(line)
                continue
            k, _, _ = stripped.partition("=")
            if k.strip() == key:
                new_lines.append(f"{key}={value}\n")
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines.append("\n")
            new_lines.append(f"{key}={value}\n")

        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as fh:
            fh.writelines(new_lines)

    def delete(self, key: str) -> bool:
        """Remove *key* from the .env file. Returns True if the key was present."""
        if not self._path.exists():
            return False
        with open(self._path, encoding="utf-8") as fh:
            lines = fh.readlines()
        new_lines = []
        removed = False
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                k, _, _ = stripped.partition("=")
                if k.strip() == key:
                    removed = True
                    continue
            new_lines.append(line)
        if removed:
            with open(self._path, "w", encoding="utf-8") as fh:
                fh.writelines(new_lines)
        return removed

    def load_environ(self) -> None:
        """Load all keys into os.environ (existing values are not overwritten)."""
        for key, value in self.list().items():
            os.environ.setdefault(key, value)
