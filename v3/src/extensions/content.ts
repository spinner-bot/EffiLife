import { requireCondition } from '../domain/errors'
import { payloadBytes, payloadJson, type PackageCandidate } from './manifest'
import { scopeVisualCss } from './visual-css'

const object = (value: unknown): value is Record<string, unknown> => Boolean(value && typeof value === 'object' && !Array.isArray(value))
export interface ThemeTokens {
  mode?: 'light' | 'dark' | 'system'
  palette: Partial<Record<'background' | 'surface' | 'text' | 'muted' | 'accent', string>>
}
export function readThemeTokens(candidate: PackageCandidate): ThemeTokens {
  const value = payloadJson(candidate.payload, candidate.manifest.tokens!)
  requireCondition(object(value) && object(value.palette), 'extensions.invalidTokens')
  requireCondition(Object.entries(value.palette).every(([key, color]) => ['background', 'surface', 'text', 'muted', 'accent'].includes(key) && typeof color === 'string' && /^#[a-f0-9]{6}$/i.test(color)), 'extensions.invalidTokens')
  requireCondition(value.mode === undefined || ['light', 'dark', 'system'].includes(String(value.mode)), 'extensions.invalidTokens')
  return value as unknown as ThemeTokens
}
export interface LocaleResource {
  id: string
  direction: 'ltr' | 'rtl'
  messages: Record<string, string>
}
export function readLocale(candidate: PackageCandidate, path: string): LocaleResource {
  const value = payloadJson(candidate.payload, path)
  requireCondition(object(value) && typeof value.id === 'string' && /^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$/.test(value.id), 'extensions.invalidResource')
  try { new Intl.DateTimeFormat(value.id).format() } catch { requireCondition(false, 'extensions.invalidResource') }
  requireCondition(value.direction === 'ltr' || value.direction === 'rtl', 'extensions.invalidResource')
  requireCondition(object(value.messages) && Object.entries(value.messages).every(([key, message]) => /^[a-zA-Z0-9_.-]+$/.test(key) && typeof message === 'string'), 'extensions.invalidResource')
  return value as unknown as LocaleResource
}
export function assertContent(candidate: PackageCandidate): void {
  if (candidate.manifest.type === 'theme') readThemeTokens(candidate)
  for (const path of candidate.manifest.styles || []) scopeVisualCss(new TextDecoder().decode(payloadBytes(candidate.payload, path)), 100000)
  for (const resource of candidate.manifest.resources || []) {
    if (resource.kind === 'locale') readLocale(candidate, resource.path)
    else {
      const bytes = payloadBytes(candidate.payload, resource.path)
      const magic = new TextDecoder('latin1').decode(bytes.subarray(0, 4))
      requireCondition(['wOFF', 'wOF2', 'OTTO', 'true'].includes(magic) || bytes.slice(0, 4).join(',') === '0,1,0,0', 'extensions.invalidResource')
    }
  }
}

