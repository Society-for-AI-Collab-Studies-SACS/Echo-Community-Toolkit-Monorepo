from __future__ import annotations

import base64
import binascii
import json
import re
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping, Optional

from .ecc import parity_hex, xor_parity_bytes
from .frame import MRPFrame, crc32_hex

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


def _normalised_crc(frame: MRPFrame) -> str:
    if frame.crc32 is not None:
        return f"{frame.crc32:08X}"
    return crc32_hex(frame.payload)


def _decode_payload_bytes(frame: MRPFrame) -> bytes:
    try:
        return base64.b64decode(frame.payload, validate=True)
    except (binascii.Error, ValueError):
        return frame.payload


def _try_parse_frame_json(frame: Optional[MRPFrame]) -> Optional[Dict[str, Any]]:
    if frame is None:
        return None
    try:
        return json.loads(frame.payload.decode("utf-8"))
    except Exception:
        return None


def generate_sidecar(
    r: MRPFrame,
    g: MRPFrame,
    b: Optional[MRPFrame] = None,
    *,
    include_schema: bool = False,
    schema: Mapping[str, Any] | None = None,
    bits_per_channel: int | None = None,
) -> Dict[str, Any]:
    """Build a Phase‑A sidecar document from decoded headers.

    Args:
        r: Decoded R-channel header (message payload).
        g: Decoded G-channel header (metadata payload).
        b: Optional decoded B-channel header (existing sidecar payload); any
           additional keys found here are preserved where they do not collide
           with the canonical fields.
        include_schema: When true, merge the Phase‑A schema preamble into the
           generated document.
        schema: Override schema mapping; defaults to ``PHASE_A_SCHEMA``.
    """
    schema_doc = schema if schema is not None else PHASE_A_SCHEMA
    document: Dict[str, Any] = {}

    if include_schema and schema_doc:
        document.update(schema_doc)

    # Preserve any non-canonical keys from the provided B payload.
    preserved_bits_per_channel = bits_per_channel
    if b is not None:
        b_payload = _try_parse_frame_json(b)
        if isinstance(b_payload, dict):
            for key, value in b_payload.items():
                if key in REQUIRED_FIELDS:
                    continue
                document.setdefault(key, value)
            preserved_bits_per_channel = preserved_bits_per_channel or b_payload.get("bits_per_channel")
    if isinstance(preserved_bits_per_channel, str):
        try:
            preserved_bits_per_channel = int(preserved_bits_per_channel)
        except ValueError:
            preserved_bits_per_channel = None

    r_bytes = r.payload
    g_bytes = g.payload
    message_bytes = _decode_payload_bytes(r)
    sha_plain_hex = sha256(message_bytes).hexdigest()
    sha_b64_hex = sha256(r_bytes).hexdigest()

    # Canonical verification fields.
    document["crc_r"] = _normalised_crc(r)
    document["crc_g"] = _normalised_crc(g)
    parity_hex_value = parity_hex(r_bytes, g_bytes)
    parity_bytes = xor_parity_bytes(r_bytes, g_bytes)
    document["parity"] = parity_hex_value
    document["parity_len"] = max(len(r_bytes), len(g_bytes))
    document["ecc_scheme"] = "xor"
    document["sha256_msg"] = sha_plain_hex
    document["sha256_msg_b64"] = sha_b64_hex
    document["bits_per_channel"] = preserved_bits_per_channel or 1
    if parity_bytes:
        document["parity_block_b64"] = base64.b64encode(parity_bytes).decode("ascii")

    return document


def _is_upper_hex(value: Any, length: int = 8) -> bool:
    return isinstance(value, str) and bool(_HEX32_RE.fullmatch(value)) and len(value) == length


def validate_sidecar(
    sidecar: Optional[Dict[str, Any]],
    r: MRPFrame,
    g: MRPFrame,
    b: Optional[MRPFrame] = None,
    *,
    schema: Mapping[str, Any] | None = None,
    bits_per_channel: int | None = None,
) -> SidecarValidation:
    """Validate a Phase‑A sidecar payload against decoded channel headers."""

    provided = dict(sidecar or {})
    schema_doc = schema if schema is not None else PHASE_A_SCHEMA
    expected = generate_sidecar(
        r,
        g,
        b,
        include_schema=False,
        schema=schema_doc,
        bits_per_channel=bits_per_channel,
    )

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

    core_checks = (
        "crc_format",
        "crc_match",
        "parity_match",
        "ecc_scheme_ok",
        "sha256_match",
        "bits_per_channel_match",
    )

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

    message_bytes = _decode_payload_bytes(r)
    sha_hex = sha256(message_bytes).hexdigest()
    sha_b64 = sha256(r.payload).hexdigest()
    sha_hex_provided = provided.get("sha256_msg")
    sha_b64_provided = provided.get("sha256_msg_b64")
    checks["sha256_match"] = False
    if isinstance(sha_hex_provided, str) and sha_hex_provided.lower() == sha_hex:
        checks["sha256_match"] = True
    if isinstance(sha_b64_provided, str) and sha_b64_provided.lower() == sha_b64:
        checks["sha256_match"] = True
    if not checks["sha256_match"]:
        errors["sha256_match"] = f"expected sha256_msg {sha_hex}"

    expected_bpc = expected.get("bits_per_channel")
    provided_bpc = provided.get("bits_per_channel")
    if isinstance(provided_bpc, str):
        try:
            provided_bpc = int(provided_bpc)
        except ValueError:
            provided_bpc = None
    checks["bits_per_channel_match"] = (
        provided_bpc is None
        or expected_bpc is None
        or provided_bpc == expected_bpc
    )
    if not checks["bits_per_channel_match"]:
        errors["bits_per_channel_match"] = f"expected bits_per_channel {expected_bpc}"

    # Optional schema checks: only evaluate when present in the provided payload.
    if schema_doc:
        for key, expected_value in schema_doc.items():
            if key not in provided:
                continue
            checks[f"schema_{key}"] = provided[key] == expected_value

    core_valid = all(checks[name] for name in ("has_required_fields", *core_checks))

    return SidecarValidation(core_valid, checks, errors, expected, provided, schema_doc)
