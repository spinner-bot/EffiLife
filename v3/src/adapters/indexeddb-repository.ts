import type { Workspace } from '../domain/models'
import type { WorkspaceRepository } from '../application/ports'
import { assertWorkspace } from '../domain/validation'
import { DomainError } from '../domain/errors'

const STORE = 'snapshots'
const PRIMARY = 'workspace'
const BACKUP = 'backup'

export class IndexedDBRepository implements WorkspaceRepository {
  private connection?: IDBDatabase
  private opening?: Promise<IDBDatabase>
  constructor(
    private readonly initial: Workspace,
    private readonly name = 'effilife-v3',
    private readonly factory: IDBFactory | undefined = globalThis.indexedDB,
  ) {}

  private open(): Promise<IDBDatabase> {
    if (this.connection) return Promise.resolve(this.connection)
    if (this.opening) return this.opening
    this.opening = new Promise((resolve, reject) => {
      if (!this.factory) { reject(new DomainError('storage.unavailable')); return }
      let settled = false
      const timeout = setTimeout(() => {
        settled = true
        this.opening = undefined
        reject(new DomainError('storage.openTimeout'))
      }, 10000)
      let request: IDBOpenDBRequest
      try { request = this.factory.open(this.name, 1) } catch {
        clearTimeout(timeout); reject(new DomainError('storage.unavailable')); return
      }
      request.onupgradeneeded = () => {
        if (!request.result.objectStoreNames.contains(STORE)) request.result.createObjectStore(STORE)
      }
      request.onsuccess = () => {
        clearTimeout(timeout)
        if (settled) { request.result.close(); return }
        this.connection = request.result
        this.connection.onversionchange = () => this.close()
        resolve(this.connection)
      }
      request.onerror = () => { clearTimeout(timeout); reject(new DomainError('storage.openFailed')) }
      request.onblocked = () => { /* The bounded timeout gives the UI a recoverable failure. */ }
    })
    this.opening.catch(() => { this.opening = undefined })
    return this.opening
  }

  private async readKey(key: string): Promise<unknown> {
    const database = await this.open()
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(STORE, 'readonly')
      let value: unknown
      transaction.objectStore(STORE).get(key).onsuccess = event => {
        value = (event.target as IDBRequest).result
      }
      transaction.oncomplete = () => resolve(value)
      transaction.onerror = () => reject(new DomainError('storage.readFailed'))
      transaction.onabort = () => reject(new DomainError('storage.readFailed'))
    })
  }

  async read(): Promise<Workspace> {
    const value = await this.readKey(PRIMARY) ?? structuredClone(this.initial)
    assertWorkspace(value)
    return structuredClone(value)
  }

  async readBackup(): Promise<Workspace | null> {
    const value = await this.readKey(BACKUP)
    if (!value) return null
    assertWorkspace(value)
    return structuredClone(value)
  }

  async transact<T>(reducer: (current: Workspace) => { workspace: Workspace; result: T }): Promise<T> {
    const database = await this.open()
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(STORE, 'readwrite')
      const store = transaction.objectStore(STORE)
      let result: T
      let failure: unknown
      store.get(PRIMARY).onsuccess = event => {
        try {
          const current = (event.target as IDBRequest).result ?? structuredClone(this.initial)
          assertWorkspace(current)
          const outcome = reducer(current)
          assertWorkspace(outcome.workspace)
          result = outcome.result
          if (outcome.workspace !== current) {
            store.put(structuredClone(current), BACKUP)
            store.put(structuredClone(outcome.workspace), PRIMARY)
          }
        } catch (error) { failure = error; transaction.abort() }
      }
      transaction.oncomplete = () => resolve(result!)
      transaction.onerror = () => reject(failure || new DomainError('storage.writeFailed'))
      transaction.onabort = () => reject(failure || new DomainError('storage.writeFailed'))
    })
  }

  async replace(workspace: Workspace): Promise<void> {
    assertWorkspace(workspace)
    const database = await this.open()
    await new Promise<void>((resolve, reject) => {
      const transaction = database.transaction(STORE, 'readwrite')
      const store = transaction.objectStore(STORE)
      store.get(PRIMARY).onsuccess = event => {
        try {
          const current = (event.target as IDBRequest).result
          let revision = workspace.revision
          if (current) {
            try {
              assertWorkspace(current)
              store.put(structuredClone(current), BACKUP)
              revision = Math.max(revision, current.revision)
            } catch { /* Preserve the existing known-good backup when primary is corrupt. */ }
          }
          store.put({ ...structuredClone(workspace), revision: revision + 1 }, PRIMARY)
        } catch { transaction.abort() }
      }
      transaction.oncomplete = () => resolve()
      transaction.onerror = () => reject(new DomainError('storage.writeFailed'))
      transaction.onabort = () => reject(new DomainError('storage.writeFailed'))
    })
  }

  close() {
    this.connection?.close()
    this.connection = undefined
    this.opening = undefined
  }
}

