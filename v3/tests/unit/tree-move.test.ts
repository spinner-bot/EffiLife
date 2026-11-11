import { describe, it, expect } from 'vitest'
import { emptyWorkspace } from '../../src/domain/initial'
import { execute } from '../../src/domain/engine'
import type { WorkspaceCommand } from '../../src/domain/commands'
import { assertWorkspace } from '../../src/domain/validation'
import { categoryFor } from '../../src/domain/plans'
import { flattenTree, projectDrop } from '../../src/features/plans/tree-projection'
function fixture() {
  let state = emptyWorkspace('3.1.0'), next = 0
  const run = (command: WorkspaceCommand) => {
    const result = execute(state, { operationId: 'op-' + ++next, command }, { now: '2026-11-12T00:00:00Z', id: () => 'id-' + ++next })
    state = result.workspace; assertWorkspace(state); return result.result.entityId!
  }
  const planId = run({ type: 'createPlan', title: 'Plan', categoryId: 'life' })
  const group = run({ type: 'addNode', planId, parentId: null, kind: 'group', title: 'Outer', categoryId: 'work' })
  const one = run({ type: 'addNode', planId, parentId: group, kind: 'task', title: 'One' })
  const inner = run({ type: 'addNode', planId, parentId: group, kind: 'group', title: 'Inner' })
  const two = run({ type: 'addNode', planId, parentId: inner, kind: 'task', title: 'Two' })
  const three = run({ type: 'addNode', planId, parentId: null, kind: 'task', title: 'Three' })
  return { run, state: () => state, plan: () => state.plans[0]!, planId, group, inner, one, two, three }
}
describe('tree drag projection and atomic subtree moves', () => {
  it('resolves the same gap to inner group, outer group or root from horizontal depth', () => {
    const f = fixture(), rows = flattenTree(f.plan(), new Set(), new Set([f.three]))
    expect(rows.map(row => row.depth)).toEqual([0, 1, 1, 2])
    expect(projectDrop(rows, 4, 2)).toMatchObject({ parentId: f.inner, depth: 2 })
    expect(projectDrop(rows, 4, 1)).toMatchObject({ parentId: f.group, depth: 1 })
    expect(projectDrop(rows, 4, 0)).toMatchObject({ parentId: null, depth: 0 })
    expect(flattenTree(f.plan(), new Set([f.group])).map(row => row.node.id)).toEqual([f.group, f.three])
  })
  it('moves a group with all descendants and preserves logs, identities and history categories', () => {
    const f = fixture()
    f.run({ type: 'recordAction', planId: f.planId, taskId: f.two, content: 'Progress', startAt: '2026-11-12T00:00:00Z', endAt: '2026-11-12T00:30:00Z' })
    const logs = structuredClone(f.plan().logs), records = structuredClone(f.state().records)
    f.run({ type: 'moveNode', planId: f.planId, nodeId: f.inner, parentId: null, beforeId: f.group })
    expect(f.plan().nodes.find(node => node.id === f.two)!.parentId).toBe(f.inner)
    expect(flattenTree(f.plan(), new Set()).map(row => row.node.id)).toEqual([f.inner, f.two, f.group, f.one, f.three])
    expect(categoryFor(f.plan(), f.two)).toBe('life')
    expect(f.plan().logs).toEqual(logs); expect(f.state().records).toEqual(records)
    const before = structuredClone(f.state())
    expect(() => f.run({ type: 'moveNode', planId: f.planId, nodeId: f.inner, parentId: f.two })).toThrow('validation.treeCycle')
    expect(() => f.run({ type: 'moveNode', planId: f.planId, nodeId: f.group, parentId: f.three })).toThrow('validation.invalidParent')
    expect(() => f.run({ type: 'moveNode', planId: f.planId, nodeId: f.inner, parentId: null, beforeId: f.two })).toThrow('validation.invalidParent')
    expect(f.state()).toEqual(before)
  })
})
