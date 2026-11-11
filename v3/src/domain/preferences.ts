import { requireCondition } from './errors'
import type { HeaderClockPreferences } from './models'
export const defaultHeaderClock: HeaderClockPreferences = { display: 'date', hourCycle: 24, showPeriod: true, align: 'right' }
export function assertOptionalPreferences(value: { headerClock?: unknown }, code: string) {
  if (value.headerClock !== undefined) {
    const clock = value.headerClock as HeaderClockPreferences | null
    requireCondition(clock && ['date', 'time', 'both'].includes(clock.display) && [12, 24].includes(clock.hourCycle) && typeof clock.showPeriod === 'boolean' && ['center', 'right'].includes(clock.align), code)
  }
}
