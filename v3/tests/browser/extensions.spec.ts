import { test, expect, type Page } from '@playwright/test'
import { readFile } from 'node:fs/promises'
import JSZip from 'jszip'
import { extensionFor } from '../../src/extensions/formats'
import type { ExtensionManifest } from '../../src/extensions/manifest'

const errors = new WeakMap<Page, string[]>()
test.beforeEach(({ page }) => {
  const list: string[] = []; errors.set(page, list)
  page.on('pageerror', error => list.push(error.message))
  page.on('console', message => { if (['error', 'warning'].includes(message.type())) list.push(message.text()) })
})
test.afterEach(({ page }) => { expect(errors.get(page)).toEqual([]) })
async function upload(page: Page, manifest: ExtensionManifest, files: Record<string, string | Uint8Array>) {
  const zip = new JSZip().file('manifest.json', JSON.stringify(manifest))
  for (const [path, bytes] of Object.entries(files)) zip.file(path, bytes)
  await page.getByLabel('安装扩展包', { exact: true }).setInputFiles({
    name: 'example.' + extensionFor(manifest.type), mimeType: 'application/zip', buffer: Buffer.from(await zip.generateAsync({ type: 'uint8array' })),
  })
  const dialog = page.getByRole('dialog', { name: '检查即将安装的扩展' })
  await expect(dialog).toBeVisible()
  await dialog.getByRole('button', { name: '确认安装', exact: true }).click()
  await expect(dialog).not.toBeVisible()
}
test('installs a local theme, grants visual CSS, revokes it and recovers on uninstall', async ({ page }) => {
  await page.goto('/#/settings')
  await upload(page, {
    type: 'theme', name: { 'zh-CN': '森林', 'en-US': 'Forest' }, author: 'Example', license: 'MIT', version: '1.0.0', formatVersion: 1, apiVersion: 1,
    permissions: ['appearance.tokens', 'appearance.css'], requiredPermissions: ['appearance.tokens'], tokens: 'tokens.json', styles: ['styles/main.css'],
  }, {
    'tokens.json': JSON.stringify({ palette: { background: '#102a20', surface: '#17382c', text: '#ffffff', accent: '#47b894' } }),
    'styles/main.css': '.panel { border-radius: 28px; }',
  })
  await page.goto('/#/more/appearance')
  const theme = page.getByRole('button', { name: '森林 · Example · 1.0.0 · #100000', exact: true })
  await theme.click()
  await expect(theme).toHaveAttribute('aria-pressed', 'true')
  await expect(page.locator('.panel').first()).toHaveCSS('border-radius', '14px')
  await page.goto('/#/more/settings')
  const row = page.locator('.list-row').filter({ has: page.getByText('森林', { exact: true }) })
  await row.getByRole('button', { name: '权限', exact: true }).click()
  let dialog = page.getByRole('dialog', { name: '权限', exact: true })
  await dialog.getByRole('checkbox', { name: '视觉样式增强' }).check()
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await expect(dialog).not.toBeVisible()
  await expect(page.locator('.panel').first()).toHaveCSS('border-radius', '28px')
  await page.reload()
  await expect(page.locator('.panel').first()).toHaveCSS('border-radius', '28px')
  await row.getByRole('button', { name: '权限', exact: true }).click()
  dialog = page.getByRole('dialog', { name: '权限', exact: true })
  await dialog.getByRole('checkbox', { name: '视觉样式增强' }).uncheck()
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await expect(page.locator('.panel').first()).toHaveCSS('border-radius', '14px')
  await row.getByRole('button', { name: '删除: 森林', exact: true }).click()
  await page.getByRole('dialog', { name: '卸载「森林」？' }).getByRole('button', { name: '确认', exact: true }).click()
  await page.goto('/#/more/appearance')
  await expect(theme).toHaveCount(0)
  await expect(page.getByRole('button', { name: '浅色', exact: true })).toHaveAttribute('aria-pressed', 'true')
})
test('loads packaged locale and font bytes and restores defaults when disabled', async ({ page }) => {
  await page.goto('/#/settings')
  const bytes = await readFile('node_modules/@fontsource-variable/inter/files/inter-latin-wght-normal.woff2')
  await upload(page, {
    type: 'resource', name: { 'zh-CN': '法语与字体', 'en-US': 'French resources' }, author: 'Example', license: 'OFL-1.1', version: '1.0.0', formatVersion: 1, apiVersion: 1,
    permissions: ['resources.register'], requiredPermissions: ['resources.register'], resources: [
      { kind: 'locale', alias: 'french', path: 'locales/fr.json', name: 'Français', license: 'MIT' },
      { kind: 'font', alias: 'reading', path: 'fonts/reading.woff2', name: 'Reading font', license: 'OFL-1.1' },
    ],
  }, { 'locales/fr.json': JSON.stringify({ id: 'fr-FR', direction: 'ltr', messages: { 'nav.home': 'Mon quotidien' } }), 'fonts/reading.woff2': bytes })
  await page.goto('/#/more/appearance')
  await page.getByRole('combobox', { name: '字体', exact: true }).selectOption('pkg:resource:100000:reading')
  await expect.poll(() => page.evaluate(() => document.documentElement.style.getPropertyValue('--font-body'))).toContain('EffiLife_resource_100000_reading')
  expect(await page.evaluate(() => document.fonts.check('15px "EffiLife_resource_100000_reading"'))).toBe(true)
  await page.goto('/#/more/settings')
  await page.getByRole('combobox', { name: '语言', exact: true }).selectOption('fr-FR')
  await expect(page.getByRole('link', { name: 'Mon quotidien', exact: true })).toBeVisible()
  await page.reload()
  await expect(page.getByRole('link', { name: 'Mon quotidien', exact: true })).toBeVisible()
  const row = page.locator('.list-row').filter({ has: page.getByText('French resources', { exact: true }) })
  await row.getByRole('button', { name: 'Disable', exact: true }).click()
  await expect(page.getByRole('combobox', { name: '语言', exact: true })).toHaveValue('zh-CN')
  await expect(page.getByRole('option', { name: 'Français', exact: true })).toHaveCount(0)
  await page.goto('/#/more/appearance')
  await expect(page.getByRole('combobox', { name: '字体', exact: true })).toHaveValue('default')
})

