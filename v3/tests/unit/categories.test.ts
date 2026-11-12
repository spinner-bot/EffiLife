import { afterEach, expect, it } from 'vitest'
import { emptyWorkspace } from '../../src/domain/initial'
import { execute } from '../../src/domain/engine'
import { categoryName, setLocale } from '../../src/i18n'

afterEach(() => setLocale('zh-CN'))
it('retains translated names for metadata edits while treating explicit renames as user content', () => {
  const state = emptyWorkspace('3.0.1')
  const context = { now: '2026-11-12T00:00:00Z', id: () => 'unused' }
  const edited = execute(state, { operationId: 'color', command: { type: 'saveCategory', categoryId: 'work', color: '#123456', difficulty: 8 } }, context).workspace
  const category = edited.categories.find(item => item.id === 'work')!
  expect(categoryName(category)).toBe('工作')
  setLocale('en-US')
  expect(categoryName(category)).toBe('Work')
  expect(category).toMatchObject({ labelKey: 'category.work', color: '#123456', difficulty: 8 })
  const renamed = execute(edited, { operationId: 'rename', command: { type: 'saveCategory', categoryId: 'work', name: '我的工作', color: '#123456', difficulty: 8 } }, context).workspace
  expect(categoryName(renamed.categories.find(item => item.id === 'work')!)).toBe('我的工作')
})

it('stores a trimmed description and clears it when the field is emptied', () => {
  const context = { now: '2026-11-12T00:00:00Z', id: () => 'unused' }
  const described = execute(emptyWorkspace('3.2.0'), { operationId: 'describe', command: { type: 'saveCategory', categoryId: 'work', description: '  专注写代码的时间  ', color: '#123456', difficulty: 8 } }, context).workspace
  expect(described.categories.find(item => item.id === 'work')!.description).toBe('专注写代码的时间')
  const cleared = execute(described, { operationId: 'clear', command: { type: 'saveCategory', categoryId: 'work', description: '', color: '#123456', difficulty: 8 } }, context).workspace
  expect(cleared.categories.find(item => item.id === 'work')).not.toHaveProperty('description')
  const untouched = execute(described, { operationId: 'keep', command: { type: 'saveCategory', categoryId: 'work', color: '#123456', difficulty: 9 } }, context).workspace
  expect(untouched.categories.find(item => item.id === 'work')!.description).toBe('专注写代码的时间')
})
