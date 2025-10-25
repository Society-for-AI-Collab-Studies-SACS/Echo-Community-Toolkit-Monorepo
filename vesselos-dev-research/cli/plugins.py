"""
Lightweight plugin bus for the Prime CLI.

Plugins can subscribe to lifecycle events (e.g. ``after_command``) to mirror
state into other tools such as the VS Code extension.  The implementation keeps
dependencies minimal so the CLI remains importable without optional extras.
"""

from __future__ import annotations

from collections import defaultdict
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, DefaultDict, Dict, Iterable, List, Optional, Set

Handler = Callable[[Dict[str, Any]], None]

_subscribers: DefaultDict[str, List[Handler]] = defaultdict(list)
_loaded_modules: Set[str] = set()
_builtins: tuple[str, ...] = ("cli.vscode_plugin",)


def subscribe(event: str, handler: Handler) -> None:
    """Register ``handler`` for ``event`` notifications."""

    if handler not in _subscribers[event]:
        _subscribers[event].append(handler)


def emit(event: str, payload: Optional[Dict[str, Any]] = None) -> None:
    """Broadcast ``payload`` to all handlers listening for ``event``."""

    data = payload or {}
    for handler in list(_subscribers.get(event, [])):
        try:
            handler(data)
        except Exception as exc:  # pragma: no cover - diagnostics only
            # Avoid crashing the CLI because of plugin issues; handlers should log.
            print(f"[prime:plugin:{handler.__module__}] error: {exc}")


def load_modules(names: Iterable[str]) -> None:
    """Import plugin modules by dotted path and remember the successful ones."""

    for name in names:
        if name in _loaded_modules:
            continue
        try:
            import_module(name)
        except Exception as exc:  # pragma: no cover - optional plugins
            print(f"[prime:plugins] failed to load '{name}': {exc}")
            continue
        _loaded_modules.add(name)


def load_builtin_plugins(config_path: Optional[Path] = None) -> None:
    """Load default plugins and optional entries from ``config_path``."""

    entries: List[str] = list(_builtins)

    if config_path and config_path.exists():
        try:
            for line in config_path.read_text(encoding="utf-8").splitlines():
                dotted = line.strip()
                if dotted and not dotted.startswith("#"):
                    entries.append(dotted)
        except Exception as exc:  # pragma: no cover - defensive guard
            print(f"[prime:plugins] unable to read config: {exc}")

    load_modules(entries)

