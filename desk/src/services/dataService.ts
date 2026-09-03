// 数据服务层 - 移植自 Python DataCore

import type {
  TimeRecord,
  Plans,
  ScheduleRule,
  ManualPlans,
  Config,
  DayPlanInfo,
  RealTimeStat,
  PlanItem,
} from '@/types'

// 默认配置
export const DEFAULT_CONFIG: Config = {
  overtime_threshold: 105,
  whiten_k: 0.6,
  show_seconds: true,
  use_24h: true,
  show_ampm: false,
  theme: {
    bg_window: '#f0f0f0',
    bg_button: '#e0e0e0',
    fg_button: '#000000',
    bg_frame: '#d9d9d9',
  },
}

// 默认计划
export const DEFAULT_PLANS: Plans = {
  工作日: {
    plan_type: '切分制',
    items: [
      { name: '睡觉', hours: 8 },
      { name: '工作', hours: 8 },
      { name: '生活', hours: 8 },
    ],
    bg_tag: '生活',
    color: [0, 255, 255],
  },
  休息日: {
    plan_type: '分配制',
    items: [
      { name: '睡觉', hours: 9 },
      { name: '休闲', hours: 6 },
      { name: '运动', hours: 2 },
    ],
    bg_tag: '',
    color: [147, 253, 2],
  },
  吃了就睡: {
    plan_type: '切分制',
    items: [
      { name: '吃饭', hours: 1.5 },
      { name: '睡觉', hours: 22.5 },
    ],
    bg_tag: '睡觉',
    color: [255, 134, 68],
  },
}

// 默认日程规则
export const DEFAULT_SCHEDULE_RULES: ScheduleRule[] = [
  { rule_type: 'week', value: '6', plan_name: '休息日' },
  { rule_type: 'week', value: '7', plan_name: '休息日' },
  { rule_type: 'default', value: 'default', plan_name: '工作日' },
]

// ============ 工具函数 ============

export function hoursToHm(totalHours: number): string {
  if (totalHours <= 0) return '0分钟'
  const h = Math.floor(totalHours)
  const m = Math.round((totalHours - h) * 60)
  return h > 0 ? `${h}小时${m}分钟` : `${m}分钟`
}

export function hmToHours(h: number, m: number): number {
  return Math.round((h + m / 60) * 100) / 100
}

export function timeStrToMinutes(tStr: string): number {
  try {
    const [h, m] = tStr.split(':').map(Number)
    return h * 60 + m
  } catch {
    return 0
  }
}

export function minutesToTimeStr(minutes: number): string {
  try {
    const h = Math.max(0, Math.floor(minutes / 60))
    const m = Math.max(0, minutes % 60)
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`
  } catch {
    return '00:00'
  }
}

export function isTimeOverlap(
  start1: string,
  end1: string,
  start2: string,
  end2: string
): boolean {
  const s1 = timeStrToMinutes(start1)
  const e1 = timeStrToMinutes(end1)
  const s2 = timeStrToMinutes(start2)
  const e2 = timeStrToMinutes(end2)
  return !(e1 <= s2 || e2 <= s1)
}

export function autoBalance(items: PlanItem[], targetSum = 24): PlanItem[] {
  const total = items.reduce((sum, it) => sum + it.hours, 0)
  if (total <= 0) {
    const each = targetSum / items.length
    return items.map((it) => ({ name: it.name, hours: Math.round(each * 100) / 100 }))
  }
  const ratio = targetSum / total
  return items.map((it) => ({
    name: it.name,
    hours: Math.round(it.hours * ratio * 100) / 100,
  }))
}

export function sortRecords(records: TimeRecord[], planType: string): TimeRecord[] {
  const validRecords = records.filter((r) => r && typeof r === 'object')
  if (planType === '切分制') {
    return validRecords.sort(
      (a, b) => timeStrToMinutes(a.start) - timeStrToMinutes(b.start)
    )
  } else {
    return validRecords.sort((a, b) => {
      const midA = (timeStrToMinutes(a.start) + timeStrToMinutes(a.end)) / 2
      const midB = (timeStrToMinutes(b.start) + timeStrToMinutes(b.end)) / 2
      const durDiff =
        timeStrToMinutes(b.end) -
        timeStrToMinutes(b.start) -
        (timeStrToMinutes(a.end) - timeStrToMinutes(a.start))
      if (midA !== midB) return midA - midB
      if (durDiff !== 0) return durDiff
      return a.tag.localeCompare(b.tag)
    })
  }
}

export function rgbToHex(r: number, g: number, b: number): string {
  try {
    return `#${Math.floor(r).toString(16).padStart(2, '0')}${Math.floor(g).toString(16).padStart(2, '0')}${Math.floor(b).toString(16).padStart(2, '0')}`
  } catch {
    return '#808080'
  }
}

