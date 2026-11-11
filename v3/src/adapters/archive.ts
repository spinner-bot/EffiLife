import JSZip from 'jszip'
import type { Workspace } from '../domain/models'
import { assertWorkspace, isObject } from '../domain/validation'
import { requireCondition, DomainError } from '../domain/errors'
import { openBoundedZip } from '../extensions/bounded-zip'
import { checkImportInput, importBudget, type ImportBudget } from '../extensions/import-budget'
import { importLegacy } from './legacy-import'
import { extensionFor } from '../extensions/formats'
import { requireArchiveConsent } from '../extensions/archive-consent'

export interface ArchivePreview {
  workspace: Workspace
  warnings: string[]
  source: 'v3' | 'legacy'
  counts: { plans: number; archivedPlans: number; tasks: number; logs: number; records: number; todos: number }
}

export async function sha256(bytes: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', Uint8Array.from(bytes).buffer)
  return [...new Uint8Array(digest)].map(value => value.toString(16).padStart(2, '0')).join('')
}

export async function exportArchive(workspace: Workspace, version: string): Promise<{ bytes: Uint8Array; filename: string }> {
  assertWorkspace(workspace)
  const zip = new JSZip()
  const path = 'payload/workspace.json'
  const payload = new TextEncoder().encode(JSON.stringify(workspace, null, 2))
  const manifest = {
    type: 'data', formatVersion: 1, schemaVersion: workspace.schemaVersion, appVersion: version,
    exportedAt: new Date().toISOString(), dataFiles: [path], checksums: { [path]: await sha256(payload) },
  }
  zip.file('manifest.json', JSON.stringify(manifest, null, 2))
  zip.file(path, payload)
  const bytes = await zip.generateAsync({ type: 'uint8array', compression: 'DEFLATE' })
  const stamp = manifest.exportedAt.replaceAll(/[:.]/g, '-')
  return { bytes, filename: 'EffiLife-' + stamp + '.' + extensionFor('data') }
}

function preview(workspace: Workspace, source: ArchivePreview['source'], warnings: string[]): ArchivePreview {
  assertWorkspace(workspace)
  return {
    workspace, source, warnings,
    counts: {
      plans: workspace.plans.filter(plan => !plan.archivedAt).length,
      archivedPlans: workspace.plans.filter(plan => plan.archivedAt).length,
      tasks: workspace.plans.reduce((sum, plan) => sum + plan.nodes.filter(node => node.kind === 'task').length, 0),
      logs: workspace.plans.reduce((sum, plan) => sum + plan.logs.length, 0),
      records: workspace.records.length, todos: workspace.todos.length,
    },
  }
}

async function parseZip(bytes: Uint8Array, budget: ImportBudget): Promise<unknown> {
  const zip = await openBoundedZip(bytes, budget)
  if (!zip.has('manifest.json')) {
    requireCondition(zip.has('archive.json'), 'archive.manifestMissing')
    return JSON.parse(await zip.readText('archive.json'))
  }
  const manifest: unknown = JSON.parse(await zip.readText('manifest.json'))
  requireCondition(isObject(manifest), 'archive.manifestInvalid')
  if (manifest.type === 'data') {
    requireCondition(manifest.formatVersion === 1 && manifest.schemaVersion === 1 && Array.isArray(manifest.dataFiles) && isObject(manifest.checksums), 'archive.unsupportedFormat')
    requireCondition(manifest.dataFiles.length === 1 && typeof manifest.dataFiles[0] === 'string', 'archive.manifestInvalid')
    const path = manifest.dataFiles[0]
    const content = await zip.readBytes(path)
    requireCondition(typeof manifest.checksums[path] === 'string' && await sha256(content) === manifest.checksums[path], 'archive.checksumMismatch')
    const data = JSON.parse(new TextDecoder().decode(content))
    assertWorkspace(data)
    return data
  }
  requireCondition(manifest.format === 'effilife.bundle' && manifest.format_version === '1.0.0' && Array.isArray(manifest.datasets), 'archive.unsupportedFormat')
  const datasets: Record<string, unknown> = {}
  const seen = new Set<string>()
  for (const name of manifest.datasets) {
    requireCondition(typeof name === 'string' && /^[a-zA-Z0-9_-]+$/.test(name) && !seen.has(name), 'archive.manifestInvalid')
    seen.add(name)
    const content = await zip.readBytes('data/' + name + '.json')
    if (manifest.dataset_sha256 !== undefined) {
      requireCondition(isObject(manifest.dataset_sha256) && typeof manifest.dataset_sha256[name] === 'string' && await sha256(content) === manifest.dataset_sha256[name], 'archive.checksumMismatch')
    }
    datasets[name] = JSON.parse(new TextDecoder().decode(content))
  }
  requireCondition(isObject(datasets.app) && Array.isArray(datasets.todos) && isObject(datasets.records || datasets.time_records), 'archive.manifestInvalid')
  return datasets
}

export async function inspectArchive(
  bytes: Uint8Array, version: string, timeZone: string, budget: ImportBudget = importBudget,
): Promise<ArchivePreview> {
  let input: unknown
  try {
    checkImportInput(bytes.byteLength, budget)
    const beginning = new TextDecoder().decode(bytes.subarray(0, 20)).trimStart()
    input = beginning.startsWith('{') ? JSON.parse(new TextDecoder().decode(bytes)) : await parseZip(bytes, budget)
  } catch (error) {
    if (error instanceof DomainError) throw error
    throw new DomainError('archive.invalidFile')
  }
  if (isObject(input) && input.schemaVersion !== undefined) {
    assertWorkspace(input)
    const consent = requireArchiveConsent(input)
    return preview(consent.workspace, 'v3', consent.changed ? ['extensions.importConsent'] : [])
  }
  requireCondition(isObject(input) && (
    isObject(input.records) || isObject(input.app) || isObject(input.planHelper) || isObject(input.plan_helper) || Array.isArray(input.main) || Array.isArray(input.todos)
  ), 'archive.unsupportedFormat')
  const imported = importLegacy(input, version, timeZone)
  return preview(imported.workspace, 'legacy', imported.warnings)
}

