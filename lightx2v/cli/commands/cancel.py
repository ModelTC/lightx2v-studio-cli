from __future__ import annotations

import argparse
import json

from lightx2v.cli.commands._task_ops import with_client
from lightx2v.cli.common_args import add_json_flag, add_quiet_flag, add_task_id_arg


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("cancel", help="Cancel a running task")
    add_task_id_arg(parser)
    add_json_flag(parser)
    add_quiet_flag(parser)
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        data = client.cancel(args.task_id)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            console.println(data.get("msg", json.dumps(data)))
        return 0

    return with_client(args, _run)
