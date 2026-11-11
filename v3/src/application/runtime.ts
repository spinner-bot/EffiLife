import { computed, ref, shallowRef } from 'vue'
import { emptyWorkspace } from '../domain/initial'
import type { Workspace } from '../domain/models'
import type { WorkspaceCommand } from '../domain/commands'
import { IndexedDBRepository } from '../adapters/indexeddb-repository'
import { BrowserWorkspaceEvents } from '../adapters/workspace-events'
import { WorkspaceService } from './workspace-service'

const initial = emptyWorkspace(__APP_VERSION__)
export const workspace = shallowRef<Workspace | null>(null)
export const current = computed(() => workspace.value || initial)
export const loading = ref(true)
export const startupError = shallowRef<unknown>(null)
export const pendingWrites = ref(0)
export const service = new WorkspaceService(new IndexedDBRepository(initial), undefined, new BrowserWorkspaceEvents())

export async function refresh() {
  const state = await service.read()
  if (!workspace.value || state.revision >= workspace.value.revision) workspace.value = state
  startupError.value = null
}
export async function initialize() {
  loading.value = true
  try { await refresh() } catch (error) { startupError.value = error } finally { loading.value = false }
}
export async function dispatch(command: WorkspaceCommand, operationId = crypto.randomUUID()) {
  pendingWrites.value++
  try {
    const result = await service.dispatch({ command, operationId })
    await refresh()
    return result
  } finally { pendingWrites.value-- }
}
let refreshing = false
service.subscribe(() => {
  if (refreshing) return
  refreshing = true
  refresh().catch(error => { startupError.value = error }).finally(() => { refreshing = false })
})
if (typeof window !== 'undefined') {
  window.addEventListener('focus', () => { refresh().catch(error => { startupError.value = error }) })
}

