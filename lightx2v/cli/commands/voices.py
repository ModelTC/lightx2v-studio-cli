from __future__ import annotations

import argparse
import json

from lightx2v.cli.commands._task_ops import with_client
from lightx2v.cli.common_args import add_json_flag


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("voices", help="List built-in TTS voices")
    parser.add_argument("--version", default="all", help="Voice version filter, e.g. 2.0 (default: all)")
    parser.add_argument("--fields", choices=["all", "card"], default="card", help="Payload field set (default: card)")
    parser.add_argument("--limit", type=int, default=20, help="Rows to print in table mode (default: 20)")
    add_json_flag(parser)
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        data = client.list_voices(version=args.version, fields=args.fields)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0

        speakers = data.get("Speakers") or []
        if not speakers:
            console.println("No voices found.")
            return 0

        rows = []
        for speaker in speakers[: max(args.limit, 0)]:
            rows.append(
                (
                    str(speaker.get("Name") or ""),
                    str(speaker.get("VoiceType") or ""),
                    str(speaker.get("ResourceID") or ""),
                    str(speaker.get("Gender") or ""),
                    str(speaker.get("Age") or ""),
                )
            )
        headers = ("name", "voice_type", "resource_id", "gender", "age")
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(cell))
        fmt = "  ".join(f"{{:{w}}}" for w in widths)
        console.println(fmt.format(*headers))
        console.println(fmt.format(*("-" * w for w in widths)))
        for row in rows:
            console.println(fmt.format(*row))
        total = data.get("Total", len(speakers))
        if len(speakers) > len(rows):
            console.println(f"... showing {len(rows)} of {total}; use --json or --limit for more")
        return 0

    return with_client(args, _run)
