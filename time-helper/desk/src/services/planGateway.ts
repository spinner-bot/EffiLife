import { PLAN_HELPER_ORIGIN } from './runtimeConfig'
import { getPlanRuntime, getPlanRuntimeUnavailableReason } from './runtimeCapabilities'
import { syncPendingPlanHelperReset } from './planReset'
import { translate } from '@/i18n'
import { ref } from 'vue'
import { notifyWorkspaceChanged } from './workspaceEvents'

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

export interface InitialPlanSection {
  name: string
  info: string
  tasks: Array<{ content: string; time_minutes: number }>
}

export interface PlanTemplateSummary {
  id: string
  name: string
  description: string
  type: string
  built_in: boolean
}

export interface PlanArchiveSummary {
  file: string
  plan_id?: number
  name?: string
  date?: [number, number, number]
  archived_at?: string
}

export type PlanGatewayState = 'idle' | 'loading' | 'ready' | 'unavailable'
export type PlanDataSource = 'unknown' | 'service' | 'mobile' | 'cache'

// A cached snapshot is safe for reading but must never be mistaken for a
// writable desktop service. The UI uses this state to expose read-only mode.
export const planDataSource = ref<PlanDataSource>('unknown')

type RawPlan = {
  head?: { index?: number | string; name?: string; date?: [number, number, number] }
  main?: Array<{ name?: string; info?: string; plan?: Array<Record<string, unknown> | null>; group?: Record<string, { title?: string; description?: string }> }>
  log?: Array<{ index?: number; day?: number; plan?: string; time?: [number, number]; content?: string }>
}
type RawSection = NonNullable<RawPlan['main']>[number]

type MobileTemplateDefinition = {
  id: string
  type: string
  nameKey: string
  descriptionKey: string
  sections: Array<{
    nameKey: string
    infoKey: string
    tasks: Array<{ contentKey: string; timeMinutes: number }>
    groups?: Array<{ titleKey: string; descriptionKey: string; start: number; end: number }>
  }>
}

