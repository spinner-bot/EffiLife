import { readFileSync } from 'node:fs'
import { expect, it } from 'vitest'
import { changelog, compareVersions, currentRelease, generationFor, productReleases } from '../../src/domain/changelog'

const version = readFileSync('VERSION', 'utf8').trim()

it('exposes a parseable changelog for the in-app version panel', () => {
  expect(changelog.schema).toBe('effilife-changelog/2')
  expect(changelog.locale).toBe('zh-CN')
  expect(Object.keys(changelog.generations)).toEqual(['1', '2', '3'])
  for (const generation of Object.values(changelog.generations)) {
    expect(generation.user.trim()).not.toBe('')
    expect(generation.developer.trim()).not.toBe('')
  }
  for (const product of Object.values(changelog.products)) {
    expect(Object.keys(product.versions).length).toBeGreaterThan(0)
    for (const entry of Object.values(product.versions)) {
      expect(entry.date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
      expect(entry.user.trim()).not.toBe('')
      expect(entry.developer.trim()).not.toBe('')
    }
  }
})

it('indexes every released version with the current one present', () => {
  expect(currentRelease(version)).toMatchObject({ user: expect.any(String), developer: expect.any(String) })
  expect(generationFor('effilife-v3')?.name).toContain('第三代')
  const releases = productReleases('effilife-v3').map(release => release.version)
  expect(releases[0]).toBe(version)
  expect(releases).toContain('3.0.0')
  expect(productReleases('time-helper')).toHaveLength(22)
})

it('orders versions numerically rather than lexically', () => {
  expect(compareVersions('3.10.0', '3.9.0')).toBeGreaterThan(0)
  expect(compareVersions('3.2.2', '3.2.2')).toBe(0)
  expect(compareVersions('3.2.1', '3.2.2')).toBeLessThan(0)
})
