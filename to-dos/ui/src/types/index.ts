// to-dos 类型定义
// v0.5.0: 新增优先排位分相关字段

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
  // v0.5.0 新增字段（优先排位分算法）
  priority_rank?: number          // 优先级排位，0最高
  urgent?: boolean                // 是否紧急
  important?: boolean             // 是否重要
  start_time?: string             // 开始时间
  estimated_time?: number         // 用户填写的预估时间（分钟）
  // 运行时计算字段（不持久化）
  _score?: number                 // 优先排位分
  _score_display?: string         // 格式化后的分数显示
}

export interface Category {
  id: string
  name: string
  color: string
  icon: string
  description?: string
  created_at: string
  // v0.5.0 新增字段
  difficulty?: number             // 类别难度，默认5
  ascii_icon?: string             // ASCII图标（A-Z, a-z, 0-9）
  pinned?: boolean                // 分类置顶
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

// v0.5.0: 预设配色方案
export const PRESET_COLORS = [
  '#ef4444', '#f97316', '#f59e0b', '#eab308',
  '#84cc16', '#22c55e', '#10b981', '#14b8a6',
  '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1',
  '#8b5cf6', '#a855f7', '#d946ef', '#ec4899',
  '#f43f5e', '#78716c', '#64748b', '#334155',
]

// v0.5.0: ASCII 图标列表
export const ASCII_ICONS = [
  'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
  'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
  'U', 'V', 'W', 'X', 'Y', 'Z',
  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
  'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
  'u', 'v', 'w', 'x', 'y', 'z',
  '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
]

// v0.5.0: 设置接口
export interface AppSettings {
  updateFrequency: number         // 更新频率（毫秒），0=手动
  expandCount: number             // 前 X 名展开，默认 5
  dateFormat: string              // 日期格式
}

export const DEFAULT_SETTINGS: AppSettings = {
  updateFrequency: 5000,          // 5秒
  expandCount: 5,
  dateFormat: 'yyyy/mm/dd',
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
export type SortOption = 'score_desc' | 'created_desc' | 'created_asc' | 'deadline_asc' | 'deadline_desc' | 'priority_desc' | 'custom'
