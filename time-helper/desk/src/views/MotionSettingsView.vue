<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Gauge, Sparkles, Zap, RotateCcw, Check } from 'lucide-vue-next'
import { MotionManager } from '@/motion'
import type { MotionSettings } from '@/motion'
import { useI18n } from '@/i18n'
import { notifyToast } from '@/services/toastService'
import { requestConfirm } from '@/services/confirmService'

const router = useRouter()
const { t } = useI18n()

const settings = ref<MotionSettings>(MotionManager.getSettings())
const isOptimizing = ref(false)
const benchmarkResult = ref<{ fps: number; score: number } | null>(null)
const showRecommendation = ref(false)
const recommendation = ref<MotionSettings | null>(null)

// 帧率选项
const fpsOptions = [
  { value: 5, label: '5 FPS', descriptionKey: 'settings.motion.fps.lowest' },
  { value: 10, label: '10 FPS', descriptionKey: 'settings.motion.fps.powerSave' },
  { value: 15, label: '15 FPS', descriptionKey: 'settings.motion.fps.balanced' },
  { value: 30, label: '30 FPS', descriptionKey: 'settings.motion.fps.smooth' }
]

// 粒子数量倍率选项
const particleMultiplierOptions = [
  { value: 0.5, label: '50%', descriptionKey: 'settings.motion.density.sparse' },
  { value: 1.0, label: '100%', descriptionKey: 'settings.motion.density.standard' },
  { value: 1.5, label: '150%', descriptionKey: 'settings.motion.density.dense' },
  { value: 2.0, label: '200%', descriptionKey: 'settings.motion.density.veryDense' }
]

// 动效速度选项
const animationSpeedOptions = [
  { value: 0.5, label: '0.5x', descriptionKey: 'settings.motion.speed.slow' },
  { value: 0.75, label: '0.75x', descriptionKey: 'settings.motion.speed.ratherSlow' },
  { value: 1.0, label: '1.0x', descriptionKey: 'settings.motion.speed.standard' },
  { value: 1.25, label: '1.25x', descriptionKey: 'settings.motion.speed.ratherFast' },
  { value: 1.5, label: '1.5x', descriptionKey: 'settings.motion.speed.fast' },
  { value: 2.0, label: '2.0x', descriptionKey: 'settings.motion.speed.veryFast' }
]

// 更新设置
function updateSetting<K extends keyof MotionSettings>(key: K, value: MotionSettings[K]) {
  settings.value[key] = value
  MotionManager.updateSettings({ [key]: value })
}

// 运行自动优化
async function runAutoOptimize() {
  isOptimizing.value = true
  benchmarkResult.value = null
  showRecommendation.value = false
  recommendation.value = null

  try {
    const result = await MotionManager.runAutoOptimize()
    benchmarkResult.value = { fps: result.fps, score: result.score }
    recommendation.value = result.recommendation
    showRecommendation.value = true
  } catch (e) {
    console.error('Auto optimize failed:', e)
    notifyToast(t('settings.motion.testFailed'), 'error')
  } finally {
    isOptimizing.value = false
  }
}

// 应用推荐设置
function applyRecommendation() {
  if (recommendation.value) {
    MotionManager.applyRecommendation(recommendation.value)
    settings.value = MotionManager.getSettings()
    showRecommendation.value = false
    notifyToast(t('settings.motion.applied'), 'success')
  }
}

// 重置为默认
async function resetToDefault() {
  if (!await requestConfirm(t('settings.motion.resetConfirm'), { tone: 'danger' })) return
  MotionManager.updateSettings({
    enabled: true,
    targetFps: 15,
    themeCanvasEnabled: true,
    particleEnabled: true,
    transitionEnabled: true,
    particleCountMultiplier: 1.0,
    animationSpeed: 1.0,
    autoOptimize: false
  })
  settings.value = MotionManager.getSettings()
}

// 获取性能评级
function getPerformanceRating(): { label: string; color: string } {
  const results = MotionManager.getBenchmarkResults()
  if (!results) return { label: t('settings.motion.rating.untested'), color: 'var(--color-text-tertiary)' }

  if (results.score >= 80) return { label: t('settings.motion.rating.excellent'), color: 'var(--color-progress-high)' }
  if (results.score >= 50) return { label: t('settings.motion.rating.good'), color: 'var(--color-progress-good)' }
  if (results.score >= 25) return { label: t('settings.motion.rating.fair'), color: 'var(--color-progress-medium)' }
  return { label: t('settings.motion.rating.poor'), color: 'var(--color-progress-low)' }
}

