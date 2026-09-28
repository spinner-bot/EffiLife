<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { ArrowLeft, ChevronRight, Mail, Copy, BarChart3, CalendarDays, Target, Flame, BellRing, Music2, Palette, HardDrive } from 'lucide-vue-next'
import type { Config, ThemeType, SolidThemeConfig, GradientThemeConfig, GlassThemeConfig, NeonThemeConfig } from '@/types'
import { GuideManager } from '@/guide'
import { APP_VERSION, getBuildInfo, isDevVersion, VERSION_HISTORY } from '@/version'
import { exportArchive, importArchive, importArchiveWithDialog, resetData, getDataStats, type ResetType } from '@/services/ArchiveService'
import { getAllBackups, restoreFromSpecificBackup, checkDataIntegrity, exportEmergencyBackup, type BackupData, type DataStatus } from '@/storage'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import LocaleSwitcher from '@/components/LocaleSwitcher.vue'
import HelpCenterPanel from '@/components/HelpCenterPanel.vue'
import RecoveryPanel from '@/components/RecoveryPanel.vue'
import { useI18n } from '@/i18n'
import { getPlanRuntime } from '@/services/runtimeCapabilities'
import { importLegacyTodoPayload } from '@/services/todoService'

const appVersion = APP_VERSION
const buildInfo = getBuildInfo()
const isDev = isDevVersion

// 加载状态（用于骨架屏）
const isLoading = ref(true)

// ============ 引导功能 ============
function startGuide() {
  // 重置引导状态并启动
  GuideManager.resetCompleted()
  router.push('/')
  setTimeout(() => {
    GuideManager.startGuide()
  }, 300)

}

// ============ 反馈功能 ============
const FEEDBACK_EMAIL = 'langxibielangle@qq.com'
const copySuccess = ref(false)

