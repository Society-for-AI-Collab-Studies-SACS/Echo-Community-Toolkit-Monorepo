"""
Interactive REPL shell for the Prime CLI.
"""

from __future__ import annotations

import cmd
import shlex
from typing import Callable, Iterable, List

from .commands import CommandOutput


Executor = Callable[[List[str]], CommandOutput]


class PrimeShell(cmd.Cmd):
    intro = "Prime interactive mode. Type 'help' for assistance, 'exit' to leave."
    prompt = "prime> "

    def __init__(self, executor: Executor) -> None:
        super().__init__()
        self._execute = executor

    # ------------------------------------------------------------------ commands
    def default(self, line: str) -> None:
        tokens = self._split(line)
        if not tokens:
            return
        try:
            result = self._execute(tokens)
        except SystemExit:
            return
        except Exception as exc:
            print(f"[error] {exc}")
            return
        if result.message:
            print(result.message)

    def do_help(self, arg: str) -> None:  # type: ignore[override]
        if not arg:
            print(
                "Commands:\n"
                "  route \"<intent>\"   Route an intention through Garden→Echo→Limnus→Kira\n"
                "  status             Show current agent state summary\n"
                "  <agent> ...        Run agent commands (garden, echo, limnus, kira)\n"
                "  exit/quit          Leave the CLI\n"
            )
            return
        print("Detailed help is not yet implemented for individual commands.")  # TODO: expand help topics

    def do_exit(self, _arg: str) -> bool:  # type: ignore[override]
        print("Goodbye.")
        return True

    do_quit = do_exit

    # ------------------------------------------------------------------- helpers
    @staticmethod
    def _split(line: str) -> List[str]:
        try:
            return shlex.split(line)
        except ValueError as exc:
            print(f"[error] {exc}")
            return []

