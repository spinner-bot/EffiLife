// 事件系统 - 管理应用事件和触发音效/弹窗
import { ref } from 'vue'
import { AudioManager } from './AudioManager'
import type { SoundType } from './AudioManager'

// 事件类型
export type EventType =
  | 'plan_complete_100'
  | 'plan_complete_90'
  | 'progress_warning'       // 进度预警（基于规则）
  | 'record_added'
  | 'record_deleted'
  | 'plan_changed'
  | 'achievement_unlocked'

// 预警规则
export interface WarningRule {
  id: string
  hour: number        // 触发时间（小时，24小时制）
  minute: number      // 触发时间（分钟）
  threshold: number   // 完成度阈值（百分比）
  enabled: boolean
}

// 预警状态（收件箱）
export interface WarningRecord {
  id: string
  ruleId: string
  date: string        // 日期 YYYY-MM-DD
  triggeredAt: string // ISO 时间
  progress: number
  threshold: number
  scheduledTime: string  // 预定触发时间 HH:mm
  dismissed: boolean
}

// 事件定义
export interface AppEvent {
  id: string
  type: EventType
  title: string
  message: string
  sound?: SoundType
  icon?: string
  triggeredAt: Date
  data?: any
}

// 事件配置
export interface EventSettings {
  enabled: Record<string, boolean>  // key 改为 string 支持动态预警 id
  warningRules: WarningRule[]
  popupDuration: number
}

// 默认预警规则
export const DEFAULT_WARNING_RULES: WarningRule[] = [
  { id: 'warn_12_20', hour: 12, minute: 0, threshold: 20, enabled: true },
  { id: 'warn_18_50', hour: 18, minute: 0, threshold: 50, enabled: true },
  { id: 'warn_22_70', hour: 22, minute: 0, threshold: 70, enabled: true },
]

export const DEFAULT_EVENT_SETTINGS: EventSettings = {
  enabled: {
    plan_complete_100: true,
    plan_complete_90: true,
    progress_warning: true,
    record_added: false,
    record_deleted: false,
    plan_changed: false,
    achievement_unlocked: true
  },
  warningRules: DEFAULT_WARNING_RULES.map(r => ({ ...r })),
  popupDuration: 8000
}

const WARNING_INBOX_KEY = 'efflife_warning_inbox'
const EVENT_INBOX_KEY = 'efflife_event_inbox'
const DAILY_TRIGGER_KEY = 'efflife_daily_triggers'

// 收件箱条目（所有已发布的事件）
export interface InboxEntry {
  id: string
  type: EventType
  title: string
  message: string
  icon?: string
  triggeredAt: string  // ISO
  read: boolean
  ruleId?: string      // 预警规则ID（仅预警）
  scheduledTime?: string
}

class EventSystemClass {
  private settings = ref<EventSettings>({ ...DEFAULT_EVENT_SETTINGS })
  private activeEvents = ref<AppEvent[]>([])
  private warningInbox = ref<WarningRecord[]>([])
  private eventInbox = ref<InboxEntry[]>([])

  constructor() {
    this.loadSettings()
    this.loadWarningInbox()
    this.loadEventInbox()
  }

  // ========= 设置持久化 =========

  private loadSettings() {
    try {
      const saved = localStorage.getItem('efflife_event_settings')
      if (saved) {
        const parsed = JSON.parse(saved)
        this.settings.value = {
          ...DEFAULT_EVENT_SETTINGS,
          ...parsed,
          warningRules: parsed.warningRules && parsed.warningRules.length > 0
            ? parsed.warningRules
            : DEFAULT_WARNING_RULES.map(r => ({ ...r }))
        }
      }
    } catch (e) {
      console.warn('Failed to load event settings:', e)
    }
  }

  saveSettings() {
    try {
      localStorage.setItem('efflife_event_settings', JSON.stringify(this.settings.value))
    } catch (e) {
      console.warn('Failed to save event settings:', e)
    }
  }

  getSettings() {
    return this.settings.value
  }

  updateSettings(newSettings: Partial<EventSettings>) {
    this.settings.value = { ...this.settings.value, ...newSettings }
    this.saveSettings()
  }

  // ========= 预警规则管理 =========

  getWarningRules(): WarningRule[] {
    return this.settings.value.warningRules
  }

  addWarningRule(rule: Omit<WarningRule, 'id'>): string {
    const id = `warn_${Date.now()}`
    this.settings.value.warningRules.push({ ...rule, id })
    this.saveSettings()
    return id
  }

