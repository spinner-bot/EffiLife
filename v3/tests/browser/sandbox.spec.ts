import { test, expect, type Page } from '@playwright/test'
import JSZip from 'jszip'
import catalog from '../../resources/themes/catalog.json' with { type: 'json' }
import { extensionFor } from '../../src/extensions/formats'
import type { Capability } from '../../src/extensions/capabilities'

const errors = new WeakMap<Page, string[]>()
const policyBlocks = new WeakMap<Page, string[]>()
test.beforeEach(({ page }, info) => {
  const list: string[] = []; errors.set(page, list)
  policyBlocks.set(page, [])
  page.on('pageerror', error => list.push(error.message))
  page.on('console', message => {
    if (!['error', 'warning'].includes(message.type())) return
    if (info.title.includes('CSP') && message.text().includes('extension-network-probe') && /content security policy/i.test(message.text())) policyBlocks.get(page)!.push(message.text())
    else list.push(message.text())
  })
})
test.afterEach(({ page }) => { expect(errors.get(page)).toEqual([]) })
async function install(page: Page, source: string, grants: Capability[], type: 'theme' | 'function' = 'theme') {
  const permissions: Capability[] = type === 'theme' ? ['appearance.tokens', ...grants] : grants
  const manifest = {
    type, name: { 'zh-CN': '隔离界面', 'en-US': 'Isolated UI' }, author: 'Example', license: 'MIT', version: '1.0.0', formatVersion: 1, apiVersion: 1,
    permissions, requiredPermissions: permissions,
    ...(type === 'theme' ? { tokens: 'tokens.json', scripts: ['scripts/main.js'] } : { entry: 'scripts/main.js' }),
  }
  const zip = new JSZip().file('manifest.json', JSON.stringify(manifest)).file('scripts/main.js', source)
  if (type === 'theme') zip.file('tokens.json', JSON.stringify({ palette: { accent: '#5370cb' } }))
  await page.goto('/#/settings')
  await page.getByLabel('安装扩展包', { exact: true }).setInputFiles({ name: 'sandbox.' + extensionFor(type), mimeType: 'application/zip', buffer: Buffer.from(await zip.generateAsync({ type: 'uint8array' })) })
  const dialog = page.getByRole('dialog', { name: '检查即将安装的扩展' })
  await expect(dialog).toBeVisible()
  await expect(dialog.getByRole('checkbox')).toHaveCount(permissions.length)
  for (const checkbox of await dialog.getByRole('checkbox').all()) await checkbox.check()
  await dialog.getByRole('button', { name: '确认安装', exact: true }).click()
  if (grants.some(capability => capability.startsWith('app.'))) await page.getByRole('dialog', { name: '允许此扩展访问应用系统？' }).getByRole('button', { name: '确认', exact: true }).click()
  await expect(dialog).not.toBeVisible()
  if (type === 'theme') await page.getByRole('button', { name: '隔离界面 · Example · 1.0.0 · #100000', exact: true }).click()
}
test('runs all retained built-in decorative renderers in opaque worker frames', async ({ page }, info) => {
  await page.goto('/#/settings')
  for (const theme of catalog) {
    await page.getByRole('button', { name: theme.name['zh-CN'], exact: true }).click()
    const frame = page.locator('.theme-decoration iframe')
    if (theme.decoration.renderer || theme.decoration.particles || theme.decoration.gradient) {
      await expect(frame).toHaveAttribute('sandbox', 'allow-scripts')
      await expect(frame).toHaveAttribute('data-ready', 'true')
    } else await expect(frame).toHaveCount(0)
  }
  await page.screenshot({ path: info.outputPath('retained-decoration-1440.png'), fullPage: true })
})
test('lets an authorized replacement layout write through the audited host API and recover', async ({ page }) => {
  await install(page, `
EffiLife.onMount(async () => {
  const data = await EffiLife.request('data.read');
  const isolated = [typeof document, typeof indexedDB, typeof fetch].every(value => value === 'undefined');
  EffiLife.render({html: '<main><h1>Isolated life view</h1><p id="isolation">' + isolated + ' / registry hidden: ' + !('packages' in data) + '</p><button data-action="add">Add plan</button></main>', css: 'main{padding:40px;color:#172033;background:#f8fafc;min-height:100vh}button{padding:12px}'});
});
EffiLife.onAction(async event => {
  if(event.name === 'add') {
    await EffiLife.request('data.write', {type:'createPlan', title:'由扩展创建的计划'});
    EffiLife.render({html:'<h1>Saved through host</h1>',css:'h1{padding:40px;color:#172033}'});
  }
});
`, ['app.layout', 'app.data.read', 'app.data.write'])
  const frame = page.frameLocator('.theme-replacement iframe')
  await expect(frame.getByRole('heading', { name: 'Isolated life view' })).toBeVisible()
  await expect(frame.locator('#isolation')).toHaveText('true / registry hidden: true')
  await frame.getByRole('button', { name: 'Add plan' }).click()
  await expect(frame.getByRole('heading', { name: 'Saved through host' })).toBeVisible()
  await page.getByRole('button', { name: '恢复默认外观与停用扩展' }).click()
  await expect(page.locator('.theme-replacement')).toHaveCount(0)
  await page.goto('/#/plans')
  await expect(page.getByRole('link', { name: /由扩展创建的计划/ })).toBeVisible()
})
test('rejects ungranted writes while preserving the recoverable layout', async ({ page }) => {
  await install(page, `
EffiLife.onMount(async () => {
  let result = 'unexpected success';
  try { await EffiLife.request('data.write', {type:'createPlan',title:'Forbidden'}); }
  catch(error) { result = error.code; }
  EffiLife.render({html:'<h1>' + result + '</h1>',css:'h1{padding:32px;color:#172033}'});
});
`, ['app.layout'])
  await expect(page.frameLocator('.theme-replacement iframe').getByRole('heading')).toHaveText('extensions.permissionDenied')
  await page.getByRole('button', { name: '恢复默认外观与停用扩展' }).click()
  await page.goto('/#/plans')
  await expect(page.getByRole('link', { name: /Forbidden/ })).toHaveCount(0)
})
test('terminates a stuck worker without freezing the host and keeps it stopped after reload', async ({ page }) => {
  await install(page, 'while (true) {}', ['overlay.canvas'], 'function')
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  const row = page.locator('.list-row').filter({ has: page.getByText('隔离界面', { exact: true }) })
  await expect(row).toContainText('加载失败', { timeout: 25000 })
  await expect(page.locator('.theme-decoration iframe')).toHaveCount(0)
  await page.reload()
  await expect(row).toContainText('加载失败')
  await expect(page.locator('.theme-decoration iframe')).toHaveCount(0)
})

