<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import ThemeCanvas from './theme/ThemeCanvas.vue'
import { getThemeCssVariables } from './theme/ThemeEngine'
import { AudioManager, EventSystem, EventPopup } from './audio'
import { CheckinSystem, CheckinPopup } from './data'
import { GuideManager, GuideOverlay } from './guide'
import { TodoService } from './services/todoService'
import { Home, ClipboardList, Clock3, History, ListTodo, Settings, Search } from 'lucide-vue-next'
import { refreshLocaleFromStorage, useI18n } from '@/i18n'
import GlobalSearch from './components/GlobalSearch.vue'
import ToastHost from './components/ToastHost.vue'
import ConfirmHost from './components/ConfirmHost.vue'
import { repairTodoPlanTaskLinks, repairTodoTimeRecordLinks } from './services/workspaceSync'
import { onWorkspaceChanged } from './services/workspaceEvents'

const appStore = useAppStore()
const route = useRoute()
const { t, locale } = useI18n()

const themeVariables = computed(() => getThemeCssVariables(appStore.config.theme))

const pageTitle = computed(() => {
  const path = route.path
  if (path === '/') return t('nav.home')
  if (path.startsWith('/plans') || path === '/plan') return t('nav.plans')
  if (path.startsWith('/time')) return t('nav.time')
  if (path.startsWith('/tasks')) return t('nav.tasks')
  if (path.startsWith('/records') || path.startsWith('/day')) return t('nav.records')
  if (path.startsWith('/checkin')) return t('nav.checkin')
  return t('nav.settings')
})

const isSettingsRoute = computed(() => ['/settings', '/audio-settings', '/motion-settings', '/event-manager'].includes(route.path))

// 打卡弹窗状态
const showCheckinPopup = ref(false)
const checkinPlanName = ref('')
// 是否已为今天的100%展示过打卡弹窗
const hasPromptedCheckin = ref(false)
const runtimeReady = ref(false)
const startupError = ref(false)
const startupErrorMessage = ref('')
const showGlobalSearch = ref(false)
let stopWorkspaceListener: (() => void) | null = null
const searchShortcut = computed(() => {
  const platform = typeof navigator === 'undefined' ? '' : navigator.platform
  return /Mac|iPhone|iPad/.test(platform) ? '⌘K' : 'Ctrl K'
})

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)
}

function onGlobalKeydown(event: KeyboardEvent) {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    if (isEditableTarget(event.target)) return
    event.preventDefault()
    showGlobalSearch.value = true
  } else if (event.key === 'Escape') {
    showGlobalSearch.value = false
  }
}

function retryStartup() {
  window.location.reload()
}

function refreshWhenVisible() {
  if (document.visibilityState !== 'visible' || !runtimeReady.value) return
  refreshLocaleFromStorage()
  void appStore.refreshWorkspaceData().catch((error) => {
    console.warn('Failed to refresh workspace after visibility change:', error)
  })
}

// 应用主题到 CSS 变量
function applyTheme() {
  const root = document.documentElement
  for (const [name, value] of Object.entries(themeVariables.value)) {
    root.style.setProperty(name, value)
  }
}

// 检查进度事件
function checkProgressEvents() {
  const stat = appStore.todayStat
  if (!stat || !stat.plan_exists) return

  const progress = stat.progress
  const planName = stat.plan_name

  // 完成度达到100%且未打卡：触发打卡弹窗（而不是普通事件弹窗）
  if (progress >= 100 && CheckinSystem.canCheckinToday() && !hasPromptedCheckin.value) {
    hasPromptedCheckin.value = true
    checkinPlanName.value = planName
    showCheckinPopup.value = true
    return
  }

  // 完成度90%但未满100%：普通事件弹窗
  if (progress >= 90 && progress < 100) {
    EventSystem.checkProgressEvent(progress, planName)
  }

  // 半程完成检查（50%-89%）
  if (progress >= 50 && progress < 90) {
    EventSystem.checkHalfProgress(progress, planName)
  }

  // 检查多规则预警（支持延迟发布）
  EventSystem.checkWarnings(progress, planName)
}

