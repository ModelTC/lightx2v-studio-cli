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
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lightx2v",
        description="LightX2V CLI — submit and download AI generation tasks via OpenAPI",
    )
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
    completion.add_parser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
