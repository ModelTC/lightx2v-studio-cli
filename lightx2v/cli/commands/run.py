from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from lightx2v.cli.client import ApiError, LightX2VClient
from lightx2v.cli.common_args import add_json_flag, add_quiet_flag
from lightx2v.cli.config import resolve_config
from lightx2v.cli.console import CliConsole, Spinner
from lightx2v.cli.json_util import load_json_arg
from lightx2v.cli.media import file_to_base64_input
from lightx2v.cli.output import default_output_path, infer_output_name
from lightx2v.cli.payload import add_run_convenience_flags, apply_convenience_flags


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("run", help="Submit a task, poll until done, and download the result")
    parser.add_argument("target", help="Task and model in the form task/model_cls, e.g. t2i/Qwen-Image-2512")
    parser.add_argument("--input", help="Additional submit body fields as JSON or @file.json")
    parser.add_argument("--prompt", help="Prompt text (merged into submit body)")
    parser.add_argument("--image", help="Local image path (sets input_image as base64)")
    parser.add_argument("--video", help="Local video path (sets input_video as base64)")
    parser.add_argument("--audio", help="Local audio path (sets input_audio as base64)")
    add_run_convenience_flags(parser)
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--quote", action="store_true", help="Call billing/quote before submit")
    parser.add_argument("--poll-interval", type=float, default=2.0, help="Seconds between status polls (default: 2)")
    parser.add_argument("--timeout", type=float, default=600.0, help="Max seconds to wait for completion (default: 600)")
    parser.add_argument("--no-download", action="store_true", help="Only print result URL, do not download")
    parser.add_argument("--no-spinner", action="store_true", help="Disable polling spinner")
    add_json_flag(parser)
    add_quiet_flag(parser)
    parser.set_defaults(handler=handle)


def parse_target(target: str) -> tuple[str, str]:
    if "/" not in target:
        raise ValueError(f"Invalid target {target!r}; expected task/model_cls")
    task, model_cls = target.split("/", 1)
    task = task.strip()
    model_cls = model_cls.strip()
    if not task or not model_cls:
        raise ValueError(f"Invalid target {target!r}; expected task/model_cls")
    return task, model_cls


def build_submit_body(args: argparse.Namespace) -> dict[str, Any]:
    task, model_cls = parse_target(args.target)
    body: dict[str, Any] = {
        "task": task,
        "model_cls": model_cls,
        "stage": "single_stage",
    }

    if args.input:
        body.update(load_json_arg(args.input))

    apply_convenience_flags(body, args)

    if args.prompt:
        body["prompt"] = args.prompt
    if args.image:
        body["input_image"] = file_to_base64_input(args.image)
    if args.video:
        body["input_video"] = file_to_base64_input(args.video)
    if args.audio:
        body["input_audio"] = file_to_base64_input(args.audio)

    if "prompt" not in body:
        raise ValueError("prompt is required; pass --prompt or include it in --input JSON")

    return body


def handle(args: argparse.Namespace) -> int:
    console = CliConsole(json_mode=args.json, quiet=args.quiet)
    try:
        config = resolve_config()
        body = build_submit_body(args)
    except Exception as exc:
        if args.json:
            print(json.dumps({"type": "error", "message": str(exc)}, ensure_ascii=False))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1

    task = body["task"]
    try:
        with LightX2VClient(config, notify_updates=not args.json and not args.quiet) as client:
            if args.quote:
                quote = client.quote(body)
                credits = quote.get("quoted_credits")
                console.event("quote", quoted_credits=credits)
                console.println(f"quoted_credits: {credits}")

            submit = client.submit(body)
            task_id = submit.get("task_id")
            quoted = submit.get("quoted_credits")
            if not task_id:
                console.println("Error: submit response missing task_id")
                return 1
            console.event("submit", task_id=task_id, quoted_credits=quoted)
            console.println(f"task_id: {task_id}")
            if quoted is not None:
                console.println(f"quoted_credits: {quoted} (API channel is 2x web pricing)")

            deadline = time.time() + args.timeout
            final: dict[str, Any] | None = None
            use_spinner = not args.json and not args.quiet and not args.no_spinner

            while time.time() < deadline:
                if use_spinner:
                    with Spinner("Waiting for task"):
                        data = client.query(task_id)
                else:
                    data = client.query(task_id)

                status = data.get("status")
                console.event("status", status=status, task_id=task_id)
                if not args.json and not args.quiet:
                    print(f"status: {status}", flush=True)
                if status == "SUCCEED":
                    final = data
                    break
                if status in ("FAILED", "CANCEL"):
                    if args.json:
                        console.finish(success=False, result=data)
                    else:
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                    return 1
                time.sleep(max(args.poll_interval, 0.05))

            if final is None:
                console.println("Error: timed out waiting for task completion")
                return 1

            output_name = infer_output_name(task, body)
            result = client.result_url(task_id, output_name)
            url = result.get("url")
            if not url:
                console.println("Error: result_url response missing url")
                return 1
            console.event("result_url", url=url, name=output_name)
            console.println(f"result_url: {url}")

            outcome: dict[str, Any] = {
                "task_id": task_id,
                "status": "SUCCEED",
                "url": url,
                "name": output_name,
            }

            if args.no_download:
                console.finish(success=True, result=outcome)
                if not args.json:
                    print(json.dumps(outcome, indent=2, ensure_ascii=False))
                return 0

            output_path = args.output or default_output_path(task, body)
            if output_path:
                content = client.download(url)
                out = Path(output_path)
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(content)
                saved = str(out.resolve())
                outcome["saved"] = saved
                console.event("saved", path=saved)
                console.println(f"saved: {saved}")

            console.finish(success=True, result=outcome)
            return 0
    except ApiError as exc:
        if args.json:
            print(json.dumps({"type": "error", "status_code": exc.status_code, "message": exc.message}, ensure_ascii=False))
        else:
            print(f"Error [{exc.status_code}]: {exc.message}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        msg = f"invalid JSON in --input: {exc}"
        if args.json:
            print(json.dumps({"type": "error", "message": msg}, ensure_ascii=False))
        else:
            print(f"Error: {msg}", file=sys.stderr)
        return 1
