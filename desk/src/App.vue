<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { ref, onMounted, watch, computed } from 'vue'
import ThemeCanvas from './theme/ThemeCanvas.vue'
import { getThemeStyle } from './theme/ThemeEngine'
import { AudioManager, EventSystem, EventPopup } from './audio'
import { CheckinSystem, CheckinPopup } from './data'

const appStore = useAppStore()
const route = useRoute()

const themeStyle = computed(() => getThemeStyle(appStore.config.theme))

// 打卡弹窗状态
const showCheckinPopup = ref(false)
const checkinPlanName = ref('')
// 是否已为今天的100%展示过打卡弹窗
const hasPromptedCheckin = ref(false)

// 应用主题到 CSS 变量
function applyTheme() {
  const style = themeStyle.value
  const root = document.documentElement

  root.style.setProperty('--color-bg', style.bgColor)
  root.style.setProperty('--color-text-primary', style.textColor)
  root.style.setProperty('--color-text-secondary', style.textSecondary)
  root.style.setProperty('--color-text-tertiary', style.textTertiary)
  root.style.setProperty('--color-border', style.borderColor)
  root.style.setProperty('--color-button-bg', style.buttonBg)
  root.style.setProperty('--color-button-text', style.buttonText)
  root.style.setProperty('--color-primary', style.accentColor)
  root.style.setProperty('--color-bg-secondary', style.cardBg)

  if (style.backdropFilter) {
    root.style.setProperty('--theme-backdrop-filter', style.backdropFilter)
  }
  if (style.boxShadow) {
    root.style.setProperty('--theme-box-shadow', style.boxShadow)
  }
  if (style.textShadow) {
    root.style.setProperty('--theme-text-shadow', style.textShadow)
  }
  if (style.bgGradient) {
    root.style.setProperty('--theme-bg-gradient', style.bgGradient)
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

  // 检查多规则预警（支持延迟发布）
  EventSystem.checkWarnings(progress, planName)
}

// 打卡完成回调
function onCheckinComplete(streak: number) {
  showCheckinPopup.value = false
  // 刷新主页数据
  const homeView = document.querySelector('.home-view')?.__vue_app__
  // 通过 store 刷新
  appStore.refreshTodayData()
}

function onCheckinClose() {
  showCheckinPopup.value = false
}

onMounted(async () => {
  await appStore.init()
  applyTheme()

  // 启动背景音乐
  AudioManager.startBgm()

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
      <RouterView />
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
</style>
