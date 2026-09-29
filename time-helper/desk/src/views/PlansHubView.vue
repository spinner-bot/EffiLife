<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Check, ChevronRight, Clock3, FolderPlus, ListTodo, Pencil, Plus, Trash2 } from 'lucide-vue-next'
import { AudioManager } from '@/audio'
import { useI18n } from '@/i18n'
import {
  addPlanSection,
  updatePlanSection,
  deletePlanSection,
  addPlanGroup,
  addPlanLog,
  addPlanTask,
  archivePlan,
  completePlanTask,
  createEventPlan,
  createEventPlanFromTemplate,
  deletePlanTask,
  deletePlanGroup,
  getPlanFull,
  listPlanArchives,
  listPlanSummaries,
  listPlanTemplates,
  restorePlanArchive,
  type PlanArchiveSummary,
  type PlanFull,
  type PlanSummary,
  type PlanTemplateSummary,
  updatePlanTask,
  updatePlanGroup,
  updateEventPlan,
  planDataSource,
} from '@/services/planGateway'
import { completeLinkedTodos, syncTodoDescriptionsFromPlan, syncTodosFromPlanTask, unlinkTodosFromPlanTask } from '@/services/workspaceSync'
import { TodoService } from '@/services/todoService'
import { getPlanRuntime } from '@/services/runtimeCapabilities'
import { notifyToast } from '@/services/toastService'
import { requestConfirm } from '@/services/confirmService'
import { onWorkspaceChanged } from '@/services/workspaceEvents'

const DailyPlanView = defineAsyncComponent(() => import('@/views/PlanView.vue'))

const router = useRouter()
const route = useRoute()
const { t, locale } = useI18n()
const isMobilePlanRuntime = getPlanRuntime() === 'mobile-unavailable'
const canEditPlan = computed(() => isMobilePlanRuntime || planDataSource.value !== 'cache')
const canArchivePlan = !isMobilePlanRuntime
const view = ref<'hub' | 'events' | 'detail' | 'time'>(route.query.mode === 'time' ? 'time' : 'hub')
const plans = ref<PlanSummary[]>([])
const archives = ref<PlanArchiveSummary[]>([])
const selectedPlan = ref<PlanFull | null>(null)
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const searchTargetTaskId = ref<string | null>(null)
const showCreate = ref(false)
const createNameInput = ref<HTMLInputElement | null>(null)
const createReturnFocus = ref<HTMLElement | null>(null)
const planName = ref('')
const planDate = ref(toDateInput(new Date()))
const createSectionName = ref('')
const createSectionInfo = ref('')
const createTaskContent = ref('')
const createTaskMinutes = ref(30)
const createTodosOnCreate = ref(false)
const planTemplates = ref<PlanTemplateSummary[]>([])
const selectedTemplateId = ref('')
const templatesLoading = ref(false)
const selectedTemplate = computed(() => planTemplates.value.find((template) => template.id === selectedTemplateId.value) || null)
const editingMeta = ref(false)
const sectionName = ref('')
const sectionInfo = ref('')
const editingSectionIndex = ref<number | null>(null)
const taskSectionIndex = ref<number | null>(null)
const editingTaskId = ref<string | null>(null)
const editingTaskDisplayId = ref<string | null>(null)
const editingTaskSectionIndex = ref<number | null>(null)
const taskContent = ref('')
const taskMinutes = ref(30)
const groupSectionIndex = ref<number | null>(null)
const editingGroupKey = ref<string | null>(null)
const groupTitle = ref('')
const groupDescription = ref('')
const groupStart = ref(0)
const groupEnd = ref(1)
const logTaskId = ref('base')
const logDay = ref(new Date().getDate())
const logContent = ref('')
const linkedTodoIdsByTask = ref(new Map<string, string>())

function showPlanSaved(): void {
  successMessage.value = t('plans.saved')
  notifyToast(t('plans.saved'), 'success')
}

async function refreshPlanTodoLinks(planId?: string): Promise<void> {
  if (!planId) {
    linkedTodoIdsByTask.value = new Map()
    return
  }
  try {
    const todos = await TodoService.list()
    linkedTodoIdsByTask.value = new Map(
      todos
        .filter((todo) => todo.related_plan_id === String(planId) && todo.related_plan_task_id && !['archived', 'cancelled'].includes(todo.status))
        .map((todo) => [String(todo.related_plan_task_id), todo.id]),
    )
  } catch {
    linkedTodoIdsByTask.value = new Map()
  }
}

function isTaskLinkedToTodo(task: PlanFull['sections'][number]['tasks'][number]): boolean {
  return linkedTodoIdsByTask.value.has(String(task.internal_id)) || linkedTodoIdsByTask.value.has(String(task.display_id))
}

function openLinkedTodo(task: PlanFull['sections'][number]['tasks'][number]): void {
  const todoId = linkedTodoIdsByTask.value.get(String(task.internal_id)) || linkedTodoIdsByTask.value.get(String(task.display_id))
  if (todoId) router.push({ path: '/tasks', query: { todo: todoId } })
}

function openLinkedTaskRecord(task: PlanFull['sections'][number]['tasks'][number]): void {
  const todoId = linkedTodoIdsByTask.value.get(String(task.internal_id)) || linkedTodoIdsByTask.value.get(String(task.display_id))
  if (todoId) router.push({ path: '/records', query: { todo: todoId } })
}

const stopWorkspaceListener = onWorkspaceChanged((source) => {
  if (isLoading.value) return
  void refreshFromWorkspace(source).catch((error) => {
    console.warn('Failed to refresh plans after external change:', error)
  })
})

