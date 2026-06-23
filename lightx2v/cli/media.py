from __future__ import annotations

import base64
from pathlib import Path


def file_to_base64_input(path: str) -> dict:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    data = base64.b64encode(file_path.read_bytes()).decode("utf-8")
    return {"type": "base64", "data": data}