export function parseWeekSelection(weekStr: string): Set<string> {
  const result = new Set<string>()
  const parts = weekStr.split(',')
  for (const p of parts) {
    if (p.includes('-')) {
      const [a, b] = p.split('-').map(Number)
      for (let i = a; i <= b; i++) {
        result.add(i.toString())
      }
    } else {
      result.add(p.trim())
    }
  }
  return result
}

export function formatWeekDisplay(weekSet: Set<string>): string {
  const weekMap: Record<string, string> = {
    '1': '周一',
    '2': '周二',
    '3': '周三',
    '4': '周四',
    '5': '周五',
    '6': '周六',
    '7': '周日',
  }
  return Array.from(weekSet)
    .sort((a, b) => Number(a) - Number(b))
    .map((w) => weekMap[w] || w)
    .join(',')
}

// ============ 日期工具 ============

export function getTodayDate(): string {
  const now = new Date()
  return now.toISOString().split('T')[0]
}

export function formatDate(date: Date): string {
  return date.toISOString().split('T')[0]
}

export function addDays(dateStr: string, days: number): string {
  const date = new Date(dateStr)
  date.setDate(date.getDate() + days)
  return formatDate(date)
}

// ============ 数据存储 ============
// 注意：实际存储通过 Tauri IPC 调用 Rust 后端实现
// 这里提供接口定义和本地存储的 fallback

const STORAGE_PREFIX = 'efflife_'

