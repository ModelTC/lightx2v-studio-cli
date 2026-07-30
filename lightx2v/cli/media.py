from __future__ import annotations

import base64
import mimetypes
from pathlib import Path


def file_to_base64_input(path: str) -> dict:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    data = base64.b64encode(file_path.read_bytes()).decode("utf-8")
    return {"type": "base64", "data": data}


def file_to_data_url(path: str) -> str:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    data = base64.b64encode(file_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{data}"
