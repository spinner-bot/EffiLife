<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { GuideManager, guideState } from './GuideManager'
import type { GuideStep } from './GuideManager'
import { ChevronLeft, ChevronRight, X, Sparkles } from 'lucide-vue-next'

// 当前步骤
const currentStep = computed(() => GuideManager.getCurrentStep())
const progress = computed(() => GuideManager.getProgress())
const isActive = computed(() => guideState.isActive)

// 目标元素位置
const targetRect = ref<DOMRect | null>(null)
let resizeObserver: ResizeObserver | null = null
let targetElement: Element | null = null

// 监听步骤变化，更新目标元素位置
watch(() => guideState.version, () => {
  updateTargetElement()
}, { immediate: true })

function updateTargetElement() {
  // 清理之前的观察器
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }

  const step = currentStep.value
  if (!step?.target) {
    targetRect.value = null
    targetElement = null
    return
  }

  // 延迟查找元素，确保 DOM 已更新
  setTimeout(() => {
    targetElement = document.querySelector(step.target!)
    if (targetElement) {
      targetRect.value = targetElement.getBoundingClientRect()

      // 观察元素大小变化
      resizeObserver = new ResizeObserver(() => {
        if (targetElement) {
          targetRect.value = targetElement.getBoundingClientRect()
        }
      })
      resizeObserver.observe(targetElement)

      // 滚动到目标元素
      targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, 100)
}

// 下一步
function nextStep() {
  const step = currentStep.value

  // 如果步骤有导航目标，先导航
  if (step?.navigateTo) {
    window.location.hash = '#' + step.navigateTo
  }

  GuideManager.nextStep()
}

// 上一步
function prevStep() {
  if (progress.value.current > 1) {
    guideState.currentStepIndex--
    guideState.version++
  }
}

// 跳过引导
function skipGuide() {
  if (confirm('确定跳过引导？你可以稍后在设置中重新体验。')) {
    GuideManager.skipGuide()
  }
}

// 完成引导
function finishGuide() {
  GuideManager.endGuide()
}

// 键盘快捷键
function handleKeydown(e: KeyboardEvent) {
  if (!isActive.value) return

  if (e.key === 'ArrowRight' || e.key === 'Enter') {
    nextStep()
  } else if (e.key === 'ArrowLeft') {
    prevStep()
  } else if (e.key === 'Escape') {
    skipGuide()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})

// 计算提示框位置
const tooltipStyle = computed(() => {
  if (!targetRect.value || !currentStep.value) {
    return {
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)'
    }
  }

  const rect = targetRect.value
  const position = currentStep.value.position || 'bottom'
  const offset = 20

  switch (position) {
    case 'top':
      return {
        bottom: `${window.innerHeight - rect.top + offset}px`,
        left: `${rect.left + rect.width / 2}px`,
        transform: 'translateX(-50%)'
      }
    case 'bottom':
      return {
        top: `${rect.bottom + offset}px`,
        left: `${rect.left + rect.width / 2}px`,
        transform: 'translateX(-50%)'
      }
    case 'left':
      return {
        top: `${rect.top + rect.height / 2}px`,
        right: `${window.innerWidth - rect.left + offset}px`,
        transform: 'translateY(-50%)'
      }
    case 'right':
      return {
        top: `${rect.top + rect.height / 2}px`,
        left: `${rect.right + offset}px`,
        transform: 'translateY(-50%)'
      }
    default:
      return {
        top: `${rect.bottom + offset}px`,
        left: `${rect.left + rect.width / 2}px`,
        transform: 'translateX(-50%)'
      }
  }
})

