import type { Workspace } from '../domain/models'
import { capabilities, isCapability } from './capabilities'
import { assertManifest } from './manifest'

/** Archive possession is not consent to execute the extensions it contains. */
export function requireArchiveConsent(workspace: Workspace): { workspace: Workspace; changed: boolean } {
  const next = structuredClone(workspace)
  let changed = false
  for (const entry of next.packages) {
    assertManifest(entry.manifest)
    const grants = entry.grants.filter(value => isCapability(value) && capabilities[value].level === 0)
    if (grants.length !== entry.grants.length) changed = true
    entry.grants = grants
    if (!entry.manifest.requiredPermissions.every(value => grants.includes(value))) {
      entry.status = 'disabled'
      if (entry.kind === 'theme' && next.preferences.themeId === entry.id) next.preferences.themeId = 1
    }
  }
  return { workspace: next, changed }
}

