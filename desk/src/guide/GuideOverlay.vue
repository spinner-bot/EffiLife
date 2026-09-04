<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { GuideManager, guideState } from './GuideManager'
import type { GuideStep } from './GuideManager'
import { X, MousePointer, Sparkles } from 'lucide-vue-next'

// 当前步骤
const currentStep = computed(() => GuideManager.getCurrentStep())
const progress = computed(() => GuideManager.getProgress())
const isActive = computed(() => guideState.isActive)
const canProceed = computed(() => guideState.canProceed)

// 目标元素位置
const targetRect = ref<DOMRect | null>(null)
let resizeObserver: ResizeObserver | null = null
let targetElement: Element | null = null
let mutationObserver: MutationObserver | null = null

// 监听步骤变化，更新目标元素位置
watch(() => guideState.version, () => {
  nextTick(() => updateTargetElement())
}, { immediate: true })

function updateTargetElement() {
  // 清理之前的观察器
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (mutationObserver) {
    mutationObserver.disconnect()
    mutationObserver = null
  }

  const step = currentStep.value
  if (!step?.target) {
    targetRect.value = null
    targetElement = null
    return
  }

  // 查找目标元素
  const findTarget = () => {
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
      return true
    }
    return false
  }

  // 尝试查找，如果找不到则监听 DOM 变化
  if (!findTarget()) {
    mutationObserver = new MutationObserver(() => {
      if (findTarget()) {
        mutationObserver?.disconnect()
        mutationObserver = null
      }
    })
    mutationObserver.observe(document.body, { childList: true, subtree: true })
  }
}

// 点击目标元素
function onTargetClick(e: MouseEvent) {
  const step = currentStep.value
  if (!step || !step.actionRequired) return

  // 检查是否点击了目标区域
  if (targetElement && targetElement.contains(e.target as Node)) {
    GuideManager.markActionComplete()

    // 如果有导航目标，延迟导航
    if (step.navigateTo) {
      setTimeout(() => {
        window.location.hash = '#' + step.navigateTo
      }, 300)
    }
  }
}

