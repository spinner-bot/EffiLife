import { describe, expect, it } from 'vitest'
import { readdirSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import zh from '../../src/i18n/zh-CN.json'
import en from '../../src/i18n/en-US.json'
import { locales, setLocale, t } from '../../src/i18n'
import { themes, themeTokens, contrast } from '../../src/ui/themes'
import { zonedInstant } from '../../src/domain/time'

function sourceFiles(path: string): string[] {
  return readdirSync(path, { withFileTypes: true }).flatMap(entry => entry.isDirectory() ? sourceFiles(resolve(path, entry.name)) : /\.(ts|vue)$/.test(entry.name) ? [resolve(path, entry.name)] : [])
}

describe('extensible UI foundations', () => {
  it('keeps complete Chinese and English catalogs and resolves literal message keys', () => {
    expect(Object.keys(zh).sort()).toEqual(Object.keys(en).sort())
    const keys = sourceFiles(resolve('src')).flatMap(path => [...readFileSync(path, 'utf8').matchAll(/\bt\(['"]([^'"]+)['"]/g)].map(match => match[1]!))
    expect([...new Set(keys)].filter(key => !(key in zh))).toEqual([])
  })
  it('can register a locale without adding language branches to the application', () => {
    locales.register({ id: 'fr-FR', name: 'Français', direction: 'ltr', messages: { 'nav.home': 'Vue générale' } })
    setLocale('fr-FR')
    expect(t('nav.home')).toBe('Vue générale')
    expect(t('common.save')).toBe('Save')
    setLocale('zh-CN')
  })
  it('retains twenty-five themes with accessible body and button foregrounds', () => {
    expect(themes.values()).toHaveLength(25)
    for (const theme of themes.values()) {
      const tokens = themeTokens(theme)
      expect(contrast(tokens['--ink']!, tokens['--surface']!), theme.slug).toBeGreaterThanOrEqual(4.5)
      expect(contrast(tokens['--muted']!, tokens['--surface']!), theme.slug).toBeGreaterThanOrEqual(4.5)
      expect(contrast(tokens['--on-accent']!, tokens['--accent']!), theme.slug).toBeGreaterThanOrEqual(4.5)
    }
  })
  it('interprets date fields in the workspace zone and rejects nonexistent DST times', () => {
    expect(zonedInstant('2026-11-11T09:40', 'Asia/Shanghai')).toBe('2026-11-11T01:40:00.000Z')
    expect(() => zonedInstant('2026-03-08T02:30', 'America/New_York')).toThrow('validation.invalidTime')
    expect(() => zonedInstant('2026-02-31T10:00', 'UTC')).toThrow('validation.invalidTime')
  })
})
