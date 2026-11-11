import { requireCondition } from '../domain/errors'
import { isCapability, type Capability } from './capabilities'

export type ExtensionKind = 'theme' | 'resource' | 'function'
export interface ResourceEntry {
  kind: 'locale' | 'font'
  path: string
  alias: string
  name: string
  license: string
}
export interface ExtensionManifest {
  type: ExtensionKind
  name: Record<string, string>
  author: string
  version: string
  formatVersion: 1
  apiVersion: 1
  minAppVersion?: string
  maxAppVersion?: string
  license: string
  slug?: string
  permissions: Capability[]
  requiredPermissions: Capability[]
  checksums?: Record<string, string>
  tokens?: string
  styles?: string[]
  scripts?: string[]
  entry?: string
  extends?: number
  resources?: ResourceEntry[]
}
export interface PackageCandidate {
  manifest: ExtensionManifest
  /** Base64-encoded file bytes; source bytes survive round trips unchanged. */
  payload: Record<string, string>
  checksum: string
}
const object = (value: unknown): value is Record<string, unknown> => Boolean(value && typeof value === 'object' && !Array.isArray(value))
const string = (value: unknown): value is string => typeof value === 'string' && value.trim().length > 0
export function safePackagePath(value: unknown): value is string {
  return typeof value === 'string' && /^[a-zA-Z0-9_./ -]+$/.test(value) && !value.startsWith('/') && !value.split('/').some(part => !part || part === '.' || part === '..')
}
export function versionParts(value: unknown): number[] {
  requireCondition(typeof value === 'string' && /^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?$/.test(value), 'extensions.invalidVersion')
  const result = value.split('-')[0]!.split('.').map(Number)
  requireCondition(result.every(Number.isSafeInteger), 'extensions.invalidVersion')
  return result
}
export function compareVersions(a: string, b: string): number {
  const left = versionParts(a), right = versionParts(b)
  for (let index = 0; index < 3; index++) if (left[index] !== right[index]) return left[index]! < right[index]! ? -1 : 1
  const preA = a.split('-').slice(1).join('-'), preB = b.split('-').slice(1).join('-')
  if (!preA || !preB) return preA === preB ? 0 : preA ? -1 : 1
  const aa = preA.split('.'), bb = preB.split('.')
  for (let index = 0; index < Math.max(aa.length, bb.length); index++) {
    if (aa[index] === bb[index]) continue
    if (aa[index] === undefined || bb[index] === undefined) return aa[index] === undefined ? -1 : 1
    const x = aa[index]!, y = bb[index]!
    if (/^\d+$/.test(x) && /^\d+$/.test(y)) return Number(x) < Number(y) ? -1 : 1
    if (/^\d+$/.test(x) !== /^\d+$/.test(y)) return /^\d+$/.test(x) ? -1 : 1
    return x < y ? -1 : 1
  }
  return 0
}
export function assertManifest(value: unknown, appVersion?: string): asserts value is ExtensionManifest {
  requireCondition(object(value) && ['theme', 'resource', 'function'].includes(String(value.type)), 'extensions.invalidManifest')
  requireCondition(value.formatVersion === 1 && value.apiVersion === 1, 'extensions.incompatible')
  requireCondition(object(value.name) && Object.keys(value.name).length > 0 && Object.values(value.name).every(string), 'extensions.invalidManifest')
  requireCondition(string(value.author) && string(value.license), 'extensions.invalidManifest')
  versionParts(value.version)
  for (const key of ['minAppVersion', 'maxAppVersion']) if (value[key] !== undefined) versionParts(value[key])
  if (appVersion) {
    requireCondition(!value.minAppVersion || compareVersions(appVersion, String(value.minAppVersion)) >= 0, 'extensions.incompatible')
    requireCondition(!value.maxAppVersion || compareVersions(appVersion, String(value.maxAppVersion)) <= 0, 'extensions.incompatible')
  }
  requireCondition(Array.isArray(value.permissions) && value.permissions.every(isCapability) && new Set(value.permissions).size === value.permissions.length, 'extensions.unknownCapability')
  const permissions = value.permissions
  requireCondition(Array.isArray(value.requiredPermissions) && value.requiredPermissions.every(item => isCapability(item) && permissions.includes(item)), 'extensions.invalidManifest')
  for (const key of ['tokens', 'entry']) if (value[key] !== undefined) requireCondition(safePackagePath(value[key]), 'archive.unsafePath')
  for (const key of ['styles', 'scripts']) if (value[key] !== undefined) requireCondition(Array.isArray(value[key]) && value[key].every(safePackagePath), 'archive.unsafePath')
  if (value.extends !== undefined) requireCondition(Number.isSafeInteger(value.extends) && Number(value.extends) >= 0, 'extensions.invalidManifest')
  if (value.type === 'theme') requireCondition(safePackagePath(value.tokens) && value.permissions.includes('appearance.tokens') && (value.requiredPermissions as unknown[]).includes('appearance.tokens'), 'extensions.invalidManifest')
  if (value.type === 'function') requireCondition(safePackagePath(value.entry) && value.permissions.some(item => ['overlay.canvas', 'overlay.interactive', 'app.layout'].includes(String(item))), 'extensions.invalidManifest')
  if (value.styles && (value.styles as unknown[]).length) requireCondition(value.permissions.includes('appearance.css') || value.permissions.includes('app.layout'), 'extensions.invalidManifest')
  if (value.scripts && (value.scripts as unknown[]).length) requireCondition(value.permissions.some(item => ['overlay.canvas', 'overlay.interactive', 'app.layout'].includes(String(item))), 'extensions.invalidManifest')
  if (value.resources !== undefined) {
    requireCondition(Array.isArray(value.resources), 'extensions.invalidManifest')
    const aliases = new Set<string>()
    for (const resource of value.resources) {
      requireCondition(object(resource) && ['locale', 'font'].includes(String(resource.kind)) && safePackagePath(resource.path) && string(resource.alias) && /^[a-zA-Z0-9_-]+$/.test(resource.alias) && string(resource.name) && string(resource.license), 'extensions.invalidResource')
      requireCondition(!aliases.has(resource.alias), 'extensions.invalidResource')
      aliases.add(resource.alias)
    }
    requireCondition(value.permissions.includes('resources.register') && (value.requiredPermissions as unknown[]).includes('resources.register'), 'extensions.invalidManifest')
  }
  if (value.checksums !== undefined) requireCondition(object(value.checksums) && Object.entries(value.checksums).every(([path, hash]) => safePackagePath(path) && typeof hash === 'string' && /^[a-f0-9]{64}$/.test(hash)), 'extensions.invalidManifest')
}
export function assertCandidate(value: unknown, appVersion?: string): asserts value is PackageCandidate {
  requireCondition(object(value), 'extensions.invalidManifest')
  assertManifest(value.manifest, appVersion)
  requireCondition(object(value.payload) && Object.entries(value.payload).every(([path, bytes]) => safePackagePath(path) && typeof bytes === 'string' && bytes.length % 4 === 0 && /^[A-Za-z0-9+/]*={0,2}$/.test(bytes)), 'extensions.invalidPayload')
  requireCondition(typeof value.checksum === 'string' && /^[a-f0-9]{64}$/.test(value.checksum), 'extensions.invalidPayload')
  const manifest = value.manifest
  const paths = [manifest.tokens, manifest.entry, ...(manifest.styles || []), ...(manifest.scripts || []), ...(manifest.resources || []).map(item => item.path)].filter((path): path is string => Boolean(path))
  requireCondition(paths.every(path => Object.hasOwn(value.payload as object, path)), 'archive.payloadMissing')
}
export function payloadBytes(payload: Record<string, string>, path: string): Uint8Array {
  requireCondition(Object.hasOwn(payload, path), 'archive.payloadMissing')
  return Uint8Array.from(atob(payload[path]!), value => value.charCodeAt(0))
}
export function payloadJson(payload: Record<string, string>, path: string): unknown {
  try { return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(payloadBytes(payload, path))) }
  catch { requireCondition(false, 'extensions.invalidPayload') }
}

