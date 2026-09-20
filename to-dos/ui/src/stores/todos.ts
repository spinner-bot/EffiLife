// to-dos 状态管理
// v0.5.0: 新增优先排位分计算、设置管理

import { ref, computed, watch, onUnmounted } from 'vue'
import { defineStore } from 'pinia'
import type { Todo, Category, TodoStats, FilterState, Priority, TodoStatus, SortOption, RecurrenceType, AppSettings } from '@/types'
import { DEFAULT_SETTINGS } from '@/types'
import { calcPriorityScore, formatScoreDisplay, calcAllScores } from '@/utils/priority'

// 模拟数据 (v0.5.0: 新增字段)
const mockTodos: Todo[] = [
  {
    id: 'TODO-20260920-0001',
    title: '完成项目文档',
    description: '编写 API 文档和用户手册',
    created_at: '2026-09-18T10:00:00',
    updated_at: '2026-09-20T09:30:00',
    deadline: '2026-09-22T18:00:00',
    priority: 'urgent-important',
    category: 'work',
    status: 'in-progress',
    tags: ['文档', '紧急'],
    subtasks: [
      { id: 'SUB-001', title: '编写目录结构', completed: true, completed_at: '2026-09-19T15:00:00' },
      { id: 'SUB-002', title: '编写 API 规范', completed: true, completed_at: '2026-09-20T10:00:00' },
      { id: 'SUB-003', title: '编写使用说明', completed: false },
    ],
    time_estimate: 120,
    time_spent: 60,
    sort_order: 1,
    deadline_warning_days: 3,
    // v0.5.0 新增
    priority_rank: 2,
    urgent: true,
    important: true,
    start_time: '2026-09-18T10:00:00',
    estimated_time: 120,
  },
  {
    id: 'TODO-20260920-0002',
    title: '学习 Vue 3 Composition API',
    description: '完成官方教程',
    created_at: '2026-09-17T14:00:00',
    updated_at: '2026-09-20T08:00:00',
    deadline: '2026-09-25T23:59:59',
    priority: 'important',
    category: 'study',
    status: 'pending',
    tags: ['Vue', '学习'],
    subtasks: [],
    time_estimate: 180,
    recurrence: 'daily',
    sort_order: 2,
    // v0.5.0 新增
    priority_rank: 1,
    urgent: false,
    important: true,
    start_time: '2026-09-17T14:00:00',
    estimated_time: 180,
  },
  {
    id: 'TODO-20260920-0003',
    title: '买菜做饭',
    created_at: '2026-09-20T07:00:00',
    updated_at: '2026-09-20T07:00:00',
    deadline: '2026-09-20T19:00:00',
    priority: 'normal',
    category: 'life',
    status: 'completed',
    completed_at: '2026-09-20T12:00:00',
    tags: ['生活'],
    subtasks: [
      { id: 'SUB-004', title: '去超市', completed: true, completed_at: '2026-09-20T10:00:00' },
      { id: 'SUB-005', title: '准备晚餐', completed: true, completed_at: '2026-09-20T12:00:00' },
    ],
    sort_order: 3,
    // v0.5.0 新增
    priority_rank: 0,
    urgent: false,
    important: false,
    start_time: '2026-09-20T07:00:00',
    estimated_time: 60,
  },
  {
    id: 'TODO-20260920-0004',
    title: '回复客户邮件',
    created_at: '2026-09-19T16:00:00',
    updated_at: '2026-09-19T16:00:00',
    deadline: '2026-09-19T18:00:00',
    priority: 'urgent',
    category: 'work',
    status: 'pending',
    tags: ['邮件', '客户'],
    subtasks: [],
    sort_order: 4,
    deadline_warning_days: 1,
    // v0.5.0 新增
    priority_rank: 3,
    urgent: true,
    important: false,
    start_time: '2026-09-19T16:00:00',
    estimated_time: 30,
  },
]

const mockCategories: Category[] = [
  { id: 'default', name: '默认', color: '#6366f1', icon: 'circle', created_at: '2026-09-01T00:00:00', difficulty: 5 },
  { id: 'work', name: '工作', color: '#3b82f6', icon: 'briefcase', created_at: '2026-09-01T00:00:00', difficulty: 7 },
  { id: 'study', name: '学习', color: '#22c55e', icon: 'book-open', created_at: '2026-09-01T00:00:00', difficulty: 5 },
  { id: 'life', name: '生活', color: '#f59e0b', icon: 'home', created_at: '2026-09-01T00:00:00', difficulty: 3 },
  { id: 'health', name: '健康', color: '#ef4444', icon: 'heart', created_at: '2026-09-01T00:00:00', difficulty: 4 },
]

const STORAGE_KEY = 'to-dos-data'

