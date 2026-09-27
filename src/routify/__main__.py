"""python -m routify  →  launch desktop GUI (PyQt6)."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Routify navigation system")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run terminal CLI (CSV graph) instead of the desktop map UI",
    )
    args = parser.parse_args(argv)

    if args.cli:
        from routify.presentation.cli.main import main as cli_main

        return cli_main()

    from routify.presentation.gui.app_qt import main as gui_main

    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())