// 检测是否在移动端
function isMobileDevice(): boolean {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

async function openEmailClient() {
  const subject = encodeURIComponent(t('settings.feedback.emailSubject'))
  const body = encodeURIComponent(t('settings.feedback.emailBody', { version: appVersion }))
  const mailto = `mailto:${FEEDBACK_EMAIL}?subject=${subject}&body=${body}`

  // 移动端直接使用 window.location
  if (isMobileDevice()) {
    window.location.href = mailto
    return
  }

  // 桌面端尝试使用 Tauri shell
  try {
    const { open } = await import('@tauri-apps/plugin-shell')
    await open(mailto)
  } catch (e) {
    // fallback: 使用 window.location
    try {
      window.location.href = mailto
    } catch {
      // 最后 fallback: 复制到剪贴板
      await copyEmail()
      alert(t('settings.feedback.emailCopied'))
    }
  }
}

async function copyEmail() {
  try {
    await navigator.clipboard.writeText(FEEDBACK_EMAIL)
    copySuccess.value = true
    setTimeout(() => { copySuccess.value = false }, 2000)
  } catch (e) {
    alert(t('settings.feedback.copyFailed'))
  }
}

const router = useRouter()
const appStore = useAppStore()
const { t } = useI18n()
const isMobilePlanRuntime = getPlanRuntime() === 'mobile-unavailable'

const config = computed(() => appStore.config)

// 当前视图
type ViewType = 'main' | 'custom' | 'theme' | 'help' | 'legacy-help' | 'archive' | 'reset' | 'feedback' | 'version-info' | 'more' | 'restore' | 'legacy-recovery'
const currentView = ref<ViewType>('main')
// 导航历史栈（用于返回上一级）
const viewHistory = ref<ViewType[]>(['main'])

// 导航到指定视图（记录历史）
function navigateTo(view: ViewType) {
  viewHistory.value.push(view)
  currentView.value = view
  if (view === 'restore') loadDataStatus()
}

// 返回上一级
async function goBack() {
  if (currentView.value === 'theme' && themeDirty.value) {
    const shouldSave = confirm(t('settings.theme.unsavedConfirm'))
    if (shouldSave) await saveTheme()
    else await discardThemeChanges()
  }
  if (viewHistory.value.length > 1) {
    viewHistory.value.pop()
    currentView.value = viewHistory.value[viewHistory.value.length - 1]
  } else {
    router.push('/')
  }
}

// ============ 自定义设置 ============
const overtimeThreshold = ref(config.value.overtime_threshold)
const showSeconds = ref(config.value.show_seconds)
const use24h = ref(config.value.use_24h)
const showAmPm = ref(config.value.show_ampm)

async function saveCustomSettings() {
  const newConfig: Config = {
    ...config.value,
    overtime_threshold: overtimeThreshold.value,
    show_seconds: showSeconds.value,
    use_24h: use24h.value,
    show_ampm: showAmPm.value
  }
  await appStore.saveConfig(newConfig)
  alert(t('settings.saved'))
}

function addThreshold() {
  if (overtimeThreshold.value < 150) overtimeThreshold.value++
}

function subThreshold() {
  if (overtimeThreshold.value > 100) overtimeThreshold.value--
}

// ============ 主题设置 ============
const themeType = ref<ThemeType>(config.value.theme.type || 'solid')

const solidConfig = ref<SolidThemeConfig>(config.value.theme.solid || {
  bg_window: '#f0f0f0',
  bg_button: '#e0e0e0',
  fg_button: '#000000',
  bg_frame: '#d9d9d9'
})

const gradientConfig = ref<GradientThemeConfig>(config.value.theme.gradient || {
  color_start: '#667eea',
  color_end: '#764ba2',
  direction: 'to-br',
  fg_button: '#ffffff',
  card_bg: 'rgba(255, 255, 255, 0.15)'
})

const glassConfig = ref<GlassThemeConfig>(config.value.theme.glass || {
  bg_color: '#1a1a2e',
  glass_opacity: 0.1,
  blur_amount: 10,
  fg_button: '#ffffff',
  border_color: 'rgba(255, 255, 255, 0.2)'
})

const neonConfig = ref<NeonThemeConfig>(config.value.theme.neon || {
  bg_color: '#0a0a0f',
  neon_color: '#00ff88',
  glow_intensity: 10,
  fg_button: '#00ff88',
  accent_color: '#ff00ff'
})

function cloneTheme(theme: Config['theme']): Config['theme'] {
  return JSON.parse(JSON.stringify(theme)) as Config['theme']
}

const savedThemeSnapshot = ref<Config['theme']>(cloneTheme(config.value.theme))

function buildDraftTheme(): Config['theme'] {
  return {
    type: themeType.value,
    solid: solidConfig.value,
    gradient: gradientConfig.value,
    glass: glassConfig.value,
    neon: neonConfig.value,
  }
}

const themeDirty = computed(() =>
  JSON.stringify(buildDraftTheme()) !== JSON.stringify(savedThemeSnapshot.value)
)

function previewTheme() {
  const theme = buildDraftTheme()
  if (JSON.stringify(theme) !== JSON.stringify(config.value.theme)) {
    appStore.previewConfig({ ...config.value, theme })
  }
}

async function discardThemeChanges() {
  const restored = cloneTheme(savedThemeSnapshot.value)
  appStore.previewConfig({ ...config.value, theme: restored })
  themeType.value = restored.type
  if (restored.solid) solidConfig.value = { ...restored.solid }
  if (restored.gradient) gradientConfig.value = { ...restored.gradient }
  if (restored.glass) glassConfig.value = { ...restored.glass }
  if (restored.neon) neonConfig.value = { ...restored.neon }
}

// 所有可用主题
const availableThemes = [
  // 基础主题
  { type: 'solid' as ThemeType, name: '纯色', description: '简洁的纯色主题', category: '基础' },
  { type: 'gradient' as ThemeType, name: '渐变', description: '渐变背景主题', category: '基础' },
  { type: 'glass' as ThemeType, name: '玻璃', description: '毛玻璃效果主题', category: '基础' },
  { type: 'neon' as ThemeType, name: '霓虹', description: '霓虹灯效果主题', category: '基础' },
  // 高级主题
  { type: 'ink' as ThemeType, name: '水墨', description: '中国水墨画风格，动态墨点晕染', category: '艺术' },
  { type: 'vintage' as ThemeType, name: '画报', description: '复古画报风格，装饰花纹边框', category: '艺术' },
  { type: 'cyberpunk' as ThemeType, name: '赛博朋克', description: '未来科技风，网格扫描线效果', category: '科技' },
  { type: 'pixel' as ThemeType, name: '像素', description: '复古像素风格，星星月亮', category: '艺术' },
  { type: 'aurora' as ThemeType, name: '极光', description: '北极光效果，流动彩光', category: '自然' },
  { type: 'sakura' as ThemeType, name: '樱花', description: '日式樱花风格，飘落花瓣', category: '自然' },
  { type: 'ocean' as ThemeType, name: '深海', description: '深海探索风格，气泡上升', category: '自然' },
  { type: 'forest' as ThemeType, name: '森林', description: '神秘森林风格，萤火虫飞舞', category: '自然' },
  // 新主题
  { type: 'midnight_library' as ThemeType, name: '午夜图书馆', description: '烛光书香，书架与飘动书页', category: '艺术' },
  { type: 'star_voyage' as ThemeType, name: '星际航行', description: '星海遨游，星云旋转飞船轨迹', category: '科技' },
  { type: 'rainy_city' as ThemeType, name: '雨夜城市', description: '霓虹倒影，雨滴滑落天际线', category: '自然' },
  { type: 'desert_dusk' as ThemeType, name: '沙漠黄昏', description: '落日余晖，多层沙丘与飘沙', category: '自然' },
  { type: 'bamboo_dawn' as ThemeType, name: '竹林清晨', description: '晨雾竹林，摇曳竹影与露珠', category: '自然' },
  // 顶级主题
  { type: 'nordic_polar_night' as ThemeType, name: '北欧极夜', description: '极光流动雪粒飘落，远处小屋灯光闪烁', category: '自然' },
  { type: 'japanese_garden' as ThemeType, name: '日式庭院', description: '枯山水波纹，樱花瓣飘落，纸灯笼微光', category: '艺术' },
  { type: 'victorian_study' as ThemeType, name: '维多利亚书房', description: '壁炉火焰，灰尘粒子光束中，书香怀旧', category: '艺术' },
  { type: 'underwater_temple' as ThemeType, name: '海底神殿', description: '光线穿透深海，气泡上升，水草摇曳鱼群游过', category: '自然' },
]

const themeMeta: Partial<Record<ThemeType, { nameKey: string; descriptionKey: string; categoryKey: string }>> = {
  solid: { nameKey: 'theme.name.solid', descriptionKey: 'theme.desc.solid', categoryKey: 'theme.category.basic' },
  gradient: { nameKey: 'theme.name.gradient', descriptionKey: 'theme.desc.gradient', categoryKey: 'theme.category.basic' },
  glass: { nameKey: 'theme.name.glass', descriptionKey: 'theme.desc.glass', categoryKey: 'theme.category.basic' },
  neon: { nameKey: 'theme.name.neon', descriptionKey: 'theme.desc.neon', categoryKey: 'theme.category.basic' },
  ink: { nameKey: 'theme.name.ink', descriptionKey: 'theme.desc.ink', categoryKey: 'theme.category.art' },
  vintage: { nameKey: 'theme.name.vintage', descriptionKey: 'theme.desc.vintage', categoryKey: 'theme.category.art' },
  pixel: { nameKey: 'theme.name.pixel', descriptionKey: 'theme.desc.pixel', categoryKey: 'theme.category.art' },
  midnight_library: { nameKey: 'theme.name.midnightLibrary', descriptionKey: 'theme.desc.midnightLibrary', categoryKey: 'theme.category.art' },
  japanese_garden: { nameKey: 'theme.name.japaneseGarden', descriptionKey: 'theme.desc.japaneseGarden', categoryKey: 'theme.category.art' },
  victorian_study: { nameKey: 'theme.name.victorianStudy', descriptionKey: 'theme.desc.victorianStudy', categoryKey: 'theme.category.art' },
  aurora: { nameKey: 'theme.name.aurora', descriptionKey: 'theme.desc.aurora', categoryKey: 'theme.category.nature' },
  sakura: { nameKey: 'theme.name.sakura', descriptionKey: 'theme.desc.sakura', categoryKey: 'theme.category.nature' },
  ocean: { nameKey: 'theme.name.ocean', descriptionKey: 'theme.desc.ocean', categoryKey: 'theme.category.nature' },
  forest: { nameKey: 'theme.name.forest', descriptionKey: 'theme.desc.forest', categoryKey: 'theme.category.nature' },
  rainy_city: { nameKey: 'theme.name.rainyCity', descriptionKey: 'theme.desc.rainyCity', categoryKey: 'theme.category.nature' },
  desert_dusk: { nameKey: 'theme.name.desertDusk', descriptionKey: 'theme.desc.desertDusk', categoryKey: 'theme.category.nature' },
  bamboo_dawn: { nameKey: 'theme.name.bambooDawn', descriptionKey: 'theme.desc.bambooDawn', categoryKey: 'theme.category.nature' },
  nordic_polar_night: { nameKey: 'theme.name.nordicPolarNight', descriptionKey: 'theme.desc.nordicPolarNight', categoryKey: 'theme.category.nature' },
  underwater_temple: { nameKey: 'theme.name.underwaterTemple', descriptionKey: 'theme.desc.underwaterTemple', categoryKey: 'theme.category.nature' },
  cyberpunk: { nameKey: 'theme.name.cyberpunk', descriptionKey: 'theme.desc.cyberpunk', categoryKey: 'theme.category.tech' },
  star_voyage: { nameKey: 'theme.name.starVoyage', descriptionKey: 'theme.desc.starVoyage', categoryKey: 'theme.category.tech' },
  tech: { nameKey: 'theme.name.tech', descriptionKey: 'theme.desc.tech', categoryKey: 'theme.category.tech' },
}

function themeMetaFor(theme: { type: ThemeType }) {
  return themeMeta[theme.type] || { nameKey: theme.type, descriptionKey: theme.type, categoryKey: 'theme.category.basic' }
}

function themeCategory(theme: { type: ThemeType }): string {
  return themeMetaFor(theme).categoryKey
}

function themeName(theme: { type: ThemeType }): string {
  return t(themeMetaFor(theme).nameKey)
}

function themeDescription(theme: { type: ThemeType }): string {
  return t(themeMetaFor(theme).descriptionKey)
}

async function saveTheme() {
  const newConfig: Config = {
    ...config.value,
    theme: buildDraftTheme()
  }
  await appStore.saveConfig(newConfig)
  savedThemeSnapshot.value = cloneTheme(newConfig.theme)
}

// 纯色预设
function applySolidPreset(preset: 'default' | 'dark' | 'light') {
  if (preset === 'default') {
    solidConfig.value = { bg_window: '#f0f0f0', bg_button: '#e0e0e0', fg_button: '#000000', bg_frame: '#d9d9d9' }
  } else if (preset === 'dark') {
    solidConfig.value = { bg_window: '#1a1a2e', bg_button: '#16213e', fg_button: '#eaeaea', bg_frame: '#0f3460' }
  } else {
    solidConfig.value = { bg_window: '#ffffff', bg_button: '#f5f5f5', fg_button: '#333333', bg_frame: '#e0e0e0' }
  }
}

// 渐变预设
function applyGradientPreset(preset: 'purple' | 'blue' | 'sunset' | 'forest') {
  const presets = {
    purple: { color_start: '#667eea', color_end: '#764ba2', direction: 'to-br' as const },
    blue: { color_start: '#2193b0', color_end: '#6dd5ed', direction: 'to-right' as const },
    sunset: { color_start: '#ff6b6b', color_end: '#feca57', direction: 'to-br' as const },
    forest: { color_start: '#134e5e', color_end: '#71b280', direction: 'to-bottom' as const },
  }
  const p = presets[preset]
  gradientConfig.value = { ...gradientConfig.value, ...p }
}

// 玻璃预设
function applyGlassPreset(preset: 'dark' | 'light' | 'blue') {
  const presets = {
    dark: { bg_color: '#1a1a2e', glass_opacity: 0.1, blur_amount: 10 },
    light: { bg_color: '#f0f0f0', glass_opacity: 0.3, blur_amount: 8 },
    blue: { bg_color: '#0c1445', glass_opacity: 0.15, blur_amount: 12 },
  }
  const p = presets[preset]
  glassConfig.value = { ...glassConfig.value, ...p }
}

// 霓虹预设
function applyNeonPreset(preset: 'green' | 'pink' | 'cyan' | 'rainbow') {
  const presets = {
    green: { bg_color: '#0a0a0f', neon_color: '#00ff88', glow_intensity: 10, accent_color: '#ff00ff' },
    pink: { bg_color: '#0f0a1a', neon_color: '#ff69b4', glow_intensity: 12, accent_color: '#00ffff' },
    cyan: { bg_color: '#0a0f1a', neon_color: '#00ffff', glow_intensity: 8, accent_color: '#ff6b6b' },
    rainbow: { bg_color: '#0a0a0f', neon_color: '#ff00ff', glow_intensity: 15, accent_color: '#00ff88' },
  }
  const p = presets[preset]
  neonConfig.value = { ...neonConfig.value, ...p }
}

// 颜色选择器
function pickColor(target: string) {
  const input = document.createElement('input')
  input.type = 'color'

  let currentValue = '#000000'
  const key = target.includes('_') ? target.split('_').slice(1).join('_') : target

  if (target.startsWith('solid_')) {
    currentValue = (solidConfig.value as unknown as Record<string, string>)[key] || '#000000'
  } else if (target.startsWith('gradient_')) {
    currentValue = (gradientConfig.value as unknown as Record<string, string>)[key] || '#000000'
  } else if (target.startsWith('glass_')) {
    currentValue = (glassConfig.value as unknown as Record<string, string>)[key] || '#000000'
  } else if (target.startsWith('neon_')) {
    currentValue = (neonConfig.value as unknown as Record<string, string>)[key] || '#000000'
  }

  input.value = currentValue
  input.onchange = () => {
    const color = input.value
    if (target.startsWith('solid_')) {
      (solidConfig.value as unknown as Record<string, string>)[key] = color
    } else if (target.startsWith('gradient_')) {
      (gradientConfig.value as unknown as Record<string, string>)[key] = color
    } else if (target.startsWith('glass_')) {
      (glassConfig.value as unknown as Record<string, string>)[key] = color
    } else if (target.startsWith('neon_')) {
      (neonConfig.value as unknown as Record<string, string>)[key] = color
    }
  }
  input.click()
}

// ============ 恢复设置 ============
const dataStats = ref({
  recordDays: 0,
  totalRecords: 0,
  hasConfig: false,
  hasPlans: false,
  eventPlanCount: 0,
  hasAudioSettings: false,
  hasEventSettings: false,
  hasCheckin: false,
})

async function handleReset(type: ResetType) {
  const messages: Record<ResetType, string> = {
    all: t('settings.reset.confirmAll'),
    records: t('settings.reset.confirmRecords'),
    plans: t('settings.reset.confirmPlans'),
    config: t('settings.reset.confirmConfig'),
    settings: t('settings.reset.confirmSettings'),
  }

  if (!confirm(messages[type])) return
  await resetData(type)
}

// ============ 存档管理 ============
// 文件选择输入框引用
const fileInputRef = ref<HTMLInputElement | null>(null)
const legacyTodoInputRef = ref<HTMLInputElement | null>(null)

async function handleExportArchive() {
  try {
    const result = await exportArchive()
    if (result.success) {
      if (result.path) {
          alert(`${t('settings.archive.savedTo')}\n${result.path}${result.warning ? `\n\n${t('settings.archive.warning')}${result.warning}` : ''}`)
      } else {
          alert(`${t('settings.archive.downloaded')}${result.warning ? `\n\n${t('settings.archive.warning')}${result.warning}` : ''}`)
      }
    }
  } catch (e) {
    alert(t('settings.archive.exportFailed') + (e as Error).message)
  }
}

async function handleImportArchive() {
  // 检测是否在 Tauri 环境
  if ((window as any).__TAURI__) {
    // Tauri 环境：使用原生文件对话框
    const result = await importArchiveWithDialog(() => confirm(t('settings.archive.importConfirm')))
    if (result.cancelled) return
    if (result.success) {
      if (confirm(result.message + '\n\n' + t('settings.archive.reloadConfirm'))) {
        window.location.reload()
      }
    } else {
      alert(result.message)
    }
  } else {
    // 浏览器环境：使用文件选择器
    if (fileInputRef.value) {
      fileInputRef.value.click()
    }
  }
}

async function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // 重置 input 以便可以再次选择同一文件
  input.value = ''

  if (!confirm(t('settings.archive.importConfirm'))) return

  const result = await importArchive(file)
  alert(result.message)

  if (result.success) {
    // 刷新页面以应用更改
    window.location.reload()
  }
}

