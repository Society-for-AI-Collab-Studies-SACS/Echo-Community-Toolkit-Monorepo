import React from 'react'
import type { BundleState } from '../types/telemetry'

type Props = {
  bundle?: BundleState
  onRefresh?: () => void
}

export function BundlePanel({ bundle, onRefresh }: Props) {
  return (
    <div style={{ padding: 16 }}>
      <h2 style={{ marginBottom: 8 }}>Bundle Viewer</h2>
      <button onClick={onRefresh} style={{ marginBottom: 12 }}>
        Refresh
      </button>
      {!bundle ? (
        <p>No bundle loaded</p>
      ) : (
        <pre style={{ whiteSpace: 'pre-wrap', background: '#0f172a', color: '#f8fafc', padding: 12 }}>
          {JSON.stringify(bundle, null, 2)}
        </pre>
      )}
    </div>
  )
}
