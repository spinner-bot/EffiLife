import { ambient } from './ambient-decoration'
import { defaultAppearance, type AppearanceOptions } from '../domain/appearance'
import type { InstalledPackage } from '../domain/models'
import type { ThemeDefinition } from '../ui/themes'
import type { ExtensionManifest } from './manifest'

function encode(value: string) {
  const bytes = new TextEncoder().encode(value)
  let text = ''
  for (let start = 0; start < bytes.length; start += 32768) text += String.fromCharCode(...bytes.subarray(start, start + 32768))
  return btoa(text)
}
function particles(config: { enabled?: boolean; type: string; count: number; speed: number; size: number; color: string } | null, ctx: CanvasRenderingContext2D, w: number, h: number, time: number) {
  if (!config?.enabled) return
  for (let i = 0; i < Math.min(100, config.count); i++) {
    const seed = Math.abs(Math.sin(i * 83.17 + 12) * 931.33) % 1
    const drift = time * config.speed * 0.015
    const x = (seed * w + Math.sin(time * 0.0005 + i) * 16 + w) % w
    const y = (i * 127.7 + drift) % h
    ctx.save(); ctx.fillStyle = config.color; ctx.strokeStyle = config.color
    ctx.globalAlpha = config.type === 'fireflies' || config.type === 'stars' ? 0.3 + Math.sin(time * 0.001 + i) * 0.25 : 0.6
    ctx.beginPath()
    if (config.type === 'leaves') { ctx.translate(x, y); ctx.rotate(time * 0.0003 + i); ctx.ellipse(0, 0, config.size / 2, config.size / 4, 0, 0, Math.PI * 2); ctx.fill() }
    else if (config.type === 'snow') { ctx.moveTo(x, y); ctx.lineTo(x - 2, y + config.size * 5); ctx.stroke() }
    else { ctx.arc(x, config.type === 'bubbles' ? h - y : y, config.size / 2, 0, Math.PI * 2); config.type === 'bubbles' ? ctx.stroke() : ctx.fill() }
    ctx.restore()
  }
}
export async function builtinDecoration(theme: ThemeDefinition, options: AppearanceOptions = theme.appearance || defaultAppearance()): Promise<InstalledPackage | undefined> {
  const decoration = theme.decoration
  if (!options.animation.enabled || !decoration || !(decoration.renderer || decoration.particles || decoration.gradient || decoration.ambient)) return undefined
  const renderer = decoration.factory ? '(' + decoration.factory + ')().renderCanvas' : decoration.renderer || '() => {}'
  const particleConfig = decoration.particles ? { ...decoration.particles as Record<string, unknown>, count: Math.round(Number((decoration.particles as { count: number }).count) * options.animation.density) } : null
  const source = (decoration.helpers || '') + '\nconst renderer = ' + renderer + ';\nconst particles = ' + particles.toString() + ';\nconst ambient = ' + ambient.toString() + ';\nEffiLife.onFrame(({ctx,width,height,time}) => { const adjustedTime = time * ' + options.animation.speed + '; renderer(ctx,width,height,adjustedTime); particles(' + JSON.stringify(particleConfig) + ',ctx,width,height,adjustedTime); ambient(' + JSON.stringify(decoration.ambient || null) + ',ctx,width,height,adjustedTime,' + options.animation.density + '); });'
  const manifest: ExtensionManifest = {
    type: 'theme', name: theme.name, author: 'EffiLife', license: 'UNLICENSED', version: '1.0.0', formatVersion: 1, apiVersion: 1,
    permissions: ['appearance.tokens', 'overlay.canvas'], requiredPermissions: ['appearance.tokens', 'overlay.canvas'],
    tokens: 'tokens.json', scripts: ['scripts/decoration.js'],
  }
  const payload = { 'tokens.json': encode(JSON.stringify({ palette: theme.palette })), 'scripts/decoration.js': encode(source) }
  const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(JSON.stringify({ manifest, payload })))
  return {
    id: theme.id, kind: 'theme', name: theme.name['en-US'] || Object.values(theme.name)[0]!, author: 'EffiLife',
    version: '1.0.0', source: 'builtin', status: 'enabled', permissions: manifest.permissions, grants: manifest.permissions,
    manifest: { ...manifest }, payload, checksum: [...new Uint8Array(hash)].map(value => value.toString(16).padStart(2, '0')).join(''),
  }
}

