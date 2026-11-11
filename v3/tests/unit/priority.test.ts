import { describe, expect, it } from 'vitest'
import { priorityScore } from '../../src/domain/priority'
import type { Category, Todo } from '../../src/domain/models'

const todo: Todo = {
  id: 'todo', title: 'Ticket', description: '', categoryId: 'life', createdAt: '2026-11-11T00:00:00Z',
  updatedAt: '2026-11-11T00:00:00Z', startAt: '2026-11-11T00:00:00Z', deadline: '2026-11-12T00:00:00Z',
  priorityRank: 5, urgent: false, important: false, estimatedMinutes: 60, status: 'pending', tags: [], recordIds: [],
}
const category: Category = { id: 'life', name: 'Life', color: '#ffffff', icon: 'circle', difficulty: 5 }
const now = '2026-11-11T12:00:00Z'

describe('priority compatibility', () => {
  it.each([
    [5, 5, false, false, 60, 4515],
    [5, 5, true, true, 60, 6773],
    [0, 5, false, false, 60, 1],
    [5, 0, false, false, 60, 225],
    [10, 20, true, false, 120, 40998],
  ] as const)('matches the original Python formula for rank %s and difficulty %s', (rank, difficulty, urgent, important, estimated, expected) => {
    expect(priorityScore({ ...todo, priorityRank: rank, urgent, important, estimatedMinutes: estimated }, { ...category, difficulty }, now)).toBe(expected)
  })
  it('preserves expired and deadline-free behavior', () => {
    expect(priorityScore(todo, category, '2026-11-13T00:00:00Z')).toBe(-1)
    expect(priorityScore({ ...todo, deadline: undefined }, category, now)).toBe(0)
  })
  it('keeps very high ranks finite and sortable', () => {
    expect(Number.isFinite(priorityScore({ ...todo, priorityRank: 1000000 }, category, now))).toBe(true)
  })
})

