import subprocess  # nosec B404

from ..constants import RED, RESET, ROOT, YELLOW


def run(cmd, cwd=ROOT):
    """Run shell command safely."""
    print(f"\n>>> {cmd}\n")
    result = subprocess.run(cmd, shell=True, cwd=cwd)  # nosec B602  # nosemgrep

    if result.returncode != 0:
        print(f"{RED}\nCommand failed: {cmd}{RESET}")

    return result.returncode


_PYTEST_NO_TESTS = 5  # pytest exit code when no tests are collected


def _run_pytest(cmd: str) -> int:
    """Run a pytest command; exit code 5 (no tests collected) is treated as success."""
    print(f"\n>>> {cmd}\n")
    result = subprocess.run(cmd, shell=True, cwd=ROOT)  # nosec B602  # nosemgrep
    rc = result.returncode
    if rc == _PYTEST_NO_TESTS:
        print(f"{YELLOW}No tests collected — skipping.{RESET}")
        return 0
    if rc != 0:
        print(f"{RED}\nCommand failed: {cmd}{RESET}")
    return rc


def pause():
    input("\nPlease enter to continue...")
