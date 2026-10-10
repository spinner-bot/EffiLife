/** Stable search tokens for the PH [year, month, day] tuple. */
export function dateSearchTokens(date: unknown): string[] {
  if (!Array.isArray(date) || date.length < 3) return []
  const parts = date.slice(0, 3).map(Number)
  if (parts.some((part) => !Number.isFinite(part) || !Number.isInteger(part))) return []
  const [year, month, day] = parts
  const paddedMonth = String(month).padStart(2, '0')
  const paddedDay = String(day).padStart(2, '0')
  return [
    `${year}-${paddedMonth}-${paddedDay}`,
    `${year}/${paddedMonth}/${paddedDay}`,
    `${year}.${paddedMonth}.${paddedDay}`,
    `${year}-${month}-${day}`,
  ]
}

export function dateSearchText(date: unknown): string {
  return dateSearchTokens(date).join(' ')
}
