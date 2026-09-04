// 粒子系统 - 支持多种粒子效果
import type { ParticleConfig } from '@/types'
import { MotionManager } from '@/motion'

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  opacity: number
  rotation: number
  rotationSpeed: number
  life: number
  maxLife: number
  color: string
}

export class ParticleSystem {
  private canvas: HTMLCanvasElement
  private ctx: CanvasRenderingContext2D
  private particles: Particle[] = []
  private config: ParticleConfig
  private animationId: number | null = null
  private width = 0
  private height = 0
  private lastFrameTime = 0

  constructor(canvas: HTMLCanvasElement, config: ParticleConfig) {
    this.canvas = canvas
    this.ctx = canvas.getContext('2d')!
    this.config = config
    this.resize()
    this.init()
  }

  resize() {
    this.width = window.innerWidth
    this.height = window.innerHeight
    this.canvas.width = this.width
    this.canvas.height = this.height
  }

  init() {
    this.particles = []
    for (let i = 0; i < this.config.count; i++) {
      this.particles.push(this.createParticle())
    }
  }

  private createParticle(): Particle {
    const type = this.config.type

    switch (type) {
      case 'snow':
        return {
          x: Math.random() * this.width,
          y: Math.random() * this.height - this.height,
          vx: (Math.random() - 0.5) * 0.5,
          vy: Math.random() * 1 + 0.5,
          size: Math.random() * 4 + 2,
          opacity: Math.random() * 0.5 + 0.3,
          rotation: 0,
          rotationSpeed: 0,
          life: 0,
          maxLife: Infinity,
          color: '#ffffff'
        }

      case 'leaves':
        return {
          x: Math.random() * this.width,
          y: -20,
          vx: Math.random() * 2 - 1,
          vy: Math.random() * 1 + 0.5,
          size: Math.random() * 10 + 8,
          opacity: Math.random() * 0.5 + 0.3,
          rotation: Math.random() * Math.PI * 2,
          rotationSpeed: (Math.random() - 0.5) * 0.05,
          life: 0,
          maxLife: Infinity,
          color: this.config.color
        }

      case 'fireflies':
        return {
          x: Math.random() * this.width,
          y: Math.random() * this.height,
          vx: (Math.random() - 0.5) * 0.5,
          vy: (Math.random() - 0.5) * 0.5,
          size: Math.random() * 3 + 2,
          opacity: 0,
          rotation: 0,
          rotationSpeed: 0,
          life: Math.random() * 200,
          maxLife: 200 + Math.random() * 100,
          color: this.config.color
        }

      case 'bubbles':
        return {
          x: Math.random() * this.width,
          y: this.height + 20,
          vx: (Math.random() - 0.5) * 0.3,
          vy: -(Math.random() * 1 + 0.5),
          size: Math.random() * 15 + 5,
          opacity: Math.random() * 0.3 + 0.1,
          rotation: 0,
          rotationSpeed: 0,
          life: 0,
          maxLife: Infinity,
          color: this.config.color
        }

      case 'stars':
        return {
          x: Math.random() * this.width,
          y: Math.random() * this.height,
          vx: 0,
          vy: 0,
          size: Math.random() * 2 + 1,
          opacity: Math.random() * 0.8 + 0.2,
          rotation: 0,
          rotationSpeed: 0,
          life: 0,
          maxLife: Infinity,
          color: '#ffffff'
        }

      case 'matrix':
        return {
          x: Math.random() * this.width,
          y: -20,
          vx: 0,
          vy: Math.random() * 3 + 2,
          size: 14,
          opacity: Math.random() * 0.5 + 0.3,
          rotation: 0,
          rotationSpeed: 0,
          life: 0,
          maxLife: Infinity,
          color: this.config.color
        }

      default:
        return {
          x: Math.random() * this.width,
          y: Math.random() * this.height,
          vx: 0,
          vy: 0,
          size: 3,
          opacity: 0.5,
          rotation: 0,
          rotationSpeed: 0,
          life: 0,
          maxLife: Infinity,
          color: '#ffffff'
        }
    }
  }

