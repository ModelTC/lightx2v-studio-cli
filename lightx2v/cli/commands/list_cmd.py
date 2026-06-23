from __future__ import annotations

import argparse
import json

from lightx2v.cli.commands._task_ops import with_client
from lightx2v.cli.common_args import add_json_flag, add_quiet_flag


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("list", help="List tasks with pagination")
    parser.add_argument("--status", default="ALL", help="Status filter: ALL, SUCCEED, RUNNING, etc.")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=10)
    add_json_flag(parser)
    add_quiet_flag(parser)
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        data = client.list_tasks(page=args.page, page_size=args.page_size, status=args.status)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        tasks = data.get("tasks", [])
        pagination = data.get("pagination", {})
        for task in tasks:
            print(f"{task.get('task_id')}  {task.get('status')}  {task.get('task_type')}  {task.get('model_cls')}")
        print(
            f"page {pagination.get('page')}/{pagination.get('total_pages')} "
            f"(total {pagination.get('total')})"
        )
        return 0

    return with_client(args, _run)
