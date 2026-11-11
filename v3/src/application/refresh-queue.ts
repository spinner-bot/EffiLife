/** Coalesce reads while preserving notifications that arrive during a read. */
export function refreshQueue(read: () => Promise<void>): () => Promise<void> {
  let active: Promise<void> | undefined
  let requested = false
  return () => {
    requested = true
    if (!active) {
      active = Promise.resolve().then(async () => {
        try { do { requested = false; await read() } while (requested) }
        finally { active = undefined }
      })
    }
    return active
  }
}
