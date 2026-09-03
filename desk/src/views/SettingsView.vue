<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { ArrowLeft, ChevronRight } from 'lucide-vue-next'
import type { Config, ThemeType, SolidThemeConfig } from '@/types'

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
  if (overtimeThreshold.value < 150) {
    overtimeThreshold.value++
  }
}

function subThreshold() {
  if (overtimeThreshold.value > 100) {
    overtimeThreshold.value--
  }
}

// ============ 主题设置 ============
const themeType = ref<ThemeType>(config.value.theme.type || 'solid')
const solidConfig = ref<SolidThemeConfig>(config.value.theme.solid || {
  bg_window: '#f0f0f0',
  bg_button: '#e0e0e0',
  fg_button: '#000000',
  bg_frame: '#d9d9d9'
})

// 可用的主题类型（预留扩展）
const availableThemes = [
  { type: 'solid' as ThemeType, name: '纯色', description: '简洁的纯色主题', available: true },
  { type: 'gradient' as ThemeType, name: '渐变', description: '渐变背景主题', available: false },
  { type: 'glass' as ThemeType, name: '玻璃', description: '毛玻璃效果主题', available: false },
  { type: 'neon' as ThemeType, name: '霓虹', description: '霓虹灯效果主题', available: false },
]

async function saveTheme() {
  const newConfig: Config = {
    ...config.value,
    theme: {
      type: themeType.value,
      solid: themeType.value === 'solid' ? solidConfig.value : undefined,
    }
  }
  await appStore.saveConfig(newConfig)
  alert('主题已保存')
}

function applyPreset(preset: 'default' | 'dark' | 'light') {
  if (preset === 'default') {
    solidConfig.value = {
      bg_window: '#f0f0f0',
      bg_button: '#e0e0e0',
      fg_button: '#000000',
      bg_frame: '#d9d9d9'
    }
  } else if (preset === 'dark') {
    solidConfig.value = {
      bg_window: '#1a1a2e',
      bg_button: '#16213e',
      fg_button: '#eaeaea',
      bg_frame: '#0f3460'
    }
  } else {
    solidConfig.value = {
      bg_window: '#ffffff',
      bg_button: '#f5f5f5',
      fg_button: '#333333',
      bg_frame: '#e0e0e0'
    }
  }
}

function pickColor(target: 'bg' | 'button' | 'fg' | 'frame') {
  const input = document.createElement('input')
  input.type = 'color'
  input.value = target === 'bg' ? solidConfig.value.bg_window
    : target === 'button' ? solidConfig.value.bg_button
    : target === 'fg' ? solidConfig.value.fg_button
    : solidConfig.value.bg_frame
  input.onchange = () => {
    const color = input.value
    if (target === 'bg') solidConfig.value.bg_window = color
    else if (target === 'button') solidConfig.value.bg_button = color
    else if (target === 'fg') solidConfig.value.fg_button = color
    else solidConfig.value.bg_frame = color
  }
  input.click()
}

