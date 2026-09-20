// 存储模块入口 - 统一导出所有存储相关功能

export {
  openDB,
  closeDB,
  get,
  set,
  del,
  getAll,
  clear,
  isEmpty,
  STORE_NAMES,
} from './indexedDB'

export {
  createBackup,
  scheduleBackup,
  restoreFromBackup,
  getBackups,
  getAllBackups,
  getBackupModules,
  deleteBackup,
  clearModuleBackups,
  type BackupData,
} from './backup'

export {
  runMigration,
  isMigrationDone,
  hasIndexedDBData,
  hasLocalStorageData,
} from './migration'

export {
  checkDataIntegrity,
  getRecoverySuggestions,
  restoreFromLatestBackup,
  restoreFromSpecificBackup,
  exportEmergencyBackup,
  restoreFromEmergencyBackup,
  type DataStatus,
  type RecoverySuggestion,
} from './recovery'
