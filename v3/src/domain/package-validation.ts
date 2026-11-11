import { requireCondition } from './errors'
import { assertCandidate, assertManifest } from '../extensions/manifest'
import { isCapability } from '../extensions/capabilities'

const object = (value: unknown): value is Record<string, unknown> => Boolean(value && typeof value === 'object' && !Array.isArray(value))
const kinds = ['theme', 'resource', 'function']
export function assertPackages(packages: unknown, tombstones: unknown, audit: unknown): void {
  requireCondition(Array.isArray(packages) && Array.isArray(tombstones), 'storage.invalidWorkspace')
  const used = new Set<string>()
  for (const entry of packages) {
    requireCondition(object(entry) && kinds.includes(String(entry.kind)) && entry.source === 'local' && Number.isSafeInteger(entry.id) && Number(entry.id) >= 100000 && Number(entry.id) <= 999999, 'extensions.invalidRegistry')
    const identity = entry.kind + ':' + entry.id
    requireCondition(!used.has(identity), 'storage.duplicateIdentity')
    used.add(identity)
    assertManifest(entry.manifest)
    const manifest = entry.manifest
    requireCondition(entry.kind === entry.manifest.type && entry.version === entry.manifest.version && entry.author === entry.manifest.author && typeof entry.name === 'string', 'extensions.invalidRegistry')
    requireCondition(['enabled', 'disabled', 'broken'].includes(String(entry.status)), 'extensions.invalidRegistry')
    requireCondition(Array.isArray(entry.permissions) && entry.permissions.length === manifest.permissions.length && entry.permissions.every(item => isCapability(item) && manifest.permissions.includes(item)) && new Set(entry.permissions).size === entry.permissions.length, 'extensions.invalidRegistry')
    requireCondition(Array.isArray(entry.grants) && entry.grants.every(item => isCapability(item) && (entry.permissions as unknown[]).includes(item)) && new Set(entry.grants).size === entry.grants.length, 'extensions.invalidRegistry')
    requireCondition(entry.status !== 'enabled' || entry.manifest.requiredPermissions.every(item => (entry.grants as unknown[]).includes(item)), 'extensions.missingGrant')
    assertCandidate({ manifest: entry.manifest, payload: entry.payload, checksum: entry.checksum })
  }
  for (const entry of tombstones) {
    requireCondition(object(entry) && kinds.includes(String(entry.kind)) && Number.isSafeInteger(entry.id) && Number(entry.id) >= 100000 && Number(entry.id) <= 999999, 'extensions.invalidRegistry')
    const identity = entry.kind + ':' + entry.id
    requireCondition(!used.has(identity), 'storage.duplicateIdentity')
    used.add(identity)
  }
  if (audit !== undefined) {
    requireCondition(Array.isArray(audit), 'extensions.invalidRegistry')
    const ids = new Set<string>()
    for (const entry of audit) {
      requireCondition(object(entry) && typeof entry.id === 'string' && !ids.has(entry.id) && kinds.includes(String(entry.kind)) && Number.isSafeInteger(entry.packageId) && typeof entry.occurredAt === 'string' && Number.isFinite(Date.parse(entry.occurredAt)) && ['install', 'upgrade', 'grants', 'enable', 'disable', 'remove', 'failure', 'write'].includes(String(entry.action)), 'extensions.invalidRegistry')
      requireCondition(Array.isArray(entry.capabilities) && entry.capabilities.every(isCapability), 'extensions.invalidRegistry')
      ids.add(entry.id)
    }
  }
}

