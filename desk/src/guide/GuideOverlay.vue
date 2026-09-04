<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { GuideManager, guideState } from './GuideManager'
import { X, MousePointer, Sparkles } from 'lucide-vue-next'

const currentStep = computed(() => GuideManager.getCurrentStep())
const progress = computed(() => GuideManager.getProgress())
const isActive = computed(() => guideState.isActive)

const targetRect = ref<DOMRect | null>(null)
let targetElement: Element | null = null
let mutationObserver: MutationObserver | null = null

watch(() => guideState.version, () => {
  nextTick(() => updateTargetElement())
}, { immediate: true })

function updateTargetElement() {
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

  const findTarget = () => {
    targetElement = document.querySelector(step.target!)
    if (targetElement) {
      targetRect.value = targetElement.getBoundingClientRect()
      targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
      return true
    }
    return false
  }

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

// 点击事件处理 - 拦截高亮区域外的点击
function onClickCapture(e: MouseEvent) {
  const step = currentStep.value
  if (!step || !isActive.value) return

  const clickedTarget = e.target as Node

  // 检查是否点击了提示框内部（允许）
  const tooltip = document.querySelector('.guide-tooltip')
  if (tooltip && tooltip.contains(clickedTarget)) {
    return
  }

  // 检查是否点击了关闭按钮（允许）
  const closeBtn = document.querySelector('.guide-close')
  if (closeBtn && closeBtn.contains(clickedTarget)) {
    return
  }

  // 对于操作类步骤，检查是否点击了高亮区域内
  if (step.actionRequired && targetRect.value) {
    const rect = targetRect.value
    const x = e.clientX
    const y = e.clientY
    const isInHighlight = x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom

    if (!isInHighlight) {
      // 点击在高亮区域外，阻止事件
      e.stopPropagation()
      e.preventDefault()
      return
    }

    // 点击在高亮区域内，检查是否是目标元素
    const isTargetClick = targetElement && (
      targetElement === clickedTarget ||
      targetElement.contains(clickedTarget)
    )

    let isActionTargetClick = false
    if (step.actionTarget) {
      const actionEl = document.querySelector(step.actionTarget)
      if (actionEl && (actionEl === clickedTarget || actionEl.contains(clickedTarget))) {
        isActionTargetClick = true
      }
    }

    if (isTargetClick || isActionTargetClick) {
      // 导航到目标页面（如果需要）
      if (step.navigateTo && !window.location.hash.includes(step.navigateTo)) {
        window.location.hash = '#' + step.navigateTo
      }

      // 开始验证操作
      startActionValidation()

      // 对于简单点击任务且有 autoAdvance，延迟后自动进入下一步
      if (step.autoAdvance && !step.validateAction) {
        setTimeout(() => {
          GuideManager.nextStep()
        }, 800)
      }
    }
  } else {
    // 介绍类步骤，点击任意位置继续
    GuideManager.nextStep()
  }
}

// 开始验证操作是否完成
let validationInterval: number | null = null

function startActionValidation() {
  const step = currentStep.value
  if (!step) return

  // 如果有验证函数，定期检查
  if (step.validateAction) {
    if (validationInterval) clearInterval(validationInterval)
    validationInterval = window.setInterval(() => {
      if (step.validateAction && step.validateAction()) {
        // 操作已验证完成
        if (validationInterval) clearInterval(validationInterval)
        GuideManager.markActionComplete()
      }
    }, 500)
  } else {
    // 没有验证函数，点击后标记为可继续状态，但需要用户确认
    GuideManager.markActionComplete()
  }
}

function skipGuide() {
  if (confirm('确定跳过引导？')) {
    GuideManager.skipGuide()
  }
}

function finishGuide() {
  GuideManager.endGuide()
}

function getActionHint(): string {
  const step = currentStep.value
  if (!step) return ''
  if (!step.actionRequired) {
    return '点击空白处继续'
  }
  // 操作已完成，显示继续按钮
  if (guideState.canProceed) {
    return '✓ 已完成'
  }
  return '点击高亮区域'
}

function handleKeydown(e: KeyboardEvent) {
  if (!isActive.value) return
  if (!currentStep.value?.actionRequired && e.key === 'Enter') {
    GuideManager.nextStep()
  }
  if (e.key === 'Escape') skipGuide()
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('click', onClickCapture, true)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('click', onClickCapture, true)
  if (mutationObserver) mutationObserver.disconnect()
  if (validationInterval) clearInterval(validationInterval)
})

// 高亮区域样式
const highlightStyle = computed(() => {
  if (!targetRect.value || !currentStep.value?.highlight) return null
  const rect = targetRect.value
  const padding = 6
  return {
    top: `${rect.top - padding}px`,
    left: `${rect.left - padding}px`,
    width: `${rect.width + padding * 2}px`,
    height: `${rect.height + padding * 2}px`
  }
})

// 提示框位置 - 固定在底部
const tooltipStyle = computed(() => ({
  bottom: '24px',
  left: '50%',
  transform: 'translateX(-50%)'
}))
</script>

