# Build canonical Echo anchor JSON files deterministically.
import subprocess, sys, json, hashlib, os

def sha256_file(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def run_anchor(out_path: str, alpha, beta, gamma, a_phase, b_phase, g_phase, timestamp, seed):
    cmd = [
        sys.executable, "-m", "echo_soulcode.live_read",
        "--alpha", str(alpha), "--beta", str(beta), "--gamma", str(gamma),
        "--alpha-phase", str(a_phase), "--beta-phase", str(b_phase), "--gamma-phase", str(g_phase),
        "--timestamp", timestamp, "--seed", seed, "--out", out_path
    ]
    subprocess.check_call(cmd)

def main():
    os.makedirs("examples/anchors", exist_ok=True)
    # Anchor profile A (phi-phase baseline)
    out_a = "examples/anchors/echo_anchors_phiA.json"
    run_anchor(out_a, 0.58, 0.39, 0.63, 0.0, 0.1, -0.2, "2025-10-12T00:00:00Z", "ANCHOR_V1")
    h_a = sha256_file(out_a)

    manifest = {
        "version": "1.0",
        "anchors": [
            {
                "name": "phiA",
                "file": out_a,
                "sha256": h_a,
                "alpha": 0.58, "beta": 0.39, "gamma": 0.63,
                "alpha_phase": 0.0, "beta_phase": 0.1, "gamma_phase": -0.2,
                "timestamp": "2025-10-12T00:00:00Z",
                "seed": "ANCHOR_V1"
            }
        ]
    }
    with open("examples/anchors/manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

if __name__ == "__main__":
    main()
