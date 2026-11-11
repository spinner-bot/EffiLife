import { defaultAppearance, type AppearanceOptions } from '../domain/appearance'
import type { ThemeDefinition } from './themes'
export function appearanceFor(theme: ThemeDefinition, overrides?: Record<string, AppearanceOptions>): AppearanceOptions {
  const value = overrides?.[String(theme.id)] || theme.appearance || defaultAppearance()
  return { effect: value.effect, parameters: { ...value.parameters }, animation: { ...value.animation } }
}
const renderers: Record<string, (parameters: Record<string, number>) => Record<string, string>> = {
  solid: p => ({ '--card-surface': 'var(--surface)', '--card-filter': 'none', '--card-radius': p.radius + 'px', '--card-shadow': '0 5px 22px rgb(0 0 0 / ' + p.shadow! * .12 + ')' }),
  glass: p => ({ '--card-surface': `color-mix(in srgb, var(--surface) ${p.opacity! * 100}%, transparent)`, '--card-filter': `blur(${p.blur}px) saturate(${p.saturation}%)`, '--card-radius': 'var(--radius)', '--card-shadow': '0 8px 32px #0000000a, inset 0 1px 0 #ffffff15' }),
  frosted: p => ({ '--card-surface': `color-mix(in srgb, color-mix(in srgb, var(--surface) ${(1 - p.tint!) * 100}%, var(--accent)) ${p.opacity! * 100}%, transparent)`, '--card-filter': `blur(${p.blur}px) saturate(85%)`, '--card-radius': 'var(--radius)', '--card-shadow': '0 6px 22px #00000008, inset 0 1px 0 #ffffff28' }),
}
export function surfaceTokens(options: AppearanceOptions): Record<string, string> {
  return renderers[options.effect]!(options.parameters)
}
export function applySurface(options: AppearanceOptions) {
  document.documentElement.dataset.surfaceEffect = options.effect
  for (const [key, value] of Object.entries(surfaceTokens(options))) document.documentElement.style.setProperty(key, value)
}
