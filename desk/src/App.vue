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
    return { primary: '#18181b', secondary: '#52525b', tertiary: '#a1a1aa' }
  } else {
    return { primary: '#fafafa', secondary: '#a1a1aa', tertiary: '#71717a' }
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

// 应用主题到 CSS 变量
function applyTheme() {
  const theme = appStore.config.theme
  const root = document.documentElement

  // 清除之前的主题类
  root.classList.remove('theme-solid', 'theme-gradient', 'theme-glass', 'theme-neon')

  switch (theme.type) {
    case 'solid':
      applySolidTheme(theme.solid)
      root.classList.add('theme-solid')
      break
    case 'gradient':
      applyGradientTheme(theme.gradient)
      root.classList.add('theme-gradient')
      break
    case 'glass':
      applyGlassTheme(theme.glass)
      root.classList.add('theme-glass')
      break
    case 'neon':
      applyNeonTheme(theme.neon)
      root.classList.add('theme-neon')
      break
  }
}

function applySolidTheme(solid?: typeof appStore.config.theme.solid) {
  if (!solid) return
  const root = document.documentElement
  const textColor = getTextColor(solid.bg_window)

  root.style.setProperty('--color-bg', solid.bg_window)
  root.style.setProperty('--color-bg-secondary', adjustColor(solid.bg_window, 10))
  root.style.setProperty('--color-bg-tertiary', adjustColor(solid.bg_window, 20))
  root.style.setProperty('--color-border', adjustColor(solid.bg_window, 30))
  root.style.setProperty('--color-border-hover', adjustColor(solid.bg_window, 40))
  root.style.setProperty('--color-text-primary', textColor.primary)
  root.style.setProperty('--color-text-secondary', textColor.secondary)
  root.style.setProperty('--color-text-tertiary', textColor.tertiary)
  root.style.setProperty('--color-button-bg', solid.bg_button)
  root.style.setProperty('--color-button-text', solid.fg_button)
  root.style.setProperty('--theme-bg-gradient', 'none')
  root.style.setProperty('--theme-card-bg', solid.bg_window)
  root.style.setProperty('--theme-glow', 'none')
}

function applyGradientTheme(gradient?: typeof appStore.config.theme.gradient) {
  if (!gradient) return
  const root = document.documentElement
  const textColor = getTextColor(gradient.color_start)

  const directionMap = {
    'to-right': '90deg',
    'to-left': '270deg',
    'to-bottom': '180deg',
    'to-top': '0deg',
    'to-br': '135deg',
    'to-tl': '315deg'
  }

  root.style.setProperty('--color-bg', gradient.color_start)
  root.style.setProperty('--color-bg-secondary', gradient.card_bg)
  root.style.setProperty('--color-bg-tertiary', gradient.card_bg)
  root.style.setProperty('--color-border', 'rgba(255, 255, 255, 0.2)')
  root.style.setProperty('--color-border-hover', 'rgba(255, 255, 255, 0.3)')
  root.style.setProperty('--color-text-primary', textColor.primary)
  root.style.setProperty('--color-text-secondary', textColor.secondary)
  root.style.setProperty('--color-text-tertiary', textColor.tertiary)
  root.style.setProperty('--color-button-bg', 'rgba(255, 255, 255, 0.2)')
  root.style.setProperty('--color-button-text', gradient.fg_button)
  root.style.setProperty('--theme-bg-gradient', `linear-gradient(${directionMap[gradient.direction]}, ${gradient.color_start}, ${gradient.color_end})`)
  root.style.setProperty('--theme-card-bg', gradient.card_bg)
  root.style.setProperty('--theme-glow', 'none')
}

function applyGlassTheme(glass?: typeof appStore.config.theme.glass) {
  if (!glass) return
  const root = document.documentElement
  const textColor = getTextColor(glass.bg_color)

  root.style.setProperty('--color-bg', glass.bg_color)
  root.style.setProperty('--color-bg-secondary', `rgba(255, 255, 255, ${glass.glass_opacity})`)
  root.style.setProperty('--color-bg-tertiary', `rgba(255, 255, 255, ${glass.glass_opacity + 0.05})`)
  root.style.setProperty('--color-border', glass.border_color)
  root.style.setProperty('--color-border-hover', 'rgba(255, 255, 255, 0.3)')
  root.style.setProperty('--color-text-primary', textColor.primary)
  root.style.setProperty('--color-text-secondary', textColor.secondary)
  root.style.setProperty('--color-text-tertiary', textColor.tertiary)
  root.style.setProperty('--color-button-bg', `rgba(255, 255, 255, ${glass.glass_opacity + 0.1})`)
  root.style.setProperty('--color-button-text', glass.fg_button)
  root.style.setProperty('--theme-bg-gradient', 'none')
  root.style.setProperty('--theme-card-bg', `rgba(255, 255, 255, ${glass.glass_opacity})`)
  root.style.setProperty('--theme-blur', `${glass.blur_amount}px`)
  root.style.setProperty('--theme-glow', 'none')
}

function applyNeonTheme(neon?: typeof appStore.config.theme.neon) {
  if (!neon) return
  const root = document.documentElement

  root.style.setProperty('--color-bg', neon.bg_color)
  root.style.setProperty('--color-bg-secondary', 'rgba(255, 255, 255, 0.05)')
  root.style.setProperty('--color-bg-tertiary', 'rgba(255, 255, 255, 0.08)')
  root.style.setProperty('--color-border', `${neon.neon_color}40`)
  root.style.setProperty('--color-border-hover', `${neon.neon_color}60`)
  root.style.setProperty('--color-text-primary', neon.neon_color)
  root.style.setProperty('--color-text-secondary', `${neon.neon_color}aa`)
  root.style.setProperty('--color-text-tertiary', `${neon.neon_color}66`)
  root.style.setProperty('--color-button-bg', 'rgba(255, 255, 255, 0.05)')
  root.style.setProperty('--color-button-text', neon.fg_button)
  root.style.setProperty('--color-primary', neon.neon_color)
  root.style.setProperty('--color-accent', neon.accent_color)
  root.style.setProperty('--theme-bg-gradient', 'none')
  root.style.setProperty('--theme-card-bg', 'rgba(255, 255, 255, 0.03)')
  root.style.setProperty('--theme-glow', `0 0 ${neon.glow_intensity}px ${neon.neon_color}`)
  root.style.setProperty('--theme-glow-strong', `0 0 ${neon.glow_intensity * 2}px ${neon.neon_color}`)
}

onMounted(async () => {
  await appStore.init()
  applyTheme()
})

watch(() => appStore.config, applyTheme, { deep: true })
</script>

<template>
  <div class="app-container">
    <RouterView />
  </div>
</template>

<style>
.app-container {
  min-height: 100vh;
  background-color: var(--color-bg);
  background-image: var(--theme-bg-gradient, none);
  transition: background-color 0.3s ease, background-image 0.3s ease;
}

/* 玻璃主题模糊效果 */
.theme-glass .app-container::before {
  content: '';
  position: fixed;
  inset: 0;
  background:
    radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.2) 0%, transparent 50%);
  z-index: -1;
}

