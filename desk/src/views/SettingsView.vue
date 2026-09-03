<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { ArrowLeft, ChevronRight } from 'lucide-vue-next'
import type { Config } from '@/types'

const router = useRouter()
const appStore = useAppStore()

const config = computed(() => appStore.config)

// 当前视图
type ViewType = 'main' | 'custom' | 'appearance' | 'help' | 'archive' | 'reset'
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

// ============ 外观设置 ============
const whitenK = ref(config.value.whiten_k)
const themeBgWindow = ref(config.value.theme.bg_window)
const themeBgButton = ref(config.value.theme.bg_button)
const themeFgButton = ref(config.value.theme.fg_button)

async function saveAppearance() {
  const newConfig: Config = {
    ...config.value,
    whiten_k: whitenK.value,
    theme: {
      bg_window: themeBgWindow.value,
      bg_button: themeBgButton.value,
      fg_button: themeFgButton.value,
      bg_frame: '#d9d9d9'
    }
  }
  await appStore.saveConfig(newConfig)
  alert('外观已保存')
}

function applyPreset(preset: 'default' | 'dark' | 'light') {
  if (preset === 'default') {
    themeBgWindow.value = '#f0f0f0'
    themeBgButton.value = '#e0e0e0'
    themeFgButton.value = '#000000'
  } else if (preset === 'dark') {
    themeBgWindow.value = '#2d2d2d'
    themeBgButton.value = '#3c3c3c'
    themeFgButton.value = '#ffffff'
  } else {
    themeBgWindow.value = '#ffffff'
    themeBgButton.value = '#f0f0f0'
    themeFgButton.value = '#000000'
  }
}

function pickColor(target: 'bg' | 'button' | 'fg') {
  const input = document.createElement('input')
  input.type = 'color'
  input.onchange = () => {
    const color = input.value
    if (target === 'bg') themeBgWindow.value = color
    else if (target === 'button') themeBgButton.value = color
    else themeFgButton.value = color
  }
  input.click()
}

// ============ 恢复设置 ============
async function resetPlanData() {
  if (!confirm('确定重置所有日计划为默认？此操作不可恢复！')) return
  // 重置逻辑
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
      bg_window: '#f0f0f0',
      bg_button: '#e0e0e0',
      fg_button: '#000000',
      bg_frame: '#d9d9d9'
    }
  }
  await appStore.saveConfig(defaultConfig)
  overtimeThreshold.value = 105
  whitenK.value = 0.6
  showSeconds.value = true
  use24h.value = true
  showAmPm.value = false
  themeBgWindow.value = '#f0f0f0'
  themeBgButton.value = '#e0e0e0'
  themeFgButton.value = '#000000'
  alert('设置已重置')
}

function contactDeveloper() {
  alert('QQ号：3442386217\n抖音：@浪兮有点浪')
}
</script>

<template>
  <div class="settings-view">
    <header class="header">
      <button class="back-btn" @click="router.push('/')">
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
          <button class="settings-item" @click="currentView = 'appearance'">
            <span>外观</span>
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

      <!-- 外观设置 -->
      <template v-else-if="currentView === 'appearance'">
        <h2>外观设置</h2>

        <div class="form-section">
          <label>日历背景色白化系数</label>
          <div class="slider-control">
            <input type="range" v-model="whitenK" min="0" max="1" step="0.01" class="slider" />
            <span class="slider-value">{{ whitenK.toFixed(2) }}</span>
          </div>
        </div>

        <div class="form-section">
          <label>界面样式</label>
          <div class="color-settings">
            <div class="color-row">
              <span>窗口背景色</span>
              <input type="text" v-model="themeBgWindow" class="color-input" />
              <button class="btn small" @click="pickColor('bg')">选择</button>
            </div>
            <div class="color-row">
              <span>按钮背景色</span>
              <input type="text" v-model="themeBgButton" class="color-input" />
              <button class="btn small" @click="pickColor('button')">选择</button>
            </div>
            <div class="color-row">
              <span>按钮文字色</span>
              <input type="text" v-model="themeFgButton" class="color-input" />
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

        <div class="form-actions">
          <button class="btn secondary" @click="currentView = 'main'">返回</button>
          <button class="btn primary" @click="saveAppearance">保存</button>
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
          <button class="btn primary full" @click="alert('导出功能待实现')">导出存档</button>
          <button class="btn primary full" @click="alert('导入功能待实现')">导入存档</button>
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

.slider-control {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
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
}

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
