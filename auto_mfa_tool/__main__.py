# SPDX-License-Identifier: Apache-2.0

import argparse

from . import gui, guide


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m auto_mfa_tool")
    parser.add_argument("--app", action="store_true", help="open the Auto-MFA annotation tool directly")
    args = parser.parse_args()
    if args.app:
        gui.main()
    else:
        guide.main()


if __name__ == "__main__":
    main()
