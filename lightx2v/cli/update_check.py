from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from lightx2v.cli.config import CONFIG_DIR

UPDATE_CHECK_PATH = CONFIG_DIR / "update-check.json"
UPDATE_NOTICE_INTERVAL = timedelta(hours=24)


def _parse_version(value: str) -> tuple[tuple[int, int, int], tuple[tuple[int, Any], ...] | None]:
    raw = value.strip().lstrip("v").split("+", 1)[0]
    core, separator, prerelease = raw.partition("-")
    parts = core.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"invalid semantic version: {value!r}")
    pre: tuple[tuple[int, Any], ...] | None = None
    if separator:
        if not prerelease:
            raise ValueError(f"invalid semantic version: {value!r}")
        pre = tuple((0, int(part)) if part.isdigit() else (1, part) for part in prerelease.split("."))
    return (int(parts[0]), int(parts[1]), int(parts[2])), pre


def compare_versions(left: str, right: str) -> int:
    left_core, left_pre = _parse_version(left)
    right_core, right_pre = _parse_version(right)
    if left_core != right_core:
        return 1 if left_core > right_core else -1
    if left_pre is None and right_pre is None:
        return 0
    if left_pre is None:
        return 1
    if right_pre is None:
        return -1
    if left_pre == right_pre:
        return 0
    return 1 if left_pre > right_pre else -1


class UpdateChecker:
    def __init__(
        self,
        *,
        current_version: str,
        cache_path: Path = UPDATE_CHECK_PATH,
        enabled: bool = True,
        now: Callable[[], datetime] | None = None,
    ):
        self.current_version = current_version
        self.cache_path = cache_path
        self.enabled = enabled
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._latest_version = ""
        self._minimum_version = ""
        self._consumed = False

    def observe_headers(self, headers: Mapping[str, str]) -> None:
        normalized = {str(key).lower(): str(value).strip() for key, value in headers.items()}
        latest = normalized.get("x-lightx2v-cli-latest-version", "")
        minimum = normalized.get("x-lightx2v-cli-min-version", "")
        try:
            if latest and compare_versions(latest, self.current_version) > 0:
                self._latest_version = latest
            if minimum:
                compare_versions(minimum, self.current_version)
                self._minimum_version = minimum
        except ValueError:
            return

    def consume_notice(self) -> str | None:
        if not self.enabled or self._consumed or not self._latest_version:
            return None
        self._consumed = True
        now = self._now()
        if self._notified_recently(now):
            return None

        incompatible = bool(
            self._minimum_version
            and compare_versions(self.current_version, self._minimum_version) < 0
        )
        self._save_state(now)
        if incompatible:
            return (
                f"Your LightX2V CLI {self.current_version} may be incompatible with the current API. "
                f"Version {self._latest_version} is available.\nUpdate: lightx2v update"
            )
        return (
            f"New LightX2V CLI version available: {self._latest_version} "
            f"(current: {self.current_version})\nUpdate: lightx2v update"
        )

    def _notified_recently(self, now: datetime) -> bool:
        try:
            state = json.loads(self.cache_path.read_text(encoding="utf-8"))
            last = datetime.fromisoformat(str(state.get("last_notified_at") or ""))
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            return (
                state.get("current_version") == self.current_version
                and state.get("latest_version") == self._latest_version
                and now - last < UPDATE_NOTICE_INTERVAL
            )
        except (OSError, AttributeError, ValueError, TypeError, json.JSONDecodeError):
            return False

    def _save_state(self, now: datetime) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(
                json.dumps(
                    {
                        "current_version": self.current_version,
                        "latest_version": self._latest_version,
                        "last_notified_at": now.isoformat(),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass
