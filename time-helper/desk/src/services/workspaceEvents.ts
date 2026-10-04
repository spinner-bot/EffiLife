export type WorkspaceChangeSource = 'todos' | 'plans' | 'records' | 'archive' | 'settings' | 'network'

export const WORKSPACE_CHANGED_EVENT = 'effilife:workspace-changed'
const WORKSPACE_CHANNEL = 'effilife-workspace'
const LOCALE_STORAGE_KEY = 'efflife_locale'
// BroadcastChannel is unavailable in some embedded WebViews. Keep a tiny
// storage-event envelope as a transport fallback; it is not workspace data.
const WORKSPACE_STORAGE_KEY = 'effilife_workspace_event'
const WORKSPACE_ORIGIN = typeof globalThis.crypto?.randomUUID === 'function'
  ? globalThis.crypto.randomUUID()
  : Math.random().toString(36).slice(2)

type WorkspaceEnvelope = {
  source?: WorkspaceChangeSource
  origin?: string
  id?: string
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
  const message: WorkspaceEnvelope = {
    source,
    origin: WORKSPACE_ORIGIN,
    // Storage events are edge-triggered: a repeated identical JSON value may
    // not emit a second event. Make every notification distinguishable.
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
  }
  window.dispatchEvent(new CustomEvent(WORKSPACE_CHANGED_EVENT, { detail: message }))
  // A sender without local subscribers should not create a long-lived
  // channel merely to announce a change; the storage transport also reaches
  // other windows and has no retained object to clean up.
  const workspaceChannel = subscriberCount > 0 ? getChannel() : null
  let deliveredRemotely = false
  try {
    if (workspaceChannel) {
      channel?.postMessage(message)
      deliveredRemotely = true
    }
  } catch {
    // A restricted WebView may expose BroadcastChannel but reject messaging.
  }
  if (!deliveredRemotely) {
    try {
      window.localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(message))
    } catch {
      // Some private/restricted contexts reject localStorage. Same-window
      // listeners have already received the CustomEvent above.
    }
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
  const storageHandler = (event: StorageEvent) => {
    if (event.key === LOCALE_STORAGE_KEY) listener('settings', true)
    if (event.key !== WORKSPACE_STORAGE_KEY || !event.newValue) return
    try {
      const message = JSON.parse(event.newValue) as WorkspaceEnvelope
      if (message.origin !== WORKSPACE_ORIGIN && message.source) {
        listener(message.source, true)
      }
    } catch {
      // Ignore malformed compatibility events rather than interrupting sync.
    }
  }
  window.addEventListener('storage', storageHandler)
  broadcast?.addEventListener('message', broadcastHandler)
  subscriberCount += 1
  let active = true
  return () => {
    if (!active) return
    active = false
    window.removeEventListener(WORKSPACE_CHANGED_EVENT, handler)
    window.removeEventListener('storage', storageHandler)
    broadcast?.removeEventListener('message', broadcastHandler)
    subscriberCount = Math.max(0, subscriberCount - 1)
    if (subscriberCount === 0) {
      channel?.close()
      channel = null
    }
  }
}