const performanceRating = computed(() => getPerformanceRating())
</script>

<template>
  <div class="motion-settings-view">
    <header class="header">
      <button type="button" class="back-btn" @click="router.push('/settings')">
        <ArrowLeft :size="16" />
        <span>{{ t('settings.motion.back') }}</span>
      </button>
      <h1>{{ t('settings.motion.title') }}</h1>
    </header>

    <div class="main-content">
      <!-- 主开关 -->
      <section class="settings-section">
        <div class="section-header">
          <h2>{{ t('settings.motion.switches') }}</h2>
        </div>
        <label class="toggle-row">
          <div class="toggle-info">
            <span class="toggle-label">{{ t('settings.motion.enabled') }}</span>
            <span class="toggle-desc">{{ t('settings.motion.enabledDesc') }}</span>
          </div>
          <input
            type="checkbox"
            :checked="settings.enabled"
            @change="updateSetting('enabled', ($event.target as HTMLInputElement).checked)"
          />
        </label>
      </section>

      <!-- 帧率设置 -->
      <section class="settings-section">
        <div class="section-header">
          <h2>{{ t('settings.motion.fps.title') }}</h2>
          <Gauge :size="20" class="section-icon" />
        </div>
        <div class="option-grid">
          <button
            type="button"
            v-for="opt in fpsOptions"
            :key="opt.value"
            class="option-card"
            :class="{ active: settings.targetFps === opt.value }"
            @click="updateSetting('targetFps', opt.value)"
          >
            <span class="option-label">{{ opt.label }}</span>
            <span class="option-desc">{{ t(opt.descriptionKey) }}</span>
          </button>
        </div>
      </section>

      <!-- 动画效果开关 -->
      <section class="settings-section">
        <div class="section-header">
          <h2>{{ t('settings.motion.effects') }}</h2>
          <Sparkles :size="20" class="section-icon" />
        </div>

        <label class="toggle-row">
          <div class="toggle-info">
            <span class="toggle-label">{{ t('settings.motion.themeCanvas') }}</span>
            <span class="toggle-desc">{{ t('settings.motion.themeCanvasDesc') }}</span>
          </div>
          <input
            type="checkbox"
            :checked="settings.themeCanvasEnabled"
            @change="updateSetting('themeCanvasEnabled', ($event.target as HTMLInputElement).checked)"
          />
        </label>

        <label class="toggle-row">
          <div class="toggle-info">
            <span class="toggle-label">{{ t('settings.motion.particles') }}</span>
            <span class="toggle-desc">{{ t('settings.motion.particlesDesc') }}</span>
          </div>
          <input
            type="checkbox"
            :checked="settings.particleEnabled"
            @change="updateSetting('particleEnabled', ($event.target as HTMLInputElement).checked)"
          />
        </label>

        <label class="toggle-row">
          <div class="toggle-info">
            <span class="toggle-label">{{ t('settings.motion.transitions') }}</span>
            <span class="toggle-desc">{{ t('settings.motion.transitionsDesc') }}</span>
          </div>
          <input
            type="checkbox"
            :checked="settings.transitionEnabled"
            @change="updateSetting('transitionEnabled', ($event.target as HTMLInputElement).checked)"
          />
        </label>
      </section>

      <!-- 动效速度 -->
      <section class="settings-section">
        <div class="section-header">
          <h2>{{ t('settings.motion.speed.title') }}</h2>
        </div>
        <div class="option-grid speed-grid">
          <button
            type="button"
            v-for="opt in animationSpeedOptions"
            :key="opt.value"
            class="option-card"
            :class="{ active: settings.animationSpeed === opt.value }"
            @click="updateSetting('animationSpeed', opt.value)"
          >
            <span class="option-label">{{ opt.label }}</span>
            <span class="option-desc">{{ t(opt.descriptionKey) }}</span>
          </button>
        </div>
      </section>

      <!-- 粒子密度 -->
      <section class="settings-section" v-if="settings.particleEnabled">
        <div class="section-header">
          <h2>{{ t('settings.motion.density.title') }}</h2>
        </div>
        <div class="option-grid">
          <button
            type="button"
            v-for="opt in particleMultiplierOptions"
            :key="opt.value"
            class="option-card"
            :class="{ active: settings.particleCountMultiplier === opt.value }"
            @click="updateSetting('particleCountMultiplier', opt.value)"
          >
            <span class="option-label">{{ opt.label }}</span>
            <span class="option-desc">{{ t(opt.descriptionKey) }}</span>
          </button>
        </div>
      </section>

      <!-- 自动优化 -->
      <section class="settings-section">
        <div class="section-header">
          <h2>{{ t('settings.motion.autoOptimize') }}</h2>
          <Zap :size="20" class="section-icon" />
        </div>
        <p class="section-desc">
          {{ t('settings.motion.autoOptimizeDesc') }}
        </p>

        <div class="benchmark-area">
          <button
            type="button"
            class="btn primary full"
            :disabled="isOptimizing"
            @click="runAutoOptimize"
          >
            <RotateCcw :size="18" :class="{ spinning: isOptimizing }" />
            <span>{{ isOptimizing ? t('settings.motion.testing') : t('settings.motion.startTest') }}</span>
          </button>

          <!-- 测试结果 -->
          <div v-if="benchmarkResult" class="benchmark-result">
            <div class="result-row">
              <span class="result-label">{{ t('settings.motion.resultFps') }}</span>
              <span class="result-value">{{ benchmarkResult.fps }} FPS</span>
            </div>
            <div class="result-row">
              <span class="result-label">{{ t('settings.motion.resultRating') }}</span>
              <span class="result-value" :style="{ color: performanceRating.color }">
                {{ performanceRating.label }}
              </span>
            </div>
            <div class="result-bar">
              <div
                class="result-fill"
                :style="{
                  width: benchmarkResult.score + '%',
                  backgroundColor: performanceRating.color
                }"
              ></div>
            </div>
          </div>

          <!-- 推荐设置 -->
          <div v-if="showRecommendation && recommendation" class="recommendation">
            <h4>{{ t('settings.motion.recommendedFps') }}</h4>
            <div class="rec-details">
              <span>{{ t('settings.motion.recommendationPrefix') }}<strong>{{ recommendation.targetFps }} FPS</strong></span>
              <span>{{ t('settings.motion.recommendationNote') }}</span>
            </div>
            <button type="button" class="btn primary" @click="applyRecommendation">
              <Check :size="16" />
              <span>{{ t('settings.motion.apply') }}</span>
            </button>
          </div>
        </div>
      </section>

      <!-- 重置 -->
      <section class="settings-section">
        <button type="button" class="btn secondary full" @click="resetToDefault">
          {{ t('settings.motion.reset') }}
        </button>
      </section>
    </div>
  </div>
