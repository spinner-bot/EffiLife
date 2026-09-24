import { TodoService } from './todoService'

/**
 * Complete every unified todo linked to a plan task.
 *
 * Plan-helper keeps its original task identity model, so this coordinator only
 * updates the unified todo side after the plan API has accepted completion.
 */
export async function completeLinkedTodos(planId: string, planTaskIds: string | string[]): Promise<number> {
  const identifiers = new Set(Array.isArray(planTaskIds) ? planTaskIds.map(String) : [String(planTaskIds)])
  const todos = await TodoService.list()
  const linked = todos.filter((todo) =>
    todo.related_plan_id === String(planId)
    && Boolean(todo.related_plan_task_id && identifiers.has(String(todo.related_plan_task_id)))
    && todo.status !== 'completed'
  )

  for (const todo of linked) {
    await TodoService.complete(todo.id)
  }
  return linked.length
}
