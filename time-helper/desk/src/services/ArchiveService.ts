// 存档服务 - 处理数据导出/导入/重置
import JSZip from 'jszip'
import { saveAs } from 'file-saver'

// 存档版本
const ARCHIVE_VERSION = '2.1'

// 检测是否在 Tauri 环境
function isTauri(): boolean {
  return !!(window as any).__TAURI__
}

// 检测是否在移动端（Android/iOS）
function isMobile(): boolean {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

// 获取下载路径设置
function getDownloadPath(): string | null {
  return localStorage.getItem('efflife_download_path')
}

// 设置下载路径
export function setDownloadPath(path: string): void {
  localStorage.setItem('efflife_download_path', path)
}

// 所有需要保存的 localStorage 键
const STORAGE_KEYS = {
  // 基础配置
  CONFIG: 'efflife_config',
  PLANS: 'efflife_plans',
  SCHEDULE_RULES: 'efflife_schedule_rules',
  MANUAL_PLANS: 'efflife_manual_plans',

  // 音频设置
  AUDIO_SETTINGS: 'efflife_audio_settings',

  // 事件系统
  EVENT_SETTINGS: 'efflife_event_settings',
  EVENT_INBOX: 'efflife_event_inbox',
  WARNING_INBOX: 'efflife_warning_inbox',
  DAILY_TRIGGER: 'efflife_daily_trigger',

  // 打卡系统
  CHECKIN: 'efflife_checkin',

  // 引导状态
  GUIDE_COMPLETED: 'efflife_guide_completed',
}

// 导出数据的接口
export interface ArchiveData {
  version: string
  exportDate: string
  config: Record<string, unknown> | null
  plans: Record<string, unknown> | null
  scheduleRules: unknown[] | null
  manualPlans: Record<string, string> | null
  audioSettings: Record<string, unknown> | null
  eventSettings: Record<string, unknown> | null
  eventInbox: unknown[] | null
  warningInbox: unknown[] | null
  dailyTrigger: Record<string, unknown> | null
  checkin: Record<string, unknown> | null
  locale?: string
  records: Record<string, unknown[]>
  todos: unknown[]
  planHelper: {
    available: boolean
    plans: unknown[]
  }
}

// 获取所有日期记录
function getAllRecords(): Record<string, unknown[]> {
  const records: Record<string, unknown[]> = {}
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith('efflife_records_')) {
      const date = key.replace('efflife_records_', '')
      try {
        records[date] = JSON.parse(localStorage.getItem(key) || '[]')
      } catch {
        records[date] = []
      }
    }
  }
  return records
}

// 从 localStorage 读取 JSON
function readJSON<T>(key: string): T | null {
  try {
    const data = localStorage.getItem(key)
    return data ? JSON.parse(data) : null
  } catch {
    return null
  }
}

// 写入 JSON 到 localStorage
function writeJSON(key: string, data: unknown): void {
  localStorage.setItem(key, JSON.stringify(data))
}

async function collectPlanHelperData(): Promise<ArchiveData['planHelper']> {
  try {
    const response = await fetch('http://127.0.0.1:8765/api/data/export', {
      headers: { Accept: 'application/json' },
    })
    if (!response.ok) throw new Error(`plan-helper responded with ${response.status}`)
    const payload = await response.json() as {
      success?: boolean
      data?: { plans?: unknown[] }
    }
    if (!payload.success || !Array.isArray(payload.data?.plans)) throw new Error('Invalid plan-helper export')
    return { available: true, plans: payload.data.plans }
  } catch {
    return { available: false, plans: [] }
  }
}

// 收集所有数据
async function collectAllData(): Promise<ArchiveData> {
  const { getRawAll, STORE_NAMES } = await import('@/storage')
  return {
    version: ARCHIVE_VERSION,
    exportDate: new Date().toISOString(),
    config: readJSON(STORAGE_KEYS.CONFIG),
    plans: readJSON(STORAGE_KEYS.PLANS),
    scheduleRules: readJSON(STORAGE_KEYS.SCHEDULE_RULES),
    manualPlans: readJSON(STORAGE_KEYS.MANUAL_PLANS),
    audioSettings: readJSON(STORAGE_KEYS.AUDIO_SETTINGS),
    eventSettings: readJSON(STORAGE_KEYS.EVENT_SETTINGS),
    eventInbox: readJSON(STORAGE_KEYS.EVENT_INBOX),
    warningInbox: readJSON(STORAGE_KEYS.WARNING_INBOX),
    dailyTrigger: readJSON(STORAGE_KEYS.DAILY_TRIGGER),
    checkin: readJSON(STORAGE_KEYS.CHECKIN),
    locale: localStorage.getItem('effilife_locale') || 'zh-CN',
    records: getAllRecords(),
    todos: await getRawAll(STORE_NAMES.TODOS),
    planHelper: await collectPlanHelperData(),
  }
}

