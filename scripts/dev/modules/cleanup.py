import os
from pathlib import Path

from ..constants import CACHE_DIR, LOGS_DIR, REPORTS_DIR, RESET, ROOT, YELLOW
from ..core.shell import pause, run


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


def clean_dev_cache():
    print("\nCleaning .dev-cache...")
    total = _remove_dir(CACHE_DIR) if CACHE_DIR.exists() else 0
    print(f"Done — {total} item(s) removed.")
    pause()


def clean_pytest_reports():
    print("\nCleaning .pytest-reports...")
    total = _remove_dir(REPORTS_DIR) if REPORTS_DIR.exists() else 0
    print(f"Done — {total} item(s) removed.")
    pause()


def clean_logs():
    print("\nCleaning .logs...")
    total = _remove_dir(LOGS_DIR) if LOGS_DIR.exists() else 0
    print(f"Done — {total} item(s) removed.")
    pause()


def clean_node_modules():
    node_modules = ROOT / "node_modules"
    print("\nCleaning node_modules...")
    total = _remove_dir(node_modules) if node_modules.exists() else 0
    print(f"Removed — {total} item(s) removed.")
    print("\nInstalling node_modules...")
    run("npm install", cwd=ROOT)
    pause()


def clean_all():
    print("\nRunning full cleanup...\n")

    print("  [1/8] __pycache__...")
    total = 0
    for path in ROOT.rglob("__pycache__"):
        if path.is_dir():
            total += _remove_dir(path)
    print(f"        Done — {total} item(s) removed.")

    print("  [2/8] .mypy_cache...")
    total = 0
    for path in ROOT.rglob(".mypy_cache"):
        if path.is_dir():
            total += _remove_dir(path)
    print(f"        Done — {total} item(s) removed.")

    print("  [3/8] .pytest_cache...")
    total = 0
    for path in ROOT.rglob(".pytest_cache"):
        if path.is_dir():
            total += _remove_dir(path)
    print(f"        Done — {total} item(s) removed.")

    print("  [4/8] .ruff_cache...")
    total = 0
    for path in ROOT.rglob(".ruff_cache"):
        if path.is_dir():
            total += _remove_dir(path)
    print(f"        Done — {total} item(s) removed.")

    print("  [5/8] .dev-cache...")
    total = _remove_dir(CACHE_DIR) if CACHE_DIR.exists() else 0
    print(f"        Done — {total} item(s) removed.")

    print("  [6/8] .pytest-reports...")
    total = _remove_dir(REPORTS_DIR) if REPORTS_DIR.exists() else 0
    print(f"        Done — {total} item(s) removed.")

    print("  [7/8] .logs...")
    total = _remove_dir(LOGS_DIR) if LOGS_DIR.exists() else 0
    print(f"        Done — {total} item(s) removed.")

    print("  [8/8] node_modules (clean + install)...")
    node_modules = ROOT / "node_modules"
    total = _remove_dir(node_modules) if node_modules.exists() else 0
    print(f"        Removed — {total} item(s) removed.")
    run("npm install", cwd=ROOT)

    print("\nFull cleanup complete.")
    pause()


def cleanup_menu():
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605

        print("=== CLEANUP ===")
        print("1. All")
        print("2. Python Cache (__pycache__)")
        print("3. Mypy Cache (.mypy_cache)")
        print("4. Pytest Cache (.pytest_cache)")
        print("5. Ruff Cache (.ruff_cache)")
        print("6. Dev Cache (.dev-cache)")
        print("7. Pytest Reports (.pytest-reports)")
        print("8. Logs (.logs)")
        print("9. Node Modules (clean + install)")
        print("0. Back")

        choice = input("\nSelect: ").strip()

        if choice == "1":
            clean_all()
        elif choice == "2":
            clean_pycache()
        elif choice == "3":
            clean_mypy()
        elif choice == "4":
            clean_pytest()
        elif choice == "5":
            clean_ruff()
        elif choice == "6":
            clean_dev_cache()
        elif choice == "7":
            clean_pytest_reports()
        elif choice == "8":
            clean_logs()
        elif choice == "9":
            clean_node_modules()
        elif choice == "0":
            return
        else:
            print(f"{YELLOW}Invalid choice{RESET}")
            pause()
