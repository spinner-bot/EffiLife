import type { Category, Todo } from './models'

function logAdd(a: number, b: number): number {
  const maximum = Math.max(a, b)
  return maximum + Math.log(Math.exp(a - maximum) + Math.exp(b - maximum))
}

/** Preserve the original priority model, with stable logarithms at high ranks. */
export function priorityScore(todo: Todo, category: Category, now: string): number {
  const deadline = todo.deadline ? Date.parse(todo.deadline) : NaN
  const start = Date.parse(todo.startAt || todo.createdAt)
  const current = Date.parse(now)
  if (Number.isFinite(deadline) && deadline <= current) return -1
  if (!Number.isFinite(deadline) || !Number.isFinite(start) || deadline <= start) return 0
  const total = (deadline - start) / 60000
  const remaining = Math.max((deadline - current) / 60000, 0.001)
  const difficulty = Math.max(0, category.difficulty)
  const rank = Math.max(0, todo.priorityRank)
  const base = -Math.expm1(rank * Math.log(50 / (difficulty + 50)))
  const logEvaluation = difficulty === 0 ? 0 : base > 0 ? Math.log(base) + Math.log(total) : Math.log(0.001)
  const evaluationSufficiency = Math.log(remaining) - logEvaluation
  const calibrated = Math.min(total, todo.estimatedMinutes || 60)
  const calibrationSufficiency = Math.log(remaining) - Math.log(Math.max(calibrated, 0.001))
  const harmonicDenominator = logAdd(logAdd(evaluationSufficiency, calibrationSufficiency), Math.log(0.001))
  const logSufficiency = logAdd(
    Math.log(0.65) + 0.5 * (evaluationSufficiency + calibrationSufficiency),
    Math.log(0.7) + evaluationSufficiency + calibrationSufficiency - harmonicDenominator,
  )
  const importance = todo.important ? 145 + difficulty : 0
  const urgency = todo.urgent ? 1335 + 3 * difficulty : 1000
  const effectiveRank = Math.max(rank, 1)
  const a = Math.log(1.06) * effectiveRank
  const b = Math.log(1.35) + 1.5 * Math.log(effectiveRank)
  const maximum = Math.max(a, b)
  const logMultiplier = maximum + Math.log(Math.exp(a - maximum) + Math.exp(b - maximum) - Math.exp(-maximum))
  const logScore = Math.log(importance + urgency) - Math.max(logSufficiency, Math.log(0.001)) + logMultiplier
  return logScore > Math.log(1e10)
    ? Math.floor(1e10 + 100 * logScore / Math.LN10 + 0.5)
    : Math.floor(Math.exp(logScore) + 0.5)
}

