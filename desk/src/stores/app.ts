// 应用状态管理

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { Config, Plans, ScheduleRule, TimeRecord, DayPlanInfo, RealTimeStat } from '@/types'
import { DataService, DEFAULT_CONFIG, DEFAULT_PLANS, DEFAULT_SCHEDULE_RULES, getTodayDate } from '@/services/dataService'

export const useAppStore = defineStore('app', () => {
  // 状态
  const config = ref<Config>(DEFAULT_CONFIG)
  const plans = ref<Plans>(DEFAULT_PLANS)
  const scheduleRules = ref<ScheduleRule[]>(DEFAULT_SCHEDULE_RULES)
  const todayRecords = ref<TimeRecord[]>([])
  const todayPlan = ref<DayPlanInfo>({ name: '工作日', type: '切分制' })
  const todayStat = ref<RealTimeStat | null>(null)
  const isLoading = ref(false)

  // 计算属性
  const overtimeThreshold = computed(() => config.value.overtime_threshold)
  const showSeconds = computed(() => config.value.show_seconds)
  const use24h = computed(() => config.value.use_24h)

  // 初始化
  async function init() {
    isLoading.value = true
    try {
      config.value = await DataService.loadConfig()
      plans.value = await DataService.loadPlans()
      scheduleRules.value = await DataService.loadScheduleRules()
      await refreshTodayData()
    } finally {
      isLoading.value = false
    }
  }

  // 刷新今日数据
  async function refreshTodayData() {
    const today = getTodayDate()
    todayRecords.value = await DataService.loadRecords(today)
    todayPlan.value = await DataService.getDayPlan(today)
    todayStat.value = await DataService.calcRealTimeStat(today)
  }

  // 保存配置
  async function saveConfig(newConfig: Config) {
    config.value = newConfig
    await DataService.saveConfig(newConfig)
  }

  // 保存计划
  async function savePlans(newPlans: Plans) {
    plans.value = newPlans
    await DataService.savePlans(newPlans)
  }

  // 保存日程规则
  async function saveScheduleRules(newRules: ScheduleRule[]) {
    scheduleRules.value = newRules
    await DataService.saveScheduleRules(newRules)
  }

  // 添加记录
  async function addRecord(record: TimeRecord) {
    const today = getTodayDate()
    await DataService.saveRecord(record, today)
    await refreshTodayData()
  }

  // 删除记录
  async function deleteRecord(index: number) {
    const today = getTodayDate()
    await DataService.deleteRecord(index, today)
    await refreshTodayData()
  }

  // 更新记录
  async function updateRecord(index: number, record: TimeRecord) {
    const today = getTodayDate()
    await DataService.updateRecord(index, record, today)
    await refreshTodayData()
  }

  // 切换今日计划
  async function changeTodayPlan(planName: string) {
    const today = getTodayDate()
    await DataService.saveDayPlan(planName, today)
    await refreshTodayData()
  }

  return {
    // 状态
    config,
    plans,
    scheduleRules,
    todayRecords,
    todayPlan,
    todayStat,
    isLoading,
    // 计算属性
    overtimeThreshold,
    showSeconds,
    use24h,
    // 方法
    init,
    refreshTodayData,
    saveConfig,
    savePlans,
    saveScheduleRules,
    addRecord,
    deleteRecord,
    updateRecord,
    changeTodayPlan,
  }
})
