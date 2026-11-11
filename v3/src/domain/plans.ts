import type { Plan, PlanNode, Workspace } from './models'
import { requireCondition } from './errors'

export function findPlan(workspace: Workspace, id: string): Plan {
  const plan = workspace.plans.find(item => item.id === id)
  requireCondition(plan, 'validation.planMissing')
  return plan
}

export function findNode(plan: Plan, id: string): PlanNode {
  const node = plan.nodes.find(item => item.id === id)
  requireCondition(node, 'validation.taskMissing')
  return node
}

export function descendants(plan: Plan, parentId: string): PlanNode[] {
  const result: PlanNode[] = []
  const seen = new Set<string>([parentId])
  let parents = [parentId]
  while (parents.length) {
    const children = plan.nodes.filter(node => node.parentId !== null && parents.includes(node.parentId))
    parents = []
    for (const child of children) {
      requireCondition(!seen.has(child.id), 'validation.treeCycle')
      seen.add(child.id)
      result.push(child)
      parents.push(child.id)
    }
  }
  return result
}

export function categoryFor(plan: Plan, nodeId?: string, fallback = 'life'): string {
  let node: PlanNode | undefined = nodeId === undefined ? undefined : findNode(plan, nodeId)
  const seen = new Set<string>()
  while (node) {
    requireCondition(!seen.has(node.id), 'validation.treeCycle')
    seen.add(node.id)
    if (node.categoryId) return node.categoryId
    node = node.parentId ? findNode(plan, node.parentId) : undefined
  }
  return plan.categoryId || fallback
}

export function planProgress(plan: Plan): { total: number; completed: number; percent: number; logs: number } {
  const tasks = plan.nodes.filter(node => node.kind === 'task' && !node.deletedAt)
  const completed = tasks.filter(task => task.completedAt).length
  return { total: tasks.length, completed, percent: tasks.length ? completed / tasks.length * 100 : 0, logs: plan.logs.length }
}

function letters(index: number): string {
  let value = index + 1
  let text = ''
  while (value > 0) {
    value--
    text = String.fromCharCode(65 + value % 26) + text
    value = Math.floor(value / 26)
  }
  return text
}

export function displayCode(plan: Plan, nodeId: string): string {
  const node = findNode(plan, nodeId)
  if (node.kind !== 'task') return ''
  if (node.legacyCode) return node.legacyCode
  const sections = plan.nodes.filter(item => item.kind === 'section').sort((a, b) => a.order - b.order)
  const sectionOf = (item: PlanNode) => {
    let parent = item.parentId ? findNode(plan, item.parentId) : undefined
    const seen = new Set<string>([item.id])
    while (parent && parent.kind !== 'section') {
      requireCondition(!seen.has(parent.id), 'validation.treeCycle')
      seen.add(parent.id)
      parent = parent.parentId ? findNode(plan, parent.parentId) : undefined
    }
    return parent
  }
  const parent = sectionOf(node)
  const tasks = plan.nodes.filter(item => item.kind === 'task' && sectionOf(item)?.id === parent?.id).sort((a, b) => a.order - b.order)
  const section = parent ? sections.findIndex(item => item.id === parent.id) : sections.length
  const prefix = letters(Math.max(0, section))
  const legacyMaximum = Math.max(0, ...tasks.filter(item => item.legacyCode?.startsWith(prefix)).map(item => Number(item.legacyCode!.slice(prefix.length)) || 0))
  const newTasks = tasks.filter(item => !item.legacyCode)
  return prefix + String(legacyMaximum + newTasks.findIndex(item => item.id === nodeId) + 1)
}

