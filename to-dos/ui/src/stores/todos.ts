// to-dos 状态管理

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { Todo, Category, TodoStats, FilterState, Priority, TodoStatus } from '@/types'

// 模拟数据（实际应从 API 获取）
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
  },
]

const mockCategories: Category[] = [
  { id: 'default', name: '默认', color: '#6366f1', icon: 'circle', created_at: '2026-09-01T00:00:00' },
  { id: 'work', name: '工作', color: '#3b82f6', icon: 'briefcase', created_at: '2026-09-01T00:00:00' },
  { id: 'study', name: '学习', color: '#22c55e', icon: 'book-open', created_at: '2026-09-01T00:00:00' },
  { id: 'life', name: '生活', color: '#f59e0b', icon: 'home', created_at: '2026-09-01T00:00:00' },
  { id: 'health', name: '健康', color: '#ef4444', icon: 'heart', created_at: '2026-09-01T00:00:00' },
]

export const useTodosStore = defineStore('todos', () => {
  // 状态
  const todos = ref<Todo[]>(mockTodos)
  const categories = ref<Category[]>(mockCategories)
  const filters = ref<FilterState>({
    status: null,
    priority: null,
    category: null,
    search: '',
  })
  const selectedIds = ref<Set<string>>(new Set())
  const isLoading = ref(false)

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
    if (filters.value.search) {
      const keyword = filters.value.search.toLowerCase()
      result = result.filter(t =>
        t.title.toLowerCase().includes(keyword) ||
        t.description?.toLowerCase().includes(keyword) ||
        t.tags.some(tag => tag.toLowerCase().includes(keyword))
      )
    }

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

  // 操作方法
  function addTodo(data: Partial<Todo>): Todo {
    const now = new Date().toISOString()
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
    }

    todos.value.unshift(newTodo)
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
    filters.value = { status: null, priority: null, category: null, search: '' }
  }

  function toggleSelect(id: string) {
    if (selectedIds.value.has(id)) {
      selectedIds.value.delete(id)
    } else {
      selectedIds.value.add(id)
    }
  }

  function clearSelection() {
    selectedIds.value.clear()
  }

  function getCategoryById(id: string): Category | undefined {
    return categories.value.find(c => c.id === id)
  }

  return {
    // 状态
    todos,
    categories,
    filters,
    selectedIds,
    isLoading,
    // 计算属性
    filteredTodos,
    overdueTodos,
    todayTodos,
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
    clearSelection,
    getCategoryById,
  }
})
