from ..core.shell import pause, run


def run_precommit():
    print("\nRunning pre-commit (all files)...")
    run("git add -A")
    run("pre-commit run --all-files")
    pause()
