// time-helper API 层
// 提供清晰的接口规范，便于未来与 plan-helper、to-dos 等模块互通

import { DataService, hoursToHm, getTodayDate } from '@/services/dataService'
import { CheckinSystem, checkinState } from '@/data'
import { EventSystem } from '@/audio'
import type { Config, Plans, ScheduleRule, TimeRecord, RealTimeStat, DayPlanInfo } from '@/types'
import type { CheckinData, CheckinRecord } from '@/data'
import type { EventSettings, WarningRule, InboxEntry } from '@/audio'

// ============================================================
// 通用响应类型
// ============================================================

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  timestamp: string
}

function ok<T>(data: T): ApiResponse<T> {
  return { success: true, data, timestamp: new Date().toISOString() }
}

function fail<T>(error: string): ApiResponse<T> {
  return { success: false, error, timestamp: new Date().toISOString() }
}

// ============================================================
// 1. 配置 API
// ============================================================

export const ConfigApi = {
  /** 获取当前配置 */
  async getConfig(): Promise<ApiResponse<Config>> {
    try {
      const config = await DataService.loadConfig()
      return ok(config)
    } catch (e) {
      return fail('加载配置失败')
    }
  },

  /** 保存配置 */
  async saveConfig(config: Config): Promise<ApiResponse<void>> {
    try {
      await DataService.saveConfig(config)
      return ok(undefined)
    } catch (e) {
      return fail('保存配置失败')
    }
  },

  /** 更新部分配置 */
  async patchConfig(patch: Partial<Config>): Promise<ApiResponse<Config>> {
    try {
      const current = await DataService.loadConfig()
      const updated = { ...current, ...patch }
      await DataService.saveConfig(updated)
      return ok(updated)
    } catch (e) {
      return fail('更新配置失败')
    }
  },

  /** 重置配置为默认值 */
  async resetConfig(): Promise<ApiResponse<Config>> {
    try {
      const { DEFAULT_CONFIG } = await import('@/services/dataService')
      await DataService.saveConfig(DEFAULT_CONFIG)
      return ok(DEFAULT_CONFIG)
    } catch (e) {
      return fail('重置配置失败')
    }
  }
}

// ============================================================
// 2. 计划 API
// ============================================================

export const PlanApi = {
  /** 获取所有计划 */
  async getPlans(): Promise<ApiResponse<Plans>> {
    try {
      const plans = await DataService.loadPlans()
      return ok(plans)
    } catch (e) {
      return fail('加载计划失败')
    }
  },

  /** 保存所有计划 */
  async savePlans(plans: Plans): Promise<ApiResponse<void>> {
    try {
      await DataService.savePlans(plans)
      return ok(undefined)
    } catch (e) {
      return fail('保存计划失败')
    }
  },

  /** 获取指定计划详情 */
  async getPlan(name: string): Promise<ApiResponse<Plans[string] | null>> {
    try {
      const plans = await DataService.loadPlans()
      return ok(plans[name] || null)
    } catch (e) {
      return fail('获取计划详情失败')
    }
  },

  /** 添加/更新计划 */
  async upsertPlan(name: string, plan: Plans[string]): Promise<ApiResponse<void>> {
    try {
      const plans = await DataService.loadPlans()
      plans[name] = plan
      await DataService.savePlans(plans)
      return ok(undefined)
    } catch (e) {
      return fail('保存计划失败')
    }
  },

  /** 删除计划 */
  async deletePlan(name: string): Promise<ApiResponse<void>> {
    try {
      const plans = await DataService.loadPlans()
      delete plans[name]
      await DataService.savePlans(plans)
      return ok(undefined)
    } catch (e) {
      return fail('删除计划失败')
    }
  },

  /** 获取今日计划信息 */
  async getTodayPlan(): Promise<ApiResponse<DayPlanInfo>> {
    try {
      const plan = await DataService.getDayPlan()
      return ok(plan)
    } catch (e) {
      return fail('获取今日计划失败')
    }
  },

  /** 获取指定日期的计划 */
  async getDayPlan(date: string): Promise<ApiResponse<DayPlanInfo>> {
    try {
      const plan = await DataService.getDayPlan(date)
      return ok(plan)
    } catch (e) {
      return fail('获取日计划失败')
    }
  },

  /** 设置指定日期的计划 */
  async setDayPlan(planName: string, date?: string): Promise<ApiResponse<void>> {
    try {
      await DataService.saveDayPlan(planName, date)
      return ok(undefined)
    } catch (e) {
      return fail('设置日计划失败')
    }
  },

  /** 获取日程规则 */
  async getScheduleRules(): Promise<ApiResponse<ScheduleRule[]>> {
    try {
      const rules = await DataService.loadScheduleRules()
      return ok(rules)
    } catch (e) {
      return fail('获取日程规则失败')
    }
  },

  /** 保存日程规则 */
  async saveScheduleRules(rules: ScheduleRule[]): Promise<ApiResponse<void>> {
    try {
      await DataService.saveScheduleRules(rules)
      return ok(undefined)
    } catch (e) {
      return fail('保存日程规则失败')
    }
  }
}

