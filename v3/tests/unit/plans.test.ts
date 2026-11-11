import { describe, expect, it } from 'vitest'
import { emptyWorkspace } from '../../src/domain/initial'
import { execute } from '../../src/domain/engine'
import { categoryFor, displayCode, effectivePlanCategory } from '../../src/domain/plans'
import type { WorkspaceCommand } from '../../src/domain/commands'
import { assertWorkspace } from '../../src/domain/validation'

function setup() {
  let sequence = 0
  let state = emptyWorkspace('3.0.0')
  const run = (command: WorkspaceCommand) => {
    const result = execute(state, { command, operationId: 'operation-' + ++sequence }, { now: '2026-11-11T01:00:00Z', id: () => 'entity-' + ++sequence })
    state = result.workspace
    return result.result.entityId!
  }
  const planId = run({ type: 'createPlan', title: 'Trip' })
  const sectionId = run({ type: 'addNode', planId, parentId: null, kind: 'section', title: 'Travel', categoryId: 'life' })
  const groupId = run({ type: 'addNode', planId, parentId: sectionId, kind: 'group', title: 'Prepare' })
  const taskId = run({ type: 'addNode', planId, parentId: groupId, kind: 'task', title: 'Read', categoryId: 'study' })
  return { run, planId, sectionId, groupId, taskId, state: () => state }
}