// ============ 存档管理 ============
async function exportArchive() {
  try {
    // 收集所有数据
    const archive = {
      version: '1.0',
      exportDate: new Date().toISOString(),
      config: appStore.config,
      plans: appStore.plans,
      scheduleRules: appStore.scheduleRules,
      records: {} as Record<string, unknown>,
      manualPlans: {} as Record<string, string>
    }

    // 收集所有日期的记录
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

    // 创建下载
    const blob = new Blob([JSON.stringify(archive, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `efflife_archive_${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
    alert('存档导出成功！')
  } catch (e) {
    alert('导出失败：' + (e as Error).message)
  }
}

async function importArchive() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async () => {
    const file = input.files?.[0]
    if (!file) return

    try {
      const text = await file.text()
      const archive = JSON.parse(text)

      if (!archive.version || !archive.config) {
        alert('无效的存档文件')
        return
      }

      if (!confirm('导入存档将覆盖当前所有数据，确定继续？')) return

      // 导入配置
      await appStore.saveConfig(archive.config)

      // 导入计划
      if (archive.plans) {
        await appStore.savePlans(archive.plans)
      }

      // 导入日程规则
      if (archive.scheduleRules) {
        await appStore.saveScheduleRules(archive.scheduleRules)
      }

      // 导入记录
      if (archive.records) {
        for (const [date, records] of Object.entries(archive.records)) {
          localStorage.setItem(`efflife_records_${date}`, JSON.stringify(records))
        }
      }

      // 导入手动计划
      if (archive.manualPlans) {
        localStorage.setItem('efflife_manual', JSON.stringify(archive.manualPlans))
      }

      // 刷新数据
      await appStore.init()
      alert('存档导入成功！')
    } catch (e) {
      alert('导入失败：' + (e as Error).message)
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
      solid: {
        bg_window: '#f0f0f0',
        bg_button: '#e0e0e0',
        fg_button: '#000000',
        bg_frame: '#d9d9d9'
      }
    }
  }
  await appStore.saveConfig(defaultConfig)
  overtimeThreshold.value = 105
  themeType.value = 'solid'
  solidConfig.value = {
    bg_window: '#f0f0f0',
    bg_button: '#e0e0e0',
    fg_button: '#000000',
    bg_frame: '#d9d9d9'
  }
  alert('设置已重置')
}

function contactDeveloper() {
  alert('QQ号：3442386217\n抖音：@浪兮有点浪')
}

// 同步配置到本地状态
watch(() => config.value, (newConfig) => {
  overtimeThreshold.value = newConfig.overtime_threshold
  showSeconds.value = newConfig.show_seconds
  use24h.value = newConfig.use_24h
  showAmPm.value = newConfig.show_ampm
  themeType.value = newConfig.theme.type || 'solid'
  if (newConfig.theme.solid) {
    solidConfig.value = { ...newConfig.theme.solid }
  }
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
            <label>
              <input type="checkbox" v-model="showSeconds" />
              <span>显示秒</span>
            </label>
            <label>
              <input type="checkbox" v-model="use24h" />
              <span>24小时制</span>
            </label>
            <label>
              <input type="checkbox" v-model="showAmPm" />
              <span>半日显示(AM/PM)</span>
            </label>
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
          <label>选择主题</label>
          <div class="theme-list">
            <button
              v-for="theme in availableThemes"
              :key="theme.type"
              class="theme-card"
              :class="{ active: themeType === theme.type, disabled: !theme.available }"
              :disabled="!theme.available"
              @click="theme.available && (themeType = theme.type)"
            >
              <div class="theme-info">
                <span class="theme-name">{{ theme.name }}</span>
                <span class="theme-desc">{{ theme.description }}</span>
              </div>
              <span v-if="!theme.available" class="coming-soon">即将推出</span>
              <span v-else-if="themeType === theme.type" class="selected">✓</span>
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
                <button class="btn small" @click="pickColor('bg')">选择</button>
              </div>
              <div class="color-row">
                <span>按钮背景色</span>
                <input type="text" v-model="solidConfig.bg_button" class="color-input" />
                <button class="btn small" @click="pickColor('button')">选择</button>
              </div>
              <div class="color-row">
                <span>按钮文字色</span>
                <input type="text" v-model="solidConfig.fg_button" class="color-input" />
                <button class="btn small" @click="pickColor('fg')">选择</button>
              </div>
            </div>
            <div class="preset-buttons">
              <span>预设方案：</span>
              <button class="btn small" @click="applyPreset('default')">默认</button>
              <button class="btn small" @click="applyPreset('dark')">深色</button>
              <button class="btn small" @click="applyPreset('light')">浅色</button>
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

.theme-card:hover:not(:disabled) {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-hover);
}

.theme-card.active {
  border-color: var(--color-primary);
  background: var(--color-bg-tertiary);
}

.theme-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.coming-soon {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg);
  border-radius: var(--radius-sm);
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
