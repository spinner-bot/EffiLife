import JSZip from 'jszip'
import { inspectZip } from '../extensions/zip-structure'
import { assertCandidate, assertManifest, type PackageCandidate } from '../extensions/manifest'
import { requireCondition, DomainError } from '../domain/errors'
import { sha256 } from './archive'

function base64(bytes: Uint8Array): string {
  let result = ''
  for (let offset = 0; offset < bytes.length; offset += 32768) result += String.fromCharCode(...bytes.subarray(offset, offset + 32768))
  return btoa(result)
}
export async function inspectExtension(bytes: Uint8Array, appVersion: string): Promise<PackageCandidate> {
  try {
    inspectZip(bytes)
    const zip = await JSZip.loadAsync(bytes, { checkCRC32: true })
    const entry = zip.file('manifest.json')
    requireCondition(entry, 'archive.manifestMissing')
    const manifest: unknown = JSON.parse(await entry.async('string'))
    assertManifest(manifest, appVersion)
    const payload: Record<string, string> = Object.create(null)
    for (const file of Object.values(zip.files)) {
      if (file.dir || file.name === 'manifest.json') continue
      const content = await file.async('uint8array')
      if (manifest.checksums?.[file.name]) requireCondition(await sha256(content) === manifest.checksums[file.name], 'archive.checksumMismatch')
      payload[file.name] = base64(content)
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

