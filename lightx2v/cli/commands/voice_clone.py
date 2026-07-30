from __future__ import annotations

import argparse
import json
from pathlib import Path

from lightx2v.cli.client import ApiError
from lightx2v.cli.commands._task_ops import with_client
from lightx2v.cli.common_args import add_json_flag, add_quiet_flag


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("voice-clone", help="Create, save, list, synthesize, and delete cloned voices")
    nested = parser.add_subparsers(dest="voice_clone_command", required=True)

    create = nested.add_parser("create", help="Upload reference audio and create a cloned voice")
    create.add_argument("audio", help="Reference audio path")
    create.add_argument("--text", default="", help="Transcript of the reference audio; omitted means server ASR")
    create.add_argument("--save-name", help="Save cloned voice under this name after creation")
    add_json_flag(create)
    add_quiet_flag(create)
    create.set_defaults(handler=handle_create)

    save = nested.add_parser("save", help="Save a cloned voice to your collection")
    save.add_argument("speaker_id", help="Speaker ID returned by voice-clone create")
    save.add_argument("name", help="Display name")
    add_json_flag(save)
    add_quiet_flag(save)
    save.set_defaults(handler=handle_save)

    list_cmd = nested.add_parser("list", help="List saved cloned voices")
    add_json_flag(list_cmd)
    add_quiet_flag(list_cmd)
    list_cmd.set_defaults(handler=handle_list)

    tts = nested.add_parser("tts", help="Generate speech with a cloned voice")
    tts.add_argument("--text", required=True, help="Text to synthesize")
    tts.add_argument("--speaker-id", required=True, help="Cloned voice speaker ID")
    tts.add_argument("--style", default="正常", help="Speaking style (default: 正常)")
    tts.add_argument("--speed", type=float, default=1.0, help="Speed (default: 1.0)")
    tts.add_argument("--volume", type=float, default=0.0, help="Volume adjustment (default: 0.0)")
    tts.add_argument("--pitch", type=float, default=0.0, help="Pitch adjustment (default: 0.0)")
    tts.add_argument("--language", default="ZH_CN", help="Language code (default: ZH_CN)")
    tts.add_argument("-o", "--output", default="cloned-voice.wav", help="Output WAV path (default: cloned-voice.wav)")
    add_json_flag(tts)
    add_quiet_flag(tts)
    tts.set_defaults(handler=handle_tts)

    delete = nested.add_parser("delete", help="Delete a cloned voice")
    delete.add_argument("speaker_id", help="Speaker ID")
    add_json_flag(delete)
    add_quiet_flag(delete)
    delete.set_defaults(handler=handle_delete)


def _print_payload(args: argparse.Namespace, console, payload: dict) -> None:
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        console.println(json.dumps(payload, ensure_ascii=False, indent=2))


def handle_create(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        data = client.create_voice_clone(args.audio, text=args.text)
        if args.save_name and data.get("speaker_id"):
            try:
                saved = client.save_voice_clone(data["speaker_id"], args.save_name)
                data["saved_voice_clone"] = saved
            except ApiError as exc:
                data["save_error"] = {"status_code": exc.status_code, "message": exc.message}
        _print_payload(args, console, data)
        return 1 if data.get("save_error") else 0

    return with_client(args, _run)


def handle_save(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        data = client.save_voice_clone(args.speaker_id, args.name)
        _print_payload(args, console, data)
        return 0

    return with_client(args, _run)


def handle_list(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        data = client.list_voice_clones()
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0

        clones = data.get("voice_clones") or []
        if not clones:
            console.println("No cloned voices found.")
            return 0
        headers = ("name", "speaker_id")
        rows = [(str(c.get("name") or ""), str(c.get("speaker_id") or "")) for c in clones]
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(cell))
        fmt = "  ".join(f"{{:{w}}}" for w in widths)
        console.println(fmt.format(*headers))
        console.println(fmt.format(*("-" * w for w in widths)))
        for row in rows:
            console.println(fmt.format(*row))
        return 0

    return with_client(args, _run)


def handle_tts(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        body = {
            "text": args.text,
            "speaker_id": args.speaker_id,
            "style": args.style,
            "speed": args.speed,
            "volume": args.volume,
            "pitch": args.pitch,
            "language": args.language,
        }
        content, content_type = client.generate_voice_clone_tts(body)
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(content)
        payload = {
            "saved": str(out.resolve()),
            "bytes": len(content),
            "content_type": content_type,
            "speaker_id": args.speaker_id,
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


def handle_delete(args: argparse.Namespace) -> int:
    def _run(client, args, console):
        data = client.delete_voice_clone(args.speaker_id)
        _print_payload(args, console, data)
        return 0

    return with_client(args, _run)
