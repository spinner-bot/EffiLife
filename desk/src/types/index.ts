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

// 主题类型
export type ThemeType =
  | 'solid' | 'gradient' | 'glass' | 'neon'
  | 'ink' | 'vintage' | 'cyberpunk' | 'pixel'
  | 'aurora' | 'sakura' | 'ocean' | 'forest' | 'ink' | 'tech' | 'nature' | 'custom'

// 纯色主题配置
export interface SolidThemeConfig {
  bg_window: string
  bg_button: string
  fg_button: string
  bg_frame: string
}

// 渐变主题配置
export interface GradientThemeConfig {
  color_start: string
  color_end: string
  direction: 'to-right' | 'to-left' | 'to-bottom' | 'to-top' | 'to-br' | 'to-tl'
  fg_button: string
  card_bg: string
}

// 玻璃主题配置
export interface GlassThemeConfig {
  bg_color: string
  glass_opacity: number
  blur_amount: number
  fg_button: string
  border_color: string
}

// 霓虹主题配置
export interface NeonThemeConfig {
  bg_color: string
  neon_color: string
  glow_intensity: number
  fg_button: string
  accent_color: string
}

// 水墨主题配置
export interface InkThemeConfig {
  bg_color: string
  ink_color: string
  paper_texture: boolean
  fg_button: string
  accent_color: string
}

// 科技主题配置
export interface TechThemeConfig {
  bg_color: string
  primary_color: string
  grid_color: string
  scanline_effect: boolean
  fg_button: string
  accent_color: string
}

// 自然主题配置
export interface NatureThemeConfig {
  bg_color: string
  leaf_color: string
  sky_color: string
  particle_type: 'leaves' | 'snow' | 'fireflies' | 'none'
  fg_button: string
}

// 自定义主题配置
export interface CustomThemeConfig {
  bg_type: 'color' | 'image' | 'video' | 'gif'
  bg_color: string
  bg_media?: string // base64 or file path
  bg_opacity: number
  bg_blur: number
  fg_button: string
  accent_color: string
}

// 粒子效果配置
export interface ParticleConfig {
  enabled: boolean
  type: 'none' | 'stars' | 'snow' | 'leaves' | 'fireflies' | 'bubbles' | 'matrix'
  count: number
  speed: number
  size: number
  color: string
}

export interface Theme {
  type: ThemeType
  solid?: SolidThemeConfig
  gradient?: GradientThemeConfig
  glass?: GlassThemeConfig
  neon?: NeonThemeConfig
  ink?: InkThemeConfig
  tech?: TechThemeConfig
  nature?: NatureThemeConfig
  custom?: CustomThemeConfig
  particles?: ParticleConfig
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
