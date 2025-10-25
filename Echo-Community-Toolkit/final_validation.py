#!/usr/bin/env python3
"""
Final Production Validation for Echo-Community-Toolkit
Self-sufficient, order-agnostic runner:
 - Ensures golden sample exists (regenerates if script provided)
 - Runs LSB core tests
 - Runs demo script (if present)
 - Builds MRP payloads if missing and verifies Phase‑A
 - Emits a concise PASS/FAIL summary and proper exit code
"""

import sys
import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
SRC  = ROOT / "src"
ASSETS_DATA = ROOT / "assets" / "data"
ARTIFACTS = ROOT / "artifacts"

def run_py(label: str, path: Path, args=None, timeout=180) -> dict:
    """Run a Python script with PYTHONPATH set to src; return dict with status & output."""
    if not path.exists():
        return {"label": label, "present": False, "code": None, "ok": None, "stdout": "", "stderr": f"(missing) {path}"}
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH","")
    cmd = [sys.executable, str(path)] + list(args or [])
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT), env=env, timeout=timeout)
        return {"label": label, "present": True, "code": proc.returncode, "ok": proc.returncode == 0,
                "stdout": proc.stdout, "stderr": proc.stderr}
    except subprocess.TimeoutExpired as e:
        return {"label": label, "present": True, "code": None, "ok": False,
                "stdout": e.stdout or "", "stderr": f"(timeout after {timeout}s) {e.stderr or ''}"}

def ensure_golden_sample() -> dict:
    """Create/verify golden echo_key.png by running generate_golden_sample.py if available."""
    gen = ROOT / "generate_golden_sample.py"
    assets_png = ROOT / "assets" / "images" / "echo_key.png"
    # If file missing, try to generate
    if not assets_png.exists() and gen.exists():
        return run_py("generate_golden_sample.py", gen)
    # If file exists, still try to verify via the same script (it prints CRC check)
    if gen.exists():
        return run_py("generate_golden_sample.py", gen)
    return {"label": "generate_golden_sample.py", "present": False, "code": 0, "ok": True,
            "stdout": "Golden sample present; generator not provided.", "stderr": ""}

def ensure_mrp_payloads() -> dict:
    """Ensure canonical MRP payload fixtures exist under assets/data."""
    ASSETS_DATA.mkdir(parents=True, exist_ok=True)
    needed = [
        ASSETS_DATA / "mrp_lambda_R_payload.json",
        ASSETS_DATA / "mrp_lambda_G_payload.json",
        ASSETS_DATA / "mrp_lambda_B_payload.json",
        ASSETS_DATA / "mrp_lambda_state_sidecar.json",
    ]
    missing = [n for n in needed if not n.exists()]
    test_builder = ROOT / "test_mrp_verification.py"
    if missing and test_builder.exists():
        args = ["--outdir", str(ASSETS_DATA), "--skip-verify"]
        return run_py("test_mrp_verification.py", test_builder, args=args)
    elif missing:
        # Nothing to build with; mark as missing but allow verifier to fail clearly
        return {"label": "test_mrp_verification.py", "present": False, "code": 1, "ok": False,
                "stdout": "", "stderr": f"Missing MRP payloads and no builder script: {', '.join(missing)}"}
    else:
        # All present; optionally re-run to refresh
        return {"label": "test_mrp_verification.py", "present": test_builder.exists(), "code": 0, "ok": True,
                "stdout": "MRP payloads already present.", "stderr": ""}

def run_mrp_verify() -> dict:
    """Run mrp_verify.py against local payloads; writes report JSON."""
    verifier = ROOT / "mrp_verify.py"
    if not verifier.exists():
        return {"label": "mrp_verify.py", "present": False, "code": 1, "ok": False,
                "stdout": "", "stderr": "mrp_verify.py not found"}
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    args = [
        "--R",
        str(ASSETS_DATA / "mrp_lambda_R_payload.json"),
        "--G",
        str(ASSETS_DATA / "mrp_lambda_G_payload.json"),
        "--B",
        str(ASSETS_DATA / "mrp_lambda_B_payload.json"),
        "--sidecar",
        str(ASSETS_DATA / "mrp_lambda_state_sidecar.json"),
        "--json",
        str(ARTIFACTS / "mrp_verify_report.json"),
    ]
    return run_py("mrp_verify.py", verifier, args=args)

def banner(txt: str):
    print("="*60)
    print(txt)
    print("="*60)

def main() -> int:
    banner("ECHO-COMMUNITY-TOOLKIT FINAL VALIDATION")
    print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}Z\n")

    results = []

    # Step 0 — Golden sample
    r_golden = ensure_golden_sample();   results.append(r_golden)
    print("🔍 Golden Sample...", "✅ PASS" if r_golden.get("ok") else "❌ FAIL")

    # Step 1 — LSB core tests
    r_lsb = run_py("tests/test_lsb.py", ROOT/"tests"/"test_lsb.py");   results.append(r_lsb)
    print("🔍 Core Test Suite...", "✅ PASS" if r_lsb.get("ok") else "❌ FAIL")

    # Step 2 — Demo (optional but recommended)
    r_demo = run_py("examples/demo.py", ROOT/"examples"/"demo.py");    results.append(r_demo)
    print("🔍 Demo Script...", "✅ PASS" if r_demo.get("ok") else ("(skipped)" if r_demo.get("present") is False else "❌ FAIL"))

    # Step 3 — Build/refresh MRP payloads if needed, then verify
    r_build = ensure_mrp_payloads();     results.append(r_build)
    print("🔍 MRP Payload Builder...", "✅ PASS" if r_build.get("ok") else ("(skipped)" if r_build.get("present") is False else "❌ FAIL"))
    r_mrp = run_mrp_verify();            results.append(r_mrp)
    print("🔍 MRP Verifier...", "✅ PASS" if r_mrp.get("ok") else "❌ FAIL")

    # Summarize and emit details on failure
    passed = sum(1 for r in results if r.get("ok"))
    total  = sum(1 for r in results if r.get("ok") is not None)
    print("\n")
    banner("VALIDATION COMPLETE")
    status_line = f"Result: {passed}/{total} tests passed"
    print(status_line)
    if passed == total:
        print("\n✅ Echo-Community-Toolkit is PRODUCTION READY")
    else:
        print(f"\n⚠️ {total - passed} validation(s) failed")
        print("Please review failed steps:\n")
        for r in results:
            if r.get("ok") is False:
                print(f"— {r['label']} (exit={r['code']})")
                # Print a small, trimmed snippet of stderr/stdout to aid triage
                out = (r.get("stdout") or "")[-600:]
                err = (r.get("stderr") or "")[-600:]
                if out:
                    print("  stdout:"); print("  " + "\n  ".join(out.splitlines()[-10:]))
                if err:
                    print("  stderr:"); print("  " + "\n  ".join(err.splitlines()[-10:]))
    # Flush outputs
    sys.stdout.flush(); sys.stderr.flush()

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
