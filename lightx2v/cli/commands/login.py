from __future__ import annotations

import argparse
import getpass

from lightx2v.cli.config import DEFAULT_BASE_URL, mask_api_key, save_config_file


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("login", help="Save API key and base URL to local config")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"API base URL (default: {DEFAULT_BASE_URL})")
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    print("Get your API key at https://x2v.light-ai.top (profile menu → API Key).")
    api_key = getpass.getpass("API Key (apikey_...): ").strip()
    if not api_key:
        print("Error: API key is required.")
        return 1
    if not api_key.startswith("apikey_"):
        print("Warning: API key usually starts with apikey_")
    base_url = args.base_url.rstrip("/")
    save_config_file(base_url, api_key)
    print(f"Saved config to ~/.config/lightx2v/config.json")
    print(f"base_url: {base_url}")
    print(f"api_key:  {mask_api_key(api_key)}")
    return 0
