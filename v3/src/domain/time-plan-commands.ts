import type { CommandContext, OperationResult, Workspace } from './models'
import type { WorkspaceCommand } from './commands'
import { requireCondition, requireTitle } from './errors'
import { dayBounds } from './time'
import { validRule } from './time-planning'

export function applyTimePlanCommand(workspace: Workspace, command: WorkspaceCommand, context: CommandContext): OperationResult | undefined {
  if (!['saveTimePlan', 'deleteTimePlan', 'setDateTimePlan', 'saveTimeRule', 'deleteTimeRule', 'reorderTimeRules'].includes(command.type)) return undefined
  const planning = workspace.timePlanning ||= { plans: [], rules: [], overrides: {} }
  const finish = (result: OperationResult): OperationResult => {
    const fallback = [...planning.rules].reverse().find(rule => rule.kind === 'default')
    planning.rules = planning.rules.filter(rule => rule.kind !== 'default')
    if (fallback) planning.rules.push(fallback)
    else if (planning.plans.length) planning.rules.push({ id: context.id(), kind: 'default', value: '', planId: planning.plans[0]!.id })
    return result
  }
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
      if (command.useForDate) {
        dayBounds(command.useForDate, workspace.preferences.timeZone)
        planning.overrides[command.useForDate] = value.id
      }
      if (command.makeDefault === true) {
        planning.rules = planning.rules.filter(rule => rule.kind !== 'default')
        planning.rules.push({ id: context.id(), kind: 'default', value: '', planId: value.id })
      }
      return finish({ entityId: value.id })
    }
    case 'deleteTimePlan': {
      requireCondition(planning.plans.some(plan => plan.id === command.timePlanId), 'validation.timePlanMissing')
      const fallback = [...planning.rules].reverse().find(rule => rule.kind === 'default')
      if (fallback?.planId === command.timePlanId) {
        requireCondition(command.replacementId && command.replacementId !== command.timePlanId && planning.plans.some(plan => plan.id === command.replacementId), 'validation.defaultPlanReplacement')
        fallback.planId = command.replacementId
      }
      planning.plans = planning.plans.filter(plan => plan.id !== command.timePlanId)
      planning.rules = planning.rules.filter(rule => rule.planId !== command.timePlanId)
      for (const [date, id] of Object.entries(planning.overrides)) if (id === command.timePlanId) delete planning.overrides[date]
      return finish({ entityId: command.timePlanId })
    }
    case 'setDateTimePlan': {
      dayBounds(command.date, workspace.preferences.timeZone)
      if (command.timePlanId === null) delete planning.overrides[command.date]
      else {
        requireCondition(planning.plans.some(plan => plan.id === command.timePlanId), 'validation.timePlanMissing')
        planning.overrides[command.date] = command.timePlanId
      }
      return finish({})
    }
    case 'saveTimeRule': {
      requireCondition(planning.plans.some(plan => plan.id === command.timePlanId), 'validation.timePlanMissing')
      requireCondition(['week', 'month', 'year', 'month_week', 'default'].includes(command.kind), 'validation.ruleInvalid')
      const current = command.ruleId ? planning.rules.find(rule => rule.id === command.ruleId) : undefined
      requireCondition(!command.ruleId || current, 'validation.ruleMissing')
      requireCondition(current?.kind !== 'default' || command.kind === 'default', 'validation.defaultRuleProtected')
      const rule = { id: current?.id || context.id(), kind: command.kind, value: command.value.trim(), planId: command.timePlanId }
      requireCondition(validRule(rule.kind, rule.value), 'validation.ruleInvalid')
      if (rule.kind === 'default') planning.rules = planning.rules.filter(item => item.kind !== 'default' || item.id === rule.id)
      if (current) Object.assign(current, rule)
      else planning.rules.push(rule)
      return finish({ entityId: rule.id })
    }
    case 'reorderTimeRules': {
      const ordinary = planning.rules.filter(rule => rule.kind !== 'default')
      requireCondition(command.ruleIds.length === ordinary.length && new Set(command.ruleIds).size === ordinary.length && command.ruleIds.every(id => ordinary.some(rule => rule.id === id)), 'validation.ruleOrder')
      planning.rules = [...command.ruleIds.map(id => ordinary.find(rule => rule.id === id)!), ...planning.rules.filter(rule => rule.kind === 'default')]
      return finish({})
    }
    case 'deleteTimeRule':
      requireCondition(planning.rules.some(rule => rule.id === command.ruleId), 'validation.ruleMissing')
      requireCondition(!planning.rules.some(rule => rule.id === command.ruleId && rule.kind === 'default'), 'validation.defaultRuleProtected')
      planning.rules = planning.rules.filter(rule => rule.id !== command.ruleId)
      return finish({ entityId: command.ruleId })
  }
  return undefined
}
