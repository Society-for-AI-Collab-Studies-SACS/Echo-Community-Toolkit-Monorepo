"""
Command handlers powering the Prime CLI.

Each function returns a :class:`CommandOutput` containing a user-facing message,
optional structured payload, and an exit code.  This keeps the CLI presentation
layer lightweight while allowing plugins (such as the VS Code status writer) to
reuse the same helper functions.
"""

from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from agents.echo.echo_agent import EchoAgent
from agents.garden.garden_agent import GardenAgent
from agents.kira.kira_agent import KiraAgent
from agents.limnus.limnus_agent import LimnusAgent
from interface.dispatcher import DispatchResult, dispatch_explicit, dispatch_freeform

from .plugins import emit

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "state"


@dataclass
class CommandOutput:
    """Structured result for CLI commands."""

    message: str = ""
    exit_code: int = 0
    payload: Any = None

    def __bool__(self) -> bool:  # pragma: no cover - convenience
        return self.exit_code == 0


# --------------------------------------------------------------------------- util


def _run(cmd: Sequence[str]) -> int:
    proc = subprocess.run(cmd, cwd=ROOT)
    return proc.returncode


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, indent=2)
        except Exception:  # pragma: no cover - fallback
            return repr(value)
    return str(value)


def _emit_success(name: str, payload: Optional[Dict[str, Any]] = None) -> None:
    emit("after_command", {"name": name, **(payload or {})})


# --------------------------------------------------------------------- core tasks


def generate() -> CommandOutput:
    rc = _run(["python3", "src/schema_builder.py"])
    if rc == 0:
        rc = _run(["python3", "src/generate_chapters.py"])
    result = CommandOutput(message="", exit_code=rc)
    _emit_success("generate", {"exit_code": rc})
    return result


def listen(text: Optional[str]) -> CommandOutput:
    if not text:
        return CommandOutput("Provide --text for now (streaming capture not implemented)", exit_code=2)
    result = dispatch_freeform(text)
    message = _format_dispatch_result(result)
    payload = {"dispatch": result.__dict__}
    _emit_success("listen", {"payload": payload})
    return CommandOutput(message=message, payload=payload)


def validate() -> CommandOutput:
    result = KiraAgent(ROOT).validate()
    message = _stringify(result)
    exit_code = 0
    if isinstance(result, dict):
        exit_code = 0 if result.get("passed") else 1
    elif isinstance(result, str):
        exit_code = 0 if result == "valid" else 1
    _emit_success("kira.validate", {"exit_code": exit_code, "payload": result})
    return CommandOutput(message=message, exit_code=exit_code, payload=result)


def mentor(apply: bool = False) -> CommandOutput:
    result = KiraAgent(ROOT).mentor(apply=apply)
    message = _stringify(result)
    _emit_success("kira.mentor", {"payload": result})
    return CommandOutput(message=message, payload=result)


def publish(
    run: bool = False,
    release: bool = False,
    tag: Optional[str] = None,
    notes_file: Optional[str] = None,
    notes: Optional[str] = None,
    assets: Optional[Iterable[str]] = None,
) -> CommandOutput:
    assets_list = list(assets or [])
    result = KiraAgent(ROOT).publish(
        run=run,
        release=release,
        tag=tag,
        notes_file=notes_file,
        notes=notes,
        assets=assets_list,
    )
    message = _stringify(result)
    _emit_success("kira.publish", {"payload": result})
    return CommandOutput(message=message, payload=result)


# --------------------------------------------------------------------- route flow


AGENT_NAMES = {"garden", "echo", "limnus", "kira"}


def execute_route(intent: str) -> CommandOutput:
    explicit = _parse_explicit_command(intent)
    if explicit:
        agent, command, args = explicit
        value = dispatch_explicit(agent, command, *args)
        message = _stringify(value)
        payload = {"agent": agent, "command": command, "args": args, "result": value}
        _emit_success("route.explicit", payload)
        return CommandOutput(message=message, payload=payload)

    result = dispatch_freeform(intent)
    message = _format_dispatch_result(result)
    payload = {"intent": intent, "dispatch": result.__dict__}
    _emit_success("route.freeform", payload)
    return CommandOutput(message=message, payload=payload)


