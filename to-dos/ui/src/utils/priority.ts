/**
 * to-dos 优先排位分算法 (v0.5.0)
 *
 * 前端版本 - TypeScript 实现
 * 与后端 priority.py 算法保持一致
 */

import type { Todo, Category } from '@/types'

/**
 * 解析 ISO 时间字符串
 */
function parseTime(timeStr: string | undefined): Date | null {
  if (!timeStr) return null
  try {
    const d = new Date(timeStr)
    return isNaN(d.getTime()) ? null : d
  } catch {
    return null
  }
}

/**
 * 计算优先排位分
 */
export function calcPriorityScore(
  todo: Todo,
  category: Category,
  now: Date = new Date(),
): number {
  const deadlineDt = parseTime(todo.deadline)
  const startDt = parseTime(todo.start_time || todo.created_at)

  // 校验：已过期
  if (deadlineDt && deadlineDt <= now) return -1

  // 校验：无效时间范围
  if (!deadlineDt || !startDt || deadlineDt <= startDt) return 0

  const difficulty = category.difficulty ?? 5
  const priority = todo.priority_rank ?? 0

  // 时间差（分钟）
  const totalTime = (deadlineDt.getTime() - startDt.getTime()) / 60000
  const remainingTime = (deadlineDt.getTime() - now.getTime()) / 60000

  // 评估时间（对数域）
  let logEvalTime: number
  if (difficulty === 0) {
    logEvalTime = 0
  } else {
    const base = 1 - Math.pow(50 / (difficulty + 50), priority)
    logEvalTime = base <= 0
      ? Math.log(0.001)
      : Math.log(base) + Math.log(totalTime)
  }

  // 评估充裕度
  const logEvalSufficiency = Math.log(Math.max(remainingTime, 0.001)) - logEvalTime

  // 标定时间
  const estimatedTime = todo.estimated_time || todo.time_estimate || 60
  const calibrateTime = Math.min(totalTime, estimatedTime)
  const logCalibrateSufficiency =
    Math.log(Math.max(remainingTime, 0.001)) - Math.log(Math.max(calibrateTime, 0.001))

  // 时间充裕度
  const evalSuff = Math.exp(logEvalSufficiency)
  const calibrateSuff = Math.exp(logCalibrateSufficiency)
  const timeSufficiency =
    0.65 * Math.exp(0.5 * logEvalSufficiency + 0.5 * logCalibrateSufficiency) +
    0.7 * evalSuff * calibrateSuff / (evalSuff + calibrateSuff + 0.001)

  // 基础优先度
  const importanceScore = todo.important ? (145 + difficulty) : 0
  const urgencyScore = todo.urgent ? (1335 + 3 * difficulty) : 1000
  const basePriority = (importanceScore + urgencyScore) / Math.max(timeSufficiency, 0.001)

  // 优先排位分
  const effectivePriority = Math.max(priority, 1)
  let multiplier = Math.pow(1.06, effectivePriority) + 1.35 * Math.pow(effectivePriority, 1.5) - 1
  if (multiplier <= 0) multiplier = 0.001

  const logScore = Math.log(Math.max(basePriority, 0.001)) + Math.log(Math.max(multiplier, 0.001))
  let score = Math.exp(logScore)

  // 软封顶
  if (score > 1e10) {
    score = 1e10 + 100 * Math.log10(score)
  }

  return Math.round(score)
}

/**
 * 格式化分数显示
 */
export function formatScoreDisplay(score: number): string {
  if (score < 0) return '过期'
  if (score === 0) return '0'
  if (score >= 1e10) {
    const number = (score - 1e10) / 100
    return `EL${number.toFixed(1)}`
  }
  if (score >= 1e8) {
    const number = Math.log10(score)
    return `EL${number.toFixed(1)}`
  }
  return String(score)
}

/**
 * 计算分类分数
 * sum(该分类下所有待办的分数) / sqrt(待办数量)
 */
export function calcCategoryScores(
  todos: Todo[],
  categories: Category[],
  now: Date = new Date(),
): Map<string, number> {
  const categoryMap = new Map(categories.map(c => [c.id, c]))
  const scores = new Map<string, number>()
  const counts = new Map<string, number>()

  for (const todo of todos) {
    if (['completed', 'cancelled', 'archived'].includes(todo.status)) continue

    const category = categoryMap.get(todo.category)
    if (!category) continue

    const score = calcPriorityScore(todo, category, now)
    scores.set(todo.category, (scores.get(todo.category) ?? 0) + score)
    counts.set(todo.category, (counts.get(todo.category) ?? 0) + 1)
  }

  const result = new Map<string, number>()
  for (const [catId, totalScore] of scores) {
    const count = counts.get(catId) ?? 1
    result.set(catId, totalScore / Math.sqrt(count))
  }

  return result
}

/**
 * 批量计算所有待办的分数
 */
export function calcAllScores(
  todos: Todo[],
  categories: Category[],
  now: Date = new Date(),
): Map<string, number> {
  const categoryMap = new Map(categories.map(c => [c.id, c]))
  const scores = new Map<string, number>()

  for (const todo of todos) {
    const category = categoryMap.get(todo.category)
    if (category) {
      scores.set(todo.id, calcPriorityScore(todo, category, now))
    }
  }

  return scores
}
