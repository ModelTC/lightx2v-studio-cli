from __future__ import annotations

import json
import sys
import threading
import time
from typing import Any


class CliConsole:
    def __init__(self, *, json_mode: bool = False, quiet: bool = False):
        self.json_mode = json_mode
        self.quiet = quiet
        self._events: list[dict[str, Any]] = []

    def event(self, kind: str, **payload: Any) -> None:
        record = {"type": kind, **payload}
        self._events.append(record)
        if self.json_mode:
            print(json.dumps(record, ensure_ascii=False), flush=True)
            return
        if self.quiet:
            return
        if kind == "status":
            sys.stderr.write(f"\rstatus: {payload.get('status', '')}   ")
            sys.stderr.flush()
        elif kind == "message":
            sys.stderr.write(f"{payload.get('text', '')}\n")
            sys.stderr.flush()

    def println(self, text: str = "") -> None:
        if self.json_mode:
            self.event("message", text=text)
            return
        if not self.quiet:
            print(text, flush=True)

    def finish(self, *, success: bool, result: dict[str, Any] | None = None) -> None:
        if self.json_mode:
            print(
                json.dumps({"type": "done", "success": success, "result": result, "events": self._events}, ensure_ascii=False),
                flush=True,
            )
        elif not self.quiet and self._events:
            sys.stderr.write("\n")


class Spinner:
    def __init__(self, message: str):
        self.message = message
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> Spinner:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        sys.stderr.write("\r" + " " * (len(self.message) + 4) + "\r")
        sys.stderr.flush()

    def _run(self) -> None:
        frames = "|/-\\"
        i = 0
        while not self._stop.is_set():
            sys.stderr.write(f"\r{self.message} {frames[i % len(frames)]}")
            sys.stderr.flush()
            i += 1
            time.sleep(0.12)
