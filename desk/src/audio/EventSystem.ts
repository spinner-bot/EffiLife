// 事件系统 - 管理应用事件和触发音效/弹窗
import { ref, computed, reactive } from 'vue'
import { AudioManager } from './AudioManager'
import type { SoundType } from './AudioManager'

// 事件类型
export type EventType =
  | 'plan_complete_100'      // 当天计划完成度达到100%
  | 'plan_complete_90'       // 当天计划完成度达到90%
  | 'plan_low_progress'      // 完成度低但时间已晚
  | 'record_added'           // 添加记录
  | 'record_deleted'         // 删除记录
  | 'plan_changed'           // 计划切换
  | 'achievement_unlocked'   // 成就解锁

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
  // 各事件的开关
  enabled: Record<EventType, boolean>

  // 低完成度预警阈值
  lowProgressThreshold: number  // 百分比

  // 预警时间（小时，24小时制）
  warningHour: number  // 超过这个时间且完成度低则预警

  // 弹窗显示时长（毫秒）
  popupDuration: number
}

export const DEFAULT_EVENT_SETTINGS: EventSettings = {
  enabled: {
    plan_complete_100: true,
    plan_complete_90: true,
    plan_low_progress: true,
    record_added: false,
    record_deleted: false,
    plan_changed: false,
    achievement_unlocked: true
  },
  lowProgressThreshold: 50,
  warningHour: 21,  // 晚上9点后
  popupDuration: 5000
}

class EventSystemClass {
  private settings = ref<EventSettings>({ ...DEFAULT_EVENT_SETTINGS })
  private activeEvents = ref<AppEvent[]>([])
  private triggeredEvents = ref<Set<string>>(new Set())  // 记录已触发的事件，避免重复

  constructor() {
    this.loadSettings()
  }

  // 加载设置
  private loadSettings() {
    try {
      const saved = localStorage.getItem('efflife_event_settings')
      if (saved) {
        const parsed = JSON.parse(saved)
        this.settings.value = { ...DEFAULT_EVENT_SETTINGS, ...parsed }
      }
    } catch (e) {
      console.warn('Failed to load event settings:', e)
    }
  }

  // 保存设置
  saveSettings() {
    try {
      localStorage.setItem('efflife_event_settings', JSON.stringify(this.settings.value))
    } catch (e) {
      console.warn('Failed to save event settings:', e)
    }
  }

  // 获取设置
  getSettings() {
    return this.settings.value
  }

  // 更新设置
  updateSettings(newSettings: Partial<EventSettings>) {
    this.settings.value = { ...this.settings.value, ...newSettings }
    this.saveSettings()
  }

  // 获取活跃事件列表
  getActiveEvents() {
    return this.activeEvents.value
  }

  // 生成事件ID
  private generateEventId(type: EventType, data?: any): string {
    const date = new Date().toDateString()
    const dataKey = data ? JSON.stringify(data) : ''
    return `${type}_${date}_${dataKey}`
  }

  // 触发事件
  triggerEvent(type: EventType, title: string, message: string, data?: any) {
    // 检查事件是否启用
    if (!this.settings.value.enabled[type]) {
      return
    }

    // 检查是否已触发（同一天同一类型只触发一次）
    const eventId = this.generateEventId(type, data)
    if (this.triggeredEvents.value.has(eventId)) {
      return
    }

    // 确定音效类型
    let sound: SoundType | undefined
    switch (type) {
      case 'plan_complete_100':
      case 'achievement_unlocked':
        sound = 'achievement'
        break
      case 'plan_complete_90':
        sound = 'success'
        break
      case 'plan_low_progress':
        sound = 'warning'
        break
      case 'record_added':
        sound = 'notification'
        break
      case 'plan_changed':
        sound = 'toggle'
        break
    }

    // 确定图标
    let icon = ''
    switch (type) {
      case 'plan_complete_100':
        icon = '🎉'
        break
      case 'plan_complete_90':
        icon = '⭐'
        break
      case 'plan_low_progress':
        icon = '⚠️'
        break
      case 'record_added':
        icon = '📝'
        break
      case 'plan_changed':
        icon = '🔄'
        break
      case 'achievement_unlocked':
        icon = '🏆'
        break
    }

    // 创建事件
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

    // 添加到活跃事件
    this.activeEvents.value.push(event)
    this.triggeredEvents.value.add(eventId)

    // 播放音效
    if (sound) {
      AudioManager.playSound(sound)
    }

    // 自动移除（根据设置时长）
    setTimeout(() => {
      this.dismissEvent(eventId)
    }, this.settings.value.popupDuration)

    return event
  }

  // 关闭事件弹窗
  dismissEvent(eventId: string) {
    this.activeEvents.value = this.activeEvents.value.filter(e => e.id !== eventId)
  }

  // 关闭所有事件弹窗
  dismissAllEvents() {
    this.activeEvents.value = []
  }

  // 重置每日触发记录（每天零点调用）
  resetDailyTriggers() {
    this.triggeredEvents.value.clear()
  }

  // 检查计划完成度事件
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

  // 检查低完成度预警
  checkLowProgressWarning(progress: number, planName: string) {
    const now = new Date()
    const currentHour = now.getHours()

    // 如果当前时间超过预警时间，且完成度低于阈值
    if (currentHour >= this.settings.value.warningHour &&
        progress < this.settings.value.lowProgressThreshold) {
      this.triggerEvent(
        'plan_low_progress',
        '时间不早了',
        `当前完成度仅${progress}%，「${planName}」计划还需努力！`,
        { progress, planName, hour: currentHour }
      )
    }
  }
}

// 导出单例
export const EventSystem = new EventSystemClass()
