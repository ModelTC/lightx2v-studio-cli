from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_arg(value: str) -> dict[str, Any]:
    raw = value.strip()
    if raw.startswith("@"):
        path = Path(raw[1:])
        if not path.is_file():
            raise FileNotFoundError(f"Input file not found: {path}")
        raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("JSON input must be an object")
    return data
