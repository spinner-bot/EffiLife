import { PLAN_HELPER_ORIGIN } from './runtimeConfig'
import { getPlanRuntime, getPlanRuntimeUnavailableReason } from './runtimeCapabilities'

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
  internal_index: number
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

type RawPlan = {
  head?: { index?: number | string; name?: string; date?: [number, number, number] }
  main?: Array<{ name?: string; info?: string; plan?: Array<Record<string, unknown> | null>; group?: Record<string, { title?: string; description?: string }> }>
  log?: Array<{ index?: number; day?: number; plan?: string; time?: [number, number]; content?: string }>
}
type RawSection = NonNullable<RawPlan['main']>[number]

async function getMobileRawPlans(): Promise<RawPlan[]> {
  const { get, STORE_NAMES } = await import('@/storage')
  const plans = await get<unknown[]>(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'plans')
  return Array.isArray(plans) ? plans.filter((plan): plan is RawPlan => Boolean(plan && typeof plan === 'object')) : []
}

function planLetter(index: number): string {
  let value = index
  let result = ''
  do {
    result = String.fromCharCode(65 + (value % 26)) + result
    value = Math.floor(value / 26) - 1
  } while (value >= 0)
  return result
}

function activeRawTasks(section: RawSection) {
  const rawTasks = Array.isArray(section.plan) ? section.plan : []
  return rawTasks.flatMap((task, internalIndex) => {
    if (internalIndex === 0 || !task || task.is_active === false) return []
    return [{ task, internalIndex }]
  })
}

function toMobilePlanSummary(raw: RawPlan, fallbackIndex: number): PlanSummary {
  const sections = Array.isArray(raw.main) ? raw.main : []
  const tasks = sections.flatMap(activeRawTasks)
  const completed = tasks.filter(({ task }) => Boolean(task.finish)).length
  const estimatedMinutes = tasks.reduce((total, { task }) => total + Math.max(0, Number(task.t_m || 0) * 6), 0)
  const id = String(raw.head?.index ?? fallbackIndex)
  return {
    id,
    name: String(raw.head?.name || `Plan ${id}`),
    date: Array.isArray(raw.head?.date) ? raw.head.date : undefined,
    total_tasks: tasks.length,
    completed_tasks: completed,
    progress_percentage: tasks.length ? (completed / tasks.length) * 100 : 0,
    estimated_minutes: estimatedMinutes,
  }
}

function findMobilePlan(plans: RawPlan[], planId: string): RawPlan | undefined {
  return plans.find((plan, index) => String(plan.head?.index ?? index) === String(planId))
}

function toMobilePlanFull(raw: RawPlan, fallbackIndex: number): PlanFull {
  const summary = toMobilePlanSummary(raw, fallbackIndex)
  const sections = (Array.isArray(raw.main) ? raw.main : []).map((section, sectionIndex) => {
    const letter = planLetter(sectionIndex)
    const tasks = activeRawTasks(section).map(({ task, internalIndex }, displayIndex) => ({
      display_id: `${letter}${displayIndex + 1}`,
      internal_id: `${letter}${internalIndex}`,
      internal_index: internalIndex,
      content: String(task.content || ''),
      time_minutes: Math.max(0, Number(task.t_m || 0) * 6),
      is_active: true,
      finish: task.finish as PlanTaskSummary['finish'],
    }))
    const groups = Object.fromEntries(Object.entries(section.group || {}).map(([key, group]) => [key, {
      title: String(group?.title || ''),
      description: String(group?.description || ''),
    }]))
    return { index: sectionIndex, letter, name: String(section.name || ''), info: String(section.info || ''), tasks, groups }
  })
  const logs = (Array.isArray(raw.log) ? raw.log : []).map((log, index) => ({
    index: Number(log.index ?? index),
    day: log.day,
    plan: String(log.plan || 'base'),
    time: (Array.isArray(log.time) && log.time.length >= 2 ? [Number(log.time[0]), Number(log.time[1])] : [99, 99]) as [number, number],
    content: String(log.content || ''),
  }))
  return { ...summary, sections, logs }
}

interface ApiPayload<T> {
  success?: boolean
  data?: T
  error?: string
}