const MOBILE_TEMPLATE_DEFINITIONS: MobileTemplateDefinition[] = [
  {
    id: 'workday',
    type: 'workday',
    nameKey: 'plans.templateTypes.workdayName',
    descriptionKey: 'plans.templateTypes.workdayDescription',
    sections: [
      {
        nameKey: 'plans.mobileTemplates.workday.morningName',
        infoKey: 'plans.mobileTemplates.workday.morningInfo',
        tasks: [
          { contentKey: 'plans.mobileTemplates.workday.plan', timeMinutes: 15 },
          { contentKey: 'plans.mobileTemplates.workday.deepWork', timeMinutes: 90 },
        ],
        groups: [{ titleKey: 'plans.mobileTemplates.workday.morningName', descriptionKey: 'plans.mobileTemplates.workday.morningInfo', start: 1, end: 2 }],
      },
      {
        nameKey: 'plans.mobileTemplates.workday.afternoonName',
        infoKey: 'plans.mobileTemplates.workday.afternoonInfo',
        tasks: [
          { contentKey: 'plans.mobileTemplates.workday.routine', timeMinutes: 60 },
          { contentKey: 'plans.mobileTemplates.workday.project', timeMinutes: 60 },
        ],
      },
      {
        nameKey: 'plans.mobileTemplates.workday.eveningName',
        infoKey: 'plans.mobileTemplates.workday.eveningInfo',
        tasks: [
          { contentKey: 'plans.mobileTemplates.workday.review', timeMinutes: 20 },
          { contentKey: 'plans.mobileTemplates.workday.read', timeMinutes: 45 },
        ],
      },
    ],
  },
  {
    id: 'weekend',
    type: 'weekend',
    nameKey: 'plans.templateTypes.weekendName',
    descriptionKey: 'plans.templateTypes.weekendDescription',
    sections: [
      {
        nameKey: 'plans.mobileTemplates.weekend.morningName',
        infoKey: 'plans.mobileTemplates.weekend.morningInfo',
        tasks: [
          { contentKey: 'plans.mobileTemplates.weekend.exercise', timeMinutes: 60 },
          { contentKey: 'plans.mobileTemplates.weekend.learning', timeMinutes: 90 },
        ],
      },
      {
        nameKey: 'plans.mobileTemplates.weekend.afternoonName',
        infoKey: 'plans.mobileTemplates.weekend.afternoonInfo',
        tasks: [
          { contentKey: 'plans.mobileTemplates.weekend.leisure', timeMinutes: 120 },
          { contentKey: 'plans.mobileTemplates.weekend.social', timeMinutes: 120 },
        ],
      },
      {
        nameKey: 'plans.mobileTemplates.weekend.eveningName',
        infoKey: 'plans.mobileTemplates.weekend.eveningInfo',
        tasks: [
          { contentKey: 'plans.mobileTemplates.weekend.entertainment', timeMinutes: 90 },
          { contentKey: 'plans.mobileTemplates.weekend.preview', timeMinutes: 20 },
        ],
      },
    ],
  },
  {
    id: 'exam',
    type: 'exam',
    nameKey: 'plans.templateTypes.examName',
    descriptionKey: 'plans.templateTypes.examDescription',
    sections: [
      {
        nameKey: 'plans.mobileTemplates.exam.morningName',
        infoKey: 'plans.mobileTemplates.exam.morningInfo',
        tasks: [
          { contentKey: 'plans.mobileTemplates.exam.review', timeMinutes: 30 },
          { contentKey: 'plans.mobileTemplates.exam.practice', timeMinutes: 90 },
        ],
        groups: [{ titleKey: 'plans.mobileTemplates.exam.morningName', descriptionKey: 'plans.mobileTemplates.exam.morningInfo', start: 1, end: 2 }],
      },
      {
        nameKey: 'plans.mobileTemplates.exam.afternoonName',
        infoKey: 'plans.mobileTemplates.exam.afternoonInfo',
        tasks: [
          { contentKey: 'plans.mobileTemplates.exam.mock', timeMinutes: 120 },
          { contentKey: 'plans.mobileTemplates.exam.errors', timeMinutes: 60 },
        ],
      },
      {
        nameKey: 'plans.mobileTemplates.exam.eveningName',
        infoKey: 'plans.mobileTemplates.exam.eveningInfo',
        tasks: [
          { contentKey: 'plans.mobileTemplates.exam.notes', timeMinutes: 45 },
          { contentKey: 'plans.mobileTemplates.exam.tomorrow', timeMinutes: 15 },
        ],
      },
    ],
  },
]

function mobileTemplateSummary(template: MobileTemplateDefinition): PlanTemplateSummary {
  return {
    id: template.id,
    name: translate(template.nameKey),
    description: translate(template.descriptionKey),
    type: template.type,
    built_in: true,
  }
}

function mobileTemplateSections(template: MobileTemplateDefinition): InitialPlanSection[] {
  return template.sections.map((section) => ({
    name: translate(section.nameKey),
    info: translate(section.infoKey),
    tasks: section.tasks.map((task) => ({ content: translate(task.contentKey), time_minutes: task.timeMinutes })),
  }))
}

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
    name: String(raw.head?.name || translate('plans.unnamed', { id })),
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

function cloneMobilePlans(plans: RawPlan[]): RawPlan[] {
  return JSON.parse(JSON.stringify(plans)) as RawPlan[]
}

async function saveMobileRawPlans(plans: RawPlan[]): Promise<void> {
  const { set, STORE_NAMES } = await import('@/storage')
  await set(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'plans', plans)
  notifyWorkspaceChanged('plans')
}

async function mutateMobilePlan(planId: string, mutate: (plan: RawPlan) => void): Promise<RawPlan> {
  const plans = cloneMobilePlans(await getMobileRawPlans())
  const plan = findMobilePlan(plans, planId)
  if (!plan) throw new Error(translate('plans.mobileSnapshotMissing'))
  mutate(plan)
  await saveMobileRawPlans(plans)
  return plan
}

