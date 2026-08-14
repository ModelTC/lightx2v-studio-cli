from argparse import Namespace

from lightx2v.cli.payload import apply_convenience_flags


def test_resolution_level_is_forwarded_to_submit_body():
    body = {"task": "t2av", "model_cls": "MiniMax-H3"}
    args = Namespace(
        shape=None,
        resolution_level="768p",
        aspect_ratio="9:16",
        duration=None,
        vsr_preset=None,
        vsr_input_slot=None,
    )

    apply_convenience_flags(body, args)

    assert body["resolution_level"] == "768p"
    assert body["aspect_ratio"] == "9:16"


def test_duration_uses_model_aware_server_field():
    body = {"task": "t2av", "model_cls": "MiniMax-H3"}
    args = Namespace(
        shape=None,
        resolution_level="768p",
        aspect_ratio="9:16",
        duration=15,
        vsr_preset=None,
        vsr_input_slot=None,
    )

    apply_convenience_flags(body, args)

    assert body["video_duration_seconds"] == 15.0
    assert "target_video_length" not in body
