<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { AlertTriangle, ArrowLeft, ChevronRight, Mail, Copy } from 'lucide-vue-next'
import type { Config, ThemeType, SolidThemeConfig, GradientThemeConfig, GlassThemeConfig, NeonThemeConfig } from '@/types'
import { GuideManager } from '@/guide'
import { APP_VERSION, getBuildInfo, getVersionChanges, isDevVersion, VERSION_HISTORY } from '@/version'
import { exportArchive, importArchive, importArchiveWithDialog, previewArchive, resetData, getDataStats, type ArchivePreview, type ResetType } from '@/services/ArchiveService'
import { getAllBackups, restoreFromSpecificBackup, checkDataIntegrity, exportEmergencyBackup, type BackupData, type DataStatus } from '@/storage'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import LocaleSwitcher from '@/components/LocaleSwitcher.vue'
import HelpCenterPanel from '@/components/HelpCenterPanel.vue'
import RecoveryPanel from '@/components/RecoveryPanel.vue'
import { useI18n } from '@/i18n'
import { isMobilePlanRuntime, isMobilePlatform, isTauriRuntime } from '@/services/runtimeCapabilities'
import { importLegacyTodoPayload } from '@/services/todoService'
import { notifyToast } from '@/services/toastService'
import { requestConfirm } from '@/services/confirmService'
import { DataService, getTodayDate, normalizeConfig } from '@/services/dataService'
import { getAvailableThemes, getAvailableThemeCategories, type ThemeDefinition } from '@/theme/ThemeEngine'
import { onWorkspaceChanged } from '@/services/workspaceEvents'
import { AudioManager } from '@/audio/AudioManager'
import { EventSystem } from '@/audio/EventSystem'
import { CheckinSystem } from '@/data/CheckinSystem'

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
async function openEmailClient() {
  const subject = encodeURIComponent(t('settings.feedback.emailSubject'))
  const body = encodeURIComponent(t('settings.feedback.emailBody', { version: appVersion }))
  const mailto = `mailto:${FEEDBACK_EMAIL}?subject=${subject}&body=${body}`

  // 移动端直接使用 window.location
  if (isMobilePlatform()) {
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
      notifyToast(t('settings.feedback.emailCopied'), 'success')
    }
  }
}

async function copyEmail() {
  try {
    await navigator.clipboard.writeText(FEEDBACK_EMAIL)
    copySuccess.value = true
    setTimeout(() => { copySuccess.value = false }, 2000)
  } catch (e) {
    notifyToast(t('settings.feedback.copyFailed'), 'error')
  }
}

const router = useRouter()
const appStore = useAppStore()
const { t, locale } = useI18n()
const mobilePlanRuntime = isMobilePlanRuntime()

const config = computed(() => appStore.config)

// 当前视图
type ViewType = 'main' | 'custom' | 'theme' | 'help' | 'archive' | 'reset' | 'feedback' | 'version-info' | 'more' | 'restore'
const currentView = ref<ViewType>('main')
// 导航历史栈（用于返回上一级）
const viewHistory = ref<ViewType[]>(['main'])

// 导航到指定视图（记录历史）
async function navigateTo(view: ViewType) {
  // Internal settings navigation does not trigger vue-router guards. Protect
  // this exit path with the same theme confirmation used by the back button.
  if (currentView.value === 'theme' && themeDirty.value) {
    const canLeave = await confirmThemeExit()
    if (!canLeave) return
  }
  viewHistory.value.push(view)
  currentView.value = view
  if (view === 'restore') loadDataStatus()
}

