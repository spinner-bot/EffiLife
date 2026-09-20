// 存储层测试 - 验证数据完整性
// 这些测试可以在浏览器控制台或 Vitest 中运行

import {
  openDB,
  closeDB,
  get,
  set,
  del,
  getAll,
  clear,
  isEmpty,
  STORE_NAMES,
} from '../storage/indexedDB'

import {
  createBackup,
  getBackups,
  getAllBackups,
  restoreFromBackup,
  clearModuleBackups,
  type BackupData,
} from '../storage/backup'

import {
  runMigration,
  isMigrationDone,
  hasIndexedDBData,
  hasLocalStorageData,
} from '../storage/migration'

import {
  checkDataIntegrity,
  getRecoverySuggestions,
  restoreFromLatestBackup,
  exportEmergencyBackup,
  restoreFromEmergencyBackup,
} from '../storage/recovery'

// 简单的测试框架
let passed = 0
let failed = 0
const errors: string[] = []

function assert(condition: boolean, message: string) {
  if (condition) {
    passed++
    console.log(`✅ ${message}`)
  } else {
    failed++
    errors.push(message)
    console.error(`❌ ${message}`)
  }
}

function assertEqual<T>(actual: T, expected: T, message: string) {
  const equal = JSON.stringify(actual) === JSON.stringify(expected)
  if (equal) {
    passed++
    console.log(`✅ ${message}`)
  } else {
    failed++
    errors.push(`${message}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`)
    console.error(`❌ ${message}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`)
  }
}

// ============ IndexedDB 测试 ============
async function testIndexedDB() {
  console.log('\n📦 Testing IndexedDB storage layer...')

  // 清理
  await clear(STORE_NAMES.CONFIG)

  // 测试 set/get
  const testData = { name: 'test', value: 42, nested: { a: 1 } }
  await set(STORE_NAMES.CONFIG, 'test_key', testData)
  const result = await get<typeof testData>(STORE_NAMES.CONFIG, 'test_key')
  assertEqual(result, testData, 'set/get: 应该能正确存储和读取数据')

  // 测试 getAll
  await set(STORE_NAMES.CONFIG, 'test_key2', { name: 'test2', value: 100 })
  const all = await getAll<typeof testData>(STORE_NAMES.CONFIG)
  assert(all.length >= 2, `getAll: 应该返回所有数据 (got ${all.length})`)

  // 测试 isEmpty
  const configEmpty = await isEmpty(STORE_NAMES.CONFIG)
  assert(!configEmpty, 'isEmpty: 有数据时应该返回 false')

  // 测试 delete
  await del(STORE_NAMES.CONFIG, 'test_key')
  const deleted = await get(STORE_NAMES.CONFIG, 'test_key')
  assertEqual(deleted, null, 'delete: 删除后应该返回 null')

  // 测试 clear
  await clear(STORE_NAMES.CONFIG)
  const afterClear = await isEmpty(STORE_NAMES.CONFIG)
  assert(afterClear, 'clear: 清空后 isEmpty 应该返回 true')

  // 测试不存在的 key
  const notFound = await get(STORE_NAMES.CONFIG, 'nonexistent')
  assertEqual(notFound, null, 'get: 不存在的 key 应该返回 null')
}

