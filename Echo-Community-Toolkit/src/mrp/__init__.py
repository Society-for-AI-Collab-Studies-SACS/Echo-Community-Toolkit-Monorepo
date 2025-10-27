"""Unified MRP exports bridging new codec helpers with legacy APIs."""

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


_legacy_encode = _load_legacy_callable("encode_mrp")
_legacy_decode = _load_legacy_callable("decode_mrp")


def encode_mrp(*args, **kwargs):
    legacy_impl = _legacy_encode or _load_legacy_callable("encode_mrp")
    if legacy_impl is None:
        raise ImportError("Legacy encode_mrp is unavailable; ensure src/mrp exists")
    return legacy_impl(*args, **kwargs)


def _needs_parity_error(report: dict) -> bool:
    if not isinstance(report, dict):
        return False
    scheme = report.get("ecc_scheme")
    if scheme != "parity":
        return False
    if report.get("repaired"):
        return True
    if not report.get("parity_ok", True):
        return True
    if not report.get("crc_r_ok", True) or not report.get("crc_g_ok", True):
        return True
    if not report.get("sha_ok", True):
        return True
    return False


def decode_mrp(*args, **kwargs):
    legacy_impl = _legacy_decode or _load_legacy_callable("decode_mrp")
    if legacy_impl is None:
        raise ImportError("Legacy decode_mrp is unavailable; ensure src/mrp exists")
    result = legacy_impl(*args, **kwargs)
    if isinstance(result, dict):
        report = result.get("report")
        if _needs_parity_error(report) and "error" not in result:
            result = dict(result)
            result["error"] = "Parity integrity check failed"
    return result
