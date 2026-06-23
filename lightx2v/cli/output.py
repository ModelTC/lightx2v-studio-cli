from __future__ import annotations

IMAGE_TASKS = {"t2i", "i2i"}


def infer_output_name(task: str, body: dict | None = None) -> str:
    if task in IMAGE_TASKS:
        return "output_image"
    if task == "vsr" and body:
        slot = body.get("vsr_input_slot") or (body.get("input_meta") or {}).get("vsr_input_slot")
        if slot == "image":
            return "output_image"
    return "output_video"


def default_output_path(task: str, body: dict | None = None) -> str | None:
    name = infer_output_name(task, body)
    if name == "output_image":
        return "output.png"
    return "output.mp4"