// 返回上一级
async function goBack() {
  if (currentView.value === 'theme' && themeDirty.value) {
    const canLeave = await confirmThemeExit()
    if (!canLeave) return
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

type CustomSettingsDraft = Pick<Config, 'overtime_threshold' | 'show_seconds' | 'use_24h' | 'show_ampm'>

function customSettingsFrom(configValue: Config): CustomSettingsDraft {
  return {
    overtime_threshold: configValue.overtime_threshold,
    show_seconds: configValue.show_seconds,
    use_24h: configValue.use_24h,
    show_ampm: configValue.show_ampm,
  }
}

function currentCustomSettings(): CustomSettingsDraft {
  return {
    overtime_threshold: overtimeThreshold.value,
    show_seconds: showSeconds.value,
    use_24h: use24h.value,
    show_ampm: showAmPm.value,
  }
}

const savedCustomSettingsSnapshot = ref<CustomSettingsDraft>(customSettingsFrom(config.value))
const customSettingsDirty = computed(() => JSON.stringify(currentCustomSettings()) !== JSON.stringify(savedCustomSettingsSnapshot.value))

async function saveCustomSettings() {
  const newConfig: Config = {
    ...config.value,
    overtime_threshold: overtimeThreshold.value,
    show_seconds: showSeconds.value,
    use_24h: use24h.value,
    show_ampm: showAmPm.value
  }
  try {
    await appStore.saveConfig(newConfig)
    savedCustomSettingsSnapshot.value = currentCustomSettings()
    notifyToast(t('settings.saved'), 'success')
  } catch (error) {
    console.error('Failed to save custom settings:', error)
    notifyToast(t('settings.saveFailed'), 'error')
  }
}

function addThreshold() {
  if (overtimeThreshold.value < 150) overtimeThreshold.value++
}

function subThreshold() {
  if (overtimeThreshold.value > 100) overtimeThreshold.value--
}

// ============ 主题设置 ============
const themeType = ref<ThemeType>(config.value.theme.type || 'solid')

// Keep the editor draft detached from Pinia. Otherwise v-model can mutate the
// persisted configuration object before the user leaves the theme panel, which
// makes preview, dirty detection, and exit persistence observe different state.
const solidConfig = ref<SolidThemeConfig>(config.value.theme.solid ? { ...config.value.theme.solid } : {
  bg_window: '#f0f0f0',
  bg_button: '#e0e0e0',
  fg_button: '#000000',
  bg_frame: '#d9d9d9'
})

const gradientConfig = ref<GradientThemeConfig>(config.value.theme.gradient ? { ...config.value.theme.gradient } : {
  color_start: '#667eea',
  color_end: '#764ba2',
  direction: 'to-br',
  fg_button: '#ffffff',
  card_bg: 'rgba(255, 255, 255, 0.15)'
})

const glassConfig = ref<GlassThemeConfig>(config.value.theme.glass ? { ...config.value.theme.glass } : {
  bg_color: '#1a1a2e',
  glass_opacity: 0.1,
  blur_amount: 10,
  fg_button: '#ffffff',
  border_color: 'rgba(255, 255, 255, 0.2)'
})

const neonConfig = ref<NeonThemeConfig>(config.value.theme.neon ? { ...config.value.theme.neon } : {
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
// A successful local save already makes Pinia the newest source of truth.
// Ignore the matching workspace event while that save is in flight; otherwise
// the refresh listener can read an older cross-window snapshot and briefly
// overwrite the just-confirmed theme while the settings view is leaving.
const savingTheme = ref(false)

function syncThemeDraft(theme: Config['theme']) {
  themeType.value = theme.type || 'solid'
  if (theme.solid) solidConfig.value = { ...theme.solid }
  if (theme.gradient) gradientConfig.value = { ...theme.gradient }
  if (theme.glass) glassConfig.value = { ...theme.glass }
  if (theme.neon) neonConfig.value = { ...theme.neon }
}

const stopWorkspaceListener = onWorkspaceChanged((source) => {
  if (currentView.value === 'archive') void refreshDataStats()
  if (source !== 'settings' && source !== 'archive') return
  if (savingTheme.value) return
  const hadLocalDraft = themeDirty.value
  // The workspace event is emitted before other windows finish rehydrating
  // IndexedDB. Reload here as well so the dirty marker never snapshots the
  // stale in-memory theme from before the external save/import.
  void appStore.refreshWorkspaceData().then(() => {
    const externalTheme = cloneTheme(appStore.config.theme)
    // Do not overwrite an intentional local draft. If the editor was clean,
    // keep its controls aligned with the theme written by the other window.
    if (!hadLocalDraft) {
      savedThemeSnapshot.value = externalTheme
      syncThemeDraft(externalTheme)
    } else {
      // A visibility refresh can replace Pinia's preview with the durable
      // value while this editor is open. Re-apply the draft so the editor
      // does not appear to lose changes before the exit confirmation.
      previewTheme()
    }
  }).catch((error) => {
    console.warn('Failed to refresh theme snapshot after workspace change:', error)
  })
})

function buildDraftTheme(): Config['theme'] {
  return {
    // Keep rich-theme/custom fields that are not edited by this panel. The
    // editor must not turn a valid theme into a partial object on save. Use
    // the durable snapshot as the base instead of the live preview object:
    // App-level refreshes are allowed to replace config.value while this
    // panel is open, but they must never become the source of truth for a
    // draft that is about to be confirmed and persisted.
    ...savedThemeSnapshot.value,
    type: themeType.value,
    solid: { ...solidConfig.value },
    gradient: { ...gradientConfig.value },
    glass: { ...glassConfig.value },
    neon: { ...neonConfig.value },
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

// Keep theme selection as an explicit action instead of relying on a watcher
// alone. This makes the visual preview update in the same event turn and keeps
// the draft dirty before the user leaves the panel.
function selectTheme(type: ThemeType) {
  if (themeType.value === type) return
  themeType.value = type
  previewTheme()
}

// 主题引擎是唯一的可选主题注册表，避免设置页与应用壳的主题列表漂移。
const availableThemes = getAvailableThemes()
const availableThemeCategories = getAvailableThemeCategories()

function themeCategory(theme: ThemeDefinition): string {
  return theme.categoryKey
}

function themeName(theme: ThemeDefinition): string {
  return t(theme.nameKey)
}

function themeDescription(theme: ThemeDefinition): string {
  return t(theme.descriptionKey)
}

async function saveTheme(): Promise<boolean> {
  // Build the payload from the detached editor draft, not from the previewed
  // Pinia object. The latter can be rehydrated by App.vue while this view is
  // leaving and would otherwise make a just-edited theme easy to lose.
  const draftTheme = cloneTheme(buildDraftTheme())
  const newConfig: Config = {
    ...config.value,
    theme: draftTheme,
  }
  const expectedTheme = normalizeConfig(newConfig).theme
  savingTheme.value = true
  try {
    await appStore.saveConfig(newConfig)
    // Confirm the value through the same durable read path used on startup.
    // This closes the remaining exit race where the in-memory preview looked
    // correct but a reload could still hydrate an older snapshot.
    const persistedConfig = await DataService.loadConfig()
    if (JSON.stringify(persistedConfig.theme) !== JSON.stringify(expectedTheme)) {
      throw new Error('Theme persistence verification failed')
    }
    // Use the value read back through the startup path as the final source of
    // truth. This matters when normalization adds defaults or another window
    // observes the settings event while this view is leaving: the preview and
    // the clean snapshot must be exactly what the next startup will hydrate.
    const durableTheme = cloneTheme(persistedConfig.theme)
    appStore.previewConfig({ ...appStore.config, theme: durableTheme })
    savedThemeSnapshot.value = durableTheme
    syncThemeDraft(durableTheme)
    notifyToast(t('settings.saved'), 'success')
    return true
  } catch (error) {
    console.error('Failed to save theme settings:', error)
    notifyToast(t('settings.saveFailed'), 'error')
    return false
  } finally {
    savingTheme.value = false
  }
}

async function flushThemeSave(): Promise<boolean> {
  if (!themeDirty.value) return true
  return await saveTheme()
}

async function confirmThemeExit(): Promise<boolean> {
  if (!await requestConfirm(t('settings.theme.unsavedConfirm'))) return false
  return await flushThemeSave()
}

// Global navigation can leave SettingsView without going through goBack().
// Persist the theme draft for every exit path and keep the editor mounted if
// durable storage rejects the write.
onBeforeRouteLeave(async () => {
  if (currentView.value !== 'theme' || !themeDirty.value) return true
  return await confirmThemeExit()
})

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
  todoCount: 0,
  activeTodoCount: 0,
  todoCategoryCount: 0,
  hasConfig: false,
  hasPlans: false,
  eventPlanCount: 0,
  archivedEventPlanCount: 0,
  eventPlanSource: 'unavailable' as 'live' | 'cache' | 'snapshot' | 'unavailable',
  hasAudioSettings: false,
  hasEventSettings: false,
  hasCheckin: false,
})
const dataStatsUnavailable = ref(false)
let dataStatsRequestId = 0

async function refreshDataStats() {
  const requestId = ++dataStatsRequestId
  try {
    const nextStats = await getDataStats()
    if (requestId === dataStatsRequestId) {
      dataStats.value = nextStats
      dataStatsUnavailable.value = false
    }
  } catch (error) {
    // Statistics are supplementary; an IndexedDB read failure must not block
    // the settings page or invalidate the rest of the archive controls.
    console.warn('Failed to load settings data statistics:', error)
    if (requestId === dataStatsRequestId) dataStatsUnavailable.value = true
  }
}

async function handleReset(type: ResetType) {
  const messages: Record<ResetType, string> = {
    all: t('settings.reset.confirmAll'),
    records: t('settings.reset.confirmRecords'),
    plans: t('settings.reset.confirmPlans'),
    config: t('settings.reset.confirmConfig'),
    settings: t('settings.reset.confirmSettings'),
  }

  if (!await requestConfirm(messages[type], { tone: 'danger' })) return
  await resetData(type)
}

// ============ 存档管理 ============
// 文件选择输入框引用
const fileInputRef = ref<HTMLInputElement | null>(null)
const legacyTodoInputRef = ref<HTMLInputElement | null>(null)
const archiveBusy = ref(false)

async function refreshAfterArchiveImport(): Promise<void> {
  // The import is durable immediately, but the current settings view may
  // still hold pre-import Pinia/statistics snapshots when the user chooses
  // to postpone the full page reload.
  await Promise.allSettled([
    appStore.refreshWorkspaceData(),
    refreshDataStats(),
    AudioManager.refreshFromStorage(),
    EventSystem.refreshFromStorage(),
    CheckinSystem.refreshFromStorage(),
  ])
}

async function handleExportArchive() {
  if (archiveBusy.value) return
  archiveBusy.value = true
  try {
    const result = await exportArchive()
    if (result.success) {
      if (result.path) {
          notifyToast(`${t('settings.archive.savedTo')}\n${result.path}${result.warning ? `\n\n${t('settings.archive.warning')}${result.warning}` : ''}`, 'success')
      } else {
          notifyToast(`${t('settings.archive.downloaded')}${result.warning ? `\n\n${t('settings.archive.warning')}${result.warning}` : ''}`, 'success')
      }
    }
  } catch (e) {
    notifyToast(t('settings.archive.exportFailed') + (e as Error).message, 'error')
  } finally {
    archiveBusy.value = false
  }
}

async function handleImportArchive() {
  // 桌面 Tauri 使用原生文件对话框；浏览器和 Tauri Mobile 使用 WebView 文件选择器。
  if (isTauriRuntime() && !isMobilePlatform()) {
    archiveBusy.value = true
    // Tauri 环境：使用原生文件对话框
    try {
      const result = await importArchiveWithDialog((preview) => requestConfirm(`${formatArchivePreview(preview)}\n\n${t('settings.archive.importConfirm')}`, { tone: 'danger' }))
      if (result.cancelled) return
      if (result.success) {
        await refreshAfterArchiveImport()
        if (await requestConfirm(result.message + '\n\n' + t('settings.archive.reloadConfirm'))) {
          window.location.reload()
        }
      } else {
        notifyToast(result.message, 'error')
      }
    } catch (error) {
      notifyToast(t('settings.archive.importFailed', { detail: error instanceof Error ? error.message : String(error) }), 'error')
    } finally {
      archiveBusy.value = false
    }
  } else {
    // 浏览器环境：使用文件选择器
    if (fileInputRef.value) {
      fileInputRef.value.click()
    }
  }
}

async function onFileSelected(event: Event) {
  if (archiveBusy.value) return
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // 重置 input 以便可以再次选择同一文件
  input.value = ''
  archiveBusy.value = true

  let preview: ArchivePreview
  try {
    preview = await previewArchive(file)
  } catch (error) {
    notifyToast(t('settings.archive.importFailed', { detail: error instanceof Error ? error.message : String(error) }), 'error')
    archiveBusy.value = false
    return
  }

  if (!await requestConfirm(`${formatArchivePreview(preview)}\n\n${t('settings.archive.importConfirm')}`, { tone: 'danger' })) {
    archiveBusy.value = false
    return
  }

  try {
    const result = await importArchive(file)
    notifyToast(result.message, result.success ? 'success' : 'error')

    if (result.success) {
      await refreshAfterArchiveImport()
      if (await requestConfirm(result.message + '\n\n' + t('settings.archive.reloadConfirm'))) {
        window.location.reload()
      }
    }
  } catch (error) {
    notifyToast(t('settings.archive.importFailed', { detail: error instanceof Error ? error.message : String(error) }), 'error')
  } finally {
    archiveBusy.value = false
  }
}

// ============ 数据恢复 ============
function formatArchivePreview(preview: ArchivePreview): string {
  const summary = t('settings.archive.importPreview', {
    plans: preview.planCount,
    archivedPlans: preview.archivedPlanCount,
    todos: preview.todoCount,
    records: preview.recordCount,
    categories: preview.categoryCount,
    repairs: preview.repairedLinkCount,
  })
  const integrity = preview.integrity === 'verified'
    ? t('settings.archive.integrityVerified')
    : t('settings.archive.integrityLegacy')
  const planStatus = preview.planStatus === 'available'
    ? t('settings.archive.planSnapshotLive')
    : preview.planStatus === 'snapshot'
      ? t('settings.archive.planSnapshotLocal')
    : preview.planStatus === 'stale'
      ? t('settings.archive.planSnapshotStale')
      : t('settings.archive.planSnapshotUnavailable')
  return `${summary}\n${planStatus}\n${integrity}`
}

function openLegacyTodoImport() {
  legacyTodoInputRef.value?.click()
}

async function onLegacyTodoSelected(event: Event) {
  if (archiveBusy.value) return
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  archiveBusy.value = true
  if (!await requestConfirm(t('settings.archive.legacyTodoImportConfirm'), { tone: 'danger' })) {
    archiveBusy.value = false
    return
  }
  try {
    const result = await importLegacyTodoPayload(await file.text())
    notifyToast(t('settings.archive.legacyTodoImportSuccess', { ...result }), 'success')
    if (await requestConfirm(t('settings.archive.reloadNow'))) {
      window.location.reload()
    }
  } catch (error) {
    notifyToast(t('settings.archive.legacyTodoImportFailed') + (error as Error).message, 'error')
  } finally {
    archiveBusy.value = false
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
  if (!await requestConfirm(`${t('settings.restore.confirmPrefix')}${new Date(backup.timestamp).toLocaleString(locale.value)}${t('settings.restore.confirmSuffix')}`, { tone: 'danger' })) {
    return
  }

  try {
    const result = await restoreFromSpecificBackup(backup)
    if (result.success) {
      await refreshAfterArchiveImport()
      notifyToast(result.message + '\n\n' + t('settings.archive.reloadConfirm'), 'success')
      if (await requestConfirm(t('settings.archive.reloadNow'))) {
        window.location.reload()
      }
    } else {
      notifyToast(result.message, 'error')
    }
  } catch (e) {
    notifyToast(t('settings.restore.failed') + (e as Error).message, 'error')
  }
}

async function handleEmergencyExport() {
  try {
    const jsonStr = await exportEmergencyBackup()
    const blob = new Blob([jsonStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `efflife_emergency_${getTodayDate()}.json`
    a.click()
    URL.revokeObjectURL(url)
    notifyToast(t('settings.restore.emergencyDownloaded'), 'success')
  } catch (e) {
    notifyToast(t('settings.archive.exportFailed') + (e as Error).message, 'error')
  }
}

// 同步配置到本地状态
watch(() => config.value, (newConfig) => {
  const hadLocalDraft = customSettingsDirty.value
  if (!hadLocalDraft) {
    overtimeThreshold.value = newConfig.overtime_threshold
    showSeconds.value = newConfig.show_seconds
    use24h.value = newConfig.use_24h
    showAmPm.value = newConfig.show_ampm
    savedCustomSettingsSnapshot.value = customSettingsFrom(newConfig)
  }
}, { immediate: true, deep: true })

watch(() => config.value.theme, (newTheme) => {
  if (themeDirty.value) {
    // App-level visibility refreshes reload durable data. A dirty theme edit
    // must remain the source of truth until the user confirms leaving.
    previewTheme()
    return
  }
  savedThemeSnapshot.value = cloneTheme(newTheme)
  syncThemeDraft(newTheme)
}, { deep: true })

watch([themeType, solidConfig, gradientConfig, glassConfig, neonConfig], () => {
  previewTheme()
}, { deep: true })

watch(currentView, (view) => {
  if (view === 'archive') void refreshDataStats()
})

// 初始化完成后关闭加载状态
onMounted(async () => {
  try {
    await refreshDataStats()
  } catch (error) {
    // Keep the initialization boundary explicit even if the refresh helper
    // later gains a caller-specific error policy.
    console.warn('Failed to load settings data statistics:', error)
  }
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
        if (await requestConfirm(t('settings.restore.emptyWithBackups'))) {
          navigateTo('restore')
        }
      }
    }
  } catch {
    // ignore
  }
})

onUnmounted(() => {
  stopWorkspaceListener()
})
</script>

<template>
  <div class="settings-view">
    <header class="header">
      <button type="button" class="back-btn" @click="goBack">
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
          <button type="button" class="settings-item" @click="navigateTo('custom')">
            <span>{{ t('settings.custom') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button type="button" class="settings-item" @click="navigateTo('theme')">
            <span>{{ t('settings.theme.title') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button type="button" class="settings-item" @click="router.push('/audio-settings')">
            <span>{{ t('settings.audio') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button type="button" class="settings-item" @click="router.push('/motion-settings')">
            <span>{{ t('settings.motion') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button type="button" class="settings-item" @click="router.push('/event-manager')">
            <span>{{ t('settings.events') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button type="button" class="settings-item" @click="navigateTo('archive')">
            <span>{{ t('settings.archive.title') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button type="button" class="settings-item" @click="navigateTo('restore')">
            <span>{{ t('settings.restore.title') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button type="button" class="settings-item" @click="navigateTo('more')">
            <span>{{ t('settings.more') }}</span>
            <ChevronRight :size="16" />
          </button>
        </div>

        <footer class="credits">
          <p class="version">{{ t('home.appTitle') }} v{{ appVersion }}</p>
          <p class="build-info" :class="{ dev: isDev }">{{ buildInfo }}</p>
          <p>{{ t('settings.about.developer') }}</p>
          <p>{{ t('settings.about.social') }}</p>
        </footer>
      </template>

      <!-- 自定义设置 -->
      <template v-else-if="currentView === 'custom'">
        <form class="custom-settings-form" @submit.prevent="saveCustomSettings">
        <h2>{{ t('settings.customTitle') }}</h2>

        <div class="form-section">
          <label>{{ t('settings.threshold') }}</label>
          <div class="threshold-control">
            <button type="button" class="threshold-btn" @click="subThreshold">-</button>
            <span class="threshold-value">{{ t('settings.currentThreshold') }}：{{ overtimeThreshold }}%</span>
            <button type="button" class="threshold-btn" @click="addThreshold">+</button>
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
          <button type="button" class="btn secondary" @click="goBack">{{ t('settings.back') }}</button>
          <button type="submit" class="btn primary">{{ t('settings.save') }}</button>
        </div>
        </form>
      </template>

      <!-- 主题设置 -->
      <template v-else-if="currentView === 'theme'">
        <h2>{{ t('settings.theme.title') }}</h2>

        <div v-for="category in availableThemeCategories" :key="category" class="form-section theme-category" role="group" :aria-labelledby="`theme-category-${category}`">
          <div class="theme-category-heading">
            <h3 :id="`theme-category-${category}`">{{ t(category) }}</h3>
            <span class="theme-category-count">{{ availableThemes.filter(theme => themeCategory(theme) === category).length }}</span>
          </div>
          <div class="theme-list">
            <button
              v-for="theme in availableThemes.filter(theme => themeCategory(theme) === category)"
              :key="theme.type"
              type="button"
              class="theme-card"
              :class="{ active: themeType === theme.type }"
              :aria-pressed="themeType === theme.type"
              @click="selectTheme(theme.type)"
            >
              <span class="theme-swatch" :style="{ background: theme.preview }" aria-hidden="true"></span>
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
                <button type="button" class="btn small" @click="pickColor('solid_bg_window')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.buttonBackground') }}</span>
                <input type="text" v-model="solidConfig.bg_button" class="color-input" />
                <button type="button" class="btn small" @click="pickColor('solid_bg_button')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.buttonText') }}</span>
                <input type="text" v-model="solidConfig.fg_button" class="color-input" />
                <button type="button" class="btn small" @click="pickColor('solid_fg_button')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
            </div>
            <div class="preset-buttons">
              <span>{{ t('settings.theme.presetLabel') }}</span>
              <button type="button" class="btn small" @click="applySolidPreset('default')">{{ t('settings.theme.preset.default') }}</button>
              <button type="button" class="btn small" @click="applySolidPreset('dark')">{{ t('settings.theme.preset.dark') }}</button>
              <button type="button" class="btn small" @click="applySolidPreset('light')">{{ t('settings.theme.preset.light') }}</button>
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
                <button type="button" class="btn small" @click="pickColor('gradient_color_start')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.endColor') }}</span>
                <input type="text" v-model="gradientConfig.color_end" class="color-input" />
                <button type="button" class="btn small" @click="pickColor('gradient_color_end')">{{ t('settings.theme.chooseColor') }}</button>
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
              <button type="button" class="btn small" @click="applyGradientPreset('purple')">{{ t('settings.theme.preset.purple') }}</button>
              <button type="button" class="btn small" @click="applyGradientPreset('blue')">{{ t('settings.theme.preset.blue') }}</button>
              <button type="button" class="btn small" @click="applyGradientPreset('sunset')">{{ t('settings.theme.preset.sunset') }}</button>
              <button type="button" class="btn small" @click="applyGradientPreset('forest')">{{ t('settings.theme.preset.forest') }}</button>
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
                <button type="button" class="btn small" @click="pickColor('glass_bg_color')">{{ t('settings.theme.chooseColor') }}</button>
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
              <button type="button" class="btn small" @click="applyGlassPreset('dark')">{{ t('settings.theme.preset.dark') }}</button>
              <button type="button" class="btn small" @click="applyGlassPreset('light')">{{ t('settings.theme.preset.light') }}</button>
              <button type="button" class="btn small" @click="applyGlassPreset('blue')">{{ t('settings.theme.preset.blue') }}</button>
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
                <button type="button" class="btn small" @click="pickColor('neon_bg_color')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.neonColor') }}</span>
                <input type="text" v-model="neonConfig.neon_color" class="color-input" />
                <button type="button" class="btn small" @click="pickColor('neon_neon_color')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.accentColor') }}</span>
                <input type="text" v-model="neonConfig.accent_color" class="color-input" />
                <button type="button" class="btn small" @click="pickColor('neon_accent_color')">{{ t('settings.theme.chooseColor') }}</button>
              </div>
              <div class="color-row">
                <span>{{ t('settings.theme.glowIntensity') }}</span>
                <input type="range" v-model.number="neonConfig.glow_intensity" min="0" max="30" step="2" class="slider" />
                <span class="slider-value">{{ neonConfig.glow_intensity }}px</span>
              </div>
            </div>
            <div class="preset-buttons">
              <span>{{ t('settings.theme.presetLabel') }}</span>
              <button type="button" class="btn small" @click="applyNeonPreset('green')">{{ t('settings.theme.preset.green') }}</button>
              <button type="button" class="btn small" @click="applyNeonPreset('pink')">{{ t('settings.theme.preset.pink') }}</button>
              <button type="button" class="btn small" @click="applyNeonPreset('cyan')">{{ t('settings.theme.preset.cyan') }}</button>
              <button type="button" class="btn small" @click="applyNeonPreset('rainbow')">{{ t('settings.theme.preset.rainbow') }}</button>
            </div>
          </div>
        </template>

        <div class="form-actions">
          <button type="button" class="btn secondary" @click="goBack">{{ t('settings.back') }}</button>
          <span class="theme-preview-status" role="status" aria-live="polite">{{ t('settings.theme.previewStatus') }}</span>
        </div>
      </template>

      <!-- 帮助 -->
      <template v-else-if="currentView === 'help'">
        <HelpCenterPanel @back="goBack" />
      </template>

      <!-- 存档管理 -->
      <template v-else-if="currentView === 'archive'">
        <h2>{{ t('settings.archive.title') }}</h2>

        <section class="archive-scope theme-card" :aria-label="t('settings.archive.scopeTitle')">
          <div class="archive-scope-copy">
            <strong>{{ t('settings.archive.scopeTitle') }}</strong>
            <span>{{ t('settings.archive.scopeDescription') }}</span>
          </div>
          <div class="archive-scope-domains" :aria-label="t('settings.archive.scopeTitle')">
            <span class="archive-scope-chip"><b>TH</b>{{ t('settings.archive.scopeTime') }}</span>
            <span class="archive-scope-chip"><b>PH</b>{{ t('settings.archive.scopePlans') }}</span>
            <span class="archive-scope-chip"><b>TD</b>{{ t('settings.archive.scopeTodos') }}</span>
          </div>
        </section>

        <div v-if="mobilePlanRuntime" class="archive-capability-note">
          <strong>{{ t('settings.archive.mobilePlanTitle') }}</strong>
          <p>{{ t('settings.archive.mobilePlanDescription') }}</p>
        </div>
        <div v-if="isMobilePlatform()" class="archive-capability-note archive-mobile-note">
          <strong>{{ t('settings.archive.mobileTransferTitle') }}</strong>
          <p>{{ t('settings.archive.mobileTransferDescription') }}</p>
        </div>

        <!-- 数据统计 -->
        <div class="data-stats">
          <h3>{{ t('settings.archive.currentData') }}</h3>
          <div v-if="dataStatsUnavailable" class="archive-stats-unavailable" role="status" aria-live="polite">
            <span>{{ t('settings.archive.statsUnavailable') }}</span>
            <button type="button" @click="refreshDataStats">{{ t('settings.archive.retryStats') }}</button>
          </div>
          <div v-else class="stats-grid">
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
              <span class="stat-value">{{ dataStats.eventPlanCount }} / {{ dataStats.archivedEventPlanCount }}</span>
              <span class="stat-label">{{ t('settings.archive.eventPlanSnapshotsBreakdown', { active: dataStats.eventPlanCount, archived: dataStats.archivedEventPlanCount }) }} · {{ t(`settings.archive.planSource.${dataStats.eventPlanSource}`) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ dataStats.todoCount }}</span>
              <span class="stat-label">{{ t('settings.archive.totalTodos') }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ dataStats.activeTodoCount }}</span>
              <span class="stat-label">{{ t('settings.archive.activeTodos') }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ dataStats.todoCategoryCount }}</span>
              <span class="stat-label">{{ t('settings.archive.todoCategories') }}</span>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="archive-actions" :aria-busy="archiveBusy">
          <button type="button" class="btn primary full" :disabled="archiveBusy" @click="handleExportArchive">
            {{ t('settings.archive.export') }}
          </button>
          <button type="button" class="btn primary full" :disabled="archiveBusy" @click="handleImportArchive">
            {{ t('settings.archive.import') }}
          </button>
          <button type="button" class="btn secondary full" :disabled="archiveBusy" @click="openLegacyTodoImport">
            {{ t('settings.archive.importLegacyTodos') }}
          </button>
        </div>
        <p v-if="archiveBusy" class="archive-status" role="status" aria-live="polite">
          {{ t('settings.archive.busy') }}
        </p>

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

        <button type="button" class="btn secondary full" @click="goBack">{{ t('settings.back') }}</button>
      </template>

      <!-- 数据恢复 -->
      <template v-else-if="currentView === 'restore'">
        <RecoveryPanel :data-status="dataStatus" :backups="backupsList" @back="goBack" @restore="handleRestoreBackup" @emergency-export="handleEmergencyExport" />
      </template>

      <!-- 恢复 -->
      <template v-else-if="currentView === 'reset'">
        <h2>{{ t('settings.reset.title') }}</h2>
        <p class="reset-warning">
          <AlertTriangle :size="18" aria-hidden="true" />
          <span>{{ t('settings.reset.warning') }}</span>
        </p>

        <div class="reset-section">
          <h3>{{ t('settings.reset.dataClearTitle') }}</h3>
          <button type="button" class="btn danger full" @click="handleReset('all')">{{ t('settings.reset.all') }}</button>
          <button type="button" class="btn secondary full" @click="handleReset('records')">{{ t('settings.reset.records') }}</button>
          <button type="button" class="btn secondary full" @click="handleReset('plans')">{{ t('settings.reset.plans') }}</button>
        </div>

        <div class="reset-section">
          <h3>{{ t('settings.reset.settingsTitle') }}</h3>
          <button type="button" class="btn secondary full" @click="handleReset('config')">{{ t('settings.reset.config') }}</button>
          <button type="button" class="btn secondary full" @click="handleReset('settings')">{{ t('settings.reset.audioEvents') }}</button>
        </div>

        <button type="button" class="btn secondary full" @click="goBack">{{ t('settings.back') }}</button>
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
              <button type="button" class="copy-btn" @click="copyEmail" :title="copySuccess ? t('settings.feedback.copied') : t('settings.feedback.copyEmail')">
                <Copy :size="16" />
                <span v-if="copySuccess">{{ t('settings.feedback.copied') }}</span>
              </button>
            </div>
          </div>

          <button type="button" class="btn primary full email-btn" @click="openEmailClient">
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
        <button type="button" class="btn secondary full" @click="goBack">{{ t('settings.back') }}</button>
      </template>

      <!-- 更多设置 -->
      <template v-else-if="currentView === 'more'">
        <h2>{{ t('settings.more') }}</h2>
        <div class="settings-list">
          <button type="button" class="settings-item" @click="navigateTo('version-info')">
            <span>{{ t('settings.more.version') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button type="button" class="settings-item" @click="navigateTo('feedback')">
            <span>{{ t('settings.more.feedback') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button type="button" class="settings-item" @click="startGuide">
            <span>{{ t('settings.more.guide') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button type="button" class="settings-item" @click="navigateTo('help')">
            <span>{{ t('settings.more.help') }}</span>
            <ChevronRight :size="16" />
          </button>
          <button type="button" class="settings-item" @click="navigateTo('reset')">
            <span>{{ t('settings.more.reset') }}</span>
            <ChevronRight :size="16" />
          </button>
        </div>
        <button type="button" class="btn secondary full" @click="goBack">{{ t('settings.back') }}</button>
      </template>

      <!-- 版本信息 -->
      <template v-else-if="currentView === 'version-info'">
        <div class="version-info-view">
          <!-- 当前版本 - 突出显示 -->
          <div class="current-version-card">
            <div class="version-badge" :class="{ dev: isDev }">
              {{ isDev ? t('version.build.development') : t('version.build.release') }}
            </div>
            <h1 class="current-version-number">v{{ appVersion }}</h1>
            <p class="current-version-build">{{ buildInfo }}</p>
            <div v-if="VERSION_HISTORY[0]" class="current-version-changes">
              <p class="changes-label">{{ t('settings.version.latestChanges') }}</p>
              <ul>
                <li v-for="(change, i) in getVersionChanges(VERSION_HISTORY[0], locale)" :key="i">{{ change }}</li>
              </ul>
            </div>
          </div>

          <!-- 历史更新记录 -->
          <div class="version-history">
            <h3 class="history-title">{{ t('settings.version.history') }}</h3>
            <div class="history-list">
              <div v-for="release in VERSION_HISTORY.slice(1)" :key="release.version" class="history-item">
                <div class="history-header">
                  <span class="history-version">v{{ release.version }}</span>
                  <span class="history-date">{{ release.date }}</span>
                </div>
                <ul class="history-changes">
                  <li v-for="(change, i) in getVersionChanges(release, locale)" :key="i">{{ change }}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
        <button type="button" class="btn secondary full" @click="goBack">{{ t('settings.back') }}</button>
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
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.theme-category-heading {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.theme-category-heading h3 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 0.9rem;
}

.theme-category-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.35rem;
  height: 1.35rem;
  padding: 0 0.35rem;
  border-radius: 999px;
  color: var(--color-text-tertiary);
  background: var(--color-bg-tertiary);
  font-size: 0.7rem;
  font-variant-numeric: tabular-nums;
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

.theme-swatch {
  flex: 0 0 auto;
  width: 42px;
  height: 30px;
  margin-right: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, .12);
}

.theme-card:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-hover);
}

.theme-card:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 55%, transparent);
  outline-offset: 2px;
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

.archive-actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.archive-scope { display: grid; gap: 14px; margin-bottom: var(--spacing-lg); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: var(--spacing-md) var(--spacing-lg); background: var(--color-bg-secondary); }
.archive-scope-copy { display: grid; gap: 4px; }
.archive-scope-copy strong { color: var(--color-text-primary); font-size: 13px; }
.archive-scope-copy span { color: var(--color-text-secondary); font-size: 12px; line-height: 1.5; }
.archive-scope-domains { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.archive-scope-chip { display: inline-flex; align-items: center; gap: 7px; min-width: 0; border: 1px solid var(--color-border); border-radius: 9px; padding: 8px 10px; color: var(--color-text-secondary); background: var(--color-bg); font-size: 11px; }
.archive-scope-chip b { color: var(--color-primary); font-family: var(--font-mono, ui-monospace, monospace); font-size: 10px; letter-spacing: .04em; }

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

.archive-status {
  margin: 10px 0 0;
  color: var(--color-primary);
  font-size: 12px;
  text-align: center;
}
.archive-stats-unavailable { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px; border: 1px solid color-mix(in srgb, var(--color-error) 42%, var(--color-border)); border-radius: 10px; color: var(--color-text-secondary); background: var(--color-bg); font-size: 12px; }
.archive-stats-unavailable button { flex: 0 0 auto; border: 1px solid var(--color-border); border-radius: 8px; padding: 6px 9px; color: var(--color-primary); background: var(--color-bg-secondary); cursor: pointer; font: inherit; font-size: 11px; font-weight: 650; }
.archive-stats-unavailable button:hover, .archive-stats-unavailable button:focus-visible { border-color: var(--color-primary); outline: 0; }

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
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
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

@media (min-width: 900px) {
  .settings-view { padding: 24px 32px; }
  .settings-view > .main-content { max-width: 920px; }
  .settings-list {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }
  .settings-item { min-height: 58px; }
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

@media (max-width: 680px) {
  .theme-list { grid-template-columns: 1fr; }
  .settings-view { padding: 16px; }
  .header { gap: 10px; margin-bottom: 20px; }
  .header h1 { font-size: 1.25rem; }
  .back-btn { min-height: 40px; padding: 8px 10px; }
  .settings-item { min-height: 52px; padding: 13px 14px; }
  .stats-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
  .archive-actions { display: flex; flex-direction: column; }
  .archive-scope { padding: 14px; }
  .archive-scope-domains { grid-template-columns: 1fr; }
  .data-stats { padding: 14px; }
  .stat-value { font-size: 1.3rem; }
  .modal-footer { flex-direction: column-reverse; padding: 14px 16px; }
  .modal-footer .btn { justify-content: center; min-height: 42px; }
}
</style>