// 打卡完成回调
function onCheckinComplete() {
  showCheckinPopup.value = false
  // 通过 store 刷新
  void appStore.refreshTodayData().catch((error) => {
    // The check-in is already recorded; a refresh failure should not create
    // an unhandled rejection or undo the user's completed action.
    console.warn('Failed to refresh today data after check-in:', error)
  })
}

function onCheckinClose() {
  showCheckinPopup.value = false
}

onMounted(async () => {
  window.addEventListener('keydown', onGlobalKeydown)
  document.addEventListener('visibilitychange', refreshWhenVisible)
  stopWorkspaceListener = onWorkspaceChanged((source) => {
    if (!runtimeReady.value || !source || !['plans', 'records', 'settings', 'archive'].includes(source)) return
    if (source === 'archive' || source === 'settings') refreshLocaleFromStorage()
    void appStore.refreshWorkspaceData().catch((error) => {
      console.warn('Failed to refresh workspace after external change:', error)
    })
  })
  try {
    await Promise.all([AudioManager.whenReady(), CheckinSystem.whenReady(), EventSystem.whenReady()])
    await appStore.init()
    await TodoService.migrateLegacyLocalStorage()
    try {
      await repairTodoTimeRecordLinks()
    } catch (error) {
      // Link repair is recoverable maintenance; it must not block the workspace.
      console.warn('Failed to repair todo/time-record links during startup:', error)
    }
  } catch (error) {
    console.error('Failed to initialize EffiLife workspace:', error)
    startupErrorMessage.value = error instanceof Error ? error.message : String(error)
    startupError.value = true
    return
  }
  applyTheme()
  runtimeReady.value = true
  // Plan-helper may need network retries; do not delay the first usable frame.
  void repairTodoPlanTaskLinks().catch((error) => {
    // Link repair is recoverable maintenance; it must not create an
    // unhandled rejection or make the first usable frame look broken.
    console.warn('Failed to repair todo/plan links after startup:', error)
  })

  // 启动背景音乐
  AudioManager.startBgm()

  // 自动补打卡检查（跨天后如果昨天完成了计划但没打卡）
  const autoCheckinResult = await CheckinSystem.autoCheckinIfMissed()

  if (autoCheckinResult.result === 'checked') {
    // 自动补打卡成功，通知用户
    EventSystem.triggerEvent(
      'achievement_unlocked',
      t('settings.events.runtime.autoCheckinTitle'),
      t('settings.events.runtime.autoCheckinMessage', { count: autoCheckinResult.streak ?? 0 })
    )
  } else if (autoCheckinResult.result === 'streak-broken') {
    // 连续天数已断，但昨天有完成的计划，添加到收件箱让用户手动补打
    const yesterdayRecords = await CheckinSystem.getYesterdayCompletedRecords()
    if (yesterdayRecords.length > 0) {
      const yesterday = CheckinSystem.getYesterdayDate()
      // 为每个完成的计划添加收件箱提醒（虽然连续天数断了，但用户仍可手动打卡记录）
      for (const record of yesterdayRecords) {
        EventSystem.addMissedCheckinReminder(record.planName, yesterday)
      }
    }
  }
  // result === 'no-record': 昨天没有100%完成的任务，无法打卡，什么都不做
  // result === 'already': 今天已打卡，什么都不做

  // 检查是否需要启动引导
  if (!GuideManager.isCompleted()) {
    // 延迟启动引导，确保页面已加载
    setTimeout(() => {
      GuideManager.startGuide()
    }, 500)
  }

  // 检查进度事件
  checkProgressEvents()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onGlobalKeydown)
  document.removeEventListener('visibilitychange', refreshWhenVisible)
  stopWorkspaceListener?.()
  stopWorkspaceListener = null
})

watch(() => appStore.config, applyTheme, { deep: true })

watch([() => route.path, locale], () => {
  document.title = t('app.documentTitle', { page: pageTitle.value })
}, { immediate: true })

// 监听统计数据变化，检查事件
watch(() => appStore.todayStat, () => {
  checkProgressEvents()
}, { deep: true })
</script>

