import os
from pathlib import Path

from ..constants import RESET, ROOT, YELLOW
from ..core.shell import pause


def _remove_dir(path: Path) -> int:
    """Recursively remove a directory and return the count of items deleted."""
    count = 0
    for child in sorted(path.rglob("*"), reverse=True):
        try:
            if child.is_file():
                child.unlink()
                count += 1
            elif child.is_dir():
                child.rmdir()
        except Exception:  # nosec B110
            pass
    try:
        path.rmdir()
        count += 1
    except Exception:  # nosec B110
        pass
    return count


def clean_pycache():
    print("\nCleaning __pycache__...")
    total = 0
    for path in ROOT.rglob("__pycache__"):
        if path.is_dir():
            total += _remove_dir(path)
    print(f"Done — {total} item(s) removed.")
    pause()


def clean_mypy():
    print("\nCleaning .mypy_cache...")
    total = 0
    for path in ROOT.rglob(".mypy_cache"):
        if path.is_dir():
            total += _remove_dir(path)
    print(f"Done — {total} item(s) removed.")
    pause()


def clean_pytest():
    print("\nCleaning .pytest_cache...")
    total = 0
    for path in ROOT.rglob(".pytest_cache"):
        if path.is_dir():
            total += _remove_dir(path)
    print(f"Done — {total} item(s) removed.")
    pause()


def clean_ruff():
    print("\nCleaning .ruff_cache...")
    total = 0
    for path in ROOT.rglob(".ruff_cache"):
        if path.is_dir():
            total += _remove_dir(path)
    print(f"Done — {total} item(s) removed.")
    pause()


def cleanup_menu():
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605

        print("=== CLEANUP ===")
        print("1. Python Cache (__pycache__)")
        print("2. Mypy Cache (.mypy_cache)")
        print("3. Pytest Cache (.pytest_cache)")
        print("4. Ruff Cache (.ruff_cache)")
        print("0. Back")

        choice = input("\nSelect: ").strip()

        if choice == "1":
            clean_pycache()
        elif choice == "2":
            clean_mypy()
        elif choice == "3":
            clean_pytest()
        elif choice == "4":
            clean_ruff()
        elif choice == "0":
            return
        else:
            print(f"{YELLOW}Invalid choice{RESET}")
            pause()