test('enforces opaque origins and CSP even against native network API recovery', async ({ page }) => {
  const requests: string[] = []
  await page.route('**/extension-network-probe', route => { requests.push(route.request().url()); return route.fulfill({ body: 'unexpected network access' }) })
  await install(page, `
EffiLife.onMount(async () => {
  let proto = self, nativeFetch;
  while(proto) { const descriptor = Object.getOwnPropertyDescriptor(proto, 'fetch'); if(typeof descriptor?.value === 'function') nativeFetch = descriptor.value; proto = Object.getPrototypeOf(proto); }
  let network = 'unavailable';
  if(nativeFetch) { try { await nativeFetch.call(self, 'http://127.0.0.1:3420/extension-network-probe'); network = 'unexpected'; } catch { network = 'blocked'; } }
  EffiLife.render({html:'<main><h1>Security probe</h1><p id="network">' + network + '</p><img src="http://127.0.0.1:3420/extension-network-probe"><script>parent.document.body.innerHTML="escaped"</script><a href="http://127.0.0.1:3420/extension-network-probe">escape</a></main>',css:'main{padding:32px;color:#172033}'});
});
`, ['app.layout'])
  const locator = page.frameLocator('.theme-replacement iframe')
  await expect(locator.getByRole('heading')).toHaveText('Security probe')
  await expect(locator.locator('#network')).toHaveText(/blocked|unavailable/)
  await expect(locator.locator('img,a')).toHaveCount(0)
  const frame = page.frames().find(frame => frame.parentFrame())!
  const result = await frame.evaluate(async () => {
    const denied = (read: () => unknown) => { try { read(); return false } catch (error) { return (error as Error).name === 'SecurityError' } }
    let network = false
    try { await fetch('http://127.0.0.1:3420/extension-network-probe') } catch { network = true }
    return { parent: denied(() => parent.document), local: denied(() => localStorage), indexed: denied(() => indexedDB.open('forbidden')), network }
  })
  expect(result).toEqual({ parent: true, local: true, indexed: true, network: true })
  expect(requests).toEqual([])
  expect(policyBlocks.get(page)!.length).toBeGreaterThan(0)
  await page.goto('/?safe=1#/settings')
  await expect(page.getByText('安全模式：扩展暂未加载', { exact: true })).toBeVisible()
  await expect(page.locator('.extension-frame')).toHaveCount(0)
  const row = page.locator('.list-row').filter({ has: page.getByText('隔离界面', { exact: true }) })
  await expect(row).toContainText('已启用')
  await page.getByRole('button', { name: '恢复默认外观与停用扩展' }).click()
  await expect(page).not.toHaveURL(/safe=1/)
  await expect(row).toContainText('已停用')
})

