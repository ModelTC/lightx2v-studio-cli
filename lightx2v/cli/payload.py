from __future__ import annotations

import argparse
from typing import Any


def parse_shape(value: str) -> list[int]:
    parts = [p.strip() for p in value.split(",")]
    if len(parts) != 2:
        raise ValueError("--shape must be HEIGHT,WIDTH e.g. 720,1280")
    return [int(parts[0]), int(parts[1])]


def seconds_to_video_length(seconds: float) -> int:
    frames = int(seconds * 24)
    n = max(1, round((frames - 1) / 24))
    return 24 * n + 1


def apply_convenience_flags(body: dict[str, Any], args: argparse.Namespace) -> None:
    if getattr(args, "shape", None):
        body["custom_shape"] = parse_shape(args.shape)
    if getattr(args, "aspect_ratio", None):
        body["aspect_ratio"] = args.aspect_ratio
    if getattr(args, "vsr_preset", None):
        body["vsr_preset"] = args.vsr_preset
    if getattr(args, "vsr_input_slot", None):
        body["vsr_input_slot"] = args.vsr_input_slot
    if getattr(args, "duration", None) is not None:
        task = body.get("task", "")
        if task in ("t2av", "i2av"):
            body["target_video_length"] = seconds_to_video_length(float(args.duration))
        elif task == "s2v":
            meta = dict(body.get("input_meta") or {})
            meta["audio_seconds"] = float(args.duration)
            body["input_meta"] = meta
        else:
            raise ValueError(f"--duration is not supported for task {task!r}")


def add_run_convenience_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--shape", help="Output shape as HEIGHT,WIDTH (custom_shape)")
    parser.add_argument("--aspect-ratio", help="Aspect ratio e.g. 16:9")
    parser.add_argument("--duration", type=float, help="Duration in seconds (t2av/i2av/s2v)")
    parser.add_argument("--vsr-preset", help="VSR preset e.g. 1080_standard")
    parser.add_argument("--vsr-input-slot", choices=["video", "image"], help="VSR input slot")
