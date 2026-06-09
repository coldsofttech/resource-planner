"""Run pytest treating exit code 5 (no tests collected) as success."""

import subprocess
import sys

result = subprocess.run([sys.executable, "-m", "pytest"] + sys.argv[1:])
sys.exit(0 if result.returncode == 5 else result.returncode)
