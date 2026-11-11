import type { Workspace } from './models'

export function emptyWorkspace(productVersion: string, now = new Date().toISOString(), timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone): Workspace {
  return {
    schemaVersion: 1, productVersion, revision: 0, updatedAt: now,
    plans: [], records: [], todos: [], receipts: {}, packages: [], packageTombstones: [],
    timePlanning: { plans: [], rules: [], overrides: {} },
    categories: [
      { id: 'work', name: '', labelKey: 'category.work', color: '#526ac9', icon: 'briefcase', difficulty: 5 },
      { id: 'study', name: '', labelKey: 'category.study', color: '#3e8b78', icon: 'book', difficulty: 5 },
      { id: 'life', name: '', labelKey: 'category.life', color: '#ca9653', icon: 'sun', difficulty: 3 },
      { id: 'rest', name: '', labelKey: 'category.rest', color: '#9277ba', icon: 'moon', difficulty: 2 },
      { id: 'exercise', name: '', labelKey: 'category.exercise', color: '#b76d7c', icon: 'heart', difficulty: 4 },
    ],
    preferences: { locale: 'zh-CN', themeId: 1, fontId: 'default', timeZone, weekStartsOn: 1 },
  }
}