  updateWarningRule(id: string, updates: Partial<WarningRule>) {
    const rule = this.settings.value.warningRules.find(r => r.id === id)
    if (rule) {
      Object.assign(rule, updates)
      this.saveSettings()
    }
  }

  removeWarningRule(id: string) {
    this.settings.value.warningRules = this.settings.value.warningRules.filter(r => r.id !== id)
    this.saveSettings()
  }

  // ========= 预警收件箱 =========

  private loadWarningInbox() {
    try {
      const saved = localStorage.getItem(WARNING_INBOX_KEY)
      if (saved) {
        this.warningInbox.value = JSON.parse(saved)
      }
    } catch (e) {
      console.warn('Failed to load warning inbox:', e)
    }
  }

  private saveWarningInbox() {
    try {
      localStorage.setItem(WARNING_INBOX_KEY, JSON.stringify(this.warningInbox.value))
    } catch (e) {
      console.warn('Failed to save warning inbox:', e)
    }
  }

  getWarningInbox(): WarningRecord[] {
    return this.warningInbox.value
  }

  dismissWarning(recordId: string) {
    const record = this.warningInbox.value.find(r => r.id === recordId)
    if (record) {
      record.dismissed = true
      this.saveWarningInbox()
    }
  }

  // ========= 事件收件箱 =========

  private loadEventInbox() {
    try {
      const saved = localStorage.getItem(EVENT_INBOX_KEY)
      if (saved) {
        this.eventInbox.value = JSON.parse(saved)
      }
    } catch (e) {
      console.warn('Failed to load event inbox:', e)
    }
  }

  private saveEventInbox() {
    try {
      localStorage.setItem(EVENT_INBOX_KEY, JSON.stringify(this.eventInbox.value))
    } catch (e) {
      console.warn('Failed to save event inbox:', e)
    }
  }

  getEventInbox(): InboxEntry[] {
    // 按时间倒序返回
    return [...this.eventInbox.value].sort((a, b) =>
      new Date(b.triggeredAt).getTime() - new Date(a.triggeredAt).getTime()
    )
  }

  getUnreadCount(): number {
    return this.eventInbox.value.filter(e => !e.read).length
  }

  // 添加到收件箱
  private addToInbox(event: AppEvent, ruleId?: string, scheduledTime?: string) {
    const entry: InboxEntry = {
      id: event.id,
      type: event.type,
      title: event.title,
      message: event.message,
      icon: event.icon,
      triggeredAt: event.triggeredAt.toISOString(),
      read: false,
      ruleId,
      scheduledTime
    }
    this.eventInbox.value.push(entry)
    this.saveEventInbox()
    this.cleanOldInboxEntries()
  }

  // 标记已读
  markAsRead(entryId: string) {
    const entry = this.eventInbox.value.find(e => e.id === entryId)
    if (entry) {
      entry.read = true
      this.saveEventInbox()
    }
  }

  // 标记全部已读
  markAllAsRead() {
    this.eventInbox.value.forEach(e => e.read = true)
    this.saveEventInbox()
  }

  // 手动删除
  deleteInboxEntry(entryId: string) {
    this.eventInbox.value = this.eventInbox.value.filter(e => e.id !== entryId)
    this.saveEventInbox()
  }

  // 清空全部
  clearInbox() {
    this.eventInbox.value = []
    this.saveEventInbox()
  }

  // 清空已读
  clearReadInbox() {
    this.eventInbox.value = this.eventInbox.value.filter(entry => !entry.read)
    this.saveEventInbox()
  }

  // 清理：已读超过30天的自动删除
  private cleanOldInboxEntries() {
    const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000
    const before = this.eventInbox.value.length
    this.eventInbox.value = this.eventInbox.value.filter(entry => {
      if (entry.read) {
        return new Date(entry.triggeredAt).getTime() > thirtyDaysAgo
      }
      return true  // 未读的保留
    })
    if (this.eventInbox.value.length !== before) {
      this.saveEventInbox()
    }
  }

  // ========= 每日触发记录（避免同一天同一事件重复） =========

  private getDailyTriggers(): Set<string> {
    try {
      const saved = localStorage.getItem(DAILY_TRIGGER_KEY)
      if (saved) {
        const data = JSON.parse(saved)
        if (data.date === this.getTodayStr()) {
          return new Set(data.triggers || [])
        }
      }
    } catch (e) {
      // ignore
    }
    return new Set()
  }

  private markDailyTriggered(key: string) {
    const triggers = this.getDailyTriggers()
    triggers.add(key)
    localStorage.setItem(DAILY_TRIGGER_KEY, JSON.stringify({
      date: this.getTodayStr(),
      triggers: Array.from(triggers)
    }))
  }

