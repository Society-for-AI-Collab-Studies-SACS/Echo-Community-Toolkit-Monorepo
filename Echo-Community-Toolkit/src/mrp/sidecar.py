from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping, Optional

from .ecc import parity_hex
from .headers import MRPHeader, crc32_hex

__all__ = [
    "PHASE_A_SCHEMA",
    "REQUIRED_FIELDS",
    "SidecarValidation",
    "generate_sidecar",
    "validate_sidecar",
]

# Canonical Phase‑A schema descriptor (see assets/data/mrp_lambda_state_sidecar.json)
PHASE_A_SCHEMA: Mapping[str, Any] = {
    "carrier": "png",
    "channels": ["R", "G", "B"],
    "phase": "A",
}

# Phase‑A required verification keys embedded in the B channel.
REQUIRED_FIELDS: tuple[str, ...] = (
    "crc_r",
    "crc_g",
    "parity",
    "ecc_scheme",
    "sha256_msg",
    "sha256_msg_b64",
)

_HEX32_RE = re.compile(r"^[0-9A-F]{8}$")


@dataclass
class SidecarValidation:
    """Validation report for a decoded sidecar payload."""

    valid: bool
    checks: Dict[str, bool]
    errors: Dict[str, str]
    expected: Dict[str, Any]
    provided: Dict[str, Any]
    schema: Mapping[str, Any] = field(default_factory=dict)


def _decode_payload_bytes(header: MRPHeader) -> bytes:
    return base64.b64decode(header.payload_b64.encode("utf-8"))


def _normalised_crc(header: MRPHeader) -> str:
    if header.crc32:
        return header.crc32.upper()
    return crc32_hex(_decode_payload_bytes(header))


def _sha256_digest(payload: bytes) -> tuple[str, str]:
    digest = sha256(payload).digest()
    return digest.hex(), base64.b64encode(digest).decode("ascii")


def _try_parse_header_json(header: Optional[MRPHeader]) -> Optional[Dict[str, Any]]:
    if header is None:
        return None
    try:
        return json.loads(_decode_payload_bytes(header).decode("utf-8"))
    except Exception:
        return None


def generate_sidecar(
    r: MRPHeader,
    g: MRPHeader,
    b: Optional[MRPHeader] = None,
    *,
    include_schema: bool = False,
    schema: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a Phase‑A sidecar document from decoded headers."""

    schema_doc = schema if schema is not None else PHASE_A_SCHEMA
    document: Dict[str, Any] = {}

    if include_schema and schema_doc:
        document.update(schema_doc)

    if b is not None:
        b_payload = _try_parse_header_json(b)
        if isinstance(b_payload, dict):
            for key, value in b_payload.items():
                if key in REQUIRED_FIELDS:
                    continue
                document.setdefault(key, value)

    r_bytes = _decode_payload_bytes(r)
    g_bytes = _decode_payload_bytes(g)
    sha_hex, sha_b64 = _sha256_digest(r_bytes)

    document["crc_r"] = _normalised_crc(r)
    document["crc_g"] = _normalised_crc(g)
    document["parity"] = parity_hex(r_bytes, g_bytes)
    document["parity_len"] = max(len(r_bytes), len(g_bytes))
    document["ecc_scheme"] = "xor"
    document["sha256_msg"] = sha_hex
    document["sha256_msg_b64"] = sha_b64

    return document


def _is_upper_hex(value: Any, length: int = 8) -> bool:
    return isinstance(value, str) and bool(_HEX32_RE.fullmatch(value)) and len(value) == length


def validate_sidecar(
    sidecar: Optional[Dict[str, Any]],
    r: MRPHeader,
    g: MRPHeader,
    b: Optional[MRPHeader] = None,
    *,
    schema: Mapping[str, Any] | None = None,
) -> SidecarValidation:
    """Validate a Phase‑A sidecar payload against decoded channel headers."""

    provided = dict(sidecar or {})
    schema_doc = schema if schema is not None else PHASE_A_SCHEMA
    expected = generate_sidecar(r, g, b, include_schema=False, schema=schema_doc)

    checks: Dict[str, bool] = {}
    errors: Dict[str, str] = {}

    if not provided:
        checks["has_required_fields"] = False
        errors["has_required_fields"] = "sidecar payload is empty or missing"
        return SidecarValidation(False, checks, errors, expected, provided, schema_doc)

    missing = [key for key in REQUIRED_FIELDS if key not in provided]
    checks["has_required_fields"] = not missing
    if missing:
        errors["has_required_fields"] = f"missing keys: {', '.join(missing)}"

    core_checks = ("crc_format", "crc_match", "parity_match", "ecc_scheme_ok", "sha256_match")

    if not checks["has_required_fields"]:
        for name in core_checks:
            checks[name] = False
        return SidecarValidation(False, checks, errors, expected, provided, schema_doc)

    crc_r = provided.get("crc_r")
    crc_g = provided.get("crc_g")
    checks["crc_format"] = _is_upper_hex(crc_r) and _is_upper_hex(crc_g)
    if not checks["crc_format"]:
        errors["crc_format"] = "crc_r/crc_g must be 8-character uppercase hex strings"

    checks["crc_match"] = (
        isinstance(crc_r, str)
        and isinstance(crc_g, str)
        and crc_r.upper() == expected["crc_r"]
        and crc_g.upper() == expected["crc_g"]
    )
    if not checks["crc_match"]:
        errors["crc_match"] = f"expected crc_r={expected['crc_r']} crc_g={expected['crc_g']}"

    parity_expected = expected["parity"]
    parity_provided = provided.get("parity")
    checks["parity_match"] = isinstance(parity_provided, str) and parity_provided.upper() == parity_expected
    if not checks["parity_match"]:
        errors["parity_match"] = f"expected parity {parity_expected}"

    ecc_expected = expected["ecc_scheme"]
    ecc_provided = provided.get("ecc_scheme")
    checks["ecc_scheme_ok"] = ecc_provided == ecc_expected
    if not checks["ecc_scheme_ok"]:
        errors["ecc_scheme_ok"] = f"expected ecc_scheme {ecc_expected}"

    r_bytes = _decode_payload_bytes(r)
    sha_hex, sha_b64 = _sha256_digest(r_bytes)
    sha_hex_provided = provided.get("sha256_msg")
    sha_b64_provided = provided.get("sha256_msg_b64")
    checks["sha256_match"] = (
        isinstance(sha_hex_provided, str) and sha_hex_provided.lower() == sha_hex
    ) or (
        isinstance(sha_b64_provided, str) and sha_b64_provided == sha_b64
    )
    if not checks["sha256_match"]:
        errors["sha256_match"] = f"expected sha256_msg {sha_hex}"

    if schema_doc:
        for key, expected_value in schema_doc.items():
            if key not in provided:
                continue
            checks[f"schema_{key}"] = provided[key] == expected_value

    core_valid = all(checks.get(name, False) for name in ("has_required_fields", *core_checks))

    return SidecarValidation(core_valid, checks, errors, expected, provided, schema_doc)