function mobileTaskLocation(plan: RawPlan, taskId: string): { section: RawSection; task: Record<string, unknown> } | undefined {
  const sections = Array.isArray(plan.main) ? plan.main : []
  const normalizedId = String(taskId)
  for (let sectionIndex = 0; sectionIndex < sections.length; sectionIndex += 1) {
    const section = sections[sectionIndex]
    const letter = planLetter(sectionIndex)
    const rawTasks = Array.isArray(section.plan) ? section.plan : []
    let displayIndex = 0
    for (let internalIndex = 1; internalIndex < rawTasks.length; internalIndex += 1) {
      const task = rawTasks[internalIndex]
      if (!task || task.is_active === false) continue
      displayIndex += 1
      if (normalizedId === `${letter}${internalIndex}` || normalizedId === `${letter}${displayIndex}`) {
        return { section, task }
      }
    }
  }
  return undefined
}

function mobileTaskUnit(minutes: number): number {
  return Math.max(0, Math.round(Math.max(0, Number(minutes) || 0) / 6))
}

function mobileCurrentTime(): { day: number; time: [number, number] } {
  const now = new Date()
  return { day: now.getDate(), time: [now.getHours(), now.getMinutes()] }
}

function mobileGroupCrossesExisting(group: Record<string, { title?: string; description?: string }>, startIndex: number, endIndex: number): boolean {
  return Object.keys(group).some((key) => {
    const [existingStart, existingEnd] = key.split('_').map(Number)
    if (!Number.isInteger(existingStart) || !Number.isInteger(existingEnd)) return false
    return (existingStart < startIndex && startIndex < existingEnd && existingEnd < endIndex)
      || (startIndex < existingStart && existingStart < endIndex && endIndex < existingEnd)
  })
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
    throw new Error(response.ok ? translate('plans.serviceInvalidResponse') : translate('plans.serviceError', { status: response.status }))
  }
  if (!response.ok || !payload.success) {
    throw new Error(payload.error || translate('plans.serviceError', { status: response.status }))
  }
  return payload
}

async function fetchPlan(path: string, options: RequestInit = {}): Promise<Response> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    throw new Error(getPlanRuntimeUnavailableReason())
  }
  await syncPendingPlanHelperReset()
  const retryDelays = [150, 300, 600, 1000, 1000]
  for (let attempt = 0; attempt <= retryDelays.length; attempt += 1) {
    try {
      return await fetch(`${PLAN_HELPER_ORIGIN}${path}`, options)
    } catch (error) {
      if (options.signal?.aborted) {
        throw error
      }
      if (attempt === retryDelays.length) {
        throw new Error(translate('plans.serviceUnavailable'))
      }
      await new Promise((resolve) => setTimeout(resolve, retryDelays[attempt]))
    }
  }

  throw new Error(translate('plans.serviceUnavailable'))
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetchPlan(path, {
    ...options,
    headers: { Accept: 'application/json', ...(options.headers || {}) },
  })
  const payload = await readPayload<T>(response)
  if (!response.ok || !payload.success) throw new Error(payload.error || translate('plans.serviceError', { status: response.status }))
  if ((options.method || 'GET').toUpperCase() !== 'GET') {
    planDataSource.value = 'service'
    notifyWorkspaceChanged('plans')
  }
  return payload.data as T
}