def _parse_explicit_command(intent: str) -> Optional[tuple[str, str, List[str]]]:
    tokens = shlex.split(intent)
    if not tokens:
        return None
    agent = tokens[0].lower()
    if agent not in AGENT_NAMES:
        return None
    if len(tokens) == 1:
        raise ValueError("Explicit agent command requires a verb, e.g. 'echo say \"...\"'")
    command = tokens[1].replace("_", "-")
    args = tokens[2:]
    return agent, command, args


def _format_dispatch_result(result: DispatchResult) -> str:
    parts = []
    if result.garden:
        parts.append(f"Garden: {result.garden}")
    if result.echo:
        parts.append(f"Echo: {result.echo}")
    if result.limnus:
        parts.append(f"Limnus: {result.limnus}")
    if result.kira:
        parts.append(f"Kira: {result.kira}")
    return " | ".join(parts) if parts else "No response recorded."


# ------------------------------------------------------------------ agent helpers


def echo_command(action: str, *, tone: Optional[str] = None, message: Optional[str] = None, text: Optional[str] = None) -> CommandOutput:
    agent = EchoAgent(ROOT)
    if action == "summon":
        result = agent.summon()
    elif action == "mode":
        if tone is None:
            raise ValueError("Echo mode requires a tone argument")
        result = agent.mode(tone)
    elif action == "say":
        if message is None:
            raise ValueError("Echo say requires a message")
        result = agent.say(message)
    elif action == "learn":
        if text is None:
            raise ValueError("Echo learn requires text")
        result = agent.learn(text)
    elif action == "status":
        result = agent.status()
    elif action == "calibrate":
        result = agent.calibrate()
    else:
        raise ValueError(f"Unknown Echo action: {action}")
    payload = {"agent": "echo", "action": action, "result": result}
    _emit_success("echo", payload)
    return CommandOutput(message=_stringify(result), payload=payload)


def garden_command(
    action: str,
    *,
    scroll: Optional[str] = None,
    prev: bool = False,
    reset: bool = False,
    text: Optional[str] = None,
) -> CommandOutput:
    agent = GardenAgent(ROOT)
    if action == "start":
        result = agent.start()
    elif action == "next":
        result = agent.next()
    elif action == "open":
        if scroll is None:
            raise ValueError("Garden open requires a scroll identifier")
        result = agent.open(scroll, prev=prev, reset=reset)
    elif action == "resume":
        result = agent.resume()
    elif action == "log":
        if text is None:
            raise ValueError("Garden log requires text")
        result = agent.log(text)
    elif action == "ledger":
        result = agent.ledger()
    else:
        raise ValueError(f"Unknown Garden action: {action}")
    payload = {"agent": "garden", "action": action, "result": result}
    _emit_success("garden", payload)
    return CommandOutput(message=_stringify(result), payload=payload)


def limnus_command(
    action: str,
    *,
    text: Optional[str] = None,
    query: Optional[str] = None,
    kind: Optional[str] = None,
    data: Optional[str] = None,
    backend: Optional[str] = None,
) -> CommandOutput:
    agent = LimnusAgent(ROOT)
    if action == "cache":
        if text is None:
            raise ValueError("Limnus cache requires text")
        result = agent.cache(text)
    elif action == "recall":
        result = agent.recall(query)
    elif action == "commit-block":
        if not kind or data is None:
            raise ValueError("Limnus commit-block requires kind and data")
        result = agent.commit_block(kind, {"text": data})
    elif action == "encode-ledger":
        result = agent.encode_ledger()
    elif action == "decode-ledger":
        result = agent.decode_ledger()
    elif action == "status":
        result = agent.status()
    elif action == "reindex":
        result = agent.reindex(backend=backend)
    else:
        raise ValueError(f"Unknown Limnus action: {action}")
    payload = {"agent": "limnus", "action": action, "result": result}
    _emit_success("limnus", payload)
    return CommandOutput(message=_stringify(result), payload=payload)


