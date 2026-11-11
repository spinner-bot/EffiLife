import { expect, it, vi } from 'vitest'
import JSZip from 'jszip'
import { inspectZip } from '../../src/extensions/zip-structure'
import { openBoundedZip } from '../../src/extensions/bounded-zip'
import { importBudget } from '../../src/extensions/import-budget'
import { inspectArchive } from '../../src/adapters/archive'
import { inspectExtension } from '../../src/adapters/extension-package'

it('rejects cumulative declared output before JSZip loads either import format', async () => {
  const bytes = await new JSZip().file('one', new Uint8Array(60_000)).file('two', new Uint8Array(60_000)).generateAsync({ type: 'uint8array' })
  const budget = { ...importBudget, maxEntryBytes: 70_000, maxExpandedBytes: 100_000 }
  const load = vi.spyOn(JSZip, 'loadAsync')
  try {
    await expect(inspectArchive(bytes, '3.0.1', 'UTC', budget)).rejects.toThrow('archive.importBudget')
    await expect(inspectExtension(bytes, '3.0.1', budget)).rejects.toThrow('archive.importBudget')
    expect(load).not.toHaveBeenCalled()
  } finally { load.mockRestore() }
})

it('stops actual expansion when the central directory lies about its output size', async () => {
  const bytes = await new JSZip().file('payload', new Uint8Array(65_536)).generateAsync({ type: 'uint8array', compression: 'DEFLATE' })
  const view = new DataView(bytes.buffer)
  const central = view.getUint32(bytes.length - 22 + 16, true)
  view.setUint32(central + 24, 1, true)
  view.setUint32(22, 1, true)
  const zip = await openBoundedZip(bytes)
  await expect(zip.readBytes('payload')).rejects.toThrow('archive.importBudget')
})

it('checks CRC on requested files while leaving unreferenced contents compressed', async () => {
  const bytes = await new JSZip().file('payload', 'hello').file('unused', 'retained').generateAsync({ type: 'uint8array' })
  const view = new DataView(bytes.buffer)
  const offset = 30 + view.getUint16(26, true) + view.getUint16(28, true)
  bytes[offset] ^= 1
  const zip = await openBoundedZip(bytes)
  await expect(zip.readText('unused')).resolves.toBe('retained')
  await expect(zip.readBytes('payload')).rejects.toThrow('archive.checksumMismatch')
})

it('rejects extreme compression and input allocations under the configured policy', async () => {
  const bytes = await new JSZip().file('zeros', new Uint8Array(2 * 1024 * 1024)).generateAsync({ type: 'uint8array', compression: 'DEFLATE' })
  expect(() => inspectZip(bytes)).toThrow('archive.compressionRatio')
  await expect(inspectArchive(new Uint8Array(10), '3.0.1', 'UTC', { ...importBudget, maxInputBytes: 5 })).rejects.toThrow('archive.importBudget')
})
