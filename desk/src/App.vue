<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { onMounted, watch } from 'vue'

const appStore = useAppStore()

// 计算颜色亮度 (0-255)
function getLuminance(hex: string): number {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = (num >> 16) & 255
  const g = (num >> 8) & 255
  const b = num & 255
  return (r * 299 + g * 587 + b * 114) / 1000
}

// 根据背景色返回合适的文字颜色
function getTextColor(bgHex: string): { primary: string; secondary: string; tertiary: string } {
  const luminance = getLuminance(bgHex)
  if (luminance > 128) {
    // 浅色背景 -> 深色文字
    return { primary: '#18181b', secondary: '#52525b', tertiary: '#a1a1aa' }
  } else {
    // 深色背景 -> 浅色文字
    return { primary: '#fafafa', secondary: '#a1a1aa', tertiary: '#71717a' }
  }
}

// 应用主题到 CSS 变量
function applyTheme() {
  const theme = appStore.config.theme
  const root = document.documentElement

  if (theme.type === 'solid' && theme.solid) {
    const bg = theme.solid.bg_window
    const textColor = getTextColor(bg)

    root.style.setProperty('--color-bg', bg)
    root.style.setProperty('--color-bg-secondary', adjustColor(bg, 10))
    root.style.setProperty('--color-bg-tertiary', adjustColor(bg, 20))
    root.style.setProperty('--color-border', adjustColor(bg, 30))
    root.style.setProperty('--color-border-hover', adjustColor(bg, 40))

    // 动态设置文字颜色
    root.style.setProperty('--color-text-primary', textColor.primary)
    root.style.setProperty('--color-text-secondary', textColor.secondary)
    root.style.setProperty('--color-text-tertiary', textColor.tertiary)

    // 按钮颜色也根据主题调整
    root.style.setProperty('--color-button-bg', theme.solid.bg_button)
    root.style.setProperty('--color-button-text', theme.solid.fg_button)
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
