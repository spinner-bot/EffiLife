// 主题引擎 - 支持复杂视觉效果
import type { Theme, ThemeType, ParticleConfig } from '@/types'

export interface ThemeStyle {
  // 基础颜色
  bgColor: string
  bgGradient?: string
  textColor: string
  textSecondary: string
  textTertiary: string
  borderColor: string
  buttonBg: string
  buttonText: string
  accentColor: string
  cardBg: string

  // 高级效果
  backdropFilter?: string
  boxShadow?: string
  textShadow?: string
  backgroundImage?: string

  // 粒子配置
  particles?: ParticleConfig

  // Canvas 渲染函数
  renderCanvas?: (ctx: CanvasRenderingContext2D, width: number, height: number, time: number) => void
}

// 主题预设
const themePresets: Record<string, () => ThemeStyle> = {
  // ============ 水墨风格 ============
  ink: () => ({
    bgColor: '#f5f0e6',
    bgGradient: 'radial-gradient(ellipse at center, #f5f0e6 0%, #e8dcc4 100%)',
    textColor: '#2c2c2c',
    textSecondary: '#555555',
    textTertiary: '#888888',
    borderColor: 'rgba(0, 0, 0, 0.1)',
    buttonBg: 'rgba(0, 0, 0, 0.05)',
    buttonText: '#2c2c2c',
    accentColor: '#8b0000',
    cardBg: 'rgba(255, 255, 255, 0.6)',
    backdropFilter: 'blur(2px)',
    boxShadow: '2px 2px 8px rgba(0, 0, 0, 0.1)',
    renderCanvas: (ctx, w, h, time) => {
      // 水墨晕染效果
      ctx.save()
      ctx.globalAlpha = 0.03

      // 随机墨点
      for (let i = 0; i < 5; i++) {
        const x = Math.sin(time * 0.001 + i) * w * 0.3 + w * 0.5
        const y = Math.cos(time * 0.0015 + i * 2) * h * 0.3 + h * 0.5
        const r = 50 + Math.sin(time * 0.002 + i) * 20

        const gradient = ctx.createRadialGradient(x, y, 0, x, y, r)
        gradient.addColorStop(0, 'rgba(0, 0, 0, 0.3)')
        gradient.addColorStop(0.5, 'rgba(0, 0, 0, 0.1)')
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)')

        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.arc(x, y, r, 0, Math.PI * 2)
        ctx.fill()
      }

      // 山水线条
      ctx.globalAlpha = 0.08
      ctx.strokeStyle = '#2c2c2c'
      ctx.lineWidth = 1
      ctx.beginPath()
      for (let x = 0; x < w; x += 20) {
        const y = h * 0.7 + Math.sin(x * 0.01 + time * 0.001) * 30
        if (x === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      ctx.stroke()

      ctx.restore()
    }
  }),

  // ============ 画报/复古风格 ============
  vintage: () => ({
    bgColor: '#f4e4c1',
    bgGradient: 'linear-gradient(135deg, #f4e4c1 0%, #e8d4a8 50%, #d4b896 100%)',
    textColor: '#3d2817',
    textSecondary: '#5c3d2e',
    textTertiary: '#8b6914',
    borderColor: 'rgba(61, 40, 23, 0.2)',
    buttonBg: 'rgba(139, 105, 20, 0.15)',
    buttonText: '#3d2817',
    accentColor: '#8b0000',
    cardBg: 'rgba(244, 228, 193, 0.8)',
    boxShadow: '3px 3px 0px rgba(61, 40, 23, 0.3)',
    renderCanvas: (ctx, w, h) => {
      ctx.save()

      // 复古边框装饰
      ctx.globalAlpha = 0.15
      ctx.strokeStyle = '#3d2817'
      ctx.lineWidth = 2

      // 四角装饰
      const cornerSize = 40
      const corners = [
        [20, 20], [w - 20, 20], [20, h - 20], [w - 20, h - 20]
      ]

      corners.forEach(([x, y]) => {
        ctx.beginPath()
        const dx = x < w / 2 ? 1 : -1
        const dy = y < h / 2 ? 1 : -1
        ctx.moveTo(x, y + dy * cornerSize)
        ctx.lineTo(x, y)
        ctx.lineTo(x + dx * cornerSize, y)
        ctx.stroke()

        // 内部小装饰
        ctx.beginPath()
        ctx.arc(x + dx * 10, y + dy * 10, 3, 0, Math.PI * 2)
        ctx.fillStyle = '#8b0000'
        ctx.fill()
      })

      // 装饰线条
      ctx.globalAlpha = 0.1
      ctx.setLineDash([5, 5])
      ctx.strokeRect(30, 30, w - 60, h - 60)
      ctx.setLineDash([])

      // 复古花纹
      ctx.globalAlpha = 0.05
      for (let i = 0; i < 3; i++) {
        const cx = w * (0.2 + i * 0.3)
        const cy = h * 0.1
        drawFlower(ctx, cx, cy, 15, '#8b0000')
      }

      ctx.restore()
    }
  }),

  // ============ 赛博朋克/科技风格 ============
  cyberpunk: () => ({
    bgColor: '#0a0a1a',
    bgGradient: 'linear-gradient(180deg, #0a0a1a 0%, #1a0a2e 100%)',
    textColor: '#00ffff',
    textSecondary: '#00cccc',
    textTertiary: '#008888',
    borderColor: 'rgba(0, 255, 255, 0.3)',
    buttonBg: 'rgba(0, 255, 255, 0.1)',
    buttonText: '#00ffff',
    accentColor: '#ff00ff',
    cardBg: 'rgba(0, 255, 255, 0.05)',
    backdropFilter: 'blur(5px)',
    boxShadow: '0 0 10px rgba(0, 255, 255, 0.3), inset 0 0 10px rgba(0, 255, 255, 0.1)',
    textShadow: '0 0 5px rgba(0, 255, 255, 0.5)',
    renderCanvas: (ctx, w, h, time) => {
      ctx.save()

      // 网格背景
      ctx.globalAlpha = 0.1
      ctx.strokeStyle = '#00ffff'
      ctx.lineWidth = 0.5

      const gridSize = 40
      const offsetY = (time * 0.02) % gridSize

      for (let x = 0; x < w; x += gridSize) {
        ctx.beginPath()
        ctx.moveTo(x, 0)
        ctx.lineTo(x, h)
        ctx.stroke()
      }

      for (let y = -gridSize + offsetY; y < h + gridSize; y += gridSize) {
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(w, y)
        ctx.stroke()
      }

      // 扫描线
      ctx.globalAlpha = 0.05
      ctx.fillStyle = '#00ffff'
      const scanY = (time * 0.1) % h
      ctx.fillRect(0, scanY, w, 2)

      // 随机数据流
      ctx.globalAlpha = 0.3
      ctx.font = '10px monospace'
      ctx.fillStyle = '#00ffff'
      for (let i = 0; i < 10; i++) {
        const x = (Math.sin(time * 0.001 + i) + 1) * w * 0.5
        const y = (time * 0.5 + i * 100) % h
        const char = String.fromCharCode(0x30A0 + Math.random() * 96)
        ctx.fillText(char, x, y)
      }

      // 光晕效果
      ctx.globalAlpha = 0.1
      const gradient = ctx.createRadialGradient(w * 0.5, h * 0.5, 0, w * 0.5, h * 0.5, w * 0.5)
      gradient.addColorStop(0, 'rgba(0, 255, 255, 0.2)')
      gradient.addColorStop(1, 'rgba(0, 255, 255, 0)')
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, w, h)

      ctx.restore()
    }
  }),

  // ============ 像素风格 ============
  pixel: () => ({
    bgColor: '#1a1c2c',
    textColor: '#f4f4f4',
    textSecondary: '#b8b8b8',
    textTertiary: '#787878',
    borderColor: '#333c57',
    buttonBg: '#333c57',
    buttonText: '#f4f4f4',
    accentColor: '#38b764',
    cardBg: 'rgba(51, 60, 87, 0.8)',
    boxShadow: '4px 4px 0px #0f0f1a',
    renderCanvas: (ctx, w, h, time) => {
      ctx.save()
      ctx.imageSmoothingEnabled = false

      // 像素星星
      ctx.globalAlpha = 0.5
      const starSize = 4
      for (let i = 0; i < 30; i++) {
        const x = Math.floor((Math.sin(i * 1.5) + 1) * w * 0.5 / starSize) * starSize
        const y = Math.floor(((time * 0.01 + i * 50) % h) / starSize) * starSize
        const brightness = Math.sin(time * 0.005 + i) * 0.5 + 0.5

        ctx.fillStyle = `rgba(255, 255, 100, ${brightness * 0.8})`
        ctx.fillRect(x, y, starSize, starSize)
      }

      // 像素月亮
      ctx.globalAlpha = 0.8
      ctx.fillStyle = '#f4e04d'
      const moonX = w * 0.8
      const moonY = h * 0.2
      const moonSize = 40

      for (let dy = -moonSize; dy <= moonSize; dy += starSize) {
        for (let dx = -moonSize; dx <= moonSize; dx += starSize) {
          if (dx * dx + dy * dy <= moonSize * moonSize) {
            if (dx > -moonSize * 0.3) {
              ctx.fillRect(
                Math.floor((moonX + dx) / starSize) * starSize,
                Math.floor((moonY + dy) / starSize) * starSize,
                starSize, starSize
              )
            }
          }
        }
      }

      ctx.restore()
    }
  }),

  // ============ 极光风格 ============
  aurora: () => ({
    bgColor: '#0a0a2a',
    bgGradient: 'linear-gradient(180deg, #0a0a2a 0%, #1a1a4a 100%)',
    textColor: '#e0e0ff',
    textSecondary: '#b0b0dd',
    textTertiary: '#8080aa',
    borderColor: 'rgba(100, 200, 255, 0.2)',
    buttonBg: 'rgba(100, 200, 255, 0.1)',
    buttonText: '#e0e0ff',
    accentColor: '#00ff88',
    cardBg: 'rgba(100, 200, 255, 0.05)',
    backdropFilter: 'blur(10px)',
    renderCanvas: (ctx, w, h, time) => {
      ctx.save()

      // 极光效果
      for (let i = 0; i < 5; i++) {
        ctx.globalAlpha = 0.1 - i * 0.015
        ctx.beginPath()

        const gradient = ctx.createLinearGradient(0, 0, w, 0)
        gradient.addColorStop(0, `hsla(${120 + i * 20}, 100%, 50%, 0.5)`)
        gradient.addColorStop(0.5, `hsla(${180 + i * 20}, 100%, 50%, 0.5)`)
        gradient.addColorStop(1, `hsla(${240 + i * 20}, 100%, 50%, 0.5)`)

        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.moveTo(0, h * 0.3)

        for (let x = 0; x <= w; x += 10) {
          const y = h * 0.3 +
            Math.sin(x * 0.005 + time * 0.001 + i) * 50 +
            Math.sin(x * 0.01 + time * 0.002 + i * 2) * 30
          ctx.lineTo(x, y)
        }

        ctx.lineTo(w, h * 0.5)
        ctx.lineTo(0, h * 0.5)
        ctx.closePath()
        ctx.fill()
      }

      // 星星
      ctx.globalAlpha = 0.8
      ctx.fillStyle = '#ffffff'
      for (let i = 0; i < 50; i++) {
        const x = (Math.sin(i * 7.5) + 1) * w * 0.5
        const y = (Math.cos(i * 3.7) + 1) * h * 0.4
        const size = Math.sin(time * 0.003 + i) * 1 + 1.5
        ctx.beginPath()
        ctx.arc(x, y, size, 0, Math.PI * 2)
        ctx.fill()
      }

      ctx.restore()
    }
  }),

  // ============ 樱花风格 ============
  sakura: () => ({
    bgColor: '#fff0f5',
    bgGradient: 'linear-gradient(180deg, #fff0f5 0%, #ffe4e1 100%)',
    textColor: '#4a3040',
    textSecondary: '#6b4a5a',
    textTertiary: '#8b6a7a',
    borderColor: 'rgba(255, 182, 193, 0.4)',
    buttonBg: 'rgba(255, 182, 193, 0.3)',
    buttonText: '#4a3040',
    accentColor: '#ff69b4',
    cardBg: 'rgba(255, 255, 255, 0.7)',
    boxShadow: '0 4px 15px rgba(255, 105, 180, 0.1)',
    particles: {
      enabled: true,
      type: 'leaves',
      count: 20,
      speed: 1,
      size: 12,
      color: '#ffb6c1'
    },
    renderCanvas: (ctx, w, h) => {
      ctx.save()

      // 樱花树枝
      ctx.globalAlpha = 0.3
      ctx.strokeStyle = '#4a3040'
      ctx.lineWidth = 3

      ctx.beginPath()
      ctx.moveTo(w * 0.1, 0)
      ctx.quadraticCurveTo(w * 0.3, h * 0.2, w * 0.5, h * 0.15)
      ctx.stroke()

      ctx.beginPath()
      ctx.moveTo(w * 0.5, h * 0.15)
      ctx.quadraticCurveTo(w * 0.7, h * 0.1, w * 0.9, h * 0.2)
      ctx.stroke()

      // 小分支
      ctx.lineWidth = 1.5
      for (let i = 0; i < 5; i++) {
        const x = w * (0.2 + i * 0.15)
        const y = h * (0.1 + Math.sin(i) * 0.05)
        ctx.beginPath()
        ctx.moveTo(x, y)
        ctx.lineTo(x + 20, y + 30)
        ctx.stroke()
      }

      ctx.restore()
    }
  }),

  // ============ 深海风格 ============
  ocean: () => ({
    bgColor: '#001a33',
    bgGradient: 'linear-gradient(180deg, #001a33 0%, #003366 50%, #004d99 100%)',
    textColor: '#e0f0ff',
    textSecondary: '#b0d0ff',
    textTertiary: '#80a0cc',
    borderColor: 'rgba(0, 150, 255, 0.3)',
    buttonBg: 'rgba(0, 150, 255, 0.15)',
    buttonText: '#e0f0ff',
    accentColor: '#00ccff',
    cardBg: 'rgba(0, 100, 200, 0.1)',
    backdropFilter: 'blur(5px)',
    particles: {
      enabled: true,
      type: 'bubbles',
      count: 15,
      speed: 0.5,
      size: 8,
      color: 'rgba(255, 255, 255, 0.3)'
    },
    renderCanvas: (ctx, w, h, time) => {
      ctx.save()

      // 水波效果
      ctx.globalAlpha = 0.1
      for (let i = 0; i < 3; i++) {
        ctx.beginPath()
        ctx.strokeStyle = `rgba(0, 200, 255, ${0.2 - i * 0.05})`
        ctx.lineWidth = 2

        for (let x = 0; x <= w; x += 5) {
          const y = h * (0.3 + i * 0.2) +
            Math.sin(x * 0.02 + time * 0.002 + i) * 20 +
            Math.sin(x * 0.01 + time * 0.001) * 10
          if (x === 0) ctx.moveTo(x, y)
          else ctx.lineTo(x, y)
        }
        ctx.stroke()
      }

      // 光线效果
      ctx.globalAlpha = 0.05
      const gradient = ctx.createLinearGradient(0, 0, 0, h)
      gradient.addColorStop(0, 'rgba(255, 255, 255, 0.3)')
      gradient.addColorStop(1, 'rgba(255, 255, 255, 0)')
      ctx.fillStyle = gradient

      for (let i = 0; i < 5; i++) {
        const x = w * (0.2 + i * 0.15) + Math.sin(time * 0.001 + i) * 20
        ctx.beginPath()
        ctx.moveTo(x - 30, 0)
        ctx.lineTo(x + 30, 0)
        ctx.lineTo(x + 50, h)
        ctx.lineTo(x - 50, h)
        ctx.closePath()
        ctx.fill()
      }

      ctx.restore()
    }
  }),

  // ============ 森林风格 ============
  forest: () => ({
    bgColor: '#1a2f1a',
    bgGradient: 'linear-gradient(180deg, #0d1f0d 0%, #1a2f1a 50%, #2d4a2d 100%)',
    textColor: '#e0f0e0',
    textSecondary: '#b0d0b0',
    textTertiary: '#80a080',
    borderColor: 'rgba(100, 200, 100, 0.2)',
    buttonBg: 'rgba(100, 200, 100, 0.15)',
    buttonText: '#e0f0e0',
    accentColor: '#90ee90',
    cardBg: 'rgba(50, 100, 50, 0.2)',
    particles: {
      enabled: true,
      type: 'fireflies',
      count: 20,
      speed: 0.3,
      size: 4,
      color: '#ffff00'
    },
    renderCanvas: (ctx, w, h) => {
      ctx.save()

      // 树木轮廓
      ctx.globalAlpha = 0.2
      ctx.fillStyle = '#0a1a0a'

      const drawTree = (x: number, height: number) => {
        ctx.beginPath()
        ctx.moveTo(x, h)
        ctx.lineTo(x, h - height)
        ctx.lineTo(x - 20, h - height + 30)
        ctx.lineTo(x - 10, h - height + 30)
        ctx.lineTo(x - 30, h - height + 60)
        ctx.lineTo(x - 15, h - height + 60)
        ctx.lineTo(x - 40, h - height + 100)
        ctx.lineTo(x + 40, h - height + 100)
        ctx.lineTo(x + 15, h - height + 60)
        ctx.lineTo(x + 30, h - height + 60)
        ctx.lineTo(x + 10, h - height + 30)
        ctx.lineTo(x + 20, h - height + 30)
        ctx.closePath()
        ctx.fill()
      }

      drawTree(w * 0.15, 200)
      drawTree(w * 0.85, 180)
      drawTree(w * 0.5, 150)

      // 雾气效果
      ctx.globalAlpha = 0.05
      for (let i = 0; i < 3; i++) {
        const y = h * (0.6 + i * 0.1)
        const gradient = ctx.createLinearGradient(0, y - 30, 0, y + 30)
        gradient.addColorStop(0, 'rgba(255, 255, 255, 0)')
        gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.3)')
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0)')
        ctx.fillStyle = gradient
        ctx.fillRect(0, y - 30, w, 60)
      }

      ctx.restore()
    }
  }),
}