// ============ 备份测试 ============
async function testBackup() {
  console.log('\n💾 Testing backup module...')

  // 清理
  clearModuleBackups('test_module')

  // 测试创建备份
  const testData = { config: { theme: 'dark' }, plans: { work: true } }
  await createBackup('test_module', testData)

  // 等待防抖
  await new Promise(resolve => setTimeout(resolve, 100))

  // 测试获取备份
  const backups = getBackups('test_module')
  assert(backups.length >= 1, `createBackup: 应该创建至少1个备份 (got ${backups.length})`)

  // 测试备份数据完整性
  if (backups.length > 0) {
    const backup = backups[0]
    assertEqual(backup.module, 'test_module', 'backup.module: 模块名应该匹配')
    assertEqual(backup.data, testData, 'backup.data: 备份数据应该与原始数据一致')
    assert(!!backup.timestamp, 'backup.timestamp: 应该有创建时间')
  }

  // 测试获取所有备份
  const allBackups = getAllBackups()
  assert(allBackups.length >= 1, `getAllBackups: 应该返回所有备份 (got ${allBackups.length})`)

  // 测试最大备份数量限制
  clearModuleBackups('test_max')
  for (let i = 0; i < 15; i++) {
    await createBackup('test_max', { index: i })
    await new Promise(resolve => setTimeout(resolve, 50))
  }
  const maxBackups = getBackups('test_max')
  assert(maxBackups.length <= 10, `MAX_BACKUPS: 最多保留10个备份 (got ${maxBackups.length})`)

  // 清理
  clearModuleBackups('test_module')
  clearModuleBackups('test_max')
}

// ============ 迁移测试 ============
async function testMigration() {
  console.log('\n🔄 Testing migration module...')

  // 清理 localStorage 中的迁移标记
  localStorage.removeItem('efflife_db_migration_done')

  // 在 localStorage 中写入测试数据
  localStorage.setItem('efflife_config', JSON.stringify({ theme: 'light', test: true }))
  localStorage.setItem('efflife_plans', JSON.stringify({ work: { plan_type: '切分制' } }))

  // 清理 IndexedDB 中的对应数据
  await clear(STORE_NAMES.CONFIG)
  await clear(STORE_NAMES.PLANS)

  // 运行迁移
  const result = await runMigration()
  assert(result.success, `runMigration: 应该成功迁移 (errors: ${result.errors.join(', ')})`)
  assert(result.migrated.includes('config'), 'runMigration: 应该迁移 config')
  assert(result.migrated.includes('plans'), 'runMigration: 应该迁移 plans')

  // 验证 IndexedDB 中有数据
  const configData = await get(STORE_NAMES.CONFIG, 'config')
  assert(configData !== null, 'migration: config 应该已迁移到 IndexedDB')

  const plansData = await get(STORE_NAMES.PLANS, 'plans')
  assert(plansData !== null, 'migration: plans 应该已迁移到 IndexedDB')

  // 验证迁移标记
  assert(isMigrationDone(), 'isMigrationDone: 迁移后应该返回 true')

  // 再次运行迁移应该是 no-op
  const result2 = await runMigration()
  assertEqual(result2.migrated.length, 0, 'runMigration: 重复运行应该没有迁移')

  // 测试 hasLocalStorageData
  assert(hasLocalStorageData(), 'hasLocalStorageData: localStorage 有数据时应该返回 true')

  // 测试 hasIndexedDBData
  const idbHasData = await hasIndexedDBData()
  assert(idbHasData, 'hasIndexedDBData: IndexedDB 有数据时应该返回 true')

  // 清理测试数据
  localStorage.removeItem('efflife_config')
  localStorage.removeItem('efflife_plans')
}

