// 存档服务 - 处理数据导出/导入/重置
import JSZip from 'jszip'
import { saveAs } from 'file-saver'
import {
  DEFAULT_TODO_CATEGORIES,
  normalizeImportedCategory,
  normalizeImportedTodo,
  TodoCategoryService,
  TodoSettingsService,
  type TodoCategory,
  type TodoSettings,
  type UnifiedTodo,
} from './todoService'
import { PLAN_HELPER_ORIGIN } from './runtimeConfig'
import { getPlanRuntime, isMobilePlatform, isTauriRuntime } from './runtimeCapabilities'
import { clearPlanHelperResetPending, markPlanHelperResetPending, syncPendingPlanHelperReset } from './planReset'
import { currentLocale, setLocale, translate } from '@/i18n'
import { getTodayDate, normalizeConfig } from '@/services/dataService'
import type { Config } from '@/types'
import { notifyWorkspaceChanged } from './workspaceEvents'
import { MOTION_SETTINGS_STORAGE_KEY } from '@/motion/MotionManager'

// 存档版本
const ARCHIVE_VERSION = '2.2'
const ARCHIVE_FORMAT = 'effilife.bundle'
const ARCHIVE_FORMAT_VERSION = '1.0.0'
const CANONICAL_ARCHIVE_DATASETS = ['app', 'records', 'todos', 'todo_categories', 'plan_helper'] as const
const MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
const MAX_ARCHIVE_DATASET_BYTES = 32 * 1024 * 1024
const MAX_ARCHIVE_TOTAL_DATASET_BYTES = 64 * 1024 * 1024
const MAX_ARCHIVE_DATASET_COUNT = 16
const MAX_ARCHIVE_ENTRIES = 64
const PLAN_HELPER_REQUEST_TIMEOUT_MS = 4000

function assertArchiveBlobSize(blob: Blob): void {
  if (blob.size > MAX_ARCHIVE_BYTES) {
    throw new Error(translate('settings.archive.fileTooLarge'))
  }
}

function assertArchiveEntryCount(zip: JSZip): void {
  if (Object.keys(zip.files).length > MAX_ARCHIVE_ENTRIES) {
    throw new Error(translate('settings.archive.tooManyEntries'))
  }
}

async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const input = new Uint8Array(bytes)
  const digest = await crypto.subtle.digest('SHA-256', input.buffer as ArrayBuffer)
  return Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, '0')).join('')
}

/**
 * Serialize bundle datasets with the same rules as common.data_exchange.
 *
 * The Python side uses ``json.dumps(..., indent=2, sort_keys=True,
 * ensure_ascii=False)``. Object insertion order is not a data contract, so
 * hashing the raw JSON.stringify result would make an otherwise identical
 * archive fail verification after crossing the frontend/Python boundary.
 */
function canonicalJson(value: unknown): string {
  const normalize = (current: unknown): unknown => {
    if (Array.isArray(current)) return current.map(normalize)
    if (current && typeof current === 'object') {
      const object = current as Record<string, unknown>
      return Object.fromEntries(
        Object.keys(object)
          .sort()
          .map((key) => [key, normalize(object[key])]),
      )
    }
    return current
  }

  const serialized = JSON.stringify(normalize(value), null, 2)
  if (serialized === undefined) throw new Error(translate('settings.archive.serializationFailed'))
  return serialized
}

// 检测是否在 Tauri 环境
// 检测是否在移动端（Android/iOS）
// 获取下载路径设置
function getDownloadPath(): string | null {
  const stored = localStorage.getItem('efflife_download_path')
  if (!stored) return null
  // Versions before 1215 stored a directory plus the archive filename prefix.
  // Strip that legacy suffix while preserving the platform separator/root.
  return stored.replace(/([\\/])efflife_archive_$/, '$1')
}

function archiveDefaultPath(fileName: string): string {
  const directory = getDownloadPath()
  if (!directory) return fileName
  const separator = directory.includes('\\') ? '\\' : '/'
  return `${directory.replace(/[\\/]+$/, '')}${separator}${fileName}`
}

// 设置下载路径
export function setDownloadPath(path: string): void {
  localStorage.setItem('efflife_download_path', path.replace(/([\\/])efflife_archive_$/, '$1'))
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
  DAILY_TRIGGER: 'efflife_daily_triggers',

  // 打卡系统
  CHECKIN: 'efflife_checkin_data',

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
  motionSettings?: Record<string, unknown> | null
  locale?: string
  records?: Record<string, unknown[]>
  todos: UnifiedTodo[]
  categories: TodoCategory[]
  todoSettings: TodoSettings
  importRepairs?: {
    todoRecordLinks: number
    todoPlanTaskLinks: number
  }
  planHelper?: PlanHelperData
  archiveIntegrity?: 'verified' | 'legacy'
}

type PlanHelperData = {
  available: boolean
  source?: 'live' | 'cache' | 'snapshot'
  plans: unknown[]
  archives?: unknown[]
  unavailableReason?: string
  stale?: boolean
}

export interface ArchivePreview {
  exportDate: string
  planCount: number
  archivedPlanCount: number
  todoCount: number
  recordCount: number
  categoryCount: number
  localPlanCount: number
  localArchivedPlanCount: number
  localTodoCount: number
  localRecordCount: number
  localCategoryCount: number
  repairedLinkCount: number
  repairedTodoRecordLinks: number
  repairedTodoPlanTaskLinks: number
  planStatus: 'available' | 'cache' | 'snapshot' | 'stale' | 'unavailable'
  integrity: 'verified' | 'legacy'
}

type ArchiveContentPreview = Omit<ArchivePreview,
  'localPlanCount' | 'localArchivedPlanCount' | 'localTodoCount' | 'localRecordCount' | 'localCategoryCount'
>

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}

function normalizeImportedPlanHelper(raw: unknown): PlanHelperData {
  if (!isObjectRecord(raw)) return { available: false, plans: [] }
  const plans = Array.isArray(raw.plans) ? raw.plans : []
  const archives = Array.isArray(raw.archives) ? raw.archives : []
  const source = raw.source === 'live' || raw.source === 'cache' || raw.source === 'snapshot'
    ? raw.source
    : undefined
  return {
    // Older archive.json files carried plans without the newer availability
    // flag. Treat that shape as available unless it explicitly says false.
    available: raw.available !== false && Array.isArray(raw.plans),
    source,
    plans,
    archives,
    unavailableReason: typeof raw.unavailableReason === 'string' ? raw.unavailableReason : undefined,
    stale: raw.stale === true,
  }
}

