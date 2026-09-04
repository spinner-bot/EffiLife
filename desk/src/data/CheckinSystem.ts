// 打卡系统 - 记录用户连续完成计划的天数
import { ref } from 'vue'

const STORAGE_KEY = 'efflife_checkin_data'

// 打卡记录
export interface CheckinRecord {
  date: string          // YYYY-MM-DD
  planName: string
  progress: number      // 完成度，通常100
  checkedInAt: string   // ISO时间
}

// 打卡数据
export interface CheckinData {
  records: CheckinRecord[]
  currentStreak: number     // 当前连续打卡天数
  longestStreak: number     // 最长连续打卡天数
  totalCheckins: number     // 总打卡次数
  lastCheckinDate: string   // 最后打卡日期 YYYY-MM-DD
}

const DEFAULT_DATA: CheckinData = {
  records: [],
  currentStreak: 0,
  longestStreak: 0,
  totalCheckins: 0,
  lastCheckinDate: ''
}

class CheckinSystemClass {
  private data = ref<CheckinData>({ ...DEFAULT_DATA })

  constructor() {
    this.load()
  }

  // ========= 持久化 =========

  private load() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        this.data.value = { ...DEFAULT_DATA, ...JSON.parse(saved) }
      }
    } catch (e) {
      console.warn('Failed to load checkin data:', e)
    }
  }

  private save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.data.value))
    } catch (e) {
      console.warn('Failed to save checkin data:', e)
    }
  }

  // ========= 查询 =========

  getData(): CheckinData {
    // 每次查询都刷新连续天数（防止用户几天没打开软件后数据不准）
    this.refreshStreak()
    return this.data.value
  }

  getCurrentStreak(): number {
    this.refreshStreak()
    return this.data.value.currentStreak
  }

  getLongestStreak(): number {
    return this.data.value.longestStreak
  }

  getTotalCheckins(): number {
    return this.data.value.totalCheckins
  }

  // 今天是否已打卡
  hasCheckedInToday(): boolean {
    return this.data.value.lastCheckinDate === this.getTodayStr()
  }

  // 今天是否可打卡（计划100%完成但还没打卡）
  canCheckinToday(): boolean {
    return !this.hasCheckedInToday()
  }

  // ========= 打卡操作 =========

  /**
   * 执行打卡
   * @param planName 计划名
   * @param progress 完成度（通常为100）
   * @returns 打卡后的连续天数，如果今天已打卡返回 null
   */
  checkin(planName: string, progress: number = 100): number | null {
    const today = this.getTodayStr()

    // 今天已打卡
    if (this.data.value.lastCheckinDate === today) {
      return null
    }

    // 添加打卡记录
    const record: CheckinRecord = {
      date: today,
      planName,
      progress,
      checkedInAt: new Date().toISOString()
    }
    this.data.value.records.push(record)

    // 更新连续天数
    this.refreshStreak()

    // 如果昨天有打卡，连续天数+1；否则重置为1
    const yesterday = this.getYesterdayStr()
    if (this.data.value.lastCheckinDate === yesterday) {
      this.data.value.currentStreak += 1
    } else {
      this.data.value.currentStreak = 1
    }

    // 更新最长连续
    if (this.data.value.currentStreak > this.data.value.longestStreak) {
      this.data.value.longestStreak = this.data.value.currentStreak
    }

    this.data.value.totalCheckins += 1
    this.data.value.lastCheckinDate = today

    this.save()

    return this.data.value.currentStreak
  }

  // ========= 连续天数刷新 =========

  /**
   * 刷新连续天数（处理跨天场景）
   * 如果用户几天没打开软件，连续天数可能会断
   */
  private refreshStreak() {
    if (!this.data.value.lastCheckinDate) {
      this.data.value.currentStreak = 0
      return
    }

    const lastDate = new Date(this.data.value.lastCheckinDate)
    const today = new Date(this.getTodayStr())
    const diffDays = Math.floor((today.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24))

    // 如果最后一次打卡是昨天或今天，连续天数保持
    // 如果超过1天没打卡，连续天数清零
    if (diffDays > 1) {
      this.data.value.currentStreak = 0
      this.save()
    }
  }

  // ========= 工具方法 =========

  private getTodayStr(): string {
    const d = new Date()
    return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
  }

  private getYesterdayStr(): string {
    const d = new Date()
    d.setDate(d.getDate() - 1)
    return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
  }

  // ========= 重置（调试用） =========
  reset() {
    this.data.value = { ...DEFAULT_DATA, records: [] }
    this.save()
  }
}

export const CheckinSystem = new CheckinSystemClass()
