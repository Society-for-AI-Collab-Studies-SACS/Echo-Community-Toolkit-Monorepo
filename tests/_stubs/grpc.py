"""Minimal grpc shim for test environments without grpcio installed."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

__all__ = [
    "__version__",
    "StatusCode",
    "RpcError",
    "insecure_channel",
    "server",
    "aio",
    "experimental",
    "unary_unary_rpc_method_handler",
    "method_handlers_generic_handler",
]

__version__ = "0.0-stub"


class RpcError(RuntimeError):
    """Raised when a grpc call is attempted while using the stub."""


class _StatusCode:
    UNIMPLEMENTED = "UNIMPLEMENTED"


StatusCode = _StatusCode()


def _raise(*_args, **_kwargs):
    raise RpcError("grpc stub invoked; install grpcio for network operations.")


class _StubChannel:
    def __init__(self, target: str):
        self.target = target

    def unary_unary(self, *_args, **_kwargs):
        return _raise


def insecure_channel(target: str) -> _StubChannel:
    return _StubChannel(target)


def server(*_args, **_kwargs):
    _raise()


def unary_unary_rpc_method_handler(*_args, **_kwargs):
    return _raise


def method_handlers_generic_handler(*_args, **_kwargs):
    return SimpleNamespace()


def _experimental_unary_unary(*_args, **_kwargs):
    _raise()


experimental = SimpleNamespace(unary_unary=_experimental_unary_unary)


class _AioModule(SimpleNamespace):
    def __init__(self):
        super().__init__(
            server=self._server,
            ServicerContext=object,
            insecure_channel=insecure_channel,
        )

    def _server(self, *_args, **_kwargs):
        _raise()


aio = _AioModule()


def _first_version_is_lower(_current: str, _required: str) -> bool:
    return False


_utilities = ModuleType("grpc._utilities")
_utilities.first_version_is_lower = _first_version_is_lower
sys.modules.setdefault("grpc._utilities", _utilities)

# Ensure importing `grpc` resolves to this stub.
sys.modules.setdefault("grpc", sys.modules[__name__])
