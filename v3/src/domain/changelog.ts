import data from '../data/changelog.json'

export interface ChangelogEntry { date: string; user: string; developer: string; note?: string }
export interface ChangelogGeneration { name: string; date: string; user: string; developer: string }
export interface ChangelogProduct { name: string; generation: number; versions: Record<string, ChangelogEntry> }
export interface Changelog {
  schema: string
  locale: string
  description: string
  updated: string
  generations: Record<string, ChangelogGeneration>
  products: Record<string, ChangelogProduct>
}

export const changelog = data as Changelog
export const currentProductId = 'effilife-v3'

export function compareVersions(left: string, right: string): number {
  const a = left.split('.').map(Number)
  const b = right.split('.').map(Number)
  for (let index = 0; index < Math.max(a.length, b.length); index += 1) {
    const difference = (a[index] ?? 0) - (b[index] ?? 0)
    if (difference) return difference
  }
  return 0
}

export function productReleases(productId: string): Array<ChangelogEntry & { version: string }> {
  const product = changelog.products[productId]
  if (!product) return []
  return Object.entries(product.versions)
    .map(([version, entry]) => ({ version, ...entry }))
    .sort((left, right) => compareVersions(right.version, left.version))
}

export function releaseFor(productId: string, version: string): ChangelogEntry | undefined {
  return changelog.products[productId]?.versions[version]
}

export function generationFor(productId: string): ChangelogGeneration | undefined {
  return changelog.generations[String(changelog.products[productId]?.generation)]
}

export function currentRelease(version: string, productId = currentProductId) {
  return releaseFor(productId, version)
}
