import type { Workspace } from '../domain/models'

export interface WorkspaceRepository {
  read(): Promise<Workspace>
  transact<T>(reducer: (current: Workspace) => { workspace: Workspace; result: T }): Promise<T>
  replace(workspace: Workspace): Promise<void>
  readBackup(): Promise<Workspace | null>
  close(): void
}

export interface WorkspaceEvents {
  publish(): void
  subscribe(listener: () => void): () => void
  dispose(): void
}