<template>
  <Teleport to="body">
    <Transition name="guide-fade">
      <div v-if="isActive && currentStep" class="guide-overlay">
        <!-- 高亮区域 + 遮罩（使用 box-shadow 创建遮罩，高亮区域可点击） -->
        <div
          v-if="highlightStyle"
          class="guide-highlight"
          :style="highlightStyle"
        ></div>
        <!-- 没有目标时显示全屏遮罩 -->
        <div v-else class="guide-backdrop"></div>

        <!-- 鼠标指引 -->
        <div
          v-if="targetRect && currentStep.actionRequired"
          class="guide-pointer"
          :style="{
            top: `${targetRect.top + targetRect.height / 2}px`,
            left: `${targetRect.left + targetRect.width / 2}px`
          }"
        >
          <MousePointer :size="24" />
        </div>

        <!-- 提示框 - 固定在底部，小巧不遮挡 -->
        <div class="guide-tooltip" :style="tooltipStyle">
          <div class="tooltip-header">
            <span class="progress-badge">{{ progress.current }}/{{ progress.total }}</span>
            <h3 class="tooltip-title">{{ currentStep.title }}</h3>
            <button class="close-btn" @click="skipGuide">
              <X :size="14" />
            </button>
          </div>
          <p class="tooltip-desc">{{ currentStep.description }}</p>
          <div class="tooltip-hint" :class="{ action: currentStep.actionRequired, done: guideState.canProceed }">
            <span>{{ getActionHint() }}</span>
            <span v-if="currentStep.actionRequired && !guideState.canProceed && !currentStep.skippable" class="waiting-dots">
              <span></span><span></span><span></span>
            </span>
            <button v-if="currentStep.skippable && currentStep.actionRequired && !guideState.canProceed" class="skip-step-btn" @click="GuideManager.skipStep()">
              跳过此步 →
            </button>
            <button v-else-if="guideState.canProceed && !currentStep.autoAdvance && progress.current < progress.total" class="next-btn" @click="GuideManager.nextStep()">
              继续 →
            </button>
            <button v-else-if="guideState.canProceed && !currentStep.autoAdvance" class="next-btn finish" @click="finishGuide">
              开始使用 ✨
            </button>
          </div>
        </div>
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
  background: rgba(0, 0, 0, 0.5);
  pointer-events: auto;
}

.guide-highlight {
  position: absolute;
  border-radius: 8px;
  background: transparent;
  /* 使用 box-shadow 创建遮罩，高亮区域可点击 */
  box-shadow:
    0 0 0 9999px rgba(0, 0, 0, 0.5),
    0 0 0 3px rgba(99, 102, 241, 0.9);
  pointer-events: none;
  z-index: 1;
  animation: pulse-box 1.5s ease-in-out infinite;
}

@keyframes pulse-box {
  0%, 100% { box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5), 0 0 0 3px rgba(99, 102, 241, 0.9); }
  50% { box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5), 0 0 0 5px rgba(99, 102, 241, 1), 0 0 15px rgba(99, 102, 241, 0.4); }
}

.guide-pointer {
  position: absolute;
  transform: translate(-50%, -50%);
  color: white;
  pointer-events: none;
  z-index: 2;
  animation: bounce 1s ease-in-out infinite;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
}

@keyframes bounce {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -60%) scale(1.15); }
}

.guide-tooltip {
  position: absolute;
  width: 320px;
  background: rgba(25, 25, 40, 0.92);
  border: 1px solid rgba(99, 102, 241, 0.4);
  border-radius: 12px;
  padding: 14px 16px;
  pointer-events: auto;
  z-index: 3;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
}

.tooltip-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.progress-badge {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
}

.tooltip-title {
  flex: 1;
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.tooltip-desc {
  margin: 0 0 10px 0;
  font-size: 13px;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.8);
}

.tooltip-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(99, 102, 241, 0.15);
  border-radius: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.tooltip-hint.action {
  background: rgba(251, 191, 36, 0.15);
}

.tooltip-hint.done {
  background: rgba(34, 197, 94, 0.2);
  border-color: rgba(34, 197, 94, 0.3);
}

.waiting-dots {
  display: inline-flex;
  gap: 3px;
  margin-left: auto;
}

.waiting-dots span {
  width: 4px;
  height: 4px;
  background: rgba(251, 191, 36, 0.6);
  border-radius: 50%;
  animation: dots 1.4s ease-in-out infinite;
}

.waiting-dots span:nth-child(2) { animation-delay: 0.2s; }
.waiting-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dots {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.next-btn {
  margin-left: auto;
  padding: 4px 12px;
  background: rgba(99, 102, 241, 0.8);
  border: none;
  border-radius: 4px;
  color: white;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.next-btn:hover {
  background: rgba(99, 102, 241, 1);
}

.next-btn.finish {
  background: rgba(251, 191, 36, 0.8);
}

.next-btn.finish:hover {
  background: rgba(251, 191, 36, 1);
}

.skip-step-btn {
  margin-left: auto;
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.skip-step-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.guide-fade-enter-active,
.guide-fade-leave-active {
  transition: opacity 0.3s ease;
}

.guide-fade-enter-from,
.guide-fade-leave-to {
  opacity: 0;
}
</style>