describe('hierarchical plan categories', () => {
  it('resolves an old plan without a root default against a custom category catalog', () => {
    const state = emptyWorkspace('3.1.0')
    state.categories = state.categories.filter(category => category.id === 'study')
    state.plans = [{ id: 'old', title: 'Old plan', description: '', createdAt: '2026-11-11T00:00:00Z', updatedAt: '2026-11-11T00:00:00Z', nodes: [], logs: [] }]
    assertWorkspace(state)
    expect(effectivePlanCategory(state, state.plans[0]!)).toBe('study')
    const result = execute(state, { operationId: 'old-record', command: { type: 'recordAction', planId: 'old', content: 'Progress', startAt: '2026-11-11T00:00:00Z', endAt: '2026-11-11T00:30:00Z' } }, { now: '2026-11-11T01:00:00Z', id: (() => { let id = 0; return () => 'old-' + ++id })() })
    expect(result.workspace.records[0]!.categoryId).toBe('study')
    assertWorkspace(result.workspace)
  })
  it('creates valid plan defaults and lets groups override or resume inheritance', () => {
    const f = setup()
    expect(f.state().plans[0]!.categoryId).toBe('life')
    const second = f.run({ type: 'createPlan', title: 'Work', categoryId: 'work' })
    expect(f.state().plans.find(plan => plan.id === second)!.categoryId).toBe('work')
    expect(() => f.run({ type: 'createPlan', title: 'Invalid', categoryId: 'missing' })).toThrow('validation.categoryMissing')
    f.run({ type: 'updateNode', planId: f.planId, nodeId: f.groupId, title: 'Prepare', description: '', estimatedMinutes: 0, categoryId: 'exercise' })
    const task = f.run({ type: 'addNode', planId: f.planId, parentId: f.groupId, kind: 'task', title: 'Walk' })
    expect(categoryFor(f.state().plans[0]!, task)).toBe('exercise')
    f.run({ type: 'updateNode', planId: f.planId, nodeId: f.groupId, title: 'Prepare', description: '', estimatedMinutes: 0, categoryId: null })
    expect(categoryFor(f.state().plans[0]!, task)).toBe('life')
    expect(categoryFor(f.state().plans[0]!, f.taskId)).toBe('study')
  })
  it('detaches todo task references when deleting an ancestor and preserves the plan link', () => {
    const f = setup()
    const todoId = f.run({ type: 'saveTodo', title: 'Related todo' })
    const todo = f.state().todos.find(item => item.id === todoId)!
    todo.relatedPlanId = f.planId
    todo.relatedTaskId = f.taskId
    assertWorkspace(f.state())
    f.run({ type: 'deleteNode', planId: f.planId, nodeId: f.sectionId })
    expect(f.state().plans[0]!.nodes).toHaveLength(0)
    expect(f.state().todos[0]).toMatchObject({ id: todoId, relatedPlanId: f.planId })
    expect(f.state().todos[0]!.relatedTaskId).toBeUndefined()
    expect(() => assertWorkspace(f.state())).not.toThrow()
  })
  it('assigns the whole plan without rewriting history or explicit child choices', () => {
    const f = setup()
    const loose = f.run({ type: 'addNode', planId: f.planId, parentId: null, kind: 'task', title: 'Loose' })
    f.run({ type: 'recordAction', planId: f.planId, taskId: f.taskId, content: 'Before', startAt: '2026-11-11T00:00:00Z', endAt: '2026-11-11T00:10:00Z' })
    f.run({ type: 'assignCategory', planId: f.planId, nodeId: null, categoryId: 'work', overwrite: false })
    expect(categoryFor(f.state().plans[0]!)).toBe('work')
    expect(categoryFor(f.state().plans[0]!, loose)).toBe('work')
    expect(categoryFor(f.state().plans[0]!, f.taskId)).toBe('study')
    const later = f.run({ type: 'addNode', planId: f.planId, parentId: null, kind: 'task', title: 'Later' })
    expect(categoryFor(f.state().plans[0]!, later)).toBe('work')
    f.run({ type: 'recordAction', planId: f.planId, content: 'Plan-level action', startAt: '2026-11-11T00:10:00Z', endAt: '2026-11-11T00:20:00Z' })
    expect(f.state().records[1]!.categoryId).toBe('work')
    f.run({ type: 'assignCategory', planId: f.planId, nodeId: null, categoryId: 'rest', overwrite: true })
    expect(f.state().plans[0]!.nodes.every(node => categoryFor(f.state().plans[0]!, node.id) === 'rest')).toBe(true)
    expect(f.state().records.map(record => record.categoryId)).toEqual(['study', 'work'])
    expect(() => f.run({ type: 'assignCategory', planId: f.planId, nodeId: null, categoryId: 'missing', overwrite: true })).toThrow('validation.categoryMissing')
  })
  it('keeps explicit child choices unless bulk overwrite is requested', () => {
    const f = setup()
    f.run({ type: 'assignCategory', planId: f.planId, nodeId: f.sectionId, categoryId: 'work', overwrite: false })
    expect(categoryFor(f.state().plans[0]!, f.groupId)).toBe('work')
    expect(categoryFor(f.state().plans[0]!, f.taskId)).toBe('study')
    f.run({ type: 'assignCategory', planId: f.planId, nodeId: f.sectionId, categoryId: 'rest', overwrite: true })
    expect(categoryFor(f.state().plans[0]!, f.taskId)).toBe('rest')
  })
  it('gives newly created descendants the nearest ancestor category', () => {
    const f = setup()
    f.run({ type: 'assignCategory', planId: f.planId, nodeId: f.groupId, categoryId: 'exercise', overwrite: false })
    const id = f.run({ type: 'addNode', planId: f.planId, parentId: f.groupId, kind: 'task', title: 'Walk' })
    expect(categoryFor(f.state().plans[0]!, id)).toBe('exercise')
  })
  it('uses display codes without replacing stable task identities', () => {
    const f = setup()
    expect(displayCode(f.state().plans[0]!, f.taskId)).toBe('A1')
    f.run({ type: 'recordAction', planId: f.planId, taskId: f.taskId, content: 'Progress' })
    expect(f.state().plans[0]!.logs[0]!.taskId).toBe(f.taskId)
    expect(() => f.run({ type: 'deleteNode', planId: f.planId, nodeId: f.sectionId })).toThrow('validation.taskHasHistory')
  })
  it('keeps display codes distinct for root items and section items', () => {
    const f = setup()
    const rootTask = f.run({ type: 'addNode', planId: f.planId, parentId: null, kind: 'task', title: 'Loose item' })
    const plan = f.state().plans[0]!
    expect(displayCode(plan, rootTask)).not.toBe(displayCode(plan, f.taskId))
    const rootFirst = setup()
    const extra = rootFirst.run({ type: 'addNode', planId: rootFirst.planId, parentId: null, kind: 'task', title: 'Extra' })
    const third = rootFirst.run({ type: 'addNode', planId: rootFirst.planId, parentId: rootFirst.sectionId, kind: 'task', title: 'Another section item' })
    expect(new Set([extra, third, rootFirst.taskId].map(id => displayCode(rootFirst.state().plans[0]!, id))).size).toBe(3)
  })
})

