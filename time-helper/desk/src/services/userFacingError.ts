const TECHNICAL_ERROR_PATTERNS = [
  /indexeddb/i,
  /object store/i,
  /transaction/i,
  /quotaexceeded/i,
  /failed to execute/i,
  /cannot read properties/i,
  /networkerror/i,
  /\bundefined\b/i,
  /\bnull\b/i,
]

/** Keep implementation details out of the primary user-facing error channel. */
export function getUserFacingError(error: unknown, fallback: string): string {
  if (!(error instanceof Error)) return fallback
  const message = error.message.trim()
  if (!message || message.length > 240 || TECHNICAL_ERROR_PATTERNS.some((pattern) => pattern.test(message))) {
    return fallback
  }
  return message
}