// 点击屏幕任意位置继续（仅用于介绍类步骤）
function onBackdropClick() {
  const step = currentStep.value
  if (!step) return

  // 只有不需要操作的步骤才能点击继续
  if (!step.actionRequired) {
    GuideManager.nextStep()
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

// 获取操作提示文字
function getActionHint(): string {
  const step = currentStep.value
  if (!step) return ''

  if (!step.actionRequired) {
    return '点击屏幕任意位置继续'
  }

  // 根据操作类型返回提示
  switch (step.actionType) {
    case 'click':
      return '点击上方高亮区域继续'
    case 'input':
      return '完成操作后自动继续'
    case 'navigate':
      return '点击导航继续'
    default:
      return '完成操作后继续'
  }
}

// 键盘快捷键
function handleKeydown(e: KeyboardEvent) {
  if (!isActive.value) return

  // 只有不需要操作的步骤才能用键盘
  if (!currentStep.value?.actionRequired) {
    if (e.key === 'Enter' || e.key === ' ') {
      GuideManager.nextStep()
    }
  }

  if (e.key === 'Escape') {
    skipGuide()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('click', onTargetClick, true)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('click', onTargetClick, true)
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  if (mutationObserver) {
    mutationObserver.disconnect()
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
  const offset = 24

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

// 点击指引位置
const pointerStyle = computed(() => {
  if (!targetRect.value || !currentStep.value?.actionRequired) {
    return null
  }

  const rect = targetRect.value
  return {
    top: `${rect.top + rect.height / 2}px`,
    left: `${rect.left + rect.width / 2}px`
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="guide-fade">
      <div v-if="isActive && currentStep" class="guide-overlay" @click="onBackdropClick">
        <!-- 背景遮罩 - 半透明，不模糊 -->
        <div class="guide-backdrop"></div>

        <!-- 高亮区域 - 只有目标区域清晰 -->
        <div
          v-if="highlightStyle"
          class="guide-highlight"
          :style="highlightStyle"
        ></div>

        <!-- 点击指引鼠标图标 -->
        <div
          v-if="pointerStyle && currentStep.actionRequired"
          class="guide-pointer"
          :style="pointerStyle"
        >
          <MousePointer :size="32" />
        </div>

        <!-- 提示框 -->
        <div class="guide-tooltip" :style="tooltipStyle" @click.stop>
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
            <Sparkles v-if="!currentStep.actionRequired" :size="18" class="title-icon" />
            {{ currentStep.title }}
          </h3>

          <!-- 描述 -->
          <p class="guide-description">{{ currentStep.description }}</p>

          <!-- 操作提示 -->
          <div class="guide-hint" :class="{ waiting: currentStep.actionRequired && !canProceed }">
            <span class="hint-icon">{{ currentStep.actionRequired ? '👆' : '👉' }}</span>
            <span>{{ getActionHint() }}</span>
          </div>

          <!-- 介绍类步骤：点击继续按钮 -->
          <div v-if="!currentStep.actionRequired" class="guide-actions">
            <button
              v-if="progress.current < progress.total"
              class="guide-btn primary"
              @click="GuideManager.nextStep()"
            >
              下一步
            </button>
            <button
              v-else
              class="guide-btn finish"
              @click="finishGuide"
            >
              <Sparkles :size="16" />
              开始使用
            </button>
          </div>

          <!-- 操作类步骤：等待用户操作 -->
          <div v-else class="guide-actions">
            <div class="waiting-indicator">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
              <span>等待操作...</span>
            </div>
          </div>
        </div>

        <!-- 关闭按钮 -->
        <button class="guide-close" @click.stop="skipGuide" title="跳过引导">
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
  pointer-events: auto;
}

.guide-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  pointer-events: auto;
}

.guide-highlight {
  position: absolute;
  border-radius: 12px;
  background: transparent;
  box-shadow:
    0 0 0 9999px rgba(0, 0, 0, 0.5),
    0 0 0 4px rgba(99, 102, 241, 0.8);
  pointer-events: none;
  z-index: 1;
  animation: pulse-highlight 2s ease-in-out infinite;
}

@keyframes pulse-highlight {
  0%, 100% {
    box-shadow:
      0 0 0 9999px rgba(0, 0, 0, 0.5),
      0 0 0 4px rgba(99, 102, 241, 0.8);
  }
  50% {
    box-shadow:
      0 0 0 9999px rgba(0, 0, 0, 0.5),
      0 0 0 6px rgba(99, 102, 241, 1),
      0 0 20px rgba(99, 102, 241, 0.5);
  }
}

.guide-pointer {
  position: absolute;
  transform: translate(-50%, -50%);
  color: white;
  pointer-events: none;
  z-index: 2;
  animation: pointer-bounce 1s ease-in-out infinite;
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.5));
}

@keyframes pointer-bounce {
  0%, 100% {
    transform: translate(-50%, -50%) scale(1);
  }
  50% {
    transform: translate(-50%, -60%) scale(1.1);
  }
}

.guide-tooltip {
  position: absolute;
  width: 360px;
  max-width: calc(100vw - 40px);
  background: rgba(30, 30, 50, 0.95);
  border: 1px solid rgba(99, 102, 241, 0.5);
  border-radius: 16px;
  padding: 20px;
  pointer-events: auto;
  z-index: 3;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.5),
    0 0 40px rgba(99, 102, 241, 0.3);
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
  margin: 0 0 16px 0;
  font-size: 14px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.9);
}

.guide-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(99, 102, 241, 0.2);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}

.guide-hint.waiting {
  background: rgba(251, 191, 36, 0.2);
  border-color: rgba(251, 191, 36, 0.3);
}

.hint-icon {
  font-size: 18px;
}

.guide-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.waiting-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
}

.waiting-indicator .dot {
  width: 6px;
  height: 6px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 50%;
  animation: dot-pulse 1.4s ease-in-out infinite;
}

.waiting-indicator .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.waiting-indicator .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dot-pulse {
  0%, 100% {
    opacity: 0.4;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

.guide-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
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
  color: #1a1a2e;
}

.guide-btn.finish:hover {
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4);
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
  z-index: 4;
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