function summarizeArchive(data: ArchiveData): ArchiveContentPreview {
  const planStatus = !data.planHelper?.available
    ? 'unavailable'
    : data.planHelper.source === 'snapshot'
      ? 'snapshot'
      : data.planHelper.stale || data.planHelper.source === 'cache'
        ? 'stale'
        : 'available'
  return {
    exportDate: data.exportDate,
    planCount: Array.isArray(data.planHelper?.plans) ? data.planHelper.plans.length : 0,
    archivedPlanCount: Array.isArray(data.planHelper?.archives) ? data.planHelper.archives.length : 0,
    todoCount: data.todos.length,
    recordCount: Object.values(data.records || {}).reduce((total, records) => total + records.length, 0),
    categoryCount: data.categories.length,
    repairedTodoRecordLinks: data.importRepairs?.todoRecordLinks || 0,
    repairedTodoPlanTaskLinks: data.importRepairs?.todoPlanTaskLinks || 0,
    repairedLinkCount: (data.importRepairs?.todoRecordLinks || 0) + (data.importRepairs?.todoPlanTaskLinks || 0),
    planStatus,
    integrity: data.archiveIntegrity || 'legacy',
  }
}

async function addLocalArchiveScope(preview: ArchiveContentPreview): Promise<ArchivePreview> {
  const localStats = await getDataStats()
  return {
    ...preview,
    localPlanCount: localStats.eventPlanCount,
    localArchivedPlanCount: localStats.archivedEventPlanCount,
    localTodoCount: localStats.todoCount,
    localRecordCount: localStats.totalRecords,
    localCategoryCount: localStats.todoCategoryCount,
  }
}

// 获取所有日期记录
function getLocalStorageRecords(): Record<string, unknown[]> {
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

// IndexedDB is the primary archive source; localStorage remains a compatibility fallback.
async function getAllRecords(): Promise<Record<string, unknown[]>> {
  const legacyRecords = getLocalStorageRecords()
  try {
    const { getRawAll, STORE_NAMES } = await import('@/storage')
    const entries = await getRawAll<{ key?: string; value?: unknown }>(STORE_NAMES.RECORDS)
    const indexedDBRecords: Record<string, unknown[]> = {}
    for (const entry of entries) {
      if (typeof entry.key === 'string' && Array.isArray(entry.value)) {
        indexedDBRecords[entry.key] = entry.value
      }
    }
    // A successful IndexedDB read is authoritative even when the store is
    // empty. Do not resurrect stale localStorage dates into a valid empty
    // primary dataset; fall back only when the primary read itself fails.
    return indexedDBRecords
  } catch {
    // IndexedDB unavailable: use the legacy localStorage snapshot.
  }
  return legacyRecords
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
  try {
    localStorage.setItem(key, JSON.stringify(data))
  } catch (error) {
    // The archive's canonical target is IndexedDB. A restricted legacy
    // mirror must not turn an otherwise valid import into a rollback.
    console.warn(`Failed to update archive compatibility mirror for ${key}:`, error)
  }
}

// Core data is written to IndexedDB first by DataService. Keep localStorage
// only as a compatibility fallback so an archive reflects the same state that
// the unified workspace loads at runtime.
async function readCoreJSON<T>(localKey: string, storeName: string, storeKey: string): Promise<T | null> {
  try {
    const { get } = await import('@/storage')
    const stored = await get<T>(storeName, storeKey)
    if (stored !== null && stored !== undefined) return stored
  } catch {
    // Fall back to the legacy mirror when IndexedDB is unavailable.
  }
  return readJSON<T>(localKey)
}

async function requestPlanHelper(path: string, options: RequestInit = {}): Promise<Response> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), PLAN_HELPER_REQUEST_TIMEOUT_MS)
  try {
    return await fetch(`${PLAN_HELPER_ORIGIN}${path}`, {
      ...options,
      signal: controller.signal,
    })
  } finally {
    window.clearTimeout(timeout)
  }
}

async function readCachedPlanHelperData(): Promise<{ plans: unknown[] | null; archives: unknown[] | null }> {
  try {
    const { get, STORE_NAMES } = await import('@/storage')
    const plans = await get<unknown[]>(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'plans')
    const archives = await get<unknown[]>(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'archives')
    return {
      plans: Array.isArray(plans) ? plans : null,
      archives: Array.isArray(archives) ? archives : null,
    }
  } catch {
    return { plans: null, archives: null }
  }
}

async function collectPlanHelperData(): Promise<PlanHelperData> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    try {
      const { get, STORE_NAMES } = await import('@/storage')
      const plans = await get<unknown[]>(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'plans')
      const archives = await get<unknown[]>(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'archives')
      if (Array.isArray(plans)) return { available: true, source: 'snapshot', plans, archives: Array.isArray(archives) ? archives : [] }
    } catch {
      // Fall through to the explicit unavailable result.
    }
    return { available: false, plans: [], unavailableReason: translate('settings.archive.mobilePlanSnapshotMissing') }
  }
  try {
    await syncPendingPlanHelperReset()
    const response = await requestPlanHelper('/api/data/export', {
      headers: { Accept: 'application/json' },
    })
    if (!response.ok) throw new Error(translate('settings.archive.planServiceResponse', { status: response.status }))
    const payload = await response.json() as {
      success?: boolean
      data?: { plans?: unknown[]; archives?: unknown[] }
    }
    if (!payload.success || !Array.isArray(payload.data?.plans)) throw new Error(translate('settings.archive.planExportInvalid'))
    try {
      const { set, STORE_NAMES } = await import('@/storage')
      await set(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'plans', payload.data.plans)
      await set(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'archives', Array.isArray(payload.data.archives) ? payload.data.archives : [])
    } catch {
      // The HTTP export remains valid even if the optional cache is unavailable.
    }
    return { available: true, source: 'live', plans: payload.data.plans, archives: Array.isArray(payload.data.archives) ? payload.data.archives : [] }
  } catch {
    return { available: false, plans: [], unavailableReason: translate('settings.archive.planServiceUnavailable') }
  }
}

// 收集所有数据
async function collectPlanHelperDataWithCache(): Promise<PlanHelperData> {
  const live = await collectPlanHelperData()
  if (live.available || getPlanRuntime() === 'mobile-unavailable') return live
  const cached = await readCachedPlanHelperData()
  if (!cached.plans) return live
  return {
    available: true,
    source: 'cache',
    plans: cached.plans,
    archives: cached.archives || [],
    stale: true,
    unavailableReason: live.unavailableReason || translate('settings.archive.usingCachedPlanSnapshot'),
  }
}

