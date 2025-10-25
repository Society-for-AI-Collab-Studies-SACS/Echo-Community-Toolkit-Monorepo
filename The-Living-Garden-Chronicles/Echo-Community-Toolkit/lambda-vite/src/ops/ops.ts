/**
 * Pure operator helpers for testing and reuse.
 * Hilbert basis ordering: [🌰, ✧, 🦊, ∿, φ∞, 🐿️]
 */

export const TWO_PI = Math.PI * 2;
export const PHI = 1.618033988749;
// Choose NORM so that squared magnitudes sum ≈ 1 for canonicalBasis
// Sum of squares of raw magnitudes ≈ 3.9969, so NORM ≈ 2.0
export const NORM = 2.0;

export type Basis = {
  glyph: string;
  mag: number;   // normalized magnitude
  phase: number; // radians
}[];

/** Normalize angle into [0, 2π) */
export function normAngle(a: number): number {
  const t = a % TWO_PI;
  return t < 0 ? t + TWO_PI : t;
}

/** Glitch operator: ψ → ψ + ε */
export function opGlitch(psi: number, epsilon = Math.PI / 6): number {
  return normAngle(psi + epsilon);
}

/** Mirror operator: ψ → -ψ (conjugation-like) */
export function opMirror(psi: number): number {
  return normAngle(-psi);
}

/** Bloom operator: ψ → ψ + φ */
export function opBloom(psi: number): number {
  return normAngle(psi + PHI);
}

/** Seed operator: ψ → 0 */
export function opSeed(_psi: number): number {
  return 0;
}

/** Collapse operator: choose phase of max-amplitude basis */
export function opCollapse(basis: Basis): number {
  if (basis.length === 0) return 0;
  let max = basis[0];
  for (const s of basis) {
    if (s.mag > max.mag) max = s;
  }
  return normAngle(max.phase);
}

/** Canonical basis magnitudes & phases matching LambdaStateViewer */
export function canonicalBasis(psi: number): Basis {
  return [
    { glyph: '🌰', mag: 0.71 / NORM, phase: 0 },
    { glyph: '✧', mag: 0.68 / NORM, phase: Math.PI / 4 },
    { glyph: '🦊', mag: 0.92 / NORM, phase: psi },
    { glyph: '∿', mag: 0.64 / NORM, phase: Math.PI / 6 },
    { glyph: 'φ∞', mag: 1.0 / NORM, phase: 0 },
    { glyph: '🐿️', mag: 0.88 / NORM, phase: 0 },
  ];
}
