// 存档服务 - 处理数据导出/导入/重置
import JSZip from 'jszip'
import { saveAs } from 'file-saver'

// 存档版本
const ARCHIVE_VERSION = '2.0'

// 检测是否在 Tauri 环境
function isTauri(): boolean {
  return !!(window as any).__TAURI__
}

// 检测是否在移动端（Android/iOS）
function isMobile(): boolean {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

// 检测是否在 Tauri 移动端
function isTauriMobile(): boolean {
  return isTauri() && isMobile()
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
  records: Record<string, unknown[]>
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

// 收集所有数据
function collectAllData(): ArchiveData {
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
    records: getAllRecords(),
  }
}

// 导出数据为 .efl 文件
export async function exportArchive(): Promise<{ success: boolean; path?: string }> {
  const data = collectAllData()
  const zip = new JSZip()

  // 添加主数据文件
  zip.file('archive.json', JSON.stringify(data, null, 2))

  // 添加说明文件
  zip.file('README.txt', `浪兮效率时钟存档文件
版本: ${ARCHIVE_VERSION}
导出时间: ${new Date(data.exportDate).toLocaleString('zh-CN')}

此文件包含以下数据:
- 应用配置
- 计划和时间表规则
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

      return { success: true, path: filePath }
    } catch (e) {
      // Tauri API 失败，回退到浏览器下载
      console.warn('Tauri export failed, falling back to browser:', e)
    }
  }

  // 移动端 Tauri 或浏览器环境，使用浏览器下载
  // Tauri Mobile 的 WebView 也支持 saveAs 下载
  saveAs(blob, fileName)
  return { success: true }
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

// 处理存档数据（内部函数）
async function processArchiveData(zip: JSZip): Promise<{ success: boolean; message: string }> {
  // 读取主数据文件
    const archiveFile = zip.file('archive.json')
    if (!archiveFile) {
      return { success: false, message: '存档文件格式无效：缺少 archive.json' }
    }

    const content = await archiveFile.async('text')
    const data: ArchiveData = JSON.parse(content)

    // 验证版本
    if (!data.version) {
      return { success: false, message: '存档文件格式无效：缺少版本信息' }
    }

    // 恢复数据
    if (data.config) writeJSON(STORAGE_KEYS.CONFIG, data.config)
    if (data.plans) writeJSON(STORAGE_KEYS.PLANS, data.plans)
    if (data.scheduleRules) writeJSON(STORAGE_KEYS.SCHEDULE_RULES, data.scheduleRules)
    if (data.manualPlans) writeJSON(STORAGE_KEYS.MANUAL_PLANS, data.manualPlans)
    if (data.audioSettings) writeJSON(STORAGE_KEYS.AUDIO_SETTINGS, data.audioSettings)
    if (data.eventSettings) writeJSON(STORAGE_KEYS.EVENT_SETTINGS, data.eventSettings)
    if (data.eventInbox) writeJSON(STORAGE_KEYS.EVENT_INBOX, data.eventInbox)
    if (data.warningInbox) writeJSON(STORAGE_KEYS.WARNING_INBOX, data.warningInbox)
    if (data.dailyTrigger) writeJSON(STORAGE_KEYS.DAILY_TRIGGER, data.dailyTrigger)
    if (data.checkin) writeJSON(STORAGE_KEYS.CHECKIN, data.checkin)

    // 恢复日期记录
    if (data.records) {
      // 先清除现有的记录
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i)
        if (key && key.startsWith('efflife_records_')) {
          localStorage.removeItem(key)
        }
      }
      // 写入新记录
      for (const [date, records] of Object.entries(data.records)) {
        writeJSON(`efflife_records_${date}`, records)
      }
    }

  return { success: true, message: '存档导入成功' }
}

// 重置类型
export type ResetType = 'all' | 'records' | 'plans' | 'config' | 'settings'

// 重置数据
export function resetData(type: ResetType): void {
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
      break

    case 'plans':
      localStorage.removeItem(STORAGE_KEYS.PLANS)
      localStorage.removeItem(STORAGE_KEYS.SCHEDULE_RULES)
      localStorage.removeItem(STORAGE_KEYS.MANUAL_PLANS)
      break

    case 'config':
      localStorage.removeItem(STORAGE_KEYS.CONFIG)
      break

    case 'settings':
      localStorage.removeItem(STORAGE_KEYS.AUDIO_SETTINGS)
      localStorage.removeItem(STORAGE_KEYS.EVENT_SETTINGS)
      localStorage.removeItem(STORAGE_KEYS.EVENT_INBOX)
      localStorage.removeItem(STORAGE_KEYS.WARNING_INBOX)
      localStorage.removeItem(STORAGE_KEYS.DAILY_TRIGGER)
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
