import type { WorkspaceCommand } from './commands'
import type { CommandContext, ExtensionAudit, InstalledPackage, OperationResult, Workspace } from './models'
import { requireCondition } from './errors'
import { assertCandidate, assertManifest, compareVersions, type ExtensionManifest } from '../extensions/manifest'
import { assertContent, readLocale } from '../extensions/content'
import { defaultGrants, isCapability } from '../extensions/capabilities'

function audit(workspace: Workspace, entry: InstalledPackage, action: ExtensionAudit['action'], context: CommandContext) {
  ;(workspace.extensionAudit ||= []).push({ id: context.id(), packageId: entry.id, kind: entry.kind, action, occurredAt: context.now, capabilities: [...entry.grants] })
}
function fallback(workspace: Workspace, entry: InstalledPackage) {
  if (entry.kind === 'theme' && workspace.preferences.themeId === entry.id) workspace.preferences.themeId = 1
  if (workspace.preferences.fontId.startsWith('pkg:' + entry.kind + ':' + entry.id + ':')) workspace.preferences.fontId = 'default'
  assertManifest(entry.manifest)
  const candidate = { manifest: entry.manifest, payload: entry.payload, checksum: entry.checksum || '' }
  for (const resource of entry.manifest.resources || []) {
    if (resource.kind === 'locale') {
      try { if (readLocale(candidate, resource.path).id === workspace.preferences.locale) workspace.preferences.locale = 'zh-CN' }
      catch { /* A broken resource must remain removable. */ }
    }
  }
}
function status(entry: InstalledPackage, manifest: ExtensionManifest) {
  return manifest.requiredPermissions.every(capability => entry.grants.includes(capability)) ? 'enabled' as const : 'disabled' as const
}
export function applyPackageCommand(workspace: Workspace, command: WorkspaceCommand, context: CommandContext): OperationResult | undefined {
  if (command.type === 'recoverAppearance') {
    for (const entry of workspace.packages) if (entry.status === 'enabled') {
      entry.status = 'disabled'; entry.updatedAt = context.now
      audit(workspace, entry, 'disable', context)
    }
    Object.assign(workspace.preferences, { themeId: 1, fontId: 'default', locale: 'zh-CN', appearance: undefined })
    return {}
  }
  if (command.type === 'packageRuntimeFailure') {
    const entry = workspace.packages.find(item => item.kind === command.kind && item.id === command.packageId && item.checksum === command.checksum)
    if (!entry || entry.status !== 'enabled') return {}
    entry.status = 'broken'; entry.updatedAt = context.now
    fallback(workspace, entry)
    audit(workspace, entry, 'failure', context)
    workspace.extensionAudit!.at(-1)!.detail = command.detail.slice(0, 200)
    return { entityId: String(entry.id) }
  }
  if (command.type === 'installPackage') {
    assertCandidate(command.candidate, workspace.productVersion)
    assertContent(command.candidate)
    const { manifest, payload, checksum } = command.candidate
    const old = command.updateId === undefined ? undefined : workspace.packages.find(item => item.kind === manifest.type && item.id === command.updateId && item.source === 'local')
    requireCondition(command.updateId === undefined || old, 'extensions.packageMissing')
    if (old) {
      assertManifest(old.manifest)
      const name = manifest.name['en-US'] || Object.values(manifest.name)[0]!
      requireCondition(old.author === manifest.author && old.name === name, 'extensions.identityMismatch')
      requireCondition(compareVersions(manifest.version, old.version) > 0, 'extensions.versionNotNewer')
    }
    const used = [...workspace.packages, ...workspace.packageTombstones].filter(item => item.kind === manifest.type).map(item => item.id)
    const id = old?.id ?? Math.max(99999, ...used) + 1
    requireCondition(id <= 999999, 'extensions.idsExhausted')
    const grants = command.grants || (old ? old.grants.filter(isCapability).filter(item => manifest.permissions.includes(item)) : defaultGrants(manifest.permissions))
    requireCondition(grants.every(item => isCapability(item) && manifest.permissions.includes(item)) && new Set(grants).size === grants.length, 'extensions.unknownCapability')
    const entry: InstalledPackage = {
      id, kind: manifest.type, name: manifest.name['en-US'] || Object.values(manifest.name)[0]!,
      author: manifest.author, version: manifest.version, source: 'local', status: 'disabled',
      permissions: [...manifest.permissions], grants: [...grants], manifest: { ...manifest }, payload,
      checksum, installedAt: old?.installedAt || context.now, updatedAt: context.now,
    }
    entry.status = status(entry, manifest)
    if (old) workspace.packages.splice(workspace.packages.indexOf(old), 1, entry)
    else workspace.packages.push(entry)
    if (entry.status !== 'enabled') fallback(workspace, entry)
    audit(workspace, entry, old ? 'upgrade' : 'install', context)
    return { entityId: String(id) }
  }
  if (!['setPackageGrants', 'setPackageStatus', 'removePackage'].includes(command.type)) return undefined
  if (command.type !== 'setPackageGrants' && command.type !== 'setPackageStatus' && command.type !== 'removePackage') return undefined
  const entry = workspace.packages.find(item => item.kind === command.kind && item.id === command.packageId)
  requireCondition(entry && entry.source === 'local', 'extensions.packageMissing')
  assertManifest(entry.manifest)
  if (command.type === 'setPackageGrants') {
    requireCondition(command.grants.every(item => isCapability(item) && entry.permissions.includes(item)) && new Set(command.grants).size === command.grants.length, 'extensions.unknownCapability')
    entry.grants = [...command.grants]
    if (entry.status === 'enabled') entry.status = status(entry, entry.manifest)
    audit(workspace, entry, 'grants', context)
  } else if (command.type === 'setPackageStatus') {
    if (command.enabled) requireCondition(status(entry, entry.manifest) === 'enabled', 'extensions.missingGrant')
    entry.status = command.enabled ? 'enabled' : 'disabled'
    audit(workspace, entry, command.enabled ? 'enable' : 'disable', context)
  } else {
    workspace.packages.splice(workspace.packages.indexOf(entry), 1)
    workspace.packageTombstones.push({ kind: entry.kind, id: entry.id })
    audit(workspace, entry, 'remove', context)
  }
  entry.updatedAt = context.now
  if (command.type === 'removePackage' || entry.status !== 'enabled') fallback(workspace, entry)
  return { entityId: String(entry.id) }
}

