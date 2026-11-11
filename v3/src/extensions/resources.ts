import { shallowRef } from 'vue'
import type { InstalledPackage } from '../domain/models'
import { assertCandidate, payloadBytes, type PackageCandidate } from './manifest'
import { assertContent, readLocale, readThemeTokens } from './content'
import { effectiveCapabilities, isCapability } from './capabilities'
import { scopeVisualCss } from './visual-css'
import { themes, type ThemeDefinition } from '../ui/themes'
import { fonts } from '../ui/fonts'
import { locales } from '../i18n'
import { DomainError, requireCondition } from '../domain/errors'

export const resourceRevision = shallowRef(0)
export const resourceFailures = shallowRef<Array<{ kind: string; id: number; code: string }>>([])
const cleanup = new Map<string, () => void>()
let fingerprint = ''
function candidateFor(entry: InstalledPackage): PackageCandidate {
  const value = { manifest: entry.manifest, payload: entry.payload, checksum: entry.checksum }
  assertCandidate(value)
  assertContent(value)
  return value
}
function installResources(entry: InstalledPackage, candidate: PackageCandidate, dispose: Array<() => void>) {
  for (const resource of candidate.manifest.resources || []) {
    if (resource.kind === 'locale') {
      const locale = readLocale(candidate, resource.path)
      requireCondition(!locales.get(locale.id), 'extensions.resourceConflict')
      locales.register({ ...locale, name: resource.name })
      dispose.push(() => { locales.remove(locale.id) })
    } else {
      const id = 'pkg:' + entry.id + ':' + resource.alias
      requireCondition(!fonts.get(id), 'extensions.resourceConflict')
      const family = 'EffiLife_' + entry.id + '_' + resource.alias.replaceAll('-', '_')
      const bytes = payloadBytes(candidate.payload, resource.path)
      let face: FontFace | undefined
      let live = true
      let loading: Promise<void> | undefined
      fonts.register({
        id, name: resource.name, family: '"' + family + '", system-ui, sans-serif', license: resource.license,
        load: () => loading ||= (async () => {
          const loaded = await new FontFace(family, Uint8Array.from(bytes).buffer).load()
          if (live) { face = loaded; document.fonts.add(loaded) }
        })().catch(error => { loading = undefined; throw error }),
      })
      dispose.push(() => { live = false; if (face) document.fonts.delete(face); fonts.remove(id) })
    }
  }
}
export function reconcileResources(entries: readonly InstalledPackage[]): void {
  // A data archive may contain changed bytes with copied metadata. Compare the
  // content too; claimed fingerprints are not a trusted cache invalidation key.
  const signature = JSON.stringify(entries)
  if (signature === fingerprint) return
  fingerprint = signature
  for (const dispose of cleanup.values()) dispose()
  cleanup.clear()
  const failures: typeof resourceFailures.value = []
  const active = entries.filter(entry => entry.status === 'enabled')
  const waiting = [...active]
  // Resolve inheritance in dependency order, irrespective of installation order.
  for (let pass = 0; waiting.length && pass <= active.length; pass++) {
    let progressed = false
    for (const entry of [...waiting]) {
      const dispose: Array<() => void> = []
      try {
        const candidate = candidateFor(entry)
        const granted = effectiveCapabilities(candidate.manifest.permissions, entry.grants.filter(isCapability))
        if (entry.kind === 'theme') {
          const parent = themes.get(candidate.manifest.extends ?? 1)
          if (!parent && active.some(item => item.kind === 'theme' && item.id === candidate.manifest.extends && waiting.includes(item))) continue
          requireCondition(parent, 'extensions.parentMissing')
          const tokens = readThemeTokens(candidate)
          const definition: ThemeDefinition = {
            id: entry.id, slug: candidate.manifest.slug || String(entry.id), name: candidate.manifest.name,
            mode: tokens.mode || 'light', palette: { ...parent.palette, ...tokens.palette },
          }
          if (granted.includes('appearance.css')) definition.css = (candidate.manifest.styles || []).map(path => scopeVisualCss(new TextDecoder().decode(payloadBytes(candidate.payload, path)), entry.id)).join('\n')
          themes.register(definition)
          dispose.push(() => { themes.remove(entry.id) })
        }
        if (granted.includes('resources.register')) installResources(entry, candidate, dispose)
        cleanup.set(entry.kind + ':' + entry.id, () => { for (const callback of dispose.reverse()) callback() })
      } catch (error) {
        for (const callback of dispose.reverse()) callback()
        failures.push({ kind: entry.kind, id: entry.id, code: error instanceof DomainError ? error.code : 'extensions.loadFailed' })
      }
      waiting.splice(waiting.indexOf(entry), 1)
      progressed = true
    }
    if (!progressed) break
  }
  for (const entry of waiting) failures.push({ kind: entry.kind, id: entry.id, code: 'extensions.inheritanceCycle' })
  resourceFailures.value = failures
  resourceRevision.value++
}

