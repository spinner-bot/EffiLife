import { zonedInstant } from '../domain/time'

export function dateTimeInput(value: string, timeZone: string): string {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(new Date(value))
  const field = (name: string) => parts.find(part => part.type === name)!.value
  return field('year') + '-' + field('month') + '-' + field('day') + 'T' + field('hour') + ':' + field('minute')
}
export function parseDateTimeInput(value: string, timeZone: string): string {
  return zonedInstant(value, timeZone)
}