<template>
  <div class="app-container" :aria-busy="!runtimeReady">
    <!-- 主题背景画布 -->
    <ThemeCanvas :theme="appStore.config.theme" />

    <!-- 主内容 -->
    <template v-if="runtimeReady">
    <div class="app-content">
      <header class="global-nav theme-card" aria-label="EffiLife">
        <RouterLink class="global-brand" to="/" aria-label="EffiLife home">
          <span class="global-brand-mark">E</span>
          <span>EffiLife</span>
        </RouterLink>
        <nav class="global-nav-links desktop-nav-links" :aria-label="t('nav.primary')">
          <RouterLink class="global-nav-link" to="/" :class="{ active: route.path === '/' }" :aria-current="route.path === '/' ? 'page' : undefined">
            <Home :size="16" /> <span>{{ t('nav.home') }}</span>
          </RouterLink>
          <RouterLink class="global-nav-link" data-guide="plans" to="/plans" :class="{ active: route.path.startsWith('/plans') || route.path === '/plan' }" :aria-current="route.path.startsWith('/plans') || route.path === '/plan' ? 'page' : undefined">
            <ClipboardList :size="16" /> <span>{{ t('nav.plans') }}</span>
          </RouterLink>
          <RouterLink class="global-nav-link" data-guide="time" to="/time" :class="{ active: route.path.startsWith('/time') }" :aria-current="route.path.startsWith('/time') ? 'page' : undefined">
            <Clock3 :size="16" /> <span>{{ t('nav.time') }}</span>
          </RouterLink>
          <RouterLink class="global-nav-link" data-guide="records" to="/records" :class="{ active: route.path.startsWith('/records') || route.path.startsWith('/day') }" :aria-current="route.path.startsWith('/records') || route.path.startsWith('/day') ? 'page' : undefined">
            <History :size="16" /> <span>{{ t('nav.records') }}</span>
          </RouterLink>
          <RouterLink class="global-nav-link" data-guide="tasks" to="/tasks" :class="{ active: route.path.startsWith('/tasks') }" :aria-current="route.path.startsWith('/tasks') ? 'page' : undefined">
            <ListTodo :size="16" /> <span>{{ t('nav.tasks') }}</span>
          </RouterLink>
          <RouterLink class="global-nav-link" data-guide="settings" to="/settings" :class="{ active: isSettingsRoute }" :aria-current="isSettingsRoute ? 'page' : undefined">
            <Settings :size="16" /> <span>{{ t('nav.settings') }}</span>
          </RouterLink>
        </nav>
        <button id="global-search-trigger" class="global-search-trigger" type="button" :aria-label="t('search.open')" aria-haspopup="dialog" :aria-expanded="showGlobalSearch" aria-controls="global-search-dialog" aria-keyshortcuts="Control+K Meta+K" @click="showGlobalSearch = true">
          <Search :size="15" /><span>{{ t('search.open') }}</span><kbd>{{ searchShortcut }}</kbd>
        </button>
      </header>
      <nav class="mobile-bottom-nav theme-card" :aria-label="t('nav.primary')">
        <RouterLink class="mobile-bottom-nav-link" to="/" :class="{ active: route.path === '/' }" :aria-current="route.path === '/' ? 'page' : undefined">
          <Home :size="19" /> <span>{{ t('nav.home') }}</span>
        </RouterLink>
          <RouterLink class="mobile-bottom-nav-link" data-guide="plans" to="/plans" :class="{ active: route.path.startsWith('/plans') || route.path === '/plan' }" :aria-current="route.path.startsWith('/plans') || route.path === '/plan' ? 'page' : undefined">
            <ClipboardList :size="19" /> <span>{{ t('nav.plans') }}</span>
          </RouterLink>
          <RouterLink class="mobile-bottom-nav-link" data-guide="time" to="/time" :class="{ active: route.path.startsWith('/time') }" :aria-current="route.path.startsWith('/time') ? 'page' : undefined">
            <Clock3 :size="19" /> <span>{{ t('nav.time') }}</span>
          </RouterLink>
          <RouterLink class="mobile-bottom-nav-link" data-guide="records" to="/records" :class="{ active: route.path.startsWith('/records') || route.path.startsWith('/day') }" :aria-current="route.path.startsWith('/records') || route.path.startsWith('/day') ? 'page' : undefined">
            <History :size="19" /> <span>{{ t('nav.records') }}</span>
          </RouterLink>
          <RouterLink class="mobile-bottom-nav-link" data-guide="tasks" to="/tasks" :class="{ active: route.path.startsWith('/tasks') }" :aria-current="route.path.startsWith('/tasks') ? 'page' : undefined">
          <ListTodo :size="19" /> <span>{{ t('nav.tasks') }}</span>
        </RouterLink>
        <RouterLink class="mobile-bottom-nav-link" data-guide="settings" to="/settings" :class="{ active: isSettingsRoute }" :aria-current="isSettingsRoute ? 'page' : undefined">
          <Settings :size="19" /> <span>{{ t('nav.settings') }}</span>
        </RouterLink>
      </nav>
      <RouterView v-slot="{ Component }">
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </div>

    <!-- 事件弹窗 -->
    <EventPopup />

    <!-- 打卡弹窗 -->
    <CheckinPopup
      :show="showCheckinPopup"
      :plan-name="checkinPlanName"
      @close="onCheckinClose"
      @checkin="onCheckinComplete"
    />

    <!-- 引导覆盖层 -->
    <GuideOverlay />
    <GlobalSearch :open="showGlobalSearch" @close="showGlobalSearch = false" />
    <ToastHost />
    <ConfirmHost />
    </template>

    <div v-else-if="startupError" class="app-startup app-startup-error" role="alert">
      <span class="app-startup-mark">!</span>
      <strong>{{ t('app.startupFailed') }}</strong>
      <span>{{ t('app.startupFailedDescription') }}</span>
      <small v-if="startupErrorMessage" class="app-startup-detail">{{ t('app.startupFailedDetail', { detail: startupErrorMessage }) }}</small>
      <button class="app-startup-retry" type="button" @click="retryStartup">
        {{ t('app.retryStartup') }}
      </button>
    </div>
    <div v-else class="app-startup" role="status" aria-live="polite">
      <span class="app-startup-mark">E</span>
      <span>{{ t('app.starting') }}</span>
    </div>
  </div>
