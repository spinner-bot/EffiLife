import type { CommandContext, OperationResult, Workspace } from './models'
import type { WorkspaceCommand } from './commands'
import { requireCondition, requireTitle } from './errors'
import { dayBounds } from './time'
import { validRule } from './time-planning'

export function applyTimePlanCommand(workspace: Workspace, command: WorkspaceCommand, context: CommandContext): OperationResult | undefined {
  if (!['saveTimePlan', 'deleteTimePlan', 'setDateTimePlan', 'saveTimeRule', 'deleteTimeRule'].includes(command.type)) return undefined
  const planning = workspace.timePlanning ||= { plans: [], rules: [], overrides: {} }
  switch (command.type) {
    case 'saveTimePlan': {
      const current = command.timePlanId ? planning.plans.find(plan => plan.id === command.timePlanId) : undefined
      requireCondition(!command.timePlanId || current, 'validation.timePlanMissing')
      requireCondition(command.mode === 'allocation' || command.mode === 'partition', 'validation.timePlanMode')
      requireCondition(command.items.length > 0 && new Set(command.items.map(item => item.categoryId)).size === command.items.length, 'validation.timePlanItems')
      for (const item of command.items) {
        requireCondition(workspace.categories.some(category => category.id === item.categoryId), 'validation.categoryMissing')
        requireCondition(Number.isFinite(item.minutes) && item.minutes >= 0, 'validation.invalidDuration')
      }
      requireCondition(command.mode !== 'partition' || command.items.some(item => item.categoryId === command.backgroundCategoryId), 'validation.backgroundCategory')
      const value = { id: current?.id || context.id(), name: requireTitle(command.name), mode: command.mode, items: structuredClone(command.items), backgroundCategoryId: command.mode === 'partition' ? command.backgroundCategoryId : undefined }
      if (current) Object.assign(current, value)
      else planning.plans.push(value)
      return { entityId: value.id }
    }
    case 'deleteTimePlan': {
      requireCondition(planning.plans.some(plan => plan.id === command.timePlanId), 'validation.timePlanMissing')
      planning.plans = planning.plans.filter(plan => plan.id !== command.timePlanId)
      planning.rules = planning.rules.filter(rule => rule.planId !== command.timePlanId)
      for (const [date, id] of Object.entries(planning.overrides)) if (id === command.timePlanId) delete planning.overrides[date]
      return { entityId: command.timePlanId }
    }
    case 'setDateTimePlan': {
      dayBounds(command.date, workspace.preferences.timeZone)
      if (command.timePlanId === null) delete planning.overrides[command.date]
      else {
        requireCondition(planning.plans.some(plan => plan.id === command.timePlanId), 'validation.timePlanMissing')
        planning.overrides[command.date] = command.timePlanId
      }
      return {}
    }
    case 'saveTimeRule': {
      requireCondition(planning.plans.some(plan => plan.id === command.timePlanId), 'validation.timePlanMissing')
      requireCondition(['week', 'month', 'year', 'month_week', 'default'].includes(command.kind), 'validation.ruleInvalid')
      const current = command.ruleId ? planning.rules.find(rule => rule.id === command.ruleId) : undefined
      requireCondition(!command.ruleId || current, 'validation.ruleMissing')
      const rule = { id: current?.id || context.id(), kind: command.kind, value: command.value.trim(), planId: command.timePlanId }
      requireCondition(validRule(rule.kind, rule.value), 'validation.ruleInvalid')
      if (rule.kind === 'default') planning.rules = planning.rules.filter(item => item.kind !== 'default' || item.id === rule.id)
      if (current) Object.assign(current, rule)
      else planning.rules.push(rule)
      return { entityId: rule.id }
    }
    case 'deleteTimeRule':
      requireCondition(planning.rules.some(rule => rule.id === command.ruleId), 'validation.ruleMissing')
      planning.rules = planning.rules.filter(rule => rule.id !== command.ruleId)
      return { entityId: command.ruleId }
  }
  return undefined
}