  update() {
    const type = this.config.type
    const speed = this.config.speed

    for (let i = 0; i < this.particles.length; i++) {
      const p = this.particles[i]

      // 更新位置
      p.x += p.vx * speed
      p.y += p.vy * speed
      p.rotation += p.rotationSpeed
      p.life++

      // 萤火虫特殊处理
      if (type === 'fireflies') {
        p.vx += (Math.random() - 0.5) * 0.1
        p.vy += (Math.random() - 0.5) * 0.1
        p.vx = Math.max(-1, Math.min(1, p.vx))
        p.vy = Math.max(-1, Math.min(1, p.vy))

        // 闪烁效果
        const lifeRatio = p.life / p.maxLife
        if (lifeRatio < 0.3) {
          p.opacity = lifeRatio / 0.3
        } else if (lifeRatio > 0.7) {
          p.opacity = (1 - lifeRatio) / 0.3
        } else {
          p.opacity = 0.8 + Math.sin(p.life * 0.1) * 0.2
        }

        if (p.life >= p.maxLife) {
          this.particles[i] = this.createParticle()
        }
      }

      // 星星闪烁
      if (type === 'stars') {
        p.opacity = 0.3 + Math.sin(p.life * 0.02 + i) * 0.3
        p.life++
      }

      // 边界处理
      if (type === 'snow' || type === 'matrix') {
        if (p.y > this.height + 20) {
          this.particles[i] = this.createParticle()
        }
      } else if (type === 'leaves') {
        if (p.y > this.height + 20 || p.x < -20 || p.x > this.width + 20) {
          this.particles[i] = this.createParticle()
        }
      } else if (type === 'bubbles') {
        if (p.y < -20) {
          this.particles[i] = this.createParticle()
        }
      } else if (type === 'fireflies') {
        // 萤火虫在边界反弹
        if (p.x < 0 || p.x > this.width) p.vx *= -1
        if (p.y < 0 || p.y > this.height) p.vy *= -1
      }
    }
  }

  draw() {
    this.ctx.clearRect(0, 0, this.width, this.height)
    const type = this.config.type

    for (const p of this.particles) {
      this.ctx.save()
      this.ctx.globalAlpha = p.opacity

      switch (type) {
        case 'snow':
          this.ctx.fillStyle = p.color
          this.ctx.beginPath()
          this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
          this.ctx.fill()
          break

        case 'leaves':
          this.drawLeaf(p)
          break

        case 'fireflies':
          // 发光效果
          const gradient = this.ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 3)
          gradient.addColorStop(0, p.color)
          gradient.addColorStop(0.5, p.color + '80')
          gradient.addColorStop(1, 'transparent')
          this.ctx.fillStyle = gradient
          this.ctx.beginPath()
          this.ctx.arc(p.x, p.y, p.size * 3, 0, Math.PI * 2)
          this.ctx.fill()
          break

        case 'bubbles':
          this.ctx.strokeStyle = p.color
          this.ctx.lineWidth = 1
          this.ctx.beginPath()
          this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
          this.ctx.stroke()
          // 高光
          this.ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
          this.ctx.beginPath()
          this.ctx.arc(p.x - p.size * 0.3, p.y - p.size * 0.3, p.size * 0.2, 0, Math.PI * 2)
          this.ctx.fill()
          break

        case 'stars':
          this.drawStar(p)
          break

        case 'matrix':
          this.ctx.fillStyle = p.color
          this.ctx.font = `${p.size}px monospace`
          const char = String.fromCharCode(0x30A0 + Math.random() * 96)
          this.ctx.fillText(char, p.x, p.y)
          break
      }

      this.ctx.restore()
    }
  }

  private drawLeaf(p: Particle) {
    this.ctx.translate(p.x, p.y)
    this.ctx.rotate(p.rotation)
    this.ctx.fillStyle = p.color

    // 樱花花瓣形状
    this.ctx.beginPath()
    this.ctx.moveTo(0, -p.size * 0.5)
    this.ctx.bezierCurveTo(
      p.size * 0.5, -p.size * 0.3,
      p.size * 0.5, p.size * 0.3,
      0, p.size * 0.5
    )
    this.ctx.bezierCurveTo(
      -p.size * 0.5, p.size * 0.3,
      -p.size * 0.5, -p.size * 0.3,
      0, -p.size * 0.5
    )
    this.ctx.fill()
  }

  private drawStar(p: Particle) {
    this.ctx.fillStyle = p.color
    this.ctx.beginPath()

    // 四角星
    const spikes = 4
    const outerRadius = p.size
    const innerRadius = p.size * 0.4

    for (let i = 0; i < spikes * 2; i++) {
      const radius = i % 2 === 0 ? outerRadius : innerRadius
      const angle = (i / (spikes * 2)) * Math.PI * 2 - Math.PI / 2
      const x = p.x + Math.cos(angle) * radius
      const y = p.y + Math.sin(angle) * radius
      if (i === 0) this.ctx.moveTo(x, y)
      else this.ctx.lineTo(x, y)
    }

    this.ctx.closePath()
    this.ctx.fill()
  }

  start() {
    const animate = (currentTime: number) => {
      // 使用 MotionManager 获取帧间隔
      const frameInterval = MotionManager.getFrameInterval()
      if (frameInterval === Infinity) {
        // 动画被禁用
        return
      }

      // 帧率控制
      if (currentTime - this.lastFrameTime >= frameInterval) {
        this.lastFrameTime = currentTime
        this.update()
        this.draw()
      }
      this.animationId = requestAnimationFrame(animate)
    }
    this.animationId = requestAnimationFrame(animate)
  }

  stop() {
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId)
      this.animationId = null
    }
  }

  updateConfig(config: ParticleConfig) {
    this.config = config
    this.init()
  }
}
