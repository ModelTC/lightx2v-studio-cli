from __future__ import annotations

import argparse
import json
import time
from typing import Any

from lightx2v.cli.commands._task_ops import with_client
from lightx2v.cli.common_args import add_json_flag, add_quiet_flag
from lightx2v.cli.json_util import load_json_arg
from lightx2v.cli.media import file_to_data_url


TERMINAL_STATUSES = {"succeeded", "failed", "cancelled"}


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("workflow", help="List, create, run, and inspect workflows")
    nested = parser.add_subparsers(dest="workflow_command", required=True)

    list_cmd = nested.add_parser("list", help="List workflows")
    list_cmd.add_argument(
        "--public",
        action="store_true",
        help="Legacy compatibility flag; API keys only list workflows owned by the account",
    )
    list_cmd.add_argument("--search", help="Search keyword")
    list_cmd.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    list_cmd.add_argument("--page-size", type=int, default=10, help="Page size (default: 10)")
    add_json_flag(list_cmd)
    add_quiet_flag(list_cmd)
    list_cmd.set_defaults(handler=handle_list)

    get = nested.add_parser("get", help="Get workflow JSON")
    get.add_argument("workflow_id", help="Workflow ID")
    add_json_flag(get)
    add_quiet_flag(get)
    get.set_defaults(handler=handle_get)

    inputs = nested.add_parser("inputs", help="Describe inputs required for a workflow run")
    inputs.add_argument("workflow_id", help="Workflow ID")
    inputs.add_argument("--mode", choices=["full", "single", "downstream", "upstream"], default="full")
    inputs.add_argument("--node-id", action="append", dest="node_ids", help="Node ID in the requested run scope; repeatable")
    inputs.add_argument("--no-include-upstream", action="store_true", help="Do not include upstream dependencies")
    add_json_flag(inputs)
    add_quiet_flag(inputs)
    inputs.set_defaults(handler=handle_inputs)

    create = nested.add_parser("create", help="Create a workflow from JSON")
    create.add_argument("--input", required=True, help="Workflow body JSON or @file.json")
    add_json_flag(create)
    add_quiet_flag(create)
    create.set_defaults(handler=handle_create)

    run = nested.add_parser("run", help="Start a workflow run")
    run.add_argument("workflow_id", help="Workflow ID")
    run.add_argument("--mode", choices=["full", "single", "downstream", "upstream"], default="full")
    run.add_argument("--node-id", action="append", dest="node_ids", help="Node ID to run; repeatable")
    run.add_argument("--no-include-upstream", action="store_true", help="Do not include upstream nodes")
    run.add_argument("--inputs", help="Run inputs JSON or @file.json, keyed by input node_id")
    run.add_argument("--input-file", action="append", default=[], metavar="NODE_ID=PATH", help="Bind a local media file to an input node; repeatable")
    run.add_argument("--save-as-default", action="store_true", help="Persist inputs as workflow defaults")
    run.add_argument("--poll", action="store_true", help="Poll until terminal status")
    run.add_argument("--poll-interval", type=float, default=2.0, help="Seconds between polls (default: 2)")
    run.add_argument("--timeout", type=float, default=600.0, help="Max seconds to poll (default: 600)")
    add_json_flag(run)
    add_quiet_flag(run)
    run.set_defaults(handler=handle_run)

    runs = nested.add_parser("runs", help="List runs for a workflow")
    runs.add_argument("workflow_id", help="Workflow ID")
    runs.add_argument("--status", choices=["running"], help="Only list active runs")
    add_json_flag(runs)
    add_quiet_flag(runs)
    runs.set_defaults(handler=handle_runs)

    status = nested.add_parser("status", help="Get workflow run status")
    status.add_argument("workflow_id", help="Workflow ID")
    status.add_argument("run_id", help="Run ID")
    add_json_flag(status)
    add_quiet_flag(status)
    status.set_defaults(handler=handle_status)

    stream = nested.add_parser("stream", help="Stream workflow run events over SSE")
    stream.add_argument("workflow_id", help="Workflow ID")
    stream.add_argument("run_id", help="Run ID")
    add_json_flag(stream)
    add_quiet_flag(stream)
    stream.set_defaults(handler=handle_stream)

    outputs = nested.add_parser("outputs", help="Get workflow run final outputs")
    outputs.add_argument("workflow_id", help="Workflow ID")
    outputs.add_argument("run_id", help="Run ID")
    add_json_flag(outputs)
    add_quiet_flag(outputs)
    outputs.set_defaults(handler=handle_outputs)

    cancel = nested.add_parser("cancel", help="Cancel a workflow run")
    cancel.add_argument("workflow_id", help="Workflow ID")
    cancel.add_argument("run_id", help="Run ID")
    add_json_flag(cancel)
    add_quiet_flag(cancel)
    cancel.set_defaults(handler=handle_cancel)

    cancel_node = nested.add_parser("cancel-node", help="Cancel one node and dependent downstream work")
    cancel_node.add_argument("workflow_id", help="Workflow ID")
    cancel_node.add_argument("run_id", help="Run ID")
    cancel_node.add_argument("node_id", help="Node ID")
    add_json_flag(cancel_node)
    add_quiet_flag(cancel_node)
    cancel_node.set_defaults(handler=handle_cancel_node)


