"""Pipeline exports and enhanced dispatcher bindings.

This package provides the intent parser, logging utilities, and both the
basic and enhanced dispatchers used across the repo. It unifies previously
vendored modules so integration scripts and audits can import from
`pipeline.*` directly, per AGENTS.md and docs.
"""

from .intent_parser import IntentParser, ParsedIntent  # type: ignore F401

# Back-compat: the legacy dispatcher lives in dispatcher.py
# The production-style dispatcher lives in dispatcher_enhanced.py
from .dispatcher_enhanced import (  # type: ignore F401
    DispatcherConfig,
    EnhancedMRPDispatcher,
    PipelineContext,
)

__all__ = [
    "IntentParser",
    "ParsedIntent",
    "EnhancedMRPDispatcher",
    "DispatcherConfig",
    "PipelineContext",
]
