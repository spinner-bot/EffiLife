export interface FocusSession {
  todoId: string
  todoTitle: string
  startedAt: number
}

const STORAGE_KEY = 'effilife.focus-session.v1'
const CHANGE_EVENT = 'effilife:focus-session-changed'
let memorySession: FocusSession | null = null

function isValidSession(value: unknown): value is FocusSession {
  if (!value || typeof value !== 'object') return false
  const candidate = value as Partial<FocusSession>
  return typeof candidate.todoId === 'string'
    && candidate.todoId.length > 0
    && typeof candidate.todoTitle === 'string'
    && candidate.todoTitle.length > 0
    && typeof candidate.startedAt === 'number'
    && Number.isFinite(candidate.startedAt)
    && candidate.startedAt > 0
    && candidate.startedAt <= Date.now() + 60_000
}

function readStored(): FocusSession | null {
  if (typeof window === 'undefined') return memorySession
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed: unknown = JSON.parse(raw)
    if (!isValidSession(parsed)) {
      window.localStorage.removeItem(STORAGE_KEY)
      return null
    }
    return parsed
  } catch {
    return memorySession
  }
}

function emitChange(): void {
  if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent(CHANGE_EVENT))
}

export const FocusSessionService = {
  get(): FocusSession | null {
    const session = readStored()
    memorySession = session
    return session
  },

  start(session: FocusSession): void {
    if (!isValidSession(session)) return
    memorySession = session
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
    } catch {
      // Private browsing and restricted webviews may reject localStorage.
    }
    emitChange()
  },

  clear(): void {
    memorySession = null
    try {
      window.localStorage.removeItem(STORAGE_KEY)
    } catch {
      // The in-memory state is still cleared when durable storage is absent.
    }
    emitChange()
  },

  onChange(handler: () => void): () => void {
    if (typeof window === 'undefined') return () => undefined
    const onStorage = (event: StorageEvent) => {
      if (event.key === STORAGE_KEY) handler()
    }
    const onLocal = () => handler()
    window.addEventListener('storage', onStorage)
    window.addEventListener(CHANGE_EVENT, onLocal)
    return () => {
      window.removeEventListener('storage', onStorage)
      window.removeEventListener(CHANGE_EVENT, onLocal)
    }
  },
}
