<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import type { Theme } from '@/types'
import { getThemeStyle } from './ThemeEngine'
import { ParticleSystem } from './ParticleSystem'
import { MotionManager, motionState } from '@/motion'

const props = defineProps<{
  theme: Theme
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const particleCanvasRef = ref<HTMLCanvasElement | null>(null)
let particleSystem: ParticleSystem | null = null
let animationId: number | null = null
let startTime = Date.now()
let resizeHandler: (() => void) | null = null
let lastFrameTime = 0

function startCanvasAnimation() {
  if (!canvasRef.value) return

  // 检查是否启用主题画布
  if (!MotionManager.isThemeCanvasEnabled()) {
    // 清空画布并返回
    const ctx = canvasRef.value.getContext('2d')
    if (ctx) {
      ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
    }
    return
  }

  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const resize = () => {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
  }
  resize()
  resizeHandler = resize
  window.addEventListener('resize', resize)

  const style = getThemeStyle(props.theme)

  // 如果主题没有动画效果，只渲染一次
  if (!style.renderCanvas) {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    return
  }

  const animate = (currentTime: number) => {
    // 使用 MotionManager 获取帧间隔
    const frameInterval = MotionManager.getFrameInterval()
    if (frameInterval === Infinity) {
      // 动画被禁用
      return
    }

    // 帧率控制
    if (currentTime - lastFrameTime < frameInterval) {
      animationId = requestAnimationFrame(animate)
      return
    }
    lastFrameTime = currentTime

    const time = Date.now() - startTime
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    if (style.renderCanvas) {
      style.renderCanvas(ctx, canvas.width, canvas.height, time)
    }

    animationId = requestAnimationFrame(animate)
  }

  animationId = requestAnimationFrame(animate)
}

function initParticleSystem() {
  if (!particleCanvasRef.value) return

  // 检查是否启用粒子
  if (!MotionManager.isParticleEnabled()) {
    // 清空画布
    const ctx = particleCanvasRef.value.getContext('2d')
    if (ctx) {
      ctx.clearRect(0, 0, particleCanvasRef.value.width, particleCanvasRef.value.height)
    }
    return
  }

  const style = getThemeStyle(props.theme)

  if (style.particles?.enabled) {
    // 使用 MotionManager 调整粒子数量
    const adjustedConfig = {
      ...style.particles,
      count: MotionManager.getActualParticleCount(style.particles.count)
    }
    particleSystem = new ParticleSystem(particleCanvasRef.value, adjustedConfig)
    particleSystem.start()
  }
}

function cleanup() {
  // 停止动画
  if (animationId !== null) {
    cancelAnimationFrame(animationId)
    animationId = null
  }

  // 移除 resize 监听
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
    resizeHandler = null
  }

  // 停止粒子系统
  if (particleSystem) {
    particleSystem.stop()
    particleSystem = null
  }

  // 清理两个 canvas 的内容
  if (canvasRef.value) {
    const ctx = canvasRef.value.getContext('2d')
    if (ctx) {
      ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
    }
  }
  if (particleCanvasRef.value) {
    const ctx = particleCanvasRef.value.getContext('2d')
    if (ctx) {
      ctx.clearRect(0, 0, particleCanvasRef.value.width, particleCanvasRef.value.height)
    }
  }
}

onMounted(() => {
  startCanvasAnimation()
  initParticleSystem()
})

onUnmounted(() => {
  cleanup()
})

// 监听主题变化
watch(() => props.theme, () => {
  cleanup()
  startCanvasAnimation()
  initParticleSystem()
}, { deep: true })

// 监听动效设置变化
watch(() => motionState.version, () => {
  cleanup()
  startCanvasAnimation()
  initParticleSystem()
})
</script>

<template>
  <div class="theme-canvas-container">
    <canvas ref="canvasRef" class="theme-canvas" />
    <canvas ref="particleCanvasRef" class="particle-canvas" />
  </div>
</template>

<style scoped>
.theme-canvas-container {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.theme-canvas,
.particle-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.particle-canvas {
  z-index: 1;
}
</style>
