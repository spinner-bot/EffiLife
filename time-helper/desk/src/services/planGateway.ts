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

export interface PlanSection {
  index: number
  letter: string
  name: string
  info: string
  tasks: PlanTaskSummary[]
  groups: Record<string, { title: string; description: string }>
}

export interface PlanFull extends PlanSummary {
  sections: PlanSection[]
  logs: Array<{ index: number; day?: number; plan: string; time: [number, number]; content: string }>
}

export interface PlanArchiveSummary {
  file: string
  plan_id?: number
  name?: string
  date?: [number, number, number]
  archived_at?: string
}

export type PlanGatewayState = 'idle' | 'loading' | 'ready' | 'unavailable'

const PLAN_HELPER_ORIGIN = 'http://127.0.0.1:8765'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${PLAN_HELPER_ORIGIN}${path}`, {
    ...options,
    headers: { Accept: 'application/json', ...(options.headers || {}) },
  })
  const payload = await response.json() as { success?: boolean; data?: T; error?: string }
  if (!response.ok || !payload.success) throw new Error(payload.error || `计划服务响应异常（${response.status}）`)
  return payload.data as T
}

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

export async function listPlanArchives(): Promise<PlanArchiveSummary[]> {
  const data = await request<{ archives?: PlanArchiveSummary[] }>('/api/archives')
  return data.archives || []
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

export async function getPlanFull(planId: string): Promise<PlanFull> {
  return request<PlanFull>(`/api/plans/${encodeURIComponent(planId)}/full`)
}

export async function createEventPlan(name: string, date: [number, number, number]): Promise<PlanSummary> {
  return request<PlanSummary>('/api/plans', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, date }),
  })
}

export async function updateEventPlan(planId: string, name: string, date: [number, number, number]): Promise<PlanFull> {
  return request<PlanFull>(`/api/plans/${encodeURIComponent(planId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, date }),
  })
}

export async function archivePlan(planId: string): Promise<void> {
  await request(`/api/plans/${encodeURIComponent(planId)}/archive`, { method: 'POST' })
}

export async function restorePlanArchive(file: string): Promise<void> {
  await request('/api/archives/restore', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file }),
  })
}

export async function addPlanSection(planId: string, name: string, info = ''): Promise<void> {
  await request(`/api/plans/${encodeURIComponent(planId)}/sections`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, info }),
  })
}

export async function addPlanTask(planId: string, sectionIndex: number, content: string, timeMinutes: number): Promise<void> {
  await request(`/api/plans/${encodeURIComponent(planId)}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ section_index: sectionIndex, content, time_minutes: timeMinutes }),
  })
}

export async function updatePlanTask(planId: string, taskId: string, content: string, timeMinutes: number): Promise<void> {
  await request(`/api/plans/${encodeURIComponent(planId)}/tasks/${encodeURIComponent(taskId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, time_minutes: timeMinutes }),
  })
}

export async function completePlanTask(planId: string, taskId: string): Promise<void> {
  await request(`/api/plans/${encodeURIComponent(planId)}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task_id: taskId }),
  })
}

export async function deletePlanTask(planId: string, taskId: string): Promise<void> {
  await request(`/api/plans/${encodeURIComponent(planId)}/tasks/${encodeURIComponent(taskId)}`, {
    method: 'DELETE',
  })
}

export async function addPlanLog(planId: string, day: number, taskId: string, content: string): Promise<void> {
  await request(`/api/plans/${encodeURIComponent(planId)}/logs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ day, task_id: taskId || 'base', time: 'acc', content }),
  })
}
