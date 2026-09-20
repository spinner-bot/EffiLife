// IndexedDB 存储层 - 提供持久化存储，localStorage 作为降级方案

const DB_NAME = 'efflife_db'
const DB_VERSION = 1
const STORAGE_PREFIX = 'efflife_'

// 对象存储名称
export const STORE_NAMES = {
  CONFIG: 'config',
  RECORDS: 'records',
  PLANS: 'plans',
  EVENTS: 'events',
  TODOS: 'todos',
  MANUAL_PLANS: 'manual_plans',
  SCHEDULE_RULES: 'schedule_rules',
  AUDIO_SETTINGS: 'audio_settings',
  EVENT_SETTINGS: 'event_settings',
  EVENT_INBOX: 'event_inbox',
  WARNING_INBOX: 'warning_inbox',
  DAILY_TRIGGER: 'daily_trigger',
  CHECKIN: 'checkin',
} as const

let dbInstance: IDBDatabase | null = null
let dbPromise: Promise<IDBDatabase> | null = null

// 检测 IndexedDB 是否可用
function isIndexedDBAvailable(): boolean {
  try {
    return typeof indexedDB !== 'undefined' && indexedDB !== null
  } catch {
    return false
  }
}

// 打开数据库
export async function openDB(): Promise<IDBDatabase> {
  if (dbInstance) {
    return dbInstance
  }

  if (dbPromise) {
    return dbPromise
  }

  if (!isIndexedDBAvailable()) {
    throw new Error('IndexedDB is not available')
  }

  dbPromise = new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)

    request.onerror = () => {
      dbPromise = null
      reject(request.error)
    }

    request.onsuccess = () => {
      dbInstance = request.result
      resolve(dbInstance)
    }

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result

      // 创建对象存储
      if (!db.objectStoreNames.contains(STORE_NAMES.CONFIG)) {
        db.createObjectStore(STORE_NAMES.CONFIG, { keyPath: 'key' })
      }
      if (!db.objectStoreNames.contains(STORE_NAMES.RECORDS)) {
        db.createObjectStore(STORE_NAMES.RECORDS, { keyPath: 'date' })
      }
      if (!db.objectStoreNames.contains(STORE_NAMES.PLANS)) {
        db.createObjectStore(STORE_NAMES.PLANS, { keyPath: 'id' })
      }
      if (!db.objectStoreNames.contains(STORE_NAMES.EVENTS)) {
        db.createObjectStore(STORE_NAMES.EVENTS, { keyPath: 'id', autoIncrement: true })
      }
      if (!db.objectStoreNames.contains(STORE_NAMES.TODOS)) {
        db.createObjectStore(STORE_NAMES.TODOS, { keyPath: 'id', autoIncrement: true })
      }
      if (!db.objectStoreNames.contains(STORE_NAMES.MANUAL_PLANS)) {
        db.createObjectStore(STORE_NAMES.MANUAL_PLANS, { keyPath: 'date' })
      }
      if (!db.objectStoreNames.contains(STORE_NAMES.SCHEDULE_RULES)) {
        db.createObjectStore(STORE_NAMES.SCHEDULE_RULES, { keyPath: 'id', autoIncrement: true })
      }
      if (!db.objectStoreNames.contains(STORE_NAMES.AUDIO_SETTINGS)) {
        db.createObjectStore(STORE_NAMES.AUDIO_SETTINGS, { keyPath: 'key' })
      }
      if (!db.objectStoreNames.contains(STORE_NAMES.EVENT_SETTINGS)) {
        db.createObjectStore(STORE_NAMES.EVENT_SETTINGS, { keyPath: 'key' })
      }
      if (!db.objectStoreNames.contains(STORE_NAMES.EVENT_INBOX)) {
        db.createObjectStore(STORE_NAMES.EVENT_INBOX, { keyPath: 'id', autoIncrement: true })
      }
      if (!db.objectStoreNames.contains(STORE_NAMES.WARNING_INBOX)) {
        db.createObjectStore(STORE_NAMES.WARNING_INBOX, { keyPath: 'id', autoIncrement: true })
      }
      if (!db.objectStoreNames.contains(STORE_NAMES.DAILY_TRIGGER)) {
        db.createObjectStore(STORE_NAMES.DAILY_TRIGGER, { keyPath: 'key' })
      }
      if (!db.objectStoreNames.contains(STORE_NAMES.CHECKIN)) {
        db.createObjectStore(STORE_NAMES.CHECKIN, { keyPath: 'key' })
      }
    }
  })

  return dbPromise
}

