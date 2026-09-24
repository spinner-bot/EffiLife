import type { TodoCategory, UnifiedTodo, TodoPriority } from './todoService'

export interface PriorityScore {
  score: number
  display: string
  expired: boolean
}

const MINUTES = 60 * 1000
const LOG_SCORE_LIMIT = Math.log(10 ** 10)

function parseDate(value?: string): number | null {
  if (!value) return null
  const timestamp = Date.parse(value)
  return Number.isFinite(timestamp) ? timestamp : null
}

function prioritySignals(todo: UnifiedTodo): { rank: number; urgent: boolean; important: boolean } {
  const legacyPriority: Record<TodoPriority, { urgent: boolean; important: boolean }> = {
    'urgent-important': { urgent: true, important: true },
    important: { urgent: false, important: true },
    urgent: { urgent: true, important: false },
    normal: { urgent: false, important: false },
  }
  const fallback = legacyPriority[todo.priority] || legacyPriority.normal
  const rank = Number.isFinite(todo.priority_rank) ? Math.max(0, Math.trunc(todo.priority_rank as number)) : 0
  return {
    rank,
    urgent: todo.urgent ?? fallback.urgent,
    important: todo.important ?? fallback.important,
  }
}

/**
 * Frontend equivalent of to-dos/src/priority.py.
 * Scores are calculated in the logarithmic domain so an urgent item close to
 * its deadline cannot overflow the UI process.
 */
export function calcPriorityScore(todo: UnifiedTodo, category: TodoCategory | undefined, now = new Date()): number {
  const deadline = parseDate(todo.deadline)
  const start = parseDate(todo.start_time || todo.created_at)
  const current = now.getTime()

  if (deadline !== null && deadline <= current) return -1
  if (deadline === null || start === null || deadline <= start) return 0

  const difficulty = Math.max(0, Math.min(10, Number(category?.difficulty ?? 5)))
  const { rank, urgent, important } = prioritySignals(todo)
  const totalMinutes = (deadline - start) / MINUTES
  const remainingMinutes = (deadline - current) / MINUTES

  let logEvaluationTime: number
  if (difficulty === 0) {
    logEvaluationTime = 0
  } else {
    const base = 1 - (50 / (difficulty + 50)) ** rank
    logEvaluationTime = Math.log(Math.max(base, 0.001)) + Math.log(totalMinutes)
  }

  const safeRemaining = Math.max(remainingMinutes, 0.001)
  const logEvaluationSufficiency = Math.log(safeRemaining) - logEvaluationTime
  const estimatedMinutes = Math.max(0.001, Number(todo.estimated_time ?? todo.time_estimate ?? 60))
  const calibratedMinutes = Math.min(totalMinutes, estimatedMinutes)
  const logCalibratedSufficiency = Math.log(safeRemaining) - Math.log(Math.max(calibratedMinutes, 0.001))

  const evaluationSufficiency = Math.exp(Math.min(logEvaluationSufficiency, 700))
  const calibratedSufficiency = Math.exp(Math.min(logCalibratedSufficiency, 700))
  const logGeometric = 0.5 * logEvaluationSufficiency + 0.5 * logCalibratedSufficiency
  const combinedSufficiency = 0.65 * Math.exp(Math.min(logGeometric, 700))
    + 0.7 * evaluationSufficiency * calibratedSufficiency
      / (evaluationSufficiency + calibratedSufficiency + 0.001)

  const importanceScore = important ? 145 + difficulty : 0
  const urgencyScore = urgent ? 1335 + 3 * difficulty : 1000
  const basePriority = (importanceScore + urgencyScore) / Math.max(combinedSufficiency, 0.001)
  const effectiveRank = Math.max(rank, 1)
  const multiplier = 1.06 ** effectiveRank + 1.35 * (effectiveRank ** 1.5) - 1
  const logScore = Math.log(Math.max(basePriority, 0.001)) + Math.log(Math.max(multiplier, 0.001))

  if (logScore >= LOG_SCORE_LIMIT) {
    return Math.trunc(10 ** 10 + 100 * (logScore / Math.LN10) + 0.5)
  }
  return Math.max(0, Math.trunc(Math.exp(logScore) + 0.5))
}

export function formatPriorityScore(score: number): string {
  if (score < 0) return '—'
  if (score === 0) return '0'
  if (score >= 10 ** 10) return `EL${((score - 10 ** 10) / 100).toFixed(1)}`
  if (score >= 10 ** 8) return `EL${Math.log10(score).toFixed(1)}`
  return String(score)
}

export function getPriorityScore(todo: UnifiedTodo, category: TodoCategory | undefined, now = new Date()): PriorityScore {
  const score = calcPriorityScore(todo, category, now)
  return { score, display: formatPriorityScore(score), expired: score < 0 }
}
