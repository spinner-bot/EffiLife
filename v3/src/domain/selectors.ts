import type { Workspace, Plan } from './models'
import { recordedMinutes, unionMinutes, dayBounds } from './time'

export function daySummary(workspace: Workspace, date: string) {
  const zone = workspace.preferences.timeZone
  const bounds = dayBounds(date, zone)
  const categories = workspace.categories.map(category => ({
    category,
    minutes: recordedMinutes(workspace.records.filter(record => record.categoryId === category.id), date, zone),
  })).filter(item => item.minutes > 0)
  return {
    total: recordedMinutes(workspace.records, date, zone),
    dayMinutes: (bounds[1] - bounds[0]) / 60000,
    categories,
  }
}
export function planMinutes(workspace: Workspace, plan: Plan, taskId?: string) {
  return unionMinutes(workspace.records.filter(record => record.planId === plan.id && (!taskId || record.taskId === taskId))
    .map(record => [Date.parse(record.startAt), Date.parse(record.endAt)]))
}
export function recentActivities(workspace: Workspace) {
  const records = workspace.records.map(record => ({
    id: record.id, title: record.title, content: record.note, at: record.endAt,
    planId: record.planId, taskId: record.taskId, categoryId: record.categoryId,
    minutes: (Date.parse(record.endAt) - Date.parse(record.startAt)) / 60000,
  }))
  const logs = workspace.plans.flatMap(plan => plan.logs.filter(log => !log.recordIds.length).map(log => ({
    id: log.id, title: log.taskId ? plan.nodes.find(node => node.id === log.taskId)?.title || plan.title : plan.title,
    content: log.content, at: log.occurredAt, planId: plan.id, taskId: log.taskId,
    categoryId: undefined, minutes: 0,
  })))
  return [...records, ...logs].sort((a, b) => Date.parse(b.at) - Date.parse(a.at))
}

