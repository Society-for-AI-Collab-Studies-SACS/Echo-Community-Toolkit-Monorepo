"""
Dispatcher orchestrates user inputs through the four agents in sequence
when inputs are free‑form: Garden → Echo → Limnus → Kira.

Explicit agent‑addressed commands are routed directly.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from interface.logger import log_event


@dataclass
class DispatchResult:
    garden: Optional[str] = None
    echo: Optional[str] = None
    limnus: Optional[str] = None
    kira: Optional[str] = None


def _load_agent(module: str):
    # Local import to avoid import cycles at startup
    root = Path(__file__).resolve().parents[1]
    agents_dir = root / "agents" / module
    if module == "garden":
        from agents.garden.garden_agent import GardenAgent  # type: ignore

        return GardenAgent(root)
    if module == "echo":
        from agents.echo.echo_agent import EchoAgent  # type: ignore

        return EchoAgent(root)
    if module == "limnus":
        from agents.limnus.limnus_agent import LimnusAgent  # type: ignore

        return LimnusAgent(root)
    if module == "kira":
        from agents.kira.kira_agent import KiraAgent  # type: ignore

        return KiraAgent(root)
    raise ValueError(f"Unknown agent: {module}")


def dispatch_freeform(text: str) -> DispatchResult:
    """Default pipeline for free‑form inputs.
    Garden logs → Echo responds/learns → Limnus archives → Kira validates.
    """
    garden = _load_agent("garden")
    echo = _load_agent("echo")
    limnus = _load_agent("limnus")
    kira = _load_agent("kira")

    log_event("router", "freeform", {"text": text})
    garden_ref = garden.log(text)
    echo_ref = echo.say(text)
    block_ref = limnus.commit_block(kind="input", data={"text": text, "echo_ref": echo_ref, "garden_ref": garden_ref})
    kira_result = kira.validate()
    kira_ref = kira_result
    if isinstance(kira_result, dict):
        kira_ref = "valid" if kira_result.get("passed") else "invalid"
    return DispatchResult(garden=garden_ref, echo=echo_ref, limnus=block_ref, kira=kira_ref)


def dispatch_explicit(agent: str, command: str, *args: str) -> str:
    """Route an explicit agent command, e.g. kira validate, echo mode fox."""
    a = _load_agent(agent)
    method = getattr(a, command.replace("-", "_"), None)
    if not callable(method):
        raise AttributeError(f"{agent} has no command '{command}'")
    log_event("router", "explicit", {"agent": agent, "command": command, "args": list(args)})
    return method(*args)
