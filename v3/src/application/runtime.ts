import { computed, ref, shallowRef } from 'vue'
import { emptyWorkspace } from '../domain/initial'
import type { Workspace } from '../domain/models'
import type { WorkspaceCommand } from '../domain/commands'
import { IndexedDBRepository } from '../adapters/indexeddb-repository'
import { BrowserWorkspaceEvents } from '../adapters/workspace-events'
import { WorkspaceService } from './workspace-service'
import { refreshQueue } from './refresh-queue'

const initial = emptyWorkspace(__APP_VERSION__)
export const workspace = shallowRef<Workspace | null>(null)
export const current = computed(() => workspace.value || initial)
export const loading = ref(true)
export const startupError = shallowRef<unknown>(null)
export const pendingWrites = ref(0)
export const service = new WorkspaceService(new IndexedDBRepository(initial), undefined, new BrowserWorkspaceEvents())

function accept(state: Workspace) {
  if (!workspace.value || state.revision >= workspace.value.revision) workspace.value = state
  startupError.value = null
}
export const refresh = refreshQueue(async () => { accept(await service.read()) })
export async function initialize() {
  loading.value = true
  try { await refresh() } catch (error) { startupError.value = error } finally { loading.value = false }
}
export async function dispatch(command: WorkspaceCommand, operationId: string = crypto.randomUUID()) {
  pendingWrites.value++
  try {
    const { workspace: state, result } = await service.dispatchCommitted({ command, operationId })
    accept(state)
    return result
  } finally { pendingWrites.value-- }
}
service.subscribe(() => {
  refresh().catch(error => { startupError.value = error })
})
if (typeof window !== 'undefined') {
  window.addEventListener('focus', () => { refresh().catch(error => { startupError.value = error }) })
}