// ============ 恢复测试 ============
async function testRecovery() {
  console.log('\n🛡️ Testing recovery module...')

  // 测试数据完整性检查
  const status = await checkDataIntegrity()
  assert(typeof status.localStorageEmpty === 'boolean', 'checkDataIntegrity: 应该返回 localStorageEmpty')
  assert(typeof status.indexedDBEmpty === 'boolean', 'checkDataIntegrity: 应该返回 indexedDBEmpty')
  assert(typeof status.hasBackups === 'boolean', 'checkDataIntegrity: 应该返回 hasBackups')

  // 测试恢复建议
  const suggestions = await getRecoverySuggestions()
  assert(Array.isArray(suggestions), 'getRecoverySuggestions: 应该返回数组')
  assert(suggestions.length > 0, 'getRecoverySuggestions: 应该至少有一个建议')

  // 测试紧急备份
  const emergencyBackup = await exportEmergencyBackup()
  assert(typeof emergencyBackup === 'string', 'exportEmergencyBackup: 应该返回 JSON 字符串')
  assert(emergencyBackup.length > 0, 'exportEmergencyBackup: 不应该为空')

  // 验证 JSON 格式
  try {
    const parsed = JSON.parse(emergencyBackup)
    assert(typeof parsed === 'object', 'exportEmergencyBackup: 应该返回有效的 JSON 对象')
  } catch {
    assert(false, 'exportEmergencyBackup: 应该返回有效的 JSON')
  }

  // 测试从紧急备份恢复
  const restoreResult = await restoreFromEmergencyBackup(emergencyBackup)
  assert(restoreResult.success, `restoreFromEmergencyBackup: 应该成功恢复 (${restoreResult.message})`)

  // 测试从最新备份恢复（需要先有备份）
  await createBackup('recovery_test', { test: 'data' })
  const latestResult = await restoreFromLatestBackup()
  // 可能成功也可能没有备份
  assert(typeof latestResult.success === 'boolean', 'restoreFromLatestBackup: 应该返回 success')
  assert(typeof latestResult.message === 'string', 'restoreFromLatestBackup: 应该返回 message')

  // 清理
  clearModuleBackups('recovery_test')
}

// ============ 数据完整性测试 ============
async function testDataIntegrity() {
  console.log('\n🔍 Testing data integrity...')

  // 测试配置数据写入和读取
  const testConfig = {
    overtime_threshold: 105,
    whiten_k: 0.6,
    show_seconds: true,
    use_24h: true,
    show_ampm: false,
    theme: { type: 'forest' },
  }
  await set(STORE_NAMES.CONFIG, 'integrity_test', testConfig)
  const readConfig = await get(STORE_NAMES.CONFIG, 'integrity_test')
  assertEqual(readConfig, testConfig, '数据完整性: 配置数据应该完全一致')

  // 测试记录数据
  const testRecords = [
    { date: '2024-01-01', start: '09:00', end: '11:00', duration: 2, content: '测试', tag: '工作' },
    { date: '2024-01-01', start: '14:00', end: '16:00', duration: 2, content: '测试2', tag: '学习' },
  ]
  await set(STORE_NAMES.RECORDS, '2024-01-01', testRecords)
  const readRecords = await get(STORE_NAMES.RECORDS, '2024-01-01')
  assertEqual(readRecords, testRecords, '数据完整性: 记录数据应该完全一致')

  // 测试备份后恢复的数据完整性
  await createBackup('integrity_test', testConfig)
  await new Promise(resolve => setTimeout(resolve, 100))
  const backups = getBackups('integrity_test')
  if (backups.length > 0) {
    const backup = backups[0]
    assertEqual(backup.data, testConfig, '数据完整性: 备份数据应该完全一致')
  }

  // 清理
  await del(STORE_NAMES.CONFIG, 'integrity_test')
  await del(STORE_NAMES.RECORDS, '2024-01-01')
  clearModuleBackups('integrity_test')
}

// ============ 运行所有测试 ============
export async function runAllTests() {
  console.log('🚀 开始运行存储层测试...\n')
  console.log('='.repeat(50))

  try {
    await testIndexedDB()
    await testBackup()
    await testMigration()
    await testRecovery()
    await testDataIntegrity()
  } catch (e) {
    console.error('💥 测试运行出错:', e)
    failed++
    errors.push(`测试运行出错: ${(e as Error).message}`)
  }

  console.log('\n' + '='.repeat(50))
  console.log(`\n📊 测试结果: ${passed} 通过, ${failed} 失败`)

  if (errors.length > 0) {
    console.log('\n❌ 失败的测试:')
    errors.forEach(e => console.log(`  - ${e}`))
  } else {
    console.log('\n✅ 所有测试通过！')
  }

  return { passed, failed, errors }
}

// 如果在浏览器中直接运行
if (typeof window !== 'undefined') {
  (window as any).runStorageTests = runAllTests
  console.log('💡 运行测试: 在控制台输入 runStorageTests()')
}
