from __future__ import annotations
"""
operators_agent — run experiments aligned with the operators README:
- compute ⟨ψ|H_ECHO|ψ⟩ for given magnitudes/phases
- sweep a phase and dump CSV
- build a custom operator and evaluate
- spectral decomposition (Jacobi) of H_ECHO
"""
import argparse, json, math, csv
from pathlib import Path
from typing import Dict, Any

from echo_soulcode.hilbert import normalize, to_complex
from echo_soulcode.operators import (
    H_ECHO, bra_ket_expectation,
    spectral_jacobi, rotation_ab, rotation_bc, rotation_ac,
    phase_shifter, matmul, projector_squirrel, projector_fox, projector_paradox
)

def ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)

def eval_expectation(alpha, beta, gamma, pha, phb, phg) -> Dict[str, float]:
    a,b,g = normalize(alpha, beta, gamma)
    v = to_complex(a,b,g, pha, phb, phg)
    val = bra_ket_expectation(H_ECHO, v)
    return {"real": float(val.real), "imag": float(val.imag)}

def sweep_phase(alpha, beta, gamma, sweep='gamma', steps=36, pha=0.0, phb=0.0, phg=0.0, out_csv=Path("examples/operators/sweep.csv")):
    a,b,g = normalize(alpha, beta, gamma)
    ensure_dir(out_csv)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["phase_rad", "expectation_real", "expectation_imag"])
        for k in range(steps+1):
            t = -math.pi + 2*math.pi*k/steps
            A,B,C = pha, phb, phg
            if sweep == 'alpha': A = t
            elif sweep == 'beta': B = t
            else: C = t
            v = to_complex(a,b,g, A,B,C)
            val = bra_ket_expectation(H_ECHO, v)
            w.writerow([t, float(val.real), float(val.imag)])

def spectral(out_json=Path("examples/operators/spectral.json")):
    ensure_dir(out_json)
    evals, evecs = spectral_jacobi(H_ECHO)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump({"eigenvalues": evals, "eigenvectors": evecs}, f, indent=2)

def main():
    p = argparse.ArgumentParser(description="Operators experiments agent")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("expect", help="Evaluate <psi|H_ECHO|psi>.")
    g.add_argument("--alpha", type=float, required=True)
    g.add_argument("--beta", type=float, required=True)
    g.add_argument("--gamma", type=float, required=True)
    g.add_argument("--alpha-phase", type=float, default=0.0)
    g.add_argument("--beta-phase", type=float, default=0.0)
    g.add_argument("--gamma-phase", type=float, default=0.0)

    s = sub.add_parser("sweep", help="Sweep one phase and write CSV.")
    s.add_argument("--alpha", type=float, required=True)
    s.add_argument("--beta", type=float, required=True)
    s.add_argument("--gamma", type=float, required=True)
    s.add_argument("--sweep", choices=["alpha","beta","gamma"], default="gamma")
    s.add_argument("--steps", type=int, default=36)
    s.add_argument("--alpha-phase", type=float, default=0.0)
    s.add_argument("--beta-phase", type=float, default=0.0)
    s.add_argument("--gamma-phase", type=float, default=0.0)
    s.add_argument("--out", type=str, default="examples/operators/sweep.csv")

    e = sub.add_parser("spectral", help="Jacobi eigendecomposition of H_ECHO.")
    e.add_argument("--out", type=str, default="examples/operators/spectral.json")

    args = p.parse_args()
    if args.cmd == "expect":
        out = eval_expectation(args.alpha, args.beta, args.gamma, args.alpha_phase, args.beta_phase, args.gamma_phase)
        print(json.dumps(out, indent=2))
    elif args.cmd == "sweep":
        sweep_phase(args.alpha, args.beta, args.gamma, args.sweep, args.steps, args.alpha_phase, args.beta_phase, args.gamma_phase, Path(args.out))
        print("OK:", args.out)
    elif args.cmd == "spectral":
        spectral(Path(args.out))
        print("OK:", args.out)

if __name__ == "__main__":
    main()
