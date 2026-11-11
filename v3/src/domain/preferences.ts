import { assertAppearance } from './appearance'
import { requireCondition } from './errors'
import type { HeaderClockPreferences } from './models'
export const defaultHeaderClock: HeaderClockPreferences = { display: 'date', hourCycle: 24, showPeriod: true, align: 'right' }
export function assertOptionalPreferences(value: { headerClock?: unknown; appearance?: unknown }, code: string) {
  if (value.appearance !== undefined) {
    requireCondition(value.appearance && typeof value.appearance === 'object' && !Array.isArray(value.appearance) && Object.keys(value.appearance).length <= 200, code)
    for (const [id, options] of Object.entries(value.appearance)) {
      requireCondition(/^\d{1,12}$/.test(id), code)
      assertAppearance(options, code)
    }
  }
  if (value.headerClock !== undefined) {
    const clock = value.headerClock as HeaderClockPreferences | null
    requireCondition(clock && ['date', 'time', 'both'].includes(clock.display) && [12, 24].includes(clock.hourCycle) && typeof clock.showPeriod === 'boolean' && ['center', 'right'].includes(clock.align), code)
  }
}
