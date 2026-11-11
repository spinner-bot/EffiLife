import { expect, it, vi } from 'vitest'
import { WorkspaceService } from '../../src/application/workspace-service'
import { sandboxBridge } from '../../src/application/sandbox-bridge'
import { MemoryRepository } from '../../src/adapters/memory-repository'
import { emptyWorkspace } from '../../src/domain/initial'
import type { Capability } from '../../src/extensions/capabilities'
import type { CoreCommand } from '../../src/domain/commands'
import type { PackageCandidate } from '../../src/extensions/manifest'

async function setup(grants: Capability[] = ['app.layout', 'app.data.read', 'app.data.write', 'app.settings.write']) {
  const permissions: Capability[] = ['app.layout', 'app.data.read', 'app.data.write', 'app.settings.write', 'app.theme', 'app.navigation']
  const candidate: PackageCandidate = {
    manifest: { type: 'function', name: { 'en-US': 'Host test' }, author: 'Test', license: 'MIT', version: '1.0.0', formatVersion: 1, apiVersion: 1, permissions, requiredPermissions: ['app.layout'], entry: 'main.js' },
    payload: { 'main.js': btoa('EffiLife.onMount(() => {});') }, checksum: 'e'.repeat(64),
  }
  const service = new WorkspaceService(new MemoryRepository(emptyWorkspace('3.0.0')))
  await service.dispatch({ operationId: 'install', command: { type: 'installPackage', candidate, grants } })
  const dispatch = vi.fn((command, operationId) => service.dispatch({ command, operationId }))
  const host = { service, dispatch, navigate: vi.fn() }
  const identity = { kind: 'function' as const, packageId: 100000, checksum: candidate.checksum }
  return { service, host, identity, bridge: sandboxBridge(identity, host) }
}
it('exposes life data without receipts packages registry grants or audit', async () => {
  const f = await setup()
  const data = await f.bridge({ id: 'read', method: 'data.read' })
  expect(Object.keys(data as object).sort()).toEqual(['categories', 'plans', 'records', 'timePlanning', 'todos'])
  await expect(f.bridge({ id: 'registry', method: 'registry.read' })).rejects.toThrow('extensions.invalidRequest')
})
it('commits the extension write and its audit together and deduplicates transport retries', async () => {
  const f = await setup()
  const request = { id: 'create-once', method: 'data.write', params: { type: 'createPlan', title: 'Once' } }
  const result = await f.bridge(request)
  expect(await f.bridge(request)).toEqual(result)
  const state = await f.service.read()
  expect(state.plans).toHaveLength(1)
  expect(state.extensionAudit?.filter(entry => entry.action === 'write')).toHaveLength(1)
  expect(state.extensionAudit?.at(-1)).toMatchObject({ capabilities: ['app.data.write'], detail: 'createPlan' })
})
it('rejects package management and preference escalation through a data-write grant', async () => {
  const f = await setup()
  for (const params of [
    { type: 'removePackage', kind: 'function', packageId: 100000 },
    { type: 'setPackageGrants', kind: 'function', packageId: 100000, grants: ['app.theme'] },
    { type: 'savePreferences', preferences: { themeId: 2 } },
    { type: 'recoverAppearance' },
  ]) await expect(f.bridge({ id: crypto.randomUUID(), method: 'data.write', params })).rejects.toThrow('extensions.permissionDenied')
  expect((await f.service.read()).packages).toHaveLength(1)
})
it('checks revocation inside the write transaction even if an earlier host read allowed it', async () => {
  const f = await setup()
  const dispatch = f.host.dispatch
  f.host.dispatch = vi.fn(async (command, operationId) => {
    await f.service.dispatch({ operationId: 'revoke', command: { type: 'setPackageGrants', kind: 'function', packageId: 100000, grants: ['app.layout'] } })
    return dispatch(command, operationId)
  })
  const bridge = sandboxBridge(f.identity, f.host)
  await expect(bridge({ id: 'racing-write', method: 'data.write', params: { type: 'createPlan', title: 'Forbidden' } })).rejects.toThrow('extensions.permissionDenied')
  expect((await f.service.read()).plans).toEqual([])
  expect((await f.service.read()).extensionAudit?.some(row => row.action === 'write')).toBe(false)
})
it('checks the loaded content fingerprint and separates theme control from settings writes', async () => {
  const f = await setup()
  await expect(sandboxBridge({ ...f.identity, checksum: 'f'.repeat(64) }, f.host)({ id: 'stale', method: 'data.read' })).rejects.toThrow('extensions.permissionDenied')
  await expect(f.bridge({ id: 'settings', method: 'settings.write', params: { themeId: 2 } })).rejects.toThrow('extensions.permissionDenied')
  await f.bridge({ id: 'locale', method: 'settings.write', params: { locale: 'en-US' } })
  expect((await f.service.read()).preferences.locale).toBe('en-US')
})
it('rejects direct recursive wrappers and unknown commands without committing an audit', async () => {
  const f = await setup()
  const params = { type: 'extensionCommand', ...f.identity, scope: 'app.data.write', command: { type: 'createPlan', title: 'Escape' } } as unknown as CoreCommand
  await expect(f.bridge({ id: 'nested', method: 'data.write', params })).rejects.toThrow('extensions.permissionDenied')
  expect((await f.service.read()).plans).toEqual([])
})

