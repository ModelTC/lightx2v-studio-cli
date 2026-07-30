from __future__ import annotations

import argparse
import json
from pathlib import Path

from lightx2v.cli.commands._task_ops import with_client
from lightx2v.cli.common_args import add_json_flag, add_quiet_flag


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("tts", help="Generate speech with a built-in TTS voice")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--voice-type", required=True, help="VoiceType from `lightx2v voices`")
    parser.add_argument("--resource-id", required=True, help="ResourceID from `lightx2v voices`, e.g. seed-tts-2.0")
    parser.add_argument("--context-texts", default="", help="Optional context text")
    parser.add_argument("--emotion", default="", help="Emotion, e.g. neutral")
    parser.add_argument("--emotion-scale", type=int, default=3, help="Emotion intensity (default: 3)")
    parser.add_argument("--speech-rate", type=int, default=0, help="Speech rate adjustment (default: 0)")
    parser.add_argument("--loudness-rate", type=int, default=0, help="Loudness adjustment (default: 0)")
    parser.add_argument("--pitch", type=int, default=0, help="Pitch adjustment (default: 0)")
    parser.add_argument("-o", "--output", default="speech.mp3", help="Output MP3 path (default: speech.mp3)")
    add_json_flag(parser)
    add_quiet_flag(parser)
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        body = {
            "text": args.text,
            "voice_type": args.voice_type,
            "resource_id": args.resource_id,
            "context_texts": args.context_texts,
            "emotion": args.emotion,
            "emotion_scale": args.emotion_scale,
            "speech_rate": args.speech_rate,
            "loudness_rate": args.loudness_rate,
            "pitch": args.pitch,
        }
        content, content_type = client.generate_tts(body)
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(content)
        payload = {
            "saved": str(out.resolve()),
            "bytes": len(content),
            "content_type": content_type,
            "voice_type": args.voice_type,
            "resource_id": args.resource_id,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            console.println(f"saved: {payload['saved']}")
            console.println(f"bytes: {payload['bytes']}")
            if content_type:
                console.println(f"content_type: {content_type}")
        return 0

    return with_client(args, _run)