async function collectAllData(): Promise<ArchiveData> {
  const { getRawAll, STORE_NAMES } = await import('@/storage')
  const todos = await getRawAll<UnifiedTodo>(STORE_NAMES.TODOS)
  return {
    version: ARCHIVE_VERSION,
    exportDate: new Date().toISOString(),
    config: normalizeConfig(await readCoreJSON<Partial<Config>>(STORAGE_KEYS.CONFIG, STORE_NAMES.CONFIG, 'config') || {}) as unknown as Record<string, unknown>,
    plans: await readCoreJSON(STORAGE_KEYS.PLANS, STORE_NAMES.PLANS, 'plans'),
    scheduleRules: await readCoreJSON(STORAGE_KEYS.SCHEDULE_RULES, STORE_NAMES.SCHEDULE_RULES, 'rules'),
    manualPlans: await readCoreJSON(STORAGE_KEYS.MANUAL_PLANS, STORE_NAMES.MANUAL_PLANS, 'all'),
    audioSettings: await readCoreJSON(STORAGE_KEYS.AUDIO_SETTINGS, STORE_NAMES.AUDIO_SETTINGS, 'settings'),
    eventSettings: await readCoreJSON(STORAGE_KEYS.EVENT_SETTINGS, STORE_NAMES.EVENT_SETTINGS, 'settings'),
    eventInbox: await readCoreJSON(STORAGE_KEYS.EVENT_INBOX, STORE_NAMES.EVENT_INBOX, 'inbox'),
    warningInbox: await readCoreJSON(STORAGE_KEYS.WARNING_INBOX, STORE_NAMES.WARNING_INBOX, 'inbox'),
    dailyTrigger: await readCoreJSON(STORAGE_KEYS.DAILY_TRIGGER, STORE_NAMES.DAILY_TRIGGER, 'trigger'),
    checkin: await readCoreJSON(STORAGE_KEYS.CHECKIN, STORE_NAMES.CHECKIN, 'data'),
    motionSettings: readJSON<Record<string, unknown>>(MOTION_SETTINGS_STORAGE_KEY),
    locale: localStorage.getItem('effilife_locale') || 'zh-CN',
    records: await getAllRecords(),
    todos,
    categories: await TodoCategoryService.ensureDefaults(todos),
    todoSettings: await TodoSettingsService.get(),
    planHelper: await collectPlanHelperDataWithCache(),
  }
}

function planExportWarning(planHelper: PlanHelperData): string | undefined {
  if (planHelper.source === 'snapshot') return translate('settings.archive.planSnapshotLocalExportWarning')
  if (planHelper.stale || planHelper.source === 'cache') {
    return planHelper.unavailableReason || translate('settings.archive.usingCachedPlanSnapshot')
  }
  if (!planHelper.available) return translate('settings.archive.planSnapshotUnavailable')
  return undefined
}

