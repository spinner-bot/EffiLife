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
import { currentLocale, translate } from '@/i18n'
import { getTodayDate } from '@/services/dataService'
import { notifyWorkspaceChanged } from './workspaceEvents'

// 存档版本
const ARCHIVE_VERSION = '2.1'
const ARCHIVE_FORMAT = 'effilife.bundle'
const ARCHIVE_FORMAT_VERSION = '1.0.0'
const CANONICAL_ARCHIVE_DATASETS = ['app', 'records', 'todos', 'todo_categories', 'plan_helper'] as const
const PLAN_HELPER_REQUEST_TIMEOUT_MS = 4000

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
  locale?: string
  records: Record<string, unknown[]>
  todos: UnifiedTodo[]
  categories: TodoCategory[]
  todoSettings: TodoSettings
  importRepairs?: {
    todoRecordLinks: number
    todoPlanTaskLinks: number
  }
  planHelper: {
    available: boolean
    plans: unknown[]
    unavailableReason?: string
    stale?: boolean
  }
  archiveIntegrity?: 'verified' | 'legacy'
}

export interface ArchivePreview {
  exportDate: string
  planCount: number
  todoCount: number
  recordCount: number
  categoryCount: number
  repairedLinkCount: number
  integrity: 'verified' | 'legacy'
}

function summarizeArchive(data: ArchiveData): ArchivePreview {
  return {
    exportDate: data.exportDate,
    planCount: Array.isArray(data.planHelper?.plans) ? data.planHelper.plans.length : 0,
    todoCount: data.todos.length,
    recordCount: Object.values(data.records).reduce((total, records) => total + records.length, 0),
    categoryCount: data.categories.length,
    repairedLinkCount: (data.importRepairs?.todoRecordLinks || 0) + (data.importRepairs?.todoPlanTaskLinks || 0),
    integrity: data.archiveIntegrity || 'legacy',
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
    // IndexedDB is authoritative once it has readable records. Do not merge
    // stale localStorage dates back into the primary dataset.
    if (Object.keys(indexedDBRecords).length > 0) return indexedDBRecords
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
  localStorage.setItem(key, JSON.stringify(data))
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

async function readCachedPlanHelperData(): Promise<unknown[] | null> {
  try {
    const { get, STORE_NAMES } = await import('@/storage')
    const plans = await get<unknown[]>(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'plans')
    return Array.isArray(plans) ? plans : null
  } catch {
    return null
  }
}

async function collectPlanHelperData(): Promise<ArchiveData['planHelper']> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    try {
      const { get, STORE_NAMES } = await import('@/storage')
      const plans = await get<unknown[]>(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'plans')
      if (Array.isArray(plans)) return { available: true, plans }
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
      data?: { plans?: unknown[] }
    }
    if (!payload.success || !Array.isArray(payload.data?.plans)) throw new Error(translate('settings.archive.planExportInvalid'))
    try {
      const { set, STORE_NAMES } = await import('@/storage')
      await set(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'plans', payload.data.plans)
    } catch {
      // The HTTP export remains valid even if the optional cache is unavailable.
    }
    return { available: true, plans: payload.data.plans }
  } catch {
    return { available: false, plans: [], unavailableReason: translate('settings.archive.planServiceUnavailable') }
  }
}

// 收集所有数据
async function collectPlanHelperDataWithCache(): Promise<ArchiveData['planHelper']> {
  const live = await collectPlanHelperData()
  if (live.available || getPlanRuntime() === 'mobile-unavailable') return live
  const cachedPlans = await readCachedPlanHelperData()
  if (!cachedPlans) return live
  return {
    available: true,
    plans: cachedPlans,
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
    config: await readCoreJSON(STORAGE_KEYS.CONFIG, STORE_NAMES.CONFIG, 'config'),
    plans: await readCoreJSON(STORAGE_KEYS.PLANS, STORE_NAMES.PLANS, 'plans'),
    scheduleRules: await readCoreJSON(STORAGE_KEYS.SCHEDULE_RULES, STORE_NAMES.SCHEDULE_RULES, 'rules'),
    manualPlans: await readCoreJSON(STORAGE_KEYS.MANUAL_PLANS, STORE_NAMES.MANUAL_PLANS, 'all'),
    audioSettings: await readCoreJSON(STORAGE_KEYS.AUDIO_SETTINGS, STORE_NAMES.AUDIO_SETTINGS, 'settings'),
    eventSettings: await readCoreJSON(STORAGE_KEYS.EVENT_SETTINGS, STORE_NAMES.EVENT_SETTINGS, 'settings'),
    eventInbox: await readCoreJSON(STORAGE_KEYS.EVENT_INBOX, STORE_NAMES.EVENT_INBOX, 'inbox'),
    warningInbox: await readCoreJSON(STORAGE_KEYS.WARNING_INBOX, STORE_NAMES.WARNING_INBOX, 'inbox'),
    dailyTrigger: await readCoreJSON(STORAGE_KEYS.DAILY_TRIGGER, STORE_NAMES.DAILY_TRIGGER, 'trigger'),
    checkin: await readCoreJSON(STORAGE_KEYS.CHECKIN, STORE_NAMES.CHECKIN, 'data'),
    locale: localStorage.getItem('effilife_locale') || 'zh-CN',
    records: await getAllRecords(),
    todos,
    categories: await TodoCategoryService.ensureDefaults(todos),
    todoSettings: await TodoSettingsService.get(),
    planHelper: await collectPlanHelperDataWithCache(),
  }
}

