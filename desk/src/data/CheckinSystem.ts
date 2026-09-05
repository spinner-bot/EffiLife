// 打卡系统 - 记录用户连续完成计划的天数
import { ref, reactive } from 'vue'

const STORAGE_KEY = 'efflife_checkin_data'

// 全局响应式打卡状态（供组件监听）
export const checkinState = reactive({
  currentStreak: 0,
  longestStreak: 0,
  totalCheckins: 0,
  lastCheckinDate: '',
  hasCheckedInToday: false,
  // 变化计数器，组件可以 watch 这个值来刷新
  version: 0
})

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
      this.syncState()
    } catch (e) {
      console.warn('Failed to load checkin data:', e)
    }
  }

  private save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.data.value))
      // 更新全局响应式状态
      this.syncState()
    } catch (e) {
      console.warn('Failed to save checkin data:', e)
    }
  }

  private syncState() {
    checkinState.currentStreak = this.data.value.currentStreak
    checkinState.longestStreak = this.data.value.longestStreak
    checkinState.totalCheckins = this.data.value.totalCheckins
    checkinState.lastCheckinDate = this.data.value.lastCheckinDate
    checkinState.hasCheckedInToday = this.data.value.lastCheckinDate === this.getTodayStr()
    checkinState.version += 1
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

  // ========= 自动补打卡 =========

  /**
   * 检查并执行自动补打卡
   * 如果昨天有完成计划但未打卡，在新的一天自动补打卡
   * @returns 补打卡结果：'checked' 补打卡成功, 'already' 已打过卡, 'no-record' 昨天无记录, 'streak-broken' 连续天数已断
   */
  autoCheckinIfMissed(): { result: string; streak?: number } {
    const today = this.getTodayStr()
    const yesterday = this.getYesterdayStr()

    // 今天已打卡，无需补打卡
    if (this.data.value.lastCheckinDate === today) {
      return { result: 'already' }
    }

    // 检查昨天是否有完成的计划记录
    const yesterdayRecords = this.getYesterdayRecords()
    if (yesterdayRecords.length === 0) {
      return { result: 'no-record' }
    }

    // 检查连续天数是否已断（超过1天没打卡）
    if (this.data.value.lastCheckinDate) {
      const lastDate = new Date(this.data.value.lastCheckinDate)
      const yesterdayDate = new Date(yesterday)
      const diffDays = Math.floor((yesterdayDate.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24))
      if (diffDays > 1) {
        // 连续天数已断，无法补打卡
        return { result: 'streak-broken' }
      }
    }

    // 执行补打卡（使用昨天的第一个完成记录的计划名）
    const planName = yesterdayRecords[0]?.planName || '自动补打卡'
    const streak = this.checkinForDate(yesterday, planName, 100)

    if (streak !== null) {
      return { result: 'checked', streak }
    }

    return { result: 'failed' }
  }

  /**
   * 为指定日期打卡（用于补打卡）
   */
  checkinForDate(date: string, planName: string, progress: number): number | null {
    // 检查该日期是否已经打过卡
    const existingRecord = this.data.value.records.find(r => r.date === date)
    if (existingRecord) {
      return null  // 该日期已经打过卡
    }

    // 添加打卡记录
    const record: CheckinRecord = {
      date,
      planName,
      progress,
      checkedInAt: new Date().toISOString()
    }
    this.data.value.records.push(record)

    // 更新连续天数
    const yesterday = this.getPreviousDayStr(date)
    if (this.data.value.lastCheckinDate === yesterday || this.data.value.lastCheckinDate === '') {
      this.data.value.currentStreak += 1
    } else {
      this.data.value.currentStreak = 1
    }

    // 更新最长连续
    if (this.data.value.currentStreak > this.data.value.longestStreak) {
      this.data.value.longestStreak = this.data.value.currentStreak
    }

    this.data.value.totalCheckins += 1
    this.data.value.lastCheckinDate = date

    this.save()
    return this.data.value.currentStreak
  }

  /**
   * 获取昨天完成的计划记录（用于判断是否需要补打卡）
   */
  getYesterdayCompletedRecords(): { planName: string; progress: number }[] {
    const yesterday = this.getYesterdayStr()
    return this.getCompletedRecordsForDate(yesterday)
  }

  /**
   * 获取指定日期完成的计划记录
   */
  getCompletedRecordsForDate(dateStr: string): { planName: string; progress: number }[] {
    const key = `efflife_records_${dateStr}`
    try {
      const saved = localStorage.getItem(key)
      if (saved) {
        const records = JSON.parse(saved)
        // 筛选出完成度 100% 的记录
        return records
          .filter((r: { progress?: number }) => r.progress === 100)
          .map((r: { plan_name?: string; planName?: string; progress: number }) => ({
            planName: r.plan_name || r.planName || '未知计划',
            progress: r.progress
          }))
      }
    } catch (e) {
      console.warn('Failed to get records for date:', e)
    }
    return []
  }

  /**
   * 获取昨天的时间记录（判断是否完成了计划）
   */
  private getYesterdayRecords(): { planName: string; progress: number }[] {
    return this.getYesterdayCompletedRecords()
  }

  /**
   * 获取指定日期的前一天
   */
  private getPreviousDayStr(dateStr: string): string {
    const d = new Date(dateStr)
    d.setDate(d.getDate() - 1)
    return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart('0', '0')}-${d.getDate().toString().padStart('0', '0')}`
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

  // 公开的获取昨天日期方法
  getYesterdayDate(): string {
    return this.getYesterdayStr()
  }

  // ========= 重置（调试用） =========
  reset() {
    this.data.value = { ...DEFAULT_DATA, records: [] }
    this.save()
  }
}

export const CheckinSystem = new CheckinSystemClass()
