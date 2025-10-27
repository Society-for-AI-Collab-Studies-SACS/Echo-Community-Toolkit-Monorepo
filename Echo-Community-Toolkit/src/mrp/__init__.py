"""Toolkit MRP API with legacy compatibility shims."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable, Optional, TypeVar

from .codec import decode, encode, encode_with_mode
from .frame import MRPFrame

__all__ = [
    "encode",
    "decode",
    "encode_with_mode",
    "encode_mrp",
    "decode_mrp",
    "MRPFrame",
]

_TCallable = TypeVar("_TCallable", bound=Callable[..., object])
_LEGACY_PKG = "_mrp_legacy"
_LEGACY_ROOT = Path(__file__).resolve().parents[3] / "src" / "mrp"


def _load_legacy_package() -> Optional[ModuleType]:
    """Load the legacy MRP package from the root src/ directory if present."""
    init_path = _LEGACY_ROOT / "__init__.py"
    if not init_path.exists():
        return None

    existing = sys.modules.get(_LEGACY_PKG)
    if isinstance(existing, ModuleType):
        return existing

    spec = importlib.util.spec_from_file_location(
        _LEGACY_PKG,
        init_path,
        submodule_search_locations=[str(_LEGACY_ROOT)],
    )
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[_LEGACY_PKG] = module
    spec.loader.exec_module(module)
    return module


def _load_legacy_callable(name: str) -> Optional[_TCallable]:
    package = _load_legacy_package()
    if package is None:
        return None
    try:
        codec = importlib.import_module(f"{package.__name__}.codec")
    except ModuleNotFoundError:
        return None
    attr = getattr(codec, name, None)
    return attr if callable(attr) else None


def _missing_legacy(name: str) -> Callable[..., object]:
    def _raiser(*_args, **_kwargs) -> object:
        raise ImportError(f"Legacy MRP function '{name}' is unavailable")

    return _raiser


encode_mrp = _load_legacy_callable("encode_mrp") or _missing_legacy("encode_mrp")
decode_mrp = _load_legacy_callable("decode_mrp") or _missing_legacy("decode_mrp")