export const DataService = {
  // 配置
  async loadConfig(): Promise<Config> {
    try {
      const stored = localStorage.getItem(STORAGE_PREFIX + 'config')
      if (stored) {
        return JSON.parse(stored)
      }
    } catch {
      // ignore
    }
    return DEFAULT_CONFIG
  },

  async saveConfig(config: Config): Promise<void> {
    localStorage.setItem(STORAGE_PREFIX + 'config', JSON.stringify(config))
  },

  // 计划
  async loadPlans(): Promise<Plans> {
    try {
      const stored = localStorage.getItem(STORAGE_PREFIX + 'plans')
      if (stored) {
        return JSON.parse(stored)
      }
    } catch {
      // ignore
    }
    return DEFAULT_PLANS
  },

  async savePlans(plans: Plans): Promise<void> {
    localStorage.setItem(STORAGE_PREFIX + 'plans', JSON.stringify(plans))
  },

  // 日程规则
  async loadScheduleRules(): Promise<ScheduleRule[]> {
    try {
      const stored = localStorage.getItem(STORAGE_PREFIX + 'rules')
      if (stored) {
        return JSON.parse(stored)
      }
    } catch {
      // ignore
    }
    return DEFAULT_SCHEDULE_RULES
  },

  async saveScheduleRules(rules: ScheduleRule[]): Promise<void> {
    localStorage.setItem(STORAGE_PREFIX + 'rules', JSON.stringify(rules))
  },

  // 手动计划
  async loadManualPlans(): Promise<ManualPlans> {
    try {
      const stored = localStorage.getItem(STORAGE_PREFIX + 'manual')
      if (stored) {
        return JSON.parse(stored)
      }
    } catch {
      // ignore
    }
    return {}
  },

  async saveManualPlans(plans: ManualPlans): Promise<void> {
    localStorage.setItem(STORAGE_PREFIX + 'manual', JSON.stringify(plans))
  },

  // 记录
  async loadRecords(day?: string): Promise<TimeRecord[]> {
    const targetDay = day || getTodayDate()
    try {
      const stored = localStorage.getItem(STORAGE_PREFIX + 'records_' + targetDay)
      if (stored) {
        return JSON.parse(stored)
      }
    } catch {
      // ignore
    }
    return []
  },

  async saveRecord(record: TimeRecord, day?: string): Promise<void> {
    const targetDay = day || getTodayDate()
    const records = await this.loadRecords(targetDay)
    records.push(record)
    localStorage.setItem(STORAGE_PREFIX + 'records_' + targetDay, JSON.stringify(records))
  },

  async deleteRecord(index: number, day?: string): Promise<void> {
    const targetDay = day || getTodayDate()
    const records = await this.loadRecords(targetDay)
    if (index >= 0 && index < records.length) {
      records.splice(index, 1)
      localStorage.setItem(STORAGE_PREFIX + 'records_' + targetDay, JSON.stringify(records))
    }
  },

  async updateRecord(index: number, record: TimeRecord, day?: string): Promise<void> {
    const targetDay = day || getTodayDate()
    const records = await this.loadRecords(targetDay)
    if (index >= 0 && index < records.length) {
      records[index] = record
      localStorage.setItem(STORAGE_PREFIX + 'records_' + targetDay, JSON.stringify(records))
    }
  },

  // 日计划
  async getDayPlan(day?: string): Promise<DayPlanInfo> {
    const targetDay = day || getTodayDate()
    const manualPlans = await this.loadManualPlans()
    const plans = await this.loadPlans()

    if (targetDay in manualPlans) {
      const planName = manualPlans[targetDay]
      return { name: planName, type: plans[planName]?.plan_type || '切分制' }
    }

    const rules = await this.loadScheduleRules()
    const date = new Date(targetDay)
    const weekNum = date.getDay() === 0 ? '7' : date.getDay().toString()
    const month = (date.getMonth() + 1).toString()
    const monthDay = `${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
    const dayInMonth = date.getDate()
    const monthWeekIndex = Math.floor((dayInMonth - 1) / 7 + 1).toString()
    const monthWeek = `${monthWeekIndex}-${weekNum}`

    for (const rule of rules.slice(0, -1)) {
      if (rule.rule_type === 'week') {
        const weekSet = parseWeekSelection(rule.value)
        if (weekSet.has(weekNum)) {
          return { name: rule.plan_name, type: plans[rule.plan_name]?.plan_type || '切分制' }
        }
      } else if (rule.rule_type === 'month') {
        const monthSet = new Set(rule.value.split(','))
        if (monthSet.has(month)) {
          return { name: rule.plan_name, type: plans[rule.plan_name]?.plan_type || '切分制' }
        }
      } else if (rule.rule_type === 'year') {
        const yearSet = new Set(rule.value.split(','))
        if (yearSet.has(monthDay)) {
          return { name: rule.plan_name, type: plans[rule.plan_name]?.plan_type || '切分制' }
        }
      } else if (rule.rule_type === 'month_week' && rule.value === monthWeek) {
        return { name: rule.plan_name, type: plans[rule.plan_name]?.plan_type || '切分制' }
      }
    }

    const defaultPlan = rules[rules.length - 1].plan_name
    return { name: defaultPlan, type: plans[defaultPlan]?.plan_type || '切分制' }
  },

  async saveDayPlan(planName: string, day?: string): Promise<void> {
    const targetDay = day || getTodayDate()
    const manualPlans = await this.loadManualPlans()
    manualPlans[targetDay] = planName
    await this.saveManualPlans(manualPlans)
  },

  // 实时统计
  async calcRealTimeStat(day?: string): Promise<RealTimeStat> {
    const today = getTodayDate()
    const targetDay = day || today
    const plans = await this.loadPlans()
    const dayPlan = await this.getDayPlan(targetDay)
    const planName = dayPlan.name
    const plan = plans[planName]
    const planExists = !!plan
    const planType = plan?.plan_type || '切分制'
    const bgTag = plan?.bg_tag || ''
    const records = await this.loadRecords(targetDay)
    const hasRecords = records.length > 0

    const target: Record<string, number> = {}
    const stat: Record<string, number> = {}

    if (planExists && plan) {
      for (const item of plan.items) {
        target[item.name] = item.hours
        stat[item.name] = 0
      }
    }

    let usedMinutes = 0
    for (const r of records) {
      const tag = r.tag
      const s = timeStrToMinutes(r.start)
      const e = timeStrToMinutes(r.end)
      const dur = Math.max(0, (e - s) / 60)
      if (planExists && tag in stat) {
        stat[tag] += dur
      }
      usedMinutes += Math.max(0, e - s)
    }

    const totalUsedHours = usedMinutes / 60

    // 切分制：背景类别计算
    if (planExists && planType === '切分制' && bgTag) {
      let totalAvailable: number
      if (targetDay === today) {
        const now = new Date()
        totalAvailable = now.getHours() * 60 + now.getMinutes()
      } else {
        const targetDate = new Date(targetDay)
        const todayDate = new Date(today)
        totalAvailable = targetDate < todayDate ? 24 * 60 : 0
      }
      const bgUsed = Math.max(0, (totalAvailable - usedMinutes) / 60)
      if (bgTag in stat) {
        stat[bgTag] += bgUsed
      }
    }

    // 计算完成度
    let progress = 0
    if (planExists) {
      const totalPlanHours = Object.values(target).reduce((a, b) => a + b, 0)
      if (totalPlanHours > 0) {
        const validTotal = Object.keys(target).reduce((sum, k) => {
          return sum + Math.min(stat[k] || 0, target[k])
        }, 0)
        progress = (validTotal / totalPlanHours) * 100
      }
    }

    return {
      stat,
      progress: Math.round(progress * 10) / 10,
      bg_tag: bgTag,
      target,
      plan_exists: planExists,
      plan_name: planName,
      plan_type: planType,
      total_used_hours: totalUsedHours,
      has_records: hasRecords,
      raw_stat: { ...stat },
    }
  },
}
