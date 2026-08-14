from __future__ import annotations

import argparse
import json
import sys

from lightx2v.cli.client import ApiError, LightX2VClient
from lightx2v.cli.config import resolve_config


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("models", help="List available models")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    try:
        config = resolve_config()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        with LightX2VClient(config, notify_updates=not args.json) as client:
            data = client.list_models()
    except ApiError as exc:
        print(f"Error [{exc.status_code}]: {exc.message}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0

    models = data.get("models", [])
    if not models:
        print("No models found.")
        return 0

    headers = ("task", "model_cls", "stage", "supported_plans")
    rows = [
        (
            m.get("task", ""),
            m.get("model_cls", ""),
            m.get("stage", ""),
            ",".join(m.get("supported_plans", [])),
        )
        for m in models
    ]
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    fmt = "  ".join(f"{{:{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))
    for row in rows:
        print(fmt.format(*row))
    return 0
