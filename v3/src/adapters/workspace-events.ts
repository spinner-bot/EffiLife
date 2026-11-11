import type { WorkspaceEvents } from '../application/ports'

export class BrowserWorkspaceEvents implements WorkspaceEvents {
  private readonly listeners = new Set<() => void>()
  private readonly channel?: BroadcastChannel
  constructor(name = 'effilife-v3-workspace') {
    if (typeof BroadcastChannel !== 'undefined') {
      this.channel = new BroadcastChannel(name)
      this.channel.onmessage = () => { for (const listener of this.listeners) listener() }
    }
  }
  publish() { this.channel?.postMessage({ type: 'workspace-updated' }) }
  subscribe(listener: () => void) {
    this.listeners.add(listener)
    return () => { this.listeners.delete(listener) }
  }
  dispose() { this.channel?.close(); this.listeners.clear() }
}

