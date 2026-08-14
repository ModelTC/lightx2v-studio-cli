from __future__ import annotations

import argparse
import os
import subprocess
import sys
from urllib.request import Request, urlopen

from lightx2v import __version__

DEFAULT_INSTALL_URL = "https://raw.githubusercontent.com/ModelTC/lightx2v-studio-cli/main/install.sh"


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("update", help="Update the LightX2V CLI")
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    url = (os.getenv("LIGHTX2V_CLI_UPDATE_URL") or DEFAULT_INSTALL_URL).strip()
    if not url.startswith("https://"):
        print("Error: LIGHTX2V_CLI_UPDATE_URL must use HTTPS.", file=sys.stderr)
        return 1
    print(f"Updating LightX2V CLI {__version__}...")
    try:
        request = Request(url, headers={"User-Agent": f"lightx2v-cli/{__version__}"})
        with urlopen(request, timeout=30) as response:
            script = response.read().decode("utf-8")
        result = subprocess.run(["bash"], input=script, text=True, check=False)
    except (OSError, UnicodeError) as exc:
        print(f"Update failed: {exc}", file=sys.stderr)
        return 1
    return int(result.returncode)
