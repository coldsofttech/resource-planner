from ..constants import TEST_TRACKER_DIR, TEST_TRACKER_PORT
from ..core.shell import pause, run
from ..modules.keycloak import _get_local_ip


def run_test_tracker():
    host = _get_local_ip()
    print("\nTest Tracker available at:")
    print(f"  http://localhost:{TEST_TRACKER_PORT}")
    print(f"  http://{host}:{TEST_TRACKER_PORT}")
    run("python server.py", cwd=TEST_TRACKER_DIR)
    pause()
