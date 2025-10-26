#!/usr/bin/env python3
"""Generate sample MRP payloads and run the Phase-A verifier."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
import zlib
from pathlib import Path
from typing import Dict, List


def create_test_payloads(outdir: Path) -> Dict[str, str]:
    """Create sample R/G/B payloads plus the sidecar in ``outdir``."""
    outdir.mkdir(parents=True, exist_ok=True)

    r_payload = {
        "protocol": "MRP-Phase-A",
        "channel": "R",
        "message": "Primary quantum resonance data",
        "timestamp": "2025-01-12T15:30:00Z",
        "sequence": 1,
    }
    g_payload = {
        "protocol": "MRP-Phase-A",
        "channel": "G",
        "message": "Secondary harmonic calibration",
        "metadata": {"version": 1, "phase": "A", "resonance_freq": 432},
    }

    r_min = json.dumps(r_payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    g_min = json.dumps(g_payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    crc_r = format(zlib.crc32(r_min) & 0xFFFFFFFF, "08X")
    crc_g = format(zlib.crc32(g_min) & 0xFFFFFFFF, "08X")

    sha_r_digest = hashlib.sha256(r_min).digest()
    sha_r_hex = sha_r_digest.hex()
    sha_r_b64 = base64.b64encode(sha_r_digest).decode("ascii")

    parity_len = max(len(r_min), len(g_min))
    parity_bytes = bytearray(parity_len)
    for i in range(parity_len):
        r_val = r_min[i] if i < len(r_min) else 0
        g_val = g_min[i] if i < len(g_min) else 0
        parity_bytes[i] = r_val ^ g_val
    parity_hex = bytes(parity_bytes).hex().upper()

    bits_per_channel = 1

    b_payload = {
        "crc_r": crc_r,
        "crc_g": crc_g,
        "sha256_msg": sha_r_hex,
        "sha256_msg_b64": sha_r_b64,
        "ecc_scheme": "xor",
        "parity": parity_hex,
        "parity_len": parity_len,
        "bits_per_channel": bits_per_channel,
    }

    payload_paths = {
        "R": outdir / "mrp_lambda_R_payload.json",
        "G": outdir / "mrp_lambda_G_payload.json",
        "B": outdir / "mrp_lambda_B_payload.json",
        "sidecar": outdir / "mrp_lambda_state_sidecar.json",
    }

    payload_paths["R"].write_text(json.dumps(r_payload, indent=2), encoding="utf-8")
    payload_paths["G"].write_text(json.dumps(g_payload, indent=2), encoding="utf-8")
    payload_paths["B"].write_text(json.dumps(b_payload, indent=2), encoding="utf-8")

    sidecar = {
        "file": "mrp_lambda_state.png",
        "sha256_msg": sha_r_hex,
        "sha256_msg_b64": sha_r_b64,
        "parity": parity_hex,
        "parity_len": parity_len,
        "ecc_scheme": "xor",
        "bits_per_channel": bits_per_channel,
        "channels": {
            "R": {
                "payload_len": len(r_min),
                "used_bits": (len(r_min) + 14) * 8,
                "capacity_bits": 512 * 512,
            },
            "G": {
                "payload_len": len(g_min),
                "used_bits": (len(g_min) + 14) * 8,
                "capacity_bits": 512 * 512,
            },
            "B": {
                "payload_len": len(json.dumps(b_payload, separators=(",", ":"), sort_keys=True).encode("utf-8")),
                "used_bits": (
                    len(json.dumps(b_payload, separators=(",", ":"), sort_keys=True).encode("utf-8")) + 14
                )
                * 8,
                "capacity_bits": 512 * 512,
            },
        },
        "headers": {
            "R": {"magic": "MRP1", "channel": "R", "flags": 1},
            "G": {"magic": "MRP1", "channel": "G", "flags": 1},
            "B": {"magic": "MRP1", "channel": "B", "flags": 1},
        },
    }
    payload_paths["sidecar"].write_text(json.dumps(sidecar, indent=2), encoding="utf-8")

    print("✅ Created MRP test payloads in", outdir)
    print(f"   R CRC32: {crc_r}")
    print(f"   G CRC32: {crc_g}")
    print(f"   SHA256:  {sha_r_hex[:32]}…")
    print(f"   Parity:  {parity_hex[:32]}… (len={parity_len})")

    return {k: str(v) for k, v in payload_paths.items()}


def run_verification(payloads: Dict[str, str], image: str, report_path: Path | None) -> bool:
    """Invoke ``mrp_verify.py`` with generated payloads."""
    verifier_path = Path("mrp_verify.py")
    if not verifier_path.exists():
        verifier_path = Path("/mnt/user-data/outputs/mrp_verify.py")
    if not verifier_path.exists():
        print("❌ mrp_verify.py not found")
        return False

    cmd: List[str] = [sys.executable, str(verifier_path)]
    if image:
        cmd.append(image)
    cmd.extend(
        [
            "--R",
            payloads["R"],
            "--G",
            payloads["G"],
            "--B",
            payloads["B"],
            "--sidecar",
            payloads["sidecar"],
        ]
    )
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        cmd.extend(["--json", str(report_path)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception as exc:
        print(f"❌ Error running verifier: {exc}")
        return False

    print("\n📊 MRP Verification Output:")
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    ok = result.returncode == 0
    if ok:
        print("\n✅ MRP Verification PASSED")
        if report_path and report_path.exists():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            print("\n📋 Verification Checks:")
            for name, status in report["checks"].items():
                icon = "✓" if status else "✗"
                print(f"   {icon} {name}: {status}")
    else:
        print("\n❌ MRP Verification FAILED")

    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Phase-A payload fixtures and run the verifier.")
    parser.add_argument("--outdir", default="assets/data", help="Directory to store payload JSON files.")
    parser.add_argument("--image", default="", help="Optional stego PNG path to provide capacity context.")
    parser.add_argument("--json-report", default="", help="Optional path to write mrp_verify.py JSON report.")
    parser.add_argument(
        "--skip-verify", action="store_true", help="Only generate payload files; do not invoke mrp_verify.py."
    )
    args = parser.parse_args()

    outdir = Path(args.outdir)
    payloads = create_test_payloads(outdir)
    report_path = Path(args.json_report) if args.json_report else outdir / "mrp_verify_report.json"

    success = True
    if not args.skip_verify:
        success = run_verification(payloads, args.image, report_path)

    print("\n📦 Summary:")
    print(json.dumps({"created": payloads, "verification_passed": success}, indent=2))
    print("\nTo clean up: rm -f", " ".join(f'"{p}"' for p in payloads.values()), f'"{report_path}"')

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