export async function listPlanSummaries(signal?: AbortSignal): Promise<PlanSummary[]> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    planDataSource.value = 'mobile'
    const plans = await getMobileRawPlans()
    return plans.map((plan, index) => toMobilePlanSummary(plan, index))
  }
  try {
    const response = await fetchPlan('/api/plans', {
      signal,
      headers: { Accept: 'application/json' },
    })
    if (!response.ok) throw new Error(translate('plans.serviceError', { status: response.status }))
    const payload = await readPayload<{ plans?: PlanSummary[] }>(response)
    if (!payload.success) throw new Error(payload.error || translate('plans.serviceFailed'))
    planDataSource.value = 'service'
    return (payload.data?.plans || []).map((plan) => ({
      ...plan,
      id: String(plan.id),
    }))
  } catch (error) {
    if (signal?.aborted) throw error
    const cached = (await getMobileRawPlans()).map((plan, index) => toMobilePlanSummary(plan, index))
    if (cached.length === 0) throw error
    planDataSource.value = 'cache'
    return cached
  }
}

export async function listPlanArchives(): Promise<PlanArchiveSummary[]> {
  if (getPlanRuntime() === 'mobile-unavailable') return []
  try {
    const data = await request<{ archives?: PlanArchiveSummary[] }>('/api/archives')
    return data.archives || []
  } catch {
    // Archives are a secondary panel; keep cached active plans visible when
    // the service is temporarily unavailable.
    return []
  }
}

export async function getPlanTasks(planId: string, signal?: AbortSignal): Promise<PlanTaskSummary[]> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    planDataSource.value = 'mobile'
    const plans = await getMobileRawPlans()
    const plan = findMobilePlan(plans, planId)
    return plan ? toMobilePlanFull(plan, plans.indexOf(plan)).sections.flatMap((section) => section.tasks) : []
  }
  try {
    const response = await fetchPlan(`/api/plans/${encodeURIComponent(planId)}/tasks`, {
      signal,
      headers: { Accept: 'application/json' },
    })
    if (!response.ok) throw new Error(translate('plans.taskServiceError', { status: response.status }))
    const payload = await readPayload<{ tasks?: PlanTaskSummary[] }>(response)
    if (!payload.success) throw new Error(payload.error || translate('plans.taskServiceFailed'))
    planDataSource.value = 'service'
    return (payload.data?.tasks || []).filter((task) => task.is_active !== false)
  } catch (error) {
    if (signal?.aborted) throw error
    const plans = await getMobileRawPlans()
    const plan = findMobilePlan(plans, planId)
    if (!plan) throw error
    planDataSource.value = 'cache'
    return toMobilePlanFull(plan, plans.indexOf(plan)).sections.flatMap((section) => section.tasks)
  }
}

export async function getPlanFull(planId: string): Promise<PlanFull> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    planDataSource.value = 'mobile'
    const plans = await getMobileRawPlans()
    const plan = findMobilePlan(plans, planId)
    if (!plan) throw new Error(translate('plans.mobileSnapshotMissing'))
    return toMobilePlanFull(plan, plans.indexOf(plan))
  }
  try {
    const result = await request<PlanFull>(`/api/plans/${encodeURIComponent(planId)}/full`)
    planDataSource.value = 'service'
    return result
  } catch (error) {
    const plans = await getMobileRawPlans()
    const plan = findMobilePlan(plans, planId)
    if (!plan) throw error
    planDataSource.value = 'cache'
    return toMobilePlanFull(plan, plans.indexOf(plan))
  }
}

export async function createEventPlan(
  name: string,
  date: [number, number, number],
  sections: InitialPlanSection[] = [],
): Promise<PlanSummary> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    const plans = cloneMobilePlans(await getMobileRawPlans())
    const nextId = plans.reduce((max, plan, index) => Math.max(max, Number(plan.head?.index ?? index)), 0) + 1
    const main = sections
      .filter((section) => section.name.trim())
      .map((section) => ({
        name: section.name.trim(),
        info: section.info.trim(),
        plan: [null, ...section.tasks
          .filter((task) => task.content.trim())
          .map((task) => ({ is_active: true, content: task.content.trim(), t_m: Math.max(0, Number(task.time_minutes) || 0) / 6 }))],
        group: {},
      }))
    const plan: RawPlan = { head: { index: nextId, name, date }, main, log: [] }
    plans.push(plan)
    await saveMobileRawPlans(plans)
    planDataSource.value = 'mobile'
    return toMobilePlanSummary(plan, plans.length - 1)
  }
  const result = await request<PlanSummary>('/api/plans', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, date, sections }),
  })
  planDataSource.value = 'service'
  return result
}

