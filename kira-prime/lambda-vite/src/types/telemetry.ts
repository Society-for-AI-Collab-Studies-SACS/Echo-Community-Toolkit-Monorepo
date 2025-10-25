export type TelemetryEventType =
  | 'memory.loaded'
  | 'bundle.loaded'
  | 'operator.applied'
  | 'search.run'

export interface TelemetryEvent<T = unknown> {
  type: TelemetryEventType
  ts: number
  payload?: T
}

export interface MemorySnapshot {
  id?: string
  ts: string
  items: Array<{ key: string; value: unknown; tags?: string[] }>
}

export interface BundleState {
  version: string
  channel: 'R' | 'G' | 'B' | 'RGB'
  payload: Record<string, unknown>
}
