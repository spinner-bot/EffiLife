export type WorkspaceChangeSource = 'todos' | 'plans' | 'records' | 'archive' | 'settings'

export const WORKSPACE_CHANGED_EVENT = 'effilife:workspace-changed'
const WORKSPACE_CHANNEL = 'effilife-workspace'

let channel: BroadcastChannel | null = null
let subscriberCount = 0

function getChannel(): BroadcastChannel | null {
  if (typeof BroadcastChannel === 'undefined') return null
  if (!channel) channel = new BroadcastChannel(WORKSPACE_CHANNEL)
  return channel
}

export function notifyWorkspaceChanged(source: WorkspaceChangeSource): void {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(WORKSPACE_CHANGED_EVENT, { detail: { source } }))
  channel?.postMessage({ source })
}

export function onWorkspaceChanged(listener: (source?: WorkspaceChangeSource) => void): () => void {
  if (typeof window === 'undefined') return () => undefined
  const handler = (event: Event) => {
    const source = (event as CustomEvent<{ source?: WorkspaceChangeSource }>).detail?.source
    listener(source)
  }
  const broadcast = getChannel()
  const broadcastHandler = (event: MessageEvent<{ source?: WorkspaceChangeSource }>) => listener(event.data?.source)
  window.addEventListener(WORKSPACE_CHANGED_EVENT, handler)
  broadcast?.addEventListener('message', broadcastHandler)
  subscriberCount += 1
  return () => {
    window.removeEventListener(WORKSPACE_CHANGED_EVENT, handler)
    broadcast?.removeEventListener('message', broadcastHandler)
    subscriberCount -= 1
    if (subscriberCount === 0) {
      channel?.close()
      channel = null
    }
  }
}
