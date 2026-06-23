from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any

from lightx2v.cli.client import ApiError, LightX2VClient
from lightx2v.cli.config import resolve_config
from lightx2v.cli.console import CliConsole


def with_client(
    args: Any,
    fn: Callable[[LightX2VClient, Any, CliConsole], int],
) -> int:
    try:
        config = resolve_config()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    console = CliConsole(json_mode=getattr(args, "json", False), quiet=getattr(args, "quiet", False))
    try:
        with LightX2VClient(config) as client:
            return fn(client, args, console)
    except ApiError as exc:
        if console.json_mode:
            print(json.dumps({"type": "error", "status_code": exc.status_code, "message": exc.message}, ensure_ascii=False))
        else:
            print(f"Error [{exc.status_code}]: {exc.message}", file=sys.stderr)
        return 1
