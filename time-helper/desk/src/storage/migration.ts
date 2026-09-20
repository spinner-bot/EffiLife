// 数据迁移模块 - 从 localStorage 迁移到 IndexedDB

import { get, set, isEmpty } from './indexedDB'
import { STORE_NAMES } from './indexedDB'
import { createBackup } from './backup'

const STORAGE_PREFIX = 'efflife_'
const MIGRATION_FLAG_KEY = 'efflife_db_migration_done'

// 检测是否已完成迁移
export function isMigrationDone(): boolean {
  return localStorage.getItem(MIGRATION_FLAG_KEY) === 'true'
}

// 标记迁移完成
function markMigrationDone(): void {
  localStorage.setItem(MIGRATION_FLAG_KEY, 'true')
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

// 迁移配置数据
async function migrateConfig(): Promise<boolean> {
  const data = readJSON<Record<string, unknown>>(`${STORAGE_PREFIX}config`)
  if (!data) return false

  const existing = await get<Record<string, unknown>>(STORE_NAMES.CONFIG, 'config')
  if (existing) return false // IndexedDB 已有数据，跳过

  await set(STORE_NAMES.CONFIG, 'config', data)
  return true
}

// 迁移计划数据
async function migratePlans(): Promise<boolean> {
  const data = readJSON<Record<string, unknown>>(`${STORAGE_PREFIX}plans`)
  if (!data) return false

  const existing = await get<Record<string, unknown>>(STORE_NAMES.PLANS, 'plans')
  if (existing) return false

  await set(STORE_NAMES.PLANS, 'plans', data)
  return true
}

// 迁移日程规则
async function migrateScheduleRules(): Promise<boolean> {
  const data = readJSON<unknown[]>(`${STORAGE_PREFIX}schedule_rules`)
  if (!data) return false

  const existing = await get<unknown[]>(STORE_NAMES.SCHEDULE_RULES, 'rules')
  if (existing) return false

  await set(STORE_NAMES.SCHEDULE_RULES, 'rules', data)
  return true
}

// 迁移手动计划
async function migrateManualPlans(): Promise<boolean> {
  const data = readJSON<Record<string, string>>(`${STORAGE_PREFIX}manual_plans`)
  if (!data) return false

  const existing = await get<Record<string, string>>(STORE_NAMES.MANUAL_PLANS, 'all')
  if (existing) return false

  await set(STORE_NAMES.MANUAL_PLANS, 'all', data)
  return true
}

// 迁移记录数据
async function migrateRecords(): Promise<boolean> {
  let migrated = false

  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(`${STORAGE_PREFIX}records_`)) {
      const date = key.replace(`${STORAGE_PREFIX}records_`, '')
      const data = readJSON<unknown[]>(key)
      if (data) {
        const existing = await get<unknown[]>(STORE_NAMES.RECORDS, date)
        if (!existing) {
          await set(STORE_NAMES.RECORDS, date, data)
          migrated = true
        }
      }
    }
  }

  return migrated
}

// 迁移音频设置
async function migrateAudioSettings(): Promise<boolean> {
  const data = readJSON<Record<string, unknown>>(`${STORAGE_PREFIX}audio_settings`)
  if (!data) return false

  const existing = await get<Record<string, unknown>>(STORE_NAMES.AUDIO_SETTINGS, 'settings')
  if (existing) return false

  await set(STORE_NAMES.AUDIO_SETTINGS, 'settings', data)
  return true
}

// 迁移事件设置
async function migrateEventSettings(): Promise<boolean> {
  const data = readJSON<Record<string, unknown>>(`${STORAGE_PREFIX}event_settings`)
  if (!data) return false

  const existing = await get<Record<string, unknown>>(STORE_NAMES.EVENT_SETTINGS, 'settings')
  if (existing) return false

  await set(STORE_NAMES.EVENT_SETTINGS, 'settings', data)
  return true
}

// 迁移事件收件箱
async function migrateEventInbox(): Promise<boolean> {
  const data = readJSON<unknown[]>(`${STORAGE_PREFIX}event_inbox`)
  if (!data) return false

  const existing = await get<unknown[]>(STORE_NAMES.EVENT_INBOX, 'inbox')
  if (existing) return false

  await set(STORE_NAMES.EVENT_INBOX, 'inbox', data)
  return true
}

