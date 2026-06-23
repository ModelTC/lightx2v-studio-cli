from __future__ import annotations

import argparse


def add_json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Emit structured JSON logs")


def add_quiet_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress non-essential output")


def add_task_id_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("task_id", help="Task ID")


def add_task_id_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--task-id", required=True, dest="task_id", help="Task ID")