</template>

<style scoped>
.motion-settings-view {
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

.settings-section {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.section-header h2 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.section-icon {
  color: var(--color-text-tertiary);
}

.section-desc {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-md) 0;
  line-height: 1.5;
}

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) 0;
  cursor: pointer;
}

.toggle-row + .toggle-row {
  border-top: 1px solid var(--color-border);
}

.toggle-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.toggle-label {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

.toggle-desc {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.toggle-row input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.option-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: var(--spacing-sm);
}

.option-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: var(--spacing-md);
  background: var(--color-bg);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.option-card:hover {
  border-color: var(--color-border-hover);
}

.option-card.active {
  border-color: var(--color-primary);
  background: rgba(99, 102, 241, 0.1);
}

.option-label {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.option-desc {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.benchmark-area {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.benchmark-result {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-xs) 0;
}

.result-label {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.result-value {
  font-size: 0.9375rem;
  font-weight: 600;
  font-family: var(--font-mono);
}

.result-bar {
  height: 8px;
  background: var(--color-bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
  margin-top: var(--spacing-sm);
}

.result-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.recommendation {
  background: var(--color-bg);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.recommendation h4 {
  margin: 0 0 var(--spacing-sm) 0;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-primary);
}

.rec-details {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.rec-details span {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
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

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.secondary {
  background: var(--color-bg);
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

.btn.primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn.full {
  width: 100%;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
