"""
Configuration helpers for The Living Library.

These utilities will eventually wrap the Phase 3 YAML loader so that
submodules (Echo, Kira Prime, MRP) can share a unified settings surface.
"""

from pathlib import Path
from typing import Any, Dict

CONFIG_ROOT = Path(__file__).resolve().parent


def describe() -> Dict[str, Any]:
    """Return a high-level view of available configuration assets."""
    return {
        "root": str(CONFIG_ROOT),
        "schema": str(CONFIG_ROOT / "schema"),
        "defaults": str(CONFIG_ROOT / "defaults"),
    }


__all__ = ["CONFIG_ROOT", "describe"]
