import { shallowRef } from 'vue'
import { Registry } from '../extensions/registry'
import zh from './zh-CN.json'
import en from './en-US.json'

export interface LocaleDefinition { id: string; name: string; direction: 'ltr' | 'rtl'; messages: Record<string, string> }
export const locales = new Registry<LocaleDefinition>()
locales.register({ id: 'zh-CN', name: '简体中文', direction: 'ltr', messages: zh })
locales.register({ id: 'en-US', name: 'English', direction: 'ltr', messages: en })
export const currentLocale = shallowRef('zh-CN')

export function setLocale(id: string) {
  const locale = locales.get(id) || locales.get('zh-CN')!
  currentLocale.value = locale.id
  if (typeof document !== 'undefined') {
    document.documentElement.lang = locale.id
    document.documentElement.dir = locale.direction
  }
}
export function t(key: string, values: Record<string, string | number> = {}): string {
  const message = locales.get(currentLocale.value)?.messages[key] || en[key as keyof typeof en] || key
  return message.replace(/\{(\w+)\}/g, (match, name: string) => String(values[name] ?? match))
}
export function duration(minutes: number): string {
  const rounded = Math.round(minutes)
  if (rounded < 60) return t('common.minutes', { value: rounded })
  const hours = Math.floor(rounded / 60)
  const remainder = rounded % 60
  return t('common.hours', { value: hours }) + (remainder ? ' ' + t('common.minutes', { value: remainder }) : '')
}
export function calendarDate(date: string, options: Intl.DateTimeFormatOptions = {}): string {
  return new Intl.DateTimeFormat(currentLocale.value, { month: 'long', day: 'numeric', timeZone: 'UTC', ...options }).format(new Date(date + 'T12:00:00Z'))
}
export function clock(value: string, timeZone: string): string {
  return new Intl.DateTimeFormat(currentLocale.value, { hour: '2-digit', minute: '2-digit', hourCycle: 'h23', timeZone }).format(new Date(value))
}
export function categoryName(category: { name: string; labelKey?: string }): string { return category.name || t(category.labelKey || '') }
export function errorMessage(error: unknown): string {
  const key = error && typeof error === 'object' && 'code' in error ? String(error.code) : ''
  const message = key ? t(key) : ''
  return message && message !== key ? message : t('error.generic')
}

