export interface AmbientConfig { motif: string; color: string; secondary: string; count: number; scale: number }
/** Self-contained function serialized into the same isolated decorative Worker. */
export function ambient(config: AmbientConfig | undefined, ctx: CanvasRenderingContext2D, w: number, h: number, time: number, density: number) {
  if (!config) return
  const count = Math.max(1, Math.min(80, Math.round(config.count * density))), phase = time * .000035
  ctx.save()
  if (config.motif === 'orbits') {
    for (let i = 0; i < count; i++) {
      const x = w * (.15 + .7 * ((i * .618 + .17) % 1)) + Math.sin(phase + i * 2) * w * .08
      const y = h * (.15 + .7 * ((i * .427 + .21) % 1)) + Math.cos(phase * .7 + i) * h * .07
      const radius = Math.min(w, h) * .35 * config.scale
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius)
      gradient.addColorStop(0, i % 2 ? config.secondary : config.color); gradient.addColorStop(1, 'transparent')
      ctx.globalAlpha = .26; ctx.fillStyle = gradient; ctx.fillRect(x - radius, y - radius, radius * 2, radius * 2)
    }
  } else if (config.motif === 'waves') {
    ctx.strokeStyle = config.color; ctx.globalAlpha = .35; ctx.lineWidth = 1
    for (let i = 0; i < count; i++) {
      ctx.beginPath()
      for (let x = 0; x <= w + 20; x += 20) {
        const y = h * (.18 + i / (count + 1) * .75) + Math.sin(x / w * 5 + phase + i * .7) * 40 * config.scale
        if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y)
      }
      ctx.stroke()
    }
  } else {
    for (let i = 0; i < count; i++) {
      const x = ((i * .618 + .05) % 1) * w, y = ((i * .427 + phase * .03) % 1) * h
      ctx.globalAlpha = .25 + Math.sin(phase * 3 + i) * .15; ctx.fillStyle = i % 3 ? config.color : config.secondary
      if (config.motif === 'grid') { ctx.fillRect(x, 0, .7, h); ctx.fillRect(0, y, w, .7) }
      else { ctx.beginPath(); ctx.arc(x + Math.sin(phase + i) * 10, y, (1 + i % 3) * config.scale, 0, Math.PI * 2); ctx.fill() }
    }
  }
  ctx.restore()
}
