// 数据类型定义（对应 Python 版本的数据结构）

export interface TimeRecord {
  date: string
  start: string
  end: string
  duration: number
  content: string
  tag: string
}

export interface PlanItem {
  name: string
  hours: number
}

export interface DayPlan {
  plan_type: '切分制' | '分配制'
  items: PlanItem[]
  bg_tag: string
  color: number[]
}

export interface Plans {
  [key: string]: DayPlan
}

export interface ScheduleRule {
  rule_type: 'week' | 'month' | 'year' | 'month_week' | 'default'
  value: string
  plan_name: string
}

export interface ManualPlans {
  [date: string]: string
}

export interface Config {
  overtime_threshold: number
  whiten_k: number
  show_seconds: boolean
  use_24h: boolean
  show_ampm: boolean
  theme: Theme
}

// 主题类型（预留扩展）
export type ThemeType = 'solid' | 'gradient' | 'glass' | 'neon'

// 纯色主题配置
export interface SolidThemeConfig {
  bg_window: string
  bg_button: string
  fg_button: string
  bg_frame: string
}

export interface Theme {
  type: ThemeType
  // 纯色主题的具体配置
  solid?: SolidThemeConfig
  // 未来主题类型的配置字段（预留）
  gradient?: Record<string, string>
  glass?: Record<string, string>
  neon?: Record<string, string>
}

export interface DayPlanInfo {
  name: string
  type: '切分制' | '分配制'
}

export interface RealTimeStat {
  stat: Record<string, number>
  progress: number
  bg_tag: string
  target: Record<string, number>
  plan_exists: boolean
  plan_name: string
  plan_type: string
  total_used_hours: number
  has_records: boolean
  raw_stat: Record<string, number>
}