def kira_command(
    action: str,
    *,
    apply: bool = False,
    run: bool = False,
    message: Optional[str] = None,
    include_all: bool = False,
    release: bool = False,
    tag: Optional[str] = None,
    notes_file: Optional[str] = None,
    notes: Optional[str] = None,
    assets: Optional[Iterable[str]] = None,
    docs: bool = False,
    types: bool = False,
) -> CommandOutput:
    agent = KiraAgent(ROOT)
    if action == "validate":
        result = agent.validate()
        exit_code = 0 if result == "valid" else 1
        if isinstance(result, dict):
            exit_code = 0 if result.get("passed") else 1
        payload = {"agent": "kira", "action": action, "result": result, "exit_code": exit_code}
        _emit_success("kira", payload)
        return CommandOutput(message=_stringify(result), payload=payload, exit_code=exit_code)
    if action == "mentor":
        result = agent.mentor(apply=apply)
    elif action == "mantra":
        result = agent.mantra()
    elif action == "seal":
        result = agent.seal()
    elif action == "push":
        result = agent.push(run=run, message=message, include_all=include_all)
    elif action == "publish":
        payload_assets = list(assets or [])
        result = agent.publish(
            run=run,
            release=release,
            tag=tag,
            notes_file=notes_file,
            notes=notes,
            assets=payload_assets,
        )
    elif action == "codegen":
        result = agent.codegen(docs=docs, types=types)
    else:
        raise ValueError(f"Unknown Kira action: {action}")
    payload = {"agent": "kira", "action": action, "result": result}
    _emit_success("kira", payload)
    return CommandOutput(message=_stringify(result), payload=payload)


# --------------------------------------------------------------------- status API


def build_status_snapshot() -> Dict[str, Any]:
    """Aggregate key state values used by the status command and VS Code plugin."""

    snapshot: Dict[str, Any] = {}

    echo_state = _read_json(STATE_DIR / "echo_state.json")
    if echo_state:
        snapshot["echo"] = {
            "alpha": echo_state.get("alpha"),
            "beta": echo_state.get("beta"),
            "gamma": echo_state.get("gamma"),
            "last_mode": echo_state.get("last_mode"),
        }

    garden_state = _read_json(STATE_DIR / "garden_ledger.json")
    if garden_state:
        entries = garden_state.get("entries") or []
        snapshot["garden"] = {"stage": garden_state.get("stage"), "entries": len(entries)}

    limnus_state = _read_json(STATE_DIR / "limnus_memory.json")
    if limnus_state:
        entries = limnus_state.get("entries") or []
        snapshot["memory"] = {"count": len(entries)}

    contract = _read_json(STATE_DIR / "contract.json")
    if contract is not None:
        snapshot["contract"] = contract

    return snapshot


def status(json_output: bool = False) -> CommandOutput:
    snapshot = build_status_snapshot()
    if json_output:
        message = json.dumps(snapshot, indent=2)
    else:
        message = _format_status(snapshot)
    _emit_success("status", {"payload": snapshot})
    return CommandOutput(message=message, payload=snapshot)


def _format_status(snapshot: Dict[str, Any]) -> str:
    parts: List[str] = []
    echo = snapshot.get("echo") or {}
    if echo:
        parts.append(
            "Persona α={alpha:.2f} β={beta:.2f} γ={gamma:.2f}".format(
                alpha=echo.get("alpha", 0.0),
                beta=echo.get("beta", 0.0),
                gamma=echo.get("gamma", 0.0),
            )
        )
    garden = snapshot.get("garden") or {}
    if garden:
        parts.append(f"Garden stage: {garden.get('stage', 'unknown')} (entries: {garden.get('entries', 0)})")
    memory = snapshot.get("memory") or {}
    if memory:
        parts.append(f"Memories cached: {memory.get('count', 0)}")
    contract = snapshot.get("contract") or {}
    if isinstance(contract, dict) and contract:
        status_text = "sealed" if contract.get("sealed") else "pending"
        parts.append(f"Contract: {status_text}")
    return " | ".join(parts) if parts else "No state information available."


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # pragma: no cover - defensive
        return None
