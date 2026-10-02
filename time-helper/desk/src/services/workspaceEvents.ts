export type WorkspaceChangeSource = 'todos' | 'plans' | 'records' | 'archive' | 'settings' | 'network'

export const WORKSPACE_CHANGED_EVENT = 'effilife:workspace-changed'
const WORKSPACE_CHANNEL = 'effilife-workspace'
const WORKSPACE_ORIGIN = typeof globalThis.crypto?.randomUUID === 'function'
  ? globalThis.crypto.randomUUID()
  : Math.random().toString(36).slice(2)

type WorkspaceEnvelope = {
  source?: WorkspaceChangeSource
  origin?: string
}

let channel: BroadcastChannel | null = null
let subscriberCount = 0

function getChannel(): BroadcastChannel | null {
  if (typeof BroadcastChannel === 'undefined') return null
  if (!channel) {
    try {
      channel = new BroadcastChannel(WORKSPACE_CHANNEL)
    } catch {
      return null
    }
  }
  return channel
}

export function notifyWorkspaceChanged(source: WorkspaceChangeSource): void {
  if (typeof window === 'undefined') return
  const message: WorkspaceEnvelope = { source, origin: WORKSPACE_ORIGIN }
  window.dispatchEvent(new CustomEvent(WORKSPACE_CHANGED_EVENT, { detail: message }))
  try {
    channel?.postMessage(message)
  } catch {
    // A restricted WebView may expose BroadcastChannel but reject messaging.
    // The same-window CustomEvent above remains the reliable fallback.
  }
}

export function onWorkspaceChanged(listener: (source?: WorkspaceChangeSource, remote?: boolean) => void): () => void {
  if (typeof window === 'undefined') return () => undefined
  const handler = (event: Event) => {
    const message = (event as CustomEvent<WorkspaceEnvelope>).detail
    listener(message?.source, false)
  }
  const broadcast = getChannel()
  const broadcastHandler = (event: MessageEvent<WorkspaceEnvelope>) => {
    listener(event.data?.source, event.data?.origin !== WORKSPACE_ORIGIN)
  }
  window.addEventListener(WORKSPACE_CHANGED_EVENT, handler)
  broadcast?.addEventListener('message', broadcastHandler)
  subscriberCount += 1
  let active = true
  return () => {
    if (!active) return
    active = false
    window.removeEventListener(WORKSPACE_CHANGED_EVENT, handler)
    broadcast?.removeEventListener('message', broadcastHandler)
    subscriberCount = Math.max(0, subscriberCount - 1)
    if (subscriberCount === 0) {
      channel?.close()
      channel = null
    }
  }
}
