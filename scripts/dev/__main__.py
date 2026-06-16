import argparse
import sys
from collections.abc import Callable
from typing import Any


def _run_options(options: list[str]) -> None:
    """Navigate the MENU_TREE non-interactively using a list of option numbers."""
    from .menu import MENU_TREE

    node: dict[str, Any] = MENU_TREE
    action: Callable[[], None] | None = None
    for opt in options:
        entry = node.get(opt)
        if entry is None:
            print(f"Invalid option: {opt}")
            sys.exit(1)
        action = entry["action"]
        node = entry.get("children", {})
    if action is not None:
        action()


def main() -> None:
    parser = argparse.ArgumentParser(prog="rplanner-dev")
    parser.add_argument(
        "--options",
        "-o",
        nargs="+",
        metavar="N",
        help="Navigate menu options non-interactively (e.g. --options 1 2)",
    )
    args = parser.parse_args()
    if args.options:
        from .core import shell as _shell

        _shell.non_interactive = True
        _run_options(args.options)
    else:
        from .menu import main_menu

        main_menu()


if __name__ == "__main__":
    main()
