import { test, expect, type Page } from '@playwright/test'

const browserErrors = new WeakMap<Page, string[]>()
test.beforeEach(async ({ page }) => {
  const errors: string[] = []
  browserErrors.set(page, errors)
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error' || message.type() === 'warning') errors.push(message.text()) })
})
test.afterEach(async ({ page }) => { expect(browserErrors.get(page)).toEqual([]) })

async function createPlan(page: Page, title = '数学课程复习') {
  await page.goto('/#/plans')
  await page.getByRole('button', { name: '新建计划', exact: true }).first().click()
  const dialog = page.getByRole('dialog', { name: '开始一份主题计划' })
  await dialog.getByLabel('名称', { exact: true }).fill(title)
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await expect(page.getByRole('heading', { level: 1, name: title })).toBeVisible()
}

async function createTask(page: Page) {
  await createPlan(page)
  await page.getByRole('button', { name: '添加章节', exact: true }).first().click()
  let dialog = page.getByRole('dialog', { name: '添加章节', exact: true })
  await dialog.getByLabel('名称', { exact: true }).fill('微积分')
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await expect(dialog).not.toBeVisible()
  await page.getByRole('button', { name: '更多操作', exact: true }).first().click()
  await page.getByRole('menuitem', { name: '添加子项', exact: true }).click()
  dialog = page.getByRole('dialog', { name: '添加子项', exact: true })
  await dialog.getByLabel('名称', { exact: true }).fill('极限与连续')
  await dialog.getByLabel('预计用时（分钟）').fill('60')
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await expect(dialog).not.toBeVisible()
  await page.getByRole('button', { name: '更多操作', exact: true }).first().click()
  await page.getByRole('menuitem', { name: '统一设置时间类别', exact: true }).click()
  dialog = page.getByRole('dialog', { name: '统一设置时间类别', exact: true })
  await dialog.getByRole('combobox', { name: '时间类别', exact: true }).selectOption('study')
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await expect(dialog).not.toBeVisible()
}

test('starts with honest empty data and bundled readable fonts', async ({ page }, info) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('让每一份投入，都有迹可循。')
  await expect(page.getByText('给重要的事情，一个清晰的主题', { exact: true })).toBeVisible()
  await page.evaluate(() => document.fonts.ready)
  expect(await page.evaluate(() => document.fonts.check('15px "Inter Variable"') && document.fonts.check('15px "Noto Sans SC"', '生活管理'))).toBe(true)
  await page.screenshot({ path: info.outputPath('overview-empty-1440.png'), fullPage: true })
})

test('records partial progress and actual time once, persists, and links both views', async ({ page }, info) => {
  await createTask(page)
  await page.getByRole('button', { name: '记录进展: 极限与连续', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: '记录一次行动' })
  await expect(dialog.getByRole('combobox', { name: '时间类别', exact: true })).toHaveValue('study')
  await dialog.getByLabel('这次做了什么？').fill('完成前三节，尚未完成')
  await dialog.getByLabel('开始时间', { exact: true }).fill('2026-11-11T09:00')
  await dialog.getByLabel('结束时间', { exact: true }).fill('2026-11-11T09:40')
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await expect(dialog).not.toBeVisible()
  await expect(page.getByText('完成前三节，尚未完成', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '标记完成: 极限与连续', exact: true })).toHaveAttribute('aria-pressed', 'false')
  await page.reload()
  await expect(page.getByText('完成前三节，尚未完成', { exact: true })).toBeVisible()
  await page.screenshot({ path: info.outputPath('plan-progress-1440.png'), fullPage: true })
  await page.goto('/#/time?date=2026-11-11')
  await expect(page.locator('.list-row')).toHaveCount(1)
  await expect(page.locator('.list-row')).toContainText('40 分钟')
  await page.locator('.list-row').getByRole('link', { name: '数学课程复习' }).click()
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('数学课程复习')
  await expect(page.getByText('完成前三节，尚未完成', { exact: true })).toBeVisible()
})

