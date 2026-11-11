import catalog from '../../resources/themes/catalog.json'
import { Registry } from '../extensions/registry'

export interface ThemeDefinition {
  id: number
  slug: string
  name: Record<string, string>
  mode: string
  palette: { background: string; surface: string; text: string; muted: string; accent: string }
  decoration?: { gradient: string | null; particles: unknown; renderer: string | null }
  legacyType?: string
  css?: string
}
export const themes = new Registry<ThemeDefinition>()
for (const theme of catalog) themes.register(theme)

function rgb(value: string, fallback: number[] = [255, 255, 255]): number[] {
  if (/^#[a-f0-9]{6}$/i.test(value)) return [1, 3, 5].map(index => parseInt(value.slice(index, index + 2), 16))
  if (/^#[a-f0-9]{3}$/i.test(value)) return value.slice(1).split('').map(char => parseInt(char + char, 16))
  const match = value.match(/^rgba?\(([^)]+)\)$/i)
  if (match) {
    const parts = match[1]!.split(',').map(Number)
    const alpha = parts[3] ?? 1
    return parts.slice(0, 3).map((item, index) => Math.round(item * alpha + fallback[index]! * (1 - alpha)))
  }
  return fallback
}
function luminance(value: number[]): number {
  const linear = value.map(component => component / 255 <= 0.04045 ? component / 255 / 12.92 : ((component / 255 + 0.055) / 1.055) ** 2.4)
  return linear[0]! * 0.2126 + linear[1]! * 0.7152 + linear[2]! * 0.0722
}
export function contrast(a: string, b: string): number {
  const values = [luminance(rgb(a)), luminance(rgb(b))].sort((x, y) => y - x)
  return (values[0]! + 0.05) / (values[1]! + 0.05)
}
const css = (value: number[]) => '#' + value.map(channel => Math.round(channel).toString(16).padStart(2, '0')).join('')
export function themeTokens(theme: ThemeDefinition): Record<string, string> {
  const background = rgb(theme.palette.background)
  const surface = css(rgb(theme.palette.surface, background))
  const page = css(background)
  const dark = luminance(background) < 0.15
  const foreground = dark ? '#edf2f7' : '#202a35'
  const ensure = (color: string, against: string, fallback: string) => {
    if (contrast(color, against) >= 4.5) return color
    if (contrast(fallback, against) >= 4.5) return fallback
    return contrast('#ffffff', against) >= contrast('#000000', against) ? '#ffffff' : '#000000'
  }
  const ink = ensure(css(rgb(theme.palette.text)), surface, foreground)
  const muted = ensure(css(rgb(theme.palette.muted)), surface, dark ? '#b8c4d4' : '#5f6b7b')
  const accent = css(rgb(theme.palette.accent))
  const onAccent = contrast('#ffffff', accent) >= contrast('#000000', accent) ? '#ffffff' : '#000000'
  return {
    '--page': page, '--surface': surface, '--ink': ink, '--muted': muted,
    '--accent': accent, '--on-accent': onAccent,
    '--accent-text': ensure(accent, surface, ink),
    '--line': dark ? '#354052' : '#e4e8ee',
    '--subtle': dark ? '#1e293b' : '#f3f5f8',
    '--sidebar': dark ? page : '#f0f3f5',
    '--danger': dark ? '#ffb5ac' : '#aa3639',
    '--success': dark ? '#99d9b8' : '#2e7758',
    '--color-scheme': dark ? 'dark' : 'light',
  }
}
export function applyTheme(id: number): void {
  let theme = themes.get(id) || themes.get(1)!
  document.documentElement.dataset.activeTheme = String(theme.id)
  if (theme.mode === 'system') theme = themes.get(matchMedia('(prefers-color-scheme: dark)').matches ? 2 : 1)!
  const tokens = themeTokens(theme)
  for (const [key, value] of Object.entries(tokens)) document.documentElement.style.setProperty(key, value)
  document.documentElement.style.colorScheme = tokens['--color-scheme']!
  let style = document.getElementById('effilife-theme-visuals') as HTMLStyleElement | null
  if (!style) { style = document.createElement('style'); style.id = 'effilife-theme-visuals'; document.head.append(style) }
  style.textContent = theme.css || ''
}

