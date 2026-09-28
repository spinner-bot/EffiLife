export type WorkspaceChangeSource = 'todos' | 'plans' | 'records' | 'archive' | 'settings'

export const WORKSPACE_CHANGED_EVENT = 'effilife:workspace-changed'

export function notifyWorkspaceChanged(source: WorkspaceChangeSource): void {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(WORKSPACE_CHANGED_EVENT, { detail: { source } }))
}

export function onWorkspaceChanged(listener: (source?: WorkspaceChangeSource) => void): () => void {
  if (typeof window === 'undefined') return () => undefined
  const handler = (event: Event) => {
    const source = (event as CustomEvent<{ source?: WorkspaceChangeSource }>).detail?.source
    listener(source)
  }
  window.addEventListener(WORKSPACE_CHANGED_EVENT, handler)
  return () => window.removeEventListener(WORKSPACE_CHANGED_EVENT, handler)
}
