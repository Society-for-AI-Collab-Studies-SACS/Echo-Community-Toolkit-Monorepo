# Specialized Echo ↔ Hilbert example:
# - Accepts α,β,γ and phases θα, θβ, θγ
# - Emits canonical JSON via library CLI

import subprocess, sys, json, os, tempfile

def run(alpha=0.58, beta=0.39, gamma=0.63, pha=0.0, phb=0.0, phg=0.0, out_path="examples/echo_live.json"):
    cmd = [
        sys.executable, "-m", "echo_soulcode.live_read",
        "--alpha", str(alpha), "--beta", str(beta), "--gamma", str(gamma),
        "--alpha-phase", str(pha), "--beta-phase", str(phb), "--gamma-phase", str(phg),
        "--out", out_path
    ]
    subprocess.check_call(cmd)

if __name__ == "__main__":
    run()
