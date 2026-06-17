import os

from ..constants import PACKAGES_DIR, REPORTS_DIR, RESET, ROOT, YELLOW
from ..core.shell import _run_pytest, pause


def _html_flags(report_name: str) -> str:
    REPORTS_DIR.mkdir(exist_ok=True)
    return f"--html={REPORTS_DIR / report_name} --self-contained-html"


def _discover_package_test_dirs() -> list:
    """Return test directories for packages that have tests."""
    dirs = []
    for pkg in sorted(PACKAGES_DIR.iterdir()):
        if pkg.is_dir() and not pkg.name.startswith("."):
            tests_dir = pkg / "tests"
            if tests_dir.exists() and any(tests_dir.rglob("test_*.py")):
                dirs.append(tests_dir)
    return dirs


def _run_django_tests(path: str = "", report: str = "django-report.html") -> int:
    # --override-ini=addopts= clears the root pyproject.toml addopts (which sets
    # its own --html flag) so our explicit report name is the only one used.
    # --no-migrations creates tables directly from model state (syncdb-style) instead
    # of replaying every migration per worker — significantly faster for large schemas.
    cmd = (
        f"pytest -v -n auto --dist=loadfile --no-migrations --durations=30 "
        f"--override-ini=addopts= {_html_flags(report)}"
    )
    if path:
        cmd += f" {path}"
    return _run_pytest(cmd)


def _run_django_unit_tests(
    path: str = "", report: str = "django-unit-report.html"
) -> int:
    # Unit tests use SimpleTestCase (no DB) — dist=load gives pure load-balancing
    # without the file-grouping constraint that loadfile adds for DB isolation.
    cmd = (
        f"pytest -v -n auto --dist=load -m unit --durations=30 "
        f"--override-ini=addopts= {_html_flags(report)}"
    )
    if path:
        cmd += f" {path}"
    return _run_pytest(cmd)


def _run_django_integration_tests(
    path: str = "", report: str = "django-integration-report.html"
) -> int:
    # Integration tests hit the DB — loadfile keeps tests in the same file on the
    # same worker so they share DB state correctly.
    # --no-migrations creates tables directly from model state (syncdb-style) instead
    # of replaying every migration per worker — significantly faster for large schemas.
    cmd = (
        f"pytest -v -n auto --dist=loadfile -m integration --no-migrations "
        f"--durations=30 --override-ini=addopts= {_html_flags(report)}"
    )
    if path:
        cmd += f" {path}"
    return _run_pytest(cmd)


def _pkg_base_cmd(marker: str = "", report: str = "packages-report.html") -> str:
    # -p no:django disables pytest-django so packages can be collected in a single
    # pytest call regardless of which pyproject.toml becomes the rootdir.
    # --rootdir ensures packages/conftest.py is always discovered.
    html = _html_flags(report)
    marker_flag = f"-m {marker} " if marker else ""
    return (
        f"pytest -v -n auto --dist=loadfile {marker_flag}"
        f"-p no:django --override-ini=addopts= "
        f'--rootdir="{ROOT}" --import-mode=importlib {html}'
    )


def _run_package_tests(path: str = "", report: str = "packages-report.html") -> int:
    base = _pkg_base_cmd(report=report)
    if path:
        return _run_pytest(f"{base} {path}")
    test_dirs = _discover_package_test_dirs()
    if not test_dirs:
        print("No package test directories found.")
        return 0
    paths = " ".join(str(d) for d in test_dirs)
    return _run_pytest(f"{base} {paths}")


def _run_package_unit_tests(
    path: str = "", report: str = "packages-unit-report.html"
) -> int:
    # Unit tests have no external dependencies — use dist=load
    # (no file grouping needed).
    html = _html_flags(report)
    base = (
        f"pytest -v -n auto --dist=load -m unit "
        f"-p no:django --override-ini=addopts= "
        f'--rootdir="{ROOT}" --import-mode=importlib {html}'
    )
    if path:
        return _run_pytest(f"{base} {path}")
    test_dirs = _discover_package_test_dirs()
    if not test_dirs:
        print("No package test directories found.")
        return 0
    paths = " ".join(str(d) for d in test_dirs)
    return _run_pytest(f"{base} {paths}")


