#!/usr/bin/env python3
"""
MRP Test Example - Demonstrates the Multi-Channel Resonance Protocol verifier
"""

import json
import base64
import hashlib
import zlib
import subprocess
import sys
from pathlib import Path

def create_test_payloads():
    """Create sample MRP payloads for testing"""
    
    # R channel payload (primary data)
    r_payload = {
        "protocol": "MRP-Phase-A",
        "channel": "R",
        "message": "Primary quantum resonance data",
        "timestamp": "2025-01-12T15:30:00Z",
        "sequence": 1
    }
    
    # G channel payload (secondary data)
    g_payload = {
        "protocol": "MRP-Phase-A",
        "channel": "G",
        "message": "Secondary harmonic calibration",
        "metadata": {
            "version": 1,
            "phase": "A",
            "resonance_freq": 432
        }
    }
    
    # Compute verification data
    r_min = json.dumps(r_payload, separators=(",", ":")).encode("utf-8")
    g_min = json.dumps(g_payload, separators=(",", ":")).encode("utf-8")
    r_b64 = base64.b64encode(r_min)
    g_b64 = base64.b64encode(g_min)
    
    # Calculate CRC32 values
    crc_r = format(zlib.crc32(r_b64) & 0xFFFFFFFF, "08X")
    crc_g = format(zlib.crc32(g_b64) & 0xFFFFFFFF, "08X")
    
    # Calculate SHA256
    sha_r = hashlib.sha256(r_b64).hexdigest()
    
    # Generate XOR parity block
    parity = bytearray(len(g_b64))
    for i in range(len(g_b64)):
        if i < len(r_b64):
            parity[i] = r_b64[i] ^ g_b64[i]
        else:
            parity[i] = g_b64[i]
    parity_b64 = base64.b64encode(parity).decode("ascii")
    
    # B channel payload (verification metadata)
    b_payload = {
        "crc_r": crc_r,
        "crc_g": crc_g,
        "sha256_msg_b64": sha_r,
        "ecc_scheme": "parity",
        "parity_block_b64": parity_b64
    }
    
    # Save all payloads
    with open("mrp_lambda_R_payload.json", "w") as f:
        json.dump(r_payload, f, indent=2)
    
    with open("mrp_lambda_G_payload.json", "w") as f:
        json.dump(g_payload, f, indent=2)
    
    with open("mrp_lambda_B_payload.json", "w") as f:
        json.dump(b_payload, f, indent=2)
    
    # Create sidecar metadata
    sidecar = {
        "file": "mrp_lambda_state.png",
        "sha256_msg_b64": sha_r,
        "channels": {
            "R": {
                "payload_len": len(r_b64),
                "used_bits": (len(r_b64) + 14) * 8,
                "capacity_bits": 512 * 512  # Example for 512x512 image
            },
            "G": {
                "payload_len": len(g_b64),
                "used_bits": (len(g_b64) + 14) * 8,
                "capacity_bits": 512 * 512
            },
            "B": {
                "payload_len": len(base64.b64encode(json.dumps(b_payload, separators=(",", ":")).encode())),
                "used_bits": (len(base64.b64encode(json.dumps(b_payload, separators=(",", ":")).encode())) + 14) * 8,
                "capacity_bits": 512 * 512
            }
        },
        "headers": {
            "R": {"magic": "MRP1", "channel": "R", "flags": 1},
            "G": {"magic": "MRP1", "channel": "G", "flags": 1},
            "B": {"magic": "MRP1", "channel": "B", "flags": 1}
        }
    }
    
    with open("mrp_lambda_state_sidecar.json", "w") as f:
        json.dump(sidecar, f, indent=2)
    
    print("✅ Created MRP test payloads:")
    print(f"   R CRC32: {crc_r}")
    print(f"   G CRC32: {crc_g}")
    print(f"   SHA256:  {sha_r[:32]}...")
    print(f"   Parity:  {parity_b64[:32]}...")
    
    return {
        "r_crc": crc_r,
        "g_crc": crc_g,
        "sha256": sha_r,
        "files_created": [
            "mrp_lambda_R_payload.json",
            "mrp_lambda_G_payload.json",
            "mrp_lambda_B_payload.json",
            "mrp_lambda_state_sidecar.json"
        ]
    }

def run_verification():
    """Run the MRP verifier on test data"""
    
    # Check if verifier exists
    verifier_path = Path("mrp_verify.py")
    if not verifier_path.exists():
        verifier_path = Path("/mnt/user-data/outputs/mrp_verify.py")
    
    if not verifier_path.exists():
        print("❌ mrp_verify.py not found")
        return False
    
    # Run verification (without actual PNG since we're testing)
    cmd = [
        sys.executable, str(verifier_path),
        "--R", "mrp_lambda_R_payload.json",
        "--G", "mrp_lambda_G_payload.json",
        "--B", "mrp_lambda_B_payload.json",
        "--sidecar", "mrp_lambda_state_sidecar.json",
        "--json", "mrp_verify_report.json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("\n📊 MRP Verification Output:")
        print(result.stdout)
        
        if result.returncode == 0:
            print("\n✅ MRP Verification PASSED")
            
            # Load and display report highlights
            if Path("mrp_verify_report.json").exists():
                with open("mrp_verify_report.json", "r") as f:
                    report = json.load(f)
                    
                print("\n📋 Verification Checks:")
                for check, status in report["checks"].items():
                    status_icon = "✓" if status else "✗"
                    print(f"   {status_icon} {check}: {status}")
                    
            return True
        else:
            print("\n❌ MRP Verification FAILED")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running verifier: {e}")
        return False

def main():
    print("="*60)
    print("MRP PHASE-A VERIFICATION TEST")
    print("="*60)
    
    # Step 1: Create test payloads
    print("\n📦 Creating test payloads...")
    metadata = create_test_payloads()
    
    # Step 2: Run verification
    print("\n🔍 Running MRP verification...")
    success = run_verification()
    
    # Step 3: Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Status: {'PASS ✅' if success else 'FAIL ❌'}")
    print(f"Files created: {len(metadata['files_created'])}")
    print(f"R CRC32: {metadata['r_crc']}")
    print(f"G CRC32: {metadata['g_crc']}")
    print(f"SHA256: {metadata['sha256'][:32]}...")
    
    # Cleanup option
    print("\nTest files created:")
    for f in metadata['files_created']:
        print(f"  - {f}")
    print("\nTo clean up: rm mrp_lambda_*.json mrp_verify_report.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
