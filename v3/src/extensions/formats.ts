import formats from '../../shared/package-formats.json'
export type PackageKind = keyof typeof formats.formats
export const packageFormats = formats.formats
export function extensionFor(kind: PackageKind): string { return packageFormats[kind].current }
export function acceptedExtensions(kind: PackageKind): string[] { return packageFormats[kind].accepted }
export function acceptsFilename(kind: PackageKind, filename: string): boolean {
  const extension = filename.split('.').pop()?.toLowerCase() || ''
  return acceptedExtensions(kind).includes(extension)
}

