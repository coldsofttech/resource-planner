import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "apps" / "web"
PACKAGES_DIR = ROOT / "packages"
REPORTS_DIR = ROOT / ".pytest-reports"
CACHE_DIR = ROOT / ".dev-cache"
TEST_TRACKER_DIR = ROOT / "tools" / "test-tracker"
TEST_TRACKER_PORT = 8001

_tty = sys.stdout.isatty()
YELLOW = "\033[93m" if _tty else ""
GREEN = "\033[92m" if _tty else ""
RED = "\033[91m" if _tty else ""
RESET = "\033[0m" if _tty else ""