</template>

<style>
.app-container {
  min-height: 100vh;
  background-color: var(--color-bg);
  background-image: var(--theme-bg-gradient, none);
  position: relative;
  transition: background-color 0.3s ease;
}

.app-content {
  position: relative;
  z-index: 2;
  min-height: 100vh;
  padding-top: 64px;
}

.app-startup { position: fixed; inset: 0; z-index: 3; display: grid; place-items: center; align-content: center; gap: 12px; color: var(--color-text-secondary); font-size: 13px; transition: opacity .2s ease, transform .2s ease; }
.app-startup-error { padding: 24px; text-align: center; }
.app-startup-error strong { color: var(--color-text-primary); font-size: 16px; }
.app-startup-error > span:not(.app-startup-mark) { max-width: 360px; }
.app-startup-detail { max-width: min(620px, calc(100vw - 48px)); overflow-wrap: anywhere; color: var(--color-text-tertiary); font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 11px; line-height: 1.5; }
.app-startup-retry { border: 1px solid var(--color-border); border-radius: 10px; padding: 8px 14px; color: var(--color-button-text); background: var(--color-primary); cursor: pointer; font: inherit; }
.app-startup-retry:hover { filter: brightness(1.06); }
.app-startup-mark { display: grid; place-items: center; width: 42px; height: 42px; border-radius: 14px; color: var(--color-button-text); background: var(--color-primary); font-size: 18px; font-weight: 700; box-shadow: var(--theme-box-shadow, 0 8px 30px rgba(0,0,0,.08)); }