test('keeps progress-only logs distinct from completed tasks and recorded durations', async ({ page }) => {
  await createTask(page)
  await page.getByRole('button', { name: '记录进展: 极限与连续', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: '记录一次行动' })
  await dialog.getByLabel('这次做了什么？').fill('整理了思路，继续推进')
  await dialog.getByLabel('同时记录实际用时').uncheck()
  await dialog.getByLabel('进展发生时间').fill('2026-11-11T10:00')
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await expect(dialog).not.toBeVisible()
  await expect(page.getByText('整理了思路，继续推进', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '标记完成: 极限与连续', exact: true })).toHaveAttribute('aria-pressed', 'false')
  await page.goto('/#/time?date=2026-11-11')
  await expect(page.getByText('这一天，还没有时间记录', { exact: true })).toBeVisible()
})

test('captures, completes and reopens independent small tasks', async ({ page }) => {
  await page.goto('/#/todos')
  await page.getByPlaceholder('有什么需要记住的？').fill('订火车票')
  await page.locator('.quick-capture').getByRole('button', { name: '添加待办', exact: true }).click()
  await expect(page.locator('.list-row')).toContainText('订火车票')
  await page.getByRole('button', { name: '标记完成: 订火车票', exact: true }).click()
  await expect(page.locator('.list-row')).toHaveCount(0)
  await page.getByRole('button', { name: '已完成', exact: true }).click()
  await expect(page.locator('.list-row')).toContainText('订火车票')
  await page.getByRole('button', { name: '重新打开: 订火车票', exact: true }).click()
  await page.getByRole('button', { name: '待处理', exact: true }).click()
  await expect(page.locator('.list-row')).toContainText('订火车票')
})

test('persists locale and theme through the shared registry', async ({ page }, info) => {
  await page.goto('/#/settings')
  await page.getByRole('combobox', { name: '语言', exact: true }).selectOption('en-US')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Make it feel like yours.')
  await page.getByRole('button', { name: 'Midnight', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Midnight', exact: true })).toHaveAttribute('aria-pressed', 'true')
  await page.reload()
  await expect(page.getByRole('combobox', { name: 'Language', exact: true })).toHaveValue('en-US')
  await expect(page.getByRole('button', { name: 'Midnight', exact: true })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByText('Version 3.0.0', { exact: false })).toBeVisible()
  await page.screenshot({ path: info.outputPath('settings-dark-1440.png'), fullPage: true })
})

test('exports, previews replacement, imports and restores the prior workspace', async ({ page }, info) => {
  await createPlan(page, '保留的计划')
  await page.goto('/#/settings')
  const downloadEvent = page.waitForEvent('download')
  await page.getByRole('button', { name: '导出存档', exact: true }).click()
  const download = await downloadEvent
  const path = info.outputPath(download.suggestedFilename())
  await download.saveAs(path)
  await createPlan(page, '导出之后新建的计划')
  await page.goto('/#/settings')
  await page.getByLabel('导入存档', { exact: true }).setInputFiles(path)
  const dialog = page.getByRole('dialog', { name: '检查即将导入的内容' })
  await expect(dialog).toContainText('1 份计划')
  await dialog.getByRole('button', { name: '确认替换并导入', exact: true }).click()
  await expect(dialog).not.toBeVisible()
  await page.goto('/#/plans')
  await expect(page.getByRole('link', { name: /保留的计划/ })).toBeVisible()
  await expect(page.getByRole('link', { name: /导出之后新建的计划/ })).toHaveCount(0)
  await page.goto('/#/settings')
  await page.getByRole('button', { name: '恢复上一份有效备份', exact: true }).click()
  await page.getByRole('dialog').getByRole('button', { name: '确认', exact: true }).click()
  await page.goto('/#/plans')
  await expect(page.getByRole('link', { name: /导出之后新建的计划/ })).toBeVisible()
})

test('keeps major screens within seven viewport widths', async ({ page }, info) => {
  for (const width of [320, 390, 768, 1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 950 })
    for (const path of ['/', '/plans', '/time', '/todos', '/settings']) {
      await page.goto('/#' + path)
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
      expect(overflow, path + ' at ' + width).toBeLessThanOrEqual(1)
    }
    if (width === 390) {
      await page.goto('/')
      await page.screenshot({ path: info.outputPath('overview-empty-390.png'), fullPage: true })
    }
  }
})
