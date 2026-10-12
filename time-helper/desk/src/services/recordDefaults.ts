export interface RecordTimeDefaults {
  start: { h: string; m: string }
  end: { h: string; m: string }
  duration: { h: string; m: string }
  reference: { h: string; m: string }
}

export function formatInputClock(totalMinutes: number): { h: string; m: string } {
  const bounded = Math.max(0, Math.min(24 * 60, Math.trunc(totalMinutes)))
  return {
    h: String(Math.floor(bounded / 60)).padStart(2, '0'),
    m: String(bounded % 60).padStart(2, '0'),
  }
}

/** Defaults for a new same-day record, shared by the primary and history forms. */
export function currentRecordDefaults(now = new Date()): RecordTimeDefaults {
  const startMinutes = now.getHours() * 60 + now.getMinutes()
  const availableMinutes = Math.max(1, 24 * 60 - startMinutes)
  const defaultDuration = Math.min(60, availableMinutes)
  return {
    start: formatInputClock(startMinutes),
    end: formatInputClock(startMinutes + defaultDuration),
    duration: { h: String(Math.floor(defaultDuration / 60)), m: String(defaultDuration % 60) },
    reference: formatInputClock(startMinutes),
  }
}
