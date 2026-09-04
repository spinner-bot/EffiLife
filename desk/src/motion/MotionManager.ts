// 动效管理器 - 控制动画帧率、粒子效果等
import { reactive } from 'vue'

export interface MotionSettings {
  // 主开关
  enabled: boolean

  // 帧率设置
  targetFps: number  // 目标帧率：30, 60, 90, 120

  // 动画效果开关
  themeCanvasEnabled: boolean    // 主题画布动画
  particleEnabled: boolean       // 粒子效果
  transitionEnabled: boolean     // 过渡动画

  // 粒子设置
  particleCountMultiplier: number  // 粒子数量倍率：0.5, 1.0, 1.5, 2.0

  // 动效速度
  animationSpeed: number  // 动画速度倍率：0.5, 0.75, 1.0, 1.25, 1.5, 2.0

  // 自动优化
  autoOptimize: boolean
  lastAutoOptimizeTime: number  // 上次自动优化时间
}

export const DEFAULT_MOTION_SETTINGS: MotionSettings = {
  enabled: true,
  targetFps: 120,
  themeCanvasEnabled: true,
  particleEnabled: true,
  transitionEnabled: true,
  particleCountMultiplier: 1.0,
  animationSpeed: 1.0,
  autoOptimize: false,
  lastAutoOptimizeTime: 0
}

const STORAGE_KEY = 'efflife_motion_settings'

// 全局响应式状态
export const motionState = reactive({
  settings: { ...DEFAULT_MOTION_SETTINGS },
  version: 0
})

class MotionManagerClass {
  private benchmarkResults: { fps: number; score: number } | null = null

  constructor() {
    this.loadSettings()
  }

  // ========= 设置持久化 =========

  private loadSettings() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        motionState.settings = { ...DEFAULT_MOTION_SETTINGS, ...parsed }
      }
    } catch (e) {
      console.warn('Failed to load motion settings:', e)
    }
    motionState.version++
  }

  private saveSettings() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(motionState.settings))
      motionState.version++
    } catch (e) {
      console.warn('Failed to save motion settings:', e)
    }
  }

  // ========= 设置操作 =========

  getSettings(): MotionSettings {
    return motionState.settings
  }

  updateSettings(updates: Partial<MotionSettings>) {
    motionState.settings = { ...motionState.settings, ...updates }
    this.saveSettings()
  }

  // ========= 帧率计算 =========

  getFrameInterval(): number {
    if (!motionState.settings.enabled) {
      return Infinity  // 禁用动画
    }
    return 1000 / motionState.settings.targetFps
  }

  getActualParticleCount(baseCount: number): number {
    if (!motionState.settings.particleEnabled) {
      return 0
    }
    return Math.round(baseCount * motionState.settings.particleCountMultiplier)
  }

  isThemeCanvasEnabled(): boolean {
    return motionState.settings.enabled && motionState.settings.themeCanvasEnabled
  }

  isParticleEnabled(): boolean {
    return motionState.settings.enabled && motionState.settings.particleEnabled
  }

  isTransitionEnabled(): boolean {
    return motionState.settings.enabled && motionState.settings.transitionEnabled
  }

  getAnimationSpeed(): number {
    return motionState.settings.animationSpeed
  }

  // ========= 自动优化 =========

  async runAutoOptimize(): Promise<{ fps: number; score: number; recommendation: MotionSettings }> {
    // 运行性能测试
    const result = await this.runBenchmark()
    this.benchmarkResults = result

    // 根据测试结果推荐设置
    const recommendation = this.generateRecommendation(result)

    // 记录优化时间
    motionState.settings.lastAutoOptimizeTime = Date.now()

    return {
      fps: result.fps,
      score: result.score,
      recommendation
    }
  }

  async applyRecommendation(recommendation: MotionSettings) {
    motionState.settings = { ...recommendation }
    motionState.settings.lastAutoOptimizeTime = Date.now()
    this.saveSettings()
  }

  // ========= 性能测试 =========

  private async runBenchmark(): Promise<{ fps: number; score: number }> {
    return new Promise((resolve) => {
      const canvas = document.createElement('canvas')
      canvas.width = 400
      canvas.height = 300
      document.body.appendChild(canvas)

      const ctx = canvas.getContext('2d')!
      const testDuration = 2000  // 测试2秒
      let frameCount = 0
      const startTime = performance.now()

      // 模拟一个中等复杂度的渲染任务
      const renderFrame = () => {
        const now = performance.now()
        const elapsed = now - startTime

        if (elapsed >= testDuration) {
          // 测试结束
          const fps = Math.round((frameCount / elapsed) * 1000)
          document.body.removeChild(canvas)

          // 计算性能分数 (0-100)
          // 60fps = 100分, 30fps = 50分, 15fps = 25分
          const score = Math.min(100, Math.round((fps / 60) * 100))

          resolve({ fps, score })
          return
        }

        // 渲染测试内容
        ctx.clearRect(0, 0, canvas.width, canvas.height)

        // 模拟粒子效果
        for (let i = 0; i < 50; i++) {
          const x = Math.sin(now * 0.001 + i * 0.5) * 150 + 200
          const y = Math.cos(now * 0.0015 + i * 0.3) * 100 + 150
          const size = Math.sin(now * 0.002 + i) * 3 + 5

          ctx.beginPath()
          ctx.arc(x, y, size, 0, Math.PI * 2)
          ctx.fillStyle = `hsl(${(now * 0.1 + i * 10) % 360}, 70%, 60%)`
          ctx.fill()
        }

        // 模拟主题画布效果
        ctx.strokeStyle = 'rgba(100, 100, 255, 0.3)'
        ctx.lineWidth = 2
        ctx.beginPath()
        for (let x = 0; x < canvas.width; x += 10) {
          const y = Math.sin(x * 0.02 + now * 0.001) * 50 + 150
          if (x === 0) ctx.moveTo(x, y)
          else ctx.lineTo(x, y)
        }
        ctx.stroke()

        frameCount++
        requestAnimationFrame(renderFrame)
      }

      requestAnimationFrame(renderFrame)
    })
  }

  private generateRecommendation(result: { fps: number; score: number }): MotionSettings {
    const base = { ...DEFAULT_MOTION_SETTINGS }

    if (result.score >= 90) {
      // 顶级设备 - 120fps
      return {
        ...base,
        enabled: true,
        targetFps: 120,
        themeCanvasEnabled: true,
        particleEnabled: true,
        transitionEnabled: true,
        particleCountMultiplier: 2.0
      }
    } else if (result.score >= 75) {
      // 高性能设备 - 90fps
      return {
        ...base,
        enabled: true,
        targetFps: 90,
        themeCanvasEnabled: true,
        particleEnabled: true,
        transitionEnabled: true,
        particleCountMultiplier: 1.5
      }
    } else if (result.score >= 50) {
      // 中等性能设备 - 60fps
      return {
        ...base,
        enabled: true,
        targetFps: 60,
        themeCanvasEnabled: true,
        particleEnabled: true,
        transitionEnabled: true,
        particleCountMultiplier: 1.0
      }
    } else {
      // 低性能设备 - 30fps
      return {
        ...base,
        enabled: true,
        targetFps: 30,
        themeCanvasEnabled: true,
        particleEnabled: false,
        transitionEnabled: true,
        particleCountMultiplier: 0.5
      }
    }
  }

  getBenchmarkResults() {
    return this.benchmarkResults
  }
}

export const MotionManager = new MotionManagerClass()
