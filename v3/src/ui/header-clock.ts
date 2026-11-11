import type { HeaderClockPreferences } from '../domain/models'
import { defaultHeaderClock } from '../domain/preferences'
export function headerClockText(now: string, locale: string, timeZone: string, options: HeaderClockPreferences = defaultHeaderClock): string {
  const date = new Intl.DateTimeFormat(locale, { timeZone, month: 'short', day: 'numeric', weekday: 'long' }).format(new Date(now))
  const parts = new Intl.DateTimeFormat(locale, { timeZone, hour: 'numeric', minute: '2-digit', hourCycle: options.hourCycle === 12 ? 'h12' : 'h23' }).formatToParts(new Date(now))
  const time = parts.filter(part => options.showPeriod || part.type !== 'dayPeriod').map(part => part.value).join('').trim()
  return options.display === 'date' ? date : options.display === 'time' ? time : time + ' · ' + date
}
