// 自动备份模块 - 数据变更时自动备份

import { set, STORE_NAMES } from './indexedDB'

const MAX_BACKUPS_PER_MODULE = 10
const BACKUP_DEBOUNCE_MS = 5000 // 5秒内多次变更只备份一次
const STORAGE_PREFIX = 'efflife_backup_'

// 检测是否在 Tauri 环境
function isTauri(): boolean {
  return !!(window as any).__TAURI__
}

// 检测是否在移动端
function isMobile(): boolean {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

// 备份数据接口
export interface BackupData {
  version: string
  module: string
  timestamp: string
  data: unknown
}

// 防抖计时器
const debounceTimers: Record<string, NodeJS.Timeout> = {}

// 获取所有备份（从 localStorage）
export function getBackups(moduleName: string): BackupData[] {
  const backups: BackupData[] = []
  const prefix = `${STORAGE_PREFIX}${moduleName}_`

  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(prefix)) {
      try {
        const backup = JSON.parse(localStorage.getItem(key) || '{}')
        backups.push(backup)
      } catch {
        // ignore corrupted backup
      }
    }
  }

  // 按时间戳排序（最新的在前）
  return backups.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  )
}

// 保存备份到 localStorage
function saveBackupToLocalStorage(moduleName: string, data: unknown): void {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  const key = `${STORAGE_PREFIX}${moduleName}_${timestamp}`

  const backup: BackupData = {
    version: '1.0',
    module: moduleName,
    timestamp: new Date().toISOString(),
    data,
  }

  localStorage.setItem(key, JSON.stringify(backup))

  // 清理旧备份，保留最新的 MAX_BACKUPS_PER_MODULE 个
  const backups = getBackups(moduleName)
  if (backups.length > MAX_BACKUPS_PER_MODULE) {
    const toDelete = backups.slice(MAX_BACKUPS_PER_MODULE)
    toDelete.forEach((b) => {
      const ts = new Date(b.timestamp).toISOString().replace(/[:.]/g, '-').slice(0, 19)
      localStorage.removeItem(`${STORAGE_PREFIX}${moduleName}_${ts}`)
    })
  }
}

// 保存备份到文件系统（Tauri 桌面端）
async function saveBackupToFileSystem(
  moduleName: string,
  data: unknown
): Promise<string | null> {
  if (!isTauri() || isMobile()) {
    return null
  }

  try {
    const { appDataDir, join } = await import('@tauri-apps/api/path')
    const { createDir, writeTextFile, exists } = await import('@tauri-apps/plugin-fs')

    const baseDir = await appDataDir()
    const backupsDir = await join(baseDir, 'data', 'backups')

    // 确保目录存在
    if (!(await exists(backupsDir))) {
      await createDir(backupsDir, { recursive: true })
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    const filename = `${moduleName}_${timestamp}.json`
    const filePath = await join(backupsDir, filename)

    const backup: BackupData = {
      version: '1.0',
      module: moduleName,
      timestamp: new Date().toISOString(),
      data,
    }

    await writeTextFile(filePath, JSON.stringify(backup, null, 2))

    // 清理旧备份
    await cleanupFileSystemBackups(backupsDir, moduleName)

    return filePath
  } catch (error) {
    console.warn('Failed to save backup to file system:', error)
    return null
  }
}

// 清理文件系统上的旧备份
async function cleanupFileSystemBackups(
  backupsDir: string,
  moduleName: string
): Promise<void> {
  try {
    const { readDir, remove } = await import('@tauri-apps/plugin-fs')
    const { join } = await import('@tauri-apps/api/path')

    const files = await readDir(backupsDir)
    const backupFiles = files
      .filter((f) => f.name && f.name.startsWith(`${moduleName}_`) && f.name.endsWith('.json'))
      .sort((a, b) => (b.name || '').localeCompare(a.name || ''))

    if (backupFiles.length > MAX_BACKUPS_PER_MODULE) {
      const toDelete = backupFiles.slice(MAX_BACKUPS_PER_MODULE)
      for (const file of toDelete) {
        if (file.name) {
          const filePath = await join(backupsDir, file.name)
          await remove(filePath)
        }
      }
    }
  } catch (error) {
    console.warn('Failed to cleanup file system backups:', error)
  }
}

// 创建备份（自动选择存储方式）
export async function createBackup(moduleName: string, data: unknown): Promise<void> {
  // 始终保存到 localStorage 作为快速恢复源
  saveBackupToLocalStorage(moduleName, data)

  // 桌面端同时保存到文件系统
  if (isTauri() && !isMobile()) {
    await saveBackupToFileSystem(moduleName, data)
  }
}

// 防抖备份（数据变更时调用）
export function scheduleBackup(moduleName: string, data: unknown): void {
  if (debounceTimers[moduleName]) {
    clearTimeout(debounceTimers[moduleName])
  }

  debounceTimers[moduleName] = setTimeout(async () => {
    try {
      await createBackup(moduleName, data)
    } catch (error) {
      console.error(`Backup failed for ${moduleName}:`, error)
    } finally {
      delete debounceTimers[moduleName]
    }
  }, BACKUP_DEBOUNCE_MS)
}

// 从备份恢复数据
export async function restoreFromBackup(backup: BackupData): Promise<void> {
  const data = backup.data as Record<string, unknown>

  // 根据模块类型恢复数据
  switch (backup.module) {
    case 'config':
      await set(STORE_NAMES.CONFIG, 'config', data)
      break
    case 'plans':
      await set(STORE_NAMES.PLANS, 'plans', data)
      break
    case 'records':
      if (Array.isArray(data)) {
        for (const record of data) {
          const r = record as { date: string; records: unknown[] }
          await set(STORE_NAMES.RECORDS, r.date, r.records)
        }
      }
      break
    case 'schedule_rules':
      await set(STORE_NAMES.SCHEDULE_RULES, 'rules', data)
      break
    case 'manual_plans':
      if (typeof data === 'object' && data !== null) {
        for (const [date, planName] of Object.entries(data)) {
          await set(STORE_NAMES.MANUAL_PLANS, date, planName)
        }
      }
      break
  }
}

// 获取所有备份模块列表
export function getBackupModules(): string[] {
  const modules = new Set<string>()
  const prefix = STORAGE_PREFIX

  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(prefix)) {
      const rest = key.slice(prefix.length)
      const moduleName = rest.split('_')[0]
      modules.add(moduleName)
    }
  }

  return Array.from(modules)
}

// 获取所有备份（所有模块）
export function getAllBackups(): BackupData[] {
  const backups: BackupData[] = []

  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(STORAGE_PREFIX)) {
      try {
        const backup = JSON.parse(localStorage.getItem(key) || '{}')
        backups.push(backup)
      } catch {
        // ignore corrupted backup
      }
    }
  }

  return backups.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  )
}

// 删除指定备份
export function deleteBackup(moduleName: string, timestamp: string): void {
  const ts = new Date(timestamp).toISOString().replace(/[:.]/g, '-').slice(0, 19)
  localStorage.removeItem(`${STORAGE_PREFIX}${moduleName}_${ts}`)
}

// 清除指定模块的所有备份
export function clearModuleBackups(moduleName: string): void {
  const keysToRemove: string[] = []
  const prefix = `${STORAGE_PREFIX}${moduleName}_`

  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(prefix)) {
      keysToRemove.push(key)
    }
  }

  keysToRemove.forEach(key => localStorage.removeItem(key))
}