// ============================================================
// 3. 时间记录 API
// ============================================================

export const RecordApi = {
  /** 获取指定日期的时间记录 */
  async getRecords(date?: string): Promise<ApiResponse<TimeRecord[]>> {
    try {
      const records = await DataService.loadRecords(date)
      return ok(records)
    } catch (e) {
      return fail('加载记录失败')
    }
  },

  /** 添加时间记录 */
  async addRecord(record: TimeRecord): Promise<ApiResponse<void>> {
    try {
      await DataService.saveRecord(record)
      return ok(undefined)
    } catch (e) {
      return fail('添加记录失败')
    }
  },

  /** 删除时间记录 */
  async deleteRecord(index: number, date?: string): Promise<ApiResponse<void>> {
    try {
      await DataService.deleteRecord(index, date)
      return ok(undefined)
    } catch (e) {
      return fail('删除记录失败')
    }
  },

  /** 更新指定记录 */
  async updateRecord(index: number, record: TimeRecord, date?: string): Promise<ApiResponse<void>> {
    try {
      await DataService.updateRecord(index, record, date)
      return ok(undefined)
    } catch (e) {
      return fail('更新记录失败')
    }
  },

  /** 获取日期范围内的所有记录 */
  async getRecordsInRange(startDate: string, endDate: string): Promise<ApiResponse<Record<string, TimeRecord[]>>> {
    try {
      const result: Record<string, TimeRecord[]> = {}
      const start = new Date(startDate)
      const end = new Date(endDate)
      const current = new Date(start)

      while (current <= end) {
        const dateStr = current.toISOString().split('T')[0]
        const records = await DataService.loadRecords(dateStr)
        if (records.length > 0) {
          result[dateStr] = records
        }
        current.setDate(current.getDate() + 1)
      }
      return ok(result)
    } catch (e) {
      return fail('获取范围记录失败')
    }
  },

  /** 获取实时统计 */
  async getRealTimeStat(date?: string): Promise<ApiResponse<RealTimeStat>> {
    try {
      const stat = await DataService.calcRealTimeStat(date)
      return ok(stat)
    } catch (e) {
      return fail('获取统计失败')
    }
  },

  /** 获取日期范围内的统计摘要 */
  async getStatsSummary(startDate: string, endDate: string): Promise<ApiResponse<{
    dates: string[]
    progress: number[]
    totalHours: number[]
    planNames: string[]
  }>> {
    try {
      const dates: string[] = []
      const progress: number[] = []
      const totalHours: number[] = []
      const planNames: string[] = []
      const start = new Date(startDate)
      const end = new Date(endDate)
      const current = new Date(start)

      while (current <= end) {
        const dateStr = current.toISOString().split('T')[0]
        const stat = await DataService.calcRealTimeStat(dateStr)
        dates.push(dateStr)
        progress.push(stat.progress)
        totalHours.push(stat.total_used_hours)
        planNames.push(stat.plan_name)
        current.setDate(current.getDate() + 1)
      }
      return ok({ dates, progress, totalHours, planNames })
    } catch (e) {
      return fail('获取统计摘要失败')
    }
  }
}

