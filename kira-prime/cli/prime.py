"""
Prime CLI entry point.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, List, Optional

from . import commands
from .commands import CommandOutput
from .plugins import load_builtin_plugins
from .repl import PrimeShell

ROOT = commands.ROOT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prime", description="Kira Prime – Multi-agent CLI")
    sub = parser.add_subparsers(dest="command")

    # route
    p_route = sub.add_parser("route", help="Route an intention through the agents")
    p_route.add_argument("intent", help="Instruction or explicit agent command")
    p_route.set_defaults(handler=_handle_route)

    # status
    p_status = sub.add_parser("status", help="Show current agent state summary")
    p_status.add_argument("--json", action="store_true", help="Output JSON instead of prose")
    p_status.set_defaults(handler=_handle_status)

    # compatibility commands
    p_generate = sub.add_parser("generate", help="Rebuild schema and chapters")
    p_generate.set_defaults(handler=_handle_generate)

    p_listen = sub.add_parser("listen", help="Process free-form text through all agents")
    p_listen.add_argument("--text", help="Input text to route", default=None)
    p_listen.set_defaults(handler=_handle_listen)

    p_validate = sub.add_parser("validate", help="Run Kira validation")
    p_validate.set_defaults(handler=_handle_validate)

    p_mentor = sub.add_parser("mentor", help="Run Kira mentor guidance")
    p_mentor.add_argument("--apply", action="store_true", help="Apply recommended actions automatically")
    p_mentor.set_defaults(handler=_handle_mentor)

    p_publish = sub.add_parser("publish", help="Run Kira publish (dry-run unless --run)")
    p_publish.add_argument("--run", action="store_true", help="Execute the publish instead of a dry run")
    p_publish.add_argument("--release", action="store_true", help="Create a GitHub release")
    p_publish.add_argument("--tag", default=None, help="Release tag")
    p_publish.add_argument("--notes-file", default=None, help="Path to release notes file")
    p_publish.add_argument("--notes", default=None, help="Inline release notes text")
    p_publish.add_argument("--asset", action="append", default=None, help="Assets to attach (repeatable)")
    p_publish.set_defaults(handler=_handle_publish)

    # garden
    p_garden = sub.add_parser("garden", help="Garden agent commands")
    garden_sub = p_garden.add_subparsers(dest="action", required=True)
    garden_sub.add_parser("start").set_defaults(handler=_handle_garden, action="start")
    garden_sub.add_parser("next").set_defaults(handler=_handle_garden, action="next")
    p_garden_open = garden_sub.add_parser("open")
    p_garden_open.add_argument("scroll")
    p_garden_open.add_argument("--prev", action="store_true")
    p_garden_open.add_argument("--reset", action="store_true")
    p_garden_open.set_defaults(handler=_handle_garden, action="open")
    garden_sub.add_parser("resume").set_defaults(handler=_handle_garden, action="resume")
    p_garden_log = garden_sub.add_parser("log")
    p_garden_log.add_argument("text")
    p_garden_log.set_defaults(handler=_handle_garden, action="log")
    garden_sub.add_parser("ledger").set_defaults(handler=_handle_garden, action="ledger")

    # echo
    p_echo = sub.add_parser("echo", help="Echo agent commands")
    echo_sub = p_echo.add_subparsers(dest="action", required=True)
    echo_sub.add_parser("summon").set_defaults(handler=_handle_echo, action="summon")
    p_echo_mode = echo_sub.add_parser("mode")
    p_echo_mode.add_argument("tone")
    p_echo_mode.set_defaults(handler=_handle_echo, action="mode")
    p_echo_say = echo_sub.add_parser("say")
    p_echo_say.add_argument("message")
    p_echo_say.set_defaults(handler=_handle_echo, action="say")
    p_echo_learn = echo_sub.add_parser("learn")
    p_echo_learn.add_argument("text")
    p_echo_learn.set_defaults(handler=_handle_echo, action="learn")
    echo_sub.add_parser("status").set_defaults(handler=_handle_echo, action="status")
    echo_sub.add_parser("calibrate").set_defaults(handler=_handle_echo, action="calibrate")

    # limnus
    p_limnus = sub.add_parser("limnus", help="Limnus agent commands")
    limnus_sub = p_limnus.add_subparsers(dest="action", required=True)
    p_limnus_cache = limnus_sub.add_parser("cache")
    p_limnus_cache.add_argument("text")
    p_limnus_cache.set_defaults(handler=_handle_limnus, action="cache")
    p_limnus_recall = limnus_sub.add_parser("recall")
    p_limnus_recall.add_argument("query", nargs="?")
    p_limnus_recall.set_defaults(handler=_handle_limnus, action="recall")
    p_limnus_commit = limnus_sub.add_parser("commit-block")
    p_limnus_commit.add_argument("kind")
    p_limnus_commit.add_argument("data")
    p_limnus_commit.set_defaults(handler=_handle_limnus, action="commit-block")
    limnus_sub.add_parser("encode-ledger").set_defaults(handler=_handle_limnus, action="encode-ledger")
    limnus_sub.add_parser("decode-ledger").set_defaults(handler=_handle_limnus, action="decode-ledger")
    limnus_sub.add_parser("status").set_defaults(handler=_handle_limnus, action="status")
    p_limnus_reindex = limnus_sub.add_parser("reindex")
    p_limnus_reindex.add_argument("--backend", choices=["sbert", "faiss"], default=None)
    p_limnus_reindex.set_defaults(handler=_handle_limnus, action="reindex")

    # kira
    p_kira = sub.add_parser("kira", help="Kira agent commands")
    kira_sub = p_kira.add_subparsers(dest="action", required=True)
    kira_sub.add_parser("validate").set_defaults(handler=_handle_kira, action="validate")
    p_kira_mentor = kira_sub.add_parser("mentor")
    p_kira_mentor.add_argument("--apply", action="store_true")
    p_kira_mentor.set_defaults(handler=_handle_kira, action="mentor")
    kira_sub.add_parser("mantra").set_defaults(handler=_handle_kira, action="mantra")
    kira_sub.add_parser("seal").set_defaults(handler=_handle_kira, action="seal")
    p_kira_push = kira_sub.add_parser("push")
    p_kira_push.add_argument("--run", action="store_true")
    p_kira_push.add_argument("--message", default=None)
    p_kira_push.add_argument("--all", action="store_true", dest="include_all")
    p_kira_push.set_defaults(handler=_handle_kira, action="push")
    p_kira_publish = kira_sub.add_parser("publish")
    p_kira_publish.add_argument("--run", action="store_true")
    p_kira_publish.add_argument("--release", action="store_true")
    p_kira_publish.add_argument("--tag", default=None)
    p_kira_publish.add_argument("--notes-file", default=None)
    p_kira_publish.add_argument("--notes", default=None)
    p_kira_publish.add_argument("--asset", action="append", default=None)
    p_kira_publish.set_defaults(handler=_handle_kira, action="publish")

    p_kira_codegen = kira_sub.add_parser("codegen", help="Generate knowledge docs and types")
    p_kira_codegen.add_argument("--docs", action="store_true", help="Emit docs/kira_knowledge.md")
    p_kira_codegen.add_argument("--types", action="store_true", help="Emit TypeScript type definitions")
    p_kira_codegen.set_defaults(handler=_handle_kira, action="codegen")

    return parser


# --------------------------------------------------------------------------- handlers


def _handle_route(args: argparse.Namespace) -> CommandOutput:
    return commands.execute_route(args.intent)


def _handle_status(args: argparse.Namespace) -> CommandOutput:
    return commands.status(json_output=args.json)


def _handle_generate(_args: argparse.Namespace) -> CommandOutput:
    return commands.generate()


def _handle_listen(args: argparse.Namespace) -> CommandOutput:
    return commands.listen(args.text)


def _handle_validate(_args: argparse.Namespace) -> CommandOutput:
    return commands.validate()


def _handle_mentor(args: argparse.Namespace) -> CommandOutput:
    return commands.mentor(apply=args.apply)


def _handle_publish(args: argparse.Namespace) -> CommandOutput:
    assets = args.asset or []
    return commands.publish(
        run=args.run,
        release=args.release,
        tag=args.tag,
        notes_file=args.notes_file,
        notes=args.notes,
        assets=assets,
    )


def _handle_garden(args: argparse.Namespace) -> CommandOutput:
    return commands.garden_command(
        action=args.action,
        scroll=getattr(args, "scroll", None),
        prev=getattr(args, "prev", False),
        reset=getattr(args, "reset", False),
        text=getattr(args, "text", None),
    )


def _handle_echo(args: argparse.Namespace) -> CommandOutput:
    return commands.echo_command(
        action=args.action,
        tone=getattr(args, "tone", None),
        message=getattr(args, "message", None),
        text=getattr(args, "text", None),
    )


def _handle_limnus(args: argparse.Namespace) -> CommandOutput:
    return commands.limnus_command(
        action=args.action,
        text=getattr(args, "text", None),
        query=getattr(args, "query", None),
        kind=getattr(args, "kind", None),
        data=getattr(args, "data", None),
        backend=getattr(args, "backend", None),
    )


def _handle_kira(args: argparse.Namespace) -> CommandOutput:
    assets = getattr(args, "asset", None)
    return commands.kira_command(
        action=args.action,
        apply=getattr(args, "apply", False),
        run=getattr(args, "run", False),
        message=getattr(args, "message", None),
        include_all=getattr(args, "include_all", False),
        release=getattr(args, "release", False),
        tag=getattr(args, "tag", None),
        notes_file=getattr(args, "notes_file", None),
        notes=getattr(args, "notes", None),
        assets=assets,
        docs=getattr(args, "docs", False),
        types=getattr(args, "types", False),
    )


# --------------------------------------------------------------------------- runtime


def execute(argv: List[str], parser: Optional[argparse.ArgumentParser] = None) -> CommandOutput:
    parser = parser or build_parser()
    args = parser.parse_args(argv)
    handler: Optional[Callable[[argparse.Namespace], CommandOutput]] = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        raise SystemExit(2)
    return handler(args)


def main(argv: Optional[List[str]] = None) -> int:
    load_builtin_plugins(_plugin_config_path())
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        shell = PrimeShell(lambda tokens: execute(tokens, parser))
        shell.cmdloop()
        return 0
    try:
        result = execute(argv, parser)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1
    output = result.message
    if output:
        print(output)
    return result.exit_code


def _plugin_config_path() -> Optional[Path]:
    candidate = ROOT / "config" / "prime_plugins.txt"
    return candidate if candidate.exists() else None


if __name__ == "__main__":
    sys.exit(main())
