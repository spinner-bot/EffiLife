import type { Plan, PlanNode, Workspace } from '../domain/models'
import { list, object, string, number, legacyDate, logInstant, sectionLetter } from './legacy-utils'

export function importLegacyPlans(
  workspace: Workspace, values: unknown[], warnings: string[], namespace = 'legacy-plan-',
): Map<string, { planId: string; tasks: Map<string, string> }> {
  const mapping = new Map<string, { planId: string; tasks: Map<string, string> }>()
  for (const [position, value] of values.entries()) {
    const raw = object(value)
    const head = object(raw.head)
    if (!Array.isArray(raw.main)) { warnings.push('legacy.planInvalid'); continue }
    const rawId = String(head.index ?? position + 1)
    const planId = namespace + rawId
    if (mapping.has(rawId)) { warnings.push('legacy.duplicatePlan'); continue }
    const baseDate = legacyDate(head.date, workspace.updatedAt)
    let createdAt = workspace.updatedAt
    try { createdAt = logInstant({ day: 0 }, baseDate, workspace.preferences.timeZone).occurredAt }
    catch { warnings.push('legacy.localTimeInvalid') }
    const plan: Plan = {
      id: planId, title: string(head.name, 'Plan ' + rawId), description: '',
      createdAt,
      updatedAt: workspace.updatedAt, nodes: [], logs: [], legacy: structuredClone(raw),
    }
    const tasks = new Map<string, string>()
    for (const [sectionIndex, sectionValue] of raw.main.entries()) {
      const section = object(sectionValue)
      const sectionId = planId + '-section-' + sectionIndex
      plan.nodes.push({ id: sectionId, parentId: null, kind: 'section', title: string(section.name, sectionLetter(sectionIndex)), description: string(section.info), order: plan.nodes.length, estimatedMinutes: 0 })
      const groups = Object.entries(object(section.group)).map(([range, value]) => {
        const [start, end] = range.split('_').map(Number)
        return { start: start!, end: end!, raw: object(value), id: sectionId + '-group-' + range }
      }).filter(group => Number.isInteger(group.start) && Number.isInteger(group.end) && group.start <= group.end)
      for (const group of groups) {
        const enclosing = groups.filter(other => other.id !== group.id && other.start <= group.start && other.end >= group.end && (other.start !== group.start || other.end !== group.end))
          .sort((a, b) => (a.end - a.start) - (b.end - b.start))[0]
        plan.nodes.push({ id: group.id, parentId: enclosing?.id || sectionId, kind: 'group', title: string(group.raw.title, 'Group'), description: string(group.raw.description), order: plan.nodes.length, estimatedMinutes: 0 })
      }
      for (const [taskIndex, taskValue] of list(section.plan).entries()) {
        if (!taskValue || typeof taskValue !== 'object') continue
        const task = object(taskValue)
        const id = sectionId + '-task-' + taskIndex
        const enclosing = groups.filter(group => group.start <= taskIndex && group.end >= taskIndex)
          .sort((a, b) => (a.end - a.start) - (b.end - b.start))[0]
        const node: PlanNode = {
          id, parentId: enclosing?.id || sectionId, kind: 'task',
          title: string(task.content, 'Task ' + taskIndex), description: '',
          order: plan.nodes.length, estimatedMinutes: Math.max(0, number(task.t_m) * 6),
          legacyCode: sectionLetter(sectionIndex) + taskIndex,
          deletedAt: task.is_active === false ? workspace.updatedAt : undefined,
        }
        if (task.finish && typeof task.finish === 'object') {
          try { node.completedAt = logInstant(object(task.finish), baseDate, workspace.preferences.timeZone).occurredAt }
          catch { warnings.push('legacy.localTimeInvalid') }
        }
        plan.nodes.push(node)
        tasks.set(sectionLetter(sectionIndex) + taskIndex, id)
      }
    }
    for (const [index, value] of list(raw.log).entries()) {
      const log = object(value)
      const taskId = tasks.get(string(log.plan))
      if (log.plan !== 'base' && !taskId) warnings.push('legacy.logTaskMissing')
      try {
        const timestamp = logInstant(log, baseDate, workspace.preferences.timeZone)
        plan.logs.push({
          id: planId + '-log-' + index, taskId, occurredAt: timestamp.occurredAt,
          timePrecision: timestamp.precision, content: string(log.content), kind: 'progress', recordIds: [],
        })
      } catch { warnings.push('legacy.localTimeInvalid') }
    }
    workspace.plans.push(plan)
    mapping.set(rawId, { planId, tasks })
  }
  return mapping
}

