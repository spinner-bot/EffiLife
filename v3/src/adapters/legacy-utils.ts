import { isObject } from '../domain/validation'

export const object = (value: unknown): Record<string, unknown> => isObject(value) ? value : {}
export const list = (value: unknown): unknown[] => Array.isArray(value) ? value : []
export const string = (value: unknown, fallback = ''): string => typeof value === 'string' ? value : fallback
export const number = (value: unknown, fallback = 0): number => Number.isFinite(Number(value)) ? Number(value) : fallback

export function legacyDate(value: unknown, fallback: string): string {
  if (Array.isArray(value) && value.length >= 3) {
    const text = String(value[0]).padStart(4, '0') + '-' + String(value[1]).padStart(2, '0') + '-' + String(value[2]).padStart(2, '0')
    if (Number.isFinite(Date.parse(text))) return text
  }
  if (typeof value === 'string' && Number.isFinite(Date.parse(value))) return value.slice(0, 10)
  return fallback.slice(0, 10)
}

export function localInstant(date: string, time: string, timeZone: string): string {
  const desired = Date.parse(date + 'T' + time + (time.length === 5 ? ':00' : '') + 'Z')
  if (!Number.isFinite(desired)) throw new Error('archive.invalidLegacyTime')
  let candidate = desired
  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
  })
  for (let index = 0; index < 4; index++) {
    const parts = formatter.formatToParts(new Date(candidate))
    const field = (name: string) => Number(parts.find(part => part.type === name)!.value)
    const actual = Date.UTC(field('year'), field('month') - 1, field('day'), field('hour'), field('minute'), field('second'))
    const adjusted = desired - (actual - candidate)
    if (adjusted === candidate) break
    candidate = adjusted
  }
  return new Date(candidate).toISOString()
}

export function logInstant(raw: Record<string, unknown>, baseDate: string, timeZone: string) {
  const offset = Math.trunc(number(raw.day))
  const base = new Date(baseDate + 'T12:00:00Z')
  base.setUTCDate(base.getUTCDate() + offset)
  const date = typeof raw.date === 'string' ? legacyDate(raw.date, baseDate) : base.toISOString().slice(0, 10)
  const time = list(raw.time)
  const hour = number(time[0], 99)
  const minute = number(time[1], 99)
  const precision = hour === 99 ? 'date' : minute === 99 ? 'hour' : 'minute'
  const clock = String(hour === 99 ? 0 : hour).padStart(2, '0') + ':' + String(minute === 99 ? 0 : minute).padStart(2, '0')
  return { occurredAt: localInstant(date, clock, timeZone), precision } as const
}

export function sectionLetter(index: number): string {
  let value = index + 1
  let text = ''
  while (value > 0) { value--; text = String.fromCharCode(65 + value % 26) + text; value = Math.floor(value / 26) }
  return text
}

