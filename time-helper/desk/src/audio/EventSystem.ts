// 事件系统 - 管理应用事件和触发音效/弹窗
import { ref } from 'vue'
import { AudioManager } from './AudioManager'
import type { SoundType } from './AudioManager'

// 事件类型
export type EventType =
  | 'plan_complete_100'
  | 'plan_complete_90'
  | 'plan_complete_50'       // 半程完成
  | 'progress_warning'       // 进度预警（基于规则）
  | 'record_added'
  | 'record_deleted'
  | 'plan_changed'
  | 'achievement_unlocked'
  | 'checkin_complete'       // 打卡完成
  | 'streak_milestone'       // 连续打卡里程碑（7/14/30/60/90/180/365天）
  | 'idle_reminder'          // 长时间未操作提醒
  | 'weekly_summary'         // 周报摘要
  | 'daily_first_record'     // 当天第一条记录

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

// 自动清空时限选项（天）
export type AutoCleanDays = 1 | 3 | 7 | 30 | -1  // -1 表示永不

// 事件配置
export interface EventSettings {
  enabled: Record<string, boolean>  // key 改为 string 支持动态预警 id
  warningRules: WarningRule[]
  popupDuration: number
  autoCleanDays: AutoCleanDays  // 自动清空已读事件的时限（天），-1 表示永不
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
    plan_complete_50: true,
    progress_warning: true,
    record_added: false,
    record_deleted: false,
    plan_changed: false,
    achievement_unlocked: true,
    checkin_complete: true,
    streak_milestone: true,
    idle_reminder: true,
    weekly_summary: true,
    daily_first_record: true
  },
  warningRules: DEFAULT_WARNING_RULES.map(r => ({ ...r })),
  popupDuration: 8000,
  autoCleanDays: 30
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
  checkinPlanName?: string  // 可用于打卡的计划名（遗漏打卡提醒）
  checkinDate?: string      // 补打卡的日期
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

  // 添加遗漏打卡提醒到收件箱
  addMissedCheckinReminder(planName: string, date: string): string {
    const id = `missed_checkin_${Date.now()}`
    const entry: InboxEntry = {
      id,
      type: 'achievement_unlocked',  // 使用成就类型图标
      title: '补打卡',
      message: `${date} 完成了「${planName}」但未打卡，点击此处补打`,
      icon: '🔥',
      triggeredAt: new Date().toISOString(),
      read: false,
      checkinPlanName: planName,
      checkinDate: date
    }
    this.eventInbox.value.push(entry)
    this.saveEventInbox()
    return id
  }

  // 获取可打卡的收件箱条目
  getCheckinableEntries(): InboxEntry[] {
    return this.eventInbox.value.filter(e => e.checkinPlanName && e.checkinDate)
  }

  // 删除打卡提醒（打卡完成后调用）
  removeCheckinReminder(entryId: string) {
    this.eventInbox.value = this.eventInbox.value.filter(e => e.id !== entryId)
    this.saveEventInbox()
  }

  // 清理：已读超过指定天数的自动删除
  private cleanOldInboxEntries() {
    const autoCleanDays = this.settings.value.autoCleanDays

    // 永不自动清空
    if (autoCleanDays === -1) return

    const cutoffTime = Date.now() - autoCleanDays * 24 * 60 * 60 * 1000
    const before = this.eventInbox.value.length
    this.eventInbox.value = this.eventInbox.value.filter(entry => {
      if (entry.read) {
        return new Date(entry.triggeredAt).getTime() > cutoffTime
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
      case 'plan_complete_50':
        sound = 'success'
        icon = '📈'
        break
      case 'progress_warning':
        sound = 'warning'
        icon = '⚠️'
        break
      case 'record_added':
        sound = 'notification'
        icon = '📝'
        break
      case 'record_deleted':
        sound = 'notification'
        icon = '🗑️'
        break
      case 'plan_changed':
        sound = 'toggle'
        icon = '🔄'
        break
      case 'checkin_complete':
        sound = 'achievement'
        icon = '🔥'
        break
      case 'streak_milestone':
        sound = 'achievement'
        icon = '🎊'
        break
      case 'idle_reminder':
        sound = 'notification'
        icon = '💤'
        break
      case 'weekly_summary':
        sound = 'success'
        icon = '📊'
        break
      case 'daily_first_record':
        sound = 'notification'
        icon = '🌅'
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

  // ========= 半程完成检查 =========

  checkHalfProgress(progress: number, planName: string) {
    if (!this.settings.value.enabled.plan_complete_50) return
    // 仅当进度刚跨过 50% 时触发（50-89 区间内，避免与 90% 和 100% 冲突）
    if (progress >= 50 && progress < 90) {
      this.triggerEvent(
        'plan_complete_50',
        '半程完成！',
        `「${planName}」计划已完成${progress}%，继续加油！`,
        { progress, planName }
      )
    }
  }

  // ========= 打卡里程碑检查 =========

  checkStreakMilestone(streak: number) {
    if (!this.settings.value.enabled.streak_milestone) return
    const milestones = [7, 14, 30, 60, 90, 180, 365]
    if (milestones.includes(streak)) {
      const titles: Record<number, string> = {
        7: '一周坚持！',
        14: '两周达人！',
        30: '月度先锋！',
        60: '两月勇士！',
        90: '季度精英！',
        180: '半年之星！',
        365: '年度传说！'
      }
      this.triggerEvent(
        'streak_milestone',
        titles[streak] || `连续${streak}天！`,
        `连续打卡${streak}天，这是一个了不起的里程碑！🔥`,
        { streak }
      )
    }
  }

  // ========= 空闲提醒 =========

  triggerIdleReminder(minutesIdle: number) {
    if (!this.settings.value.enabled.idle_reminder) return
    this.triggerEvent(
      'idle_reminder',
      '休息一下？',
      `你已经${minutesIdle}分钟没有操作了，记得记录时间哦`,
      { minutesIdle }
    )
  }

  // ========= 周报摘要 =========

  triggerWeeklySummary(data: {
    totalRecords: number
    totalHours: number
    avgProgress: number
    checkinDays: number
    topTag: string
  }) {
    if (!this.settings.value.enabled.weekly_summary) return
    this.triggerEvent(
      'weekly_summary',
      '本周摘要',
      `记录${data.totalRecords}条，共${data.totalHours.toFixed(1)}小时，平均完成${data.avgProgress}%，打卡${data.checkinDays}天`,
      data
    )
  }

  // ========= 当天第一条记录 =========

  triggerDailyFirstRecord(planName: string) {
    if (!this.settings.value.enabled.daily_first_record) return
    this.triggerEvent(
      'daily_first_record',
      '新的一天',
      `今天的第一条记录已开始，「${planName}」加油！`,
      { planName }
    )
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
