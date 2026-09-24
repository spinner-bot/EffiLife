export interface PlanSummary {
  id: string
  name: string
  date?: [number, number, number]
  total_tasks: number
  completed_tasks: number
  progress_percentage: number
  estimated_minutes: number
}

export interface PlanTaskSummary {
  display_id: string
  internal_id: string
  content: string
  time_minutes: number
  is_active: boolean
  finish?: { day?: number; time?: [number, number] }
}

export type PlanGatewayState = 'idle' | 'loading' | 'ready' | 'unavailable'

const PLAN_HELPER_ORIGIN = 'http://127.0.0.1:8765'

export async function listPlanSummaries(signal?: AbortSignal): Promise<PlanSummary[]> {
  const response = await fetch(`${PLAN_HELPER_ORIGIN}/api/plans`, {
    signal,
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) throw new Error(`计划服务响应异常（${response.status}）`)
  const payload = await response.json() as { success?: boolean; data?: { plans?: PlanSummary[] }; error?: string }
  if (!payload.success) throw new Error(payload.error || '计划服务返回失败')
  return (payload.data?.plans || []).map((plan) => ({
    ...plan,
    id: String(plan.id),
  }))
}

export async function getPlanTasks(planId: string, signal?: AbortSignal): Promise<PlanTaskSummary[]> {
  const response = await fetch(`${PLAN_HELPER_ORIGIN}/api/plans/${encodeURIComponent(planId)}/tasks`, {
    signal,
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) throw new Error(`计划任务服务响应异常（${response.status}）`)
  const payload = await response.json() as { success?: boolean; data?: { tasks?: PlanTaskSummary[] }; error?: string }
  if (!payload.success) throw new Error(payload.error || '计划任务服务返回失败')
  return (payload.data?.tasks || []).filter((task) => task.is_active !== false)
}