export async function listPlanTemplates(): Promise<PlanTemplateSummary[]> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    planDataSource.value = 'mobile'
    return MOBILE_TEMPLATE_DEFINITIONS.map(mobileTemplateSummary)
  }
  const data = await request<{ templates?: PlanTemplateSummary[] }>('/api/templates')
  planDataSource.value = 'service'
  return data.templates || []
}

export async function createEventPlanFromTemplate(
  templateId: string,
  name: string,
  date: [number, number, number],
  locale = 'zh-CN',
): Promise<PlanFull> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    const template = MOBILE_TEMPLATE_DEFINITIONS.find((candidate) => candidate.id === templateId)
    if (!template) throw new Error(translate('plans.templateMissing'))
    const created = await createEventPlan(name, date, mobileTemplateSections(template))
    for (const [sectionIndex, section] of template.sections.entries()) {
      for (const group of section.groups || []) {
        await addPlanGroup(
          created.id,
          sectionIndex,
          translate(group.titleKey),
          translate(group.descriptionKey),
          group.start,
          group.end,
        )
      }
    }
    return getPlanFull(created.id)
  }
  const result = await request<PlanFull>('/api/plans/from-template', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ template_id: templateId, name, date, locale }),
  })
  planDataSource.value = 'service'
  return result
}

export async function updateEventPlan(planId: string, name: string, date: [number, number, number]): Promise<PlanFull> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    const plan = await mutateMobilePlan(planId, (raw) => {
      raw.head = { ...(raw.head || {}), index: raw.head?.index ?? Number(planId), name, date }
    })
    return toMobilePlanFull(plan, Number(planId) || 0)
  }
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
  if (getPlanRuntime() === 'mobile-unavailable') {
    await mutateMobilePlan(planId, (plan) => {
      if (!Array.isArray(plan.main)) plan.main = []
      plan.main.push({ name, info, plan: [null], group: {} })
    })
    return
  }
  await request(`/api/plans/${encodeURIComponent(planId)}/sections`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, info }),
  })
}

export async function updatePlanSection(planId: string, sectionIndex: number, name: string, info = ''): Promise<void> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    await mutateMobilePlan(planId, (plan) => {
      const section = plan.main?.[sectionIndex]
      if (!section) throw new Error(translate('plans.sectionMissing'))
      section.name = name
      section.info = info
    })
    return
  }
  await request(`/api/plans/${encodeURIComponent(planId)}/sections/${sectionIndex}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, info }),
  })
}

export async function deletePlanSection(planId: string, sectionIndex: number): Promise<void> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    await mutateMobilePlan(planId, (plan) => {
      const section = plan.main?.[sectionIndex]
      if (!section) throw new Error(translate('plans.sectionMissing'))
      // Match plan.py del_section: clear active task slots without shifting
      // section indexes or rewriting historical task references.
      section.plan = [null]
    })
    return
  }
  await request(`/api/plans/${encodeURIComponent(planId)}/sections/${sectionIndex}`, { method: 'DELETE' })
}

export async function addPlanGroup(planId: string, sectionIndex: number, title: string, description: string, startIndex: number, endIndex: number): Promise<void> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    await mutateMobilePlan(planId, (plan) => {
      const section = plan.main?.[sectionIndex]
      if (!section) throw new Error(translate('plans.sectionMissing'))
      if (!section.group) section.group = {}
      if (startIndex < 0 || endIndex <= startIndex) throw new Error(translate('plans.groupRangeInvalid'))
      if (mobileGroupCrossesExisting(section.group, startIndex, endIndex)) {
        throw new Error(translate('plans.groupConflict'))
      }
      section.group[`${startIndex}_${endIndex}`] = { title, description }
    })
    return
  }
  await request(`/api/plans/${encodeURIComponent(planId)}/sections/${sectionIndex}/groups`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description, start_index: startIndex, end_index: endIndex }),
  })
}

export async function updatePlanGroup(planId: string, sectionIndex: number, groupKey: string, title: string, description: string): Promise<void> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    await mutateMobilePlan(planId, (plan) => {
      const group = plan.main?.[sectionIndex]?.group?.[groupKey]
      if (!group) throw new Error(translate('plans.groupMissing'))
      group.title = title
      group.description = description
    })
    return
  }
  await request(`/api/plans/${encodeURIComponent(planId)}/sections/${sectionIndex}/groups/${encodeURIComponent(groupKey)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description }),
  })
}