// 辅助函数：画花朵
function drawFlower(ctx: CanvasRenderingContext2D, x: number, y: number, size: number, color: string) {
  ctx.fillStyle = color
  for (let i = 0; i < 5; i++) {
    const angle = (i / 5) * Math.PI * 2
    const px = x + Math.cos(angle) * size
    const py = y + Math.sin(angle) * size
    ctx.beginPath()
    ctx.arc(px, py, size * 0.5, 0, Math.PI * 2)
    ctx.fill()
  }
  // 花心
  ctx.fillStyle = '#ffd700'
  ctx.beginPath()
  ctx.arc(x, y, size * 0.3, 0, Math.PI * 2)
  ctx.fill()
}

// 获取主题样式
export function getThemeStyle(theme: Theme | undefined): ThemeStyle {
  // 防护：如果 theme 未定义，返回默认主题
  if (!theme) {
    theme = { type: 'forest' }
  }

  // 检查高级主题预设
  const preset = themePresets[theme.type]
  if (preset) {
    return preset()
  }

  // 处理基础主题
  switch (theme.type) {
    case 'solid': {
      const solid = theme.solid || { bg_window: '#f0f0f0', bg_button: '#e0e0e0', fg_button: '#000000', bg_frame: '#d9d9d9' }
      const isDark = getLuminance(solid.bg_window) < 128
      return {
        bgColor: solid.bg_window,
        textColor: isDark ? '#fafafa' : '#18181b',
        textSecondary: isDark ? '#a1a1aa' : '#52525b',
        textTertiary: isDark ? '#71717a' : '#a1a1aa',
        borderColor: isDark ? 'rgba(255,255,255,0.1)' : '#e4e4e7',
        buttonBg: solid.bg_button,
        buttonText: solid.fg_button,
        accentColor: '#6366f1',
        cardBg: isDark ? 'rgba(255,255,255,0.05)' : solid.bg_frame
      }
    }

    case 'gradient': {
      const gradient = theme.gradient || { color_start: '#667eea', color_end: '#764ba2', direction: 'to-br', fg_button: '#ffffff', card_bg: 'rgba(255,255,255,0.15)' }
      const isDark = getLuminance(gradient.color_start) < 128
      return {
        bgColor: gradient.color_start,
        bgGradient: `linear-gradient(${gradient.direction}, ${gradient.color_start}, ${gradient.color_end})`,
        textColor: gradient.fg_button,
        textSecondary: isDark ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.7)',
        textTertiary: isDark ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.5)',
        borderColor: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.1)',
        buttonBg: gradient.card_bg,
        buttonText: gradient.fg_button,
        accentColor: '#ffffff',
        cardBg: gradient.card_bg,
        backdropFilter: 'blur(10px)'
      }
    }

    case 'glass': {
      const glass = theme.glass || { bg_color: '#1a1a2e', glass_opacity: 0.1, blur_amount: 10, fg_button: '#ffffff', border_color: 'rgba(255,255,255,0.2)' }
      return {
        bgColor: glass.bg_color,
        textColor: glass.fg_button,
        textSecondary: 'rgba(255,255,255,0.8)',
        textTertiary: 'rgba(255,255,255,0.5)',
        borderColor: glass.border_color,
        buttonBg: `rgba(255,255,255,${glass.glass_opacity + 0.1})`,
        buttonText: glass.fg_button,
        accentColor: '#6366f1',
        cardBg: `rgba(255,255,255,${glass.glass_opacity})`,
        backdropFilter: `blur(${glass.blur_amount}px)`
      }
    }

    case 'neon': {
      const neon = theme.neon || { bg_color: '#0a0a0f', neon_color: '#00ff88', glow_intensity: 10, fg_button: '#00ff88', accent_color: '#ff00ff' }
      return {
        bgColor: neon.bg_color,
        textColor: neon.neon_color,
        textSecondary: `${neon.neon_color}cc`,
        textTertiary: `${neon.neon_color}66`,
        borderColor: `${neon.neon_color}40`,
        buttonBg: 'rgba(255,255,255,0.05)',
        buttonText: neon.fg_button,
        accentColor: neon.accent_color,
        cardBg: 'rgba(255,255,255,0.03)',
        boxShadow: `0 0 ${neon.glow_intensity}px ${neon.neon_color}`,
        textShadow: `0 0 ${neon.glow_intensity / 2}px ${neon.neon_color}`
      }
    }

    default:
      // 默认回退
      return {
        bgColor: '#f0f0f0',
        textColor: '#18181b',
        textSecondary: '#52525b',
        textTertiary: '#a1a1aa',
        borderColor: '#e4e4e7',
        buttonBg: '#e0e0e0',
        buttonText: '#000000',
        accentColor: '#6366f1',
        cardBg: '#f0f0f0'
      }
  }
}

