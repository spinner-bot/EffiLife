import type { WorkspaceRepository, WorkspaceEvents } from './ports'
import type { CommandEnvelope } from '../domain/commands'
import type { CommandContext, Workspace } from '../domain/models'
import { execute } from '../domain/engine'
import { DomainError } from '../domain/errors'

function plainDto<T>(value: T): T {
  try { return JSON.parse(JSON.stringify(value)) as T } catch { throw new DomainError('storage.invalidWorkspace') }
}

export class WorkspaceService {
  constructor(
    readonly repository: WorkspaceRepository,
    private readonly context: () => CommandContext = () => ({ now: new Date().toISOString(), id: () => crypto.randomUUID() }),
    private readonly events?: WorkspaceEvents,
  ) {}
  read() { return this.repository.read() }
  private notify() {
    // Cross-window notification is best effort; a completed transaction must
    // never be reported as failed because a channel has already closed.
    try { this.events?.publish() } catch { /* A focus refresh also reconciles windows. */ }
  }
  async dispatchCommitted(envelope: CommandEnvelope) {
    const context = this.context()
    const command = plainDto(envelope)
    const result = await this.repository.transact(current => {
      const outcome = execute(current, command, context)
      return { workspace: outcome.workspace, result: outcome }
    })
    this.notify()
    return result
  }
  async dispatch(envelope: CommandEnvelope) {
    return (await this.dispatchCommitted(envelope)).result
  }
  async replace(workspace: Workspace) {
    await this.repository.replace(plainDto(workspace))
    this.notify()
  }
  async restoreBackup() {
    const backup = await this.repository.readBackup()
    if (!backup) throw new DomainError('storage.noBackup')
    await this.replace(backup)
  }
  subscribe(listener: () => void) { return this.events?.subscribe(listener) || (() => {}) }
  dispose() { this.repository.close(); this.events?.dispose() }
}

