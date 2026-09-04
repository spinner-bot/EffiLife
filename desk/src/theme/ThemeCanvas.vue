<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import type { Theme } from '@/types'
import { getThemeStyle } from './ThemeEngine'
import { ParticleSystem } from './ParticleSystem'

const props = defineProps<{
  theme: Theme
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const particleCanvasRef = ref<HTMLCanvasElement | null>(null)
let particleSystem: ParticleSystem | null = null
let animationId: number | null = null
let startTime = Date.now()

function startCanvasAnimation() {
  if (!canvasRef.value) return

  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const resize = () => {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
  }
  resize()
  window.addEventListener('resize', resize)

  const style = getThemeStyle(props.theme)

  const animate = () => {
    const time = Date.now() - startTime
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    if (style.renderCanvas) {
      style.renderCanvas(ctx, canvas.width, canvas.height, time)
    }

    animationId = requestAnimationFrame(animate)
  }

  animate()
}

function initParticleSystem() {
  if (!particleCanvasRef.value) return

  const style = getThemeStyle(props.theme)

  if (style.particles?.enabled) {
    particleSystem = new ParticleSystem(particleCanvasRef.value, style.particles)
    particleSystem.start()
  }
}

function cleanup() {
  if (animationId !== null) {
    cancelAnimationFrame(animationId)
    animationId = null
  }
  if (particleSystem) {
    particleSystem.stop()
    particleSystem = null
  }
}

onMounted(() => {
  startCanvasAnimation()
  initParticleSystem()
})

onUnmounted(() => {
  cleanup()
})

watch(() => props.theme, () => {
  cleanup()
  startCanvasAnimation()
  initParticleSystem()
}, { deep: true })
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
