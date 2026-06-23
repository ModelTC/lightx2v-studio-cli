from __future__ import annotations

import argparse
import json
from pathlib import Path

from lightx2v.cli.commands._task_ops import with_client
from lightx2v.cli.common_args import add_json_flag, add_quiet_flag, add_task_id_arg
from lightx2v.cli.output import infer_output_name


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("result", help="Get result download URL for a succeeded task")
    add_task_id_arg(parser)
    parser.add_argument("--name", help="Output name: output_video or output_image (auto-detect if omitted)")
    parser.add_argument("-o", "--output", help="Download to this file path")
    add_json_flag(parser)
    add_quiet_flag(parser)
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        task = client.query(args.task_id)
        if task.get("status") != "SUCCEED":
            console.println(f"task status is {task.get('status')}, not SUCCEED")
            return 1
        name = args.name
        if not name:
            outputs = task.get("outputs") or {}
            if "output_image" in outputs:
                name = "output_image"
            elif "output_video" in outputs:
                name = "output_video"
            else:
                name = infer_output_name(task.get("task_type", ""), task.get("params"))
        result = client.result_url(args.task_id, name)
        url = result.get("url")
        payload = {"task_id": args.task_id, "name": name, "url": url}
        if args.output and url:
            content = client.download(url)
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(content)
            payload["saved"] = str(out.resolve())
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            console.println(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    return with_client(args, _run)