// 导出数据为 .efl 文件
export async function exportArchive(): Promise<{ success: boolean; path?: string; warning?: string }> {
  const data = await collectAllData()
  const zip = new JSZip()

  // 使用公共层约定的 manifest + datasets 协议导出。
  const { records, todos, planHelper, ...app } = data
  const datasets = ['app', 'records', 'todos', 'plan_helper']
  zip.file('manifest.json', JSON.stringify({
    format: 'effilife.bundle',
    format_version: '1.0.0',
    created_at: data.exportDate,
    datasets,
    metadata: { source: 'time-helper', archive_version: ARCHIVE_VERSION },
  }, null, 2))
  zip.file('data/app.json', JSON.stringify(app, null, 2))
  zip.file('data/records.json', JSON.stringify(records, null, 2))
  zip.file('data/todos.json', JSON.stringify(todos, null, 2))
  zip.file('data/plan_helper.json', JSON.stringify(planHelper, null, 2))

  // 添加说明文件
  zip.file('README.txt', `浪兮效率时钟存档文件
协议: effilife.bundle 1.0.0
版本: ${ARCHIVE_VERSION}
导出时间: ${new Date(data.exportDate).toLocaleString('zh-CN')}

此文件包含以下数据:
- 应用配置
- 计划和时间表规则
- plan-helper 原始事件计划快照
- 音频和事件设置
- 打卡记录
- 历史记录

导入方法: 设置 → 更多设置 → 存档管理 → 导入存档
`)

  // 生成 zip blob
  const blob = await zip.generateAsync({ type: 'blob' })

  // 生成文件名
  const dateStr = new Date().toISOString().split('T')[0]
  const fileName = `efflife_archive_${dateStr}.efl`

  // 如果在 Tauri 桌面环境，使用原生对话框
  if (isTauri() && !isMobile()) {
    try {
      const { save } = await import('@tauri-apps/plugin-dialog')
      const { writeFile } = await import('@tauri-apps/plugin-fs')

      const filePath = await save({
        title: '导出存档',
        defaultPath: getDownloadPath() || fileName,
        filters: [{ name: '效率时钟存档', extensions: ['efl'] }]
      })

      if (!filePath) {
        return { success: false }
      }

      // 保存文件
      const buffer = await blob.arrayBuffer()
      await writeFile(filePath, new Uint8Array(buffer))

      // 记住用户选择的目录
      const dir = filePath.substring(0, filePath.lastIndexOf('\\')) || filePath.substring(0, filePath.lastIndexOf('/'))
      if (dir) {
        setDownloadPath(dir + '/' + fileName.replace(/_[\d-]+\.efl$/, '_'))
      }

      return {
        success: true,
        path: filePath,
        warning: data.planHelper.available ? undefined : 'plan-helper 当前不可用，存档未包含事件计划快照',
      }
    } catch (e) {
      // Tauri API 失败，回退到浏览器下载
      console.warn('Tauri export failed, falling back to browser:', e)
    }
  }

  // 移动端 Tauri 或浏览器环境，使用浏览器下载
  // Tauri Mobile 的 WebView 也支持 saveAs 下载
  saveAs(blob, fileName)
  return {
    success: true,
    warning: data.planHelper.available ? undefined : 'plan-helper 当前不可用，存档未包含事件计划快照',
  }
}

// 从 .efl 文件导入数据
export async function importArchive(file: File): Promise<{ success: boolean; message: string }> {
  try {
    // 检查文件扩展名
    if (!file.name.endsWith('.efl')) {
      return { success: false, message: '请选择 .efl 格式的存档文件' }
    }

    // 读取 zip 文件
    const zip = await JSZip.loadAsync(file)

    return await processArchiveData(zip)
  } catch (e) {
    return { success: false, message: `导入失败：${(e as Error).message}` }
  }
}