// ============================================================
// 4. 打卡 API
// ============================================================

export const CheckinApi = {
  /** 获取完整打卡数据 */
  getCheckinData(): ApiResponse<CheckinData> {
    try {
      const data = CheckinSystem.getData()
      return ok(data)
    } catch (e) {
      return fail('获取打卡数据失败')
    }
  },

  /** 获取当前连续天数 */
  getCurrentStreak(): ApiResponse<number> {
    return ok(CheckinSystem.getCurrentStreak())
  },

  /** 获取最长连续天数 */
  getLongestStreak(): ApiResponse<number> {
    return ok(CheckinSystem.getLongestStreak())
  },

  /** 获取累计打卡数 */
  getTotalCheckins(): ApiResponse<number> {
    return ok(CheckinSystem.getTotalCheckins())
  },

  /** 今天是否已打卡 */
  hasCheckedInToday(): ApiResponse<boolean> {
    return ok(CheckinSystem.hasCheckedInToday())
  },

  /** 执行打卡 */
  checkin(planName: string, progress: number = 100): ApiResponse<number | null> {
    try {
      const result = CheckinSystem.checkin(planName, progress)
      if (result !== null) {
        // 检查里程碑
        EventSystem.checkStreakMilestone(result)
        // 触发打卡完成事件
        EventSystem.triggerEvent(
          'checkin_complete',
          '打卡成功！',
          `连续打卡 ${result} 天 🔥`,
          { streak: result }
        )
      }
      return ok(result)
    } catch (e) {
      return fail('打卡失败')
    }
  },

  /** 为指定日期打卡（补打卡） */
  checkinForDate(date: string, planName: string, progress: number = 100): ApiResponse<number | null> {
    try {
      const result = CheckinSystem.checkinForDate(date, planName, progress)
      return ok(result)
    } catch (e) {
      return fail('补打卡失败')
    }
  },

  /** 获取打卡记录列表 */
  getCheckinRecords(): ApiResponse<CheckinRecord[]> {
    try {
      const data = CheckinSystem.getData()
      return ok(data.records)
    } catch (e) {
      return fail('获取打卡记录失败')
    }
  },

  /** 获取指定日期的打卡状态 */
  getCheckinStatus(date: string): ApiResponse<{ checkedIn: boolean; planName?: string }> {
    try {
      const data = CheckinSystem.getData()
      const record = data.records.find(r => r.date === date)
      if (record) {
        return ok({ checkedIn: true, planName: record.planName })
      }
      return ok({ checkedIn: false })
    } catch (e) {
      return fail('获取打卡状态失败')
    }
  },

  /** 获取日期范围内的打卡记录 */
  getCheckinsInRange(startDate: string, endDate: string): ApiResponse<CheckinRecord[]> {
    try {
      const data = CheckinSystem.getData()
      const filtered = data.records.filter(r => r.date >= startDate && r.date <= endDate)
      return ok(filtered)
    } catch (e) {
      return fail('获取范围打卡记录失败')
    }
  },

  /** 重置打卡数据（调试用） */
  reset(): ApiResponse<void> {
    try {
      CheckinSystem.reset()
      return ok(undefined)
    } catch (e) {
      return fail('重置打卡数据失败')
    }
  }
}

// ============================================================
// 5. 事件/收件箱 API
// ============================================================

