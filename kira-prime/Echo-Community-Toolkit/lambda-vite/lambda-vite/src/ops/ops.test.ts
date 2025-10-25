import { describe, it, expect } from 'vitest'
import { opGlitch, opMirror, opBloom, opSeed, opCollapse, canonicalBasis, PHI } from './ops'

const approx = (a: number, b: number, eps = 1e-9) => Math.abs(a - b) < eps;

describe('Operator suite 𝒢/ℬ/𝓜/𝓢/𝓒', () => {
  it('𝒢 Glitch: adds π/6 to ψ', () => {
    const psi0 = Math.PI / 3;
    const psi1 = opGlitch(psi0);
    expect(approx(psi1, psi0 + Math.PI / 6)).toBe(true);
  });

  it('𝓜 Mirror: inverts phase', () => {
    const psi0 = Math.PI / 3;
    const psi1 = opMirror(psi0);
    expect(approx(psi1, (2 * Math.PI - psi0) % (2 * Math.PI))).toBe(true);
  });

  it('ℬ Bloom: adds φ', () => {
    const psi0 = Math.PI / 3;
    const psi1 = opBloom(psi0);
    expect(approx(psi1, (psi0 + PHI) % (2 * Math.PI))).toBe(true);
  });

  it('𝓢 Seed: zeroes phase', () => {
    const psi0 = Math.PI / 3;
    const psi1 = opSeed(psi0);
    expect(psi1).toBe(0);
  });

  it('𝓒 Collapse: chooses phase of max-amplitude basis (φ∞)', () => {
    const psi0 = Math.PI / 3;
    const basis = canonicalBasis(psi0);
    const chosen = opCollapse(basis);
    // In canonical magnitudes, φ∞ has the largest magnitude and phase 0
    expect(chosen).toBe(0);
  });
});