// 在 Tauri 桌面环境下打开文件对话框导入
export async function importArchiveWithDialog(): Promise<{ success: boolean; message: string; cancelled?: boolean }> {
  // 移动端使用文件选择器，不使用此函数
  if (!isTauri() || isMobile()) {
    return { success: false, message: '请使用文件选择器导入' }
  }

  try {
    const { open } = await import('@tauri-apps/plugin-dialog')
    const { readFile } = await import('@tauri-apps/plugin-fs')

    const filePath = await open({
      title: '导入存档',
      filters: [{ name: '效率时钟存档', extensions: ['efl'] }],
      multiple: false,
      directory: false
    })

    if (!filePath) {
      return { success: false, message: '', cancelled: true }
    }

    // 读取文件
    const data = await readFile(filePath as string)
    const blob = new Blob([data])
    const zip = await JSZip.loadAsync(blob)

    return await processArchiveData(zip)
  } catch (e) {
    return { success: false, message: `导入失败：${(e as Error).message}` }
  }
}

async function parseArchiveData(zip: JSZip): Promise<ArchiveData> {
  const manifestFile = zip.file('manifest.json')
  if (manifestFile) {
    let manifest: { format?: string; format_version?: string; created_at?: string; datasets?: string[] }
    try {
      manifest = JSON.parse(await manifestFile.async('text'))
    } catch {
      throw new Error('存档 manifest.json 无效')
    }
    if (manifest.format !== 'effilife.bundle' || !Array.isArray(manifest.datasets)) {
      throw new Error('不支持的 .efl 存档协议')
    }

    const datasets: Record<string, unknown> = {}
    for (const name of manifest.datasets) {
      if (!/^[A-Za-z0-9_-]+$/.test(name)) throw new Error(`非法数据集名称：${name}`)
      const file = zip.file(`data/${name}.json`)
      if (!file) throw new Error(`存档缺少数据集：${name}`)
      try {
        datasets[name] = JSON.parse(await file.async('text'))
      } catch {
        throw new Error(`数据集无效：${name}`)
      }
    }

    const app = (datasets.app && typeof datasets.app === 'object') ? datasets.app as Partial<ArchiveData> : {}
    const planHelper = datasets.plan_helper || datasets.planHelper || {
      available: Array.isArray(datasets.plans),
      plans: Array.isArray(datasets.plans) ? datasets.plans : [],
    }
    return {
      version: String(app.version || manifest.format_version || '1.0.0'),
      exportDate: String(app.exportDate || manifest.created_at || new Date().toISOString()),
      config: app.config || null,
      plans: app.plans || null,
      scheduleRules: app.scheduleRules || null,
      manualPlans: app.manualPlans || null,
      audioSettings: app.audioSettings || null,
      eventSettings: app.eventSettings || null,
      eventInbox: app.eventInbox || null,
      warningInbox: app.warningInbox || null,
      dailyTrigger: app.dailyTrigger || null,
      checkin: app.checkin || null,
      locale: typeof app.locale === 'string' ? app.locale : 'zh-CN',
      records: (datasets.records && typeof datasets.records === 'object' ? datasets.records : {}) as Record<string, unknown[]>,
      todos: Array.isArray(datasets.todos) ? datasets.todos : [],
      planHelper: (planHelper && typeof planHelper === 'object' ? planHelper : { available: false, plans: [] }) as ArchiveData['planHelper'],
    }
  }

  // 兼容 2.0 及更早的单文件 archive.json 存档。
  const archiveFile = zip.file('archive.json')
  if (!archiveFile) throw new Error('存档格式无效：缺少 manifest.json 或 archive.json')
  let legacy: ArchiveData
  try {
    legacy = JSON.parse(await archiveFile.async('text')) as ArchiveData
  } catch {
    throw new Error('旧版 archive.json 无效')
  }
  if (!legacy.version) throw new Error('存档文件格式无效：缺少版本信息')
  return {
    ...legacy,
    locale: legacy.locale || 'zh-CN',
    todos: Array.isArray(legacy.todos) ? legacy.todos : [],
    planHelper: legacy.planHelper || { available: false, plans: [] },
  }
}