function toDateInput(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function toDateTuple(value: string): [number, number, number] {
  const [year, month, day] = value.split('-').map(Number)
  return [year, month, day]
}

function formatPlanDate(date?: [number, number, number]): string {
  if (!date) return ''
  const [year, month, day] = date
  const value = new Date(year, month - 1, day)
  return new Intl.DateTimeFormat(locale.value, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(value)
}

function formatLogTime(time?: [number, number]): string {
  if (!time || time.length < 2 || time[0] === 99 || time[1] === 99) return t('plans.timeUnknown')
  return `${String(time[0]).padStart(2, '0')}:${String(time[1]).padStart(2, '0')}`
}

async function loadPlans() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const [activePlans, archivedPlans] = await Promise.all([listPlanSummaries(), listPlanArchives()])
    plans.value = activePlans
    archives.value = archivedPlans
  } catch (error) {
    plans.value = []
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function refreshFromWorkspace(source?: string): Promise<void> {
  if (!source || !['todos', 'plans', 'archive'].includes(source)) return
  if (source === 'todos') {
    if (selectedPlan.value) await refreshPlanTodoLinks(selectedPlan.value.id)
    return
  }
  if (selectedPlan.value && source === 'plans') {
    selectedPlan.value = await getPlanFull(selectedPlan.value.id)
    return
  }
  if (view.value === 'events') await loadPlans()
  if (view.value === 'hub') await loadPlans()
  if (selectedPlan.value) await refreshPlanTodoLinks(selectedPlan.value.id)
}

async function archiveSelectedPlan() {
  if (isLoading.value) return
  if (!selectedPlan.value || !(await requestConfirm(t('plans.archiveConfirm'), { tone: 'danger' }))) return
  const planId = selectedPlan.value.id
  isLoading.value = true
  errorMessage.value = ''
  try {
    await archivePlan(planId)
    selectedPlan.value = null
    view.value = 'events'
    await loadPlans()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function restoreArchive(archive: PlanArchiveSummary) {
  if (isLoading.value) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    await restorePlanArchive(archive.file)
    await loadPlans()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

function openCreatePlan() {
  createReturnFocus.value = document.activeElement instanceof HTMLElement ? document.activeElement : null
  planName.value = ''
  planDate.value = toDateInput(new Date())
  createSectionName.value = ''
  createSectionInfo.value = ''
  createTaskContent.value = ''
  createTaskMinutes.value = 30
  createTodosOnCreate.value = false
  selectedTemplateId.value = ''
  void loadPlanTemplates()
  errorMessage.value = ''
  showCreate.value = true
  void nextTick(() => createNameInput.value?.focus())
}

function closeCreatePlan() {
  showCreate.value = false
  createSectionName.value = ''
  createSectionInfo.value = ''
  createTaskContent.value = ''
  createTaskMinutes.value = 30
  createTodosOnCreate.value = false
  selectedTemplateId.value = ''
  const returnTarget = createReturnFocus.value
  createReturnFocus.value = null
  void nextTick(() => {
    if (returnTarget?.isConnected) returnTarget.focus()
  })
}

async function loadPlanTemplates(): Promise<void> {
  templatesLoading.value = true
  try {
    planTemplates.value = await listPlanTemplates()
  } catch {
    planTemplates.value = []
  } finally {
    templatesLoading.value = false
  }
}

function openTimePlan() {
  view.value = 'time'
  router.replace({ path: '/plans', query: { mode: 'time' } })
}

async function openPlan(plan: PlanSummary) {
  if (isLoading.value) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    selectedPlan.value = await getPlanFull(plan.id)
    view.value = 'detail'
    await router.replace({ path: '/plans', query: { ...route.query, plan: String(plan.id) } })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function retryPlanService() {
  if (isLoading.value) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    if (selectedPlan.value) {
      selectedPlan.value = await getPlanFull(selectedPlan.value.id)
    } else {
      await loadPlans()
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function createPlan() {
  if (isLoading.value) return
  const name = planName.value.trim()
  if (!name || !planDate.value) return
  if (!selectedTemplateId.value && (!createSectionName.value.trim() || !createTaskContent.value.trim())) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    const linkTodosAfterCreate = createTodosOnCreate.value
    let createdId: string | number
    if (selectedTemplateId.value) {
      const created = await createEventPlanFromTemplate(selectedTemplateId.value, name, toDateTuple(planDate.value))
      createdId = created.id
      selectedPlan.value = created
    } else {
      const created = await createEventPlan(name, toDateTuple(planDate.value), [{
        name: createSectionName.value.trim(),
        info: createSectionInfo.value.trim(),
        tasks: [{ content: createTaskContent.value.trim(), time_minutes: Math.max(0, Number(createTaskMinutes.value) || 0) }],
      }])
      createdId = created.id
      selectedPlan.value = await getPlanFull(created.id)
    }
    if (linkTodosAfterCreate && selectedPlan.value) {
      try {
        const result = await linkPendingPlanTasksToTodos(selectedPlan.value)
        if (result.failed > 0) notifyToast(t('plans.todoSyncFailed'), 'error')
        if (result.created > 0) notifyToast(t('plans.todosBulkCreated', { count: result.created }), 'success')
      } catch {
        // The plan is already created; keep it usable and let the detail page
        // expose the existing bulk-link action for a later retry.
        notifyToast(t('plans.todoSyncFailed'), 'error')
      }
    }
    closeCreatePlan()
    planName.value = ''
    view.value = 'detail'
    await router.replace({ path: '/plans', query: { plan: String(createdId) } })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function savePlanMeta() {
  if (isLoading.value) return
  if (!selectedPlan.value || !planName.value.trim() || !planDate.value) return
  isLoading.value = true
  try {
    const planId = selectedPlan.value.id
    const previousName = selectedPlan.value.name
    await updateEventPlan(planId, planName.value.trim(), toDateTuple(planDate.value))
    try {
      await syncTodoDescriptionsFromPlan(planId, previousName, planName.value.trim())
    } catch {
      errorMessage.value = t('plans.todoSyncFailed')
    }
    selectedPlan.value = await getPlanFull(planId)
    editingMeta.value = false
    showPlanSaved()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

function startMetaEdit() {
  if (!selectedPlan.value) return
  planName.value = selectedPlan.value.name
  planDate.value = selectedPlan.value.date ? `${selectedPlan.value.date[0]}-${String(selectedPlan.value.date[1]).padStart(2, '0')}-${String(selectedPlan.value.date[2]).padStart(2, '0')}` : toDateInput(new Date())
  editingMeta.value = true
}

async function saveSection() {
  if (isLoading.value) return
  if (!selectedPlan.value || !sectionName.value.trim()) return
  const planId = selectedPlan.value.id
  isLoading.value = true
  errorMessage.value = ''
  try {
    if (editingSectionIndex.value === null) {
      await addPlanSection(planId, sectionName.value.trim(), sectionInfo.value.trim())
    } else {
      await updatePlanSection(planId, editingSectionIndex.value, sectionName.value.trim(), sectionInfo.value.trim())
    }
    sectionName.value = ''
    sectionInfo.value = ''
    editingSectionIndex.value = null
    selectedPlan.value = await getPlanFull(planId)
    showPlanSaved()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

function startSectionEdit(section: PlanFull['sections'][number]) {
  editingSectionIndex.value = section.index
  sectionName.value = section.name
  sectionInfo.value = section.info
}

function cancelSectionEdit() {
  editingSectionIndex.value = null
  sectionName.value = ''
  sectionInfo.value = ''
}

async function deleteSection(section: PlanFull['sections'][number]) {
  if (isLoading.value || !selectedPlan.value || !(await requestConfirm(t('plans.deleteSectionConfirm'), { tone: 'danger' }))) return
  const planId = selectedPlan.value.id
  isLoading.value = true
  errorMessage.value = ''
  try {
    await deletePlanSection(planId, section.index)
    for (const task of section.tasks) {
      try {
        await unlinkTodosFromPlanTask(planId, task.internal_id)
        if (task.display_id !== task.internal_id) {
          await unlinkTodosFromPlanTask(planId, task.display_id)
        }
      } catch {
        errorMessage.value = t('plans.todoSyncFailed')
      }
    }
    cancelSectionEdit()
    selectedPlan.value = await getPlanFull(planId)
    showPlanSaved()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.sectionUnavailable')
  } finally {
    isLoading.value = false
  }
}

async function saveTask() {
  if (isLoading.value) return
  if (!selectedPlan.value || !taskContent.value.trim()) return
  const planId = selectedPlan.value.id
  const minutes = Math.max(0, Number(taskMinutes.value) || 0)
  if (!editingTaskId.value && taskSectionIndex.value === null) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    if (editingTaskId.value) {
      await updatePlanTask(planId, editingTaskId.value, taskContent.value.trim(), minutes)
      try {
        await syncTodosFromPlanTask(
          planId,
          [editingTaskId.value, ...(editingTaskDisplayId.value && editingTaskDisplayId.value !== editingTaskId.value ? [editingTaskDisplayId.value] : [])],
          taskContent.value.trim(),
          minutes,
        )
      } catch {
        errorMessage.value = t('plans.todoSyncFailed')
      }
    } else if (taskSectionIndex.value !== null) {
      await addPlanTask(planId, taskSectionIndex.value, taskContent.value.trim(), minutes)
    }
    taskContent.value = ''
    taskMinutes.value = 30
    taskSectionIndex.value = null
    editingTaskId.value = null
    editingTaskDisplayId.value = null
    editingTaskSectionIndex.value = null
    selectedPlan.value = await getPlanFull(planId)
    showPlanSaved()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function saveLog() {
  if (isLoading.value) return
  if (!selectedPlan.value || !logContent.value.trim()) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    await addPlanLog(selectedPlan.value.id, Math.max(0, Math.min(31, Math.trunc(Number(logDay.value) || new Date().getDate()))), logTaskId.value, logContent.value.trim())
    logContent.value = ''
    selectedPlan.value = await getPlanFull(selectedPlan.value.id)
    showPlanSaved()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.logUnavailable')
  } finally {
    isLoading.value = false
  }
}

function startLog(taskId = 'base') {
  logTaskId.value = taskId
  logContent.value = ''
}

function groupEntries(section: PlanFull['sections'][number]) {
  const entries = Object.entries(section.groups || {}).flatMap(([key, group]) => {
    const [start, end] = key.split('_').map(Number)
    return Number.isInteger(start) && Number.isInteger(end)
      ? [{ key, start, end, title: group.title, description: group.description }]
      : []
  }).sort((left, right) => left.start - right.start || right.end - left.end)

  return entries.map((entry) => ({
    ...entry,
    depth: entries.filter((parent) => parent !== entry && parent.start <= entry.start && parent.end >= entry.end).length,
  }))
}

function startNewGroup(section: PlanFull['sections'][number]) {
  const taskIndexes = section.tasks.map((task) => task.internal_index)
  groupSectionIndex.value = section.index
  editingGroupKey.value = null
  groupTitle.value = ''
  groupDescription.value = ''
  groupStart.value = taskIndexes[0] ?? 0
  groupEnd.value = taskIndexes[taskIndexes.length - 1] ?? 1
}

function startGroupEdit(section: PlanFull['sections'][number], group: ReturnType<typeof groupEntries>[number]) {
  groupSectionIndex.value = section.index
  editingGroupKey.value = group.key
  groupTitle.value = group.title
  groupDescription.value = group.description
  groupStart.value = group.start
  groupEnd.value = group.end
}

function cancelGroupEdit() {
  groupSectionIndex.value = null
  editingGroupKey.value = null
  groupTitle.value = ''
  groupDescription.value = ''
}

async function saveGroup() {
  if (isLoading.value) return
  if (!selectedPlan.value || groupSectionIndex.value === null || !groupTitle.value.trim()) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    if (editingGroupKey.value) {
      await updatePlanGroup(selectedPlan.value.id, groupSectionIndex.value, editingGroupKey.value, groupTitle.value.trim(), groupDescription.value.trim())
    } else {
      await addPlanGroup(selectedPlan.value.id, groupSectionIndex.value, groupTitle.value.trim(), groupDescription.value.trim(), groupStart.value, groupEnd.value)
    }
    selectedPlan.value = await getPlanFull(selectedPlan.value.id)
    cancelGroupEdit()
    showPlanSaved()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.groupUnavailable')
  } finally {
    isLoading.value = false
  }
}

async function deleteGroup(sectionIndex: number, groupKey: string) {
  if (isLoading.value) return
  if (!selectedPlan.value || !(await requestConfirm(t('plans.deleteGroupConfirm'), { tone: 'danger' }))) return
  isLoading.value = true
  try {
    await deletePlanGroup(selectedPlan.value.id, sectionIndex, groupKey)
    selectedPlan.value = await getPlanFull(selectedPlan.value.id)
    cancelGroupEdit()
    showPlanSaved()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.groupUnavailable')
  } finally {
    isLoading.value = false
  }
}

function startTaskEdit(sectionIndex: number, task: PlanFull['sections'][number]['tasks'][number]) {
  taskSectionIndex.value = null
  editingTaskId.value = task.internal_id
  editingTaskDisplayId.value = task.display_id
  editingTaskSectionIndex.value = sectionIndex
  taskContent.value = task.content
  taskMinutes.value = task.time_minutes
}

function cancelTaskEdit() {
  taskSectionIndex.value = null
  editingTaskId.value = null
  editingTaskDisplayId.value = null
  editingTaskSectionIndex.value = null
  taskContent.value = ''
  taskMinutes.value = 30
}

async function completeTask(taskId: string, displayTaskId = taskId) {
  if (isLoading.value) return
  if (!selectedPlan.value) return
  const planId = selectedPlan.value.id
  isLoading.value = true
  errorMessage.value = ''
  try {
    await completePlanTask(planId, taskId)
    try {
      await completeLinkedTodos(planId, [taskId, displayTaskId])
    } catch {
      errorMessage.value = t('plans.todoSyncFailed')
    }
    selectedPlan.value = await getPlanFull(planId)
    showPlanSaved()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function addTaskToTodos(task: PlanFull['sections'][number]['tasks'][number]) {
  if (isLoading.value || !selectedPlan.value) return
  const planId = String(selectedPlan.value.id)
  isLoading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const todos = await TodoService.list()
    const existing = todos.find((todo) =>
      todo.related_plan_id === planId
      && (
        todo.related_plan_task_id === String(task.internal_id)
        || todo.related_plan_task_id === String(task.display_id)
      )
      && !['archived', 'cancelled'].includes(todo.status)
    )
    if (existing) {
      linkedTodoIdsByTask.value = new Map(linkedTodoIdsByTask.value).set(String(existing.related_plan_task_id), existing.id)
      errorMessage.value = t('plans.todoAlreadyLinked')
      return
    }
    const createdTodo = await TodoService.create({
      title: task.content,
      description: selectedPlan.value.name,
      related_plan_id: planId,
      related_plan_task_id: String(task.internal_id),
      time_estimate: task.time_minutes,
      estimated_time: task.time_minutes,
    })
    linkedTodoIdsByTask.value = new Map(linkedTodoIdsByTask.value).set(String(task.internal_id), createdTodo.id)
    successMessage.value = t('plans.todoCreated')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.todoCreateFailed')
  } finally {
    isLoading.value = false
  }
}

async function linkPendingPlanTasksToTodos(plan: PlanFull): Promise<{ created: number; failed: number }> {
  const existingTodos = await TodoService.list()
  const activeLinks = new Set(
    existingTodos
      .filter((todo) => todo.related_plan_id === String(plan.id) && todo.related_plan_task_id && !['archived', 'cancelled'].includes(todo.status))
      .map((todo) => String(todo.related_plan_task_id)),
  )
  const pendingTasks = plan.sections
    .flatMap((section) => section.tasks)
    .filter((task) => !task.finish && !activeLinks.has(String(task.internal_id)) && !activeLinks.has(String(task.display_id)))
  let created = 0
  let failed = 0
  for (const task of pendingTasks) {
    try {
      await TodoService.create({
        title: task.content,
        description: plan.name,
        related_plan_id: String(plan.id),
        related_plan_task_id: String(task.internal_id),
        time_estimate: task.time_minutes,
        estimated_time: task.time_minutes,
      })
      activeLinks.add(String(task.internal_id))
      created += 1
    } catch {
      failed += 1
    }
  }
  await refreshPlanTodoLinks(plan.id)
  return { created, failed }
}

async function addAllTasksToTodos() {
  if (isLoading.value || !selectedPlan.value) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    const result = await linkPendingPlanTasksToTodos(selectedPlan.value)
    if (result.created > 0) notifyToast(t('plans.todosBulkCreated', { count: result.created }), 'success')
    if (result.failed > 0) notifyToast(t('plans.todoSyncFailed'), 'error')
    if (result.created === 0 && result.failed === 0) notifyToast(t('plans.todosAllLinked'), 'info')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.todoCreateFailed')
  } finally {
    isLoading.value = false
  }
}

async function deleteTask(taskId: string, displayTaskId = taskId) {
  if (isLoading.value) return
  if (!selectedPlan.value || !(await requestConfirm(`${t('plans.delete')}?`, { tone: 'danger' }))) return
  const planId = selectedPlan.value.id
  isLoading.value = true
  errorMessage.value = ''
  try {
    await deletePlanTask(planId, taskId)
    try {
      await unlinkTodosFromPlanTask(planId, taskId)
      if (displayTaskId !== taskId) {
        await unlinkTodosFromPlanTask(planId, displayTaskId)
      }
    } catch {
      // The plan deletion is already accepted; keep the view current and
      // surface the secondary cleanup failure without masking the deletion.
      errorMessage.value = t('plans.todoSyncFailed')
    }
    selectedPlan.value = await getPlanFull(planId)
    showPlanSaved()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

function backFromDetail() {
  selectedPlan.value = null
  editingMeta.value = false
  view.value = 'events'
  router.replace({ path: '/plans', query: {} })
  loadPlans()
}

const activeTaskCount = computed(() => selectedPlan.value?.sections.reduce((total, section) => total + section.tasks.length, 0) || 0)
const completedTaskCount = computed(() => selectedPlan.value?.sections.reduce((total, section) => total + section.tasks.filter((task) => task.finish).length, 0) || 0)
const selectedPlanProgress = computed(() => activeTaskCount.value > 0
  ? Math.round((completedTaskCount.value / activeTaskCount.value) * 100)
  : 0)

watch(() => selectedPlan.value?.id, (planId) => {
  void refreshPlanTodoLinks(planId)
}, { immediate: true })

function planProgress(plan: PlanSummary): number {
  const total = Number(plan.total_tasks || 0)
  return total > 0 ? Math.round((Number(plan.completed_tasks || 0) / total) * 100) : 0
}

async function revealSearchTarget(): Promise<void> {
  const targetId = String(route.query.plan || '')
  if (!targetId) return
  const target = plans.value.find((plan) => String(plan.id) === targetId)
  if (!target) return
  if (String(selectedPlan.value?.id) !== targetId) await openPlan(target)
  const taskId = String(route.query.task || '')
  const task = selectedPlan.value?.sections
    .flatMap((section) => section.tasks)
    .find((item) => item.internal_id === taskId || item.display_id === taskId)
  if (!task) return
  const internalTaskId = task.internal_id
  searchTargetTaskId.value = internalTaskId
  await nextTick()
  document.getElementById(`plan-task-${internalTaskId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  window.setTimeout(() => { searchTargetTaskId.value = null }, 2200)
}

onMounted(async () => {
  await loadPlans()
  await revealSearchTarget()
})

watch(() => [route.query.plan, route.query.task], () => {
  if (plans.value.length > 0) void revealSearchTarget()
})

onUnmounted(() => {
  stopWorkspaceListener()
})
</script>

<template>
  <div class="plans-hub">
    <header v-if="view !== 'time'" class="plans-header">
      <button class="plans-back" @click="AudioManager.playSound('click'); router.push('/')" :aria-label="t('plans.back')">
        <ArrowLeft :size="18" />
      </button>
      <div>
        <p class="plans-eyebrow">{{ t('plans.center') }}</p>
        <h1>{{ view === 'detail' ? selectedPlan?.name : t('plans.center') }}</h1>
      </div>
      <button v-if="(view === 'events' || view === 'hub') && canEditPlan" class="plans-primary" @click="openCreatePlan"><Plus :size="16" /> {{ t('plans.create') }}</button>
    </header>

    <main class="plans-content">
      <DailyPlanView v-if="view === 'time'" />

      <template v-else-if="view === 'hub'">
        <section class="unified-plan-section">
          <div class="unified-section-heading">
            <div><p class="plans-eyebrow">{{ t('plans.time') }}</p><h2>{{ t('plans.timeDescription') }}</h2></div>
            <button class="plans-secondary" @click="openTimePlan"><Clock3 :size="15" /> {{ t('plans.time') }}</button>
          </div>
          <DailyPlanView :embedded="true" />
        </section>
        <section class="unified-plan-section event-plans-section">
          <div class="unified-section-heading">
            <div><p class="plans-eyebrow">{{ t('plans.events') }}</p><h2>{{ t('plans.eventsDescription') }}</h2></div>
            <button v-if="canEditPlan" class="plans-secondary" @click="openCreatePlan"><Plus :size="15" /> {{ t('plans.create') }}</button>
          </div>
          <p v-if="errorMessage" class="plans-error">{{ errorMessage }}</p>
          <div v-if="!isMobilePlanRuntime && planDataSource === 'cache'" class="plans-readonly-note plans-list-source-note">
            <div><strong>{{ t('plans.cachedTitle') }}</strong><span>{{ t('plans.cachedDescription') }}</span></div>
            <button class="plans-secondary plans-retry" :disabled="isLoading" @click="retryPlanService">{{ isLoading ? t('plans.loading') : t('plans.retryService') }}</button>
          </div>
          <section v-if="isLoading" class="plans-empty theme-card">{{ t('plans.loading') }}</section>
          <section v-else-if="plans.length === 0" class="plans-empty theme-card">
            <FolderPlus :size="34" />
            <strong>{{ t('plans.empty') }}</strong>
            <span>{{ t('plans.emptyHint') }}</span>
            <button v-if="canEditPlan" class="plans-primary" @click="openCreatePlan"><Plus :size="16" /> {{ t('plans.create') }}</button>
          </section>
          <section v-else class="event-plan-grid">
            <button v-for="plan in plans" :key="plan.id" class="event-plan-card theme-card" @click="openPlan(plan)">
              <div class="event-plan-card-top"><span>#{{ plan.id }}</span><ChevronRight :size="17" /></div>
              <strong>{{ plan.name }}</strong>
              <span>{{ formatPlanDate(plan.date) }}</span>
              <div class="plan-progress-meta"><small>{{ plan.completed_tasks || 0 }}/{{ plan.total_tasks || 0 }} {{ t('plans.tasks') }}</small><small>{{ planProgress(plan) }}%</small></div>
              <div class="plan-progress-track"><span :style="{ width: `${planProgress(plan)}%` }" /></div>
            </button>
          </section>
          <section class="archives-panel theme-card">
            <header><div><h2>{{ t('plans.archived') }}</h2><p>{{ t('plans.archivedAt') }}</p></div></header>
            <p v-if="archives.length === 0" class="section-empty">{{ t('plans.noArchives') }}</p>
            <div v-for="archive in archives" :key="archive.file" class="archive-row">
              <div><strong>{{ archive.name || archive.file }}</strong><span>{{ formatPlanDate(archive.date) }}</span></div>
              <button v-if="canArchivePlan" class="plans-secondary" :disabled="isLoading" @click="restoreArchive(archive)">{{ t('plans.restore') }}</button>
            </div>
          </section>
        </section>
      </template>

      <template v-else-if="view === 'events'">
        <p v-if="errorMessage" class="plans-error">{{ errorMessage }}</p>
        <div v-if="!isMobilePlanRuntime && planDataSource === 'cache'" class="plans-readonly-note plans-list-source-note">
          <div><strong>{{ t('plans.cachedTitle') }}</strong><span>{{ t('plans.cachedDescription') }}</span></div>
          <button class="plans-secondary plans-retry" :disabled="isLoading" @click="retryPlanService">{{ isLoading ? t('plans.loading') : t('plans.retryService') }}</button>
        </div>
        <section v-if="isLoading" class="plans-empty theme-card">{{ t('plans.loading') }}</section>
        <section v-else-if="plans.length === 0" class="plans-empty theme-card">
          <FolderPlus :size="34" />
          <strong>{{ t('plans.empty') }}</strong>
          <span>{{ t('plans.emptyHint') }}</span>
          <button v-if="canEditPlan" class="plans-primary" @click="openCreatePlan"><Plus :size="16" /> {{ t('plans.create') }}</button>
        </section>
        <section v-else class="event-plan-grid">
          <button v-for="plan in plans" :key="plan.id" class="event-plan-card theme-card" @click="openPlan(plan)">
            <div class="event-plan-card-top"><span>#{{ plan.id }}</span><ChevronRight :size="17" /></div>
            <strong>{{ plan.name }}</strong>
            <span>{{ formatPlanDate(plan.date) }}</span>
            <div class="plan-progress-meta"><small>{{ plan.completed_tasks || 0 }}/{{ plan.total_tasks || 0 }} {{ t('plans.tasks') }}</small><small>{{ planProgress(plan) }}%</small></div>
            <div class="plan-progress-track"><span :style="{ width: `${planProgress(plan)}%` }" /></div>
          </button>
        </section>
        <section class="archives-panel theme-card">
          <header><div><h2>{{ t('plans.archived') }}</h2><p>{{ t('plans.archivedAt') }}</p></div></header>
          <p v-if="archives.length === 0" class="section-empty">{{ t('plans.noArchives') }}</p>
          <div v-for="archive in archives" :key="archive.file" class="archive-row">
            <div><strong>{{ archive.name || archive.file }}</strong><span>{{ formatPlanDate(archive.date) }}</span></div>
            <button v-if="canArchivePlan" class="plans-secondary" :disabled="isLoading" @click="restoreArchive(archive)">{{ t('plans.restore') }}</button>
          </div>
        </section>
      </template>

      <template v-else-if="selectedPlan">
        <div v-if="errorMessage" class="plans-error">{{ errorMessage }}</div>
        <div v-if="successMessage" class="plans-success">{{ successMessage }}</div>
        <div v-if="isMobilePlanRuntime" class="plans-readonly-note">
          <strong>{{ t('plans.mobileLocalTitle') }}</strong>
          <span>{{ t('plans.mobileLocalDescription') }}</span>
        </div>
        <div v-else-if="planDataSource === 'cache'" class="plans-readonly-note">
          <strong>{{ t('plans.cachedTitle') }}</strong>
          <span>{{ t('plans.cachedDescription') }}</span>
          <button class="plans-secondary plans-retry" :disabled="isLoading" @click="retryPlanService">{{ isLoading ? t('plans.loading') : t('plans.retryService') }}</button>
        </div>
        <div class="detail-toolbar">
          <button class="plans-link" @click="backFromDetail">← {{ t('plans.back') }}</button>
          <div v-if="canEditPlan" class="detail-actions">
            <button class="plans-secondary" @click="startMetaEdit"><Pencil :size="15" /> {{ t('plans.edit') }}</button>
            <button class="plans-secondary" :disabled="isLoading || !activeTaskCount" @click="addAllTasksToTodos"><ListTodo :size="15" /> {{ t('plans.linkAllTodos') }}</button>
            <button v-if="canArchivePlan" class="plans-secondary" :disabled="isLoading" @click="archiveSelectedPlan">{{ t('plans.archive') }}</button>
          </div>
        </div>
        <form v-if="editingMeta && canEditPlan" class="meta-editor theme-card" @submit.prevent="savePlanMeta">
          <label>{{ t('plans.name') }}<input v-model="planName" required /></label>
          <label>{{ t('plans.date') }}<input v-model="planDate" type="date" required /></label>
          <div><button type="button" class="plans-secondary" @click="editingMeta = false">{{ t('plans.cancel') }}</button><button type="submit" class="plans-primary">{{ t('plans.save') }}</button></div>
        </form>
        <section class="plan-detail-summary theme-card">
          <div><span>{{ t('plans.date') }}</span><strong>{{ formatPlanDate(selectedPlan.date) }}</strong></div>
          <div><span>{{ t('plans.events') }}</span><strong>{{ activeTaskCount }}</strong></div>
          <div><span>{{ t('plans.completed') }}</span><strong>{{ completedTaskCount }}</strong></div>
          <div class="plan-detail-progress"><span>{{ t('plans.progress') }}</span><strong>{{ selectedPlanProgress }}%</strong><div class="plan-progress-track"><span :style="{ width: `${selectedPlanProgress}%` }" /></div></div>
        </section>
        <form v-if="canEditPlan" class="log-editor theme-card" @submit.prevent="saveLog">
          <div class="log-editor-heading"><div><strong>{{ t('plans.recordProgress') }}</strong><small>{{ t('plans.recordProgressHint') }}</small></div></div>
          <label>{{ t('plans.logTask') }}
            <select v-model="logTaskId">
              <option value="base">{{ t('plans.generalProgress') }}</option>
              <template v-for="section in selectedPlan.sections" :key="section.index">
                <option v-for="task in section.tasks" :key="task.internal_id" :value="task.internal_id">{{ task.display_id }} · {{ task.content }}</option>
              </template>
            </select>
          </label>
          <label>{{ t('plans.logDay') }}<input v-model.number="logDay" type="number" min="0" max="31" /></label>
          <label for="plan-log-content">{{ t('plans.logContent') }}</label>
          <input id="plan-log-content" v-model="logContent" class="log-content-input" :placeholder="t('plans.logContentPlaceholder')" />
          <button type="submit" class="plans-primary" :disabled="isLoading || !logContent.trim()">{{ t('plans.record') }}</button>
        </form>
        <section v-if="selectedPlan.logs.length" class="log-list theme-card">
          <header><strong>{{ t('plans.progressHistory') }}</strong><small>{{ selectedPlan.logs.length }}</small></header>
          <article v-for="log in [...selectedPlan.logs].reverse()" :key="log.index" class="log-row">
            <div class="log-time"><strong>{{ log.day }}</strong><span>{{ formatLogTime(log.time) }}</span></div>
            <div><strong>{{ log.plan }}</strong><p>{{ log.content }}</p></div>
          </article>
        </section>
        <form v-if="canEditPlan" class="section-editor theme-card" @submit.prevent="saveSection">
          <label for="plan-section-name">{{ t('plans.sectionName') }}</label>
          <input id="plan-section-name" v-model="sectionName" :placeholder="t('plans.sectionName')" required />
          <label for="plan-section-info">{{ t('plans.sectionInfo') }}</label>
          <input id="plan-section-info" v-model="sectionInfo" :placeholder="t('plans.sectionInfo')" />
          <div class="section-editor-actions"><button v-if="editingSectionIndex !== null" type="button" class="plans-secondary" :disabled="isLoading" @click="cancelSectionEdit">{{ t('plans.cancel') }}</button><button type="submit" class="plans-secondary" :disabled="isLoading"><Pencil v-if="editingSectionIndex !== null" :size="15" /><Plus v-else :size="15" /> {{ editingSectionIndex !== null ? t('plans.saveSection') : t('plans.addSection') }}</button></div>
        </form>
        <section v-if="selectedPlan.sections.length === 0" class="plans-empty theme-card">{{ t('plans.noSections') }}</section>
        <section v-for="section in selectedPlan.sections" :key="section.index" class="plan-section theme-card">
          <header><div><span class="section-letter">{{ section.letter }}</span><strong>{{ section.name }}</strong><small>{{ section.info }}</small></div><div v-if="canEditPlan" class="section-actions"><button class="plans-secondary" :disabled="isLoading" @click="startSectionEdit(section)"><Pencil :size="15" /> {{ t('plans.editSection') }}</button><button class="plans-secondary" :disabled="isLoading" @click="deleteSection(section)"><Trash2 :size="15" /> {{ t('plans.deleteSection') }}</button><button class="plans-secondary" :disabled="isLoading" @click="taskSectionIndex = section.index"><Plus :size="15" /> {{ t('plans.addTask') }}</button><button class="plans-secondary" :disabled="isLoading || !section.tasks.length" @click="startNewGroup(section)"><Plus :size="15" /> {{ t('plans.addGroup') }}</button></div></header>
          <form v-if="canEditPlan && (taskSectionIndex === section.index || editingTaskSectionIndex === section.index)" class="task-editor" @submit.prevent="saveTask">
            <label>{{ t('plans.taskContent') }}<input v-model="taskContent" required autofocus /></label>
            <label class="task-minutes-field">{{ t('plans.taskMinutes') }}<input v-model.number="taskMinutes" type="number" min="0" step="1" /></label>
            <button type="button" class="plans-secondary" @click="cancelTaskEdit">{{ t('plans.cancel') }}</button>
            <button type="submit" class="plans-primary">{{ editingTaskId ? t('plans.editTask') : t('plans.save') }}</button>
          </form>
          <form v-if="canEditPlan && groupSectionIndex === section.index" class="group-editor" @submit.prevent="saveGroup">
            <label>{{ t('plans.groupTitle') }}<input v-model="groupTitle" required autofocus /></label>
            <label>{{ t('plans.groupDescription') }}<input v-model="groupDescription" /></label>
            <label>{{ t('plans.groupStart') }}<select v-model.number="groupStart"><option v-for="task in section.tasks" :key="`start-${task.internal_id}`" :value="task.internal_index">{{ task.display_id }}</option></select></label>
            <label>{{ t('plans.groupEnd') }}<select v-model.number="groupEnd"><option v-for="task in section.tasks" :key="`end-${task.internal_id}`" :value="task.internal_index">{{ task.display_id }}</option></select></label>
            <button type="button" class="plans-secondary" @click="cancelGroupEdit">{{ t('plans.cancel') }}</button>
            <button type="submit" class="plans-primary" :disabled="isLoading || !groupTitle.trim() || groupEnd <= groupStart">{{ editingGroupKey ? t('plans.save') : t('plans.addGroup') }}</button>
          </form>
          <p v-if="section.tasks.length === 0" class="section-empty">{{ t('plans.noTasks') }}</p>
          <article v-for="task in section.tasks" :id="`plan-task-${task.internal_id}`" :key="task.internal_id" class="event-task-row" :class="{ finished: task.finish, 'search-target': searchTargetTaskId === task.internal_id }">
            <button class="task-complete" :disabled="!!task.finish || isLoading || !canEditPlan" :aria-label="t('plans.complete')" @click="completeTask(task.internal_id, task.display_id)"><Check v-if="task.finish" :size="15" /></button>
            <div><strong>{{ task.display_id }}</strong><span>{{ task.content }}</span></div>
            <small>{{ task.time_minutes }} {{ t('plans.minutesShort') }}</small>
            <button v-if="canEditPlan" class="task-log" :disabled="isLoading" :aria-label="t('plans.recordProgress')" @click="startLog(task.internal_id)">{{ t('plans.record') }}</button>
            <button v-if="canEditPlan && !task.finish" class="task-todo" :class="{ linked: isTaskLinkedToTodo(task) }" :disabled="isLoading" :aria-label="isTaskLinkedToTodo(task) ? t('plans.viewTodo') : t('plans.linkTodo')" @click="isTaskLinkedToTodo(task) ? openLinkedTodo(task) : addTaskToTodos(task)">{{ isTaskLinkedToTodo(task) ? t('plans.viewTodo') : t('plans.linkTodo') }}</button>
            <button v-if="isTaskLinkedToTodo(task)" class="task-time" :disabled="isLoading" :aria-label="t('plans.recordTodoTime')" @click="openLinkedTaskRecord(task)"><Clock3 :size="14" /><span>{{ t('plans.recordTodoTime') }}</span></button>
            <button v-if="canEditPlan" class="task-edit" :disabled="isLoading" :aria-label="t('plans.editTask')" @click="startTaskEdit(section.index, task)"><Pencil :size="15" /></button>
            <button v-if="canEditPlan" class="task-delete" :disabled="isLoading" :aria-label="t('plans.delete')" @click="deleteTask(task.internal_id, task.display_id)"><Trash2 :size="15" /></button>
          </article>
          <div v-if="groupEntries(section).length" class="group-list">
            <div v-for="group in groupEntries(section)" :key="group.key" class="group-item" :style="{ '--group-depth': group.depth }">
              <span class="group-range">{{ group.key }}</span>
              <div><strong>{{ group.title }}</strong><small v-if="group.description">{{ group.description }}</small></div>
              <button v-if="canEditPlan" class="group-action" :aria-label="t('plans.editGroup')" @click="startGroupEdit(section, group)"><Pencil :size="13" /></button>
              <button v-if="canEditPlan" class="group-action danger" :aria-label="t('plans.deleteGroup')" @click="deleteGroup(section.index, group.key)"><Trash2 :size="13" /></button>
            </div>
          </div>
        </section>
      </template>
    </main>

    <div v-if="showCreate" class="modal-backdrop" @click.self="closeCreatePlan">
      <form class="create-modal theme-card" role="dialog" aria-modal="true" aria-labelledby="plan-create-title" @submit.prevent="createPlan" @keydown.esc.prevent.stop="closeCreatePlan">
        <h2 id="plan-create-title">{{ t('plans.create') }}</h2>
        <p>{{ t('plans.createHint') }}</p>
        <label>{{ t('plans.name') }}<input ref="createNameInput" v-model="planName" required /></label>
        <label>{{ t('plans.date') }}<input v-model="planDate" type="date" required /></label>
        <label v-if="planTemplates.length" class="create-template-field">{{ t('plans.template') }}
          <select v-model="selectedTemplateId" :disabled="templatesLoading">
            <option value="">{{ t('plans.templateManual') }}</option>
            <option v-for="template in planTemplates" :key="template.id" :value="template.id">{{ template.name }}</option>
          </select>
        </label>
        <div v-if="selectedTemplate" class="create-template-note">
          <strong>{{ selectedTemplate.name }}</strong>
          <span>{{ selectedTemplate.description }}</span>
          <small>{{ t('plans.templateType') }} · {{ selectedTemplate.type }}</small>
        </div>
        <label class="create-todos-option">
          <input v-model="createTodosOnCreate" type="checkbox" />
          <span><strong>{{ t('plans.createTodos') }}</strong><small>{{ t('plans.createTodosHint') }}</small></span>
        </label>
        <div v-if="!selectedTemplateId" class="create-first-action">
          <strong>{{ t('plans.firstActionTitle') }}</strong>
          <span>{{ t('plans.firstActionHint') }}</span>
          <label>{{ t('plans.sectionName') }}<input v-model="createSectionName" required /></label>
          <label>{{ t('plans.sectionInfo') }}<input v-model="createSectionInfo" /></label>
          <label>{{ t('plans.taskContent') }}<input v-model="createTaskContent" required /></label>
          <label>{{ t('plans.taskMinutes') }}<input v-model.number="createTaskMinutes" type="number" min="0" step="1" required /></label>
        </div>
        <p class="create-editor-note">{{ t('plans.createEditorHint') }}</p>
        <div class="modal-actions"><button type="button" class="plans-secondary" @click="closeCreatePlan">{{ t('plans.cancel') }}</button><button class="plans-primary" type="submit" :disabled="isLoading">{{ t('plans.createAndEdit') }}</button></div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.plans-hub { min-height: 100vh; color: var(--color-text-primary); background: var(--color-bg); }
.plans-header { display: flex; align-items: center; gap: 15px; max-width: 1080px; margin: 0 auto; padding: 30px 28px 20px; }
.plans-back { display: grid; place-items: center; width: 36px; height: 36px; border: 1px solid var(--color-border); border-radius: 12px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; }
.plans-eyebrow { margin: 0 0 4px; color: var(--color-text-tertiary); font-size: 12px; letter-spacing: .08em; }
.plans-header h1 { margin: 0; font-size: 25px; }
.plans-primary, .plans-secondary, .plans-link { display: inline-flex; align-items: center; justify-content: center; gap: 6px; border-radius: 9px; padding: 8px 12px; cursor: pointer; font-weight: 600; }
.plans-primary { margin-left: auto; border: 1px solid var(--color-primary); color: var(--color-button-text); background: var(--color-primary); }
.plans-secondary { border: 1px solid var(--color-border); color: var(--color-text-secondary); background: var(--color-bg-secondary); }
.plans-link { border: 0; padding-left: 0; color: var(--color-primary); background: transparent; }
.icon-button { display: grid; place-items: center; border: 1px solid var(--color-border); border-radius: 8px; padding: 7px; color: var(--color-text-tertiary); background: var(--color-bg-secondary); cursor: pointer; }
.icon-button:hover { color: var(--color-error); border-color: var(--color-error); }
.plans-content { max-width: 1080px; margin: 0 auto; padding: 10px 28px 50px; }
.unified-plan-section { margin-bottom: 28px; }
.unified-section-heading { display: flex; align-items: end; justify-content: space-between; gap: 16px; margin-bottom: 14px; }
.unified-section-heading h2 { margin: 0; font-size: 21px; letter-spacing: -.02em; }
.unified-section-heading .plans-eyebrow { margin-bottom: 5px; }
.event-plans-section { border-top: 1px solid var(--color-border); padding-top: 26px; }
.event-plans-section .archives-panel { margin-top: 20px; }
.plan-domain-grid, .event-plan-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.domain-card, .event-plan-card { position: relative; display: grid; gap: 9px; border: 1px solid var(--color-border); border-radius: 17px; padding: 24px; color: var(--color-text-primary); background: var(--color-bg-secondary); text-align: left; cursor: pointer; transition: border-color .18s, transform .18s; }
.domain-card:hover, .event-plan-card:hover { border-color: var(--color-border-hover); transform: translateY(-2px); }
.domain-card svg { color: var(--color-primary); }
.domain-card strong, .event-plan-card strong { font-size: 18px; }
.domain-card span, .event-plan-card span, .event-plan-card small { color: var(--color-text-secondary); }
.domain-card > svg:last-child { position: absolute; right: 20px; bottom: 20px; color: var(--color-text-tertiary); }
.event-plan-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.event-plan-card-top { display: flex; justify-content: space-between; color: var(--color-text-tertiary); font-size: 12px; }
.event-plan-card-top svg { color: var(--color-text-tertiary); }
.plan-progress-meta { display: flex; justify-content: space-between; gap: 8px; color: var(--color-text-secondary); }
.plan-progress-track { height: 6px; overflow: hidden; border-radius: 999px; background: var(--color-bg-elevated); }
.plan-progress-track span { display: block; height: 100%; border-radius: inherit; background: var(--color-primary); transition: width .25s ease; }
.plans-empty { display: grid; place-items: center; gap: 10px; min-height: 230px; border: 1px dashed var(--color-border); border-radius: 17px; color: var(--color-text-tertiary); text-align: center; }
.plans-empty strong { color: var(--color-text-secondary); }
.plans-error, .plans-success { margin-bottom: 14px; font-size: 13px; }
.plans-error { color: var(--color-error); }
.plans-success { color: var(--color-success, #16a34a); }
.plans-readonly-note { display: grid; gap: 4px; margin-bottom: 14px; padding: 12px 14px; border: 1px solid var(--color-primary); border-radius: 12px; color: var(--color-text-secondary); background: var(--color-bg-secondary); font-size: 13px; line-height: 1.5; }
.plans-readonly-note strong { color: var(--color-text-primary); }
.plans-retry { justify-self: start; }
.detail-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.detail-actions { display: flex; gap: 8px; }
.meta-editor, .section-editor { display: flex; align-items: flex-end; gap: 10px; margin-bottom: 14px; padding: 14px; border: 1px solid var(--color-border); border-radius: 14px; }
.meta-editor label, .section-editor label, .task-editor label, .create-modal label { display: grid; gap: 6px; color: var(--color-text-secondary); font-size: 12px; }
.meta-editor input, .section-editor input, .task-editor input, .create-modal input { min-width: 0; border: 1px solid var(--color-border); border-radius: 8px; padding: 8px 10px; color: var(--color-text-primary); background: var(--color-bg-secondary); outline: none; }
.meta-editor input:focus, .section-editor input:focus, .task-editor input:focus, .create-modal input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-muted); }
.create-modal { width: min(440px, calc(100vw - 32px)); }
.create-first-action { display: grid; gap: 8px; margin-top: 4px; border: 1px solid var(--color-border); border-radius: 12px; padding: 12px; background: var(--color-bg-secondary); }
.create-first-action > strong { color: var(--color-text-primary); font-size: 13px; }
.create-first-action > span { color: var(--color-text-tertiary); font-size: 11px; line-height: 1.45; }
.create-first-action label { font-size: 11px; }
.create-template-field select { border: 1px solid var(--color-border); border-radius: 8px; padding: 8px 10px; color: var(--color-text-primary); background: var(--color-bg-secondary); }
.create-template-note { display: grid; gap: 3px; margin: 0; border-left: 3px solid var(--color-primary); padding: 8px 10px; color: var(--color-text-secondary); background: var(--color-primary-muted); font-size: 12px; line-height: 1.45; }
.create-template-note strong { color: var(--color-text-primary); }
.create-template-note small { color: var(--color-text-tertiary); font-size: 11px; }
.create-todos-option { display: flex !important; align-items: flex-start; gap: 8px; border: 1px solid var(--color-border); border-radius: 10px; padding: 9px 10px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; }
.create-todos-option input { margin-top: 2px; accent-color: var(--color-primary); }
.create-todos-option span { display: grid; gap: 2px; }
.create-todos-option strong { color: var(--color-text-primary); font-size: 12px; }
.create-todos-option small { color: var(--color-text-tertiary); font-size: 11px; line-height: 1.4; }
.plan-detail-summary { display: flex; gap: 38px; margin-bottom: 14px; padding: 17px 20px; border: 1px solid var(--color-border); border-radius: 14px; }
.plan-detail-summary div { display: grid; gap: 4px; }
.plan-detail-summary span { color: var(--color-text-tertiary); font-size: 12px; }
.plan-detail-progress { min-width: 130px; }
.log-editor, .log-list { display: grid; gap: 10px; margin-bottom: 14px; padding: 14px; border: 1px solid var(--color-border); border-radius: 14px; }
.log-editor { grid-template-columns: minmax(190px, 1fr) auto minmax(180px, 1.4fr) auto; align-items: end; }
.log-editor-heading { display: grid; gap: 3px; }
.log-editor-heading small, .log-list header small { color: var(--color-text-tertiary); font-size: 11px; }
.log-editor label { display: grid; gap: 5px; color: var(--color-text-secondary); font-size: 11px; }
.log-editor select, .log-editor label input, .log-content-input { min-width: 0; border: 1px solid var(--color-border); border-radius: 8px; padding: 8px 9px; color: var(--color-text-primary); background: var(--color-bg-secondary); outline: none; }
.log-editor label input { width: 66px; }
.log-content-input:focus, .log-editor select:focus, .log-editor label input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-muted); }
.log-list header { display: flex; align-items: center; justify-content: space-between; color: var(--color-text-secondary); }
.log-row { display: grid; grid-template-columns: 58px minmax(0, 1fr); gap: 12px; border-top: 1px solid var(--color-border); padding-top: 10px; text-align: left; }
.log-time { display: grid; align-content: start; gap: 2px; color: var(--color-primary); font-variant-numeric: tabular-nums; }
.log-time span { color: var(--color-text-tertiary); font-size: 11px; }
.log-row p { margin: 4px 0 0; color: var(--color-text-secondary); font-size: 12px; }
.section-editor { align-items: center; }
.section-editor-actions { display: flex; gap: 7px; flex: 0 0 auto; }
.section-editor input:first-child { flex: 1; }
.section-editor input:nth-child(2) { flex: 1.5; }
.plan-section { margin-bottom: 12px; padding: 17px; border: 1px solid var(--color-border); border-radius: 14px; }
.plan-section > header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.plan-section > header > div { display: flex; align-items: center; gap: 9px; min-width: 0; }
.section-actions { display: flex; gap: 7px; }
.section-letter { display: grid; place-items: center; width: 26px; height: 26px; border-radius: 8px; color: var(--color-button-text); background: var(--color-primary); font-size: 12px; font-weight: 700; }
.plan-section header small { overflow: hidden; color: var(--color-text-tertiary); text-overflow: ellipsis; white-space: nowrap; }
.task-editor { display: flex; align-items: flex-end; gap: 9px; margin: 15px 0 8px; padding: 10px; border-radius: 10px; background: var(--color-bg-secondary); }
.task-editor label:first-child { flex: 1; }
.task-minutes-field { flex: 0 0 110px; }
.task-minutes-field input { width: 100%; box-sizing: border-box; }
.group-editor { display: grid; grid-template-columns: minmax(120px, .8fr) minmax(160px, 1.4fr) 110px 110px auto auto; align-items: end; gap: 8px; margin: 10px 0; padding: 10px; border: 1px dashed var(--color-border); border-radius: 10px; background: var(--color-bg-secondary); }
.group-editor label { display: grid; gap: 5px; color: var(--color-text-tertiary); font-size: 11px; }
.group-editor input, .group-editor select { min-width: 0; border: 1px solid var(--color-border); border-radius: 7px; padding: 7px 8px; color: var(--color-text-primary); background: var(--color-bg); outline: none; }
.section-empty { color: var(--color-text-tertiary); font-size: 13px; }
.event-task-row { display: grid; grid-template-columns: 24px minmax(0, 1fr) auto 64px auto 64px 28px 28px; align-items: center; gap: 8px; padding: 12px 0; border-top: 1px solid var(--color-border); }
.event-task-row > div { display: flex; align-items: baseline; gap: 10px; min-width: 0; }
.event-task-row > div strong { color: var(--color-primary); font-size: 12px; }
.event-task-row > div span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.event-task-row > small { color: var(--color-text-tertiary); white-space: nowrap; }
.task-log { border: 0; border-radius: 7px; padding: 5px 7px; color: var(--color-primary); background: var(--color-primary-muted); cursor: pointer; font-size: 11px; white-space: nowrap; }
.task-todo { border: 0; border-radius: 7px; padding: 5px 7px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; font-size: 11px; white-space: nowrap; }
.task-todo:hover { color: var(--color-primary); }
.task-todo.linked { color: var(--color-success, #16a34a); background: color-mix(in srgb, var(--color-success, #16a34a) 12%, var(--color-bg-secondary)); cursor: default; }
.task-time { display: inline-flex; align-items: center; gap: 4px; border: 0; border-radius: 7px; padding: 5px 7px; color: var(--color-primary); background: var(--color-primary-muted); cursor: pointer; font-size: 11px; white-space: nowrap; }
.task-time:hover { filter: brightness(1.05); }
.event-task-row.finished { opacity: .62; }
.event-task-row.search-target { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-muted); }
.event-task-row.finished span { text-decoration: line-through; }
.task-complete, .task-edit, .task-delete { display: grid; place-items: center; border: 0; color: var(--color-text-tertiary); background: transparent; cursor: pointer; }
.task-complete { width: 22px; height: 22px; border: 2px solid var(--color-border-hover); border-radius: 50%; }
.task-complete:disabled { color: var(--color-button-text); background: var(--color-primary); }
.group-list { display: grid; gap: 5px; margin-top: 10px; }
.group-item { display: flex; align-items: flex-start; gap: 7px; margin-left: calc(var(--group-depth) * 16px); border-left: 2px solid var(--color-primary-muted); padding: 5px 7px; border-radius: 5px; background: var(--color-bg-secondary); font-size: 11px; }
.group-item > div { display: grid; gap: 2px; min-width: 0; text-align: left; }
.group-range { flex: 0 0 auto; color: var(--color-primary); font-family: var(--font-mono, monospace); }
.group-item small { overflow: hidden; color: var(--color-text-tertiary); text-overflow: ellipsis; white-space: nowrap; }
.group-action { display: grid; place-items: center; margin-left: auto; border: 0; color: var(--color-text-tertiary); background: transparent; cursor: pointer; }
.group-action + .group-action { margin-left: 0; }
.group-action:hover { color: var(--color-primary); }
.group-action.danger:hover { color: var(--color-error); }
.archives-panel { margin-top: 24px; padding: 17px; border: 1px solid var(--color-border); border-radius: 14px; }
.archives-panel header h2, .archives-panel header p { margin: 0; }
.archives-panel header p { margin-top: 4px; color: var(--color-text-tertiary); font-size: 12px; }
.archive-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 0; border-top: 1px solid var(--color-border); }
.archive-row > div { display: grid; gap: 4px; min-width: 0; }
.archive-row span { color: var(--color-text-tertiary); font-size: 12px; }
.modal-backdrop { position: fixed; inset: 0; z-index: 20; display: grid; place-items: center; padding: 20px; background: rgba(0,0,0,.3); }
.create-modal { display: grid; gap: 14px; width: min(440px, 100%); padding: 24px; border: 1px solid var(--color-border); border-radius: 18px; background: var(--color-bg); box-shadow: var(--shadow-lg, 0 18px 50px rgba(0,0,0,.2)); }
.create-modal h2, .create-modal p { margin: 0; }
.create-modal p { color: var(--color-text-secondary); font-size: 13px; }
.create-editor-note { border: 1px solid var(--color-primary-muted); border-radius: 10px; padding: 10px 12px; color: var(--color-text-secondary); background: var(--color-primary-muted); line-height: 1.5; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; }
@media (prefers-reduced-motion: reduce) { .domain-card, .event-plan-card { transition: none; } }
@media (max-width: 760px) { .plans-header, .plans-content { padding-left: 18px; padding-right: 18px; } .plan-domain-grid, .event-plan-grid { grid-template-columns: 1fr; } .unified-section-heading { align-items: flex-start; flex-direction: column; } .meta-editor, .section-editor, .task-editor, .log-editor, .group-editor { align-items: stretch; flex-direction: column; } .meta-editor > div { display: flex; justify-content: flex-end; } .plan-detail-summary { gap: 18px; justify-content: space-between; } .log-editor, .group-editor { display: flex; } .section-actions { flex-wrap: wrap; justify-content: flex-end; } .event-task-row { grid-template-columns: 24px minmax(0, 1fr) auto; } .event-task-row .task-log, .event-task-row .task-todo, .event-task-row .task-time { grid-column: 2; justify-self: start; } .event-task-row .task-edit, .event-task-row .task-delete { grid-row: 1; } }
</style>
