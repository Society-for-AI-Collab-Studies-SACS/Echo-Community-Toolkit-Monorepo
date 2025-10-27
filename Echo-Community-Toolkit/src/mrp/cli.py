from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from mrp.adapters import png_lsb
from mrp.frame import MRPFrame, parse_frame
from mrp.codec import (
    RitualConsentError,
    decode as codec_decode,
    encode_with_mode,
)
from mrp.sidecar import validate_sidecar
from ritual.state import default_ritual_state


def _load_headers_from_png(path: Path, *, bits_per_channel: int) -> Dict[str, MRPFrame]:
    frames = png_lsb.extract_frames(str(path), bits_per_channel=bits_per_channel)
    return {channel: parse_frame(frames[channel]) for channel in ("R", "G", "B")}


def _extract_sidecar_from_b(header: MRPFrame) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        payload = header.payload.decode("utf-8")
    except Exception as exc:  # pylint: disable=broad-except
        return None, f"unable to decode B-channel payload: {exc}"

    try:
        return json.loads(payload), None
    except json.JSONDecodeError as exc:
        return None, f"B-channel payload is not valid JSON: {exc}"


def _load_metadata(meta_raw: Optional[str], meta_file: Optional[str]) -> Dict[str, Any]:
    if meta_file:
        data_path = Path(meta_file)
        try:
            raw_text = data_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ValueError(f"metadata file not found: {data_path}") from exc
        source = raw_text
    else:
        source = meta_raw or "{}"

    try:
        return json.loads(source)
    except json.JSONDecodeError as exc:  # pylint: disable=broad-except
        raise ValueError(f"invalid metadata JSON: {exc}") from exc


def cmd_sidecar_validate(args: argparse.Namespace) -> int:
    stego = Path(args.input)
    if not stego.exists():
        raise SystemExit(f"input not found: {stego}")

    headers = _load_headers_from_png(stego, bits_per_channel=args.bpc)
    sidecar_payload, decode_error = _extract_sidecar_from_b(headers["B"])

    validation = validate_sidecar(
        sidecar_payload,
        headers["R"],
        headers["G"],
        headers["B"],
        bits_per_channel=args.bpc,
    )

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
    try:
        meta = _load_metadata(args.meta, args.meta_file)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if args.quiet and args.verbose:
        raise SystemExit("Cannot use --quiet and --verbose together.")

    try:
        result = encode_with_mode(
            args.cover_png,
            args.out_png,
            args.msg,
            meta,
            mode=args.mode,
            ritual_state=default_ritual_state,
            bits_per_channel=args.bpc,
        )
    except NotImplementedError as exc:
        raise SystemExit(f"mode '{args.mode}' not yet available: {exc}") from exc
    except RitualConsentError as exc:
        raise SystemExit(str(exc)) from exc
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if args.quiet:
        print(result["out"])
    elif args.verbose:
        print(
            json.dumps(
                {
                    "result": result,
                    "ritual": default_ritual_state.snapshot(),
                },
                indent=2,
            )
        )
    else:
        print(json.dumps(result, indent=2))
    return 0


def cmd_decode(args: argparse.Namespace) -> int:
    if args.quiet and args.verbose:
        raise SystemExit("Cannot use --quiet and --verbose together.")

    try:
        result = codec_decode(
            args.stego_png,
            ritual_state=default_ritual_state,
            bits_per_channel=args.bpc,
        )
    except RitualConsentError as exc:
        raise SystemExit(str(exc)) from exc
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if args.quiet:
        print(result["message"])
    elif args.verbose:
        print(
            json.dumps(
                {
                    "result": result,
                    "ritual": default_ritual_state.snapshot(),
                },
                indent=2,
            )
        )
    else:
        print(json.dumps(result, indent=2))
    return 0


def cmd_ritual_status(_args: argparse.Namespace) -> int:
    print(json.dumps(default_ritual_state.snapshot(), indent=2))
    return 0


