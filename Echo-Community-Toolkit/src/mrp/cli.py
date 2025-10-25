from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .adapters import png_lsb
from .headers import MRPHeader, parse_frame
from .codec import encode_with_mode
from .sidecar import validate_sidecar


def _load_headers_from_png(path: Path) -> Dict[str, MRPHeader]:
    frames = png_lsb.extract_frames(str(path))
    return {channel: parse_frame(frames[channel]) for channel in ("R", "G", "B")}


def _extract_sidecar_from_b(header: MRPHeader) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        payload = base64.b64decode(header.payload_b64.encode("utf-8")).decode("utf-8")
    except Exception as exc:  # pylint: disable=broad-except
        return None, f"unable to decode B-channel payload: {exc}"

    try:
        return json.loads(payload), None
    except json.JSONDecodeError as exc:
        return None, f"B-channel payload is not valid JSON: {exc}"


def cmd_sidecar_validate(args: argparse.Namespace) -> int:
    stego = Path(args.input)
    if not stego.exists():
        raise SystemExit(f"input not found: {stego}")

    headers = _load_headers_from_png(stego)
    sidecar_payload, decode_error = _extract_sidecar_from_b(headers["B"])

    validation = validate_sidecar(sidecar_payload, headers["R"], headers["G"], headers["B"])

    output: Dict[str, Any] = {
        "input": str(stego),
        "valid": validation.valid,
        "checks": validation.checks,
        "errors": validation.errors or None,
        "sidecar": validation.provided or None,
    }

    if decode_error:
        output["sidecar_decode_error"] = decode_error

    if args.verbose:
        output["expected"] = validation.expected
        output["schema"] = dict(validation.schema)

    print(json.dumps(output, indent=2))
    return 0 if validation.valid else 1

def cmd_encode(args: argparse.Namespace) -> int:
    meta_raw = args.meta or "{}"
    try:
        meta = json.loads(meta_raw)
    except json.JSONDecodeError as exc:  # pylint: disable=broad-except
        raise SystemExit(f"invalid metadata JSON: {exc}") from exc

    try:
        result = encode_with_mode(args.cover_png, args.out_png, args.msg, meta, mode=args.mode)
    except NotImplementedError as exc:
        raise SystemExit(f"mode '{args.mode}' not yet available: {exc}") from exc
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    print(json.dumps(result, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("mrp")
    sub = parser.add_subparsers(dest="cmd", required=True)

    encoder = sub.add_parser("encode", help="Encode a message with a selected mode")
    encoder.add_argument("cover_png", help="path to cover image PNG")
    encoder.add_argument("out_png", help="output stego PNG path")
    encoder.add_argument("--msg", required=True, help="message string to embed")
    encoder.add_argument("--meta", type=str, default="{}", help="metadata JSON string")
    encoder.add_argument(
        "--mode",
        type=str,
        default="phaseA",
        choices=["phaseA", "sigprint", "entropic", "bloom"],
        help="encoding mode",
    )
    encoder.set_defaults(func=cmd_encode)

    validator = sub.add_parser("sidecar-validate", help="Validate Phase‑A sidecar from a stego PNG")
    validator.add_argument("input", help="path to stego PNG")
    validator.add_argument(
        "--verbose",
        action="store_true",
        help="include expected sidecar and schema details in output",
    )
    validator.set_defaults(func=cmd_sidecar_validate)

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    main()
