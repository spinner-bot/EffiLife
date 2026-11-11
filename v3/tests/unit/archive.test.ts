import { describe, expect, it } from 'vitest'
import JSZip from 'jszip'
import { emptyWorkspace } from '../../src/domain/initial'
import { exportArchive, inspectArchive, sha256 } from '../../src/adapters/archive'
import { assertWorkspace } from '../../src/domain/validation'

const rawPlan = {
  head: { index: 1, name: 'Mathematics', date: [2026, 11, 10] },
  main: [{
    name: 'Calculus', info: 'Topic', group: { '1_3': { title: 'All', description: '' }, '1_2': { title: 'Part', description: '' } },
    plan: [null, { is_active: true, content: 'Limits', t_m: 10 }, null, { is_active: false, content: 'Historical item', t_m: 5 }],
  }],
  log: [{ day: 1, plan: 'A1', time: [10, 99], content: 'Made progress' }, { day: 1, plan: 'A3', time: [11, 0], content: 'Historical progress' }],
}

describe('portable archive pipeline', () => {
  it('round-trips a v3 workspace without losing configuration or receipts', async () => {
    const state = emptyWorkspace('3.0.0', '2026-11-11T00:00:00Z', 'Asia/Shanghai')
    const result = await exportArchive(state, '3.0.0')
    const preview = await inspectArchive(result.bytes, '3.0.0', 'Asia/Shanghai')
    expect(preview.source).toBe('v3')
    expect(preview.workspace).toEqual(state)
  })
  it('rejects modified payloads even if they contain valid JSON', async () => {
    const { bytes } = await exportArchive(emptyWorkspace('3.0.0'), '3.0.0')
    const zip = await JSZip.loadAsync(bytes)
    zip.file('payload/workspace.json', JSON.stringify(emptyWorkspace('9.0.0')))
    const changed = await zip.generateAsync({ type: 'uint8array' })
    await expect(inspectArchive(changed, '3.0.0', 'UTC')).rejects.toThrow('archive.checksumMismatch')
  })
  it('previews v2 bundles and retains fuzzy and deleted-task log semantics', async () => {
    const values = {
      app: { locale: 'en-US', plans: { Workday: { type: '切分制' } }, audioSettings: { enabled: true } },
      records: { '2026-11-11': [{ id: 'old-record', start: '09:00', end: '09:40', content: 'Study', tag: 'Study' }] },
      todos: [],
      todo_categories: [],
      plan_helper: { plans: [rawPlan], archives: [] },
    }
    const zip = new JSZip()
    const checksums: Record<string, string> = {}
    for (const [name, value] of Object.entries(values)) {
      const content = new TextEncoder().encode(JSON.stringify(value))
      zip.file('data/' + name + '.json', content)
      checksums[name] = await sha256(content)
    }
    zip.file('manifest.json', JSON.stringify({ format: 'effilife.bundle', format_version: '1.0.0', datasets: Object.keys(values), dataset_sha256: checksums }))
    const preview = await inspectArchive(await zip.generateAsync({ type: 'uint8array' }), '3.0.0', 'Asia/Shanghai')
    const plan = preview.workspace.plans[0]!
    expect(plan.logs[0]).toMatchObject({ timePrecision: 'hour', content: 'Made progress' })
    expect(plan.logs[0]!.recordIds).toEqual([])
    expect(plan.logs[1]!.taskId).toBeTruthy()
    expect(preview.workspace.records).toHaveLength(1)
    expect(plan.nodes.find(node => node.title === 'Limits')!.estimatedMinutes).toBe(60)
    expect(preview.workspace.legacy!.source).toEqual(values)
    expect(preview.workspace.preferences.locale).toBe('en-US')
  })
  it('keeps archived plans with reused legacy IDs distinct from active plans', async () => {
    const input = { planHelper: { plans: [rawPlan], archives: [{ payload: { plan: rawPlan, archived_at: '2026-11-11T00:00:00Z' } }] } }
    const result = await inspectArchive(new TextEncoder().encode(JSON.stringify(input)), '3.0.0', 'Asia/Shanghai')
    expect(result.counts).toMatchObject({ plans: 1, archivedPlans: 1, logs: 4 })
    expect(() => assertWorkspace(result.workspace)).not.toThrow()
    const ids = result.workspace.plans.flatMap(plan => plan.logs.map(log => log.id))
    expect(new Set(ids).size).toBe(ids.length)
  })
  it.each(['../escape.json', '/absolute.json', 'C:/escape.json'])('rejects unsafe ZIP entry %s', async name => {
    const zip = new JSZip()
    zip.file(name, '{}')
    await expect(inspectArchive(await zip.generateAsync({ type: 'uint8array' }), '3.0.0', 'UTC')).rejects.toThrow('archive.unsafePath')
  })
  it('rejects case-colliding entries and symlinks', async () => {
    const duplicate = new JSZip().file('Data.json', '{}').file('data.json', '{}')
    await expect(inspectArchive(await duplicate.generateAsync({ type: 'uint8array' }), '3.0.0', 'UTC')).rejects.toThrow('archive.duplicateEntry')
    const symbolic = new JSZip().file('link', 'target', { unixPermissions: 0o120777 })
    await expect(inspectArchive(await symbolic.generateAsync({ type: 'uint8array', platform: 'UNIX' }), '3.0.0', 'UTC')).rejects.toThrow('archive.symlink')
  })
  it('rejects future schema and unreadable input without modifying a workspace', async () => {
    await expect(inspectArchive(new TextEncoder().encode(JSON.stringify({ schemaVersion: 99 })), '3.0.0', 'UTC')).rejects.toThrow('storage.unsupportedSchema')
    await expect(inspectArchive(new Uint8Array([1, 2, 3]), '3.0.0', 'UTC')).rejects.toThrow('archive.invalidZip')
  })
  it('imports standalone todo exports with checklists scheduling and independent priority flags', async () => {
    const data = { version: '0.5.0', categories: [{ id: 'work', name: 'Work', color: '#526ac9' }], todos: [{ id: 'legacy', title: 'Weekly review', description: 'Main', notes: 'Extra', created_at: '2026-11-01T00:00:00Z', updated_at: 'invalid', category: 'work', priority: 'urgent-important', status: 'in-progress', pinned: true, sort_order: 3, recurrence: 'weekly', deadline_warning_days: 7, subtasks: [{ id: 'read', title: 'Read', completed: true }] }] }
    const result = await inspectArchive(new TextEncoder().encode(JSON.stringify(data)), '3.0.0', 'Asia/Shanghai')
    expect(result.workspace.todos[0]).toMatchObject({ title: 'Weekly review', description: 'Main\n\nExtra', status: 'in-progress', pinned: true, urgent: true, important: true, sortOrder: 3, recurrence: { frequency: 'week', interval: 1 }, deadlineWarningDays: 7, subtasks: [{ title: 'Read', completed: true }] })
    expect(result.workspace.todos[0]?.subtasks?.[0]?.completedAt).toBeUndefined()
    expect(result.workspace.categories.find(category => category.id === result.workspace.todos[0]?.categoryId)?.name).toBe('Work')
    expect(result.workspace.legacy?.source).toEqual(data)
  })
  it('reconciles legacy record owners without losing actual time on conflicting forward links', async () => {
    const data = { records: { '2026-11-11': [{ id: 'r1', todo_id: 'owner', start: '09:00', end: '09:30', content: 'Errand', tag: 'life' }] }, todos: [{ id: 'owner', title: 'Owner', created_at: '2026-11-01T00:00:00Z' }, { id: 'other', title: 'Other', created_at: '2026-11-01T00:00:00Z', related_time_record_ids: ['r1'] }] }
    const result = await inspectArchive(new TextEncoder().encode(JSON.stringify(data)), '3.0.0', 'Asia/Shanghai')
    expect(result.workspace.records).toHaveLength(1)
    expect(result.workspace.records[0]?.todoId).toBe('legacy-todo-owner')
    expect(result.workspace.todos[0]?.recordIds).toEqual([result.workspace.records[0]?.id])
    expect(result.workspace.todos[1]?.recordIds).toEqual([])
    expect(result.warnings).toContain('legacy.todoLinkConflict')
    expect(() => assertWorkspace(result.workspace)).not.toThrow()
  })
})

