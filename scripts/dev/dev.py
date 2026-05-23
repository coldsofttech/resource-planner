import os
import subprocess  # nosec B404
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "apps" / "web"


def run(cmd, cwd=ROOT):
    """Run shell command safely."""
    print("\n>>> %s\n", cmd)
    result = subprocess.run(cmd, shell=True, cwd=cwd)  # nosec B602

    if result.returncode != 0:
        print("\nCommand failed: %s", cmd)

    return result.returncode


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
    run("pre-commit run --all-files")
    pause()


def manage(cmd):
    return run(f"python manage.py {cmd}", cwd=WEB_DIR)


def makemigrations():
    manage("makemigrations")
    pause()


def migrate():
    manage("migrate")
    pause()


def runserver():
    run("npm run build:css")
    run("npm run build:js")
    manage("runserver")


def django_menu():
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605

        print("=== DJANGO MENU ===")
        print("1. Make Migrations")
        print("2. Migrate")
        print("3. Run Server")
        print("0. Back")

        choice = input("\nSelect: ")

        if choice == "1":
            makemigrations()
        elif choice == "2":
            migrate()
        elif choice == "3":
            runserver()
        elif choice == "0":
            return
        else:
            print("Invalid choice")
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
        print("0. Exit")

        choice = input("\nSelect: ")

        if choice == "1":
            clean_pycache()
        elif choice == "2":
            run_precommit()
        elif choice == "3":
            django_menu()
        elif choice == "0":
            sys.exit(0)
        else:
            print("Invalid choice")
            pause()


if __name__ == "__main__":
    main_menu()
