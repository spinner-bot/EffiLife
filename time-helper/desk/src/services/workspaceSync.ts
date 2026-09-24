import { TodoService } from './todoService'

/**
 * Complete every unified todo linked to a plan task.
 *
 * Plan-helper keeps its original task identity model, so this coordinator only
 * updates the unified todo side after the plan API has accepted completion.
 */
export async function completeLinkedTodos(planId: string, planTaskId: string): Promise<number> {
  const todos = await TodoService.list()
  const linked = todos.filter((todo) =>
    todo.related_plan_id === String(planId)
    && todo.related_plan_task_id === String(planTaskId)
    && todo.status !== 'completed'
  )

  for (const todo of linked) {
    await TodoService.complete(todo.id)
  }
  return linked.length
}
