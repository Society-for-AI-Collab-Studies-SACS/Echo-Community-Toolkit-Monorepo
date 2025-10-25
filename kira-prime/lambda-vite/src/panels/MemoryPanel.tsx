import React from 'react'
import type { MemorySnapshot } from '../types/telemetry'

type Props = {
  memory?: MemorySnapshot
  onRefresh?: () => void
}

export function MemoryPanel({ memory, onRefresh }: Props) {
  return (
    <div style={{ padding: 16 }}>
      <h2 style={{ marginBottom: 8 }}>Memory Viewer</h2>
      <button onClick={onRefresh} style={{ marginBottom: 12 }}>
        Refresh
      </button>
      {!memory ? (
        <p>No memory snapshot</p>
      ) : (
        <pre style={{ whiteSpace: 'pre-wrap', background: '#0f172a', color: '#f8fafc', padding: 12 }}>
          {JSON.stringify(memory, null, 2)}
        </pre>
      )}
    </div>
  )
}