// 高亮区域样式
const highlightStyle = computed(() => {
  if (!targetRect.value || !currentStep.value?.highlight) {
    return null
  }

  const rect = targetRect.value
  const padding = 8

  return {
    top: `${rect.top - padding}px`,
    left: `${rect.left - padding}px`,
    width: `${rect.width + padding * 2}px`,
    height: `${rect.height + padding * 2}px`
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="guide-fade">
      <div v-if="isActive && currentStep" class="guide-overlay">
        <!-- 背景遮罩 -->
        <div class="guide-backdrop" @click="skipGuide"></div>

        <!-- 高亮区域 -->
        <div
          v-if="highlightStyle"
          class="guide-highlight"
          :style="highlightStyle"
        ></div>

        <!-- 提示框 -->
        <div class="guide-tooltip" :style="tooltipStyle">
          <!-- 进度指示 -->
          <div class="guide-progress">
            <span class="progress-text">{{ progress.current }} / {{ progress.total }}</span>
            <div class="progress-bar">
              <div
                class="progress-fill"
                :style="{ width: `${(progress.current / progress.total) * 100}%` }"
              ></div>
            </div>
          </div>

          <!-- 标题 -->
          <h3 class="guide-title">
            <Sparkles v-if="progress.current === 1 || progress.current === progress.total" :size="18" class="title-icon" />
            {{ currentStep.title }}
          </h3>

          <!-- 描述 -->
          <p class="guide-description">{{ currentStep.description }}</p>

          <!-- 操作按钮 -->
          <div class="guide-actions">
            <button
              v-if="progress.current > 1"
              class="guide-btn secondary"
              @click="prevStep"
            >
              <ChevronLeft :size="16" />
              上一步
            </button>

            <button
              class="guide-btn skip"
              @click="skipGuide"
            >
              跳过
            </button>

            <div class="spacer"></div>

            <button
              v-if="progress.current < progress.total"
              class="guide-btn primary"
              @click="nextStep"
            >
              下一步
              <ChevronRight :size="16" />
            </button>
            <button
              v-else
              class="guide-btn primary finish"
              @click="finishGuide"
            >
              <Sparkles :size="16" />
              开始使用
            </button>
          </div>

          <!-- 快捷键提示 -->
          <div class="guide-shortcuts">
            <span>← → 切换步骤</span>
            <span>Esc 跳过</span>
          </div>
        </div>

        <!-- 关闭按钮 -->
        <button class="guide-close" @click="skipGuide" title="跳过引导">
          <X :size="20" />
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.guide-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  pointer-events: none;
}

.guide-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  pointer-events: auto;
}

.guide-highlight {
  position: absolute;
  border-radius: 12px;
  box-shadow:
    0 0 0 9999px rgba(0, 0, 0, 0.6),
    0 0 20px rgba(99, 102, 241, 0.5);
  border: 2px solid rgba(99, 102, 241, 0.8);
  pointer-events: none;
  z-index: 1;
  animation: pulse-border 2s ease-in-out infinite;
}

@keyframes pulse-border {
  0%, 100% {
    box-shadow:
      0 0 0 9999px rgba(0, 0, 0, 0.6),
      0 0 20px rgba(99, 102, 241, 0.5);
  }
  50% {
    box-shadow:
      0 0 0 9999px rgba(0, 0, 0, 0.6),
      0 0 30px rgba(99, 102, 241, 0.8);
  }
}

.guide-tooltip {
  position: absolute;
  width: 360px;
  max-width: calc(100vw - 40px);
  background: linear-gradient(135deg, rgba(30, 30, 50, 0.95) 0%, rgba(40, 40, 60, 0.95) 100%);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 16px;
  padding: 20px;
  pointer-events: auto;
  z-index: 2;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.5),
    0 0 40px rgba(99, 102, 241, 0.2);
  animation: tooltip-appear 0.3s ease-out;
}

@keyframes tooltip-appear {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.guide-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.progress-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  font-family: var(--font-mono);
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.guide-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.title-icon {
  color: #fbbf24;
}

.guide-description {
  margin: 0 0 20px 0;
  font-size: 14px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.8);
}

.guide-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spacer {
  flex: 1;
}

.guide-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.guide-btn.secondary {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
}

.guide-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.guide-btn.skip {
  background: transparent;
  color: rgba(255, 255, 255, 0.5);
  padding: 8px 12px;
}

.guide-btn.skip:hover {
  color: rgba(255, 255, 255, 0.8);
}

.guide-btn.primary {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
}

.guide-btn.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.guide-btn.finish {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
}

.guide-btn.finish:hover {
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4);
}

.guide-shortcuts {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.guide-shortcuts span {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.guide-close {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  pointer-events: auto;
  z-index: 3;
  transition: all 0.2s ease;
}

.guide-close:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  transform: scale(1.1);
}

/* 过渡动画 */
.guide-fade-enter-active,
.guide-fade-leave-active {
  transition: opacity 0.3s ease;
}

.guide-fade-enter-from,
.guide-fade-leave-to {
  opacity: 0;
}
</style>
