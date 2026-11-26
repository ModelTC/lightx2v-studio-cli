from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASE_URL = "https://x2v.light-ai.top"
CONFIG_DIR = Path.home() / ".config" / "lightx2v"
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass
class CliConfig:
    base_url: str
    api_key: str


class ConfigError(Exception):
    pass


def _first_env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value.strip()
    return None


def load_config_file() -> dict:
    if not CONFIG_PATH.is_file():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def write_private_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".login-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(payload, output, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def save_config_file(base_url: str, api_key: str) -> None:
    write_private_json(CONFIG_PATH, {"base_url": base_url.rstrip("/"), "api_key": api_key})


def resolve_config() -> CliConfig:
    file_data = load_config_file()
    base_url = (
        _first_env("LIGHTX2V_BASE_URL", "LIGHTX2V_CLOUD_URL", "API_BASE_URL")
        or file_data.get("base_url")
        or DEFAULT_BASE_URL
    )
    api_key = _first_env("LIGHTX2V_API_KEY", "LIGHTX2V_CLOUD_API_KEY") or file_data.get("api_key")
    if not api_key:
        raise ConfigError(
            "API key not configured. Run `lightx2v login` or set LIGHTX2V_API_KEY / LIGHTX2V_CLOUD_API_KEY."
        )
    return CliConfig(base_url=base_url.rstrip("/"), api_key=api_key)


def mask_api_key(api_key: str) -> str:
    if len(api_key) <= 12:
        return "***"
    return f"{api_key[:8]}...{api_key[-4:]}"
