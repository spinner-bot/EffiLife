<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { onMounted, watch, computed } from 'vue'
import ThemeCanvas from './theme/ThemeCanvas.vue'
import { getThemeStyle } from './theme/ThemeEngine'
import { AudioManager, EventSystem, EventPopup } from './audio'

const appStore = useAppStore()

const themeStyle = computed(() => getThemeStyle(appStore.config.theme))

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

  // 高级效果
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

  // 检查完成度事件
  EventSystem.checkProgressEvent(progress, planName)

  // 检查低完成度预警
  EventSystem.checkLowProgressWarning(progress, planName)
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
