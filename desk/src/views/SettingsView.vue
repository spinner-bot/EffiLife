<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { ArrowLeft, ChevronRight } from 'lucide-vue-next'
import type { Config, ThemeType, SolidThemeConfig, GradientThemeConfig, GlassThemeConfig, NeonThemeConfig } from '@/types'

const router = useRouter()
const appStore = useAppStore()

const config = computed(() => appStore.config)

// 当前视图
type ViewType = 'main' | 'custom' | 'theme' | 'help' | 'archive' | 'reset'
const currentView = ref<ViewType>('main')

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
  alert('设置已保存')
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
]

async function saveTheme() {
  const newConfig: Config = {
    ...config.value,
    theme: {
      type: themeType.value,
      solid: solidConfig.value,
      gradient: gradientConfig.value,
      glass: glassConfig.value,
      neon: neonConfig.value,
    }
  }
  await appStore.saveConfig(newConfig)
  alert('主题已保存')
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
async function resetPlanData() {
  if (!confirm('确定重置所有日计划为默认？此操作不可恢复！')) return
  alert('日计划已重置')
}

async function resetScheduleData() {
  if (!confirm('确定重置日程规则为默认？此操作不可恢复！')) return
  alert('日程规则已重置')
}

async function resetConfig() {
  if (!confirm('确定重置所有设置为默认？')) return
  const defaultConfig: Config = {
    overtime_threshold: 105,
    whiten_k: 0.6,
    show_seconds: true,
    use_24h: true,
    show_ampm: false,
    theme: {
      type: 'solid',
      solid: { bg_window: '#f0f0f0', bg_button: '#e0e0e0', fg_button: '#000000', bg_frame: '#d9d9d9' },
      gradient: { color_start: '#667eea', color_end: '#764ba2', direction: 'to-br', fg_button: '#ffffff', card_bg: 'rgba(255, 255, 255, 0.15)' },
      glass: { bg_color: '#1a1a2e', glass_opacity: 0.1, blur_amount: 10, fg_button: '#ffffff', border_color: 'rgba(255, 255, 255, 0.2)' },
      neon: { bg_color: '#0a0a0f', neon_color: '#00ff88', glow_intensity: 10, fg_button: '#00ff88', accent_color: '#ff00ff' },
    }
  }
  await appStore.saveConfig(defaultConfig)
  overtimeThreshold.value = 105
  themeType.value = 'solid'
  solidConfig.value = defaultConfig.theme.solid!
  gradientConfig.value = defaultConfig.theme.gradient!
  glassConfig.value = defaultConfig.theme.glass!
  neonConfig.value = defaultConfig.theme.neon!
  alert('设置已重置')
}

function contactDeveloper() {
  alert('QQ号：3442386217\n抖音：@浪兮有点浪')
}

// ============ 存档管理 ============
async function exportArchive() {
  try {
    const { save } = await import('@tauri-apps/plugin-dialog')
    const { writeTextFile } = await import('@tauri-apps/plugin-fs')

    const filePath = await save({
      title: '导出存档',
      defaultPath: `efflife_archive_${new Date().toISOString().split('T')[0]}.json`,
      filters: [{ name: 'JSON 文件', extensions: ['json'] }]
    })

    if (!filePath) return

    const archive = {
      version: '1.0',
      exportDate: new Date().toISOString(),
      config: appStore.config,
      plans: appStore.plans,
      scheduleRules: appStore.scheduleRules,
      records: {} as Record<string, unknown>,
      manualPlans: {} as Record<string, string>
    }

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith('efflife_records_')) {
        const date = key.replace('efflife_records_', '')
        archive.records[date] = JSON.parse(localStorage.getItem(key) || '[]')
      }
      if (key && key === 'efflife_manual') {
        archive.manualPlans = JSON.parse(localStorage.getItem(key) || '{}')
      }
    }

    await writeTextFile(filePath, JSON.stringify(archive, null, 2))
    alert('存档导出成功！')
  } catch (e) {
    alert('导出失败：' + (e as Error).message)
  }
}

