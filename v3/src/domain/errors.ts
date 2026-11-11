export class DomainError extends Error {
  constructor(public readonly code: string, public readonly details: Record<string, unknown> = {}) {
    super(code)
    this.name = 'DomainError'
  }
}

export function requireCondition(condition: unknown, code: string, details?: Record<string, unknown>): asserts condition {
  if (!condition) throw new DomainError(code, details)
}

export function requireTitle(value: string): string {
  const title = value.trim()
  requireCondition(title.length > 0, 'validation.titleRequired')
  return title
}