export const EventApi = {
  /** 获取事件设置 */
  getSettings(): ApiResponse<EventSettings> {
    return ok(EventSystem.getSettings())
  },

  /** 更新事件设置 */
  updateSettings(patch: Partial<EventSettings>): ApiResponse<void> {
    try {
      EventSystem.updateSettings(patch)
      return ok(undefined)
    } catch (e) {
      return fail('更新事件设置失败')
    }
  },

  /** 获取收件箱条目 */
  getInbox(): ApiResponse<InboxEntry[]> {
    return ok(EventSystem.getEventInbox())
  },

  /** 获取未读数量 */
  getUnreadCount(): ApiResponse<number> {
    return ok(EventSystem.getUnreadCount())
  },

  /** 标记已读 */
  markAsRead(entryId: string): ApiResponse<void> {
    try {
      EventSystem.markAsRead(entryId)
      return ok(undefined)
    } catch (e) {
      return fail('标记已读失败')
    }
  },

  /** 全部标记已读 */
  markAllAsRead(): ApiResponse<void> {
    try {
      EventSystem.markAllAsRead()
      return ok(undefined)
    } catch (e) {
      return fail('标记全部已读失败')
    }
  },

  /** 删除条目 */
  deleteInboxEntry(entryId: string): ApiResponse<void> {
    try {
      EventSystem.deleteInboxEntry(entryId)
      return ok(undefined)
    } catch (e) {
      return fail('删除条目失败')
    }
  },

  /** 清空收件箱 */
  clearInbox(): ApiResponse<void> {
    try {
      EventSystem.clearInbox()
      return ok(undefined)
    } catch (e) {
      return fail('清空收件箱失败')
    }
  },

  /** 获取预警规则 */
  getWarningRules(): ApiResponse<WarningRule[]> {
    return ok(EventSystem.getWarningRules())
  },

  /** 添加预警规则 */
  addWarningRule(rule: Omit<WarningRule, 'id'>): ApiResponse<string> {
    try {
      const id = EventSystem.addWarningRule(rule)
      return ok(id)
    } catch (e) {
      return fail('添加预警规则失败')
    }
  },

  /** 更新预警规则 */
  updateWarningRule(id: string, updates: Partial<WarningRule>): ApiResponse<void> {
    try {
      EventSystem.updateWarningRule(id, updates)
      return ok(undefined)
    } catch (e) {
      return fail('更新预警规则失败')
    }
  },

  /** 删除预警规则 */
  deleteWarningRule(id: string): ApiResponse<void> {
    try {
      EventSystem.removeWarningRule(id)
      return ok(undefined)
    } catch (e) {
      return fail('删除预警规则失败')
    }
  },

  /** 手动触发事件 */
  triggerEvent(type: string, title: string, message: string, data?: any): ApiResponse<void> {
    try {
      EventSystem.triggerEvent(type as any, title, message, data)
      return ok(undefined)
    } catch (e) {
      return fail('触发事件失败')
    }
  }
}

// ============================================================
// 6. 聚合/分析 API（跨模块数据查询）
// ============================================================