export const useTodosStore = defineStore('todos', () => {
  // 状态
  const todos = ref<Todo[]>([...mockTodos])
  const categories = ref<Category[]>([...mockCategories])
  const filters = ref<FilterState>({
    status: null,
    priority: null,
    category: null,
    search: '',
    tags: [],
  })
  const sortBy = ref<SortOption>('score_desc')  // v0.5.0: 默认按分数排序
  const selectedIds = ref<Set<string>>(new Set())
  const isLoading = ref(false)
  const darkMode = ref<'auto' | 'light' | 'dark'>('auto')

  // v0.5.0: 设置
  const settings = ref<AppSettings>({ ...DEFAULT_SETTINGS })

  // v0.5.0: 实时更新定时器
  let scoreUpdateTimer: ReturnType<typeof setInterval> | null = null

  // 初始化：从 localStorage 加载
  function loadFromStorage() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const data = JSON.parse(saved)
        if (data.todos) todos.value = data.todos
        if (data.categories) categories.value = data.categories
        if (data.filters) filters.value = { ...filters.value, ...data.filters }
        if (data.sortBy) sortBy.value = data.sortBy
        if (data.darkMode) darkMode.value = data.darkMode
        if (data.settings) settings.value = { ...DEFAULT_SETTINGS, ...data.settings }
      }
    } catch {
      // 忽略加载错误
    }
    // 初始计算分数
    recalculateScores()
    // 启动实时更新
    startScoreUpdates()
  }

  // 保存到 localStorage
  function saveToStorage() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        todos: todos.value,
        categories: categories.value,
        filters: filters.value,
        sortBy: sortBy.value,
        darkMode: darkMode.value,
        settings: settings.value,
      }))
    } catch {
      // 忽略存储错误
    }
  }

  // v0.5.0: 重新计算所有待办的优先排位分
  function recalculateScores() {
    const now = new Date()
    const scores = calcAllScores(todos.value, categories.value, now)

    for (const todo of todos.value) {
      const score = scores.get(todo.id) ?? 0
      todo._score = score
      todo._score_display = formatScoreDisplay(score)
    }
  }

  // v0.5.0: 启动/重启实时更新
  function startScoreUpdates() {
    stopScoreUpdates()
    const freq = settings.value.updateFrequency
    if (freq > 0) {
      scoreUpdateTimer = setInterval(() => {
        recalculateScores()
      }, freq)
    }
  }

  function stopScoreUpdates() {
    if (scoreUpdateTimer) {
      clearInterval(scoreUpdateTimer)
      scoreUpdateTimer = null
    }
  }

  // v0.5.0: 更新设置
  function updateSettings(newSettings: Partial<AppSettings>) {
    settings.value = { ...settings.value, ...newSettings }
    saveToStorage()
    // 如果更新频率变了，重启定时器
    if (newSettings.updateFrequency !== undefined) {
      startScoreUpdates()
    }
  }

  // 监听变化自动保存
  watch([todos, categories], () => {
    saveToStorage()
  }, { deep: true })

  // 深色模式应用
  function applyDarkMode() {
    const root = document.documentElement
    if (darkMode.value === 'dark') {
      root.setAttribute('data-theme', 'dark')
    } else if (darkMode.value === 'light') {
      root.setAttribute('data-theme', 'light')
    } else {
      root.removeAttribute('data-theme')
    }
  }

  // 计算属性
  const filteredTodos = computed(() => {
    let result = todos.value

    if (filters.value.status) {
      result = result.filter(t => t.status === filters.value.status)
    }
    if (filters.value.priority) {
      result = result.filter(t => t.priority === filters.value.priority)
    }
    if (filters.value.category) {
      result = result.filter(t => t.category === filters.value.category)
    }
    if (filters.value.tags && filters.value.tags.length > 0) {
      result = result.filter(t =>
        filters.value.tags.every(tag => t.tags.includes(tag))
      )
    }
    if (filters.value.search) {
      const keyword = filters.value.search.toLowerCase()
      result = result.filter(t =>
        t.title.toLowerCase().includes(keyword) ||
        t.description?.toLowerCase().includes(keyword) ||
        t.tags.some(tag => tag.toLowerCase().includes(keyword)) ||
        t.notes?.toLowerCase().includes(keyword)
      )
    }

    // 排序
    result = sortTodos(result, sortBy.value)

    return result
  })

  const overdueTodos = computed(() => {
    const now = new Date()
    return todos.value.filter(t => {
      if (!t.deadline || t.status === 'completed' || t.status === 'cancelled') return false
      return new Date(t.deadline) < now
    })
  })

  const todayTodos = computed(() => {
    const today = new Date().toISOString().split('T')[0]
    return todos.value.filter(t => {
      if (t.deadline && t.deadline.startsWith(today)) return true
      if (t.status === 'in-progress') return true
      return false
    })
  })

  // 所有使用中的标签
  const allTags = computed(() => {
    const tagSet = new Set<string>()
    todos.value.forEach(t => t.tags.forEach(tag => tagSet.add(tag)))
    return Array.from(tagSet).sort()
  })

  const stats = computed((): TodoStats => {
    const all = todos.value
    const active = all.filter(t => t.status !== 'archived' && t.status !== 'cancelled')

    return {
      total: all.length,
      pending: all.filter(t => t.status === 'pending').length,
      in_progress: all.filter(t => t.status === 'in-progress').length,
      completed: all.filter(t => t.status === 'completed').length,
      archived: all.filter(t => t.status === 'archived').length,
      cancelled: all.filter(t => t.status === 'cancelled').length,
      overdue: overdueTodos.value.length,
      completion_rate: active.length > 0
        ? Math.round(active.filter(t => t.status === 'completed').length / active.length * 100)
        : 0,
      by_priority: {
        'urgent-important': all.filter(t => t.priority === 'urgent-important').length,
        'important': all.filter(t => t.priority === 'important').length,
        'urgent': all.filter(t => t.priority === 'urgent').length,
        'normal': all.filter(t => t.priority === 'normal').length,
      },
      by_category: all.reduce((acc, t) => {
        acc[t.category] = (acc[t.category] || 0) + 1
        return acc
      }, {} as Record<string, number>),
    }
  })

  // 排序逻辑
  function sortTodos(list: Todo[], sort: SortOption): Todo[] {
    const sorted = [...list]
    // 置顶优先
    sorted.sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0))

    switch (sort) {
      case 'score_desc':
        // v0.5.0: 按优先排位分降序
        return sorted.sort((a, b) => (b._score ?? 0) - (a._score ?? 0))
      case 'created_desc':
        return sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      case 'created_asc':
        return sorted.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
      case 'deadline_asc':
        return sorted.sort((a, b) => {
          if (!a.deadline) return 1
          if (!b.deadline) return -1
          return new Date(a.deadline).getTime() - new Date(b.deadline).getTime()
        })
      case 'deadline_desc':
        return sorted.sort((a, b) => {
          if (!a.deadline) return 1
          if (!b.deadline) return -1
          return new Date(b.deadline).getTime() - new Date(a.deadline).getTime()
        })
      case 'priority_desc': {
        const priorityOrder: Record<string, number> = {
          'urgent-important': 4, 'important': 3, 'urgent': 2, 'normal': 1,
        }
        return sorted.sort((a, b) =>
          (priorityOrder[b.priority] || 0) - (priorityOrder[a.priority] || 0)
        )
      }
      case 'custom':
        return sorted.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
      default:
        return sorted
    }
  }

  // 操作方法
  function addTodo(data: Partial<Todo>): Todo {
    const now = new Date().toISOString()
    const maxOrder = todos.value.reduce((max, t) => Math.max(max, t.sort_order || 0), 0)
    const id = `TODO-${now.replace(/[-:T]/g, '').slice(0, 8)}-${String(todos.value.length + 1).padStart(4, '0')}`

    const newTodo: Todo = {
      id,
      title: data.title || '',
      description: data.description,
      created_at: now,
      updated_at: now,
      deadline: data.deadline,
      priority: data.priority || 'normal',
      category: data.category || 'default',
      status: 'pending',
      tags: data.tags || [],
      subtasks: data.subtasks || [],
      related_plan_id: data.related_plan_id,
      time_estimate: data.time_estimate,
      notes: data.notes,
      recurrence: data.recurrence || 'none',
      deadline_warning_days: data.deadline_warning_days || 3,
      sort_order: maxOrder + 1,
      pinned: data.pinned || false,
      // v0.5.0 新增字段
      priority_rank: data.priority_rank ?? 0,
      urgent: data.urgent ?? false,
      important: data.important ?? false,
      start_time: data.start_time || now,
      estimated_time: data.estimated_time ?? data.time_estimate,
    }

    todos.value.unshift(newTodo)
    // 重新计算分数
    recalculateScores()
    return newTodo
  }

  function updateTodo(id: string, data: Partial<Todo>) {
    const index = todos.value.findIndex(t => t.id === id)
    if (index === -1) return

    todos.value[index] = {
      ...todos.value[index],
      ...data,
      updated_at: new Date().toISOString(),
    }
    // 重新计算分数
    recalculateScores()
  }

  function completeTodo(id: string) {
    const todo = todos.value.find(t => t.id === id)
    if (!todo) return

    todo.status = 'completed'
    todo.completed_at = new Date().toISOString()
    todo.updated_at = new Date().toISOString()
  }

  function deleteTodo(id: string) {
    const index = todos.value.findIndex(t => t.id === id)
    if (index === -1) return
    todos.value[index].status = 'archived'
    todos.value[index].updated_at = new Date().toISOString()
  }

  function toggleSubtask(todoId: string, subtaskId: string) {
    const todo = todos.value.find(t => t.id === todoId)
    if (!todo) return

    const subtask = todo.subtasks.find(s => s.id === subtaskId)
    if (!subtask) return

    subtask.completed = !subtask.completed
    subtask.completed_at = subtask.completed ? new Date().toISOString() : undefined
    todo.updated_at = new Date().toISOString()
  }

  function setFilter(key: keyof FilterState, value: any) {
    ;(filters.value as any)[key] = value
  }

  function clearFilters() {
    filters.value = { status: null, priority: null, category: null, search: '', tags: [] }
  }

  function toggleSelect(id: string) {
    if (selectedIds.value.has(id)) {
      selectedIds.value.delete(id)
    } else {
      selectedIds.value.add(id)
    }
  }

  function selectAll() {
    filteredTodos.value.forEach(t => selectedIds.value.add(t.id))
  }

  function clearSelection() {
    selectedIds.value.clear()
  }

  function getCategoryById(id: string): Category | undefined {
    return categories.value.find(c => c.id === id)
  }

  // 批量操作
  function batchComplete() {
    selectedIds.value.forEach(id => completeTodo(id))
    clearSelection()
  }

  function batchDelete() {
    selectedIds.value.forEach(id => deleteTodo(id))
    clearSelection()
  }

  // 排序
  function setSortBy(option: SortOption) {
    sortBy.value = option
    saveToStorage()
  }

  // 自定义排序（拖拽后）
  function reorderTodos(fromIndex: number, toIndex: number) {
    const filtered = filteredTodos.value
    const item = filtered[fromIndex]
    const actualFrom = todos.value.findIndex(t => t.id === item.id)

    // 更新 sort_order
    const newOrder = [...todos.value]
    const [moved] = newOrder.splice(actualFrom, 1)
    const targetItem = filtered[toIndex]
    const actualTo = todos.value.findIndex(t => t.id === targetItem.id)
    newOrder.splice(actualTo, 0, moved)

    // 重新编号
    newOrder.forEach((t, i) => {
      t.sort_order = i + 1
    })

    todos.value = newOrder
  }

  // 标签筛选
  function toggleTagFilter(tag: string) {
    const tags = filters.value.tags
    if (tags.includes(tag)) {
      filters.value.tags = tags.filter(t => t !== tag)
    } else {
      filters.value.tags = [...tags, tag]
    }
  }

  // 深色模式切换
  function setDarkMode(mode: 'auto' | 'light' | 'dark') {
    darkMode.value = mode
    applyDarkMode()
    saveToStorage()
  }

  // 数据导出
  function exportData(): string {
    return JSON.stringify({
      version: '0.3.0',
      exported_at: new Date().toISOString(),
      todos: todos.value,
      categories: categories.value,
    }, null, 2)
  }

  // 数据导入
  function importData(jsonStr: string): { success: boolean; message: string; count: number } {
    try {
      const data = JSON.parse(jsonStr)
      if (!data.todos || !Array.isArray(data.todos)) {
        return { success: false, message: '无效的数据格式', count: 0 }
      }
      todos.value = data.todos
      if (data.categories) {
        categories.value = data.categories
      }
      return { success: true, message: `导入成功: ${data.todos.length} 个待办`, count: data.todos.length }
    } catch {
      return { success: false, message: '解析 JSON 失败', count: 0 }
    }
  }

  // 导出 CSV
  function exportCSV(): string {
    const headers = ['ID', '标题', '状态', '优先级', '分类', '截止日期', '标签', '创建时间']
    const rows = todos.value.map(t => [
      t.id,
      `"${t.title.replace(/"/g, '""')}"`,
      t.status,
      t.priority,
      t.category,
      t.deadline || '',
      `"${t.tags.join(', ')}"`,
      t.created_at.slice(0, 19),
    ])
    return [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
  }

  return {
    // 状态
    todos,
    categories,
    filters,
    sortBy,
    selectedIds,
    isLoading,
    darkMode,
    settings,           // v0.5.0
    // 计算属性
    filteredTodos,
    overdueTodos,
    todayTodos,
    allTags,
    stats,
    // 方法
    addTodo,
    updateTodo,
    completeTodo,
    deleteTodo,
    toggleSubtask,
    setFilter,
    clearFilters,
    toggleSelect,
    selectAll,
    clearSelection,
    getCategoryById,
    batchComplete,
    batchDelete,
    setSortBy,
    reorderTodos,
    toggleTagFilter,
    setDarkMode,
    applyDarkMode,
    exportData,
    importData,
    exportCSV,
    loadFromStorage,
    // v0.5.0 新增方法
    recalculateScores,
    updateSettings,
    startScoreUpdates,
    stopScoreUpdates,
  }
})
