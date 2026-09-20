// 数据恢复机制 - 启动时检测数据状态，提供恢复选项

import { get, set, isEmpty, openDB, STORE_NAMES } from './indexedDB'
import { getAllBackups, restoreFromBackup, type BackupData } from './backup'
import { hasLocalStorageData, hasIndexedDBData } from './migration'

// 数据状态
export interface DataStatus {
  localStorageEmpty: boolean
  indexedDBEmpty: boolean
  hasBackups: boolean
  backupCount: number
  latestBackup: BackupData | null
  lastBackupTime: string | null
}

// 恢复建议
export interface RecoverySuggestion {
  type: 'restore_from_backup' | 'import_archive' | 'start_fresh' | 'no_action'
  message: string
  backupInfo?: BackupData
}

// 检测数据完整性
export async function checkDataIntegrity(): Promise<DataStatus> {
  const localStorageEmpty = !hasLocalStorageData()
  const indexedDBEmpty = !(await hasIndexedDBData())

  const backups = getAllBackups()
  const hasBackups = backups.length > 0
  const latestBackup = hasBackups ? backups[0] : null
  const lastBackupTime = latestBackup ? latestBackup.timestamp : null

  return {
    localStorageEmpty,
    indexedDBEmpty,
    hasBackups,
    backupCount: backups.length,
    latestBackup,
    lastBackupTime,
  }
}

// 获取恢复建议
export async function getRecoverySuggestions(): Promise<RecoverySuggestion[]> {
  const status = await checkDataIntegrity()
  const suggestions: RecoverySuggestion[] = []

  // 两个存储都为空
  if (status.localStorageEmpty && status.indexedDBEmpty) {
    if (status.hasBackups) {
      suggestions.push({
        type: 'restore_from_backup',
        message: `检测到数据为空，但发现 ${status.backupCount} 个备份。建议从最近的备份恢复。`,
        backupInfo: status.latestBackup || undefined,
      })
    } else {
      suggestions.push({
        type: 'import_archive',
        message: '检测到数据为空，且无备份。可以导入存档文件恢复数据。',
      })
    }
  } else if (status.indexedDBEmpty && !status.localStorageEmpty) {
    // IndexedDB 为空但 localStorage 有数据（可能是迁移失败）
    suggestions.push({
      type: 'restore_from_backup',
      message: '检测到 IndexedDB 数据为空，但 localStorage 有数据。建议重新执行数据迁移。',
    })
  } else if (!status.indexedDBEmpty && status.localStorageEmpty) {
    // 正常状态：数据已迁移到 IndexedDB
    suggestions.push({
      type: 'no_action',
      message: '数据状态正常，无需恢复操作。',
    })
  } else {
    // 两个存储都有数据（可能是迁移后 localStorage 未清理）
    suggestions.push({
      type: 'no_action',
      message: '数据状态正常。',
    })
  }

  return suggestions
}

// 从最新备份恢复
export async function restoreFromLatestBackup(): Promise<{
  success: boolean
  message: string
}> {
  try {
    const backups = getAllBackups()
    if (backups.length === 0) {
      return { success: false, message: '没有找到备份文件' }
    }

    const latestBackup = backups[0]
    await restoreFromBackup(latestBackup)

    return {
      success: true,
      message: `已从 ${new Date(latestBackup.timestamp).toLocaleString('zh-CN')} 的备份恢复数据`,
    }
  } catch (error) {
    return {
      success: false,
      message: `恢复失败：${(error as Error).message}`,
    }
  }
}

// 从指定备份恢复
export async function restoreFromSpecificBackup(backup: BackupData): Promise<{
  success: boolean
  message: string
}> {
  try {
    await restoreFromBackup(backup)

    return {
      success: true,
      message: `已从 ${new Date(backup.timestamp).toLocaleString('zh-CN')} 的备份恢复数据`,
    }
  } catch (error) {
    return {
      success: false,
      message: `恢复失败：${(error as Error).message}`,
    }
  }
}

// 紧急数据导出（当检测到数据问题时）
export async function exportEmergencyBackup(): Promise<string> {
  const backupData: Record<string, unknown> = {}

  try {
    // 从 IndexedDB 导出
    backupData.config = await get(STORE_NAMES.CONFIG, 'config')
    backupData.plans = await get(STORE_NAMES.PLANS, 'plans')
    backupData.scheduleRules = await get(STORE_NAMES.SCHEDULE_RULES, 'rules')
    backupData.manualPlans = await get(STORE_NAMES.MANUAL_PLANS, 'all')

    // 导出所有记录
    const records: Record<string, unknown> = {}
    const db = await openDB()
    const transaction = db.transaction([STORE_NAMES.RECORDS], 'readonly')
    const store = transaction.objectStore(STORE_NAMES.RECORDS)
    const request = store.getAll()

    await new Promise<void>((resolve, reject) => {
      request.onerror = () => reject(request.error)
      request.onsuccess = () => {
        const results = request.result || []
        for (const item of results) {
          records[(item as any).date] = (item as any).value
        }
        resolve()
      }
    })

    backupData.records = records

    // 也收集 localStorage 中的数据
    const localStorageData: Record<string, unknown> = {}
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith('efflife_')) {
        try {
          localStorageData[key] = JSON.parse(localStorage.getItem(key) || 'null')
        } catch {
          localStorageData[key] = localStorage.getItem(key)
        }
      }
    }
    backupData.localStorage = localStorageData

    const jsonStr = JSON.stringify(backupData, null, 2)

    // 保存为紧急备份
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    localStorage.setItem(`efflife_emergency_backup_${timestamp}`, jsonStr)

    return jsonStr
  } catch (error) {
    console.error('Emergency backup failed:', error)
    return JSON.stringify(backupData)
  }
}

// 从紧急备份恢复
export async function restoreFromEmergencyBackup(jsonStr: string): Promise<{
  success: boolean
  message: string
}> {
  try {
    const data = JSON.parse(jsonStr)

    // 恢复 IndexedDB 数据
    if (data.config) {
      await set(STORE_NAMES.CONFIG, 'config', data.config)
    }
    if (data.plans) {
      await set(STORE_NAMES.PLANS, 'plans', data.plans)
    }
    if (data.scheduleRules) {
      await set(STORE_NAMES.SCHEDULE_RULES, 'rules', data.scheduleRules)
    }
    if (data.manualPlans) {
      await set(STORE_NAMES.MANUAL_PLANS, 'all', data.manualPlans)
    }
    if (data.records) {
      for (const [date, records] of Object.entries(data.records)) {
        await set(STORE_NAMES.RECORDS, date, records)
      }
    }

    // 恢复 localStorage 数据
    if (data.localStorage) {
      for (const [key, value] of Object.entries(data.localStorage)) {
        localStorage.setItem(key, JSON.stringify(value))
      }
    }

    return {
      success: true,
      message: '已从紧急备份恢复数据',
    }
  } catch (error) {
    return {
      success: false,
      message: `恢复失败：${(error as Error).message}`,
    }
  }
}
