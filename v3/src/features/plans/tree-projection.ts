import type { Plan, PlanNode } from '../../domain/models'
export interface TreeRow { node: PlanNode; depth: number }
export function flattenTree(plan: Plan, collapsed: Set<string>, omitted = new Set<string>()): TreeRow[] {
  const rows: TreeRow[] = []
  const visit = (parentId: string | null, depth: number) => {
    for (const node of plan.nodes.filter(item => item.parentId === parentId && !item.deletedAt && !omitted.has(item.id)).sort((a, b) => a.order - b.order)) {
      rows.push({ node, depth })
      if (node.kind !== 'task' && !collapsed.has(node.id)) visit(node.id, depth + 1)
    }
  }
  visit(null, 0)
  return rows
}
/** A vertical gap has several possible parents; horizontal movement selects depth. */
export function projectDrop(rows: TreeRow[], index: number, desiredDepth: number) {
  const previous = rows[index - 1], next = rows[index]
  const minimum = next?.depth || 0
  const maximum = previous ? previous.depth + (previous.node.kind === 'task' ? 0 : 1) : 0
  const depth = Math.max(minimum, Math.min(maximum, Math.max(0, desiredDepth)))
  let parentId: string | null = null
  if (depth > 0) for (let cursor = index - 1; cursor >= 0; cursor--) {
    const row = rows[cursor]!
    if (row.depth === depth - 1 && row.node.kind !== 'task') { parentId = row.node.id; break }
  }
  const before = rows.slice(index).find(row => row.depth === depth && row.node.parentId === parentId)
  return { depth, parentId, beforeId: before?.node.id || null }
}