// 迁移预警收件箱
async function migrateWarningInbox(): Promise<boolean> {
  const data = readJSON<unknown[]>(`${STORAGE_PREFIX}warning_inbox`)
  if (!data) return false

  const existing = await get<unknown[]>(STORE_NAMES.WARNING_INBOX, 'inbox')
  if (existing) return false

  await set(STORE_NAMES.WARNING_INBOX, 'inbox', data)
  return true
}

// 迁移每日触发器
async function migrateDailyTrigger(): Promise<boolean> {
  const data = readJSON<Record<string, unknown>>(`${STORAGE_PREFIX}daily_trigger`)
  if (!data) return false

  const existing = await get<Record<string, unknown>>(STORE_NAMES.DAILY_TRIGGER, 'trigger')
  if (existing) return false

  await set(STORE_NAMES.DAILY_TRIGGER, 'trigger', data)
  return true
}

// 迁移打卡数据
async function migrateCheckin(): Promise<boolean> {
  const data = readJSON<Record<string, unknown>>(`${STORAGE_PREFIX}checkin`)
  if (!data) return false

  const existing = await get<Record<string, unknown>>(STORE_NAMES.CHECKIN, 'data')
  if (existing) return false

  await set(STORE_NAMES.CHECKIN, 'data', data)
  return true
}

// 执行完整迁移
export async function runMigration(): Promise<{
  success: boolean
  migrated: string[]
  errors: string[]
}> {
  if (isMigrationDone()) {
    return { success: true, migrated: [], errors: [] }
  }

  const migrated: string[] = []
  const errors: string[] = []

  // 先创建备份
  try {
    const backupData = collectLocalStorageData()
    await createBackup('pre_migration_full', backupData)
  } catch (error) {
    console.warn('Failed to create pre-migration backup:', error)
  }

  // 执行各项迁移
  const migrations: Array<{ name: string; fn: () => Promise<boolean> }> = [
    { name: 'config', fn: migrateConfig },
    { name: 'plans', fn: migratePlans },
    { name: 'schedule_rules', fn: migrateScheduleRules },
    { name: 'manual_plans', fn: migrateManualPlans },
    { name: 'records', fn: migrateRecords },
    { name: 'audio_settings', fn: migrateAudioSettings },
    { name: 'event_settings', fn: migrateEventSettings },
    { name: 'event_inbox', fn: migrateEventInbox },
    { name: 'warning_inbox', fn: migrateWarningInbox },
    { name: 'daily_trigger', fn: migrateDailyTrigger },
    { name: 'checkin', fn: migrateCheckin },
  ]

  for (const migration of migrations) {
    try {
      const didMigrate = await migration.fn()
      if (didMigrate) {
        migrated.push(migration.name)
      }
    } catch (error) {
      errors.push(`${migration.name}: ${(error as Error).message}`)
      console.error(`Migration failed for ${migration.name}:`, error)
    }
  }

  if (errors.length === 0) {
    markMigrationDone()
  }

  return {
    success: errors.length === 0,
    migrated,
    errors,
  }
}

// 收集 localStorage 中的所有数据（用于备份）
function collectLocalStorageData(): Record<string, unknown> {
  const data: Record<string, unknown> = {}

  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(STORAGE_PREFIX)) {
      try {
        data[key] = JSON.parse(localStorage.getItem(key) || 'null')
      } catch {
        data[key] = localStorage.getItem(key)
      }
    }
  }

  return data
}

// 检查 IndexedDB 是否有数据
export async function hasIndexedDBData(): Promise<boolean> {
  const stores = [
    STORE_NAMES.CONFIG,
    STORE_NAMES.PLANS,
    STORE_NAMES.RECORDS,
    STORE_NAMES.SCHEDULE_RULES,
  ]

  for (const store of stores) {
    const empty = await isEmpty(store)
    if (!empty) return true
  }

  return false
}

// 检查 localStorage 是否有数据
export function hasLocalStorageData(): boolean {
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(STORAGE_PREFIX) && key !== MIGRATION_FLAG_KEY) {
      return true
    }
  }
  return false
}