async function importArchive() {
  try {
    const { open } = await import('@tauri-apps/plugin-dialog')
    const { readTextFile } = await import('@tauri-apps/plugin-fs')

    const filePath = await open({
      title: '导入存档',
      filters: [{ name: 'JSON 文件', extensions: ['json'] }],
      multiple: false,
      directory: false
    })

    if (!filePath) return

    const text = await readTextFile(filePath as string)
    const archive = JSON.parse(text)

    if (!archive.version || !archive.config) {
      alert('无效的存档文件')
      return
    }

    if (!confirm('导入存档将覆盖当前所有数据，确定继续？')) return

    await appStore.saveConfig(archive.config)
    if (archive.plans) await appStore.savePlans(archive.plans)
    if (archive.scheduleRules) await appStore.saveScheduleRules(archive.scheduleRules)

    if (archive.records) {
      for (const [date, records] of Object.entries(archive.records)) {
        localStorage.setItem(`efflife_records_${date}`, JSON.stringify(records))
      }
    }

    if (archive.manualPlans) {
      localStorage.setItem('efflife_manual', JSON.stringify(archive.manualPlans))
    }

    await appStore.init()
    alert('存档导入成功！')
  } catch (e) {
    alert('导入失败：' + (e as Error).message)
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
</script>

<template>
  <div class="settings-view">
    <header class="header">
      <button class="back-btn" @click="currentView === 'main' ? router.push('/') : currentView = 'main'">
        <ArrowLeft :size="16" />
        <span>返回</span>
      </button>
      <h1>设置</h1>
    </header>

    <main class="main-content">
      <!-- 主视图 -->
      <template v-if="currentView === 'main'">
        <div class="settings-list">
          <button class="settings-item" @click="currentView = 'custom'">
            <span>自定义</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="currentView = 'theme'">
            <span>主题</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="router.push('/audio-settings')">
            <span>声音</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="router.push('/event-manager')">
            <span>事件管理</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="currentView = 'help'">
            <span>帮助</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="currentView = 'archive'">
            <span>存档管理</span>
            <ChevronRight :size="16" />
          </button>
          <button class="settings-item" @click="currentView = 'reset'">
            <span>恢复</span>
            <ChevronRight :size="16" />
          </button>
        </div>

        <footer class="credits">
          <p>开发者：浪兮spinner_bot</p>
          <p>抖音@浪兮有点浪</p>
        </footer>
      </template>

      <!-- 自定义设置 -->
      <template v-else-if="currentView === 'custom'">
        <h2>自定义设置</h2>

        <div class="form-section">
          <label>标签超限阈值</label>
          <div class="threshold-control">
            <button class="threshold-btn" @click="subThreshold">-</button>
            <span class="threshold-value">当前阈值：{{ overtimeThreshold }}%</span>
            <button class="threshold-btn" @click="addThreshold">+</button>
          </div>
        </div>

        <div class="form-section">
          <label>时间显示</label>
          <div class="checkbox-list">
            <label><input type="checkbox" v-model="showSeconds" /><span>显示秒</span></label>
            <label><input type="checkbox" v-model="use24h" /><span>24小时制</span></label>
            <label><input type="checkbox" v-model="showAmPm" /><span>半日显示(AM/PM)</span></label>
          </div>
        </div>

        <div class="form-actions">
          <button class="btn secondary" @click="currentView = 'main'">返回</button>
          <button class="btn primary" @click="saveCustomSettings">保存</button>
        </div>
      </template>

      <!-- 主题设置 -->
      <template v-else-if="currentView === 'theme'">
        <h2>主题设置</h2>

        <div class="form-section">
          <label>基础主题</label>
          <div class="theme-list">
            <button
              v-for="theme in availableThemes.filter(t => t.category === '基础')"
              :key="theme.type"
              class="theme-card"
              :class="{ active: themeType === theme.type }"
              @click="themeType = theme.type"
            >
              <div class="theme-info">
                <span class="theme-name">{{ theme.name }}</span>
                <span class="theme-desc">{{ theme.description }}</span>
              </div>
              <span v-if="themeType === theme.type" class="selected">✓</span>
            </button>
          </div>
        </div>

        <div class="form-section">
          <label>艺术风格</label>
          <div class="theme-list">
            <button
              v-for="theme in availableThemes.filter(t => t.category === '艺术')"
              :key="theme.type"
              class="theme-card"
              :class="{ active: themeType === theme.type }"
              @click="themeType = theme.type"
            >
              <div class="theme-info">
                <span class="theme-name">{{ theme.name }}</span>
                <span class="theme-desc">{{ theme.description }}</span>
              </div>
              <span v-if="themeType === theme.type" class="selected">✓</span>
            </button>
          </div>
        </div>

        <div class="form-section">
          <label>自然风格</label>
          <div class="theme-list">
            <button
              v-for="theme in availableThemes.filter(t => t.category === '自然')"
              :key="theme.type"
              class="theme-card"
              :class="{ active: themeType === theme.type }"
              @click="themeType = theme.type"
            >
              <div class="theme-info">
                <span class="theme-name">{{ theme.name }}</span>
                <span class="theme-desc">{{ theme.description }}</span>
              </div>
              <span v-if="themeType === theme.type" class="selected">✓</span>
            </button>
          </div>
        </div>

        <div class="form-section">
          <label>科技风格</label>
          <div class="theme-list">
            <button
              v-for="theme in availableThemes.filter(t => t.category === '科技')"
              :key="theme.type"
              class="theme-card"
              :class="{ active: themeType === theme.type }"
              @click="themeType = theme.type"
            >
              <div class="theme-info">
                <span class="theme-name">{{ theme.name }}</span>
                <span class="theme-desc">{{ theme.description }}</span>
              </div>
              <span v-if="themeType === theme.type" class="selected">✓</span>
            </button>
          </div>
        </div>

        <!-- 纯色主题配置 -->
        <template v-if="themeType === 'solid'">
          <div class="form-section">
            <label>颜色配置</label>
            <div class="color-settings">
              <div class="color-row">
                <span>窗口背景色</span>
                <input type="text" v-model="solidConfig.bg_window" class="color-input" />
                <button class="btn small" @click="pickColor('solid_bg_window')">选择</button>
              </div>
              <div class="color-row">
                <span>按钮背景色</span>
                <input type="text" v-model="solidConfig.bg_button" class="color-input" />
                <button class="btn small" @click="pickColor('solid_bg_button')">选择</button>
              </div>
              <div class="color-row">
                <span>按钮文字色</span>
                <input type="text" v-model="solidConfig.fg_button" class="color-input" />
                <button class="btn small" @click="pickColor('solid_fg_button')">选择</button>
              </div>
            </div>
            <div class="preset-buttons">
              <span>预设方案：</span>
              <button class="btn small" @click="applySolidPreset('default')">默认</button>
              <button class="btn small" @click="applySolidPreset('dark')">深色</button>
              <button class="btn small" @click="applySolidPreset('light')">浅色</button>
            </div>
          </div>
        </template>

        <!-- 渐变主题配置 -->
        <template v-if="themeType === 'gradient'">
          <div class="form-section">
            <label>渐变配置</label>
            <div class="color-settings">
              <div class="color-row">
                <span>起始颜色</span>
                <input type="text" v-model="gradientConfig.color_start" class="color-input" />
                <button class="btn small" @click="pickColor('gradient_color_start')">选择</button>
              </div>
              <div class="color-row">
                <span>结束颜色</span>
                <input type="text" v-model="gradientConfig.color_end" class="color-input" />
                <button class="btn small" @click="pickColor('gradient_color_end')">选择</button>
              </div>
              <div class="color-row">
                <span>渐变方向</span>
                <select v-model="gradientConfig.direction" class="select-input">
                  <option value="to-right">向右 →</option>
                  <option value="to-left">向左 ←</option>
                  <option value="to-bottom">向下 ↓</option>
                  <option value="to-top">向上 ↑</option>
                  <option value="to-br">右下 ↘</option>
                  <option value="to-tl">左上 ↖</option>
                </select>
              </div>
            </div>
            <div class="preset-buttons">
              <span>预设方案：</span>
              <button class="btn small" @click="applyGradientPreset('purple')">紫色</button>
              <button class="btn small" @click="applyGradientPreset('blue')">蓝色</button>
              <button class="btn small" @click="applyGradientPreset('sunset')">日落</button>
              <button class="btn small" @click="applyGradientPreset('forest')">森林</button>
            </div>
          </div>
        </template>

        <!-- 玻璃主题配置 -->
        <template v-if="themeType === 'glass'">
          <div class="form-section">
            <label>玻璃配置</label>
            <div class="color-settings">
              <div class="color-row">
                <span>背景颜色</span>
                <input type="text" v-model="glassConfig.bg_color" class="color-input" />
                <button class="btn small" @click="pickColor('glass_bg_color')">选择</button>
              </div>
              <div class="color-row">
                <span>玻璃透明度</span>
                <input type="range" v-model.number="glassConfig.glass_opacity" min="0.05" max="0.5" step="0.05" class="slider" />
                <span class="slider-value">{{ glassConfig.glass_opacity.toFixed(2) }}</span>
              </div>
              <div class="color-row">
                <span>模糊程度</span>
                <input type="range" v-model.number="glassConfig.blur_amount" min="0" max="30" step="2" class="slider" />
                <span class="slider-value">{{ glassConfig.blur_amount }}px</span>
              </div>
            </div>
            <div class="preset-buttons">
              <span>预设方案：</span>
              <button class="btn small" @click="applyGlassPreset('dark')">深色</button>
              <button class="btn small" @click="applyGlassPreset('light')">浅色</button>
              <button class="btn small" @click="applyGlassPreset('blue')">蓝色</button>
            </div>
          </div>
        </template>

        <!-- 霓虹主题配置 -->
        <template v-if="themeType === 'neon'">
          <div class="form-section">
            <label>霓虹配置</label>
            <div class="color-settings">
              <div class="color-row">
                <span>背景颜色</span>
                <input type="text" v-model="neonConfig.bg_color" class="color-input" />
                <button class="btn small" @click="pickColor('neon_bg_color')">选择</button>
              </div>
              <div class="color-row">
                <span>霓虹颜色</span>
                <input type="text" v-model="neonConfig.neon_color" class="color-input" />
                <button class="btn small" @click="pickColor('neon_neon_color')">选择</button>
              </div>
              <div class="color-row">
                <span>强调颜色</span>
                <input type="text" v-model="neonConfig.accent_color" class="color-input" />
                <button class="btn small" @click="pickColor('neon_accent_color')">选择</button>
              </div>
              <div class="color-row">
                <span>发光强度</span>
                <input type="range" v-model.number="neonConfig.glow_intensity" min="0" max="30" step="2" class="slider" />
                <span class="slider-value">{{ neonConfig.glow_intensity }}px</span>
              </div>
            </div>
            <div class="preset-buttons">
              <span>预设方案：</span>
              <button class="btn small" @click="applyNeonPreset('green')">绿色</button>
              <button class="btn small" @click="applyNeonPreset('pink')">粉色</button>
              <button class="btn small" @click="applyNeonPreset('cyan')">青色</button>
              <button class="btn small" @click="applyNeonPreset('rainbow')">彩虹</button>
            </div>
          </div>
        </template>

        <div class="form-actions">
          <button class="btn secondary" @click="currentView = 'main'">返回</button>
          <button class="btn primary" @click="saveTheme">保存</button>
        </div>
      </template>

      <!-- 帮助 -->
      <template v-else-if="currentView === 'help'">
        <div class="help-header">
          <h2>帮助中心</h2>
          <button class="btn small" @click="contactDeveloper">联系开发者</button>
        </div>
        <div class="help-content">
          <p>浪兮效率时钟是一款基于分类时间管理理念的桌面工具。</p>
          <p>它借鉴3×8时间管理法，帮助用户将一天的时间按自定义类别进行计划与追踪。</p>
          <h3>主要功能</h3>
          <ul>
            <li>两种计划模式（切分制/分配制）</li>
            <li>多套日计划预设</li>
            <li>日程自动分配规则</li>
            <li>记录管理（增删改查）</li>
            <li>日历视图</li>
            <li>4种主题风格</li>
            <li>数据备份与恢复</li>
          </ul>
        </div>
        <button class="btn secondary full" @click="currentView = 'main'">返回</button>
      </template>

      <!-- 存档管理 -->
      <template v-else-if="currentView === 'archive'">
        <h2>存档管理</h2>
        <div class="archive-actions">
          <button class="btn primary full" @click="exportArchive">导出存档</button>
          <button class="btn primary full" @click="importArchive">导入存档</button>
        </div>
        <button class="btn secondary full" @click="currentView = 'main'">返回</button>
      </template>

      <!-- 恢复 -->
      <template v-else-if="currentView === 'reset'">
        <h2>恢复设置</h2>
        <div class="reset-actions">
          <button class="btn secondary full" @click="resetPlanData">重置计划数据</button>
          <button class="btn secondary full" @click="resetScheduleData">重置日程数据</button>
          <button class="btn secondary full" @click="resetConfig">重置设置数据</button>
        </div>
        <button class="btn secondary full" @click="currentView = 'main'">返回</button>
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

.credits {
  text-align: center;
  padding: var(--spacing-xl) 0;
  color: var(--color-text-tertiary);
  font-size: 0.75rem;
  line-height: 1.8;
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
</style>