// 通用 GET 操作
export async function get<T>(storeName: string, key: string): Promise<T | null> {
  try {
    const db = await openDB()
    return new Promise<T | null>((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      const request = store.get(key)

      request.onerror = () => reject(request.error)
      request.onsuccess = () => {
        const result = request.result
        resolve(result ? (result as any).value : null)
      }
    })
  } catch (error) {
    console.warn(`IndexedDB get failed for ${storeName}/${key}, falling back to localStorage:`, error)
    // 降级到 localStorage
    const stored = localStorage.getItem(`${STORAGE_PREFIX}${storeName}_${key}`)
    return stored ? JSON.parse(stored) : null
  }
}

// 通用 SET 操作
export async function set<T>(storeName: string, key: string, value: T): Promise<void> {
  try {
    const db = await openDB()
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      const request = store.put({ key, value, updatedAt: Date.now() })

      request.onerror = () => reject(request.error)
      request.onsuccess = () => resolve()
    })
  } catch (error) {
    console.warn(`IndexedDB set failed for ${storeName}/${key}, falling back to localStorage:`, error)
    // 降级到 localStorage
    localStorage.setItem(`${STORAGE_PREFIX}${storeName}_${key}`, JSON.stringify(value))
  }
}

// 通用 DELETE 操作
export async function del(storeName: string, key: string): Promise<void> {
  try {
    const db = await openDB()
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      const request = store.delete(key)

      request.onerror = () => reject(request.error)
      request.onsuccess = () => resolve()
    })
  } catch (error) {
    console.warn(`IndexedDB delete failed for ${storeName}/${key}, falling back to localStorage:`, error)
    localStorage.removeItem(`${STORAGE_PREFIX}${storeName}_${key}`)
  }
}

// 获取存储中的所有数据
export async function getAll<T>(storeName: string): Promise<T[]> {
  try {
    const db = await openDB()
    return new Promise<T[]>((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      const request = store.getAll()

      request.onerror = () => reject(request.error)
      request.onsuccess = () => {
        const results = request.result || []
        resolve(results.map((item: any) => item.value))
      }
    })
  } catch (error) {
    console.warn(`IndexedDB getAll failed for ${storeName}, falling back to localStorage:`, error)
    // 降级到 localStorage
    const results: T[] = []
    const prefix = `${STORAGE_PREFIX}${storeName}_`
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith(prefix)) {
        try {
          const value = JSON.parse(localStorage.getItem(key) || 'null')
          if (value !== null) {
            results.push(value)
          }
        } catch {
          // ignore
        }
      }
    }
    return results
  }
}

// 清空存储
export async function clear(storeName: string): Promise<void> {
  try {
    const db = await openDB()
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      const request = store.clear()

      request.onerror = () => reject(request.error)
      request.onsuccess = () => resolve()
    })
  } catch (error) {
    console.warn(`IndexedDB clear failed for ${storeName}, falling back to localStorage:`, error)
    // 降级到 localStorage
    const prefix = `${STORAGE_PREFIX}${storeName}_`
    const keysToRemove: string[] = []
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith(prefix)) {
        keysToRemove.push(key)
      }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key))
  }
}

// 检查存储是否为空
export async function isEmpty(storeName: string): Promise<boolean> {
  try {
    const db = await openDB()
    return new Promise<boolean>((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      const request = store.count()

      request.onerror = () => reject(request.error)
      request.onsuccess = () => {
        resolve(request.result === 0)
      }
    })
  } catch (error) {
    console.warn(`IndexedDB isEmpty failed for ${storeName}, falling back to localStorage:`, error)
    // 降级到 localStorage
    const prefix = `${STORAGE_PREFIX}${storeName}_`
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith(prefix)) {
        return false
      }
    }
    return true
  }
}

// 关闭数据库
export function closeDB(): void {
  if (dbInstance) {
    dbInstance.close()
    dbInstance = null
    dbPromise = null
  }
}