def cmd_ritual_invoke(args: argparse.Namespace) -> int:
    try:
        if args.phrase:
            record = default_ritual_state.invoke_phrase(args.phrase)
        else:
            record = default_ritual_state.invoke_step(args.step)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(record, indent=2))
    return 0


def cmd_ritual_auto(_args: argparse.Namespace) -> int:
    records = default_ritual_state.auto_invoke_remaining()
    output = records if records else [default_ritual_state.snapshot()]
    print(json.dumps(output, indent=2))
    return 0


def cmd_ritual_reset(_args: argparse.Namespace) -> int:
    default_ritual_state.reset()
    print(json.dumps({"status": "reset", "coherence": default_ritual_state.coherence}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("mrp")
    sub = parser.add_subparsers(dest="cmd", required=True)

    encoder = sub.add_parser("encode", help="Encode a message with a selected mode")
    encoder.add_argument("cover_png", help="path to cover image PNG")
    encoder.add_argument("out_png", help="output stego PNG path")
    encoder.add_argument("--msg", required=True, help="message string to embed")
    meta_group = encoder.add_mutually_exclusive_group()
    meta_group.add_argument("--meta", type=str, help="metadata JSON string")
    meta_group.add_argument("--meta-file", type=str, help="path to metadata JSON file")
    encoder.add_argument(
        "--mode",
        type=str,
        default="phaseA",
        choices=["phaseA", "sigprint", "entropic", "bloom"],
        help="encoding mode",
    )
    encoder.add_argument(
        "--bpc",
        type=int,
        default=1,
        choices=png_lsb.SUPPORTED_BPC,
        help="bits per channel (1 or 4)",
    )
    encoder.add_argument("--quiet", action="store_true", help="suppress JSON output; print only output path")
    encoder.add_argument(
        "--verbose",
        action="store_true",
        help="include ritual state snapshot alongside JSON result",
    )
    encoder.set_defaults(func=cmd_encode)

    decoder = sub.add_parser("decode", help="Decode a message from a stego PNG")
    decoder.add_argument("stego_png", help="path to stego PNG")
    decoder.add_argument(
        "--bpc",
        type=int,
        default=1,
        choices=png_lsb.SUPPORTED_BPC,
        help="bits per channel (1 or 4)",
    )
    decoder.add_argument("--quiet", action="store_true", help="print only the decoded message")
    decoder.add_argument(
        "--verbose",
        action="store_true",
        help="include ritual state snapshot alongside the decode result",
    )
    decoder.set_defaults(func=cmd_decode)

    validator = sub.add_parser("sidecar-validate", help="Validate Phase‑A sidecar from a stego PNG")
    validator.add_argument("input", help="path to stego PNG")
    validator.add_argument(
        "--bpc",
        type=int,
        default=1,
        choices=png_lsb.SUPPORTED_BPC,
        help="bits per channel used for the stego PNG",
    )
    validator.add_argument(
        "--verbose",
        action="store_true",
        help="include expected sidecar and schema details in output",
    )
    validator.set_defaults(func=cmd_sidecar_validate)

    ritual = sub.add_parser("ritual", help="Inspect or advance the ritual consent state")
    ritual_sub = ritual.add_subparsers(dest="ritual_cmd", required=True)

    rit_status = ritual_sub.add_parser("status", help="Show current ritual snapshot")
    rit_status.set_defaults(func=cmd_ritual_status)

    rit_invoke = ritual_sub.add_parser("invoke", help="Invoke an individual ritual step")
    step_group = rit_invoke.add_mutually_exclusive_group(required=True)
    step_group.add_argument("--step", type=int, choices=list(range(1, 7)), help="Invoke step number 1-6")
    step_group.add_argument("--phrase", type=str, help="Invoke by mantra phrase")
    rit_invoke.set_defaults(func=cmd_ritual_invoke)

    rit_auto = ritual_sub.add_parser("auto", help="Invoke all remaining steps sequentially")
    rit_auto.set_defaults(func=cmd_ritual_auto)

    rit_reset = ritual_sub.add_parser("reset", help="Reset ritual state to baseline")
    rit_reset.set_defaults(func=cmd_ritual_reset)

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    main()
