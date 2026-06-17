import os

from ..constants import RESET, ROOT, YELLOW
from ..core.shell import pause, run


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