async function readPayload<T>(response: Response): Promise<ApiPayload<T>> {
  const raw = await response.text()
  let payload: ApiPayload<T>
  try {
    payload = raw ? JSON.parse(raw) as ApiPayload<T> : {}
  } catch {
    throw new Error(response.ok ? '计划服务返回无效响应' : `计划服务响应异常（${response.status}）`)
  }
  if (!response.ok || !payload.success) {
    throw new Error(payload.error || `计划服务响应异常（${response.status}）`)
  }
  return payload
}

async function fetchPlan(path: string, options: RequestInit = {}): Promise<Response> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    throw new Error(getPlanRuntimeUnavailableReason())
  }
  const retryDelays = [150, 300, 600, 1000, 1000]
  for (let attempt = 0; attempt <= retryDelays.length; attempt += 1) {
    try {
      return await fetch(`${PLAN_HELPER_ORIGIN}${path}`, options)
    } catch (error) {
      if (options.signal?.aborted) {
        throw error
      }
      if (attempt === retryDelays.length) {
        throw new Error('计划服务不可用，请确认服务已启动')
      }
      await new Promise((resolve) => setTimeout(resolve, retryDelays[attempt]))
    }
  }

  throw new Error('计划服务不可用，请确认服务已启动')
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetchPlan(path, {
    ...options,
    headers: { Accept: 'application/json', ...(options.headers || {}) },
  })
  const payload = await readPayload<T>(response)
  if (!response.ok || !payload.success) throw new Error(payload.error || `计划服务响应异常（${response.status}）`)
  return payload.data as T
}

export async function listPlanSummaries(signal?: AbortSignal): Promise<PlanSummary[]> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    const plans = await getMobileRawPlans()
    return plans.map((plan, index) => toMobilePlanSummary(plan, index))
  }
  const response = await fetchPlan('/api/plans', {
    signal,
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) throw new Error(`计划服务响应异常（${response.status}）`)
  const payload = await readPayload<{ plans?: PlanSummary[] }>(response)
  if (!payload.success) throw new Error(payload.error || '计划服务返回失败')
  return (payload.data?.plans || []).map((plan) => ({
    ...plan,
    id: String(plan.id),
  }))
}

export async function listPlanArchives(): Promise<PlanArchiveSummary[]> {
  if (getPlanRuntime() === 'mobile-unavailable') return []
  const data = await request<{ archives?: PlanArchiveSummary[] }>('/api/archives')
  return data.archives || []
}

export async function getPlanTasks(planId: string, signal?: AbortSignal): Promise<PlanTaskSummary[]> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    const plans = await getMobileRawPlans()
    const plan = findMobilePlan(plans, planId)
    return plan ? toMobilePlanFull(plan, plans.indexOf(plan)).sections.flatMap((section) => section.tasks) : []
  }
  const response = await fetchPlan(`/api/plans/${encodeURIComponent(planId)}/tasks`, {
    signal,
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) throw new Error(`计划任务服务响应异常（${response.status}）`)
  const payload = await readPayload<{ tasks?: PlanTaskSummary[] }>(response)
  if (!payload.success) throw new Error(payload.error || '计划任务服务返回失败')
  return (payload.data?.tasks || []).filter((task) => task.is_active !== false)
}

export async function getPlanFull(planId: string): Promise<PlanFull> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    const plans = await getMobileRawPlans()
    const plan = findMobilePlan(plans, planId)
    if (!plan) throw new Error('移动端未找到该事件计划快照')
    return toMobilePlanFull(plan, plans.indexOf(plan))
  }
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

export async function addPlanGroup(planId: string, sectionIndex: number, title: string, description: string, startIndex: number, endIndex: number): Promise<void> {
  await request(`/api/plans/${encodeURIComponent(planId)}/sections/${sectionIndex}/groups`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description, start_index: startIndex, end_index: endIndex }),
  })
}

export async function updatePlanGroup(planId: string, sectionIndex: number, groupKey: string, title: string, description: string): Promise<void> {
  await request(`/api/plans/${encodeURIComponent(planId)}/sections/${sectionIndex}/groups/${encodeURIComponent(groupKey)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description }),
  })
}

export async function deletePlanGroup(planId: string, sectionIndex: number, groupKey: string): Promise<void> {
  await request(`/api/plans/${encodeURIComponent(planId)}/sections/${sectionIndex}/groups/${encodeURIComponent(groupKey)}`, { method: 'DELETE' })
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
