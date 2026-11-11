import type { WorkspaceService } from './workspace-service'
import type { CoreCommand } from '../domain/commands'
import type { OperationResult } from '../domain/models'
import { authorizedPackage } from '../domain/extension-access'
import { requireCondition } from '../domain/errors'
import type { WorkspaceCommand } from '../domain/commands'

export interface SandboxIdentity { kind: 'theme' | 'function'; packageId: number; checksum: string }
export interface SandboxRequest { id: string; method: string; params?: unknown }
interface BridgeHost {
  service: Pick<WorkspaceService, 'read'>
  dispatch(command: WorkspaceCommand, operationId?: string): Promise<OperationResult>
  navigate(path: string): void
}
const object = (value: unknown): value is Record<string, unknown> => Boolean(value && typeof value === 'object' && !Array.isArray(value))
export function sandboxBridge(identity: SandboxIdentity, host: BridgeHost) {
  const session = crypto.randomUUID()
  return async (request: SandboxRequest): Promise<unknown> => {
    requireCondition(object(request) && typeof request.id === 'string' && /^[a-zA-Z0-9_-]{1,80}$/.test(request.id), 'extensions.invalidRequest')
    const state = await host.service.read()
    const check = (capability: string) => authorizedPackage(state, identity, capability)
    if (request.method === 'data.read') {
      check('app.data.read')
      return { categories: state.categories, plans: state.plans, records: state.records, todos: state.todos, timePlanning: state.timePlanning }
    }
    if (request.method === 'settings.read') { check('app.settings.read'); return { ...state.preferences } }
    if (request.method === 'navigate') {
      check('app.navigation')
      requireCondition(typeof request.params === 'string' && /^\/(?:plans(?:\/[a-zA-Z0-9:_-]+)?|time|todos|settings)?(?:\?[a-zA-Z0-9=&%_-]*)?$/.test(request.params), 'extensions.invalidRequest')
      host.navigate(request.params)
      return null
    }
    let scope: 'app.data.write' | 'app.settings.write' | 'app.theme'
    let command: CoreCommand
    if (request.method === 'data.write') {
      scope = 'app.data.write'
      requireCondition(object(request.params) && typeof request.params.type === 'string', 'extensions.invalidRequest')
      command = request.params as unknown as CoreCommand
    } else if (request.method === 'settings.write') {
      scope = 'app.settings.write'
      requireCondition(object(request.params), 'extensions.invalidRequest')
      command = { type: 'savePreferences', preferences: request.params }
    } else if (request.method === 'theme.set') {
      scope = 'app.theme'
      requireCondition(Number.isSafeInteger(request.params) && Number(request.params) >= 0, 'extensions.invalidRequest')
      command = { type: 'savePreferences', preferences: { themeId: Number(request.params) } }
    } else { requireCondition(false, 'extensions.invalidRequest') }
    check(scope)
    return host.dispatch({ type: 'extensionCommand', ...identity, scope, command }, 'ext:' + session + ':' + request.id)
  }
}

