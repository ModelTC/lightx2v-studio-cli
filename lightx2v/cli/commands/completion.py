from __future__ import annotations

import argparse
import sys

_SUBCOMMANDS = [
    "login",
    "models",
    "run",
    "query",
    "list",
    "cancel",
    "resume",
    "delete",
    "result",
    "completion",
]

_TASK_TYPES = ["s2v", "t2v", "i2v", "flf2v", "t2av", "i2av", "vsr", "animate", "t2i", "i2i"]


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("completion", help="Print shell completion script")
    parser.add_argument("shell", choices=["bash", "zsh"], help="Shell type")
    parser.set_defaults(handler=handle)


def _bash_script() -> str:
    cmds = " ".join(_SUBCOMMANDS)
    tasks = " ".join(_TASK_TYPES)
    return f"""# LightX2V CLI bash completion
_lightx2v_completions() {{
  local cur prev
  cur="${{COMP_WORDS[COMP_CWORD]}}"
  prev="${{COMP_WORDS[COMP_CWORD-1]}}"
  if [[ ${{COMP_CWORD}} -eq 1 ]]; then
    COMPREPLY=( $(compgen -W "{cmds}" -- "$cur") )
    return 0
  fi
  case "${{COMP_WORDS[1]}}" in
    run)
      if [[ "$cur" == *"/"* ]] || [[ "$prev" == "run" ]]; then
        COMPREPLY=( $(compgen -W "{' '.join(f'{t}/' for t in _TASK_TYPES)}" -- "$cur") )
      fi
      COMPREPLY+=( $(compgen -W "--input --prompt --image --video --audio --shape --aspect-ratio --duration --vsr-preset --vsr-input-slot -o --quote --json -q" -- "$cur") )
      ;;
    list)
      COMPREPLY=( $(compgen -W "--status --page --page-size --json -q" -- "$cur") )
      ;;
    query|cancel|resume|delete|result)
      COMPREPLY=( $(compgen -W "--json -q" -- "$cur") )
      ;;
    models)
      COMPREPLY=( $(compgen -W "--json" -- "$cur") )
      ;;
    login)
      COMPREPLY=( $(compgen -W "--base-url" -- "$cur") )
      ;;
    completion)
      COMPREPLY=( $(compgen -W "bash zsh" -- "$cur") )
      ;;
  esac
}}
complete -F _lightx2v_completions lightx2v
"""


def _zsh_script() -> str:
    cmds = " ".join(_SUBCOMMANDS)
    return f"""#compdef lightx2v
_lightx2v() {{
  local -a commands
  commands=(
    'login:Save API key'
    'models:List models'
    'run:Submit and download'
    'query:Query task'
    'list:List tasks'
    'cancel:Cancel task'
    'resume:Resume task'
    'delete:Delete task'
    'result:Get result URL'
    'completion:Shell completion'
  )
  if (( CURRENT == 2 )); then
    _describe 'command' commands
    return
  fi
  case $words[2] in
    run) _arguments '*: :(t2i/Qwen-Image-2512 t2v/Wan2.2_T2V_A14B_distilled i2v/Wan2.2_I2V_A14B_distilled)' ;;
    completion) _arguments '1: :(bash zsh)' ;;
  esac
}}
_lightx2v "$@"
"""


def handle(args: argparse.Namespace) -> int:
    script = _bash_script() if args.shell == "bash" else _zsh_script()
    sys.stdout.write(script)
    return 0