def _print(args: argparse.Namespace, console, payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.json:
        print(text)
    else:
        console.println(text)


def _body_from_json_arg(value: str | None) -> dict:
    if not value:
        return {}
    body = load_json_arg(value)
    if not isinstance(body, dict):
        raise ValueError("JSON value must be an object")
    return body


def _parse_input_file(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise ValueError("--input-file must use NODE_ID=PATH")
    node_id, path = value.split("=", 1)
    node_id = node_id.strip()
    path = path.strip()
    if not node_id or not path:
        raise ValueError("--input-file must use NODE_ID=PATH")
    return node_id, path


def handle_list(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        data = client.list_workflows(page=args.page, page_size=args.page_size, public=args.public, search=args.search)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        workflows = data.get("workflows") or []
        if not workflows:
            console.println("No workflows found.")
            return 0
        headers = ("workflow_id", "name", "visibility")
        rows = [(str(w.get("workflow_id") or ""), str(w.get("name") or ""), str(w.get("visibility") or "")) for w in workflows]
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], min(len(cell), 60))
        fmt = "  ".join(f"{{:{w}}}" for w in widths)
        console.println(fmt.format(*headers))
        console.println(fmt.format(*("-" * w for w in widths)))
        for row in rows:
            console.println(fmt.format(*(cell[:60] for cell in row)))
        return 0

    return with_client(args, _run)


def handle_get(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        _print(args, console, client.get_workflow(args.workflow_id))
        return 0

    return with_client(args, _run)


def handle_inputs(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        data = client.get_workflow_inputs(
            args.workflow_id,
            mode=args.mode,
            node_ids=args.node_ids,
            include_upstream=not args.no_include_upstream,
        )
        _print(args, console, data)
        return 0

    return with_client(args, _run)


def handle_create(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        body = _body_from_json_arg(args.input)
        _print(args, console, client.create_workflow(body))
        return 0

    return with_client(args, _run)


def _run_body(args: argparse.Namespace) -> dict:
    body: dict[str, Any] = {
        "mode": args.mode,
        "include_upstream": not args.no_include_upstream,
        "save_as_default": bool(args.save_as_default),
    }
    if args.node_ids:
        body["node_ids"] = args.node_ids
    inputs = _body_from_json_arg(args.inputs) if args.inputs else {}
    for item in args.input_file:
        node_id, path = _parse_input_file(item)
        inputs[node_id] = file_to_data_url(path)
    if inputs:
        body["inputs"] = inputs
    return body


def handle_run(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        data = client.start_workflow_run(args.workflow_id, _run_body(args))
        if not args.poll:
            _print(args, console, data)
            return 0
        run_id = data.get("run_id")
        if not run_id:
            _print(args, console, data)
            return 1
        deadline = time.time() + args.timeout
        current = data
        while time.time() < deadline:
            current = client.get_workflow_run(args.workflow_id, run_id)
            status = str(current.get("status") or "").lower()
            if not args.json and not args.quiet:
                console.println(f"status: {status}")
            if status in TERMINAL_STATUSES:
                break
            time.sleep(max(args.poll_interval, 0.05))
        _print(args, console, current)
        return 0 if str(current.get("status") or "").lower() == "succeeded" else 1

    return with_client(args, _run)


def handle_status(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        _print(args, console, client.get_workflow_run(args.workflow_id, args.run_id))
        return 0

    return with_client(args, _run)


def handle_runs(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        _print(args, console, client.list_workflow_runs(args.workflow_id, status=args.status))
        return 0

    return with_client(args, _run)


def handle_stream(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        for event in client.stream_workflow_run(args.workflow_id, args.run_id):
            if args.json:
                print(json.dumps(event, ensure_ascii=False))
            elif not args.quiet:
                console.println(f"{event['event']}: {json.dumps(event['data'], ensure_ascii=False)}")
        return 0

    return with_client(args, _run)


def handle_outputs(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        _print(args, console, client.get_workflow_run_outputs(args.workflow_id, args.run_id))
        return 0

    return with_client(args, _run)


def handle_cancel(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        _print(args, console, client.cancel_workflow_run(args.workflow_id, args.run_id))
        return 0

    return with_client(args, _run)


def handle_cancel_node(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        _print(
            args,
            console,
            client.cancel_workflow_run_node(args.workflow_id, args.run_id, args.node_id),
        )
        return 0

    return with_client(args, _run)
