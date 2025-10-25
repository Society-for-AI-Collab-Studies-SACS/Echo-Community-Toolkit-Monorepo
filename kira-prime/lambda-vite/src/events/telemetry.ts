import type { TelemetryEvent, TelemetryEventType } from '../types/telemetry'

type Listener<T = unknown> = (event: TelemetryEvent<T>) => void

export class TelemetryBus {
  private listeners = new Map<TelemetryEventType, Set<Listener>>()

  on<T>(type: TelemetryEventType, fn: Listener<T>): () => void {
    const set = this.listeners.get(type) ?? new Set<Listener>()
    set.add(fn as Listener)
    this.listeners.set(type, set)
    return () => {
      set.delete(fn as Listener)
      if (set.size === 0) {
        this.listeners.delete(type)
      }
    }
  }

  emit<T>(type: TelemetryEventType, payload?: T) {
    const ev: TelemetryEvent<T> = { type, ts: Date.now(), payload }
    for (const listener of this.listeners.get(type) ?? []) {
      listener(ev)
    }
  }

  clear() {
    this.listeners.clear()
  }
}

export const telemetry = new TelemetryBus()
