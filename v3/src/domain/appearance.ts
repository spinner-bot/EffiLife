import { requireCondition } from './errors'
export interface AppearanceOptions {
  effect: string
  parameters: Record<string, number>
  animation: { enabled: boolean; speed: number; intensity: number; density: number }
}
export interface EffectParameter { key: string; label: string; min: number; max: number; step: number; initial: number }
export interface SurfaceEffect { id: string; label: string; parameters: EffectParameter[] }
const parameter = (key: string, min: number, max: number, step: number, initial: number): EffectParameter => ({ key, label: 'appearance.' + key, min, max, step, initial })
/** Parameter contracts are shared by settings, archive validation and renderers. */
export const surfaceEffects: SurfaceEffect[] = [
  { id: 'solid', label: 'appearance.solid', parameters: [parameter('radius', 8, 28, 1, 14), parameter('shadow', 0, 1, .05, .15)] },
  { id: 'glass', label: 'appearance.glass', parameters: [parameter('opacity', .55, .98, .01, .78), parameter('blur', 0, 32, 1, 16), parameter('saturation', 80, 180, 5, 120)] },
  { id: 'frosted', label: 'appearance.frosted', parameters: [parameter('opacity', .65, 1, .01, .88), parameter('blur', 12, 48, 1, 28), parameter('tint', 0, .2, .01, .04)] },
]
export function effectDefaults(id: string): Record<string, number> {
  return Object.fromEntries(surfaceEffects.find(effect => effect.id === id)!.parameters.map(field => [field.key, field.initial]))
}
export function defaultAppearance(): AppearanceOptions {
  return { effect: 'solid', parameters: effectDefaults('solid'), animation: { enabled: true, speed: .7, intensity: .35, density: 1 } }
}
export function assertAppearance(value: unknown, code: string): asserts value is AppearanceOptions {
  const options = value as AppearanceOptions | null
  requireCondition(options && typeof options === 'object', code)
  const effect = surfaceEffects.find(item => item.id === options.effect)
  requireCondition(effect && options.parameters && typeof options.parameters === 'object' && !Array.isArray(options.parameters), code)
  requireCondition(Object.keys(options.parameters).length === effect.parameters.length, code)
  for (const field of effect.parameters) requireCondition(Number.isFinite(options.parameters[field.key]) && options.parameters[field.key]! >= field.min && options.parameters[field.key]! <= field.max, code)
  const animation = options.animation
  requireCondition(animation && typeof animation.enabled === 'boolean', code)
  for (const [key, min, max] of [['speed', .2, 2], ['intensity', 0, 1], ['density', .2, 2]] as const) requireCondition(Number.isFinite(animation[key]) && animation[key] >= min && animation[key] <= max, code)
}
