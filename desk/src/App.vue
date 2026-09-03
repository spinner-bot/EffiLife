<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { onMounted, watch } from 'vue'

const appStore = useAppStore()

// 应用主题到 CSS 变量
function applyTheme() {
  const theme = appStore.config.theme
  const root = document.documentElement

  if (theme.type === 'solid' && theme.solid) {
    root.style.setProperty('--color-bg', theme.solid.bg_window)
    root.style.setProperty('--color-bg-secondary', adjustColor(theme.solid.bg_window, 10))
    root.style.setProperty('--color-bg-tertiary', adjustColor(theme.solid.bg_window, 20))
    root.style.setProperty('--color-border', adjustColor(theme.solid.bg_window, 30))
    root.style.setProperty('--color-border-hover', adjustColor(theme.solid.bg_window, 40))
  }
}

// 调整颜色亮度
function adjustColor(hex: string, amount: number): string {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = Math.min(255, Math.max(0, (num >> 16) + amount))
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00FF) + amount))
  const b = Math.min(255, Math.max(0, (num & 0x0000FF) + amount))
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`
}

onMounted(async () => {
  await appStore.init()
  applyTheme()
})

// 监听配置变化，自动应用主题
watch(() => appStore.config, applyTheme, { deep: true })
</script>

<template>
  <div class="app-container">
    <RouterView />
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  background-color: var(--color-bg);
}
</style>