// 处理存档数据（内部函数）
async function processArchiveData(zip: JSZip): Promise<{ success: boolean; message: string }> {
    const data = await parseArchiveData(zip)

    // 导入存储模块
    const { set: idbSet, putRaw, STORE_NAMES, clear: idbClear } = await import('@/storage')

    // 恢复数据（同时写入 localStorage 和 IndexedDB）
    if (data.config) {
      writeJSON(STORAGE_KEYS.CONFIG, data.config)
      await idbSet(STORE_NAMES.CONFIG, 'config', data.config)
    }
    if (data.plans) {
      writeJSON(STORAGE_KEYS.PLANS, data.plans)
      await idbSet(STORE_NAMES.PLANS, 'plans', data.plans)
    }
    if (data.scheduleRules) {
      writeJSON(STORAGE_KEYS.SCHEDULE_RULES, data.scheduleRules)
      await idbSet(STORE_NAMES.SCHEDULE_RULES, 'rules', data.scheduleRules)
    }
    if (data.manualPlans) {
      writeJSON(STORAGE_KEYS.MANUAL_PLANS, data.manualPlans)
      await idbSet(STORE_NAMES.MANUAL_PLANS, 'all', data.manualPlans)
    }
    if (data.audioSettings) {
      writeJSON(STORAGE_KEYS.AUDIO_SETTINGS, data.audioSettings)
      await idbSet(STORE_NAMES.AUDIO_SETTINGS, 'settings', data.audioSettings)
    }
    if (data.eventSettings) {
      writeJSON(STORAGE_KEYS.EVENT_SETTINGS, data.eventSettings)
      await idbSet(STORE_NAMES.EVENT_SETTINGS, 'settings', data.eventSettings)
    }
    if (data.eventInbox) {
      writeJSON(STORAGE_KEYS.EVENT_INBOX, data.eventInbox)
      await idbSet(STORE_NAMES.EVENT_INBOX, 'inbox', data.eventInbox)
    }
    if (data.warningInbox) {
      writeJSON(STORAGE_KEYS.WARNING_INBOX, data.warningInbox)
      await idbSet(STORE_NAMES.WARNING_INBOX, 'inbox', data.warningInbox)
    }
    if (data.dailyTrigger) {
      writeJSON(STORAGE_KEYS.DAILY_TRIGGER, data.dailyTrigger)
      await idbSet(STORE_NAMES.DAILY_TRIGGER, 'trigger', data.dailyTrigger)
    }
    if (data.checkin) {
      writeJSON(STORAGE_KEYS.CHECKIN, data.checkin)
      await idbSet(STORE_NAMES.CHECKIN, 'data', data.checkin)
    }
    if (data.locale === 'zh-CN' || data.locale === 'en-US') {
      localStorage.setItem('effilife_locale', data.locale)
    }

    // 恢复日期记录
    if (data.records) {
      // 先清除现有的记录
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i)
        if (key && key.startsWith('efflife_records_')) {
          localStorage.removeItem(key)
        }
      }
      // 清除 IndexedDB 记录
      await idbClear(STORE_NAMES.RECORDS)

      // 写入新记录
      for (const [date, records] of Object.entries(data.records)) {
        writeJSON(`efflife_records_${date}`, records)
        await idbSet(STORE_NAMES.RECORDS, date, records)
      }
    }

    // 恢复统一待办对象存储
    if (Array.isArray(data.todos)) {
      await idbClear(STORE_NAMES.TODOS)
      for (const todo of data.todos) {
        if (todo && typeof todo === 'object' && 'id' in todo) {
          await putRaw(STORE_NAMES.TODOS, todo)
        }
      }
    }

    const warnings: string[] = []
    if (data.planHelper?.available && Array.isArray(data.planHelper.plans)) {
      try {
        const response = await fetch('http://127.0.0.1:8765/api/data/import', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify({ plans: data.planHelper.plans, replace: true }),
        })
        const payload = await response.json() as { success?: boolean; error?: string }
        if (!response.ok || !payload.success) throw new Error(payload.error || `HTTP ${response.status}`)
      } catch (error) {
        warnings.push(`事件计划恢复失败：${error instanceof Error ? error.message : '计划服务不可用'}`)
      }
    } else if (data.planHelper && !data.planHelper.available) {
      warnings.push('存档生成时 plan-helper 不可用，未包含事件计划快照')
    }

  return {
    success: true,
    message: warnings.length ? `存档已导入，但有提示：${warnings.join('；')}` : '存档导入成功',
  }
}

async function clearPlanHelperData(): Promise<void> {
  try {
    await fetch('http://127.0.0.1:8765/api/data/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plans: [], replace: true }),
    })
  } catch {
    // plan-helper may not be running; local reset remains valid.
  }
}

// 重置类型
export type ResetType = 'all' | 'records' | 'plans' | 'config' | 'settings'