def _run_package_integration_tests(
    path: str = "", report: str = "packages-integration-report.html"
) -> int:
    html = _html_flags(report)
    base = (
        f"pytest -v -n auto --dist=loadfile -m integration "
        f"-p no:django --override-ini=addopts= "
        f'--rootdir="{ROOT}" --import-mode=importlib {html}'
    )
    if path:
        return _run_pytest(f"{base} {path}")
    test_dirs = _discover_package_test_dirs()
    if not test_dirs:
        print("No package test directories found.")
        return 0
    paths = " ".join(str(d) for d in test_dirs)
    return _run_pytest(f"{base} {paths}")


def _write_all_report_index(django_rc: int, packages_rc: int) -> None:
    """Write all-report.html — a simple index linking to both suite reports."""
    REPORTS_DIR.mkdir(exist_ok=True)
    django_status = "PASSED" if django_rc == 0 else "FAILED"
    packages_status = "PASSED" if packages_rc == 0 else "FAILED"
    overall = "PASSED" if django_rc == 0 and packages_rc == 0 else "FAILED"
    colour = "#2a9d2a" if overall == "PASSED" else "#c0392b"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>All Tests — {overall}</title>
  <style>
    body {{ font-family: sans-serif; padding: 2rem; background: #fafafa; }}
    h1 {{ color: {colour}; margin-bottom: 1.5rem; }}
    ul {{ list-style: none; padding: 0; }}
    li {{ margin: 0.6rem 0; }}
    a {{ font-size: 1.05rem; text-decoration: none; color: #1a73e8; }}
    a:hover {{ text-decoration: underline; }}
    .badge {{
      display: inline-block; margin-left: 0.6rem; padding: 0.15rem 0.5rem;
      border-radius: 3px; font-size: 0.8rem; font-weight: bold; color: #fff;
    }}
    .PASSED {{ background: #2a9d2a; }}
    .FAILED {{ background: #c0392b; }}
  </style>
</head>
<body>
  <h1>All Tests — {overall}</h1>
  <ul>
    <li>
      <a href="django-report.html">Django (apps/web)</a>
      <span class="badge {django_status}">{django_status}</span>
    </li>
    <li>
      <a href="packages-report.html">Packages</a>
      <span class="badge {packages_status}">{packages_status}</span>
    </li>
  </ul>
</body>
</html>"""
    report_path = REPORTS_DIR / "all-report.html"
    report_path.write_text(html, encoding="utf-8")
    print(f"\nReports written to {REPORTS_DIR}")
    print(f"  all-report.html      ({overall})")
    print(f"  django-report.html   ({django_status})")
    print(f"  packages-report.html ({packages_status})")


def _run_django_tests_menu() -> None:
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605
        print("=== RUN TESTS: DJANGO ===")
        print("1. All")
        print("2. Unit")
        print("3. Integration")
        print("0. Back")

        choice = input("\nSelect: ").strip()

        if choice == "1":
            path = input("Test path (blank = full suite): ").strip()
            _run_django_tests(path)
            pause()
        elif choice == "2":
            path = input("Test path (blank = all unit tests): ").strip()
            _run_django_unit_tests(path)
            pause()
        elif choice == "3":
            path = input("Test path (blank = all integration tests): ").strip()
            _run_django_integration_tests(path)
            pause()
        elif choice == "0":
            return
        else:
            print(f"{YELLOW}Invalid choice{RESET}")
            pause()


def _run_packages_tests_menu() -> None:
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605
        print("=== RUN TESTS: PACKAGES ===")
        print("1. All")
        print("2. Unit")
        print("3. Integration")
        print("0. Back")

        choice = input("\nSelect: ").strip()

        if choice == "1":
            path = input("Test path (blank = full suite): ").strip()
            _run_package_tests(path)
            pause()
        elif choice == "2":
            path = input("Test path (blank = all unit tests): ").strip()
            _run_package_unit_tests(path)
            pause()
        elif choice == "3":
            path = input("Test path (blank = all integration tests): ").strip()
            _run_package_integration_tests(path)
            pause()
        elif choice == "0":
            return
        else:
            print(f"{YELLOW}Invalid choice{RESET}")
            pause()


def run_tests():
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # nosec B605
        print("=== RUN TESTS ===")
        print("1. All")
        print("2. Django  (apps/web)")
        print("3. Packages")
        print("0. Back")

        choice = input("\nSelect: ").strip()

        if choice == "1":
            django_rc = _run_django_tests()
            packages_rc = _run_package_tests()
            _write_all_report_index(django_rc, packages_rc)
            pause()
        elif choice == "2":
            _run_django_tests_menu()
        elif choice == "3":
            _run_packages_tests_menu()
        elif choice == "0":
            return
        else:
            print(f"{YELLOW}Invalid choice{RESET}")
            pause()