// 计算颜色亮度
function getLuminance(hex: string): number {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = (num >> 16) & 255
  const g = (num >> 8) & 255
  const b = num & 255
  return (r * 299 + g * 587 + b * 114) / 1000
}

// 获取所有可用的主题类型
export function getAvailableThemes(): { type: ThemeType; name: string; description: string; preview: string }[] {
  return [
    { type: 'solid', name: '纯色', description: '简洁的纯色主题', preview: '#f0f0f0' },
    { type: 'gradient', name: '渐变', description: '渐变背景主题', preview: 'linear-gradient(135deg, #667eea, #764ba2)' },
    { type: 'glass', name: '玻璃', description: '毛玻璃效果主题', preview: 'rgba(255,255,255,0.1)' },
    { type: 'neon', name: '霓虹', description: '霓虹灯效果主题', preview: '#00ff88' },
    { type: 'ink', name: '水墨', description: '中国水墨画风格', preview: '#f5f0e6' },
    { type: 'vintage', name: '画报', description: '复古画报风格', preview: '#f4e4c1' },
    { type: 'cyberpunk', name: '赛博朋克', description: '未来科技风格', preview: '#0a0a1a' },
    { type: 'pixel', name: '像素', description: '复古像素风格', preview: '#1a1c2c' },
    { type: 'aurora', name: '极光', description: '北极光效果', preview: '#0a0a2a' },
    { type: 'sakura', name: '樱花', description: '日式樱花风格', preview: '#fff0f5' },
    { type: 'ocean', name: '深海', description: '深海探索风格', preview: '#001a33' },
    { type: 'forest', name: '森林', description: '神秘森林风格', preview: '#1a2f1a' },
  ]
}
