// 应用状态管理

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { Config, Plans, ScheduleRule, TimeRecord, DayPlanInfo, RealTimeStat } from '@/types'
import { DataService, DEFAULT_CONFIG, DEFAULT_PLANS, DEFAULT_SCHEDULE_RULES, getTodayDate, normalizeConfig } from '@/services/dataService'
import { notifyWorkspaceChanged } from '@/services/workspaceEvents'

const ENABLE_SAMPLE_DATA = import.meta.env.VITE_EFFILIFE_DEMO_DATA === 'true'

export const useAppStore = defineStore('app', () => {
  // 状态
  const config = ref<Config>(DEFAULT_CONFIG)
  const plans = ref<Plans>(DEFAULT_PLANS)
  const scheduleRules = ref<ScheduleRule[]>(DEFAULT_SCHEDULE_RULES)
  const todayRecords = ref<TimeRecord[]>([])
  const todayPlan = ref<DayPlanInfo>({ name: '工作日', type: '切分制' })
  const todayStat = ref<RealTimeStat | null>(null)
  const isLoading = ref(false)
  let initPromise: Promise<void> | null = null
  let refreshPromise: Promise<void> | null = null
  let refreshRequested = false
  // Prevent a visibility/cross-window read that started before a local write
  // from overwriting the just-persisted configuration when it resolves later.
  let workspaceWriteVersion = 0
  // A cold IndexedDB open/migration can be slower than a normal read. Keep a
  // bounded stage timeout, but do not turn a transient cold start into a
  // workspace-wide startup failure after only five seconds.
  const INIT_STAGE_TIMEOUT_MS = 15000

  async function waitForInitStage<T>(name: string, task: Promise<T>): Promise<T> {
    let timeout: ReturnType<typeof setTimeout> | undefined
    try {
      return await Promise.race([
        task,
        new Promise<T>((_, reject) => {
          timeout = setTimeout(() => reject(new Error(`Workspace initialization stalled at ${name}`)), INIT_STAGE_TIMEOUT_MS)
        }),
      ])
    } finally {
      if (timeout) clearTimeout(timeout)
    }
  }

  // 计算属性
  const overtimeThreshold = computed(() => config.value.overtime_threshold)
  const showSeconds = computed(() => config.value.show_seconds)
  const use24h = computed(() => config.value.use_24h)

  // 初始化
  async function init() {
    if (initPromise) return initPromise
    isLoading.value = true
    initPromise = (async () => {
      // 执行数据迁移（首次启动时）
      await waitForInitStage('data migration', DataService.init())

      config.value = await waitForInitStage('configuration', DataService.loadConfig())
      plans.value = await waitForInitStage('plans', DataService.loadPlans())
      scheduleRules.value = await waitForInitStage('schedule rules', DataService.loadScheduleRules())

      // 如果没有记录数据，检查是否有历史记录
      const todayRecs = await waitForInitStage('records', DataService.loadRecords())
      if (todayRecs.length === 0) {
        // 检查 IndexedDB 中是否有任何记录
        const { isEmpty, STORE_NAMES: SN } = await import('@/storage')
        const recordsEmpty = await isEmpty(SN.RECORDS)
        if (recordsEmpty && ENABLE_SAMPLE_DATA) {
          await DataService.generateSampleData()
          // 重新加载数据
          config.value = await DataService.loadConfig()
          plans.value = await DataService.loadPlans()
          scheduleRules.value = await DataService.loadScheduleRules()
        }
      }

      await initializeTodayWorkspace()
    })()
    try {
      await initPromise
    } catch (error) {
      initPromise = null
      throw error
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

  // Keep the initial hydration stages separate so a cold-storage failure
  // identifies the exact dataset instead of collapsing into "today workspace".
  async function initializeTodayWorkspace() {
    const today = getTodayDate()
    todayRecords.value = await waitForInitStage('today records', DataService.loadRecords(today))
    todayPlan.value = await waitForInitStage('today plan', DataService.getDayPlan(today))
    todayStat.value = await waitForInitStage('today statistics', DataService.calcRealTimeStat(today))
  }

  /** Reload shared state after a change made by another window. */
  async function refreshWorkspaceData() {
    refreshRequested = true
    if (refreshPromise) return refreshPromise

    refreshPromise = (async () => {
      // Workspace events may arrive while a refresh is in flight. Serialize
      // reads and run one more pass when a later event requested it, so an
      // older response cannot overwrite a newer cross-module state change.
      do {
        refreshRequested = false
        const readVersion = workspaceWriteVersion
        const [nextConfig, nextPlans, nextScheduleRules] = await Promise.all([
          DataService.loadConfig(),
          DataService.loadPlans(),
          DataService.loadScheduleRules(),
        ])
        const nextRecords = await DataService.loadRecords(getTodayDate())
        const nextPlan = await DataService.getDayPlan(getTodayDate())
        const nextStat = await DataService.calcRealTimeStat(getTodayDate())
        if (readVersion !== workspaceWriteVersion) {
          // A local save completed while these reads were in flight. Discard
          // the stale batch and perform one fresh pass before exposing data.
          refreshRequested = true
          continue
        }
        config.value = nextConfig
        plans.value = nextPlans
        scheduleRules.value = nextScheduleRules
        todayRecords.value = nextRecords
        todayPlan.value = nextPlan
        todayStat.value = nextStat
      } while (refreshRequested)
    })()
    const currentRefresh = refreshPromise
    try {
      await currentRefresh
    } finally {
      if (refreshPromise === currentRefresh) refreshPromise = null
    }
  }

  // 保存配置
  async function saveConfig(newConfig: Config) {
    const normalizedConfig = normalizeConfig(newConfig)
    const previousConfig = config.value
    workspaceWriteVersion += 1
    config.value = normalizedConfig
    try {
      await DataService.saveConfig(normalizedConfig)
      notifyWorkspaceChanged('settings')
    } catch (error) {
      // Keep the in-memory workspace consistent with durable storage when a
      // write fails. Callers can still keep their draft and retry the save.
      config.value = previousConfig
      throw error
    }
  }

  // 仅更新运行时配置，用于设置页实时预览；不会写入持久化存储。
  function previewConfig(newConfig: Config) {
    config.value = newConfig
  }

  // 保存计划
  async function savePlans(newPlans: Plans) {
    plans.value = newPlans
    await DataService.savePlans(newPlans)
    notifyWorkspaceChanged('plans')
  }

  // 保存日程规则
  async function saveScheduleRules(newRules: ScheduleRule[]) {
    scheduleRules.value = newRules
    await DataService.saveScheduleRules(newRules)
    notifyWorkspaceChanged('plans')
  }

  // 添加记录
  async function addRecord(record: TimeRecord) {
    const today = getTodayDate()
    await DataService.saveRecord(record, today)
    await refreshTodayData()
    notifyWorkspaceChanged('records')
  }

  // 删除记录
  async function deleteRecord(index: number) {
    const today = getTodayDate()
    await DataService.deleteRecord(index, today)
    await refreshTodayData()
    notifyWorkspaceChanged('records')
  }

  // 更新记录
  async function updateRecord(index: number, record: TimeRecord) {
    const today = getTodayDate()
    await DataService.updateRecord(index, record, today)
    await refreshTodayData()
    notifyWorkspaceChanged('records')
  }

  // 切换今日计划
  async function changeTodayPlan(planName: string) {
    const today = getTodayDate()
    await DataService.saveDayPlan(planName, today)
    await refreshTodayData()
    notifyWorkspaceChanged('plans')
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
    refreshWorkspaceData,
    saveConfig,
    previewConfig,
    savePlans,
    saveScheduleRules,
    addRecord,
    deleteRecord,
    updateRecord,
    changeTodayPlan,
  }
})