export const AnalyticsApi = {
  /** 获取周度报告 */
  async getWeeklyReport(weekStart?: string): Promise<ApiResponse<{
    period: { start: string; end: string }
    totalRecords: number
    totalHours: number
    avgProgress: number
    checkinDays: number
    topTags: Array<{ tag: string; hours: number }>
    dailyProgress: Array<{ date: string; progress: number }>
  }>> {
    try {
      const today = new Date()
      const start = weekStart ? new Date(weekStart) : new Date(today)
      // 找到本周一
      const dayOfWeek = start.getDay() || 7
      start.setDate(start.getDate() - dayOfWeek + 1)
      const end = new Date(start)
      end.setDate(end.getDate() + 6)

      const startStr = start.toISOString().split('T')[0]
      const endStr = end.toISOString().split('T')[0]

      let totalRecords = 0
      let totalHours = 0
      let totalProgress = 0
      let daysWithRecords = 0
      const tagTotals: Record<string, number> = {}
      const dailyProgress: Array<{ date: string; progress: number }> = []

      const current = new Date(start)
      while (current <= end) {
        const dateStr = current.toISOString().split('T')[0]
        const stat = await DataService.calcRealTimeStat(dateStr)
        const records = await DataService.loadRecords(dateStr)

        totalRecords += records.length
        totalHours += stat.total_used_hours
        if (stat.has_records) {
          daysWithRecords++
          totalProgress += stat.progress
        }
        dailyProgress.push({ date: dateStr, progress: stat.progress })

        for (const [tag, hours] of Object.entries(stat.raw_stat)) {
          tagTotals[tag] = (tagTotals[tag] || 0) + hours
        }

        current.setDate(current.getDate() + 1)
      }

      const avgProgress = daysWithRecords > 0 ? Math.round(totalProgress / daysWithRecords) : 0
      const topTags = Object.entries(tagTotals)
        .map(([tag, hours]) => ({ tag, hours: Math.round(hours * 10) / 10 }))
        .sort((a, b) => b.hours - a.hours)
        .slice(0, 5)

      const checkinData = CheckinSystem.getData()
      const checkinDays = checkinData.records.filter(r => r.date >= startStr && r.date <= endStr).length

      return ok({
        period: { start: startStr, end: endStr },
        totalRecords,
        totalHours: Math.round(totalHours * 10) / 10,
        avgProgress,
        checkinDays,
        topTags,
        dailyProgress
      })
    } catch (e) {
      return fail('获取周报失败')
    }
  },

  /** 获取月度趋势 */
  async getMonthlyTrend(year: number, month: number): Promise<ApiResponse<{
    dailyProgress: number[]
    dailyHours: number[]
    totalHours: number
    avgProgress: number
    checkinCount: number
  }>> {
    try {
      const lastDay = new Date(year, month, 0).getDate()
      const dailyProgress: number[] = []
      const dailyHours: number[] = []
      let totalHours = 0
      let totalProgress = 0
      let daysWithRecords = 0

      for (let d = 1; d <= lastDay; d++) {
        const dateStr = `${year}-${month.toString().padStart(2, '0')}-${d.toString().padStart(2, '0')}`
        const stat = await DataService.calcRealTimeStat(dateStr)
        dailyProgress.push(stat.progress)
        dailyHours.push(Math.round(stat.total_used_hours * 10) / 10)
        totalHours += stat.total_used_hours
        if (stat.has_records) {
          daysWithRecords++
          totalProgress += stat.progress
        }
      }

      const checkinData = CheckinSystem.getData()
      const monthPrefix = `${year}-${month.toString().padStart(2, '0')}`
      const checkinCount = checkinData.records.filter(r => r.date.startsWith(monthPrefix)).length

      return ok({
        dailyProgress,
        dailyHours,
        totalHours: Math.round(totalHours * 10) / 10,
        avgProgress: daysWithRecords > 0 ? Math.round(totalProgress / daysWithRecords) : 0,
        checkinCount
      })
    } catch (e) {
      return fail('获取月度趋势失败')
    }
  },

  /** 获取综合摘要（供外部模块调用） */
  async getSummary(): Promise<ApiResponse<{
    todayProgress: number
    todayPlanName: string
    currentStreak: number
    totalCheckins: number
    unreadEvents: number
    todayRecords: number
  }>> {
    try {
      const stat = await DataService.calcRealTimeStat()
      const records = await DataService.loadRecords()
      return ok({
        todayProgress: stat.progress,
        todayPlanName: stat.plan_name,
        currentStreak: CheckinSystem.getCurrentStreak(),
        totalCheckins: CheckinSystem.getTotalCheckins(),
        unreadEvents: EventSystem.getUnreadCount(),
        todayRecords: records.length
      })
    } catch (e) {
      return fail('获取摘要失败')
    }
  }
}

// ============================================================
// 7. 工具函数 API
// ============================================================

export const UtilsApi = {
  /** 小时数转可读字符串 */
  hoursToHm,

  /** 获取今天日期字符串 */
  getTodayDate,

  /** 日期加减 */
  addDays(dateStr: string, days: number): string {
    const date = new Date(dateStr)
    date.setDate(date.getDate() + days)
    return date.toISOString().split('T')[0]
  },

  /** 格式化时间范围 */
  formatTimeRange(start: string, end: string): string {
    return `${start} - ${end}`
  }
}

// ============================================================
// 统一导出
// ============================================================

export const TimeHelperApi = {
  config: ConfigApi,
  plan: PlanApi,
  record: RecordApi,
  checkin: CheckinApi,
  event: EventApi,
  analytics: AnalyticsApi,
  utils: UtilsApi
}

export default TimeHelperApi
