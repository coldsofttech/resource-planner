import os
import sys

from .constants import RESET, YELLOW
from .core.shell import pause
from .modules.autofix import auto_fix_menu, run_ruff_fix
from .modules.cleanup import (
    clean_all,
    clean_dev_cache,
    clean_logs,
    clean_mypy,
    clean_node_modules,
    clean_pycache,
    clean_pytest,
    clean_pytest_reports,
    clean_ruff,
    cleanup_menu,
)
from .modules.django_tools import (
    django_menu,
    install_requirements,
    makemigrations,
    migrate,
    reset_setup,
    runserver,
)
from .modules.docker import (
    docker_email,
    docker_keycloak_oauth,
    docker_keycloak_saml,
    docker_localstack,
    docker_menu,
    docker_postgres,
)
from .modules.keycloak import configure_keycloak
from .modules.precommit import run_precommit
from .modules.sql import sql_query_runner
from .modules.tests import (
    _run_django_integration_tests,
    _run_django_tests,
    _run_django_tests_menu,
    _run_django_unit_tests,
    _run_package_integration_tests,
    _run_package_tests,
    _run_package_unit_tests,
    _run_packages_tests_menu,
    run_tests,
)
from .modules.tracker import run_test_tracker

MENU_TREE = {
    "1": {
        "label": "Cleanup",
        "action": cleanup_menu,
        "children": {
            "1": {"label": "All", "action": clean_all},
            "2": {"label": "Python Cache (__pycache__)", "action": clean_pycache},
            "3": {"label": "Mypy Cache (.mypy_cache)", "action": clean_mypy},
            "4": {"label": "Pytest Cache (.pytest_cache)", "action": clean_pytest},
            "5": {"label": "Ruff Cache (.ruff_cache)", "action": clean_ruff},
            "6": {"label": "Dev Cache (.dev-cache)", "action": clean_dev_cache},
            "7": {
                "label": "Pytest Reports (.pytest-reports)",
                "action": clean_pytest_reports,
            },
            "8": {"label": "Logs (.logs)", "action": clean_logs},
            "9": {
                "label": "Node Modules (clean + install)",
                "action": clean_node_modules,
            },
        },
    },
    "2": {"label": "Pre-Commit (all files)", "action": run_precommit},
    "3": {
        "label": "Django Tools",
        "action": django_menu,
        "children": {
            "1": {"label": "Make Migrations", "action": makemigrations},
            "2": {"label": "Migrate", "action": migrate},
            "3": {"label": "Run Server", "action": runserver},
            "4": {"label": "Reset Setup", "action": reset_setup},
            "5": {"label": "SQL Query Runner", "action": sql_query_runner},
            "6": {"label": "Keycloak Dev Config", "action": configure_keycloak},
        },
    },
    "4": {"label": "Install Requirements", "action": install_requirements},
    "5": {
        "label": "Run Tests",
        "action": run_tests,
        "children": {
            "1": {
                "label": "All",
                "action": lambda: (_run_django_tests(), _run_package_tests()),
            },
            "2": {
                "label": "Django (apps/web)",
                "action": _run_django_tests_menu,
                "children": {
                    "1": {"label": "All", "action": lambda: _run_django_tests()},
                    "2": {"label": "Unit", "action": lambda: _run_django_unit_tests()},
                    "3": {
                        "label": "Integration",
                        "action": lambda: _run_django_integration_tests(),
                    },
                },
            },
            "3": {
                "label": "Packages",
                "action": _run_packages_tests_menu,
                "children": {
                    "1": {"label": "All", "action": lambda: _run_package_tests()},
                    "2": {
                        "label": "Unit",
                        "action": lambda: _run_package_unit_tests(),
                    },
                    "3": {
                        "label": "Integration",
                        "action": lambda: _run_package_integration_tests(),
                    },
                },
            },
        },
    },
    "6": {"label": "Tools / Test Tracker", "action": run_test_tracker},
    "7": {
        "label": "Docker",
        "action": docker_menu,
        "children": {
            "1": {"label": "PostgreSQL", "action": docker_postgres},
            "2": {"label": "Email (Mailpit)", "action": docker_email},
            "3": {"label": "LocalStack", "action": docker_localstack},
            "4": {"label": "Keycloak (OAuth)", "action": docker_keycloak_oauth},
            "5": {"label": "Keycloak (SAML)", "action": docker_keycloak_saml},
        },
    },
    "8": {
        "label": "Auto-Fix",
        "action": auto_fix_menu,
        "children": {
            "1": {"label": "Ruff", "action": run_ruff_fix},
        },
    },
}


def main_menu():
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605

        print("=================================")
        print("        DEV CONTROL PANEL        ")
        print("=================================")
        print("1. Cleanup")
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
            cleanup_menu()
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
