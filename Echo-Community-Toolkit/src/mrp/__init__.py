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


def _load_legacy_package() -> Optional[ModuleType]:
    root = Path(__file__).resolve().parents[3]
    legacy_root = root / "src" / "mrp"
    init_path = legacy_root / "__init__.py"
    if not init_path.exists():
        return None

    module_name = "_mrp_legacy"
    existing = sys.modules.get(module_name)
    if isinstance(existing, ModuleType):
        return existing

    spec = importlib.util.spec_from_file_location(
        module_name,
        init_path,
        submodule_search_locations=[str(legacy_root)],
    )
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
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
    return getattr(codec, name, None)


_legacy_encode = _load_legacy_callable("encode_mrp")
_legacy_decode = _load_legacy_callable("decode_mrp")


def encode_mrp(*args, **kwargs):
    if _legacy_encode is None:
        raise ImportError("Legacy encode_mrp is unavailable; ensure src/mrp exists")
    return _legacy_encode(*args, **kwargs)


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
    if _legacy_decode is None:
        raise ImportError("Legacy decode_mrp is unavailable; ensure src/mrp exists")
    result = _legacy_decode(*args, **kwargs)
    if isinstance(result, dict):
        report = result.get("report")
        if _needs_parity_error(report) and "error" not in result:
            result = dict(result)
            result["error"] = "Parity integrity check failed"
    return result