/* 霓虹主题发光效果 */
.theme-neon .app-container {
  background-image:
    radial-gradient(circle at 50% 50%, rgba(0, 255, 136, 0.03) 0%, transparent 70%);
}

.theme-neon button:hover {
  box-shadow: var(--theme-glow);
}

.theme-neon .stats-card,
.theme-neon .nav-btn,
.theme-neon .settings-item {
  border-color: var(--color-border);
  transition: all 0.3s ease;
}

.theme-neon .stats-card:hover,
.theme-neon .nav-btn:hover,
.theme-neon .settings-item:hover {
  box-shadow: var(--theme-glow);
  border-color: var(--color-border-hover);
}

.theme-neon .time-display {
  text-shadow: var(--theme-glow-strong);
}

.theme-neon .progress-value {
  text-shadow: var(--theme-glow);
}

/* 玻璃主题卡片效果 */
.theme-glass .stats-card,
.theme-glass .nav-btn,
.theme-glass .settings-item,
.theme-glass .record-item,
.theme-glass .plan-card {
  backdrop-filter: blur(var(--theme-blur, 10px));
  -webkit-backdrop-filter: blur(var(--theme-blur, 10px));
}

/* 渐变主题卡片效果 */
.theme-gradient .stats-card,
.theme-gradient .nav-btn,
.theme-gradient .settings-item,
.theme-gradient .record-item,
.theme-gradient .plan-card {
  background: var(--theme-card-bg);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
</style>
