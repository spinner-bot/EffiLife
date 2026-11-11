import { expect, it, vi } from 'vitest'
import { reactive } from 'vue'
import { refreshQueue } from '../../src/application/refresh-queue'
import { WorkspaceService } from '../../src/application/workspace-service'
import { MemoryRepository } from '../../src/adapters/memory-repository'
import { emptyWorkspace } from '../../src/domain/initial'

it('drains notifications received while an older snapshot is still loading', async () => {
  const releases: Array<() => void> = []
  const read = vi.fn(() => new Promise<void>(resolve => { releases.push(resolve) }))
  const refresh = refreshQueue(read)
  const first = refresh()
  await Promise.resolve()
  const second = refresh()
  const third = refresh()
  releases.shift()!()
  await vi.waitFor(() => expect(read).toHaveBeenCalledTimes(2))
  let finished = false
  first.then(() => { finished = true })
  await Promise.resolve()
  expect(finished).toBe(false)
  releases.shift()!()
  await Promise.all([first, second, third])
  expect(finished).toBe(true)
})

it('accepts new refreshes after a failed read', async () => {
  const read = vi.fn().mockRejectedValueOnce(new Error('offline')).mockResolvedValue(undefined)
  const refresh = refreshQueue(read)
  await expect(refresh()).rejects.toThrow('offline')
  await refresh()
  expect(read).toHaveBeenCalledTimes(2)
})

it('returns durable state even if post-commit notification or a later read fails', async () => {
  const repository = new MemoryRepository(emptyWorkspace('3.0.0'))
  const service = new WorkspaceService(repository, undefined, {
    publish: () => { throw new Error('channel closed') }, subscribe: () => () => {}, dispose: () => {},
  })
  const outcome = await service.dispatchCommitted(reactive({ operationId: 'reactive-create', command: { type: 'createPlan' as const, title: 'Reliable' } }))
  vi.spyOn(repository, 'read').mockRejectedValue(new Error('later read failed'))
  expect(outcome.workspace.plans[0]?.title).toBe('Reliable')
  expect(outcome.result.entityId).toBe(outcome.workspace.plans[0]?.id)
  await expect(service.read()).rejects.toThrow('later read failed')
  const retry = await service.dispatchCommitted({ operationId: 'reactive-create', command: { type: 'createPlan', title: 'Reliable' } })
  expect(retry.workspace.plans).toHaveLength(1)
  expect(retry.result).toEqual(outcome.result)
})

it('normalizes reactive archive snapshots before replacing persistent data', async () => {
  const service = new WorkspaceService(new MemoryRepository(emptyWorkspace('3.0.0')))
  await expect(service.replace(reactive(emptyWorkspace('3.0.0')))).resolves.toMatchObject({ revision: 1, schemaVersion: 1 })
  expect((await service.read()).revision).toBe(1)
})

it('acknowledges import and restore even when any subsequent primary read fails', async () => {
  const repository = new MemoryRepository(emptyWorkspace('3.0.0'))
  const service = new WorkspaceService(repository)
  await service.dispatch({ operationId: 'before-import', command: { type: 'createPlan', title: 'Retained backup' } })
  const read = vi.spyOn(repository, 'read').mockRejectedValue(new Error('later read failed'))
  expect((await service.replace(emptyWorkspace('3.0.0'))).plans).toEqual([])
  const restored = await service.restoreBackup()
  expect(restored.plans[0]?.title).toBe('Retained backup')
  expect(restored.revision).toBe(3)
  expect(read).not.toHaveBeenCalled()
})