// 导出数据为 .efl 文件
export async function exportArchive(): Promise<{ success: boolean; path?: string; warning?: string }> {
  const data = await collectAllData()
  const zip = new JSZip()

  // 使用公共层约定的 manifest + datasets 协议导出。
  const { records, todos, categories, planHelper = { available: false, plans: [] }, ...app } = data
  const datasets = [...CANONICAL_ARCHIVE_DATASETS]
  const datasetPayloads = {
    app: canonicalJson(app),
    records: canonicalJson(records),
    todos: canonicalJson(todos),
    todo_categories: canonicalJson(categories),
    plan_helper: canonicalJson(planHelper),
  }
  const datasetSha256: Record<string, string> = {}
  for (const name of datasets) {
    datasetSha256[name] = await sha256Hex(new TextEncoder().encode(datasetPayloads[name as keyof typeof datasetPayloads]))
  }
  zip.file('manifest.json', JSON.stringify({
    format: ARCHIVE_FORMAT,
    format_version: ARCHIVE_FORMAT_VERSION,
    created_at: data.exportDate,
    datasets,
    dataset_sha256: datasetSha256,
    metadata: { source: 'time-helper', archive_version: ARCHIVE_VERSION },
  }, null, 2))
  for (const name of datasets) {
    zip.file(`data/${name}.json`, datasetPayloads[name as keyof typeof datasetPayloads])
  }

  // 添加与当前界面语言一致的说明文件；协议字段和数据集名称保持不变。
  zip.file('README.txt', [
    translate('settings.archive.readme.title'),
    `${translate('settings.archive.readme.protocol')}: ${ARCHIVE_FORMAT} ${ARCHIVE_FORMAT_VERSION}`,
    `${translate('settings.archive.readme.version')}: ${ARCHIVE_VERSION}`,
    `${translate('settings.archive.readme.exportedAt')}: ${new Date(data.exportDate).toLocaleString(currentLocale.value)}`,
    '',
    `${translate('settings.archive.readme.includes')}:`,
    `- ${translate('settings.archive.readme.appData')}`,
    `- ${translate('settings.archive.readme.planHelper')}`,
    `- ${translate('settings.archive.readme.audioEvents')}`,
    `- ${translate('settings.archive.readme.checkin')}`,
    `- ${translate('settings.archive.readme.records')}`,
    '',
    translate('settings.archive.readme.importMethod'),
    '',
  ].join('\n'))

  // 生成 zip blob
  const blob = await zip.generateAsync({ type: 'blob' })

  // 生成文件名
  const dateStr = getTodayDate()
  const fileName = `efflife_archive_${dateStr}.efl`

  // 如果在 Tauri 桌面环境，使用原生对话框
  if (isTauriRuntime() && !isMobilePlatform()) {
    try {
      const { save } = await import('@tauri-apps/plugin-dialog')
      const { writeFile } = await import('@tauri-apps/plugin-fs')

      const filePath = await save({
        title: translate('settings.archive.exportDialogTitle'),
        defaultPath: archiveDefaultPath(fileName),
        filters: [{ name: translate('settings.archive.fileType'), extensions: ['efl'] }]
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
        setDownloadPath(dir)
      }

      return {
        success: true,
        path: filePath,
        warning: planExportWarning(planHelper),
      }
    } catch (e) {
      // Tauri API 失败，回退到浏览器下载
      console.warn('Tauri export failed, falling back to browser:', e)
    }
  }

  // Mobile WebViews do not consistently expose downloaded files. Prefer the
  // system share sheet when it supports sharing the archive as a file.
  if (isMobilePlatform() && typeof navigator !== 'undefined' && typeof navigator.share === 'function') {
    const archiveFile = new File([blob], fileName, { type: 'application/octet-stream' })
    let canShare = typeof navigator.canShare !== 'function'
    if (typeof navigator.canShare === 'function') {
      try {
        canShare = navigator.canShare({ files: [archiveFile] })
      } catch {
        canShare = false
      }
    }
    if (canShare) {
      try {
        await navigator.share({ title: translate('settings.archive.shareTitle'), files: [archiveFile] })
        return {
          success: true,
          warning: planExportWarning(planHelper),
        }
      } catch (error) {
        // A deliberate user cancellation must not trigger a second download.
        if (error instanceof DOMException && error.name === 'AbortError') return { success: false }
        console.warn('Mobile archive sharing failed; falling back to download:', error)
      }
    }
  }

  // Mobile Tauri or browser environments fall back to a normal download.
  saveAs(blob, fileName)
  return {
    success: true,
    warning: planExportWarning(planHelper),
  }
}

// 从 .efl 文件导入数据
export async function importArchive(file: File): Promise<{ success: boolean; message: string }> {
  try {
    // 检查文件扩展名
    if (!file.name.toLocaleLowerCase().endsWith('.efl')) {
      return { success: false, message: translate('settings.archive.invalidFile') }
    }

    assertArchiveBlobSize(file)
    // 读取 zip 文件
    const zip = await JSZip.loadAsync(file)
    assertArchiveEntryCount(zip)

    return await processArchiveData(zip)
  } catch (e) {
    return { success: false, message: translate('settings.archive.importFailed', { detail: (e as Error).message }) }
  }
}

// 在 Tauri 桌面环境下打开文件对话框导入
export async function importArchiveWithDialog(confirmImport?: (preview: ArchivePreview) => boolean | Promise<boolean>): Promise<{ success: boolean; message: string; cancelled?: boolean }> {
  // 移动端使用文件选择器，不使用此函数
  if (!isTauriRuntime() || isMobilePlatform()) {
    return { success: false, message: translate('settings.archive.filePickerOnly') }
  }

  try {
    const { open } = await import('@tauri-apps/plugin-dialog')
    const { readFile } = await import('@tauri-apps/plugin-fs')

    const filePath = await open({
      title: translate('settings.archive.importDialogTitle'),
      filters: [{ name: translate('settings.archive.fileType'), extensions: ['efl'] }],
      multiple: false,
      directory: false
    })

    if (!filePath) {
      return { success: false, message: '', cancelled: true }
    }

    // 读取文件
    const data = await readFile(filePath as string)
    const blob = new Blob([data])
    assertArchiveBlobSize(blob)
    const zip = await JSZip.loadAsync(blob)
    assertArchiveEntryCount(zip)
    const preview = await addLocalArchiveScope(summarizeArchive(await parseArchiveData(zip)))

    if (confirmImport && !(await confirmImport(preview))) {
      return { success: false, message: '', cancelled: true }
    }

    return await processArchiveData(zip)
  } catch (e) {
    return { success: false, message: translate('settings.archive.importFailed', { detail: (e as Error).message }) }
  }
}

async function parseArchiveData(zip: JSZip): Promise<ArchiveData> {
  assertArchiveEntryCount(zip)
  const manifestFile = zip.file('manifest.json')
  if (manifestFile) {
    let manifest: { format?: string; format_version?: string; created_at?: string; datasets?: string[]; dataset_sha256?: Record<string, string> }
    try {
      manifest = JSON.parse(await manifestFile.async('text'))
    } catch {
      throw new Error(translate('settings.archive.manifestInvalid'))
    }
    const hasChecksums = !!manifest.dataset_sha256 && manifest.datasets?.every((name) => /^[0-9a-f]{64}$/.test(manifest.dataset_sha256?.[name] || ''))
    if (manifest.format !== ARCHIVE_FORMAT || manifest.format_version !== ARCHIVE_FORMAT_VERSION || !Array.isArray(manifest.datasets) || (manifest.dataset_sha256 && !hasChecksums)) {
      throw new Error(translate('settings.archive.unsupportedFormat'))
    }
    if (manifest.datasets.length > MAX_ARCHIVE_DATASET_COUNT) {
      throw new Error(translate('settings.archive.tooManyDatasets'))
    }
    const declaredDatasets = new Set(manifest.datasets)
    const missingDatasets = CANONICAL_ARCHIVE_DATASETS.filter((name) => {
      if (name === 'todo_categories') return false
      if (name === 'records') return !declaredDatasets.has('records') && !declaredDatasets.has('time_records')
      if (name === 'plan_helper') return !declaredDatasets.has('plan_helper') && !declaredDatasets.has('plans')
      return !declaredDatasets.has(name)
    })
    if (missingDatasets.length > 0) {
      throw new Error(translate('settings.archive.missingDatasets', { names: missingDatasets.join(', ') }))
    }

    const datasets: Record<string, unknown> = {}
    let totalDatasetBytes = 0
    const datasetNames = new Set<string>()
    for (const name of manifest.datasets) {
      if (!/^[A-Za-z0-9_-]+$/.test(name)) throw new Error(translate('settings.archive.invalidDatasetName', { name }))
      if (datasetNames.has(name)) throw new Error(translate('settings.archive.duplicateDataset', { name }))
      datasetNames.add(name)
      const checksumError = translate('settings.archive.datasetChecksumMismatch', { name })
      const file = zip.file(`data/${name}.json`)
      if (!file) throw new Error(translate('settings.archive.datasetMissing', { name }))
      const sizeError = translate('settings.archive.datasetTooLarge', { name })
      try {
        const raw = await file.async('uint8array')
        if (raw.byteLength > MAX_ARCHIVE_DATASET_BYTES) throw new Error(sizeError)
        totalDatasetBytes += raw.byteLength
        if (totalDatasetBytes > MAX_ARCHIVE_TOTAL_DATASET_BYTES) throw new Error(translate('settings.archive.totalDatasetTooLarge'))
        const expected = manifest.dataset_sha256?.[name]
        if (expected && await sha256Hex(raw) !== expected) {
          throw new Error(checksumError)
        }
        datasets[name] = JSON.parse(new TextDecoder().decode(raw))
      } catch (error) {
        if (error instanceof Error && error.message === checksumError) throw error
        if (error instanceof Error && (error.message === sizeError || error.message === translate('settings.archive.totalDatasetTooLarge'))) throw error
          throw new Error(translate('settings.archive.datasetInvalid', { name }))
      }
    }

    if (!isObjectRecord(datasets.app)) throw new Error(translate('settings.archive.datasetInvalid', { name: 'app' }))
    if (!Array.isArray(datasets.todos)) throw new Error(translate('settings.archive.datasetInvalid', { name: 'todos' }))
    if (!('todo_categories' in datasets)) datasets.todo_categories = []
    datasets.records = datasets.records ?? datasets.time_records
    datasets.plan_helper = datasets.plan_helper || datasets.planHelper || {
      available: Array.isArray(datasets.plans),
      plans: Array.isArray(datasets.plans) ? datasets.plans : [],
    }
    if (!Array.isArray(datasets.todo_categories)) throw new Error(translate('settings.archive.datasetInvalid', { name: 'todo_categories' }))
    if (!isObjectRecord(datasets.records)) throw new Error(translate('settings.archive.datasetInvalid', { name: 'records' }))
    for (const records of Object.values(datasets.records)) {
      if (!Array.isArray(records)) throw new Error(translate('settings.archive.datasetInvalid', { name: 'records' }))
    }
    if (!isObjectRecord(datasets.plan_helper)) throw new Error(translate('settings.archive.datasetInvalid', { name: 'plan_helper' }))
    if ('plans' in datasets.plan_helper && !Array.isArray(datasets.plan_helper.plans)) {
      throw new Error(translate('settings.archive.datasetInvalid', { name: 'plan_helper' }))
    }
    if ('archives' in datasets.plan_helper && !Array.isArray(datasets.plan_helper.archives)) {
      throw new Error(translate('settings.archive.datasetInvalid', { name: 'plan_helper' }))
    }

    const app = (datasets.app && typeof datasets.app === 'object') ? datasets.app as Partial<ArchiveData> : {}
    const rawPlanHelper = datasets.plan_helper || datasets.planHelper || {
      available: Array.isArray(datasets.plans),
      plans: Array.isArray(datasets.plans) ? datasets.plans : [],
    }
    const planHelper = normalizeImportedPlanHelper(rawPlanHelper)
    const importedTodos = Array.isArray(datasets.todos)
      ? datasets.todos.map(normalizeImportedTodo)
      : []
    if (importedTodos.some((todo) => todo === null)) {
      throw new Error(translate('settings.archive.todoInvalid'))
    }

    const records = normalizeImportedRecords(datasets.records)
    const repairedRecordLinks = repairImportedTodoRecordLinks(importedTodos as UnifiedTodo[], records)
    const repairedPlanLinks = repairImportedTodoPlanLinks(repairedRecordLinks.todos, planHelper)
    const categories = normalizeImportedCategories(datasets.todo_categories, repairedPlanLinks.todos)
    return {
      version: String(app.version || manifest.format_version || '1.0.0'),
      exportDate: String(app.exportDate || manifest.created_at || new Date().toISOString()),
      config: app.config ? normalizeConfig(app.config as Partial<Config>) as unknown as Record<string, unknown> : null,
      plans: app.plans || null,
      scheduleRules: app.scheduleRules || null,
      manualPlans: app.manualPlans || null,
      audioSettings: app.audioSettings || null,
      eventSettings: app.eventSettings || null,
      eventInbox: app.eventInbox || null,
      warningInbox: app.warningInbox || null,
      dailyTrigger: app.dailyTrigger || null,
      checkin: app.checkin || null,
      motionSettings: app.motionSettings,
      locale: typeof app.locale === 'string' ? app.locale : 'zh-CN',
      records: repairedRecordLinks.records,
      todos: repairedPlanLinks.todos,
      categories,
      todoSettings: app.todoSettings || await TodoSettingsService.get(),
      importRepairs: { todoRecordLinks: repairedRecordLinks.repaired, todoPlanTaskLinks: repairedPlanLinks.repaired },
      planHelper: (planHelper && typeof planHelper === 'object' ? planHelper : { available: false, plans: [] }) as ArchiveData['planHelper'],
      archiveIntegrity: hasChecksums ? 'verified' : 'legacy',
    }
  }

  // 兼容 2.0 及更早的单文件 archive.json 存档。
  const archiveFile = zip.file('archive.json')
  if (!archiveFile) throw new Error(translate('settings.archive.archiveInvalid'))
  let legacy: ArchiveData
  try {
    const raw = await archiveFile.async('uint8array')
    if (raw.byteLength > MAX_ARCHIVE_DATASET_BYTES) throw new Error(translate('settings.archive.datasetTooLarge', { name: 'archive' }))
    legacy = JSON.parse(new TextDecoder().decode(raw)) as ArchiveData
  } catch {
    throw new Error(translate('settings.archive.legacyArchiveInvalid'))
  }
  if (!legacy.version) throw new Error(translate('settings.archive.versionMissing'))
  const importedTodos = Array.isArray(legacy.todos)
    ? legacy.todos.map(normalizeImportedTodo)
    : []
  if (importedTodos.some((todo) => todo === null)) {
    throw new Error(translate('settings.archive.legacyTodoInvalid'))
  }
  const legacyRecords = legacy.records === undefined ? undefined : normalizeImportedRecords(legacy.records)
  const repairedRecordLinks = repairImportedTodoRecordLinks(importedTodos as UnifiedTodo[], legacyRecords || {})
  if (legacyRecords !== undefined) {
    for (const date of Object.keys(legacyRecords)) delete legacyRecords[date]
    Object.assign(legacyRecords, repairedRecordLinks.records)
  }
  const normalizedLegacyPlanHelper = legacy.planHelper === undefined
    ? undefined
    : normalizeImportedPlanHelper(legacy.planHelper)
  const repairedPlanLinks = repairImportedTodoPlanLinks(repairedRecordLinks.todos, normalizedLegacyPlanHelper)
  const categories = normalizeImportedCategories(undefined, repairedPlanLinks.todos)
  return {
    ...legacy,
    config: legacy.config ? normalizeConfig(legacy.config as Partial<Config>) as unknown as Record<string, unknown> : null,
    archiveIntegrity: 'legacy',
    records: legacyRecords,
    locale: legacy.locale || 'zh-CN',
    todos: repairedPlanLinks.todos,
    categories,
    todoSettings: legacy.todoSettings || await TodoSettingsService.get(),
    importRepairs: { todoRecordLinks: repairedRecordLinks.repaired, todoPlanTaskLinks: repairedPlanLinks.repaired },
    planHelper: normalizedLegacyPlanHelper,
  }
}

export async function previewArchive(file: Blob): Promise<ArchivePreview> {
  assertArchiveBlobSize(file)
  const zip = await JSZip.loadAsync(file)
  assertArchiveEntryCount(zip)
  return await addLocalArchiveScope(summarizeArchive(await parseArchiveData(zip)))
}

// 处理存档数据（内部函数）
function normalizeImportedCategories(raw: unknown, todos: UnifiedTodo[]): TodoCategory[] {
  const categories = raw === undefined
    ? [...DEFAULT_TODO_CATEGORIES]
    : Array.isArray(raw)
      ? raw.map(normalizeImportedCategory)
      : null
  if (!categories || categories.some((category) => category === null)) {
    throw new Error(translate('settings.archive.categoriesInvalid'))
  }

  const result = categories as TodoCategory[]
  const ids = new Set<string>()
  for (const category of result) {
    if (ids.has(category.id)) throw new Error(translate('settings.archive.duplicateCategory', { id: category.id }))
    ids.add(category.id)
  }
  for (const category of DEFAULT_TODO_CATEGORIES) {
    if (!ids.has(category.id)) {
      result.push(category)
      ids.add(category.id)
    }
  }
  for (const todo of todos) {
    if (todo.category && !ids.has(todo.category)) {
      result.push({
        id: todo.category,
        name: todo.category,
        color: '#64748b',
        icon: 'circle',
        created_at: new Date().toISOString(),
        difficulty: 5,
      })
      ids.add(todo.category)
    }
  }
  return result
}

function normalizeImportedRecords(raw: unknown): Record<string, unknown[]> {
  if (raw === undefined || raw === null) return {}
  if (typeof raw !== 'object' || Array.isArray(raw)) {
    throw new Error(translate('settings.archive.recordsInvalid'))
  }
  const result: Record<string, unknown[]> = {}
  for (const [date, records] of Object.entries(raw as Record<string, unknown>)) {
    if (!Array.isArray(records)) {
      throw new Error(translate('settings.archive.recordsDateInvalid', { date }))
    }
    result[date] = records
  }
  return result
}

function repairImportedTodoRecordLinks(todos: UnifiedTodo[], records: Record<string, unknown[]>): { todos: UnifiedTodo[]; records: Record<string, unknown[]>; repaired: number } {
  const todoIds = new Set(todos.map((todo) => todo.id))
  const recordIds = new Set<string>()
  const recordTodoIds = new Map<string, string>()
  const todoRecordIds = new Map<string, string>()
  for (const todo of todos) {
    for (const recordId of todo.related_time_record_ids || []) {
      if (typeof recordId === 'string' && recordId && !todoRecordIds.has(recordId)) {
        todoRecordIds.set(recordId, todo.id)
      }
    }
  }
  let repaired = 0
  const repairedRecords: Record<string, unknown[]> = {}
  for (const [date, dayRecords] of Object.entries(records)) {
    const nextDayRecords = dayRecords.map((record) => {
      if (!record || typeof record !== 'object') return record
      const candidate = record as { id?: unknown; todo_id?: unknown }
      if (typeof candidate.id !== 'string' || !candidate.id) return record
      recordIds.add(candidate.id)
      const explicitTodoId = typeof candidate.todo_id === 'string' && candidate.todo_id ? candidate.todo_id : undefined
      const resolvedTodoId = explicitTodoId && todoIds.has(explicitTodoId)
        ? explicitTodoId
        : todoRecordIds.get(candidate.id)
      const hasInvalidExplicitLink = explicitTodoId !== undefined && !todoIds.has(explicitTodoId)
      if (resolvedTodoId) {
        recordTodoIds.set(candidate.id, resolvedTodoId)
        if (candidate.todo_id !== resolvedTodoId) {
          repaired += 1
          return { ...candidate, todo_id: resolvedTodoId }
        }
        return record
      }
      if (hasInvalidExplicitLink || candidate.todo_id !== undefined) {
        repaired += 1
        const nextRecord = { ...candidate }
        delete nextRecord.todo_id
        return nextRecord
      }
      return record
    })
    repairedRecords[date] = nextDayRecords
  }
  const repairedTodos = todos.map((todo) => {
    const validIds = (todo.related_time_record_ids || []).filter((id) => recordIds.has(id))
    const reverseIds = [...recordTodoIds.entries()]
      .filter(([, todoId]) => todoId === todo.id)
      .map(([recordId]) => recordId)
    const mergedIds = [...new Set([...validIds, ...reverseIds])]
    if (mergedIds.length === (todo.related_time_record_ids || []).length
      && mergedIds.every((id, index) => id === todo.related_time_record_ids?.[index])) return todo
    repaired += Math.max(0, mergedIds.length - (todo.related_time_record_ids || []).length)
      + Math.max(0, (todo.related_time_record_ids || []).length - validIds.length)
    return { ...todo, related_time_record_ids: mergedIds.length ? mergedIds : undefined }
  })
  return { todos: repairedTodos, records: repairedRecords, repaired }
}

function planLetter(index: number): string {
  let value = index
  let result = ''
  do {
    result = String.fromCharCode(65 + (value % 26)) + result
    value = Math.floor(value / 26) - 1
  } while (value >= 0)
  return result
}

function repairImportedTodoPlanLinks(todos: UnifiedTodo[], rawPlanHelper: unknown): { todos: UnifiedTodo[]; repaired: number } {
  if (!rawPlanHelper || typeof rawPlanHelper !== 'object') return { todos, repaired: 0 }
  const snapshot = rawPlanHelper as { available?: unknown; plans?: unknown; archives?: unknown }
  if (snapshot.available !== true || !Array.isArray(snapshot.plans)) return { todos, repaired: 0 }

  const taskIdsByPlan = new Map<string, Set<string>>()
  const rawPlans = [
    ...snapshot.plans,
    ...(Array.isArray(snapshot.archives)
      ? snapshot.archives.map((entry) => entry && typeof entry === 'object' ? (entry as { payload?: { plan?: unknown } }).payload?.plan : undefined)
      : []),
  ]
  rawPlans.forEach((raw, planIndex) => {
    if (!raw || typeof raw !== 'object') return
    const plan = raw as { head?: { index?: unknown }; main?: unknown }
    const planId = String(plan.head?.index ?? planIndex)
    const taskIds = new Set<string>()
    const sections = Array.isArray(plan.main) ? plan.main : []
    sections.forEach((rawSection, sectionIndex) => {
      if (!rawSection || typeof rawSection !== 'object') return
      const section = rawSection as { plan?: unknown }
      const rawTasks = Array.isArray(section.plan) ? section.plan : []
      let displayIndex = 0
      rawTasks.forEach((rawTask, internalIndex) => {
        if (internalIndex === 0 || !rawTask || typeof rawTask !== 'object' || (rawTask as { is_active?: unknown }).is_active === false) return
        displayIndex += 1
        taskIds.add(`${planLetter(sectionIndex)}${internalIndex}`)
        taskIds.add(`${planLetter(sectionIndex)}${displayIndex}`)
      })
    })
    // A numeric PH id can legitimately reappear across an active plan and an
    // archived historical snapshot. Keep the union so importing an archive
    // never detaches a TD merely because the later snapshot has a different
    // task layout under the same id.
    const knownTaskIds = taskIdsByPlan.get(planId)
    taskIdsByPlan.set(planId, knownTaskIds ? new Set([...knownTaskIds, ...taskIds]) : taskIds)
  })

  let repaired = 0
  const repairedTodos = todos.map((todo) => {
    if (!todo.related_plan_id || !todo.related_plan_task_id) return todo
    const taskIds = taskIdsByPlan.get(String(todo.related_plan_id))
    if (taskIds?.has(String(todo.related_plan_task_id))) return todo
    repaired += 1
    return { ...todo, related_plan_id: undefined, related_plan_task_id: undefined }
  })
  return { todos: repairedTodos, repaired }
}

interface ArchiveRuntimeSnapshot {
  localStorage: Record<string, string>
  stores: Record<string, unknown[]>
}

async function captureArchiveRuntimeSnapshot(): Promise<ArchiveRuntimeSnapshot> {
  const { getRawAll, STORE_NAMES } = await import('@/storage')
  const localStorageSnapshot: Record<string, string> = {}
  try {
    for (let i = 0; i < localStorage.length; i += 1) {
      const key = localStorage.key(i)
      if (key) {
        localStorageSnapshot[key] = localStorage.getItem(key) || ''
      }
    }
  } catch (error) {
    // IndexedDB remains sufficient for the canonical rollback snapshot.
    console.warn('Failed to capture legacy localStorage snapshot:', error)
  }

  const stores: Record<string, unknown[]> = {}
  for (const storeName of Object.values(STORE_NAMES)) {
    stores[storeName] = await getRawAll<unknown>(storeName)
  }
  return { localStorage: localStorageSnapshot, stores }
}

async function restoreArchiveRuntimeSnapshot(snapshot: ArchiveRuntimeSnapshot): Promise<void> {
  const { clear: idbClear, putRaw, STORE_NAMES } = await import('@/storage')
  try {
    for (let i = localStorage.length - 1; i >= 0; i -= 1) {
      const key = localStorage.key(i)
      if (key && !key.startsWith('efflife_backup_') && !key.startsWith('efflife_emergency_backup_')) {
        localStorage.removeItem(key)
      }
    }
    for (const [key, value] of Object.entries(snapshot.localStorage)) {
      localStorage.setItem(key, value)
    }
  } catch (error) {
    // Do not hide or undo the canonical IndexedDB rollback when the legacy
    // storage area is unavailable or has become read-only.
    console.warn('Failed to restore legacy localStorage snapshot:', error)
  }

  for (const storeName of Object.values(STORE_NAMES)) {
    await idbClear(storeName)
    for (const entry of snapshot.stores[storeName] || []) {
      await putRaw(storeName, entry)
    }
  }
}

async function restoreOptionalJsonDataset(
  localKey: string,
  storeName: string,
  storeKey: string,
  value: unknown,
  idbSet: (storeName: string, key: string, value: unknown) => Promise<unknown>,
  idbClear: (storeName: string) => Promise<unknown>,
): Promise<void> {
  // Undefined means that a legacy archive did not carry this field. Keep the
  // existing value for backward compatibility; null is an explicit empty
  // dataset in the canonical archive and must remove stale target data.
  if (value === undefined) return
  if (value === null) {
    await idbClear(storeName)
    try {
      localStorage.removeItem(localKey)
    } catch (error) {
      console.warn(`Failed to clear archive compatibility mirror for ${localKey}:`, error)
    }
    return
  }
  await idbSet(storeName, storeKey, value)
  writeJSON(localKey, value)
}

async function processArchiveData(zip: JSZip): Promise<{ success: boolean; message: string }> {
    const data = await parseArchiveData(zip)
    const runtimeSnapshot = await captureArchiveRuntimeSnapshot()

    // Keep a persistent recovery point in addition to the in-process rollback.
    // This remains available after the import succeeds and the page reloads.
    try {
      const { createBackup } = await import('@/storage')
      await createBackup('archive_import', runtimeSnapshot)
    } catch (error) {
      console.warn('Failed to persist archive import checkpoint:', error)
    }

    // 导入存储模块
    const { set: idbSet, putRaw, STORE_NAMES, clear: idbClear } = await import('@/storage')

    try {
    // 恢复数据（同时写入 localStorage 和 IndexedDB）
    await restoreOptionalJsonDataset(STORAGE_KEYS.CONFIG, STORE_NAMES.CONFIG, 'config', data.config, idbSet, idbClear)
    await restoreOptionalJsonDataset(STORAGE_KEYS.PLANS, STORE_NAMES.PLANS, 'plans', data.plans, idbSet, idbClear)
    await restoreOptionalJsonDataset(STORAGE_KEYS.SCHEDULE_RULES, STORE_NAMES.SCHEDULE_RULES, 'rules', data.scheduleRules, idbSet, idbClear)
    await restoreOptionalJsonDataset(STORAGE_KEYS.MANUAL_PLANS, STORE_NAMES.MANUAL_PLANS, 'all', data.manualPlans, idbSet, idbClear)
    await restoreOptionalJsonDataset(STORAGE_KEYS.AUDIO_SETTINGS, STORE_NAMES.AUDIO_SETTINGS, 'settings', data.audioSettings, idbSet, idbClear)
    await restoreOptionalJsonDataset(STORAGE_KEYS.EVENT_SETTINGS, STORE_NAMES.EVENT_SETTINGS, 'settings', data.eventSettings, idbSet, idbClear)
    await restoreOptionalJsonDataset(STORAGE_KEYS.EVENT_INBOX, STORE_NAMES.EVENT_INBOX, 'inbox', data.eventInbox, idbSet, idbClear)
    await restoreOptionalJsonDataset(STORAGE_KEYS.WARNING_INBOX, STORE_NAMES.WARNING_INBOX, 'inbox', data.warningInbox, idbSet, idbClear)
    await restoreOptionalJsonDataset(STORAGE_KEYS.DAILY_TRIGGER, STORE_NAMES.DAILY_TRIGGER, 'trigger', data.dailyTrigger, idbSet, idbClear)
    await restoreOptionalJsonDataset(STORAGE_KEYS.CHECKIN, STORE_NAMES.CHECKIN, 'data', data.checkin, idbSet, idbClear)
    await TodoSettingsService.save(data.todoSettings)
    if (data.motionSettings === undefined) {
      // Older archives did not carry motion settings; preserve the current
      // device preference instead of silently resetting it.
    } else if (data.motionSettings === null) {
      localStorage.removeItem(MOTION_SETTINGS_STORAGE_KEY)
    } else {
      writeJSON(MOTION_SETTINGS_STORAGE_KEY, data.motionSettings)
    }
    if (data.locale === 'zh-CN' || data.locale === 'en-US') {
      setLocale(data.locale)
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
    if (Array.isArray(data.categories)) {
      await idbClear(STORE_NAMES.TODO_CATEGORIES)
      for (const category of data.categories) {
        await putRaw(STORE_NAMES.TODO_CATEGORIES, category)
      }
    }

    const warnings: string[] = []
    if (data.importRepairs?.todoRecordLinks) {
      warnings.push(translate('settings.archive.repairedTodoRecordLinks', { count: data.importRepairs.todoRecordLinks }))
    }
    if (data.importRepairs?.todoPlanTaskLinks) {
      warnings.push(translate('settings.archive.repairedTodoPlanTaskLinks', { count: data.importRepairs.todoPlanTaskLinks }))
    }
    const savePlanHelperSnapshot = async (): Promise<void> => {
      if (!data.planHelper?.available || !Array.isArray(data.planHelper.plans)) return
      await idbSet(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'plans', data.planHelper.plans)
      await idbSet(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'archives', Array.isArray(data.planHelper.archives) ? data.planHelper.archives : [])
    }
    if (data.planHelper === undefined) {
      // Legacy archives may not contain plan-helper data. Preserve the
      // current snapshot instead of treating an absent field as an empty one.
    } else if (getPlanRuntime() === 'mobile-unavailable') {
      if (data.planHelper?.available && Array.isArray(data.planHelper.plans)) {
        try {
          await savePlanHelperSnapshot()
        } catch (error) {
          warnings.push(translate('settings.archive.snapshotSaveFailed', { detail: error instanceof Error ? error.message : translate('settings.archive.localStorageUnavailable') }))
        }
      } else {
        // Mobile has no live PH service to reconstruct an unavailable
        // dataset. Preserve the existing snapshot rather than treating a
        // degraded archive as an explicit empty plan collection.
        warnings.push(translate('settings.archive.planNotRestored', { reason: data.planHelper?.unavailableReason || translate('settings.archive.planSnapshotMissing') }))
      }
    } else if (data.planHelper?.available && Array.isArray(data.planHelper.plans)) {
      try {
        const response = await requestPlanHelper('/api/data/import', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify({ plans: data.planHelper.plans, archives: Array.isArray(data.planHelper.archives) ? data.planHelper.archives : [], replace: true }),
        })
        const payload = await response.json() as { success?: boolean; error?: string }
        if (!response.ok || !payload.success) throw new Error(payload.error || translate('settings.archive.planRestoreResponse', { status: response.status }))
        try {
          await savePlanHelperSnapshot()
        } catch (error) {
          warnings.push(translate('settings.archive.snapshotSaveFailed', { detail: error instanceof Error ? error.message : translate('settings.archive.localStorageUnavailable') }))
        }
      } catch (error) {
        warnings.push(translate('settings.archive.planRestoreFailed', { detail: error instanceof Error ? error.message : translate('settings.archive.planServiceUnavailable') }))
      }
    } else {
      // An unavailable PH export is an incomplete snapshot, not an explicit
      // empty plan dataset. Preserve the target so importing a degraded
      // archive cannot erase plans merely because the service was offline.
      warnings.push(translate('settings.archive.planNotRestored', { reason: data.planHelper?.unavailableReason || translate('settings.archive.planServiceUnavailable') }))
    }

    notifyWorkspaceChanged('archive')
    return {
      success: true,
      message: warnings.length
        ? translate('settings.archive.importedWithWarnings', { warnings: warnings.join('；') })
        : translate('settings.archive.importSuccess'),
    }
    } catch (error) {
      try {
        await restoreArchiveRuntimeSnapshot(runtimeSnapshot)
      } catch (rollbackError) {
        throw new Error(translate('settings.archive.importRollbackFailed', {
          detail: `${error instanceof Error ? error.message : String(error)}; ${rollbackError instanceof Error ? rollbackError.message : String(rollbackError)}`,
        }))
      }
      throw new Error(translate('settings.archive.importRolledBack', { detail: error instanceof Error ? error.message : String(error) }))
    }
}

async function clearPlanHelperData(): Promise<void> {
  // The cache is part of the unified plan dataset. Clear it before contacting
  // the companion service so a stopped service cannot leave stale plans that
  // reappear through the export fallback later.
  try {
    const { set, STORE_NAMES } = await import('@/storage')
    await set(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'plans', [])
    await set(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'archives', [])
  } catch {
    // Continue with the service reset attempt when local storage is unavailable.
  }

  if (getPlanRuntime() === 'mobile-unavailable') {
    clearPlanHelperResetPending()
    return
  }
  markPlanHelperResetPending()
  try {
    await requestPlanHelper('/api/data/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plans: [], archives: [], replace: true }),
    })
    clearPlanHelperResetPending()
  } catch {
    // Keep the tombstone so the next normal request retries the server reset.
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
      await idbClear(STORE_NAMES.TODO_CATEGORIES)
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
  const changeSource = type === 'all'
    ? 'archive'
    : type === 'records'
      ? 'records'
      : type === 'plans'
        ? 'plans'
        : 'settings'
  notifyWorkspaceChanged(changeSource)
  window.location.reload()
}

// 获取数据统计
export async function getDataStats(): Promise<{
  recordDays: number
  totalRecords: number
  todoCount: number
  activeTodoCount: number
  linkedPlanTodoCount: number
  todoCategoryCount: number
  hasConfig: boolean
  hasPlans: boolean
  eventPlanCount: number
  archivedEventPlanCount: number
  eventPlanSource: 'live' | 'cache' | 'snapshot' | 'unavailable'
  hasAudioSettings: boolean
  hasEventSettings: boolean
  hasMotionSettings: boolean
  hasCheckin: boolean
}> {
  const records = await getAllRecords()
  let totalRecords = 0
  for (const dateRecords of Object.values(records)) {
    totalRecords += dateRecords.length
  }
  const { getRawAll, STORE_NAMES } = await import('@/storage')
  const eventPlanData = await collectPlanHelperDataWithCache()
  const todos = await getRawAll<UnifiedTodo>(STORE_NAMES.TODOS)
  const categories = await getRawAll<TodoCategory>(STORE_NAMES.TODO_CATEGORIES)

  return {
    recordDays: Object.keys(records).length,
    totalRecords,
    todoCount: todos.length,
    activeTodoCount: todos.filter((todo) => !['completed', 'archived', 'cancelled'].includes(todo.status)).length,
    linkedPlanTodoCount: todos.filter((todo) => Boolean(todo.related_plan_id && todo.related_plan_task_id)).length,
    todoCategoryCount: categories.length,
    hasConfig: !!(await readCoreJSON(STORAGE_KEYS.CONFIG, STORE_NAMES.CONFIG, 'config')),
    hasPlans: !!(await readCoreJSON(STORAGE_KEYS.PLANS, STORE_NAMES.PLANS, 'plans')),
    eventPlanCount: eventPlanData.plans.length,
    archivedEventPlanCount: eventPlanData.archives?.length || 0,
    eventPlanSource: !eventPlanData.available
      ? 'unavailable'
      : eventPlanData.stale
        ? 'cache'
        : getPlanRuntime() === 'mobile-unavailable' ? 'snapshot' : 'live',
    // All settings and check-in data now have IndexedDB primaries with
    // compatibility mirrors.
    hasAudioSettings: !!(await readCoreJSON(STORAGE_KEYS.AUDIO_SETTINGS, STORE_NAMES.AUDIO_SETTINGS, 'settings')),
    hasEventSettings: !!(await readCoreJSON(STORAGE_KEYS.EVENT_SETTINGS, STORE_NAMES.EVENT_SETTINGS, 'settings')),
    hasMotionSettings: !!readJSON(MOTION_SETTINGS_STORAGE_KEY),
    hasCheckin: !!(await readCoreJSON(STORAGE_KEYS.CHECKIN, STORE_NAMES.CHECKIN, 'data')),
  }
}
