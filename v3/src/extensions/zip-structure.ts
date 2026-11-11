import { requireCondition } from '../domain/errors'
import { checkImportInput, importBudget, type ImportBudget } from './import-budget'

export interface ZipEntry { name: string; original: number; crc32: number }
/** Bound declared allocations before any entry is decompressed. */
export function inspectZip(bytes: Uint8Array, budget: ImportBudget = importBudget): Map<string, ZipEntry> {
  checkImportInput(bytes.byteLength, budget)
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
  const safe32 = (offset: number) => offset >= 0 && offset + 4 <= bytes.length ? view.getUint32(offset, true) : -1
  let end = -1
  for (let index = bytes.length - 22; index >= Math.max(0, bytes.length - 65557); index--) {
    if (safe32(index) === 0x06054b50 && index + 22 + view.getUint16(index + 20, true) === bytes.length) { end = index; break }
  }
  requireCondition(end >= 0, 'archive.invalidZip')
  requireCondition(view.getUint16(end + 4, true) === 0 && view.getUint16(end + 6, true) === 0, 'archive.unsupportedZip')
  const count = view.getUint16(end + 10, true)
  requireCondition(count > 0 && count <= budget.maxEntries && view.getUint16(end + 8, true) === count, 'archive.entryCount')
  let position = safe32(end + 16)
  requireCondition(position >= 0 && position + safe32(end + 12) === end, 'archive.invalidZip')
  const names = new Set<string>()
  const entries = new Map<string, ZipEntry>()
  let expanded = 0
  for (let index = 0; index < count; index++) {
    requireCondition(safe32(position) === 0x02014b50 && position + 46 <= end, 'archive.invalidZip')
    const flags = view.getUint16(position + 8, true)
    requireCondition(!(flags & 1), 'archive.encryptedZip')
    const compressed = safe32(position + 20)
    const original = safe32(position + 24)
    const method = view.getUint16(position + 10, true)
    requireCondition((method === 0 || method === 8) && original !== 0xffffffff && compressed !== 0xffffffff, 'archive.unsupportedZip')
    expanded += original
    requireCondition(original <= budget.maxEntryBytes && expanded <= budget.maxExpandedBytes, 'archive.importBudget')
    const nameLength = view.getUint16(position + 28, true)
    const extraLength = view.getUint16(position + 30, true)
    const commentLength = view.getUint16(position + 32, true)
    const mode = view.getUint32(position + 38, true) >>> 16
    requireCondition((mode & 0xf000) !== 0xa000, 'archive.symlink')
    requireCondition(position + 46 + nameLength + extraLength + commentLength <= end, 'archive.invalidZip')
    const name = new TextDecoder().decode(bytes.subarray(position + 46, position + 46 + nameLength)).replaceAll('\\', '/')
    requireCondition(name.length > 0 && !name.startsWith('/') && !/^[a-z]:/i.test(name) && !name.split('/').includes('..') && !name.includes('\0'), 'archive.unsafePath')
    const normalized = name.toLowerCase()
    requireCondition(!names.has(normalized), 'archive.duplicateEntry')
    names.add(normalized)
    requireCondition(original < budget.ratioCheckFromBytes || original / Math.max(1, compressed) <= budget.maxCompressionRatio, 'archive.compressionRatio')
    const local = safe32(position + 42)
    requireCondition(safe32(local) === 0x04034b50 && local + 30 <= safe32(end + 16), 'archive.invalidZip')
    const localNameLength = view.getUint16(local + 26, true)
    const localExtraLength = view.getUint16(local + 28, true)
    const data = local + 30 + localNameLength + localExtraLength
    requireCondition(data + compressed <= safe32(end + 16) && view.getUint16(local + 8, true) === method && view.getUint16(local + 6, true) === flags, 'archive.invalidZip')
    requireCondition(localNameLength === nameLength && bytes.subarray(local + 30, local + 30 + localNameLength).every((value, offset) => value === bytes[position + 46 + offset]), 'archive.invalidZip')
    entries.set(name, { name, original, crc32: safe32(position + 16) })
    position += 46 + nameLength + extraLength + commentLength
  }
  requireCondition(position === safe32(end + 16) + safe32(end + 12), 'archive.invalidZip')
  return entries
}