// ============ 数据恢复 ============
function openLegacyTodoImport() {
  legacyTodoInputRef.value?.click()
}

async function onLegacyTodoSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (!confirm(t('settings.archive.legacyTodoImportConfirm'))) return
  try {
    const result = await importLegacyTodoPayload(await file.text())
    alert(t('settings.archive.legacyTodoImportSuccess', result))
    window.location.reload()
  } catch (error) {
    alert(t('settings.archive.legacyTodoImportFailed') + (error as Error).message)
  }
}

const backupsList = ref<BackupData[]>([])
const dataStatus = ref<DataStatus | null>(null)

async function loadDataStatus() {
  try {
    const status = await checkDataIntegrity()
    dataStatus.value = status
    backupsList.value = getAllBackups()
  } catch (e) {
    console.error('Failed to load data status:', e)
  }
}

async function handleRestoreBackup(backup: BackupData) {
  if (!confirm(`${t('settings.restore.confirmPrefix')}${new Date(backup.timestamp).toLocaleString()}${t('settings.restore.confirmSuffix')}`)) {
    return
  }

  try {
    const result = await restoreFromSpecificBackup(backup)
    if (result.success) {
      alert(result.message + '\n\n' + t('settings.archive.reloadConfirm'))
      if (confirm(t('settings.archive.reloadNow'))) {
        window.location.reload()
      }
    } else {
      alert(result.message)
    }
  } catch (e) {
    alert(t('settings.restore.failed') + (e as Error).message)
  }
}