// 导出数据为 .efl 文件
export async function exportArchive(): Promise<{ success: boolean; path?: string; warning?: string }> {
  const data = await collectAllData()
  const zip = new JSZip()

  // 使用公共层约定的 manifest + datasets 协议导出。
  const { records, todos, categories, planHelper, ...app } = data
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

  // 添加说明文件
  zip.file('README.txt', `浪兮效率时钟存档文件
协议: ${ARCHIVE_FORMAT} ${ARCHIVE_FORMAT_VERSION}
版本: ${ARCHIVE_VERSION}
导出时间: ${new Date(data.exportDate).toLocaleString(currentLocale.value)}

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
  const dateStr = getTodayDate()
  const fileName = `efflife_archive_${dateStr}.efl`

  // 如果在 Tauri 桌面环境，使用原生对话框
  if (isTauriRuntime() && !isMobilePlatform()) {
    try {
      const { save } = await import('@tauri-apps/plugin-dialog')
      const { writeFile } = await import('@tauri-apps/plugin-fs')

      const filePath = await save({
        title: translate('settings.archive.exportDialogTitle'),
        defaultPath: getDownloadPath() || fileName,
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
        setDownloadPath(dir + '/' + fileName.replace(/_[\d-]+\.efl$/, '_'))
      }

      return {
        success: true,
        path: filePath,
        warning: data.planHelper.stale
          ? data.planHelper.unavailableReason
          : data.planHelper.available ? undefined : translate('settings.archive.planSnapshotUnavailable'),
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
          warning: data.planHelper.stale
            ? data.planHelper.unavailableReason
            : data.planHelper.available ? undefined : translate('settings.archive.planSnapshotUnavailable'),
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
    warning: data.planHelper.stale
      ? data.planHelper.unavailableReason
      : data.planHelper.available ? undefined : translate('settings.archive.planSnapshotUnavailable'),
  }
}

// 从 .efl 文件导入数据
export async function importArchive(file: File): Promise<{ success: boolean; message: string }> {
  try {
    // 检查文件扩展名
    if (!file.name.toLocaleLowerCase().endsWith('.efl')) {
      return { success: false, message: translate('settings.archive.invalidFile') }
    }

    // 读取 zip 文件
    const zip = await JSZip.loadAsync(file)

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
    const zip = await JSZip.loadAsync(blob)
    const preview = summarizeArchive(await parseArchiveData(zip))

    if (confirmImport && !(await confirmImport(preview))) {
      return { success: false, message: '', cancelled: true }
    }

    return await processArchiveData(zip)
  } catch (e) {
    return { success: false, message: translate('settings.archive.importFailed', { detail: (e as Error).message }) }
  }
}

async function parseArchiveData(zip: JSZip): Promise<ArchiveData> {
  const manifestFile = zip.file('manifest.json')
  if (manifestFile) {
    let manifest: { format?: string; format_version?: string; created_at?: string; datasets?: string[]; dataset_sha256?: Record<string, string> }
    try {
      manifest = JSON.parse(await manifestFile.async('text'))
    } catch {
      throw new Error(translate('settings.archive.manifestInvalid'))
    }
    const hasChecksums = !!manifest.dataset_sha256 && manifest.datasets?.every((name) => typeof manifest.dataset_sha256?.[name] === 'string')
    if (manifest.format !== ARCHIVE_FORMAT || manifest.format_version !== ARCHIVE_FORMAT_VERSION || !Array.isArray(manifest.datasets) || (manifest.dataset_sha256 && !hasChecksums)) {
      throw new Error(translate('settings.archive.unsupportedFormat'))
    }
    const missingDatasets = CANONICAL_ARCHIVE_DATASETS.filter((name) => !manifest.datasets?.includes(name))
    if (missingDatasets.length > 0) {
      throw new Error(translate('settings.archive.missingDatasets', { names: missingDatasets.join(', ') }))
    }

    const datasets: Record<string, unknown> = {}
    const datasetNames = new Set<string>()
    for (const name of manifest.datasets) {
      if (!/^[A-Za-z0-9_-]+$/.test(name)) throw new Error(translate('settings.archive.invalidDatasetName', { name }))
      if (datasetNames.has(name)) throw new Error(translate('settings.archive.duplicateDataset', { name }))
      datasetNames.add(name)
      const checksumError = translate('settings.archive.datasetChecksumMismatch', { name })
      const file = zip.file(`data/${name}.json`)
      if (!file) throw new Error(translate('settings.archive.datasetMissing', { name }))
      try {
        const raw = await file.async('uint8array')
        const expected = manifest.dataset_sha256?.[name]
        if (expected && await sha256Hex(raw) !== expected) {
          throw new Error(checksumError)
        }
        datasets[name] = JSON.parse(new TextDecoder().decode(raw))
      } catch (error) {
        if (error instanceof Error && error.message === checksumError) throw error
          throw new Error(translate('settings.archive.datasetInvalid', { name }))
      }
    }

    const app = (datasets.app && typeof datasets.app === 'object') ? datasets.app as Partial<ArchiveData> : {}
    const planHelper = datasets.plan_helper || datasets.planHelper || {
      available: Array.isArray(datasets.plans),
      plans: Array.isArray(datasets.plans) ? datasets.plans : [],
    }
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
      records,
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
    legacy = JSON.parse(await archiveFile.async('text')) as ArchiveData
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
  const records = normalizeImportedRecords(legacy.records)
  const repairedRecordLinks = repairImportedTodoRecordLinks(importedTodos as UnifiedTodo[], records)
  const repairedPlanLinks = repairImportedTodoPlanLinks(repairedRecordLinks.todos, legacy.planHelper)
  const categories = normalizeImportedCategories(undefined, repairedPlanLinks.todos)
  return {
    ...legacy,
    archiveIntegrity: 'legacy',
    records,
    locale: legacy.locale || 'zh-CN',
    todos: repairedPlanLinks.todos,
    categories,
    todoSettings: legacy.todoSettings || await TodoSettingsService.get(),
    importRepairs: { todoRecordLinks: repairedRecordLinks.repaired, todoPlanTaskLinks: repairedPlanLinks.repaired },
    planHelper: legacy.planHelper || { available: false, plans: [] },
  }
}

export async function previewArchive(file: Blob): Promise<ArchivePreview> {
  const zip = await JSZip.loadAsync(file)
  return summarizeArchive(await parseArchiveData(zip))
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

function repairImportedTodoRecordLinks(todos: UnifiedTodo[], records: Record<string, unknown[]>): { todos: UnifiedTodo[]; repaired: number } {
  const recordIds = new Set<string>()
  const recordTodoIds = new Map<string, string>()
  for (const dayRecords of Object.values(records)) {
    for (const record of dayRecords) {
      if (!record || typeof record !== 'object') continue
      const candidate = record as { id?: unknown; todo_id?: unknown }
      if (typeof candidate.id === 'string') {
        recordIds.add(candidate.id)
        if (typeof candidate.todo_id === 'string' && candidate.todo_id) {
          recordTodoIds.set(candidate.id, candidate.todo_id)
        }
      }
    }
  }
  let repaired = 0
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
  return { todos: repairedTodos, repaired }
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
  const snapshot = rawPlanHelper as { available?: unknown; plans?: unknown }
  if (snapshot.available !== true || !Array.isArray(snapshot.plans)) return { todos, repaired: 0 }

  const taskIdsByPlan = new Map<string, Set<string>>()
  snapshot.plans.forEach((raw, planIndex) => {
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
    taskIdsByPlan.set(planId, taskIds)
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
  for (let i = 0; i < localStorage.length; i += 1) {
    const key = localStorage.key(i)
    if (key) {
      localStorageSnapshot[key] = localStorage.getItem(key) || ''
    }
  }

  const stores: Record<string, unknown[]> = {}
  for (const storeName of Object.values(STORE_NAMES)) {
    stores[storeName] = await getRawAll<unknown>(storeName)
  }
  return { localStorage: localStorageSnapshot, stores }
}

async function restoreArchiveRuntimeSnapshot(snapshot: ArchiveRuntimeSnapshot): Promise<void> {
  const { clear: idbClear, putRaw, STORE_NAMES } = await import('@/storage')
  for (let i = localStorage.length - 1; i >= 0; i -= 1) {
    const key = localStorage.key(i)
    if (key) localStorage.removeItem(key)
  }
  for (const [key, value] of Object.entries(snapshot.localStorage)) {
    localStorage.setItem(key, value)
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
    localStorage.removeItem(localKey)
    await idbClear(storeName)
    return
  }
  writeJSON(localKey, value)
  await idbSet(storeName, storeKey, value)
}

async function processArchiveData(zip: JSZip): Promise<{ success: boolean; message: string }> {
    const data = await parseArchiveData(zip)
    const runtimeSnapshot = await captureArchiveRuntimeSnapshot()

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
    if (data.planHelper?.available && Array.isArray(data.planHelper.plans)) {
      try {
        await idbSet(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'plans', data.planHelper.plans)
      } catch (error) {
        warnings.push(translate('settings.archive.snapshotSaveFailed', { detail: error instanceof Error ? error.message : translate('settings.archive.localStorageUnavailable') }))
      }
    }
    if (getPlanRuntime() === 'mobile-unavailable') {
      if (data.planHelper?.available && Array.isArray(data.planHelper.plans)) {
        await idbSet(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'plans', data.planHelper.plans)
      } else {
        await idbClear(STORE_NAMES.PLAN_HELPER_SNAPSHOT)
        warnings.push(translate('settings.archive.planNotRestored', { reason: data.planHelper?.unavailableReason || translate('settings.archive.planSnapshotMissing') }))
      }
    } else if (data.planHelper?.available && Array.isArray(data.planHelper.plans)) {
      try {
        const response = await requestPlanHelper('/api/data/import', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify({ plans: data.planHelper.plans, replace: true }),
        })
        const payload = await response.json() as { success?: boolean; error?: string }
        if (!response.ok || !payload.success) throw new Error(payload.error || translate('settings.archive.planRestoreResponse', { status: response.status }))
      } catch (error) {
        warnings.push(translate('settings.archive.planRestoreFailed', { detail: error instanceof Error ? error.message : translate('settings.archive.planServiceUnavailable') }))
      }
    } else {
      await clearPlanHelperData()
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
      body: JSON.stringify({ plans: [], replace: true }),
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
  todoCategoryCount: number
  hasConfig: boolean
  hasPlans: boolean
  eventPlanCount: number
  hasAudioSettings: boolean
  hasEventSettings: boolean
  hasCheckin: boolean
}> {
  const records = await getAllRecords()
  let totalRecords = 0
  for (const dateRecords of Object.values(records)) {
    totalRecords += dateRecords.length
  }
  const { getRawAll, STORE_NAMES } = await import('@/storage')
  const cachedEventPlans = await readCachedPlanHelperData()
  const todos = await getRawAll<UnifiedTodo>(STORE_NAMES.TODOS)
  const categories = await getRawAll<TodoCategory>(STORE_NAMES.TODO_CATEGORIES)

  return {
    recordDays: Object.keys(records).length,
    totalRecords,
    todoCount: todos.length,
    activeTodoCount: todos.filter((todo) => !['completed', 'archived', 'cancelled'].includes(todo.status)).length,
    todoCategoryCount: categories.length,
    hasConfig: !!(await readCoreJSON(STORAGE_KEYS.CONFIG, STORE_NAMES.CONFIG, 'config')),
    hasPlans: !!(await readCoreJSON(STORAGE_KEYS.PLANS, STORE_NAMES.PLANS, 'plans')),
    eventPlanCount: cachedEventPlans?.length || 0,
    // All settings and check-in data now have IndexedDB primaries with
    // compatibility mirrors.
    hasAudioSettings: !!(await readCoreJSON(STORAGE_KEYS.AUDIO_SETTINGS, STORE_NAMES.AUDIO_SETTINGS, 'settings')),
    hasEventSettings: !!(await readCoreJSON(STORAGE_KEYS.EVENT_SETTINGS, STORE_NAMES.EVENT_SETTINGS, 'settings')),
    hasCheckin: !!(await readCoreJSON(STORAGE_KEYS.CHECKIN, STORE_NAMES.CHECKIN, 'data')),
  }
}