// 重置数据（同时清除 localStorage 和 IndexedDB）
export async function resetData(type: ResetType): Promise<void> {
  // 导入存储模块
  const { clear: idbClear, STORE_NAMES } = await import('@/storage')

  switch (type) {
    case 'all':
      // 清除所有 efflife_ 开头的键
      const keysToRemove: string[] = []
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith('efflife_')) {
          keysToRemove.push(key)
        }
      }
      keysToRemove.forEach(key => localStorage.removeItem(key))
      // 清除 IndexedDB
      await idbClear(STORE_NAMES.CONFIG)
      await idbClear(STORE_NAMES.PLANS)
      await idbClear(STORE_NAMES.RECORDS)
      await idbClear(STORE_NAMES.SCHEDULE_RULES)
      await idbClear(STORE_NAMES.MANUAL_PLANS)
      await idbClear(STORE_NAMES.AUDIO_SETTINGS)
      await idbClear(STORE_NAMES.EVENT_SETTINGS)
      await idbClear(STORE_NAMES.EVENT_INBOX)
      await idbClear(STORE_NAMES.WARNING_INBOX)
      await idbClear(STORE_NAMES.DAILY_TRIGGER)
      await idbClear(STORE_NAMES.CHECKIN)
      await idbClear(STORE_NAMES.TODOS)
      await clearPlanHelperData()
      break

    case 'records':
      // 只清除记录
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i)
        if (key && key.startsWith('efflife_records_')) {
          localStorage.removeItem(key)
        }
      }
      localStorage.removeItem(STORAGE_KEYS.CHECKIN)
      localStorage.removeItem(STORAGE_KEYS.MANUAL_PLANS)
      await idbClear(STORE_NAMES.RECORDS)
      await idbClear(STORE_NAMES.CHECKIN)
      await idbClear(STORE_NAMES.MANUAL_PLANS)
      break

    case 'plans':
      localStorage.removeItem(STORAGE_KEYS.PLANS)
      localStorage.removeItem(STORAGE_KEYS.SCHEDULE_RULES)
      localStorage.removeItem(STORAGE_KEYS.MANUAL_PLANS)
      await idbClear(STORE_NAMES.PLANS)
      await idbClear(STORE_NAMES.SCHEDULE_RULES)
      await idbClear(STORE_NAMES.MANUAL_PLANS)
      await clearPlanHelperData()
      break

    case 'config':
      localStorage.removeItem(STORAGE_KEYS.CONFIG)
      await idbClear(STORE_NAMES.CONFIG)
      break

    case 'settings':
      localStorage.removeItem(STORAGE_KEYS.AUDIO_SETTINGS)
      localStorage.removeItem(STORAGE_KEYS.EVENT_SETTINGS)
      localStorage.removeItem(STORAGE_KEYS.EVENT_INBOX)
      localStorage.removeItem(STORAGE_KEYS.WARNING_INBOX)
      localStorage.removeItem(STORAGE_KEYS.DAILY_TRIGGER)
      await idbClear(STORE_NAMES.AUDIO_SETTINGS)
      await idbClear(STORE_NAMES.EVENT_SETTINGS)
      await idbClear(STORE_NAMES.EVENT_INBOX)
      await idbClear(STORE_NAMES.WARNING_INBOX)
      await idbClear(STORE_NAMES.DAILY_TRIGGER)
      break
  }

  // 刷新页面以应用更改
  window.location.reload()
}

// 获取数据统计
export function getDataStats(): {
  recordDays: number
  totalRecords: number
  hasConfig: boolean
  hasPlans: boolean
  hasAudioSettings: boolean
  hasEventSettings: boolean
  hasCheckin: boolean
} {
  const records = getAllRecords()
  let totalRecords = 0
  for (const dateRecords of Object.values(records)) {
    totalRecords += dateRecords.length
  }

  return {
    recordDays: Object.keys(records).length,
    totalRecords,
    hasConfig: !!readJSON(STORAGE_KEYS.CONFIG),
    hasPlans: !!readJSON(STORAGE_KEYS.PLANS),
    hasAudioSettings: !!readJSON(STORAGE_KEYS.AUDIO_SETTINGS),
    hasEventSettings: !!readJSON(STORAGE_KEYS.EVENT_SETTINGS),
    hasCheckin: !!readJSON(STORAGE_KEYS.CHECKIN),
  }
}
