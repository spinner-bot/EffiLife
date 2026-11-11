import { afterEach, describe, expect, it } from 'vitest'
import { IDBFactory } from 'fake-indexeddb'
import { IndexedDBRepository } from '../../src/adapters/indexeddb-repository'
import { WorkspaceService } from '../../src/application/workspace-service'
import { emptyWorkspace } from '../../src/domain/initial'

const open: IndexedDBRepository[] = []
afterEach(() => { for (const repository of open.splice(0)) repository.close() })
function setup(factory = new IDBFactory()) {
  const initial = emptyWorkspace('3.0.0', '2026-11-11T00:00:00Z', 'Asia/Shanghai')
  const repository = new IndexedDBRepository(initial, 'test-workspace', factory)
  open.push(repository)
  let sequence = 0
  const service = new WorkspaceService(repository, () => ({
    now: '2026-11-11T01:00:00Z', id: () => crypto.randomUUID() + '-' + ++sequence,
  }))
  return { initial, repository, service, factory }
}

describe('atomic IndexedDB persistence', () => {
  it('persists confirmed results and deduplicates retries after reopening', async () => {
    const f = setup()
    const envelope = { operationId: 'plan-once', command: { type: 'createPlan', title: 'Study' } } as const
    const result = await f.service.dispatch(envelope)
    f.repository.close()
    const second = setup(f.factory)
    expect(await second.service.dispatch(envelope)).toEqual(result)
    expect((await second.service.read()).plans).toHaveLength(1)
  })
  it('serializes two independent windows without overwriting either write', async () => {
    const f = setup()
    const other = setup(f.factory)
    await Promise.all([
      f.service.dispatch({ operationId: 'first', command: { type: 'createPlan', title: 'One' } }),
      other.service.dispatch({ operationId: 'second', command: { type: 'createPlan', title: 'Two' } }),
    ])
    const state = await f.service.read()
    expect(state.plans.map(plan => plan.title).sort()).toEqual(['One', 'Two'])
    expect(state.revision).toBe(2)
  })
  it('aborts a write with dangling references without exposing partial data', async () => {
    const f = setup()
    const before = await f.service.read()
    await expect(f.repository.transact(current => ({
      workspace: { ...current, records: [{ id: 'bad', title: 'Bad', note: '', categoryId: 'missing', startAt: '2026-11-11T01:00:00Z', endAt: '2026-11-11T02:00:00Z', source: 'manual', timing: 'actual' }] },
      result: undefined,
    }))).rejects.toThrow('storage.danglingReference')
    expect(await f.service.read()).toEqual(before)
  })
  it('restores a known-good backup even when primary storage is corrupt', async () => {
    const f = setup()
    await f.service.dispatch({ operationId: 'first', command: { type: 'createPlan', title: 'Retain' } })
    await f.service.dispatch({ operationId: 'second', command: { type: 'createPlan', title: 'Later' } })
    const backup = await f.repository.readBackup()
    expect(backup!.plans).toHaveLength(1)
    await new Promise<void>((resolve, reject) => {
      const request = f.factory.open('test-workspace', 1)
      request.onsuccess = () => {
        const transaction = request.result.transaction('snapshots', 'readwrite')
        transaction.objectStore('snapshots').put({ corrupt: true }, 'workspace')
        transaction.oncomplete = () => { request.result.close(); resolve() }
        transaction.onerror = () => reject(transaction.error)
      }
    })
    await expect(f.service.read()).rejects.toThrow('storage.unsupportedSchema')
    await f.service.restoreBackup()
    expect((await f.service.read()).plans.map(plan => plan.title)).toEqual(['Retain'])
  })
  it('backs up replacement data in the same transaction', async () => {
    const f = setup()
    await f.service.dispatch({ operationId: 'first', command: { type: 'createPlan', title: 'Original' } })
    await f.service.replace(f.initial)
    expect((await f.service.read()).plans).toEqual([])
    expect((await f.repository.readBackup())!.plans[0]!.title).toBe('Original')
    await f.service.restoreBackup()
    expect((await f.service.read()).plans[0]!.title).toBe('Original')
  })
  it('reports unavailable persistence instead of silently accepting volatile writes', async () => {
    const repository = new IndexedDBRepository(emptyWorkspace('3.0.0'), 'missing', undefined)
    await expect(repository.read()).rejects.toThrow('storage.unavailable')
  })
})