.global-nav {
  position: fixed;
  z-index: 10;
  top: 14px;
  left: 50%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  width: min(1120px, calc(100% - 28px));
  min-height: 48px;
  padding: 7px 10px 7px 14px;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  background: var(--color-bg);
  background: color-mix(in srgb, var(--color-bg) 82%, transparent);
  box-shadow: var(--theme-box-shadow, 0 8px 30px rgba(0, 0, 0, .08));
  transform: translateX(-50%);
}

.global-brand, .global-nav-link { text-decoration: none; }
.global-brand { display: inline-flex; align-items: center; gap: 8px; color: var(--color-text-primary); font-size: 14px; font-weight: 700; white-space: nowrap; }
.global-brand-mark { display: grid; place-items: center; width: 27px; height: 27px; border-radius: 9px; color: var(--color-button-text); background: var(--color-primary); font-size: 13px; }
.global-nav-links { display: flex; align-items: center; gap: 3px; }
.global-nav-link { display: inline-flex; align-items: center; gap: 6px; border-radius: 10px; padding: 8px 10px; color: var(--color-text-tertiary); font-size: 12px; transition: color .2s, background-color .2s; }
.global-nav-link:hover, .global-nav-link.active { color: var(--color-text-primary); background: var(--color-primary-muted); }
.mobile-bottom-nav { display: none; }
.global-search-trigger { display: inline-flex; align-items: center; gap: 6px; margin-left: auto; border: 1px solid var(--color-border); border-radius: 10px; padding: 7px 9px; color: var(--color-text-tertiary); background: var(--color-bg-secondary); cursor: pointer; font-size: 11px; }
.global-search-trigger:hover { color: var(--color-text-primary); border-color: var(--color-border-hover); }
.global-search-trigger kbd { border: 1px solid var(--color-border); border-radius: 5px; padding: 1px 4px; color: var(--color-text-tertiary); background: var(--color-bg-elevated); font: inherit; font-size: 10px; }

@media (prefers-reduced-motion: reduce) { .app-startup { transition: none; } }

/* Keep tablet navigation horizontal while reserving room for every module. */
@media (min-width: 681px) and (max-width: 820px) {
  .global-nav { gap: 8px; padding-left: 10px; }
  .global-brand > span:last-child { display: none; }
  .global-nav-links { gap: 1px; }
  .global-nav-link { gap: 4px; padding: 7px 6px; font-size: 11px; }
  .global-search-trigger { margin-left: 0; padding: 7px; }
  .global-search-trigger span, .global-search-trigger kbd { display: none; }
}

/* 全局主题效果 */
.theme-card {
  backdrop-filter: var(--theme-backdrop-filter, none);
  -webkit-backdrop-filter: var(--theme-backdrop-filter, none);
}

.theme-shadow {
  box-shadow: var(--theme-box-shadow, none);
}

.theme-text-glow {
  text-shadow: var(--theme-text-shadow, none);
}

/* 页面切换动画 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity var(--transition-normal), transform var(--transition-normal);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 680px) {
  .app-content { padding-top: 58px; padding-bottom: calc(78px + env(safe-area-inset-bottom)); }
  .global-nav { top: 8px; width: calc(100% - 16px); gap: 8px; }
  .global-brand > span:last-child { display: none; }
  .desktop-nav-links { display: none; }
  .global-search-trigger span, .global-search-trigger kbd { display: none; }
  .global-search-trigger { margin-left: 0; padding: 8px; }
  .mobile-bottom-nav {
    position: fixed;
    z-index: 10;
    right: 0;
    bottom: 0;
    left: 0;
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 2px;
    padding: 6px 8px calc(6px + env(safe-area-inset-bottom));
    border-top: 1px solid var(--color-border);
    background: color-mix(in srgb, var(--color-bg) 88%, transparent);
    box-shadow: 0 -8px 24px rgb(0 0 0 / 8%);
  }
  .mobile-bottom-nav-link {
    display: grid;
    min-height: 54px;
    place-items: center;
    align-content: center;
    gap: 3px;
    border-radius: 11px;
    color: var(--color-text-tertiary);
    font-size: 10px;
    text-decoration: none;
  }
  .mobile-bottom-nav-link.active { color: var(--color-primary); background: var(--color-primary-muted); font-weight: 650; }
}
</style>
