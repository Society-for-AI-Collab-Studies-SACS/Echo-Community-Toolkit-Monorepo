import React from 'react'
import LambdaStateViewer from './LambdaStateViewer'
import { BundlePanel } from './panels/BundlePanel'
import { MemoryPanel } from './panels/MemoryPanel'
import { telemetry } from './events/telemetry'
import type { BundleState, MemorySnapshot } from './types/telemetry'

type Tab = 'state' | 'bundle' | 'memory'

type EchoClient = {
  getBundle?: () => Promise<BundleState>
  getMemory?: () => Promise<MemorySnapshot>
}

const getClient = (): EchoClient | undefined => {
  return typeof window !== 'undefined' ? ((window as any).EchoClient as EchoClient) : undefined
}

const FALLBACK_BUNDLE: BundleState = {
  version: 'dev-sample',
  channel: 'RGB',
  payload: { note: 'No bundle data supplied; showing scaffold sample.' }
}

const FALLBACK_MEMORY: MemorySnapshot = {
  ts: new Date().toISOString(),
  items: [
    { key: 'psi', value: Math.PI / 3, tags: ['sample'] },
    { key: 'layer', value: 'L2' }
  ]
}

export default function App(): JSX.Element {
  const [tab, setTab] = React.useState<Tab>('state')
  const [bundle, setBundle] = React.useState<BundleState>()
  const [memory, setMemory] = React.useState<MemorySnapshot>()

  const refreshBundle = React.useCallback(async () => {
    const client = getClient()
    if (client?.getBundle) {
      try {
        const data = await client.getBundle()
        setBundle(data)
        telemetry.emit<BundleState>('bundle.loaded', data)
        return
      } catch (err) {
        console.warn('Failed to load bundle from EchoClient:', err)
      }
    }
    setBundle(prev => prev ?? FALLBACK_BUNDLE)
    telemetry.emit<BundleState>('bundle.loaded', FALLBACK_BUNDLE)
  }, [])

  const refreshMemory = React.useCallback(async () => {
    const client = getClient()
    if (client?.getMemory) {
      try {
        const data = await client.getMemory()
        setMemory(data)
        telemetry.emit<MemorySnapshot>('memory.loaded', data)
        return
      } catch (err) {
        console.warn('Failed to load memory snapshot:', err)
      }
    }
    setMemory(prev => prev ?? FALLBACK_MEMORY)
    telemetry.emit<MemorySnapshot>('memory.loaded', FALLBACK_MEMORY)
  }, [])

  React.useEffect(() => {
    void refreshBundle()
    void refreshMemory()
  }, [refreshBundle, refreshMemory])

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', background: '#020617', color: '#e2e8f0', minHeight: '100vh' }}>
      <header style={{ display: 'flex', gap: 12, padding: 16, borderBottom: '1px solid #1e293b' }}>
        <button
          onClick={() => setTab('state')}
          style={{
            padding: '6px 12px',
            borderRadius: 6,
            border: '1px solid #334155',
            background: tab === 'state' ? '#1e293b' : 'transparent',
            color: '#e2e8f0',
            cursor: 'pointer'
          }}
        >
          Λ State
        </button>
        <button
          onClick={() => setTab('bundle')}
          style={{
            padding: '6px 12px',
            borderRadius: 6,
            border: '1px solid #334155',
            background: tab === 'bundle' ? '#1e293b' : 'transparent',
            color: '#e2e8f0',
            cursor: 'pointer'
          }}
        >
          Bundle
        </button>
        <button
          onClick={() => setTab('memory')}
          style={{
            padding: '6px 12px',
            borderRadius: 6,
            border: '1px solid #334155',
            background: tab === 'memory' ? '#1e293b' : 'transparent',
            color: '#e2e8f0',
            cursor: 'pointer'
          }}
        >
          Memory
        </button>
      </header>

      {tab === 'state' && <LambdaStateViewer />}
      {tab === 'bundle' && <BundlePanel bundle={bundle} onRefresh={() => void refreshBundle()} />}
      {tab === 'memory' && <MemoryPanel memory={memory} onRefresh={() => void refreshMemory()} />}
    </div>
  )
}
