import { describe, expect, it } from 'vitest'
import JSZip from 'jszip'
import { inspectExtension } from '../../src/adapters/extension-package'
import { emptyWorkspace } from '../../src/domain/initial'
import { execute } from '../../src/domain/engine'
import type { WorkspaceCommand } from '../../src/domain/commands'
import type { PackageCandidate } from '../../src/extensions/manifest'
import { assertManifest, compareVersions } from '../../src/extensions/manifest'
import { assertWorkspace } from '../../src/domain/validation'
import { scopeVisualCss } from '../../src/extensions/visual-css'
import { sha256 } from '../../src/adapters/archive'

export function candidate(): PackageCandidate {
  return {
    manifest: { type: 'theme', name: { 'en-US': 'Forest', 'zh-CN': '森林' }, author: 'Example', license: 'MIT', version: '1.0.0', formatVersion: 1, apiVersion: 1, permissions: ['appearance.tokens', 'appearance.css'], requiredPermissions: ['appearance.tokens'], tokens: 'tokens.json', styles: ['styles/main.css'] },
    payload: {
      'tokens.json': btoa(JSON.stringify({ palette: { background: '#102a20', surface: '#17382c', text: '#ffffff', accent: '#47b894' } })),
      'styles/main.css': btoa('.panel { border-radius: 18px; background-color: var(--surface); }'),
    }, checksum: 'a'.repeat(64),
  }
}
function setup() {
  let workspace = emptyWorkspace('3.0.0')
  let id = 0, operation = 0
  return {
    get state() { return workspace },
    run(command: WorkspaceCommand) {
      const result = execute(workspace, { operationId: 'op-' + ++operation, command }, { now: '2026-11-11T01:00:00Z', id: () => 'id-' + ++id })
      workspace = result.workspace
      assertWorkspace(workspace)
      return result.result
    },
  }
}
describe('extension contracts and installation', () => {
  it('ignores local manifest IDs and allocates independently by kind without reusing tombstones', () => {
    const f = setup(), first = candidate()
    Object.assign(first.manifest, { id: 1, source: 'builtin' })
    expect(f.run({ type: 'installPackage', candidate: first }).entityId).toBe('100000')
    expect(f.state.packages[0]?.source).toBe('local')
    f.run({ type: 'removePackage', kind: 'theme', packageId: 100000 })
    expect(f.run({ type: 'installPackage', candidate: candidate() }).entityId).toBe('100001')
    expect(f.state.packageTombstones).toEqual([{ kind: 'theme', id: 100000 }])
    expect(f.state.extensionAudit?.map(row => row.action)).toEqual(['install', 'remove', 'install'])
  })
  it('defaults to L0 and disables a package after revoking its required CSS grant', () => {
    const f = setup(), value = candidate()
    value.manifest.requiredPermissions.push('appearance.css')
    f.run({ type: 'installPackage', candidate: value })
    expect(f.state.packages[0]?.grants).toEqual(['appearance.tokens'])
    expect(f.state.packages[0]?.status).toBe('disabled')
    f.run({ type: 'setPackageGrants', kind: 'theme', packageId: 100000, grants: ['appearance.tokens', 'appearance.css'] })
    f.run({ type: 'setPackageStatus', kind: 'theme', packageId: 100000, enabled: true })
    f.run({ type: 'savePreferences', preferences: { themeId: 100000 } })
    f.run({ type: 'setPackageGrants', kind: 'theme', packageId: 100000, grants: ['appearance.tokens'] })
    expect(f.state.preferences.themeId).toBe(1)
    expect(f.state.packages[0]?.status).toBe('disabled')
    expect(() => f.run({ type: 'setPackageStatus', kind: 'theme', packageId: 100000, enabled: true })).toThrow('extensions.missingGrant')
  })
  it('keeps ID on explicit upgrade and requires new capabilities to be reauthorized', () => {
    const f = setup()
    f.run({ type: 'installPackage', candidate: candidate() })
    const next = candidate()
    next.manifest.version = '1.1.0'
    next.manifest.requiredPermissions.push('appearance.css')
    expect(f.run({ type: 'installPackage', candidate: next, updateId: 100000 }).entityId).toBe('100000')
    expect(f.state.packages).toHaveLength(1)
    expect(f.state.packages[0]?.status).toBe('disabled')
    expect(() => f.run({ type: 'installPackage', candidate: next, updateId: 100000 })).toThrow('extensions.versionNotNewer')
  })
  it('rejects unknown abilities, external paths, incompatible versions and unsafe theme tokens', () => {
    const value = candidate()
    expect(() => assertManifest({ ...value.manifest, permissions: ['os.filesystem'] })).toThrow('extensions.unknownCapability')
    expect(() => assertManifest({ ...value.manifest, tokens: '../tokens.json' })).toThrow('archive.unsafePath')
    expect(() => assertManifest({ ...value.manifest, minAppVersion: '4.0.0' }, '3.0.0')).toThrow('extensions.incompatible')
    value.payload['tokens.json'] = btoa(JSON.stringify({ palette: { background: 'url(https://example.com)' } }))
    expect(() => setup().run({ type: 'installPackage', candidate: value })).toThrow('extensions.invalidTokens')
  })
  it('scopes all selectors and rejects CSS geometry escape and resource loading', () => {
    expect(scopeVisualCss('.panel, .input:hover { color: #eee; }', 100000)).toBe('[data-active-theme="100000"] .panel,[data-active-theme="100000"] .input:hover{color:#eee}')
    for (const css of ['.panel{position:fixed}', '.panel{background-image:url(https://example.com/x)}', '@import "x";', '.panel{color:var(--external-image)}', '.panel{display:none}', '.panel{color:red!important}', '.panel{color:r\\65 d}', '@media(all){.panel{color:red}}']) expect(() => scopeVisualCss(css, 100000), css).toThrow('extensions.unsafeCss')
  })
  it('checks container contents and optional file digests before presenting a preview', async () => {
    const value = candidate(), zip = new JSZip()
    for (const [path, content] of Object.entries(value.payload)) zip.file(path, Uint8Array.from(atob(content), char => char.charCodeAt(0)))
    value.manifest.checksums = { 'tokens.json': await sha256(Uint8Array.from(atob(value.payload['tokens.json']!), char => char.charCodeAt(0))) }
    zip.file('manifest.json', JSON.stringify(value.manifest))
    const result = await inspectExtension(await zip.generateAsync({ type: 'uint8array' }), '3.0.0')
    expect(result.manifest.name).toEqual(value.manifest.name)
    zip.file('tokens.json', '{}')
    await expect(inspectExtension(await zip.generateAsync({ type: 'uint8array' }), '3.0.0')).rejects.toThrow('archive.checksumMismatch')
  })
  it('orders stable and prerelease versions numerically', () => {
    expect(compareVersions('3.0.0-beta.10', '3.0.0-beta.2')).toBe(1)
    expect(compareVersions('3.0.0', '3.0.0-beta.10')).toBe(1)
    expect(compareVersions('3.0.10', '3.0.9')).toBe(1)
  })
})

