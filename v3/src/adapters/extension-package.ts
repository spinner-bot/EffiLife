import { openBoundedZip } from '../extensions/bounded-zip'
import { importBudget, type ImportBudget } from '../extensions/import-budget'
import { assertCandidate, assertManifest, type PackageCandidate } from '../extensions/manifest'
import { requireCondition, DomainError } from '../domain/errors'
import { sha256 } from './archive'

function base64(bytes: Uint8Array): string {
  let result = ''
  for (let offset = 0; offset < bytes.length; offset += 32768) result += String.fromCharCode(...bytes.subarray(offset, offset + 32768))
  return btoa(result)
}
export async function inspectExtension(bytes: Uint8Array, appVersion: string, budget: ImportBudget = importBudget): Promise<PackageCandidate> {
  try {
    const zip = await openBoundedZip(bytes, budget)
    requireCondition(zip.has('manifest.json'), 'archive.manifestMissing')
    const manifest: unknown = JSON.parse(await zip.readText('manifest.json'))
    assertManifest(manifest, appVersion)
    const payload: Record<string, string> = Object.create(null)
    for (const name of zip.names) {
      if (name === 'manifest.json') continue
      const content = await zip.readBytes(name)
      if (manifest.checksums?.[name]) requireCondition(await sha256(content) === manifest.checksums[name], 'archive.checksumMismatch')
      payload[name] = base64(content)
    }
    for (const path of Object.keys(manifest.checksums || {})) requireCondition(Object.hasOwn(payload, path), 'archive.payloadMissing')
    const candidate = { manifest, payload, checksum: await sha256(bytes) }
    assertCandidate(candidate, appVersion)
    return candidate
  } catch (error) {
    if (error instanceof DomainError) throw error
    throw new DomainError('extensions.invalidPayload')
  }
}

