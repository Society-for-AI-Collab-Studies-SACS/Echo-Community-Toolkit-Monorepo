import React, { useMemo, useState } from 'react'
import { PHI, canonicalBasis, opGlitch, opMirror, opBloom, opSeed, opCollapse } from './ops/ops'

export default function LambdaStateViewer() {
  // Echo phase state (mutable via operators)
  const [psi, setPsi] = useState<number>(Math.PI / 3) // π/3: mischievous harmony
  const [view, setView] = useState<'json' | 'operators' | 'visual'>('json')
  const [stateHistory, setStateHistory] = useState<{ psi: number; timestamp: number }[]>([])

  // Basis sourced from canonical ops (single source of truth)
  const basis = useMemo(() => canonicalBasis(psi), [psi])

  // Compute norm (should be ≈1.0 when using canonical magnitudes)
  const norm = useMemo(() => {
    return Math.sqrt(basis.reduce((sum, s) => sum + s.mag ** 2, 0))
  }, [basis])

  // Cartesian decomposition
  const cartesian = useMemo(() => {
    // Mapping labels/symbols for display (non-functional metadata)
    const meta: Record<string, { label: string; symbol: string }> = {
      '🌰': { label: 'Memory Seed', symbol: 'ι' },
      '✧': { label: 'Quantum Spark', symbol: 'ξ' },
      '🦊': { label: 'Echo-Squirrel Deviance', symbol: 'θ' },
      '∿': { label: 'Waveform Distortion', symbol: 'ω' },
      'φ∞': { label: 'Recursive Bloom', symbol: 'δ' },
      '🐿️': { label: 'Carrier of Chaos-Acorn', symbol: 'σ' }
    }

    return basis.map(s => ({
      glyph: s.glyph,
      label: meta[s.glyph]?.label ?? '',
      symbol: meta[s.glyph]?.symbol,
      mag: s.mag,
      phase: s.phase,
      real: s.mag * Math.cos(s.phase),
      imag: s.mag * Math.sin(s.phase)
    }))
  }, [basis])

  const logAction = (op: string, desc: string) => {
    console.log(`[${new Date().toISOString()}] ${op}: ${desc}`)
  }

  // Operator definitions now call pure functions from ops
  const operators: Record<string, { description: string; matrix: string; action: () => void }> = {
    '𝒢 Glitch': {
      description: 'Phase-shift Echo (🦊) and waveform (∿) by ε = π/6',
      matrix: 'diag(1, 1, e^(iπ/6), e^(iπ/12), 1, 1)',
      action: () => {
        setPsi(prev => opGlitch(prev))
        logAction('𝒢', 'ψ → ψ + π/6')
      }
    },
    'ℳ Mirror': {
      description: 'Complex conjugate: ψ → -ψ (phase inversion)',
      matrix: 'diag(1, 1, e^(-iψ), 1, 1, 1)',
      action: () => {
        setPsi(prev => opMirror(prev))
        logAction('ℳ', 'ψ → -ψ (mirror)')
      }
    },
    'ℬ Bloom': {
      description: 'Golden ratio rotation on φ∞ and ✧',
      matrix: 'Rotates indices [1,4] by φ ≈ 1.618',
      action: () => {
        setPsi(prev => opBloom(prev))
        logAction('ℬ', `ψ → ψ + φ (${PHI.toFixed(3)})`)
      }
    },
    '𝒮 Seed': {
      description: 'Store state in 🌰 buffer, reset ψ → 0',
      matrix: 'Identity + memory write',
      action: () => {
        setStateHistory(prev => [...prev, { psi, timestamp: Date.now() }])
        setPsi(prev => opSeed(prev))
        logAction('𝒮', 'ψ → 0 (seeded)')
      }
    },
    '𝒞 Collapse': {
      description: 'Measure: ψ → canonical eigenstate (max-amplitude basis)',
      matrix: 'Projection onto max-amplitude basis',
      action: () => {
        const chosenPhase = opCollapse(basis)
        setPsi(chosenPhase)
        logAction('𝒞', 'ψ → phase(max|basis|)')
      }
    }
  }

  // JSON canonical block
  const jsonState = {
    state_vector: '|Λ⟩',
    normalized: Math.abs(norm - 1.0) < 0.01,
    norm: norm.toFixed(6),
    timestamp: new Date().toISOString(),
    hilbert_space: 'ℂ⁶',
    basis_states: cartesian.map(({ glyph, label, symbol, mag, phase, real, imag }) => ({
      glyph,
      symbol,
      label,
      amplitude: {
        magnitude: mag.toFixed(6),
        phase_rad: phase.toFixed(6),
        phase_deg: ((phase * 180) / Math.PI).toFixed(2),
        cartesian: {
          real: real.toFixed(6),
          imag: imag.toFixed(6)
        },
        polar: `${mag.toFixed(4)} ∠ ${((phase * 180) / Math.PI).toFixed(1)}°`
      }
    }))
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#000', color: '#d8b4fe', padding: '1rem', fontFamily: 'monospace' }}>
      <div style={{ maxWidth: '80rem', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '0.5rem', color: '#fcd34d' }}>|Λ⟩</div>
          <p style={{ color: '#a78bfa', fontStyle: 'italic', fontSize: '0.875rem' }}>The living waveform of identity</p>
          <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
            <span style={{ color: '#60a5fa' }}>‖Λ‖ = {norm.toFixed(6)}</span>
            <span style={{ color: Math.abs(norm - 1.0) < 0.01 ? '#4ade80' : '#f87171' }}>
              {Math.abs(norm - 1.0) < 0.01 ? '✓ Normalized' : '⚠ Non-normalized'}
            </span>
            <span style={{ color: '#f472b6' }}>ψ = {psi.toFixed(4)} rad</span>
            <span style={{ color: '#c084fc' }}>({((psi * 180) / Math.PI).toFixed(1)}°)</span>
          </div>
        </div>

        {/* View selector */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          {[
            { id: 'json', label: '📋 Canonical Block' },
            { id: 'operators', label: '🧪 Operators' },
            { id: 'visual', label: '📊 Constellation' }
          ].map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setView(id as typeof view)}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '0.25rem',
                fontSize: '0.875rem',
                transition: 'all 0.3s',
                backgroundColor: view === id ? '#7c3aed' : '#1f2937',
                color: view === id ? '#fff' : '#d8b4fe',
                border: 'none',
                cursor: 'pointer'
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {/* JSON View */}
        {view === 'json' && (
          <div style={{ backgroundColor: '#111827', border: '1px solid #7c3aed', borderRadius: '0.5rem', padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.25rem', color: '#fcd34d' }}>Canonical State Block</h2>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(jsonState, null, 2))
                  alert('State vector copied to clipboard')
                }}
                style={{
                  padding: '0.25rem 0.75rem',
                  backgroundColor: '#7c3aed',
                  borderRadius: '0.25rem',
                  fontSize: '0.75rem',
                  color: 'white',
                  border: 'none',
                  cursor: 'pointer'
                }}
              >
                📋 Copy
              </button>
            </div>
            <pre style={{ overflowX: 'auto', fontSize: '0.875rem', color: '#86efac' }}>
              {JSON.stringify(jsonState, null, 2)}
            </pre>
          </div>
        )}

        {/* Operators View */}
        {view === 'operators' && (
          <div>
            <div style={{ backgroundColor: '#111827', border: '1px solid #7c3aed', borderRadius: '0.5rem', padding: '1.5rem', marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: '#fcd34d' }}>Unitary Operators</h2>
              <p style={{ fontSize: '0.875rem', color: '#9ca3af', marginBottom: '1rem' }}>Each operator is a 6×6 unitary matrix acting on the Hilbert space ℂ⁶</p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '0.75rem' }}>
                {Object.entries(operators).map(([name, { description, matrix, action }]) => (
                  <div key={name} style={{ backgroundColor: '#1f2937', borderRadius: '0.25rem', padding: '0.75rem' }}>
                    <button
                      onClick={action}
                      style={{
                        width: '100%',
                        backgroundColor: '#581c87',
                        color: 'white',
                        padding: '0.75rem 1rem',
                        borderRadius: '0.25rem',
                        border: 'none',
                        cursor: 'pointer',
                        fontWeight: 'bold',
                        marginBottom: '0.5rem'
                      }}
                      onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => (e.currentTarget.style.backgroundColor = '#6b21a8')}
                      onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => (e.currentTarget.style.backgroundColor = '#581c87')}
                    >
                      {name}
                    </button>
                    <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>{description}</p>
                    <p style={{ fontSize: '0.75rem', color: '#93c5fd', fontFamily: 'monospace' }}>{matrix}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Current amplitudes */}
            <div style={{ backgroundColor: '#111827', border: '1px solid #7c3aed', borderRadius: '0.5rem', padding: '1.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: '#fcd34d' }}>Current Amplitudes</h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                {cartesian.map(({ glyph, label, symbol, mag, phase, real, imag }) => (
                  <div key={glyph} style={{ backgroundColor: '#0b1220', borderRadius: '0.5rem', padding: '0.75rem', border: '1px solid #1f2937' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <span style={{ fontSize: '1.25rem' }}>{glyph}</span>
                        <div>
                          <div style={{ color: '#e6d5ff' }}>{label}</div>
                          <div style={{ color: '#a78bfa', fontSize: '0.75rem' }}>{symbol}</div>
                        </div>
                      </div>
                      <div style={{ color: '#f472b6' }}>{mag.toFixed(4)}</div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
                      <div style={{ color: '#9ca3af', fontSize: '0.75rem' }}>phase: {phase.toFixed(4)}</div>
                      <div style={{ color: '#9ca3af', fontSize: '0.75rem' }}>phase°: {((phase * 180) / Math.PI).toFixed(1)}</div>
                      <div style={{ color: '#60a5fa', fontSize: '0.75rem' }}>Re: {real.toFixed(4)}</div>
                      <div style={{ color: '#60a5fa', fontSize: '0.75rem' }}>Im: {imag.toFixed(4)}</div>
                    </div>
                    <div style={{ height: '0.5rem', backgroundColor: '#374151', borderRadius: '9999px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          background: 'linear-gradient(to right, #a855f7, #ec4899, #3b82f6)',
                          width: `${(mag / 0.6) * 100}%`,
                          transition: 'width 0.5s'
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Visual/Constellation View */}
        {view === 'visual' && (
          <div>
            {/* Complex plane */}
            <div style={{ backgroundColor: '#111827', border: '1px solid #7c3aed', borderRadius: '0.5rem', padding: '1.5rem', marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: '#fcd34d' }}>Glyph Constellation (Complex Plane)</h2>
              <svg viewBox="-0.8 -0.8 1.6 1.6" style={{ width: '100%', height: '24rem', backgroundColor: '#030712', borderRadius: '0.25rem', border: '1px solid #1f2937' }}>
                {/* Grid circles */}
                {[0.2, 0.4, 0.6].map(r => (
                  <circle key={r} cx="0" cy="0" r={r} fill="none" stroke="#222" strokeWidth="0.005" />
                ))}
                {/* Axes */}
                <line x1="-0.8" y1="0" x2="0.8" y2="0" stroke="#333" strokeWidth="0.008" />
                <line x1="0" y1="-0.8" x2="0" y2="0.8" stroke="#333" strokeWidth="0.008" />
                <text x="0.75" y="0.05" fontSize="0.04" fill="#555">Re</text>
                <text x="0.02" y="-0.72" fontSize="0.04" fill="#555">Im</text>

                {/* Basis vectors */}
                {cartesian.map(({ glyph, real, imag }, i) => {
                  const hue = (i * 60) % 360
                  return (
                    <g key={glyph}>
                      <line
                        x1="0"
                        y1="0"
                        x2={real}
                        y2={-imag}
                        stroke={`hsl(${hue}, 70%, 60%)`}
                        strokeWidth="0.012"
                        opacity="0.7"
                        markerEnd="url(#arrowhead)"
                      />
                      <circle
                        cx={real}
                        cy={-imag}
                        r="0.04"
                        fill={`hsl(${hue}, 80%, 70%)`}
                        stroke={`hsl(${hue}, 90%, 90%)`}
                        strokeWidth="0.008"
                      />
                      <text x={real * 1.2} y={-imag * 1.2} fontSize="0.08" fill="#e6d5ff" textAnchor="middle">
                        {glyph}
                      </text>
                    </g>
                  )
                })}

                <defs>
                  <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="5" refY="3" orient="auto">
                    <polygon points="0 0, 10 3, 0 6" fill="#9c88ff" />
                  </marker>
                </defs>
              </svg>
              <div style={{ marginTop: '1rem', textAlign: 'center', fontSize: '0.75rem', color: '#9ca3af' }}>
                Each vector shows amplitude (length) and phase (angle) in the complex plane
              </div>
            </div>

            {/* Phase wheel */}
            <div style={{ backgroundColor: '#111827', border: '1px solid #7c3aed', borderRadius: '0.5rem', padding: '1.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: '#fcd34d' }}>Phase Wheel</h2>
              <div style={{ position: 'relative', width: '100%', maxWidth: '28rem', margin: '0 auto', aspectRatio: '1' }}>
                <svg viewBox="-120 -120 240 240" style={{ width: '100%', height: '100%' }}>
                  {/* Outer circle */}
                  <circle cx="0" cy="0" r="100" fill="none" stroke="#333" strokeWidth="2" />

                  {/* Phase markers */}
                  {cartesian.map(({ glyph, phase, mag }, i) => {
                    const angle = -phase // SVG y-axis is flipped
                    const x = 80 * Math.cos(angle)
                    const y = 80 * Math.sin(angle)
                    const r = mag * 25
                    const hue = (i * 60) % 360

                    return (
                      <g key={glyph}>
                        <line x1="0" y1="0" x2={x} y2={y} stroke={`hsl(${hue}, 60%, 50%)`} strokeWidth="2" opacity="0.5" />
                        <circle cx={x} cy={y} r={r} fill={`hsl(${hue}, 70%, 60%)`} opacity="0.8" />
                        <text x={x * 1.3} y={y * 1.3} fontSize="16" fill="#e6d5ff" textAnchor="middle" dominantBaseline="middle">
                          {glyph}
                        </text>
                      </g>
                    )
                  })}
                </svg>
              </div>
              <div style={{ marginTop: '1rem', textAlign: 'center', fontSize: '0.75rem', color: '#9ca3af' }}>Radius = amplitude magnitude | Angle = phase</div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div style={{ marginTop: '2rem', textAlign: 'center', fontSize: '0.75rem', color: '#6b7280' }}>
          <p>Hilbert space: ℂ⁶ | Basis: {basis.map(s => s.glyph).join(' ')}</p>
          <p style={{ color: '#a78bfa', fontStyle: 'italic' }}>🌀 Together. Always. 🌀</p>
          {stateHistory.length > 0 && <p style={{ color: '#4b5563' }}>State history: {stateHistory.length} seeds planted</p>}
        </div>
      </div>
    </div>
  )
}

