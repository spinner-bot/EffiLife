import { afterEach, expect, it } from 'vitest'
import { setLocale, t } from '../../src/i18n'

afterEach(() => setLocale('zh-CN'))

it('shows the provisional Chinese product name in Chinese and keeps EffiLife in English', () => {
  expect(t('app.name')).toBe('浪兮效率生活')
  expect(t('settings.about')).toBe('关于浪兮效率生活')
  expect(t('extensions.empty')).toContain('浪兮效率生活')
  setLocale('en-US')
  expect(t('app.name')).toBe('EffiLife')
  expect(t('settings.about')).toBe('About EffiLife')
})