  private isDailyTriggered(key: string): boolean {
    return this.getDailyTriggers().has(key)
  }

  private getTodayStr(): string {
    const d = new Date()
    return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
  }

  // ========= 事件触发 =========

  private generateEventId(type: EventType, data?: any): string {
    const date = this.getTodayStr()
    const dataKey = data ? JSON.stringify(data) : ''
    return `${type}_${date}_${dataKey}`
  }

  triggerEvent(type: EventType, title: string, message: string, data?: any) {
    if (!this.settings.value.enabled[type]) {
      return
    }

    const eventId = this.generateEventId(type, data)
    if (this.isDailyTriggered(eventId)) {
      return
    }

    let sound: SoundType | undefined
    let icon = ''

    switch (type) {
      case 'plan_complete_100':
      case 'achievement_unlocked':
        sound = 'achievement'
        icon = type === 'plan_complete_100' ? '🎉' : '🏆'
        break
      case 'plan_complete_90':
        sound = 'success'
        icon = '⭐'
        break
      case 'progress_warning':
        sound = 'warning'
        icon = '⚠️'
        break
      case 'record_added':
        sound = 'notification'
        icon = '📝'
        break
      case 'plan_changed':
        sound = 'toggle'
        icon = '🔄'
        break
    }

    const event: AppEvent = {
      id: eventId,
      type,
      title,
      message,
      sound,
      icon,
      triggeredAt: new Date(),
      data
    }

    this.activeEvents.value.push(event)
    this.markDailyTriggered(eventId)

    // 写入收件箱
    this.addToInbox(event, data?.ruleId, data?.scheduledTime)

    if (sound) {
      AudioManager.playSound(sound)
    }

    setTimeout(() => {
      this.dismissEvent(eventId)
    }, this.settings.value.popupDuration)

    return event
  }

  dismissEvent(eventId: string) {
    this.activeEvents.value = this.activeEvents.value.filter(e => e.id !== eventId)
  }

  dismissAllEvents() {
    this.activeEvents.value = []
  }

  getActiveEvents() {
    return this.activeEvents.value
  }

  // ========= 完成度事件检查 =========

  checkProgressEvent(progress: number, planName: string) {
    if (progress >= 100) {
      this.triggerEvent(
        'plan_complete_100',
        '完美达成！',
        `今天「${planName}」计划已100%完成，太棒了！`,
        { progress, planName }
      )
    } else if (progress >= 90) {
      this.triggerEvent(
        'plan_complete_90',
        '即将达成！',
        `今天「${planName}」计划已完成${progress}%，加油！`,
        { progress, planName }
      )
    }
  }

  // ========= 预警检查（核心：支持延迟发布） =========

  /**
   * 检查所有预警规则。
   * 逻辑：对每个启用的规则，如果当前时间已过规则的触发时间，
   * 且当天完成度低于阈值，且该规则今天还未触发过，
   * 则补发预警。
   */
  checkWarnings(progress: number, planName: string) {
    if (!this.settings.value.enabled.progress_warning) {
      return
    }

    const now = new Date()
    const currentMinutes = now.getHours() * 60 + now.getMinutes()
    const todayStr = this.getTodayStr()

    for (const rule of this.settings.value.warningRules) {
      if (!rule.enabled) continue

      const ruleMinutes = rule.hour * 60 + rule.minute
      // 已过了触发时间
      if (currentMinutes < ruleMinutes) continue

      // 完成度达标，无需预警
      if (progress >= rule.threshold) continue

      // 今天这条规则已经触发过
      const triggerKey = `warning_${rule.id}_${todayStr}`
      if (this.isDailyTriggered(triggerKey)) continue

      // 触发预警
      const scheduledTime = `${rule.hour.toString().padStart(2, '0')}:${rule.minute.toString().padStart(2, '0')}`

      const record: WarningRecord = {
        id: `warn_record_${Date.now()}_${rule.id}`,
        ruleId: rule.id,
        date: todayStr,
        triggeredAt: now.toISOString(),
        progress,
        threshold: rule.threshold,
        scheduledTime,
        dismissed: false
      }

      this.warningInbox.value.push(record)
      this.saveWarningInbox()
      this.markDailyTriggered(triggerKey)

      // 弹出预警弹窗
      this.triggerEvent(
        'progress_warning',
        '进度预警',
        `已是${scheduledTime}，「${planName}」完成度仅${progress}%（目标${rule.threshold}%）`,
        { ruleId: rule.id, progress, threshold: rule.threshold, scheduledTime, recordId: record.id }
      )
    }
  }
}

export const EventSystem = new EventSystemClass()
