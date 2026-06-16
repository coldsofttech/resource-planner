import hashlib
from pathlib import Path

from ..constants import CACHE_DIR


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
