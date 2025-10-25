"""
Interfaces exposed by The Living Library.

This module will register CLI commands, API endpoints, and future VSCode
extension hooks that orchestrate collaboration and narration workflows.
"""

from typing import Iterable


def cli_plugins() -> Iterable[str]:
    """Return a list of CLI entry point identifiers."""
    return ("library_core.collab", "library_core.mrp")
