// to-dos 类型定义

export type Priority = 'urgent-important' | 'important' | 'urgent' | 'normal'

export type TodoStatus = 'pending' | 'in-progress' | 'completed' | 'archived' | 'cancelled'

export type RecurrenceType = 'none' | 'daily' | 'weekly' | 'monthly' | 'custom'

export interface Subtask {
  id: string
  title: string
  completed: boolean
  completed_at?: string
}

export interface Todo {
  id: string
  title: string
  description?: string
  created_at: string
  updated_at: string
  deadline?: string
  priority: Priority
  category: string
  status: TodoStatus
  completed_at?: string
  tags: string[]
  subtasks: Subtask[]
  related_plan_id?: string
  time_estimate?: number
  time_spent?: number
  notes?: string
  // v0.3.0 新增字段
  recurrence?: RecurrenceType
  deadline_warning_days?: number  // 提前几天警告
  sort_order?: number             // 自定义排序
  pinned?: boolean                // 置顶
}

export interface Category {
  id: string
  name: string
  color: string
  icon: string
  description?: string
  created_at: string
}

export interface TodoStats {
  total: number
  pending: number
  in_progress: number
  completed: number
  archived: number
  cancelled: number
  overdue: number
  completion_rate: number
  by_priority: Record<string, number>
  by_category: Record<string, number>
}

// 优先级配置
export const PRIORITY_CONFIG: Record<Priority, { label: string; color: string; icon: string }> = {
  'urgent-important': { label: '紧急且重要', color: '#ef4444', icon: 'alert-circle' },
  'important': { label: '重要', color: '#f59e0b', icon: 'star' },
  'urgent': { label: '紧急', color: '#3b82f6', icon: 'zap' },
  'normal': { label: '普通', color: '#a1a1aa', icon: 'circle' },
}

// 状态配置
export const STATUS_CONFIG: Record<TodoStatus, { label: string; color: string }> = {
  'pending': { label: '待处理', color: '#52525b' },
  'in-progress': { label: '进行中', color: '#6366f1' },
  'completed': { label: '已完成', color: '#22c55e' },
  'archived': { label: '已归档', color: '#a1a1aa' },
  'cancelled': { label: '已取消', color: '#71717a' },
}

// 重复类型配置
export const RECURRENCE_CONFIG: Record<RecurrenceType, { label: string; short: string }> = {
  'none': { label: '不重复', short: '无' },
  'daily': { label: '每日', short: '日' },
  'weekly': { label: '每周', short: '周' },
  'monthly': { label: '每月', short: '月' },
  'custom': { label: '自定义', short: '自' },
}

// API 响应格式
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message: string
  code?: number
}

// 筛选状态
export interface FilterState {
  status: TodoStatus | null
  priority: Priority | null
  category: string | null
  search: string
  tags: string[]
}

// 排序选项
export type SortOption = 'created_desc' | 'created_asc' | 'deadline_asc' | 'deadline_desc' | 'priority_desc' | 'custom'
