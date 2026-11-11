import JSZip from 'jszip'
import { DomainError, requireCondition } from '../domain/errors'
import { inspectZip } from './zip-structure'
import { importBudget, type ImportBudget } from './import-budget'

// JSZip 3.10.2 exposes this documented API but omits it from JSZipObject's
// bundled types. Keep that compatibility declaration at the adapter boundary.
type StreamingEntry = JSZip.JSZipObject & { internalStream(type: 'uint8array'): JSZip.JSZipStreamHelper<Uint8Array> }
const crcTable = Uint32Array.from({ length: 256 }, (_, index) => {
  let value = index
  for (let bit = 0; bit < 8; bit++) value = value & 1 ? 0xedb88320 ^ value >>> 1 : value >>> 1
  return value >>> 0
})

export async function openBoundedZip(bytes: Uint8Array, budget: ImportBudget = importBudget) {
  const entries = inspectZip(bytes, budget)
  // checkCRC32:true eagerly inflates every entry. Verify CRC ourselves while
  // streaming only requested files, under declared and actual byte budgets.
  const zip = await JSZip.loadAsync(bytes, { checkCRC32: false })
  for (const file of Object.values(zip.files)) requireCondition(entries.has(file.name), 'archive.invalidZip')
  let expanded = 0
  const cached = new Map<string, Promise<Uint8Array>>()
  function has(name: string) { return Boolean(zip.file(name)) }
  function readBytes(name: string): Promise<Uint8Array> {
    const known = cached.get(name)
    if (known) return known
    const file = zip.file(name), entry = entries.get(name)
    requireCondition(file && entry, 'archive.payloadMissing')
    const result = new Promise<Uint8Array>((resolve, reject) => {
      const chunks: Uint8Array[] = []
      let size = 0, crc = 0xffffffff, settled = false
      const stream = (file as StreamingEntry).internalStream('uint8array')
      function fail(error: unknown) {
        if (settled) return
        settled = true
        stream.pause()
        chunks.length = 0
        reject(error)
      }
      stream.on('data', chunk => {
        if (settled) return
        size += chunk.byteLength
        expanded += chunk.byteLength
        if (size > entry.original || size > budget.maxEntryBytes || expanded > budget.maxExpandedBytes) { fail(new DomainError('archive.importBudget')); return }
        for (const byte of chunk) crc = crcTable[(crc ^ byte) & 255]! ^ crc >>> 8
        chunks.push(chunk)
      }).on('error', error => fail(error instanceof DomainError ? error : new DomainError('archive.invalidZip'))).on('end', () => {
        if (settled) return
        if (size !== entry.original || ((crc ^ 0xffffffff) >>> 0) !== entry.crc32) { fail(new DomainError('archive.checksumMismatch')); return }
        const content = new Uint8Array(size)
        let offset = 0
        for (const chunk of chunks) { content.set(chunk, offset); offset += chunk.byteLength }
        settled = true
        chunks.length = 0
        resolve(content)
      }).resume()
    })
    cached.set(name, result)
    return result
  }
  return { names: [...entries.keys()].filter(name => !name.endsWith('/')), has, readBytes, readText: async (name: string) => new TextDecoder().decode(await readBytes(name)) }
}