export async function deletePlanGroup(planId: string, sectionIndex: number, groupKey: string): Promise<void> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    await mutateMobilePlan(planId, (plan) => {
      if (plan.main?.[sectionIndex]?.group) delete plan.main[sectionIndex].group[groupKey]
    })
    return
  }
  await request(`/api/plans/${encodeURIComponent(planId)}/sections/${sectionIndex}/groups/${encodeURIComponent(groupKey)}`, { method: 'DELETE' })
}

export async function addPlanTask(planId: string, sectionIndex: number, content: string, timeMinutes: number): Promise<void> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    await mutateMobilePlan(planId, (plan) => {
      const section = plan.main?.[sectionIndex]
      if (!section) throw new Error(translate('plans.sectionMissing'))
      if (!Array.isArray(section.plan)) section.plan = [null]
      section.plan.push({ is_active: true, content, t_m: mobileTaskUnit(timeMinutes) })
    })
    return
  }
  await request(`/api/plans/${encodeURIComponent(planId)}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ section_index: sectionIndex, content, time_minutes: timeMinutes }),
  })
}

export async function updatePlanTask(planId: string, taskId: string, content: string, timeMinutes: number): Promise<void> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    await mutateMobilePlan(planId, (plan) => {
      const location = mobileTaskLocation(plan, taskId)
      if (!location) throw new Error(translate('plans.taskMissing'))
      location.task.content = content
      location.task.t_m = mobileTaskUnit(timeMinutes)
    })
    return
  }
  await request(`/api/plans/${encodeURIComponent(planId)}/tasks/${encodeURIComponent(taskId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, time_minutes: timeMinutes }),
  })
}

export async function completePlanTask(planId: string, taskId: string): Promise<void> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    await mutateMobilePlan(planId, (plan) => {
      const location = mobileTaskLocation(plan, taskId)
    if (!location) throw new Error(translate('plans.taskMissing'))
      const current = mobileCurrentTime()
      location.task.finish = current
    })
    return
  }
  await request(`/api/plans/${encodeURIComponent(planId)}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task_id: taskId }),
  })
}

export async function deletePlanTask(planId: string, taskId: string): Promise<void> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    await mutateMobilePlan(planId, (plan) => {
      const location = mobileTaskLocation(plan, taskId)
    if (!location) throw new Error(translate('plans.taskMissing'))
      location.task.is_active = false
    })
    return
  }
  await request(`/api/plans/${encodeURIComponent(planId)}/tasks/${encodeURIComponent(taskId)}`, {
    method: 'DELETE',
  })
}

export async function addPlanLog(planId: string, day: number, taskId: string, content: string): Promise<void> {
  if (getPlanRuntime() === 'mobile-unavailable') {
    await mutateMobilePlan(planId, (plan) => {
      if (!Array.isArray(plan.log)) plan.log = []
      const current = mobileCurrentTime()
      plan.log.push({ index: plan.log.length, day, plan: taskId || 'base', time: current.time, content })
    })
    return
  }
  await request(`/api/plans/${encodeURIComponent(planId)}/logs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ day, task_id: taskId || 'base', time: 'acc', content }),
  })
}
