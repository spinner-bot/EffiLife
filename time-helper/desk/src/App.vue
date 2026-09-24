<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { ref, onMounted, watch, computed } from 'vue'
import ThemeCanvas from './theme/ThemeCanvas.vue'
import { getThemeCssVariables } from './theme/ThemeEngine'
import { AudioManager, EventSystem, EventPopup } from './audio'
import { CheckinSystem, CheckinPopup } from './data'
import { GuideManager, GuideOverlay } from './guide'
import { TodoService } from './services/todoService'
import { Home, ClipboardList, ListTodo, Clock3, Settings } from 'lucide-vue-next'
import { useI18n } from '@/i18n'

const appStore = useAppStore()
const route = useRoute()
const { t } = useI18n()

const themeVariables = computed(() => getThemeCssVariables(appStore.config.theme))

// 打卡弹窗状态
const showCheckinPopup = ref(false)
const checkinPlanName = ref('')
// 是否已为今天的100%展示过打卡弹窗
const hasPromptedCheckin = ref(false)

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
  appStore.refreshTodayData()
}

function onCheckinClose() {
  showCheckinPopup.value = false
}

onMounted(async () => {
  await appStore.init()
  await TodoService.migrateLegacyLocalStorage()
  applyTheme()

  // 启动背景音乐
  AudioManager.startBgm()

  // 自动补打卡检查（跨天后如果昨天完成了计划但没打卡）
  const autoCheckinResult = CheckinSystem.autoCheckinIfMissed()

  if (autoCheckinResult.result === 'checked') {
    // 自动补打卡成功，通知用户
    EventSystem.triggerEvent(
      'achievement_unlocked',
      '自动补打卡',
      `已为您补打昨天的卡，连续 ${autoCheckinResult.streak} 天！`
    )
  } else if (autoCheckinResult.result === 'streak-broken') {
    // 连续天数已断，但昨天有完成的计划，添加到收件箱让用户手动补打
    const yesterdayRecords = CheckinSystem.getYesterdayCompletedRecords()
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

watch(() => appStore.config, applyTheme, { deep: true })

// 监听统计数据变化，检查事件
watch(() => appStore.todayStat, () => {
  checkProgressEvents()
}, { deep: true })
</script>

<template>
  <div class="app-container">
    <!-- 主题背景画布 -->
    <ThemeCanvas :theme="appStore.config.theme" />

    <!-- 主内容 -->
    <div class="app-content">
      <header class="global-nav theme-card" aria-label="EffiLife">
        <RouterLink class="global-brand" to="/" aria-label="EffiLife home">
          <span class="global-brand-mark">E</span>
          <span>EffiLife</span>
        </RouterLink>
        <nav class="global-nav-links" :aria-label="t('nav.primary')">
          <RouterLink class="global-nav-link" to="/" :class="{ active: route.path === '/' }">
            <Home :size="16" /> <span>{{ t('nav.home') }}</span>
          </RouterLink>
          <RouterLink class="global-nav-link" to="/plans" :class="{ active: route.path.startsWith('/plans') || route.path === '/plan' }">
            <ClipboardList :size="16" /> <span>{{ t('nav.plans') }}</span>
          </RouterLink>
          <RouterLink class="global-nav-link" to="/tasks" :class="{ active: route.path.startsWith('/tasks') }">
            <ListTodo :size="16" /> <span>{{ t('nav.tasks') }}</span>
          </RouterLink>
          <RouterLink class="global-nav-link" to="/records" :class="{ active: route.path.startsWith('/records') || route.path.startsWith('/day') }">
            <Clock3 :size="16" /> <span>{{ t('nav.records') }}</span>
          </RouterLink>
          <RouterLink class="global-nav-link" to="/settings" :class="{ active: route.path.startsWith('/settings') }">
            <Settings :size="16" /> <span>{{ t('nav.settings') }}</span>
          </RouterLink>
        </nav>
      </header>
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
  .app-content { padding-top: 58px; }
  .global-nav { top: 8px; width: calc(100% - 16px); gap: 8px; }
  .global-brand > span:last-child { display: none; }
  .global-nav-links { flex: 1; justify-content: space-between; }
  .global-nav-link { flex: 1; justify-content: center; padding: 8px 5px; }
  .global-nav-link span { display: none; }
}
</style>
