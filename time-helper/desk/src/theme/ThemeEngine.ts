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

  // ============ 午夜图书馆风格 ============
  // 电影调色：参考《哈利波特》图书馆场景 + 伦勃朗光影
  // 三层：背景书架 → 中景烛光漫射 → 前景烛焰+飘页+尘埃
  midnight_library: () => ({
    bgColor: '#1a0e08',
    bgGradient: 'linear-gradient(180deg, #0f0805 0%, #1a0e08 30%, #2c1810 60%, #1a0e08 100%)',
    textColor: '#f5e6c8',
    textSecondary: '#d4b896',
    textTertiary: '#8b7355',
    borderColor: 'rgba(212, 184, 150, 0.15)',
    buttonBg: 'rgba(212, 184, 150, 0.1)',
    buttonText: '#f5e6c8',
    accentColor: '#f4a460',
    cardBg: 'rgba(44, 24, 16, 0.7)',
    backdropFilter: 'blur(4px)',
    boxShadow: '0 4px 24px rgba(0, 0, 0, 0.5), 0 0 60px rgba(244, 164, 96, 0.04)',
    textShadow: '0 0 10px rgba(244, 164, 96, 0.15)',
    particles: {
      enabled: true,
      type: 'stars',
      count: 10,
      speed: 0.15,
      size: 4,
      color: '#f4a460'
    },
    renderCanvas: (ctx, w, h, time) => {
      ctx.save()

      // ===== 背景层：远景拱窗 + 月光 =====
      // 哥特式拱窗（远处透入微弱月光）
      ctx.globalAlpha = 0.06
      ctx.fillStyle = '#4a6080'
      const windowX = w * 0.5
      const windowY = h * 0.05
      const windowW = w * 0.12
      const windowH = h * 0.25
      // 拱形窗框
      ctx.beginPath()
      ctx.moveTo(windowX - windowW / 2, windowY + windowH)
      ctx.lineTo(windowX - windowW / 2, windowY + windowH * 0.4)
      ctx.arc(windowX, windowY + windowH * 0.4, windowW / 2, Math.PI, 0, false)
      ctx.lineTo(windowX + windowW / 2, windowY + windowH)
      ctx.closePath()
      ctx.fill()
      // 月光从窗户透入（淡蓝光柱）
      ctx.globalAlpha = 0.03
      const moonBeam = ctx.createLinearGradient(windowX, windowY + windowH, windowX, h)
      moonBeam.addColorStop(0, 'rgba(150, 180, 220, 0.3)')
      moonBeam.addColorStop(0.5, 'rgba(150, 180, 220, 0.1)')
      moonBeam.addColorStop(1, 'rgba(150, 180, 220, 0)')
      ctx.fillStyle = moonBeam
      ctx.beginPath()
      ctx.moveTo(windowX - windowW / 2, windowY + windowH)
      ctx.lineTo(windowX - windowW * 1.5, h)
      ctx.lineTo(windowX + windowW * 1.5, h)
      ctx.lineTo(windowX + windowW / 2, windowY + windowH)
      ctx.closePath()
      ctx.fill()

      // ===== 中景层：两侧木质书架（丰富的书本细节）=====
      const drawBookshelf = (startX: number, endX: number, direction: number) => {
        const shelfW = Math.abs(endX - startX)
        const rows = 5
        for (let row = 0; row < rows; row++) {
          const shelfY = h * 0.08 + row * (h * 0.18)
          // 木质架板
          ctx.globalAlpha = 0.18
          ctx.fillStyle = '#3a2010'
          ctx.fillRect(startX, shelfY, shelfW, 4)
          // 架板底部阴影
          ctx.globalAlpha = 0.06
          ctx.fillStyle = '#000000'
          ctx.fillRect(startX, shelfY + 4, shelfW, 2)

          // 书本（每本有独立颜色、高度、宽度）
          const bookCount = Math.floor(shelfW / 8)
          let bx = startX + 3
          for (let b = 0; b < bookCount; b++) {
            const seed = row * 100 + b * 7 + direction * 50
            const bookW = 4 + (Math.sin(seed * 0.7) + 1) * 2
            const bookH = 20 + Math.sin(seed * 1.3) * 10 + Math.cos(seed * 0.3) * 5
            const hue = 10 + (seed * 17) % 50  // 棕色系
            const sat = 25 + (seed * 13) % 25
            const light = 15 + (seed * 11) % 15

            ctx.globalAlpha = 0.22
            ctx.fillStyle = `hsl(${hue}, ${sat}%, ${light}%)`
            ctx.fillRect(bx, shelfY - bookH, bookW, bookH)

            // 书脊金色装饰线
            ctx.globalAlpha = 0.08
            ctx.fillStyle = '#d4a060'
            ctx.fillRect(bx + bookW * 0.3, shelfY - bookH + 4, bookW * 0.4, 1)
            ctx.fillRect(bx + bookW * 0.3, shelfY - bookH + bookH - 5, bookW * 0.4, 1)

            bx += bookW + 1
            if (bx > endX - 3) break
          }
        }
      }

      drawBookshelf(0, w * 0.2, 1)
      drawBookshelf(w * 0.8, w, -1)

      // ===== 环境光层：烛光漫射（物理精确的平方反比衰减）=====
      const flickerA = Math.sin(time * 0.008) * 0.4 + Math.sin(time * 0.013) * 0.3 + Math.sin(time * 0.021) * 0.2
      const flickerB = Math.cos(time * 0.011) * 0.3 + Math.sin(time * 0.017) * 0.2
      const candleX = w * 0.5
      const candleY = h * 0.22
      const intensity = 0.85 + flickerA * 0.15  // 烛光强度波动

      // 整体环境暖光（模拟光线在空气中的散射）
      ctx.globalAlpha = 0.12 * intensity
      const ambientWarm = ctx.createRadialGradient(
        candleX, candleY, 0,
        candleX, candleY, w * 0.8
      )
      ambientWarm.addColorStop(0, 'rgba(255, 170, 70, 0.4)')
      ambientWarm.addColorStop(0.15, 'rgba(255, 140, 50, 0.2)')
      ambientWarm.addColorStop(0.4, 'rgba(200, 80, 20, 0.06)')
      ambientWarm.addColorStop(1, 'rgba(0, 0, 0, 0)')
      ctx.fillStyle = ambientWarm
      ctx.fillRect(0, 0, w, h)

      // 书架受光面（光线从中心向两侧衰减）
      const leftShelfLight = ctx.createLinearGradient(w * 0.2, 0, 0, 0)
      leftShelfLight.addColorStop(0, `rgba(255, 160, 60, ${0.08 * intensity})`)
      leftShelfLight.addColorStop(1, 'rgba(255, 160, 60, 0)')
      ctx.globalAlpha = 1
      ctx.fillStyle = leftShelfLight
      ctx.fillRect(0, 0, w * 0.2, h)

      const rightShelfLight = ctx.createLinearGradient(w * 0.8, 0, w, 0)
      rightShelfLight.addColorStop(0, `rgba(255, 160, 60, ${0.08 * intensity})`)
      rightShelfLight.addColorStop(1, 'rgba(255, 160, 60, 0)')
      ctx.fillStyle = rightShelfLight
      ctx.fillRect(w * 0.8, 0, w * 0.2, h)

      // ===== 前景层：烛台 + 烛焰 + 光晕 =====
      // 烛台
      ctx.globalAlpha = 0.35
      ctx.fillStyle = '#2a1a0a'
      // 烛台底座
      ctx.beginPath()
      ctx.ellipse(candleX, candleY + 30, 12, 4, 0, 0, Math.PI * 2)
      ctx.fill()
      // 烛台柱
      ctx.fillRect(candleX - 3, candleY + 8, 6, 22)
      // 蜡烛本体
      ctx.globalAlpha = 0.4
      ctx.fillStyle = '#f5e6c8'
      ctx.fillRect(candleX - 4, candleY - 5, 8, 15)
      // 蜡烛顶部融化的蜡
      ctx.beginPath()
      ctx.ellipse(candleX, candleY - 5, 5, 2, 0, 0, Math.PI * 2)
      ctx.fill()

      // 烛焰外层光晕（大范围柔光）
      ctx.globalAlpha = 0.2 * intensity
      const outerHalo = ctx.createRadialGradient(
        candleX + flickerA * 3, candleY - 8 + flickerB * 2, 0,
        candleX, candleY - 5, 80
      )
      outerHalo.addColorStop(0, 'rgba(255, 200, 100, 0.5)')
      outerHalo.addColorStop(0.3, 'rgba(255, 150, 50, 0.2)')
      outerHalo.addColorStop(0.7, 'rgba(255, 100, 20, 0.05)')
      outerHalo.addColorStop(1, 'rgba(0, 0, 0, 0)')
      ctx.fillStyle = outerHalo
      ctx.beginPath()
      ctx.arc(candleX, candleY - 5, 80, 0, Math.PI * 2)
      ctx.fill()

      // 烛焰本体（三层结构：外层橙色 → 中层黄色 → 内层白色）
      const flameH = 16 + Math.sin(time * 0.018) * 3 + Math.sin(time * 0.027) * 2
      const flameW = 5 + Math.cos(time * 0.022) * 1
      const flameX = candleX + flickerA * 2
      const flameY = candleY - 12

      // 外层火焰（橙红色）
      ctx.globalAlpha = 0.5 * intensity
      const flameOuter = ctx.createRadialGradient(flameX, flameY + 3, 0, flameX, flameY, flameH)
      flameOuter.addColorStop(0, 'rgba(255, 160, 40, 0.8)')
      flameOuter.addColorStop(0.5, 'rgba(255, 100, 20, 0.4)')
      flameOuter.addColorStop(1, 'rgba(255, 50, 10, 0)')
      ctx.fillStyle = flameOuter
      ctx.beginPath()
      ctx.moveTo(flameX, flameY - flameH)
      ctx.bezierCurveTo(
        flameX - flameW * 1.5, flameY - flameH * 0.3,
        flameX - flameW * 1.2, flameY + flameH * 0.3,
        flameX, flameY + flameH * 0.4
      )
      ctx.bezierCurveTo(
        flameX + flameW * 1.2, flameY + flameH * 0.3,
        flameX + flameW * 1.5, flameY - flameH * 0.3,
        flameX, flameY - flameH
      )
      ctx.fill()

      // 内层火焰（亮黄色）
      ctx.globalAlpha = 0.7 * intensity
      const flameInner = ctx.createRadialGradient(flameX, flameY, 0, flameX, flameY, flameH * 0.6)
      flameInner.addColorStop(0, 'rgba(255, 255, 200, 1)')
      flameInner.addColorStop(0.4, 'rgba(255, 220, 100, 0.8)')
      flameInner.addColorStop(1, 'rgba(255, 180, 50, 0)')
      ctx.fillStyle = flameInner
      ctx.beginPath()
      ctx.moveTo(flameX, flameY - flameH * 0.7)
      ctx.bezierCurveTo(
        flameX - flameW * 0.8, flameY - flameH * 0.1,
        flameX - flameW * 0.6, flameY + flameH * 0.2,
        flameX, flameY + flameH * 0.25
      )
      ctx.bezierCurveTo(
        flameX + flameW * 0.6, flameY + flameH * 0.2,
        flameX + flameW * 0.8, flameY - flameH * 0.1,
        flameX, flameY - flameH * 0.7
      )
      ctx.fill()

      // 焰心（白热区域）
      ctx.globalAlpha = 0.6 * intensity
      ctx.fillStyle = 'rgba(255, 255, 240, 0.9)'
      ctx.beginPath()
      ctx.ellipse(flameX, flameY + flameH * 0.1, flameW * 0.3, flameH * 0.15, 0, 0, Math.PI * 2)
      ctx.fill()

      // ===== 飘动的书页（有物理感的曲线运动）=====
      for (let i = 0; i < 4; i++) {
        const phase = time * 0.0003 + i * 2.3
        const drift = Math.sin(phase * 1.7) * 0.5 + Math.cos(phase * 0.9) * 0.3
        const px = w * 0.3 + drift * w * 0.3 + Math.sin(phase * 0.5) * w * 0.1
        const py = ((time * 0.008 + i * h * 0.3) % (h * 1.2)) - h * 0.1
        const rot = Math.sin(time * 0.002 + i * 1.8) * 0.7 + Math.cos(time * 0.001 + i) * 0.3
        // 书页随距离烛光的远近改变亮度
        const distToCandle = Math.sqrt((px - candleX) ** 2 + (py - candleY) ** 2)
        const pageLit = Math.max(0.1, 1 - distToCandle / (w * 0.5))

        ctx.save()
        ctx.translate(px, py)
        ctx.rotate(rot)

        // 书页阴影
        ctx.globalAlpha = 0.06
        ctx.fillStyle = '#000000'
        ctx.beginPath()
        ctx.moveTo(-10 + 2, -7 + 3)
        ctx.quadraticCurveTo(2, -9 + 3, 10 + 2, -7 + 3)
        ctx.quadraticCurveTo(12, 0 + 3, 10 + 2, 7 + 3)
        ctx.quadraticCurveTo(2, 5 + 3, -10 + 2, 7 + 3)
        ctx.quadraticCurveTo(-12, 0 + 3, -10 + 2, -7 + 3)
        ctx.fill()

        // 书页本体（受烛光照亮）
        ctx.globalAlpha = 0.15 + pageLit * 0.1
        ctx.fillStyle = `rgba(245, 230, 200, ${0.8 + pageLit * 0.2})`
        ctx.beginPath()
        ctx.moveTo(-10, -7)
        ctx.quadraticCurveTo(0, -9, 10, -7)
        ctx.quadraticCurveTo(12, 0, 10, 7)
        ctx.quadraticCurveTo(0, 5, -10, 7)
        ctx.quadraticCurveTo(-12, 0, -10, -7)
        ctx.fill()

        // 书页上的文字线条
        ctx.globalAlpha = 0.06 + pageLit * 0.04
        ctx.strokeStyle = '#5c3d2e'
        ctx.lineWidth = 0.5
        for (let line = -4; line <= 4; line += 3) {
          ctx.beginPath()
          ctx.moveTo(-7, line)
          ctx.lineTo(7, line)
          ctx.stroke()
        }

        ctx.restore()
      }

      // ===== 烛光中的尘埃粒子（微小但可见）=====
      for (let i = 0; i < 15; i++) {
        const seed = i * 73.7
        const orbit = time * 0.0002 + seed
        const radius = 30 + (i * 17) % 80
        const dx = candleX + Math.cos(orbit * (1 + i * 0.1)) * radius
        const dy = candleY + Math.sin(orbit * (0.8 + i * 0.05)) * radius * 0.6 - 20
        const dustSize = 0.6 + Math.sin(time * 0.003 + i * 2.1) * 0.3

        // 尘埃受烛光照亮的程度
        const distToCandle = Math.sqrt((dx - candleX) ** 2 + (dy - candleY) ** 2)
        const brightness = Math.max(0, 1 - distToCandle / 120)

        ctx.globalAlpha = brightness * 0.35
        ctx.fillStyle = `rgba(255, 210, 140, ${brightness})`
        ctx.beginPath()
        ctx.arc(dx, dy, dustSize, 0, Math.PI * 2)
        ctx.fill()
      }

      // ===== 地面阴影（烛光投射的渐变暗角）=====
      ctx.globalAlpha = 0.3
      const floorShadow = ctx.createLinearGradient(0, h * 0.85, 0, h)
      floorShadow.addColorStop(0, 'rgba(0, 0, 0, 0)')
      floorShadow.addColorStop(1, 'rgba(0, 0, 0, 0.4)')
      ctx.fillStyle = floorShadow
      ctx.fillRect(0, h * 0.85, w, h * 0.15)

      ctx.restore()
    }
  }),

  // ============ 星际航行风格 ============
  // 电影调色：参考《星际穿越》+ 《银翼杀手2049》太空场景
  // 三层：远景星云 → 中景星星场 → 前景飞船轨迹+飞船
  star_voyage: () => ({
    bgColor: '#05051a',
    bgGradient: 'linear-gradient(135deg, #05051a 0%, #0d0d3a 30%, #1a0a3a 60%, #0a0520 100%)',
    textColor: '#e0e8ff',
    textSecondary: '#b0b8dd',
    textTertiary: '#7078aa',
    borderColor: 'rgba(120, 140, 255, 0.15)',
    buttonBg: 'rgba(120, 140, 255, 0.08)',
    buttonText: '#e0e8ff',
    accentColor: '#88aaff',
    cardBg: 'rgba(15, 15, 45, 0.6)',
    backdropFilter: 'blur(5px)',
    boxShadow: '0 0 30px rgba(100, 120, 255, 0.12), inset 0 0 20px rgba(100, 120, 255, 0.04)',
    textShadow: '0 0 8px rgba(136, 170, 255, 0.25)',
    particles: {
      enabled: true,
      type: 'stars',
      count: 30,
      speed: 0.3,
      size: 2,
      color: '#ffffff'
    },
    renderCanvas: (ctx, w, h, time) => {
      ctx.save()

      // ===== 背景层：深空渐变 + 远景星云 =====
      // 深空基底（已有 bgGradient，这里添加微妙的颜色偏移）
      const deepSpaceShift = Math.sin(time * 0.0002) * 0.02
      ctx.globalAlpha = 0.08 + deepSpaceShift
      const deepGlow = ctx.createRadialGradient(w * 0.3, h * 0.4, 0, w * 0.3, h * 0.4, w * 0.5)
      deepGlow.addColorStop(0, 'rgba(40, 20, 80, 0.3)')
      deepGlow.addColorStop(0.5, 'rgba(20, 10, 50, 0.1)')
      deepGlow.addColorStop(1, 'rgba(0, 0, 0, 0)')
      ctx.fillStyle = deepGlow
      ctx.fillRect(0, 0, w, h)

      // 星云团（3个主星云，各自独立旋转和脉动）
      const nebulae = [
        { cx: 0.25, cy: 0.3, r: 0.18, hue: 260, sat: 70, rotSpeed: 0.00015 },
        { cx: 0.7, cy: 0.5, r: 0.15, hue: 300, sat: 60, rotSpeed: -0.00012 },
        { cx: 0.5, cy: 0.75, r: 0.12, hue: 220, sat: 80, rotSpeed: 0.00018 },
      ]

      nebulae.forEach((neb, n) => {
        const cx = w * neb.cx
        const cy = h * neb.cy
        const baseR = w * neb.r
        const pulse = 1 + Math.sin(time * 0.0005 + n * 2) * 0.05
        const r = baseR * pulse
        const rot = time * neb.rotSpeed
        const hue = neb.hue + Math.sin(time * 0.0003 + n) * 15

        ctx.save()
        ctx.translate(cx, cy)
        ctx.rotate(rot)

        // 星云主体（椭圆+径向渐变）
        ctx.globalAlpha = 0.07
        const nebGrad = ctx.createRadialGradient(0, 0, 0, 0, 0, r)
        nebGrad.addColorStop(0, `hsla(${hue}, ${neb.sat}%, 55%, 0.5)`)
        nebGrad.addColorStop(0.25, `hsla(${hue + 20}, ${neb.sat - 10}%, 40%, 0.3)`)
        nebGrad.addColorStop(0.6, `hsla(${hue + 40}, ${neb.sat - 20}%, 25%, 0.1)`)
        nebGrad.addColorStop(1, `hsla(${hue + 60}, 30%, 15%, 0)`)
        ctx.fillStyle = nebGrad
        ctx.scale(1, 0.55)
        ctx.beginPath()
        ctx.arc(0, 0, r, 0, Math.PI * 2)
        ctx.fill()

        // 星云内部结构（旋涡臂）
        ctx.globalAlpha = 0.04
        for (let arm = 0; arm < 3; arm++) {
          const armAngle = (arm / 3) * Math.PI * 2
          ctx.strokeStyle = `hsla(${hue + arm * 20}, ${neb.sat}%, 60%, 0.3)`
          ctx.lineWidth = 2
          ctx.beginPath()
          for (let t = 0; t < 3; t += 0.1) {
            const spiralR = t * r * 0.3
            const spiralAngle = armAngle + t * 1.5
            const sx = Math.cos(spiralAngle) * spiralR
            const sy = Math.sin(spiralAngle) * spiralR * 0.55
            if (t === 0) ctx.moveTo(sx, sy)
            else ctx.lineTo(sx, sy)
          }
          ctx.stroke()
        }

        ctx.restore()
      })

      // ===== 中景层：星星场（多色温、多大小、有闪烁）=====
      // 使用确定性伪随机保证每帧一致
      for (let i = 0; i < 100; i++) {
        const seed1 = Math.sin(i * 127.1 + 311.7) * 43758.5453
        const seed2 = Math.sin(i * 269.5 + 183.3) * 43758.5453
        const seed3 = Math.sin(i * 419.2 + 371.9) * 43758.5453
        const x = (seed1 - Math.floor(seed1)) * w
        const y = (seed2 - Math.floor(seed2)) * h
        const temp = seed3 - Math.floor(seed3)  // 色温 0-1

        const twinkle = Math.sin(time * 0.003 + i * 1.7) * 0.3 + 0.7
        const baseSize = (seed1 * 10 - Math.floor(seed1 * 10)) * 1.8 + 0.4
        const size = baseSize * twinkle

        // 星星色温（蓝白 → 白 → 黄橙）
        let starColor: string
        if (temp < 0.3) starColor = '#aaccff'      // 蓝白（高温星）
        else if (temp < 0.6) starColor = '#ffffff'   // 白色
        else if (temp < 0.85) starColor = '#ffeedd'  // 暖白
        else starColor = '#ffccaa'                     // 黄橙（低温星）

        ctx.globalAlpha = twinkle * 0.85
        ctx.fillStyle = starColor
        ctx.beginPath()
        ctx.arc(x, y, size, 0, Math.PI * 2)
        ctx.fill()

        // 亮星（size > 1.5）画十字衍射光芒
        if (baseSize > 1.5) {
          ctx.globalAlpha = twinkle * 0.25
          ctx.strokeStyle = starColor
          ctx.lineWidth = 0.5
          const rayLen = size * 4
          ctx.beginPath()
          ctx.moveTo(x - rayLen, y)
          ctx.lineTo(x + rayLen, y)
          ctx.moveTo(x, y - rayLen)
          ctx.lineTo(x, y + rayLen)
          ctx.stroke()
          // 对角光芒（较弱）
          ctx.globalAlpha = twinkle * 0.1
          const diagLen = size * 2.5
          ctx.beginPath()
          ctx.moveTo(x - diagLen, y - diagLen)
          ctx.lineTo(x + diagLen, y + diagLen)
          ctx.moveTo(x + diagLen, y - diagLen)
          ctx.lineTo(x - diagLen, y + diagLen)
          ctx.stroke()
        }
      }

      // ===== 前景层：飞船轨迹 + 飞船 + 引擎光 =====
      // 飞船轨迹（贝塞尔曲线，有流动感）
      const trailProgress = (time * 0.00015) % 1
      ctx.globalAlpha = 0.12
      ctx.strokeStyle = '#88aaff'
      ctx.lineWidth = 1.5
      ctx.setLineDash([3, 6])
      ctx.lineDashOffset = -time * 0.02
      ctx.beginPath()
      ctx.moveTo(-10, h * 0.75)
      ctx.bezierCurveTo(
        w * 0.2, h * 0.55,
        w * 0.5, h * 0.85,
        w * 0.75, h * 0.45
      )
      ctx.bezierCurveTo(
        w * 0.9, h * 0.3,
        w * 1.05, h * 0.35,
        w + 10, h * 0.25
      )
      ctx.stroke()
      ctx.setLineDash([])

      // 飞船位置（沿轨迹运动，有加减速感）
      const shipT = trailProgress
      // 使用三次贝塞尔插值计算飞船位置
      const t = shipT
      const shipX = (1 - t) ** 3 * 0 + 3 * (1 - t) ** 2 * t * w * 0.3 +
        3 * (1 - t) * t ** 2 * w * 0.65 + t ** 3 * w
      const shipY = (1 - t) ** 3 * h * 0.7 + 3 * (1 - t) ** 2 * t * h * 0.4 +
        3 * (1 - t) * t ** 2 * h * 0.5 + t ** 3 * h * 0.3

      // 飞船尾部光迹（渐变拖尾）
      ctx.globalAlpha = 0.15
      const trailGrad = ctx.createLinearGradient(shipX - 30, shipY + 10, shipX, shipY)
      trailGrad.addColorStop(0, 'rgba(136, 170, 255, 0)')
      trailGrad.addColorStop(1, 'rgba(136, 170, 255, 0.4)')
      ctx.strokeStyle = trailGrad
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(shipX - 30, shipY + 10)
      ctx.quadraticCurveTo(shipX - 15, shipY + 5, shipX, shipY)
      ctx.stroke()

      // 飞船本体（三角形飞船）
      ctx.globalAlpha = 0.7
      ctx.fillStyle = '#ccddff'
      ctx.beginPath()
      ctx.moveTo(shipX + 8, shipY - 2)
      ctx.lineTo(shipX - 5, shipY - 5)
      ctx.lineTo(shipX - 3, shipY)
      ctx.lineTo(shipX - 5, shipY + 5)
      ctx.closePath()
      ctx.fill()
      // 飞船高光
      ctx.globalAlpha = 0.3
      ctx.fillStyle = '#ffffff'
      ctx.beginPath()
      ctx.moveTo(shipX + 6, shipY - 2)
      ctx.lineTo(shipX - 2, shipY - 4)
      ctx.lineTo(shipX - 1, shipY - 1)
      ctx.closePath()
      ctx.fill()

      // 引擎光（蓝白色发光）
      ctx.globalAlpha = 0.5
      const engineGlow = ctx.createRadialGradient(
        shipX - 6, shipY, 0,
        shipX - 6, shipY, 10
      )
      engineGlow.addColorStop(0, 'rgba(180, 210, 255, 0.8)')
      engineGlow.addColorStop(0.3, 'rgba(136, 170, 255, 0.4)')
      engineGlow.addColorStop(1, 'rgba(136, 170, 255, 0)')
      ctx.fillStyle = engineGlow
      ctx.beginPath()
      ctx.arc(shipX - 6, shipY, 10, 0, Math.PI * 2)
      ctx.fill()

      // 引擎喷流（小粒子）
      for (let p = 0; p < 5; p++) {
        const pAge = (time * 0.005 + p * 0.3) % 2
        const px = shipX - 8 - pAge * 8
        const py = shipY + Math.sin(pAge * 3 + p) * 2
        const pAlpha = Math.max(0, 0.3 - pAge * 0.15)
        const pSize = 1 + pAge * 0.5

        ctx.globalAlpha = pAlpha
        ctx.fillStyle = 'rgba(136, 170, 255, 0.6)'
        ctx.beginPath()
        ctx.arc(px, py, pSize, 0, Math.PI * 2)
        ctx.fill()
      }

      // ===== 镜头光晕（当飞船在特定位置时）=====
      if (shipT > 0.3 && shipT < 0.7) {
        const lensFlareIntensity = 1 - Math.abs(shipT - 0.5) * 5
        ctx.globalAlpha = lensFlareIntensity * 0.05
        const flare = ctx.createRadialGradient(shipX, shipY, 0, shipX, shipY, w * 0.3)
        flare.addColorStop(0, 'rgba(180, 210, 255, 0.3)')
        flare.addColorStop(0.5, 'rgba(136, 170, 255, 0.05)')
        flare.addColorStop(1, 'rgba(0, 0, 0, 0)')
        ctx.fillStyle = flare
        ctx.fillRect(0, 0, w, h)
      }

      ctx.restore()
    }
  }),

  // ============ 雨夜城市风格 ============
  // 电影调色：参考《银翼杀手2049》+ 《迷失东京》雨夜场景
  // 三层：背景天空+云层 → 中景建筑天际线 → 前景雨滴+霓虹倒影+窗户水雾
  rainy_city: () => ({
    bgColor: '#0a0f1a',
    bgGradient: 'linear-gradient(180deg, #050810 0%, #0a0f1a 25%, #111828 50%, #0d1520 100%)',
    textColor: '#c8d8e8',
    textSecondary: '#8898aa',
    textTertiary: '#556070',
    borderColor: 'rgba(100, 160, 220, 0.12)',
    buttonBg: 'rgba(100, 160, 220, 0.08)',
    buttonText: '#c8d8e8',
    accentColor: '#4488cc',
    cardBg: 'rgba(10, 20, 40, 0.75)',
    backdropFilter: 'blur(5px)',
    boxShadow: '0 4px 24px rgba(0, 0, 0, 0.6), 0 0 40px rgba(68, 136, 204, 0.03)',
    textShadow: '0 0 6px rgba(68, 136, 204, 0.15)',
    particles: {
      enabled: true,
      type: 'snow',
      count: 35,
      speed: 3.5,
      size: 1.5,
      color: 'rgba(150, 200, 255, 0.35)'
    },
    renderCanvas: (ctx, w, h, time) => {
      ctx.save()

      // ===== 背景层：阴沉天空 + 流动云层 =====
      // 天空的微弱光照变化（远处城市光污染）
      const skyPulse = Math.sin(time * 0.0003) * 0.02
      ctx.globalAlpha = 0.08 + skyPulse
      const cityGlow = ctx.createRadialGradient(w * 0.5, h, 0, w * 0.5, h, h * 0.8)
      cityGlow.addColorStop(0, 'rgba(100, 140, 180, 0.25)')
      cityGlow.addColorStop(0.4, 'rgba(80, 100, 140, 0.1)')
      cityGlow.addColorStop(1, 'rgba(0, 0, 0, 0)')
      ctx.fillStyle = cityGlow
      ctx.fillRect(0, 0, w, h)

      // 低垂的云层（缓慢移动）
      ctx.globalAlpha = 0.06
      for (let c = 0; c < 3; c++) {
        const cloudY = h * (0.1 + c * 0.08)
        const cloudDrift = (time * 0.003 + c * 100) % (w * 1.5) - w * 0.25
        const cloudW = w * (0.3 + c * 0.1)
        const cloudH = 20 + c * 8

        const cloudGrad = ctx.createRadialGradient(
          cloudDrift + cloudW / 2, cloudY, 0,
          cloudDrift + cloudW / 2, cloudY, cloudW / 2
        )
        cloudGrad.addColorStop(0, 'rgba(60, 80, 100, 0.4)')
        cloudGrad.addColorStop(0.5, 'rgba(40, 60, 80, 0.2)')
        cloudGrad.addColorStop(1, 'rgba(20, 30, 50, 0)')
        ctx.fillStyle = cloudGrad
        ctx.beginPath()
        ctx.ellipse(cloudDrift + cloudW / 2, cloudY, cloudW / 2, cloudH, 0, 0, Math.PI * 2)
        ctx.fill()
      }

      // ===== 中景层：建筑群天际线（前后两层，有深度感）=====
      // 远景建筑（较暗，较小）
      ctx.globalAlpha = 0.15
      ctx.fillStyle = '#080c15'
      const farBuildings = [
        { x: 0, w: 35, h: 80 }, { x: 30, w: 25, h: 110 }, { x: 50, w: 40, h: 90 },
        { x: 85, w: 20, h: 130 }, { x: 100, w: 35, h: 100 }, { x: 130, w: 30, h: 120 },
        { x: 155, w: 45, h: 95 }, { x: 195, w: 25, h: 140 }, { x: 215, w: 35, h: 105 },
        { x: 245, w: 40, h: 125 }, { x: 280, w: 30, h: 115 }, { x: 305, w: 35, h: 135 },
        { x: 335, w: 40, h: 100 }, { x: 370, w: 30, h: 120 },
      ]
      const farScale = w / 400
      farBuildings.forEach(b => {
        const bx = b.x * farScale
        const bw = b.w * farScale
        const bh = b.h * (h / 500)
        ctx.fillRect(bx, h - bh - 20, bw, bh + 20)
      })

      // 近景建筑（更暗，更高，有详细窗户）
      ctx.globalAlpha = 0.3
      ctx.fillStyle = '#0a1020'
      const nearBuildings = [
        { x: -5, w: 45, h: 140, windows: true },
        { x: 35, w: 32, h: 200, windows: true },
        { x: 62, w: 55, h: 165, windows: true },
        { x: 112, w: 28, h: 220, windows: true },
        { x: 135, w: 48, h: 150, windows: true },
        { x: 178, w: 38, h: 190, windows: true },
        { x: 210, w: 58, h: 160, windows: true },
        { x: 262, w: 32, h: 230, windows: true },
        { x: 288, w: 42, h: 175, windows: true },
        { x: 325, w: 52, h: 210, windows: true },
        { x: 372, w: 38, h: 165, windows: true },
        { x: 405, w: 48, h: 195, windows: true },
      ]
      const nearScale = w / 450
      nearBuildings.forEach(b => {
        const bx = b.x * nearScale
        const bw = b.w * nearScale
        const bh = b.h * (h / 450)
        ctx.fillRect(bx, h - bh, bw, bh)

        // 建筑顶部细节（天线/冷却塔）
        if (b.h > 180) {
          ctx.fillRect(bx + bw * 0.4, h - bh - 15, bw * 0.2, 15)
          ctx.fillRect(bx + bw * 0.45, h - bh - 25, bw * 0.1, 10)
        }

        // 窗户灯光（有随机性但有规律）
        if (b.windows) {
          const winW = 5
          const winH = 7
          const winGapX = 10
          const winGapY = 16
          for (let wy = h - bh + 12; wy < h - 20; wy += winGapY) {
            for (let wx = bx + 6; wx < bx + bw - 8; wx += winGapX) {
              // 使用确定性伪随机判断是否亮灯
              const winSeed = wx * 7.3 + wy * 13.7
              const isLit = Math.sin(winSeed) > -0.3
              if (isLit) {
                // 窗户颜色有细微差异（暖黄 → 暖白）
                const hue = 38 + Math.sin(winSeed * 0.5) * 8
                const sat = 70 + Math.cos(winSeed * 0.3) * 15
                const light = 60 + Math.sin(winSeed * 0.7) * 10
                const winAlpha = 0.35 + Math.sin(time * 0.001 + winSeed) * 0.05

                ctx.globalAlpha = winAlpha
                ctx.fillStyle = `hsl(${hue}, ${sat}%, ${light}%)`
                ctx.fillRect(wx, wy, winW, winH)

                // 窗户光晕（微弱）
                ctx.globalAlpha = winAlpha * 0.3
                const winGlow = ctx.createRadialGradient(
                  wx + winW / 2, wy + winH / 2, 0,
                  wx + winW / 2, wy + winH / 2, winW * 1.5
                )
                winGlow.addColorStop(0, `hsla(${hue}, ${sat}%, ${light}%, 0.3)`)
                winGlow.addColorStop(1, `hsla(${hue}, ${sat}%, ${light}%, 0)`)
                ctx.fillStyle = winGlow
                ctx.fillRect(wx - winW, wy - winH, winW * 3, winH * 3)
              }
            }
          }
          ctx.globalAlpha = 0.3
          ctx.fillStyle = '#0a1020'
        }
      })

      // ===== 前景层：雨滴 + 地面水洼 + 雾气 =====
      // 雨滴（有速度感和方向感）
      ctx.globalAlpha = 0.25
      ctx.strokeStyle = 'rgba(150, 200, 255, 0.35)'
      ctx.lineWidth = 1
      const rainAngle = 0.08  // 雨滴倾斜角度
      for (let i = 0; i < 60; i++) {
        const seed = i * 73.1
        const rx = (Math.sin(seed) * 43758.5453 % 1) * w
        const adjustedRx = rx < 0 ? rx + w : rx
        const ry = (time * 2.5 + i * 31) % (h + 40) - 20
        const len = 12 + (i % 6) * 3
        const windOffset = ry * rainAngle

        ctx.beginPath()
        ctx.moveTo(adjustedRx + windOffset, ry)
        ctx.lineTo(adjustedRx + windOffset - 1.5, ry + len)
        ctx.stroke()
      }

      // 地面水洼（反射霓虹灯光）
      const puddleY = h * 0.9
      ctx.globalAlpha = 0.08
      // 水洼基底
      const puddleGrad = ctx.createLinearGradient(0, puddleY, 0, h)
      puddleGrad.addColorStop(0, 'rgba(20, 30, 50, 0.3)')
      puddleGrad.addColorStop(1, 'rgba(10, 15, 25, 0.6)')
      ctx.fillStyle = puddleGrad
      ctx.fillRect(0, puddleY, w, h - puddleY)

      // 水洼中的霓虹反射（蓝、紫、绿）
      const neonColors = [
        { x: 0.2, color: 'rgba(68, 136, 204, 0.4)' },
        { x: 0.5, color: 'rgba(136, 68, 204, 0.3)' },
        { x: 0.8, color: 'rgba(68, 204, 136, 0.25)' },
      ]
      neonColors.forEach(neon => {
        const neonX = w * neon.x
        const ripple = Math.sin(time * 0.002 + neon.x * 10) * 3
        ctx.globalAlpha = 0.06
        const neonGlow = ctx.createRadialGradient(
          neonX + ripple, puddleY + 10, 0,
          neonX, puddleY + 15, w * 0.15
        )
        neonGlow.addColorStop(0, neon.color)
        neonGlow.addColorStop(0.5, neon.color.replace('0.4', '0.15').replace('0.3', '0.1').replace('0.25', '0.08'))
        neonGlow.addColorStop(1, 'rgba(0, 0, 0, 0)')
        ctx.fillStyle = neonGlow
        ctx.beginPath()
        ctx.ellipse(neonX, puddleY + 15, w * 0.15, 15, 0, 0, Math.PI * 2)
        ctx.fill()
      })

      // 雾气（贴近地面的薄雾）
      ctx.globalAlpha = 0.05
      for (let i = 0; i < 3; i++) {
        const fogY = h * (0.75 + i * 0.05)
        const fogDrift = Math.sin(time * 0.0004 + i * 2) * 15
        const fogGrad = ctx.createLinearGradient(0, fogY - 20, 0, fogY + 20)
        fogGrad.addColorStop(0, 'rgba(120, 150, 180, 0)')
        fogGrad.addColorStop(0.5, 'rgba(120, 150, 180, 0.3)')
        fogGrad.addColorStop(1, 'rgba(120, 150, 180, 0)')
        ctx.fillStyle = fogGrad
        ctx.fillRect(fogDrift, fogY - 20, w, 40)
      }

      // 窗户上的水雾（前景玻璃效果）
      ctx.globalAlpha = 0.03
      for (let i = 0; i < 8; i++) {
        const dropX = (Math.sin(i * 47.3) * 43758.5453 % 1) * w
        const adjDropX = dropX < 0 ? dropX + w : dropX
        const dropY = (Math.cos(i * 23.7) * 43758.5453 % 1) * h * 0.6 + h * 0.1
        const dropR = 2 + Math.sin(time * 0.001 + i) * 1

        const dropGrad = ctx.createRadialGradient(
          adjDropX, dropY, 0,
          adjDropX, dropY, dropR
        )
        dropGrad.addColorStop(0, 'rgba(200, 220, 240, 0.4)')
        dropGrad.addColorStop(1, 'rgba(200, 220, 240, 0)')
        ctx.fillStyle = dropGrad
        ctx.beginPath()
        ctx.arc(adjDropX, dropY, dropR, 0, Math.PI * 2)
        ctx.fill()
      }

      ctx.restore()
    }
  }),

  // ============ 沙漠黄昏风格 ============
  // 电影调色：参考《阿拉伯的劳伦斯》+ 《沙丘》黄昏场景
  // 三层：背景天空+落日 → 中景沙丘+热浪 → 前景沙粒+地面纹理
  desert_dusk: () => ({
    bgColor: '#1a0a20',
    bgGradient: 'linear-gradient(180deg, #2d1040 0%, #5a1a3a 20%, #a04020 45%, #d07030 65%, #c08040 80%, #6a4020 100%)',
    textColor: '#f5e0c0',
    textSecondary: '#d4b080',
    textTertiary: '#907050',
    borderColor: 'rgba(208, 112, 48, 0.15)',
    buttonBg: 'rgba(208, 112, 48, 0.1)',
    buttonText: '#f5e0c0',
    accentColor: '#e08030',
    cardBg: 'rgba(45, 16, 64, 0.5)',
    backdropFilter: 'blur(4px)',
    boxShadow: '0 4px 24px rgba(160, 64, 32, 0.25), 0 0 50px rgba(224, 128, 48, 0.05)',
    textShadow: '0 0 10px rgba(224, 128, 48, 0.2)',
    particles: {
      enabled: true,
      type: 'stars',
      count: 10,
      speed: 0.25,
      size: 1.5,
      color: '#d4a060'
    },
    renderCanvas: (ctx, w, h, time) => {
      ctx.save()

      // ===== 背景层：天空渐变 + 落日 =====
      // 天空颜色随时间微妙变化（模拟黄昏过渡）
      const duskProgress = Math.sin(time * 0.0001) * 0.1 + 0.5
      ctx.globalAlpha = 0.08
      const skyTint = ctx.createLinearGradient(0, 0, 0, h * 0.5)
      skyTint.addColorStop(0, `rgba(45, 16, 64, ${0.3 + duskProgress * 0.1})`)
      skyTint.addColorStop(1, 'rgba(0, 0, 0, 0)')
      ctx.fillStyle = skyTint
      ctx.fillRect(0, 0, w, h * 0.5)

      // 落日（多层光晕，模拟大气散射）
      const sunX = w * 0.65
      const sunY = h * 0.32
      const sunR = 45

      // 最外层光晕（大气散射）
      ctx.globalAlpha = 0.12
      const sunAtmosphere = ctx.createRadialGradient(sunX, sunY, sunR * 2, sunX, sunY, sunR * 6)
      sunAtmosphere.addColorStop(0, 'rgba(255, 140, 40, 0.25)')
      sunAtmosphere.addColorStop(0.4, 'rgba(255, 100, 30, 0.1)')
      sunAtmosphere.addColorStop(1, 'rgba(255, 60, 20, 0)')
      ctx.fillStyle = sunAtmosphere
      ctx.fillRect(0, 0, w, h)

      // 中层光晕（日落光辉）
      ctx.globalAlpha = 0.2
      const sunMidGlow = ctx.createRadialGradient(sunX, sunY, sunR * 0.8, sunX, sunY, sunR * 3)
      sunMidGlow.addColorStop(0, 'rgba(255, 180, 60, 0.5)')
      sunMidGlow.addColorStop(0.5, 'rgba(255, 120, 40, 0.2)')
      sunMidGlow.addColorStop(1, 'rgba(255, 80, 25, 0)')
      ctx.fillStyle = sunMidGlow
      ctx.beginPath()
      ctx.arc(sunX, sunY, sunR * 3, 0, Math.PI * 2)
      ctx.fill()

      // 太阳本体（明亮核心）
      ctx.globalAlpha = 0.7
      const sunCore = ctx.createRadialGradient(sunX, sunY, 0, sunX, sunY, sunR)
      sunCore.addColorStop(0, 'rgba(255, 240, 150, 1)')
      sunCore.addColorStop(0.3, 'rgba(255, 200, 80, 0.9)')
      sunCore.addColorStop(0.7, 'rgba(255, 140, 50, 0.5)')
      sunCore.addColorStop(1, 'rgba(255, 100, 30, 0)')
      ctx.fillStyle = sunCore
      ctx.beginPath()
      ctx.arc(sunX, sunY, sunR, 0, Math.PI * 2)
      ctx.fill()

      // 太阳表面细节（微弱的光斑）
      ctx.globalAlpha = 0.15
      for (let s = 0; s < 3; s++) {
        const spotAngle = time * 0.0002 + s * 2
        const spotX = sunX + Math.cos(spotAngle) * sunR * 0.4
        const spotY = sunY + Math.sin(spotAngle) * sunR * 0.3
        const spotR = sunR * 0.15

        const spotGrad = ctx.createRadialGradient(spotX, spotY, 0, spotX, spotY, spotR)
        spotGrad.addColorStop(0, 'rgba(255, 255, 200, 0.4)')
        spotGrad.addColorStop(1, 'rgba(255, 255, 200, 0)')
        ctx.fillStyle = spotGrad
        ctx.beginPath()
        ctx.arc(spotX, spotY, spotR, 0, Math.PI * 2)
        ctx.fill()
      }

      // ===== 中景层：沙丘（三层深度）+ 热浪效果 =====
      // 远景沙丘（最暗，最模糊）
      ctx.globalAlpha = 0.25
      ctx.fillStyle = '#2a1510'
      ctx.beginPath()
      ctx.moveTo(0, h * 0.68)
      for (let x = 0; x <= w; x += 4) {
        const y = h * 0.68 + Math.sin(x * 0.007 + 0.5) * 28 + Math.sin(x * 0.003 + 1) * 15
        ctx.lineTo(x, y)
      }
      ctx.lineTo(w, h)
      ctx.lineTo(0, h)
      ctx.closePath()
      ctx.fill()

      // 中景沙丘（中等色调）
      ctx.globalAlpha = 0.45
      ctx.fillStyle = '#1a0a08'
      ctx.beginPath()
      ctx.moveTo(0, h * 0.76)
      for (let x = 0; x <= w; x += 4) {
        const y = h * 0.76 + Math.sin(x * 0.005 + 2) * 22 + Math.sin(x * 0.012 + time * 0.00008) * 10
        ctx.lineTo(x, y)
      }
      ctx.lineTo(w, h)
      ctx.lineTo(0, h)
      ctx.closePath()
      ctx.fill()

      // 近景沙丘（最亮，最清晰）
      ctx.globalAlpha = 0.65
      ctx.fillStyle = '#0f0505'
      ctx.beginPath()
      ctx.moveTo(0, h * 0.84)
      for (let x = 0; x <= w; x += 4) {
        const y = h * 0.84 + Math.sin(x * 0.009 + 1) * 18 + Math.sin(x * 0.004 + 0.5) * 22
        ctx.lineTo(x, y)
      }
      ctx.lineTo(w, h)
      ctx.lineTo(0, h)
      ctx.closePath()
      ctx.fill()

      // 沙丘受光面（落日从右侧照射）
      ctx.globalAlpha = 0.08
      const duneLight = ctx.createLinearGradient(w * 0.5, 0, w, 0)
      duneLight.addColorStop(0, 'rgba(255, 160, 60, 0)')
      duneLight.addColorStop(0.7, 'rgba(255, 160, 60, 0.2)')
      duneLight.addColorStop(1, 'rgba(255, 140, 50, 0.35)')
      ctx.fillStyle = duneLight
      ctx.fillRect(0, h * 0.68, w, h * 0.32)

      // 热浪效果（贴近地面的空气扭曲）
      ctx.globalAlpha = 0.03
      for (let i = 0; i < 4; i++) {
        const heatY = h * (0.72 + i * 0.04)
        const heatWave = Math.sin(time * 0.001 + i * 1.5) * 2
        const heatGrad = ctx.createLinearGradient(0, heatY - 15, 0, heatY + 15)
        heatGrad.addColorStop(0, 'rgba(255, 200, 100, 0)')
        heatGrad.addColorStop(0.5, 'rgba(255, 200, 100, 0.3)')
        heatGrad.addColorStop(1, 'rgba(255, 200, 100, 0)')
        ctx.fillStyle = heatGrad
        ctx.fillRect(heatWave, heatY - 15, w, 30)
      }

      // ===== 前景层：飘动沙粒 + 地面纹理 =====
      // 飘动沙粒（有风速变化）
      const windSpeed = 0.025 + Math.sin(time * 0.0005) * 0.008
      ctx.globalAlpha = 0.3
      ctx.fillStyle = '#d4a060'
      for (let i = 0; i < 20; i++) {
        const seed = i * 37.3
        const baseX = (time * windSpeed * (1 + i * 0.05) + seed) % (w * 1.2) - w * 0.1
        const baseY = h * 0.5 + Math.sin(time * 0.002 + seed) * h * 0.25
        const size = 0.8 + Math.sin(seed) * 0.5
        const alpha = 0.2 + Math.sin(time * 0.003 + seed * 2) * 0.15

        // 沙粒受落日照亮
        const distToSun = Math.sqrt((baseX - sunX) ** 2 + (baseY - sunY) ** 2)
        const sunLit = Math.max(0.3, 1 - distToSun / (w * 0.6))

        ctx.globalAlpha = alpha * sunLit
        ctx.fillStyle = `rgba(212, 160, 96, ${sunLit})`
        ctx.beginPath()
        ctx.arc(baseX, baseY, size, 0, Math.PI * 2)
        ctx.fill()
      }

      // 地面纹理（沙丘表面的细微纹理）
      ctx.globalAlpha = 0.04
      ctx.strokeStyle = '#d4a060'
      ctx.lineWidth = 0.5
      for (let i = 0; i < 8; i++) {
        const rippleY = h * (0.88 + i * 0.015)
        ctx.beginPath()
        for (let x = 0; x <= w; x += 3) {
          const y = rippleY + Math.sin(x * 0.02 + i * 0.8) * 2
          if (x === 0) ctx.moveTo(x, y)
          else ctx.lineTo(x, y)
        }
        ctx.stroke()
      }

      // 黄昏星星（只在天空上方，很微弱）
      for (let i = 0; i < 12; i++) {
        const seed1 = Math.sin(i * 47.3) * 43758.5453
        const seed2 = Math.cos(i * 23.7) * 43758.5453
        const sx = (seed1 - Math.floor(seed1)) * w
        const sy = (seed2 - Math.floor(seed2)) * h * 0.25
        const twinkle = Math.sin(time * 0.003 + i * 2.3) * 0.3 + 0.5

        ctx.globalAlpha = twinkle * 0.35
        ctx.fillStyle = '#ffffff'
        ctx.beginPath()
        ctx.arc(sx, sy, 0.8, 0, Math.PI * 2)
        ctx.fill()
      }

      ctx.restore()
    }
  }),

  // ============ 竹林清晨风格 ============
  // 电影调色：参考《卧虎藏龙》竹林场景 + 日本枯山水美学
  // 三层：背景远山+晨雾 → 中景竹林 → 前景近竹+露珠+光线
  bamboo_dawn: () => ({
    bgColor: '#e8f0e0',
    bgGradient: 'linear-gradient(180deg, #c8d8c0 0%, #d8e8d0 20%, #e8f0e0 45%, #f0f5ea 70%, #e0ecd8 100%)',
    textColor: '#2a3a2a',
    textSecondary: '#4a5a4a',
    textTertiary: '#7a8a7a',
    borderColor: 'rgba(60, 100, 60, 0.15)',
    buttonBg: 'rgba(60, 100, 60, 0.08)',
    buttonText: '#2a3a2a',
    accentColor: '#5a8a5a',
    cardBg: 'rgba(255, 255, 255, 0.55)',
    backdropFilter: 'blur(4px)',
    boxShadow: '0 2px 16px rgba(60, 100, 60, 0.12), 0 0 40px rgba(120, 160, 120, 0.04)',
    textShadow: '0 0 4px rgba(120, 160, 120, 0.15)',
    particles: {
      enabled: true,
      type: 'leaves',
      count: 8,
      speed: 0.4,
      size: 7,
      color: '#6a9a5a'
    },
    renderCanvas: (ctx, w, h, time) => {
      ctx.save()

      // ===== 背景层：远山轮廓 + 弥漫晨雾 =====
      // 远山（2-3层，越远越淡）
      ctx.globalAlpha = 0.08
      ctx.fillStyle = '#8a9a8a'
      ctx.beginPath()
      ctx.moveTo(0, h * 0.35)
      for (let x = 0; x <= w; x += 6) {
        const y = h * 0.35 + Math.sin(x * 0.004 + 0.5) * 30 + Math.sin(x * 0.002) * 20
        ctx.lineTo(x, y)
      }
      ctx.lineTo(w, h)
      ctx.lineTo(0, h)
      ctx.closePath()
      ctx.fill()

      ctx.globalAlpha = 0.12
      ctx.fillStyle = '#7a8a7a'
      ctx.beginPath()
      ctx.moveTo(0, h * 0.42)
      for (let x = 0; x <= w; x += 5) {
        const y = h * 0.42 + Math.sin(x * 0.005 + 1) * 25 + Math.sin(x * 0.003 + 2) * 18
        ctx.lineTo(x, y)
      }
      ctx.lineTo(w, h)
      ctx.lineTo(0, h)
      ctx.closePath()
      ctx.fill()

      // 晨雾（多层，有流动感）
      for (let i = 0; i < 4; i++) {
        const fogY = h * (0.3 + i * 0.1)
        const fogDrift = Math.sin(time * 0.0004 + i * 1.7) * 25
        const fogH = 40 + i * 10

        ctx.globalAlpha = 0.06 - i * 0.008
        const fogGrad = ctx.createLinearGradient(0, fogY - fogH / 2, 0, fogY + fogH / 2)
        fogGrad.addColorStop(0, 'rgba(240, 245, 235, 0)')
        fogGrad.addColorStop(0.3, 'rgba(240, 245, 235, 0.4)')
        fogGrad.addColorStop(0.7, 'rgba(240, 245, 235, 0.4)')
        fogGrad.addColorStop(1, 'rgba(240, 245, 235, 0)')
        ctx.fillStyle = fogGrad
        ctx.fillRect(fogDrift, fogY - fogH / 2, w, fogH)
      }

      // ===== 中景层：竹林（左右两侧，有深度）=====
      // 竹干绘制函数（更自然的曲线）
      const drawBambooStalk = (baseX: number, segments: number, sway: number, thickness: number) => {
        ctx.globalAlpha = 0.22
        ctx.strokeStyle = '#3a5a3a'
        ctx.lineWidth = thickness

        let curX = baseX
        let curY = h
        let prevSway = 0

        for (let s = 0; s < segments; s++) {
          const segH = h / segments
          const topY = curY - segH
          // 竹子的摇摆有惯性感（越顶端摆幅越大）
          const swayX = Math.sin(time * 0.001 + s * 0.6 + baseX * 0.01) * sway * (s / segments + 0.3)

          // 竹节（略带弧度）
          ctx.beginPath()
          ctx.moveTo(curX, curY)
          ctx.quadraticCurveTo(
            (curX + curX + swayX) / 2 + prevSway * 0.3,
            (curY + topY) / 2,
            curX + swayX, topY
          )
          ctx.stroke()

          // 竹节环（更立体）
          ctx.globalAlpha = 0.3
          ctx.lineWidth = thickness + 2
          ctx.beginPath()
          ctx.ellipse(curX + swayX, topY, thickness * 0.7, thickness * 0.3, 0, 0, Math.PI * 2)
          ctx.stroke()

          // 竹叶（更自然，有层次）
          if (s > 1 && s % 2 === 0) {
            const leafDir = (s + Math.floor(baseX / 50)) % 2 === 0 ? 1 : -1
            const leafCount = 2 + (s % 2)
            const leafBaseX = curX + swayX
            const leafBaseY = topY + segH * 0.35

            for (let l = 0; l < leafCount; l++) {
              const leafAngle = (l / leafCount) * 0.5 - 0.25
              const leafLen = 25 + l * 5
              const leafWidth = 6 + l * 2

              ctx.globalAlpha = 0.18 - l * 0.03
              ctx.fillStyle = l === 0 ? '#4a7a3a' : '#5a8a4a'
              ctx.beginPath()
              ctx.moveTo(leafBaseX, leafBaseY)
              ctx.quadraticCurveTo(
                leafBaseX + leafDir * leafLen * 0.6,
                leafBaseY - leafWidth + leafAngle * 10,
                leafBaseX + leafDir * leafLen,
                leafBaseY + leafAngle * 15
              )
              ctx.quadraticCurveTo(
                leafBaseX + leafDir * leafLen * 0.6,
                leafBaseY + leafWidth + leafAngle * 10,
                leafBaseX, leafBaseY
              )
              ctx.fill()
            }
          }

          prevSway = swayX
          curX = curX + swayX
          curY = topY
          ctx.lineWidth = thickness
        }
      }

      // 远景竹子（较细，较淡）
      ctx.globalAlpha = 0.15
      drawBambooStalk(w * 0.05, 5, 2, 5)
      drawBambooStalk(w * 0.95, 5, 1.8, 5)

      // 中景竹子（主体）
      ctx.globalAlpha = 0.22
      drawBambooStalk(w * 0.1, 6, 3, 8)
      drawBambooStalk(w * 0.18, 7, 2.8, 7)
      drawBambooStalk(w * 0.85, 6, 2.5, 7)
      drawBambooStalk(w * 0.92, 7, 3.2, 8)

      // ===== 前景层：近景竹 + 露珠 + 光线 =====
      // 近景竹子（更粗，更清晰）
      ctx.globalAlpha = 0.28
      drawBambooStalk(w * 0.02, 8, 4, 10)
      drawBambooStalk(w * 0.97, 8, 3.5, 10)

      // 晨光光线（从左上角斜射）
      const lightAngle = Math.PI * 0.25
      const lightX = w * 0.1
      const lightY = h * 0.1
      ctx.globalAlpha = 0.04
      for (let i = 0; i < 3; i++) {
        const rayWidth = 30 + i * 15
        const rayLen = h * 1.2
        const rayDrift = Math.sin(time * 0.0003 + i * 2) * 10

        ctx.save()
        ctx.translate(lightX + rayDrift, lightY)
        ctx.rotate(lightAngle + i * 0.05)

        const rayGrad = ctx.createLinearGradient(0, 0, 0, rayLen)
        rayGrad.addColorStop(0, 'rgba(255, 255, 240, 0.4)')
        rayGrad.addColorStop(0.5, 'rgba(255, 255, 240, 0.15)')
        rayGrad.addColorStop(1, 'rgba(255, 255, 240, 0)')
        ctx.fillStyle = rayGrad

        ctx.beginPath()
        ctx.moveTo(-rayWidth / 2, 0)
        ctx.lineTo(rayWidth / 2, 0)
        ctx.lineTo(rayWidth / 4, rayLen)
        ctx.lineTo(-rayWidth / 4, rayLen)
        ctx.closePath()
        ctx.fill()

        ctx.restore()
      }

      // 露珠（在竹叶上闪烁，有呼吸感）
      for (let i = 0; i < 12; i++) {
        const seed = i * 73.7 + 100
        const dx = (Math.sin(seed * 0.7) * 43758.5453 % 1) * w * 0.8 + w * 0.1
        const dy = (Math.cos(seed * 0.3) * 43758.5453 % 1) * h * 0.6 + h * 0.2
        const sparkle = Math.sin(time * 0.004 + i * 1.9) * 0.5 + 0.5

        // 露珠只在特定亮度时才可见（呼吸效果）
        if (sparkle > 0.6) {
          const intensity = (sparkle - 0.6) * 2.5

          // 露珠本体（小圆点）
          ctx.globalAlpha = intensity * 0.7
          ctx.fillStyle = '#ffffff'
          ctx.beginPath()
          ctx.arc(dx, dy, 1.5, 0, Math.PI * 2)
          ctx.fill()

          // 露珠光晕
          ctx.globalAlpha = intensity * 0.3
          const dewGlow = ctx.createRadialGradient(dx, dy, 0, dx, dy, 4)
          dewGlow.addColorStop(0, 'rgba(255, 255, 255, 0.6)')
          dewGlow.addColorStop(1, 'rgba(255, 255, 255, 0)')
          ctx.fillStyle = dewGlow
          ctx.beginPath()
          ctx.arc(dx, dy, 4, 0, Math.PI * 2)
          ctx.fill()

          // 十字光芒（只在最亮时出现）
          if (intensity > 0.8) {
            ctx.globalAlpha = (intensity - 0.8) * 2
            ctx.strokeStyle = '#ffffff'
            ctx.lineWidth = 0.5
            const rayLen = 3 + intensity * 2
            ctx.beginPath()
            ctx.moveTo(dx - rayLen, dy)
            ctx.lineTo(dx + rayLen, dy)
            ctx.moveTo(dx, dy - rayLen)
            ctx.lineTo(dx, dy + rayLen)
            ctx.stroke()
          }
        }
      }

      // 地面光斑（阳光透过竹叶的斑驳光影）
      ctx.globalAlpha = 0.03
      for (let i = 0; i < 6; i++) {
        const spotX = (Math.sin(i * 47.3) * 43758.5453 % 1) * w
        const adjSpotX = spotX < 0 ? spotX + w : spotX
        const spotY = h * 0.85 + (Math.cos(i * 23.7) * 43758.5453 % 1) * h * 0.1
        const spotR = 15 + Math.sin(time * 0.002 + i) * 5

        const spotGrad = ctx.createRadialGradient(adjSpotX, spotY, 0, adjSpotX, spotY, spotR)
        spotGrad.addColorStop(0, 'rgba(255, 255, 200, 0.4)')
        spotGrad.addColorStop(1, 'rgba(255, 255, 200, 0)')
        ctx.fillStyle = spotGrad
        ctx.beginPath()
        ctx.arc(adjSpotX, spotY, spotR, 0, Math.PI * 2)
        ctx.fill()
      }

      ctx.restore()
    }
  }),

  // ============ 北欧极夜 — 极光流动 + 雪粒飘落 + 小屋灯光 ============
  nordic_polar_night: () => {
    const snow = Array.from({ length: 120 }, () => ({
      x: Math.random(), y: Math.random(),
      vx: (Math.random() - 0.5) * 0.0003, vy: Math.random() * 0.0003 + 0.00015,
      s: Math.random() * 2.2 + 0.5, o: Math.random() * 0.5 + 0.3,
      wp: Math.random() * Math.PI * 2, wf: Math.random() * 0.015 + 0.005
    }))
    const cab = Array.from({ length: 7 }, () => ({
      x: Math.random(), y: 0.72 + Math.random() * 0.14,
      w: Math.random() * 0.015 + 0.006, h: Math.random() * 0.008 + 0.004,
      fo: Math.random() * Math.PI * 2, fs: Math.random() * 0.002 + 0.001
    }))
    return {
      bgColor: '#081530',
      bgGradient: 'linear-gradient(to bottom, #040b18 0%, #081530 30%, #0c1e3a 70%, #101825 100%)',
      textColor: '#c8d8e8',
      textSecondary: '#8a9ab0',
      textTertiary: '#5a6a80',
      borderColor: 'rgba(100, 160, 220, 0.15)',
      buttonBg: 'rgba(100, 160, 220, 0.1)',
      buttonText: '#c8d8e8',
      accentColor: '#ffa050',
      cardBg: 'rgba(10, 20, 40, 0.7)',
      backdropFilter: 'blur(10px)',
      boxShadow: '0 4px 20px rgba(0, 20, 60, 0.5)',
      renderCanvas: (ctx: CanvasRenderingContext2D, w: number, h: number, t: number) => {
        // L1: Sky
        const bg = ctx.createLinearGradient(0, 0, 0, h)
        bg.addColorStop(0, '#040b18'); bg.addColorStop(0.3, '#081530')
        bg.addColorStop(0.7, '#0c1e3a'); bg.addColorStop(1, '#101825')
        ctx.fillStyle = bg; ctx.fillRect(0, 0, w, h)

        // L2: Stars
        for (let i = 0; i < 55; i++) {
          const sx = (i * 137.508 + 50) % w, sy = (i * 73.137 + 20) % (h * 0.4)
          const sb = (Math.sin(t * 0.0004 + i * 1.7) + 1) * 0.5
          ctx.beginPath(); ctx.arc(sx, sy, 0.4 + sb * 0.7, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(200,220,255,${0.1 + sb * 0.3})`; ctx.fill()
        }

        // L3: Aurora (4 bands, multi-frequency organic flow)
        ctx.save(); ctx.globalCompositeOperation = 'screen'
        const bands = [
          { y: 0.14, wd: 0.11, hu: 150, sp: 0.00025, am: 35, ph: 0 },
          { y: 0.21, wd: 0.09, hu: 180, sp: 0.00018, am: 45, ph: 2.1 },
          { y: 0.27, wd: 0.07, hu: 280, sp: 0.00032, am: 25, ph: 4.3 },
          { y: 0.17, wd: 0.05, hu: 120, sp: 0.00015, am: 50, ph: 1.2 },
        ]
        for (const b of bands) {
          const by = h * b.y
          for (let x = 0; x < w; x += 3) {
            const wave = Math.sin(x * 0.003 + t * b.sp + b.ph) * b.am
              + Math.sin(x * 0.007 + t * b.sp * 1.3 + b.ph * 0.5) * b.am * 0.4
              + Math.sin(x * 0.001 + t * b.sp * 0.7) * b.am * 0.6
            const cy = by + wave
            const inten = (Math.sin(x * 0.002 + t * b.sp * 0.5 + b.ph) + 1) * 0.5
            const r = h * b.wd
            const grad = ctx.createRadialGradient(x, cy, 0, x, cy, r)
            grad.addColorStop(0, `hsla(${b.hu},80%,60%,${0.07 * inten})`)
            grad.addColorStop(0.5, `hsla(${b.hu},70%,50%,${0.03 * inten})`)
            grad.addColorStop(1, 'hsla(180,60%,40%,0)')
            ctx.fillStyle = grad
            ctx.fillRect(x - r, cy - r, r * 2, r * 2)
          }
        }
        ctx.restore()

        // L4: Snow (wind + wobble physics)
        const windF = Math.sin(t * 0.0003) * 0.00005
        for (const p of snow) {
          p.wp += p.wf; p.vx += windF
          p.vx += Math.sin(p.wp) * 0.000008; p.vx *= 0.99
          p.x += p.vx; p.y += p.vy
          if (p.y > 1.02) { p.y = -0.02; p.x = Math.random() }
          if (p.x > 1.02) p.x = -0.02; if (p.x < -0.02) p.x = 1.02
          const px = p.x * w, py = p.y * h
          if (p.s > 1.5) {
            ctx.beginPath(); ctx.arc(px, py, p.s * 2, 0, Math.PI * 2)
            ctx.fillStyle = `rgba(200,220,255,${p.o * 0.08})`; ctx.fill()
          }
          ctx.beginPath(); ctx.arc(px, py, p.s, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(230,240,255,${p.o})`; ctx.fill()
        }

        // L5: Mountains (3 layers, atmospheric perspective)
        const mts = [
          { y: 0.68, c: 'rgba(8,16,32,0.9)', f: 0.002, a: 55 },
          { y: 0.75, c: 'rgba(12,20,38,0.95)', f: 0.003, a: 40 },
          { y: 0.82, c: 'rgba(16,24,42,1)', f: 0.005, a: 28 },
        ]
        for (const m of mts) {
          ctx.beginPath(); ctx.moveTo(0, h)
          for (let x = 0; x <= w; x += 3) {
            ctx.lineTo(x, h * m.y + Math.sin(x * m.f) * m.a + Math.sin(x * m.f * 2.3 + 1) * m.a * 0.5)
          }
          ctx.lineTo(w, h); ctx.closePath(); ctx.fillStyle = m.c; ctx.fill()
        }

        // L6: Snow ground
        const gnd = ctx.createLinearGradient(0, h * 0.88, 0, h)
        gnd.addColorStop(0, '#1a2540'); gnd.addColorStop(0.5, '#253050'); gnd.addColorStop(1, '#2a3558')
        ctx.fillStyle = gnd; ctx.fillRect(0, h * 0.88, w, h * 0.12)

        // L7: Cabin lights (warm flicker)
        for (const c of cab) {
          const fl = (Math.sin(t * c.fs + c.fo) + 1) * 0.5
            * (Math.sin(t * c.fs * 2.7 + c.fo * 1.5) + 1) * 0.5
          const warm = 0.4 + fl * 0.6
          const cx = c.x * w, cy = c.y * h, cw = c.w * w
          const wg = ctx.createRadialGradient(cx, cy, 0, cx, cy, cw * 4)
          wg.addColorStop(0, `rgba(255,180,80,${0.3 * warm})`)
          wg.addColorStop(0.5, `rgba(255,150,50,${0.12 * warm})`)
          wg.addColorStop(1, 'rgba(255,150,50,0)')
          ctx.fillStyle = wg; ctx.fillRect(cx - cw * 4, cy - cw * 4, cw * 8, cw * 8)
          ctx.fillStyle = `rgba(255,200,120,${warm})`
          ctx.fillRect(cx - cw / 2, cy - c.h * h / 2, cw, c.h * h)
        }

        // L8: Title glow
        ctx.save(); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
        ctx.font = `bold ${Math.min(36, w * 0.03)}px "PingFang SC","Microsoft YaHei",sans-serif`
        ctx.shadowColor = 'rgba(100,200,255,0.3)'; ctx.shadowBlur = 20
        ctx.fillStyle = 'rgba(180,210,240,0.12)'; ctx.fillText('北欧极夜', w / 2, h / 2)
        ctx.shadowBlur = 0; ctx.restore()

        // L9: Vignette
        const vig = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.3, w / 2, h / 2, Math.max(w, h) * 0.7)
        vig.addColorStop(0, 'rgba(0,0,0,0)'); vig.addColorStop(1, 'rgba(0,0,0,0.5)')
        ctx.fillStyle = vig; ctx.fillRect(0, 0, w, h)
      }
    }
  },


  // ============ 日式庭院 — 枯山水 + 樱花 + 灯笼 ============
  japanese_garden: () => {
    const petals = Array.from({ length: 50 }, () => ({
      x: Math.random(), y: Math.random(),
      vx: (Math.random() - 0.3) * 0.0002, vy: Math.random() * 0.0002 + 0.00008,
      rot: Math.random() * Math.PI * 2, rv: (Math.random() - 0.5) * 0.02,
      s: Math.random() * 4 + 2, o: Math.random() * 0.5 + 0.3,
      hue: Math.random() * 20 + 340, wp: Math.random() * Math.PI * 2
    }))
    const stones = [
      { x: 0.3, y: 0.55, r: 25 }, { x: 0.55, y: 0.48, r: 18 },
      { x: 0.7, y: 0.58, r: 30 }, { x: 0.45, y: 0.62, r: 15 },
    ]
    const lanterns = [
      { x: 0.2, y: 0.4, fo: 0 }, { x: 0.8, y: 0.35, fo: 2.5 },
    ]
    return {
      bgColor: '#f5f0e6',
      bgGradient: 'linear-gradient(to bottom, #f5f0e6 0%, #ebe5d5 50%, #e0d8c8 100%)',
      textColor: '#3a3530',
      textSecondary: '#6b6055',
      textTertiary: '#9a8e80',
      borderColor: 'rgba(90, 75, 60, 0.15)',
      buttonBg: 'rgba(90, 75, 60, 0.08)',
      buttonText: '#3a3530',
      accentColor: '#c47070',
      cardBg: 'rgba(245, 240, 230, 0.8)',
      backdropFilter: 'blur(5px)',
      boxShadow: '0 2px 12px rgba(90, 75, 60, 0.12)',
      renderCanvas: (ctx: CanvasRenderingContext2D, w: number, h: number, t: number) => {
        // L1: Paper background with warm gradient
        const bg = ctx.createLinearGradient(0, 0, 0, h)
        bg.addColorStop(0, '#f5f0e6'); bg.addColorStop(0.5, '#ebe5d5')
        bg.addColorStop(1, '#ddd5c5')
        ctx.fillStyle = bg; ctx.fillRect(0, 0, w, h)

        // L2: Paper texture (subtle noise dots)
        ctx.fillStyle = 'rgba(160,140,120,0.03)'
        for (let i = 0; i < 200; i++) {
          const tx = (i * 197.3 + 30) % w, ty = (i * 113.7 + 50) % h
          ctx.fillRect(tx, ty, 1, 1)
        }

        // L3: Zen garden sand area
        const sandY = h * 0.45, sandH = h * 0.45
        ctx.fillStyle = '#e8e0d0'
        ctx.fillRect(0, sandY, w, sandH)
        // Raked lines (horizontal)
        ctx.strokeStyle = 'rgba(180,170,155,0.25)'; ctx.lineWidth = 0.8
        for (let dy = 0; dy < sandH; dy += 6) {
          ctx.beginPath(); ctx.moveTo(0, sandY + dy)
          for (let x = 0; x < w; x += 4) {
            const ripple = Math.sin(x * 0.02 + dy * 0.1) * 0.5
            ctx.lineTo(x, sandY + dy + ripple)
          }
          ctx.stroke()
        }
        // Concentric circles around stones
        ctx.strokeStyle = 'rgba(170,160,140,0.2)'; ctx.lineWidth = 0.6
        for (const st of stones) {
          const sx = st.x * w, sy = sandY + st.y * sandH * 0.4 + sandH * 0.2
          for (let r = st.r + 5; r < st.r + 40; r += 5) {
            ctx.beginPath(); ctx.arc(sx, sy, r, 0, Math.PI * 2); ctx.stroke()
          }
          // Stone itself
          const sg = ctx.createRadialGradient(sx - 3, sy - 3, 0, sx, sy, st.r)
          sg.addColorStop(0, '#8a8070'); sg.addColorStop(0.7, '#6a6050')
          sg.addColorStop(1, '#5a5040')
          ctx.fillStyle = sg; ctx.beginPath()
          ctx.ellipse(sx, sy, st.r, st.r * 0.7, 0, 0, Math.PI * 2); ctx.fill()
        }

        // L4: Moss patches
        const mosses = [
          { x: 0.1, y: 0.42, r: 30 }, { x: 0.9, y: 0.45, r: 25 },
          { x: 0.15, y: 0.88, r: 35 }, { x: 0.85, y: 0.9, r: 28 },
          { x: 0.5, y: 0.92, r: 20 },
        ]
        for (const m of mosses) {
          const mx = m.x * w, my = m.y * h
          const mg = ctx.createRadialGradient(mx, my, 0, mx, my, m.r)
          mg.addColorStop(0, 'rgba(100,130,80,0.5)')
          mg.addColorStop(0.6, 'rgba(110,140,85,0.3)')
          mg.addColorStop(1, 'rgba(120,150,90,0)')
          ctx.fillStyle = mg; ctx.beginPath()
          ctx.ellipse(mx, my, m.r * 1.3, m.r * 0.8, 0, 0, Math.PI * 2); ctx.fill()
        }

        // L5: Paper lanterns (warm glow with flicker)
        for (const ln of lanterns) {
          const lx = ln.x * w, ly = ln.y * h
          const fl = (Math.sin(t * 0.002 + ln.fo) + 1) * 0.5
            * (Math.sin(t * 0.005 + ln.fo * 1.3) + 1) * 0.5
          const glow = 0.5 + fl * 0.5
          // Outer glow
          const lg = ctx.createRadialGradient(lx, ly, 0, lx, ly, 80)
          lg.addColorStop(0, `rgba(255,200,120,${0.2 * glow})`)
          lg.addColorStop(0.4, `rgba(255,180,100,${0.08 * glow})`)
          lg.addColorStop(1, 'rgba(255,180,100,0)')
          ctx.fillStyle = lg; ctx.fillRect(lx - 80, ly - 80, 160, 160)
          // Lantern body
          ctx.fillStyle = `rgba(240,220,180,${0.7 + glow * 0.3})`
          ctx.beginPath()
          ctx.ellipse(lx, ly, 12, 18, 0, 0, Math.PI * 2); ctx.fill()
          ctx.strokeStyle = 'rgba(120,80,40,0.5)'; ctx.lineWidth = 1
          ctx.stroke()
          // Lantern top/bottom caps
          ctx.fillStyle = 'rgba(100,70,40,0.6)'
          ctx.fillRect(lx - 8, ly - 20, 16, 4)
          ctx.fillRect(lx - 6, ly + 16, 12, 3)
          // Post
          ctx.fillStyle = 'rgba(100,70,40,0.4)'
          ctx.fillRect(lx - 2, ly + 18, 4, 40)
        }

        // L6: Cherry blossom petals (falling with drift + rotation)
        for (const p of petals) {
          p.wp += 0.012
          p.vx += Math.sin(p.wp) * 0.000005
          p.x += p.vx + Math.sin(t * 0.0002) * 0.00003
          p.y += p.vy; p.rot += p.rv
          if (p.y > 1.05) { p.y = -0.05; p.x = Math.random() }
          if (p.x > 1.1) p.x = -0.1; if (p.x < -0.1) p.x = 1.1
          const px = p.x * w, py = p.y * h
          ctx.save(); ctx.translate(px, py); ctx.rotate(p.rot)
          ctx.globalAlpha = p.o
          // Petal shape
          ctx.fillStyle = `hsl(${p.hue},60%,82%)`
          ctx.beginPath()
          ctx.ellipse(0, 0, p.s * 0.5, p.s, 0, 0, Math.PI * 2)
          ctx.fill()
          // Highlight
          ctx.fillStyle = `hsl(${p.hue},50%,90%)`
          ctx.beginPath()
          ctx.ellipse(-p.s * 0.15, -p.s * 0.2, p.s * 0.2, p.s * 0.4, 0, 0, Math.PI * 2)
          ctx.fill()
          ctx.restore()
        }

        // L7: Branch silhouettes
        ctx.strokeStyle = 'rgba(80,60,40,0.15)'; ctx.lineWidth = 2
        ctx.beginPath(); ctx.moveTo(0, h * 0.15)
        ctx.bezierCurveTo(w * 0.2, h * 0.12, w * 0.3, h * 0.18, w * 0.4, h * 0.08)
        ctx.stroke()
        ctx.beginPath(); ctx.moveTo(w, h * 0.1)
        ctx.bezierCurveTo(w * 0.8, h * 0.14, w * 0.7, h * 0.06, w * 0.6, h * 0.12)
        ctx.stroke()

        // L8: Title
        ctx.save(); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
        ctx.font = `${Math.min(32, w * 0.028)}px "PingFang SC","Microsoft YaHei",serif`
        ctx.fillStyle = 'rgba(60,50,40,0.08)'; ctx.fillText('日式庭院', w / 2, h / 2)
        ctx.restore()

        // L9: Soft vignette
        const vig = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.35, w / 2, h / 2, Math.max(w, h) * 0.65)
        vig.addColorStop(0, 'rgba(0,0,0,0)'); vig.addColorStop(1, 'rgba(60,50,30,0.15)')
        ctx.fillStyle = vig; ctx.fillRect(0, 0, w, h)
      }
    }
  },


  // ============ 维多利亚书房 — 壁炉 + 光束尘埃 + 书页 ============
  victorian_study: () => {
    const embers = Array.from({ length: 80 }, () => ({
      x: 0.25 + (Math.random() - 0.5) * 0.12, y: 0.85 + Math.random() * 0.1,
      vx: (Math.random() - 0.5) * 0.0002, vy: -(Math.random() * 0.0004 + 0.0001),
      s: Math.random() * 2.5 + 0.5, life: Math.random(),
      decay: Math.random() * 0.003 + 0.001, hue: Math.random() * 30 + 15
    }))
    const dust = Array.from({ length: 50 }, () => ({
      x: 0.45 + Math.random() * 0.35, y: Math.random(),
      vx: (Math.random() - 0.5) * 0.00005, vy: (Math.random() - 0.5) * 0.00004,
      s: Math.random() * 1.5 + 0.3, o: Math.random() * 0.4 + 0.1,
      phase: Math.random() * Math.PI * 2
    }))
    const pages = Array.from({ length: 5 }, () => ({
      x: 0.2 + Math.random() * 0.15, y: 0.7 + Math.random() * 0.15,
      vx: Math.random() * 0.0002 + 0.0001, vy: -(Math.random() * 0.0003 + 0.0001),
      rot: Math.random() * Math.PI * 2, rv: (Math.random() - 0.5) * 0.008,
      s: Math.random() * 8 + 6, o: Math.random() * 0.3 + 0.15
    }))
    const bookColors = ['#5c1a1a', '#2a3a2a', '#1a2a3a', '#3a2a1a', '#3a1a2a', '#1a3a2a', '#4a3a1a', '#2a1a3a']
    return {
      bgColor: '#2a1510',
      bgGradient: 'linear-gradient(to bottom, #1a0e08 0%, #2a1510 40%, #3a2218 70%, #1a0e08 100%)',
      textColor: '#d4c4a8',
      textSecondary: '#a89878',
      textTertiary: '#7a6a50',
      borderColor: 'rgba(180, 140, 80, 0.15)',
      buttonBg: 'rgba(180, 140, 80, 0.1)',
      buttonText: '#d4c4a8',
      accentColor: '#c8a050',
      cardBg: 'rgba(40, 20, 12, 0.8)',
      backdropFilter: 'blur(8px)',
      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
      renderCanvas: (ctx: CanvasRenderingContext2D, w: number, h: number, t: number) => {
        // L1: Background
        const bg = ctx.createLinearGradient(0, 0, 0, h)
        bg.addColorStop(0, '#1a0e08'); bg.addColorStop(0.4, '#2a1510')
        bg.addColorStop(0.7, '#3a2218'); bg.addColorStop(1, '#1a0e08')
        ctx.fillStyle = bg; ctx.fillRect(0, 0, w, h)

        // L2: Wall paneling (subtle vertical lines)
        ctx.strokeStyle = 'rgba(60,40,25,0.3)'; ctx.lineWidth = 1
        for (let x = w * 0.05; x < w; x += w * 0.12) {
          ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h * 0.85); ctx.stroke()
        }

        // L3: Window light beam
        const beamAlpha = 0.06 + Math.sin(t * 0.0005) * 0.015
        ctx.save()
        const beamGrad = ctx.createLinearGradient(w * 0.75, 0, w * 0.35, h)
        beamGrad.addColorStop(0, `rgba(255,220,150,${beamAlpha * 1.5})`)
        beamGrad.addColorStop(0.5, `rgba(255,200,120,${beamAlpha})`)
        beamGrad.addColorStop(1, `rgba(255,180,100,${beamAlpha * 0.3})`)
        ctx.fillStyle = beamGrad
        ctx.beginPath()
        ctx.moveTo(w * 0.7, 0); ctx.lineTo(w * 0.85, 0)
        ctx.lineTo(w * 0.55, h); ctx.lineTo(w * 0.3, h)
        ctx.closePath(); ctx.fill()
        ctx.restore()

        // L4: Dust in light beam
        for (const d of dust) {
          d.phase += 0.008
          d.x += d.vx + Math.sin(d.phase) * 0.00002
          d.y += d.vy + Math.cos(d.phase * 0.7) * 0.000015
          // Wrap in beam area
          if (d.x < 0.3) d.x = 0.8; if (d.x > 0.85) d.x = 0.35
          if (d.y < -0.02) d.y = 1.02; if (d.y > 1.02) d.y = -0.02
          const dx = d.x * w, dy = d.y * h
          // Check if in beam (approximate)
          const beamX = 0.7 - (d.y * 0.3)
          const inBeam = d.x > beamX - 0.1 && d.x < beamX + 0.15
          const bright = inBeam ? 1 : 0.15
          ctx.beginPath(); ctx.arc(dx, dy, d.s, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(255,220,160,${d.o * bright})`; ctx.fill()
        }

        // L5: Bookshelf (left side)
        const shelfX = w * 0.02, shelfW = w * 0.1
        ctx.fillStyle = 'rgba(50,30,18,0.8)'
        ctx.fillRect(shelfX, h * 0.05, shelfW, h * 0.75)
        // Shelves
        for (let sy = 0.05; sy < 0.8; sy += 0.12) {
          ctx.fillStyle = 'rgba(70,40,25,0.9)'
          ctx.fillRect(shelfX - 2, h * sy, shelfW + 4, 3)
          // Books on shelf
          let bx = shelfX + 3
          for (let bi = 0; bi < 6 && bx < shelfX + shelfW - 3; bi++) {
            const seed = bi * 7 + Math.floor(sy * 10) * 13
            const bw = 4 + ((seed * 31) % 7)
            const bh = h * 0.09 + ((seed * 17) % 10) * h * 0.002
            ctx.fillStyle = bookColors[(bi + Math.floor(sy * 10)) % bookColors.length]
            ctx.fillRect(bx, h * sy - bh + 3, bw, bh)
            bx += bw + 1
          }
        }

        // L6: Fireplace
        const fpX = w * 0.22, fpY = h * 0.82, fpW = w * 0.18, fpH = h * 0.18
        // Mantel
        ctx.fillStyle = 'rgba(60,35,20,0.9)'
        ctx.fillRect(fpX - 10, fpY - 5, fpW + 20, 8)
        // Fireplace opening
        ctx.fillStyle = '#0a0503'
        ctx.beginPath()
        ctx.moveTo(fpX, fpY + fpH); ctx.lineTo(fpX, fpY + 10)
        ctx.quadraticCurveTo(fpX + fpW / 2, fpY - 5, fpX + fpW, fpY + 10)
        ctx.lineTo(fpX + fpW, fpY + fpH); ctx.closePath(); ctx.fill()
        // Fire glow
        const flicker = 0.7 + Math.sin(t * 0.008) * 0.15 + Math.sin(t * 0.013) * 0.1
        const fg = ctx.createRadialGradient(fpX + fpW / 2, fpY + fpH * 0.6, 0, fpX + fpW / 2, fpY + fpH * 0.6, fpW * 0.8)
        fg.addColorStop(0, `rgba(255,150,50,${0.3 * flicker})`)
        fg.addColorStop(0.4, `rgba(255,100,30,${0.15 * flicker})`)
        fg.addColorStop(1, 'rgba(255,80,20,0)')
        ctx.fillStyle = fg; ctx.fillRect(fpX - fpW * 0.3, fpY, fpW * 1.6, fpH)
        // Flame tongues
        for (let fi = 0; fi < 5; fi++) {
          const fx = fpX + fpW * (0.15 + fi * 0.17)
          const fBase = fpY + fpH * 0.8
          const fH = fpH * (0.3 + Math.sin(t * 0.01 + fi * 1.5) * 0.15)
          const fGrad = ctx.createLinearGradient(fx, fBase, fx, fBase - fH)
          fGrad.addColorStop(0, `rgba(255,200,80,${0.6 * flicker})`)
          fGrad.addColorStop(0.4, `rgba(255,120,30,${0.4 * flicker})`)
          fGrad.addColorStop(1, 'rgba(255,60,10,0)')
          ctx.fillStyle = fGrad
          ctx.beginPath()
          ctx.moveTo(fx - 6, fBase)
          ctx.quadraticCurveTo(fx + Math.sin(t * 0.012 + fi) * 4, fBase - fH * 0.6, fx, fBase - fH)
          ctx.quadraticCurveTo(fx + 4 + Math.sin(t * 0.009 + fi) * 3, fBase - fH * 0.4, fx + 6, fBase)
          ctx.closePath(); ctx.fill()
        }

        // L7: Embers rising from fire
        for (const e of embers) {
          e.life -= e.decay
          if (e.life <= 0) {
            e.x = 0.25 + (Math.random() - 0.5) * 0.12; e.y = 0.85 + Math.random() * 0.05
            e.life = 1; e.vy = -(Math.random() * 0.0004 + 0.0001)
          }
          e.x += e.vx + Math.sin(t * 0.003 + e.hue) * 0.00003
          e.y += e.vy
          const ex = e.x * w, ey = e.y * h
          ctx.beginPath(); ctx.arc(ex, ey, e.s * e.life, 0, Math.PI * 2)
          ctx.fillStyle = `hsla(${e.hue},100%,${50 + e.life * 30}%,${e.life * 0.6})`
          ctx.fill()
        }

        // L8: Floating pages
        for (const p of pages) {
          p.x += p.vx; p.y += p.vy; p.rot += p.rv
          p.vy -= 0.0000003 // slight upward acceleration (heat)
          if (p.y < -0.1 || p.x > 1.1) {
            p.x = 0.22 + Math.random() * 0.1; p.y = 0.78 + Math.random() * 0.05
            p.vy = -(Math.random() * 0.0003 + 0.0001); p.vx = Math.random() * 0.0002 + 0.0001
          }
          const px = p.x * w, py = p.y * h
          ctx.save(); ctx.translate(px, py); ctx.rotate(p.rot)
          ctx.globalAlpha = p.o
          ctx.fillStyle = '#f0e8d8'
          ctx.fillRect(-p.s / 2, -p.s * 0.7, p.s, p.s * 1.4)
          // Text lines on page
          ctx.fillStyle = 'rgba(60,50,40,0.2)'
          for (let li = 0; li < 4; li++) {
            ctx.fillRect(-p.s / 2 + 2, -p.s * 0.5 + li * p.s * 0.3, p.s - 4, 1)
          }
          ctx.restore()
        }

        // L9: Title
        ctx.save(); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
        ctx.font = `bold ${Math.min(32, w * 0.028)}px "Georgia","Times New Roman",serif`
        ctx.fillStyle = 'rgba(200,170,120,0.1)'; ctx.fillText('维多利亚书房', w / 2, h / 2)
        ctx.restore()

        // L10: Heavy vignette
        const vig = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.25, w / 2, h / 2, Math.max(w, h) * 0.65)
        vig.addColorStop(0, 'rgba(0,0,0,0)'); vig.addColorStop(1, 'rgba(10,5,2,0.6)')
        ctx.fillStyle = vig; ctx.fillRect(0, 0, w, h)
      }
    }
  },


  // ============ 海底神殿 — 光线 + 气泡 + 水草 + 鱼群 ============
  underwater_temple: () => {
    const bubbles = Array.from({ length: 40 }, () => ({
      x: Math.random(), y: Math.random(),
      r: Math.random() * 4 + 1.5, vy: -(Math.random() * 0.0003 + 0.0001),
      wp: Math.random() * Math.PI * 2, wa: Math.random() * 0.00015 + 0.00005,
      o: Math.random() * 0.4 + 0.15
    }))
    const seaweed = Array.from({ length: 8 }, () => ({
      x: Math.random() * 0.9 + 0.05, h: Math.random() * 0.15 + 0.08,
      seg: Math.floor(Math.random() * 4) + 5,
      phase: Math.random() * Math.PI * 2, speed: Math.random() * 0.001 + 0.0005,
      amp: Math.random() * 8 + 5, hue: 130 + Math.random() * 30
    }))
    const fish = Array.from({ length: 15 }, (_, i) => ({
      ox: (Math.random() - 0.5) * 0.08, oy: (Math.random() - 0.5) * 0.04,
      s: Math.random() * 5 + 4, phase: i * 0.5,
      hue: Math.random() > 0.7 ? 35 : (Math.random() * 20 + 190)
    }))
    const particles = Array.from({ length: 60 }, () => ({
      x: Math.random(), y: Math.random(),
      vx: (Math.random() - 0.5) * 0.00003, vy: (Math.random() - 0.5) * 0.00003,
      s: Math.random() * 1.2 + 0.3, o: Math.random() * 0.25 + 0.05
    }))
    return {
      bgColor: '#0a2a2a',
      bgGradient: 'linear-gradient(to bottom, #083838 0%, #0a2a2a 40%, #0a1a20 70%, #061218 100%)',
      textColor: '#a0d8d0',
      textSecondary: '#70a8a0',
      textTertiary: '#508078',
      borderColor: 'rgba(80, 200, 180, 0.15)',
      buttonBg: 'rgba(80, 200, 180, 0.08)',
      buttonText: '#a0d8d0',
      accentColor: '#e8a090',
      cardBg: 'rgba(10, 30, 35, 0.8)',
      backdropFilter: 'blur(8px)',
      boxShadow: '0 4px 20px rgba(0, 30, 40, 0.5)',
      renderCanvas: (ctx: CanvasRenderingContext2D, w: number, h: number, t: number) => {
        // L1: Deep ocean gradient
        const bg = ctx.createLinearGradient(0, 0, 0, h)
        bg.addColorStop(0, '#0c3a3a'); bg.addColorStop(0.3, '#0a2a2a')
        bg.addColorStop(0.7, '#0a1a20'); bg.addColorStop(1, '#061218')
        ctx.fillStyle = bg; ctx.fillRect(0, 0, w, h)

        // L2: Caustics (animated light patterns on the floor)
        ctx.save(); ctx.globalAlpha = 0.04; ctx.globalCompositeOperation = 'screen'
        for (let i = 0; i < 12; i++) {
          const cx = (i * w / 12 + Math.sin(t * 0.0003 + i) * 40) % w
          const cy = h * 0.8 + Math.cos(t * 0.0004 + i * 2) * 20
          const cr = 40 + Math.sin(t * 0.0005 + i * 1.5) * 15
          const cg = ctx.createRadialGradient(cx, cy, 0, cx, cy, cr)
          cg.addColorStop(0, 'rgba(150,220,200,0.5)'); cg.addColorStop(1, 'rgba(150,220,200,0)')
          ctx.fillStyle = cg; ctx.fillRect(cx - cr, cy - cr, cr * 2, cr * 2)
        }
        ctx.restore()

        // L3: God rays from surface
        ctx.save(); ctx.globalCompositeOperation = 'screen'
        const rays = [
          { x: 0.2, w: 0.08, a: 0.04, sp: 0.0002, ph: 0 },
          { x: 0.5, w: 0.1, a: 0.05, sp: 0.00015, ph: 1.5 },
          { x: 0.75, w: 0.07, a: 0.035, sp: 0.00025, ph: 3 },
        ]
        for (const r of rays) {
          const sway = Math.sin(t * r.sp + r.ph) * 0.03
          const alpha = r.a * (0.7 + Math.sin(t * r.sp * 2 + r.ph) * 0.3)
          const rx = (r.x + sway) * w, rw = r.w * w
          const rg = ctx.createLinearGradient(rx, 0, rx + rw * 0.5, h * 0.8)
          rg.addColorStop(0, `rgba(150,220,200,${alpha})`)
          rg.addColorStop(0.5, `rgba(120,200,180,${alpha * 0.5})`)
          rg.addColorStop(1, 'rgba(100,180,160,0)')
          ctx.fillStyle = rg
          ctx.beginPath()
          ctx.moveTo(rx - rw / 2, 0); ctx.lineTo(rx + rw / 2, 0)
          ctx.lineTo(rx + rw, h * 0.8); ctx.lineTo(rx - rw * 0.3, h * 0.8)
          ctx.closePath(); ctx.fill()
        }
        ctx.restore()

        // L4: Temple columns at bottom
        const colY = h * 0.85
        const cols = [0.15, 0.35, 0.55, 0.75, 0.9]
        for (const cx of cols) {
          const px = cx * w
          const colGrad = ctx.createLinearGradient(px - 12, colY, px + 12, colY)
          colGrad.addColorStop(0, 'rgba(60,80,75,0.5)')
          colGrad.addColorStop(0.5, 'rgba(80,100,90,0.6)')
          colGrad.addColorStop(1, 'rgba(50,70,65,0.4)')
          ctx.fillStyle = colGrad
          ctx.fillRect(px - 12, colY, 24, h - colY)
          // Column capital
          ctx.fillStyle = 'rgba(70,90,80,0.5)'
          ctx.fillRect(px - 16, colY - 4, 32, 8)
          // Cracks/aging
          ctx.strokeStyle = 'rgba(40,60,55,0.3)'; ctx.lineWidth = 0.5
          ctx.beginPath(); ctx.moveTo(px - 3, colY + 10); ctx.lineTo(px + 2, colY + 30); ctx.stroke()
        }
        // Floor
        const floorGrad = ctx.createLinearGradient(0, h * 0.95, 0, h)
        floorGrad.addColorStop(0, 'rgba(40,60,55,0.3)')
        floorGrad.addColorStop(1, 'rgba(180,160,100,0.15)')
        ctx.fillStyle = floorGrad; ctx.fillRect(0, h * 0.95, w, h * 0.05)

        // L5: Seaweed (multi-segment swaying)
        for (const sw of seaweed) {
          const baseX = sw.x * w, baseY = h * 0.95
          const segH = (sw.h * h) / sw.seg
          let px = baseX, py = baseY
          ctx.beginPath(); ctx.moveTo(px, py)
          for (let si = 0; si < sw.seg; si++) {
            const sway = Math.sin(t * sw.speed + sw.phase + si * 0.4) * sw.amp * (si / sw.seg)
            px = baseX + sway; py = baseY - (si + 1) * segH
            ctx.lineTo(px, py)
          }
          ctx.strokeStyle = `hsla(${sw.hue},50%,35%,0.6)`; ctx.lineWidth = 3; ctx.stroke()
          // Leaf blobs
          for (let si = 1; si < sw.seg; si += 2) {
            const sway = Math.sin(t * sw.speed + sw.phase + si * 0.4) * sw.amp * (si / sw.seg)
            const lx = baseX + sway, ly = baseY - si * segH
            ctx.beginPath(); ctx.ellipse(lx + 5, ly, 4, 2, 0.3, 0, Math.PI * 2)
            ctx.fillStyle = `hsla(${sw.hue},45%,40%,0.4)`; ctx.fill()
          }
        }

        // L6: Bubbles (rising with wobble)
        for (const b of bubbles) {
          b.wp += 0.015; b.y += b.vy
          b.x += Math.sin(b.wp) * b.wa
          if (b.y < -0.03) { b.y = 1.03; b.x = Math.random() }
          const bx = b.x * w, by = b.y * h
          // Highlight
          ctx.beginPath(); ctx.arc(bx, by, b.r, 0, Math.PI * 2)
          ctx.strokeStyle = `rgba(180,230,220,${b.o})`; ctx.lineWidth = 0.8; ctx.stroke()
          ctx.beginPath(); ctx.arc(bx - b.r * 0.25, by - b.r * 0.25, b.r * 0.3, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(220,250,240,${b.o * 0.5})`; ctx.fill()
        }

        // L7: Fish school (boid-like, following a leader path)
        const schoolX = (Math.sin(t * 0.0002) * 0.3 + 0.5) * w
        const schoolY = h * 0.35 + Math.sin(t * 0.00015) * h * 0.1
        const dirX = Math.cos(t * 0.0002) * 0.3
        const dirY = Math.sin(t * 0.00015) * 0.1
        for (const f of fish) {
          const fx = schoolX + f.ox * w + Math.sin(t * 0.001 + f.phase) * 10
          const fy = schoolY + f.oy * h + Math.cos(t * 0.0012 + f.phase) * 6
          const angle = Math.atan2(dirY, dirX)
          ctx.save(); ctx.translate(fx, fy)
          if (dirX < 0) ctx.scale(-1, 1) // flip direction
          ctx.rotate(angle * 0.3)
          // Fish body
          ctx.fillStyle = `hsla(${f.hue},60%,55%,0.6)`
          ctx.beginPath(); ctx.ellipse(0, 0, f.s, f.s * 0.4, 0, 0, Math.PI * 2); ctx.fill()
          // Tail
          ctx.beginPath(); ctx.moveTo(-f.s, 0)
          ctx.lineTo(-f.s * 1.5, -f.s * 0.35)
          ctx.lineTo(-f.s * 1.5, f.s * 0.35); ctx.closePath(); ctx.fill()
          // Eye
          ctx.fillStyle = 'rgba(255,255,255,0.7)'
          ctx.beginPath(); ctx.arc(f.s * 0.4, -f.s * 0.1, f.s * 0.12, 0, Math.PI * 2); ctx.fill()
          ctx.restore()
        }

        // L8: Floating plankton particles
        for (const p of particles) {
          p.x += p.vx; p.y += p.vy
          if (p.x < 0) p.x = 1; if (p.x > 1) p.x = 0
          if (p.y < 0) p.y = 1; if (p.y > 1) p.y = 0
          const px = p.x * w, py = p.y * h
          ctx.beginPath(); ctx.arc(px, py, p.s, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(160,220,200,${p.o})`; ctx.fill()
        }

        // L9: Title
        ctx.save(); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
        ctx.font = `bold ${Math.min(36, w * 0.03)}px "PingFang SC","Microsoft YaHei",sans-serif`
        ctx.shadowColor = 'rgba(100,200,180,0.3)'; ctx.shadowBlur = 15
        ctx.fillStyle = 'rgba(160,216,208,0.1)'; ctx.fillText('海底神殿', w / 2, h / 2)
        ctx.shadowBlur = 0; ctx.restore()

        // L10: Underwater fog vignette
        const vig = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.25, w / 2, h / 2, Math.max(w, h) * 0.65)
        vig.addColorStop(0, 'rgba(0,0,0,0)'); vig.addColorStop(1, 'rgba(6,18,24,0.55)')
        ctx.fillStyle = vig; ctx.fillRect(0, 0, w, h)
      }
    }
  },

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
    { type: 'midnight_library', name: '午夜图书馆', description: '烛光书香，温暖静谧', preview: '#2c1810' },
    { type: 'star_voyage', name: '星际航行', description: '星海遨游，星云流转', preview: '#0d0d3a' },
    { type: 'rainy_city', name: '雨夜城市', description: '霓虹倒影，雨声淅沥', preview: '#111828' },
    { type: 'desert_dusk', name: '沙漠黄昏', description: '落日余晖，大漠孤烟', preview: '#5a1a3a' },
    { type: 'bamboo_dawn', name: '竹林清晨', description: '晨雾竹林，清露微光', preview: '#e8f0e0' },
  ]
}
