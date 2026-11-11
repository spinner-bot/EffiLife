import { createHash } from 'node:crypto'
import { expect, test } from '@playwright/test'
import { frameFixture } from '../helpers/frame-fixture'

for (const [label, eol] of [['LF', '\n'], ['CRLF', '\r\n'], ['CR', '\r']] as const) {
  test('runs the opaque frame with browser-normalized CSP bytes after a ' + label + ' checkout', async ({ page }) => {
    const fixture = frameFixture(eol)
    const errors: string[] = []
    page.on('pageerror', error => errors.push(error.message))
    page.on('console', entry => { if (['warning', 'error'].includes(entry.type())) errors.push(entry.text()) })
    try {
      fixture.run('--check')
      fixture.run()
      // Simulate a second checkout of generated HTML, then let the real
      // browser normalize its script text before executing the CSP gate.
      const html = fixture.read('public/extension-frame.html').replaceAll('\n', eol)
      const config = JSON.parse(fixture.read('apps/desktop/src-tauri/tauri.conf.json'))
      await page.route('**/extension-frame.html', route => route.fulfill({
        body: html,
        contentType: 'text/html; charset=utf-8',
        headers: { 'Content-Security-Policy': config.app.security.csp },
      }))
      await page.goto('/#/more/appearance')
      await page.getByRole('button', { name: '北欧极夜', exact: true }).click()
      await expect(page.locator('.theme-decoration iframe')).toHaveAttribute('data-ready', 'true')
      const frame = page.frameLocator('.theme-decoration iframe')
      const parsed = (await frame.locator('script').textContent())!
      const hash = 'sha256-' + createHash('sha256').update(parsed).digest('base64')
      expect(parsed).not.toContain('\r')
      expect(await frame.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute('content')).toContain("'" + hash + "'")
      expect(config.app.security.csp).toContain("'" + hash + "'")
      expect(errors).toEqual([])
    } finally { fixture.dispose() }
  })
}