async function handleEmergencyExport() {
  try {
    const jsonStr = await exportEmergencyBackup()
    const blob = new Blob([jsonStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `efflife_emergency_${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
    alert(t('settings.restore.emergencyDownloaded'))
  } catch (e) {
    alert(t('settings.archive.exportFailed') + (e as Error).message)
  }
}

// 同步配置到本地状态
watch(() => config.value, (newConfig) => {
  overtimeThreshold.value = newConfig.overtime_threshold
  showSeconds.value = newConfig.show_seconds
  use24h.value = newConfig.use_24h
  showAmPm.value = newConfig.show_ampm
  themeType.value = newConfig.theme.type || 'solid'
  if (newConfig.theme.solid) solidConfig.value = { ...newConfig.theme.solid }
  if (newConfig.theme.gradient) gradientConfig.value = { ...newConfig.theme.gradient }
  if (newConfig.theme.glass) glassConfig.value = { ...newConfig.theme.glass }
  if (newConfig.theme.neon) neonConfig.value = { ...newConfig.theme.neon }
}, { immediate: true, deep: true })

watch([themeType, solidConfig, gradientConfig, glassConfig, neonConfig], previewTheme, { deep: true })

// 初始化完成后关闭加载状态
onMounted(async () => {
  dataStats.value = await getDataStats()
  // 短暂延迟以展示骨架屏过渡效果
  setTimeout(() => {
    isLoading.value = false
  }, 300)

  // 检查数据完整性
  try {
    const status = await checkDataIntegrity()
    if (status.localStorageEmpty && status.indexedDBEmpty) {
      // 数据都为空，检查是否有备份
      if (status.hasBackups) {
        if (confirm(t('settings.restore.emptyWithBackups'))) {
          navigateTo('restore')
        }
      }
    }
  } catch {
    // ignore
  }
})
</script>

<template>
  <div class="settings-view">
    <header class="header">
      <button class="back-btn" @click="goBack">
        <ArrowLeft :size="16" />
        <span>{{ t('settings.back') }}</span>
      </button>
      <h1>{{ t('settings.title') }}</h1>
    </header>

    <main class="main-content">
      <!-- 加载骨架屏 -->
      <SkeletonLoader v-if="isLoading" type="list" :count="6" />

      <!-- 主视图 -->
      <template v-else-if="currentView === 'main'">
        <div class="settings-locale-row">
          <LocaleSwitcher />
        </div>
        <div class="settings-list">
          <button class="settings-item" @click="navigateTo('custom')">
            <span>{{ t('settings.custom') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="navigateTo('theme')">
            <span>{{ t('settings.theme.title') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="router.push('/audio-settings')">
            <span>{{ t('settings.audio') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="router.push('/motion-settings')">
            <span>{{ t('settings.motion') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="router.push('/event-manager')">
            <span>{{ t('settings.events') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="navigateTo('archive')">
            <span>{{ t('settings.archive.title') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="navigateTo('restore')">
            <span>{{ t('settings.restore.title') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="navigateTo('more')">
            <span>{{ t('settings.more') }}</span>
            <ChevronRight :size="16" />
          </button>
        </div>

        <footer class="credits">
          <p class="version">浪兮效率时钟 v{{ appVersion }}</p>
          <p class="build-info" :class="{ dev: isDev }">{{ buildInfo }}</p>
          <p>开发者：浪兮spinner_bot</p>
          <p>抖音@浪兮有点浪</p>
        </footer>
      </template>

      <!-- 自定义设置 -->
      <template v-else-if="currentView === 'custom'">
        <h2>{{ t('settings.customTitle') }}</h2>

        <div class="form-section">
          <label>{{ t('settings.threshold') }}</label>
          <div class="threshold-control">
            <button class="threshold-btn" @click="subThreshold">-</button>
            <span class="threshold-value">{{ t('settings.currentThreshold') }}：{{ overtimeThreshold }}%</span>
            <button class="threshold-btn" @click="addThreshold">+</button>
          </div>
        </div>

        <div class="form-section">
          <label>{{ t('settings.timeDisplay') }}</label>
          <div class="checkbox-list">
            <label><input type="checkbox" v-model="showSeconds" /><span>{{ t('settings.showSeconds') }}</span></label>
            <label><input type="checkbox" v-model="use24h" /><span>{{ t('settings.use24h') }}</span></label>
            <label><input type="checkbox" v-model="showAmPm" /><span>{{ t('settings.showAmPm') }}</span></label>
          </div>
        </div>

        <div class="form-actions">
          <button class="btn secondary" @click="goBack">{{ t('settings.back') }}</button>
          <button class="btn primary" @click="saveCustomSettings">{{ t('settings.save') }}</button>
        </div>
      </template>

      <!-- 主题设置 -->
      <template v-else-if="currentView === 'theme'">
        <h2>{{ t('settings.theme.title') }}</h2>

        <div class="form-section">
          <label>{{ t('theme.category.basic') }}</label>
          <div class="theme-list">
            <button
              v-for="theme in availableThemes.filter(theme => themeCategory(theme) === 'theme.category.basic')"
              :key="theme.type"
              class="theme-card"
              :class="{ active: themeType === theme.type }"
              @click="themeType = theme.type"
            >
              <div class="theme-info">
                <span class="theme-name">{{ themeName(theme) }}</span>
                <span class="theme-desc">{{ themeDescription(theme) }}</span>
              </div>
              <span v-if="themeType === theme.type" class="selected">✓</span>
            </button>
          </div>
        </div>

        <div class="form-section">
          <label>{{ t('theme.category.art') }}</label>
          <div class="theme-list">
            <button
              v-for="theme in availableThemes.filter(theme => themeCategory(theme) === 'theme.category.art')"
              :key="theme.type"
              class="theme-card"
              :class="{ active: themeType === theme.type }"
              @click="themeType = theme.type"
            >
              <div class="theme-info">
                <span class="theme-name">{{ themeName(theme) }}</span>
                <span class="theme-desc">{{ themeDescription(theme) }}</span>
              </div>
              <span v-if="themeType === theme.type" class="selected">✓</span>
            </button>
          </div>
        </div>

        <div class="form-section">
          <label>{{ t('theme.category.nature') }}</label>
          <div class="theme-list">
            <button
              v-for="theme in availableThemes.filter(theme => themeCategory(theme) === 'theme.category.nature')"
              :key="theme.type"
              class="theme-card"
              :class="{ active: themeType === theme.type }"
              @click="themeType = theme.type"
            >
              <div class="theme-info">
                <span class="theme-name">{{ themeName(theme) }}</span>
                <span class="theme-desc">{{ themeDescription(theme) }}</span>
              </div>
              <span v-if="themeType === theme.type" class="selected">✓</span>
            </button>
          </div>
        </div>

        <div class="form-section">
          <label>{{ t('theme.category.tech') }}</label>
          <div class="theme-list">
            <button
              v-for="theme in availableThemes.filter(theme => themeCategory(theme) === 'theme.category.tech')"
              :key="theme.type"
              class="theme-card"
              :class="{ active: themeType === theme.type }"
              @click="themeType = theme.type"
            >
              <div class="theme-info">
                <span class="theme-name">{{ themeName(theme) }}</span>
                <span class="theme-desc">{{ themeDescription(theme) }}</span>
              </div>
              <span v-if="themeType === theme.type" class="selected">✓</span>
            </button>
          </div>
        </div>

        <!-- 纯色主题配置 -->
        <template v-if="themeType === 'solid'">
          <div class="form-section">
            <label>{{ t('settings.theme.colorConfig') }}</label>
            <div class="color-settings">
              <div class="color-row">
                <span>{{ t('settings.theme.windowBackground') }}</span>
                <input type="text" v-model="solidConfig.bg_window" class="color-input" />
                <button class="btn small" @click="pickColor('solid_bg_window')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.buttonBackground') }}</span>
                <input type="text" v-model="solidConfig.bg_button" class="color-input" />
                <button class="btn small" @click="pickColor('solid_bg_button')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.buttonText') }}</span>
                <input type="text" v-model="solidConfig.fg_button" class="color-input" />
                <button class="btn small" @click="pickColor('solid_fg_button')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
            </div>
            <div class="preset-buttons">
              <span>{{ t('settings.theme.presetLabel') }}</span>
              <button class="btn small" @click="applySolidPreset('default')">{{ t('settings.theme.preset.default') }}</button>
              <button class="btn small" @click="applySolidPreset('dark')">{{ t('settings.theme.preset.dark') }}</button>
              <button class="btn small" @click="applySolidPreset('light')">{{ t('settings.theme.preset.light') }}</button>
            </div>
          </div>
        </template>

        <!-- 渐变主题配置 -->
        <template v-if="themeType === 'gradient'">
          <div class="form-section">
            <label>{{ t('settings.theme.gradientConfig') }}</label>
            <div class="color-settings">
              <div class="color-row">
                <span>{{ t('settings.theme.startColor') }}</span>
                <input type="text" v-model="gradientConfig.color_start" class="color-input" />
                <button class="btn small" @click="pickColor('gradient_color_start')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.endColor') }}</span>
                <input type="text" v-model="gradientConfig.color_end" class="color-input" />
                <button class="btn small" @click="pickColor('gradient_color_end')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.gradientDirection') }}</span>
                <select v-model="gradientConfig.direction" class="select-input">
                  <option value="to-right">{{ t('settings.theme.right') }}</option>
                  <option value="to-left">{{ t('settings.theme.left') }}</option>
                  <option value="to-bottom">{{ t('settings.theme.down') }}</option>
                  <option value="to-top">{{ t('settings.theme.up') }}</option>
                  <option value="to-br">{{ t('settings.theme.bottomRight') }}</option>
                  <option value="to-tl">{{ t('settings.theme.topLeft') }}</option>
                </select>
              </div>
            </div>
            <div class="preset-buttons">
              <span>{{ t('settings.theme.presetLabel') }}</span>
              <button class="btn small" @click="applyGradientPreset('purple')">{{ t('settings.theme.preset.purple') }}</button>
              <button class="btn small" @click="applyGradientPreset('blue')">{{ t('settings.theme.preset.blue') }}</button>
              <button class="btn small" @click="applyGradientPreset('sunset')">{{ t('settings.theme.preset.sunset') }}</button>
              <button class="btn small" @click="applyGradientPreset('forest')">{{ t('settings.theme.preset.forest') }}</button>
            </div>
          </div>
        </template>

        <!-- 玻璃主题配置 -->
        <template v-if="themeType === 'glass'">
          <div class="form-section">
            <label>{{ t('settings.theme.glassConfig') }}</label>
            <div class="color-settings">
              <div class="color-row">
                <span>{{ t('settings.theme.backgroundColor') }}</span>
                <input type="text" v-model="glassConfig.bg_color" class="color-input" />
                <button class="btn small" @click="pickColor('glass_bg_color')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.glassOpacity') }}</span>
                <input type="range" v-model.number="glassConfig.glass_opacity" min="0.05" max="0.5" step="0.05" class="slider" />
                <span class="slider-value">{{ glassConfig.glass_opacity.toFixed(2) }}</span>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.blurAmount') }}</span>
                <input type="range" v-model.number="glassConfig.blur_amount" min="0" max="30" step="2" class="slider" />
                <span class="slider-value">{{ glassConfig.blur_amount }}px</span>
              </div>
            </div>
            <div class="preset-buttons">
              <span>{{ t('settings.theme.presetLabel') }}</span>
              <button class="btn small" @click="applyGlassPreset('dark')">{{ t('settings.theme.preset.dark') }}</button>
              <button class="btn small" @click="applyGlassPreset('light')">{{ t('settings.theme.preset.light') }}</button>
              <button class="btn small" @click="applyGlassPreset('blue')">{{ t('settings.theme.preset.blue') }}</button>
            </div>
          </div>
        </template>

        <!-- 霓虹主题配置 -->
        <template v-if="themeType === 'neon'">
          <div class="form-section">
            <label>{{ t('settings.theme.neonConfig') }}</label>
            <div class="color-settings">
              <div class="color-row">
                <span>{{ t('settings.theme.backgroundColor') }}</span>
                <input type="text" v-model="neonConfig.bg_color" class="color-input" />
                <button class="btn small" @click="pickColor('neon_bg_color')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.neonColor') }}</span>
                <input type="text" v-model="neonConfig.neon_color" class="color-input" />
                <button class="btn small" @click="pickColor('neon_neon_color')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.accentColor') }}</span>
                <input type="text" v-model="neonConfig.accent_color" class="color-input" />
                <button class="btn small" @click="pickColor('neon_accent_color')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.glowIntensity') }}</span>
                <input type="range" v-model.number="neonConfig.glow_intensity" min="0" max="30" step="2" class="slider" />
                <span class="slider-value">{{ neonConfig.glow_intensity }}px</span>
              </div>
            </div>
            <div class="preset-buttons">
              <span>{{ t('settings.theme.presetLabel') }}</span>
              <button class="btn small" @click="applyNeonPreset('green')">{{ t('settings.theme.preset.green') }}</button>
              <button class="btn small" @click="applyNeonPreset('pink')">{{ t('settings.theme.preset.pink') }}</button>
              <button class="btn small" @click="applyNeonPreset('cyan')">{{ t('settings.theme.preset.cyan') }}</button>
              <button class="btn small" @click="applyNeonPreset('rainbow')">{{ t('settings.theme.preset.rainbow') }}</button>
            </div>
          </div>
        </template>

        <div class="form-actions">
          <button class="btn secondary" @click="goBack">{{ t('settings.back') }}</button>
          <span class="theme-preview-status">{{ t('settings.theme.previewStatus') }}</span>
        </div>
      </template>

      <!-- 帮助 -->
      <template v-else-if="currentView === 'help'">
        <HelpCenterPanel @back="goBack" />
      </template>

      <template v-else-if="currentView === 'legacy-help'">
        <h2>帮助中心</h2>

        <!-- 快速入门 -->
        <div class="help-section">
          <h3>快速入门</h3>
          <div class="help-steps">
            <div class="help-step">
              <div class="step-number">1</div>
              <div class="step-content">
                <strong>设置日计划</strong>
                <p>进入"管理" → "日计划管理"，创建或选择适合你的计划模板</p>
              </div>
            </div>
            <div class="help-step">
              <div class="step-number">2</div>
              <div class="step-content">
                <strong>记录时间</strong>
                <p>点击"记录"按钮，添加你花费在各项活动上的时间</p>
              </div>
            </div>
            <div class="help-step">
              <div class="step-number">3</div>
              <div class="step-content">
                <strong>查看进度</strong>
                <p>主页实时显示今日完成度，追踪你的效率目标</p>
              </div>
            </div>
            <div class="help-step">
              <div class="step-number">4</div>
              <div class="step-content">
                <strong>每日打卡</strong>
                <p>完成100%计划后，点击打卡按钮记录你的连续成就</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 常见问题 -->
        <div class="help-section">
          <h3>常见问题</h3>
          <details class="faq-item">
            <summary>什么是切分制和分配制？</summary>
            <div class="faq-answer">
              <p><strong>切分制</strong>：将24小时切分为多个时间段，所有时间类别加起来必须等于24小时。适合严格的时间管理。</p>
              <p><strong>分配制</strong>：为每个活动分配目标时长，总时长可以超过或不足24小时。更灵活，适合弹性安排。</p>
            </div>
          </details>
          <details class="faq-item">
            <summary>如何设置自动日程分配？</summary>
            <div class="faq-answer">
              <p>进入"管理" → "日程安排"，可以设置规则让系统自动为每天分配计划。例如：周一到周五使用"工作日"计划，周末使用"休息日"计划。</p>
              <p>规则按优先级排序，系统会从前往后匹配第一条符合的规则。</p>
            </div>
          </details>
          <details class="faq-item">
            <summary>为什么打卡天数没有增加？</summary>
            <div class="faq-answer">
              <p>打卡需要在完成100%计划后，手动点击"打卡"按钮。如果关闭了弹窗或没有点击打卡，天数不会增加。</p>
              <p>另外，如果当天已经打过卡，再次完成计划不会重复计数。</p>
            </div>
          </details>
          <details class="faq-item">
            <summary>如何备份我的数据？</summary>
            <div class="faq-answer">
              <p>进入"设置" → "存档管理" → "导出存档"，可以将所有数据保存为JSON文件。</p>
              <p>建议在更换设备前或重要节点定期备份。</p>
            </div>
          </details>
          <details class="faq-item">
            <summary>背景音乐没有声音？</summary>
            <div class="faq-answer">
              <p>请检查：1) 设置 → 声音 → 启用背景音乐已开启；2) 音量不为0；3) 系统音量正常。</p>
              <p>首次使用可能需要在浏览器中点击页面任意位置激活音频。</p>
            </div>
          </details>
        </div>

        <!-- 功能概览 -->
        <div class="help-section">
          <h3>功能概览</h3>
          <div class="feature-grid">
            <div class="feature-item">
              <span class="feature-icon"><BarChart3 :size="22" /></span>
              <strong>时间统计</strong>
              <p>实时追踪各类别时间分配</p>
            </div>
            <div class="feature-item">
              <span class="feature-icon"><CalendarDays :size="22" /></span>
              <strong>日历视图</strong>
              <p>直观查看历史记录和完成度</p>
            </div>
            <div class="feature-item">
              <span class="feature-icon"><Target :size="22" /></span>
              <strong>计划管理</strong>
              <p>自定义日计划，灵活配置</p>
            </div>
            <div class="feature-item">
              <span class="feature-icon"><Flame :size="22" /></span>
              <strong>打卡系统</strong>
              <p>记录连续完成天数，激励坚持</p>
            </div>
            <div class="feature-item">
              <span class="feature-icon"><BellRing :size="22" /></span>
              <strong>进度预警</strong>
              <p>多时段提醒，防止落后计划</p>
            </div>
            <div class="feature-item">
              <span class="feature-icon"><Music2 :size="22" /></span>
              <strong>环境音效</strong>
              <p>9种背景音乐，专注工作</p>
            </div>
            <div class="feature-item">
              <span class="feature-icon"><Palette :size="22" /></span>
              <strong>主题切换</strong>
              <p>12种主题风格，个性定制</p>
            </div>
            <div class="feature-item">
              <span class="feature-icon"><HardDrive :size="22" /></span>
              <strong>数据备份</strong>
              <p>导出导入，数据永不丢失</p>
            </div>
          </div>
        </div>

        <button class="btn secondary full" @click="goBack">{{ t('settings.back') }}</button>
      </template>

      <!-- 存档管理 -->
      <template v-else-if="currentView === 'archive'">
        <h2>{{ t('settings.archive.title') }}</h2>

        <div v-if="isMobilePlanRuntime" class="archive-capability-note">
          <strong>{{ t('settings.archive.mobilePlanTitle') }}</strong>
          <p>{{ t('settings.archive.mobilePlanDescription') }}</p>
        </div>

        <!-- 数据统计 -->
        <div class="data-stats">
          <h3>{{ t('settings.archive.currentData') }}</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-value">{{ dataStats.recordDays }}</span>
              <span class="stat-label">{{ t('settings.archive.recordDays') }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ dataStats.totalRecords }}</span>
              <span class="stat-label">{{ t('settings.archive.totalRecords') }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ dataStats.hasCheckin ? '✓' : '—' }}</span>
              <span class="stat-label">{{ t('settings.archive.checkinData') }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ dataStats.hasPlans ? '✓' : '—' }}</span>
              <span class="stat-label">{{ t('settings.archive.planData') }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ dataStats.eventPlanCount }}</span>
              <span class="stat-label">{{ t('settings.archive.eventPlanSnapshots') }}</span>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="archive-actions">
          <button class="btn primary full" @click="handleExportArchive">
            {{ t('settings.archive.export') }}
          </button>
          <button class="btn primary full" @click="handleImportArchive">
            {{ t('settings.archive.import') }}
          </button>
          <button class="btn secondary full" @click="openLegacyTodoImport">
            {{ t('settings.archive.importLegacyTodos') }}
          </button>
        </div>

        <!-- 隐藏的文件输入 -->
        <input
          ref="fileInputRef"
          type="file"
          accept=".efl"
          style="display: none"
          @change="onFileSelected"
        />
        <input
          ref="legacyTodoInputRef"
          type="file"
          accept=".json,application/json"
          style="display: none"
          @change="onLegacyTodoSelected"
        />

        <p class="archive-hint">
          {{ t('settings.archive.hint') }}
        </p>

        <button class="btn secondary full" @click="goBack">{{ t('settings.back') }}</button>
      </template>

      <!-- 数据恢复 -->
      <template v-else-if="currentView === 'restore'">
        <RecoveryPanel :data-status="dataStatus" :backups="backupsList" @back="goBack" @restore="handleRestoreBackup" @emergency-export="handleEmergencyExport" />
      </template>

      <template v-else-if="currentView === 'legacy-recovery'">
        <h2>{{ t('settings.legacyRecovery.title') }}</h2>

        <!-- 数据状态 -->
        <div class="data-stats">
          <h3>{{ t('settings.legacyRecovery.statusTitle') }}</h3>
          <div v-if="dataStatus" class="stats-grid">
            <div class="stat-item">
              <span class="stat-value">{{ dataStatus.localStorageEmpty ? t('settings.restore.empty') : t('settings.restore.available') }}</span>
              <span class="stat-label">localStorage</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ dataStatus.indexedDBEmpty ? t('settings.restore.empty') : t('settings.restore.available') }}</span>
              <span class="stat-label">IndexedDB</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ dataStatus.backupCount }}</span>
              <span class="stat-label">{{ t('settings.legacyRecovery.availableBackups') }}</span>
            </div>
          </div>
        </div>

        <!-- 紧急操作 -->
        <div class="reset-section">
          <h3>{{ t('settings.legacyRecovery.emergencyTitle') }}</h3>
          <button class="btn secondary full" @click="handleEmergencyExport">
            {{ t('settings.legacyRecovery.emergencyAction') }}
          </button>
          <p class="archive-hint">
            {{ t('settings.legacyRecovery.emergencyDescription') }}
          </p>
        </div>

        <!-- 备份列表 -->
        <div class="reset-section" v-if="backupsList.length > 0">
          <h3>{{ t('settings.legacyRecovery.availableBackups') }} ({{ backupsList.length }})</h3>
          <div class="backup-list">
            <div
              v-for="backup in backupsList"
              :key="`${backup.module}_${backup.timestamp}`"
              class="backup-item"
            >
              <div class="backup-info">
                <span class="backup-module">{{ backup.module }}</span>
                <span class="backup-time">{{ new Date(backup.timestamp).toLocaleString('zh-CN') }}</span>
              </div>
              <button class="btn primary" @click="handleRestoreBackup(backup)">
                {{ t('settings.legacyRecovery.restore') }}
              </button>
            </div>
          </div>
        </div>

        <div class="reset-section" v-else>
          <h3>{{ t('settings.legacyRecovery.noBackups') }}</h3>
          <p class="archive-hint">
            {{ t('settings.legacyRecovery.noBackups') }}<br>
            {{ t('settings.legacyRecovery.autoBackupHint') }}
          </p>
        </div>

        <button class="btn secondary full" @click="goBack">{{ t('settings.back') }}</button>
      </template>

      <!-- 恢复 -->
      <template v-else-if="currentView === 'reset'">
        <h2>{{ t('settings.reset.title') }}</h2>
        <p class="reset-warning">⚠️ {{ t('settings.reset.warning') }}</p>

        <div class="reset-section">
          <h3>{{ t('settings.reset.dataClearTitle') }}</h3>
          <button class="btn danger full" @click="handleReset('all')">{{ t('settings.reset.all') }}</button>
          <button class="btn secondary full" @click="handleReset('records')">{{ t('settings.reset.records') }}</button>
          <button class="btn secondary full" @click="handleReset('plans')">{{ t('settings.reset.plans') }}</button>
        </div>

        <div class="reset-section">
          <h3>{{ t('settings.reset.settingsTitle') }}</h3>
          <button class="btn secondary full" @click="handleReset('config')">{{ t('settings.reset.config') }}</button>
          <button class="btn secondary full" @click="handleReset('settings')">{{ t('settings.reset.audioEvents') }}</button>
        </div>

        <button class="btn secondary full" @click="goBack">{{ t('settings.back') }}</button>
      </template>

      <!-- 反馈 -->
      <template v-else-if="currentView === 'feedback'">
        <h2>{{ t('settings.feedback.title') }}</h2>
        <div class="feedback-content">
          <p class="feedback-desc">
            {{ t('settings.feedback.description') }}
          </p>

          <div class="email-section">
            <div class="email-row">
              <Mail :size="20" class="email-icon" />
              <span class="email-address">{{ FEEDBACK_EMAIL }}</span>
              <button class="copy-btn" @click="copyEmail" :title="copySuccess ? t('settings.feedback.copied') : t('settings.feedback.copyEmail')">
                <Copy :size="16" />
                <span v-if="copySuccess">{{ t('settings.feedback.copied') }}</span>
              </button>
            </div>
          </div>

          <button class="btn primary full email-btn" @click="openEmailClient">
            <Mail :size="18" />
            <span>{{ t('settings.feedback.sendEmail') }}</span>
          </button>

          <div class="feedback-tips">
            <h3>{{ t('settings.feedback.tipsTitle') }}</h3>
            <ul>
              <li>{{ t('settings.feedback.problem') }}</li>
              <li>{{ t('settings.feedback.featureImprovement') }}</li>
              <li>{{ t('settings.feedback.experience') }}</li>
              <li>{{ t('settings.feedback.newFeature') }}</li>
            </ul>
          </div>
        </div>
        <button class="btn secondary full" @click="goBack">{{ t('settings.back') }}</button>
      </template>

      <!-- 更多设置 -->
      <template v-else-if="currentView === 'more'">
        <h2>{{ t('settings.more') }}</h2>
        <div class="settings-list">
          <button class="settings-item" @click="navigateTo('version-info')">
            <span>{{ t('settings.more.version') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="navigateTo('feedback')">
            <span>{{ t('settings.more.feedback') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="startGuide">
            <span>{{ t('settings.more.guide') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="navigateTo('help')">
            <span>{{ t('settings.more.help') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="navigateTo('reset')">
            <span>{{ t('settings.more.reset') }}</span>
            <ChevronRight :size="16" />
          </button>
        </div>
        <button class="btn secondary full" @click="goBack">{{ t('settings.back') }}</button>
      </template>

      <!-- 版本信息 -->
      <template v-else-if="currentView === 'version-info'">
        <div class="version-info-view">
          <!-- 当前版本 - 突出显示 -->
          <div class="current-version-card">
            <div class="version-badge" :class="{ dev: isDev }">
              {{ isDev ? '开发版' : '正式版' }}
            </div>
            <h1 class="current-version-number">v{{ appVersion }}</h1>
            <p class="current-version-build">{{ buildInfo }}</p>
            <div v-if="VERSION_HISTORY[0]" class="current-version-changes">
              <p class="changes-label">最新版本更新：</p>
              <ul>
                <li v-for="(change, i) in VERSION_HISTORY[0].changes" :key="i">{{ change }}</li>
              </ul>
            </div>
          </div>

          <!-- 历史更新记录 -->
          <div class="version-history">
            <h3 class="history-title">历史更新记录</h3>
            <div class="history-list">
              <div v-for="release in VERSION_HISTORY.slice(1)" :key="release.version" class="history-item">
                <div class="history-header">
                  <span class="history-version">v{{ release.version }}</span>
                  <span class="history-date">{{ release.date }}</span>
                </div>
                <ul class="history-changes">
                  <li v-for="(change, i) in release.changes" :key="i">{{ change }}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
        <button class="btn secondary full" @click="goBack">{{ t('settings.back') }}</button>
      </template>
    </main>
  </div>
</template>

<style scoped>
.settings-view {
  min-height: 100vh;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.back-btn:hover {
  background: var(--color-bg-tertiary);
}

.header h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.main-content {
  flex: 1;
  max-width: 500px;
  margin: 0 auto;
  width: 100%;
}

.settings-locale-row { display: flex; justify-content: flex-end; margin-bottom: var(--spacing-md); }

.settings-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.settings-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: 1rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.settings-item:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-hover);
}

.settings-item:active {
  transform: scale(0.98);
}

.credits {
  text-align: center;
  padding: var(--spacing-xl) 0;
  color: var(--color-text-tertiary);
  font-size: 0.75rem;
  line-height: 1.8;
}

.credits .version {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: 2px;
}

.credits .build-info {
  font-size: 0.75rem;
  color: var(--color-text-tertiary, rgba(255,255,255,0.4));
  margin-bottom: var(--spacing-xs);
}

.credits .build-info.dev {
  color: var(--color-warning, #fbbf24);
}

h2 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: var(--spacing-lg);
}

.form-section {
  margin-bottom: var(--spacing-lg);
}

.form-section > label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.threshold-control {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.threshold-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-size: 1rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.threshold-btn:hover {
  background: var(--color-bg-tertiary);
}

.threshold-value {
  flex: 1;
  text-align: center;
  font-size: 1rem;
}

.checkbox-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.checkbox-list label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
}

.checkbox-list input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

/* 主题列表 */
.theme-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.theme-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-bg-secondary);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: left;
  width: 100%;
}

.theme-card:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-hover);
}

.theme-card.active {
  border-color: var(--color-primary);
  background: var(--color-bg-tertiary);
}

.theme-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.theme-name {
  font-weight: 600;
  color: var(--color-text-primary);
}

.theme-desc {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.selected {
  color: var(--color-primary);
  font-weight: bold;
  font-size: 1.25rem;
}

/* 颜色配置 */
.color-settings {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.color-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.color-row span {
  flex: 1;
  font-size: 0.875rem;
}

.color-input {
  width: 80px;
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-family: var(--font-mono);
  font-size: 0.875rem;
}

.select-input {
  flex: 1;
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.slider {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  outline: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
}

.slider-value {
  width: 50px;
  text-align: right;
  font-family: var(--font-mono);
  font-size: 0.875rem;
}

.preset-buttons {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.preset-buttons span {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-xl);
}

.theme-preview-status {
  margin-right: auto;
  align-self: center;
  color: var(--color-text-tertiary);
  font-size: 0.8rem;
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn.small {
  padding: var(--spacing-xs) var(--spacing-md);
  font-size: 0.75rem;
}

.btn.secondary {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.btn.secondary:hover {
  background: var(--color-bg-tertiary);
}

.btn.primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.btn.primary:hover {
  background: var(--color-primary-hover);
}

.btn:active {
  transform: scale(0.97);
}

.btn.full {
  width: 100%;
}

.help-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.help-content {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.help-content p {
  margin-bottom: var(--spacing-sm);
  line-height: 1.6;
}

.help-content h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: var(--spacing-md) 0 var(--spacing-sm);
}

.help-content ul {
  padding-left: var(--spacing-lg);
}

.help-content li {
  margin-bottom: var(--spacing-xs);
  color: var(--color-text-secondary);
}

.archive-actions, .reset-actions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

/* 数据统计样式 */
.data-stats {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.data-stats h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-md) 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-primary);
}

.stat-label {
  display: block;
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

.archive-hint {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  line-height: 1.6;
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
}

.archive-capability-note {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.archive-capability-note p {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* 数据恢复页面样式 */
.backup-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
  max-height: 400px;
  overflow-y: auto;
}

.backup-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.backup-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.backup-module {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.backup-time {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.backup-item .btn {
  flex-shrink: 0;
  margin-left: var(--spacing-md);
  padding: var(--spacing-xs) var(--spacing-md);
  font-size: 0.8125rem;
}

/* 恢复页面样式 */
.reset-warning {
  font-size: 0.875rem;
  color: var(--color-warning, #f59e0b);
  background: rgba(245, 158, 11, 0.1);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-lg);
}

.reset-section {
  margin-bottom: var(--spacing-lg);
}

.reset-section h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-sm) 0;
}

.btn.danger {
  background: rgba(239, 68, 68, 0.9);
  color: white;
  border-color: rgba(239, 68, 68, 1);
}

.btn.danger:hover {
  background: rgba(239, 68, 68, 1);
}

/* 帮助页面样式 */
.help-section {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.help-section h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-md) 0;
  color: var(--color-text-primary);
}

.help-steps {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.help-step {
  display: flex;
  gap: var(--spacing-md);
  align-items: flex-start;
}

.step-number {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: white;
  border-radius: 50%;
  font-weight: 600;
  font-size: 0.875rem;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
}

.step-content strong {
  display: block;
  margin-bottom: 4px;
  color: var(--color-text-primary);
}

.step-content p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.faq-item {
  border-bottom: 1px solid var(--color-border);
  padding: var(--spacing-md) 0;
}

.faq-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.faq-item summary {
  cursor: pointer;
  font-weight: 500;
  color: var(--color-text-primary);
  padding: var(--spacing-xs) 0;
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.faq-item summary::-webkit-details-marker {
  display: none;
}

.faq-item summary::after {
  content: '+';
  font-size: 1.25rem;
  color: var(--color-text-tertiary);
  transition: transform 0.2s ease;
}

.faq-item[open] summary::after {
  transform: rotate(45deg);
}

.faq-answer {
  margin-top: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--color-bg);
  border-radius: var(--radius-md);
}

.faq-answer p {
  margin: 0 0 var(--spacing-sm) 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.faq-answer p:last-child {
  margin-bottom: 0;
}

.faq-answer strong {
  color: var(--color-text-primary);
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--spacing-md);
  background: var(--color-bg);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.feature-icon {
  font-size: 2rem;
  margin-bottom: var(--spacing-xs);
}

.feature-item strong {
  font-size: 0.875rem;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.feature-item p {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

/* 反馈页面样式 */
.feedback-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.feedback-desc {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
}

.email-section {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.email-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.email-icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

.email-address {
  flex: 1;
  font-size: 1rem;
  font-family: var(--font-mono);
  color: var(--color-text-primary);
  word-break: break-all;
}

.copy-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.copy-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.email-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  font-size: 1rem;
}

.feedback-tips {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.feedback-tips h3 {
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--color-text-primary);
}

.feedback-tips ul {
  margin: 0;
  padding-left: var(--spacing-lg);
}

.feedback-tips li {
  margin-bottom: var(--spacing-xs);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  line-height: 1.5;
}

/* 版本信息样式 */
.version-info-view {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.current-version-card {
  background: linear-gradient(135deg, var(--color-bg-secondary), rgba(var(--color-primary-rgb, 99, 102, 241), 0.1));
  border: 2px solid var(--color-primary);
  border-radius: var(--radius-xl, 16px);
  padding: var(--spacing-xl);
  text-align: center;
  position: relative;
}

.version-badge {
  display: inline-block;
  padding: 4px 12px;
  background: var(--color-primary);
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 20px;
  margin-bottom: var(--spacing-sm);
}

.version-badge.dev {
  background: var(--color-warning, #fbbf24);
  color: #000;
}

.current-version-number {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-primary);
  margin: 0 0 var(--spacing-xs) 0;
  letter-spacing: -1px;
}

.current-version-build {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin: 0 0 var(--spacing-md) 0;
}

.current-version-changes {
  background: rgba(0, 0, 0, 0.1);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  text-align: left;
}

.changes-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin: 0 0 var(--spacing-xs) 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.current-version-changes ul {
  margin: 0;
  padding-left: var(--spacing-lg);
}

.current-version-changes li {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  line-height: 1.6;
  margin-bottom: 2px;
}

/* 历史更新记录 */
.version-history {
  margin-top: var(--spacing-sm);
}

.history-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-md) 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.history-item {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.history-version {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.history-date {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.history-changes {
  margin: 0;
  padding-left: var(--spacing-lg);
}

.history-changes li {
  color: var(--color-text-secondary);
  font-size: 0.8125rem;
  line-height: 1.6;
  margin-bottom: 2px;
}

.history-changes li:last-child {
  margin-bottom: 0;
}
</style>
