from __future__ import annotations

import argparse

from lightx2v.cli.commands import (
    cancel,
    completion,
    delete,
    list_cmd,
    login,
    models,
    query,
    result,
    resume,
    run,
    tts,
    update,
    voice_clone,
    voices,
    workflow,
)
from lightx2v import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lightx2v",
        description="LightX2V CLI — submit and download AI generation tasks via OpenAPI",
    )
    parser.add_argument("--version", action="version", version=f"lightx2v {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    login.add_parser(subparsers)
    models.add_parser(subparsers)
    run.add_parser(subparsers)
    query.add_parser(subparsers)
    list_cmd.add_parser(subparsers)
    cancel.add_parser(subparsers)
    resume.add_parser(subparsers)
    delete.add_parser(subparsers)
    result.add_parser(subparsers)
    voices.add_parser(subparsers)
    tts.add_parser(subparsers)
    voice_clone.add_parser(subparsers)
    workflow.add_parser(subparsers)
    from lightx2v.cli.commands.public_workflow import add_doctor
    add_doctor(subparsers)
    update.add_parser(subparsers)
    completion.add_parser(subparsers)
    def canonical_help(current):
        for action in current._actions:
            if '--canvas-id' in action.option_strings:
                action.option_strings.remove('--workflow-id')
            if isinstance(action, argparse._SubParsersAction):
                seen = set()
                for child in action.choices.values():
                    if id(child) not in seen:
                        seen.add(id(child))
                        canonical_help(child)
    canonical_help(parser)
    # Legacy aliases remain accepted but are omitted from the recommended surface.
    subparsers.metavar = "{" + ",".join(name for name in subparsers.choices if name != "workflow") + "}"
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
