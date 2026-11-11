import { afterEach, expect, it } from 'vitest'
import type { InstalledPackage } from '../../src/domain/models'
import { emptyWorkspace } from '../../src/domain/initial'
import { reconcileResources, resourceFailures } from '../../src/extensions/resources'
import { themes } from '../../src/ui/themes'
import { fonts } from '../../src/ui/fonts'
import { locales } from '../../src/i18n'
import { requireArchiveConsent } from '../../src/extensions/archive-consent'

function entry(id: number, parent?: number): InstalledPackage {
  return {
    id, kind: 'theme', name: 'Theme ' + id, author: 'Test', source: 'local', status: 'enabled', version: '1.0.0', permissions: ['appearance.tokens'], grants: ['appearance.tokens'], checksum: 'a'.repeat(64),
    manifest: { type: 'theme', name: { 'en-US': 'Theme ' + id }, author: 'Test', license: 'MIT', formatVersion: 1, apiVersion: 1, version: '1.0.0', permissions: ['appearance.tokens'], requiredPermissions: ['appearance.tokens'], tokens: 'tokens.json', extends: parent },
    payload: { 'tokens.json': btoa(JSON.stringify({ palette: { accent: '#7733cc' } })) },
  }
}
afterEach(() => reconcileResources([]))
it('resolves out-of-order inheritance and cleans it up when packages disappear', () => {
  reconcileResources([entry(100000, 100001), entry(100001)])
  expect(resourceFailures.value).toEqual([])
  expect(themes.get(100000)?.palette.accent).toBe('#7733cc')
  reconcileResources([])
  expect(themes.get(100000)).toBeUndefined()
  expect(themes.get(100001)).toBeUndefined()
  expect(themes.values()).toHaveLength(25)
})
it('detects inheritance cycles and retains the built-in fallback', () => {
  reconcileResources([entry(100000, 100001), entry(100001, 100000)])
  expect(resourceFailures.value).toHaveLength(2)
  expect(resourceFailures.value.every(item => item.code === 'extensions.inheritanceCycle')).toBe(true)
  expect(themes.get(1)).toBeDefined()
  expect(themes.get(100000)).toBeUndefined()
})
it('invalidates copied package fingerprints when bytes inside an imported archive differ', () => {
  const theme = entry(100000)
  reconcileResources([theme])
  theme.payload['tokens.json'] = btoa(JSON.stringify({ palette: { accent: '#008877' } }))
  reconcileResources([theme])
  expect(themes.get(100000)?.palette.accent).toBe('#008877')
})
it('rolls back partial registration on a locale identity conflict', () => {
  const value = entry(100000)
  value.kind = 'resource'; value.permissions = value.grants = ['resources.register']
  value.manifest = { type: 'resource', name: { 'en-US': 'Languages' }, author: 'Test', license: 'MIT', formatVersion: 1, apiVersion: 1, version: '1.0.0', permissions: ['resources.register'], requiredPermissions: ['resources.register'], resources: [
    { kind: 'locale', alias: 'french', path: 'fr.json', name: 'Français', license: 'MIT' },
    { kind: 'locale', alias: 'conflict', path: 'zh.json', name: 'Override', license: 'MIT' },
  ] }
  value.payload = {
    'fr.json': btoa(JSON.stringify({ id: 'fr-FR', direction: 'ltr', messages: { 'nav.home': 'Accueil' } })),
    'zh.json': btoa(JSON.stringify({ id: 'zh-CN', direction: 'ltr', messages: { 'nav.home': 'Override' } })),
  }
  reconcileResources([value])
  expect(resourceFailures.value[0]?.code).toBe('extensions.resourceConflict')
  expect(locales.get('fr-FR')).toBeUndefined()
  expect(locales.get('zh-CN')?.name).toBe('简体中文')
  expect(fonts.values()).toHaveLength(2)
})
it('resets imported executable grants without changing the source or its audit history', () => {
  const workspace = emptyWorkspace('3.0.0'), theme = entry(100000)
  theme.permissions.push('app.layout'); theme.grants.push('app.layout')
  theme.manifest.permissions = theme.permissions
  theme.manifest.requiredPermissions = theme.permissions
  workspace.packages.push(theme); workspace.preferences.themeId = theme.id
  const result = requireArchiveConsent(workspace)
  expect(result.changed).toBe(true)
  expect(result.workspace.packages[0]?.grants).toEqual(['appearance.tokens'])
  expect(result.workspace.packages[0]?.status).toBe('disabled')
  expect(result.workspace.preferences.themeId).toBe(1)
  expect(workspace.packages[0]?.grants).toContain('app.layout')
})
it('keeps a future-version package disabled even if it came inside a valid data archive', () => {
  const value = entry(100000)
  value.manifest.minAppVersion = '4.0.0'
  reconcileResources([value], '3.0.0')
  expect(themes.get(value.id)).toBeUndefined()
  expect(resourceFailures.value[0]?.code).toBe('extensions.incompatible')
})

