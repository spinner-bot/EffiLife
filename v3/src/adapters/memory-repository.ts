import type { Workspace } from '../domain/models'
import type { WorkspaceRepository } from '../application/ports'
import { assertWorkspace } from '../domain/validation'

export class MemoryRepository implements WorkspaceRepository {
  private value: Workspace
  private previous: Workspace | null = null
  private queue: Promise<unknown> = Promise.resolve()
  constructor(initial: Workspace) { this.value = structuredClone(initial) }
  async read() { return structuredClone(this.value) }
  transact<T>(reducer: (current: Workspace) => { workspace: Workspace; result: T }): Promise<T> {
    const operation = this.queue.then(() => {
      const current = structuredClone(this.value)
      const { workspace, result } = reducer(current)
      assertWorkspace(workspace)
      if (workspace !== current) {
        this.previous = structuredClone(this.value)
        this.value = structuredClone(workspace)
      }
      return result
    })
    this.queue = operation.catch(() => undefined)
    return operation
  }
  async replace(workspace: Workspace) {
    assertWorkspace(workspace)
    return this.transact(current => {
      const next = { ...structuredClone(workspace), revision: Math.max(current.revision, workspace.revision) + 1 }
      return { workspace: next, result: structuredClone(next) }
    })
  }
  async readBackup() { return this.previous ? structuredClone(this.previous) : null }
  close() {}
}

