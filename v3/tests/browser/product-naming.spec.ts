import { test, expect } from '@playwright/test'

test('the shell and tab title follow the product name of the active locale', async ({ page }) => {
  await page.goto('/#/')
  await expect(page.locator('.brand')).toHaveText('浪兮效率生活')
  await expect(page.locator('.sidebar-version')).toHaveText(/^浪兮效率生活 v\d+\.\d+\.\d+$/)
  await expect(page).toHaveTitle('总览 · 浪兮效率生活')

  await page.goto('/#/more/settings')
  await page.getByRole('combobox', { name: '语言', exact: true }).selectOption('en-US')
  await expect(page.locator('.brand')).toHaveText('EffiLife')
  await expect(page.locator('.breadcrumb')).toContainText('EffiLife')
  await expect(page).toHaveTitle('Make it feel like yours. · EffiLife')
})
