<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Check, ChevronRight, FolderPlus, Pencil, Plus, Trash2 } from 'lucide-vue-next'
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
  listPlanTemplates,
  listPlanSummaries,
  restorePlanArchive,
  type PlanArchiveSummary,
  type PlanFull,
  type InitialPlanSection,
  type PlanSummary,
  type PlanTaskSummary,
  type PlanTemplateSummary,
  updatePlanTask,
  updatePlanGroup,
  updateEventPlan,
  planDataSource,
  planArchivesState,
} from '@/services/planGateway'
import { getPlanRuntime } from '@/services/runtimeCapabilities'
import { notifyToast } from '@/services/toastService'
import { requestConfirm } from '@/services/confirmService'
import { onWorkspaceChanged } from '@/services/workspaceEvents'

const router = useRouter()
const route = useRoute()
const { t, locale } = useI18n()
const isMobilePlanRuntime = getPlanRuntime() === 'mobile-unavailable'
const canEditPlan = computed(() => isMobilePlanRuntime || planDataSource.value !== 'cache')
const canArchivePlan = computed(() => canEditPlan.value)
const archivesUnavailable = computed(() => !isMobilePlanRuntime && planArchivesState.value === 'unavailable')
const view = ref<'events' | 'detail'>('events')
const plans = ref<PlanSummary[]>([])
const archives = ref<PlanArchiveSummary[]>([])
const selectedPlan = ref<PlanFull | null>(null)
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const planSearch = ref('')
const searchTargetTaskId = ref<string | null>(null)
const showCreate = ref(false)
const showTemplatePicker = ref(false)
const createNameInput = ref<HTMLInputElement | null>(null)
const createReturnFocus = ref<HTMLElement | null>(null)
const planName = ref('')
const planDate = ref(toDateInput(new Date()))
const createSections = ref<InitialPlanSection[]>([])
const templateDraftName = ref('')
const templateDraftDate = ref(toDateInput(new Date()))
const templateDraftId = ref('')
const templateOptions = ref<PlanTemplateSummary[]>([])
const templateLoading = ref(false)
const editingMeta = ref(false)
const sectionName = ref('')
const sectionInfo = ref('')
const editingSectionIndex = ref<number | null>(null)
const taskSectionIndex = ref<number | null>(null)
const editingTaskId = ref<string | null>(null)
const editingTaskSectionIndex = ref<number | null>(null)
const taskContent = ref('')
const taskMinutes = ref(0)
const groupSectionIndex = ref<number | null>(null)
const editingGroupKey = ref<string | null>(null)
const groupTitle = ref('')
const groupDescription = ref('')
const groupStart = ref(0)
const groupEnd = ref(1)
const logTaskId = ref('base')
const logDay = ref(new Date().getDate())
const logContent = ref('')

const archivedPlanTarget = computed(() => {
  const targetFile = String(route.query.archive || '')
  if (targetFile && !selectedPlan.value) {
    return archives.value.find((archive) => archive.file === targetFile) || null
  }
  const targetId = String(route.query.plan || '')
  if (!targetId || selectedPlan.value) return null
  return archives.value.find((archive) => String(archive.plan_id ?? '') === targetId) || null
})
const archivedTaskTargetId = computed(() => String(route.query.task || ''))

const filteredPlans = computed(() => {
  const query = planSearch.value.trim().toLocaleLowerCase()
  if (!query) return plans.value
  return plans.value.filter((plan) => `${plan.name} ${plan.id} ${plan.date?.join('-') || ''}`.toLocaleLowerCase().includes(query))
})

const filteredArchives = computed(() => {
  const query = planSearch.value.trim().toLocaleLowerCase()
  if (!query) return archives.value
  return archives.value.filter((archive) => `${archive.name || ''} ${archive.file} ${archive.plan_id ?? ''} ${archive.date?.join('-') || ''}`.toLocaleLowerCase().includes(query))
})

function isArchivedTaskTarget(task: PlanTaskSummary): boolean {
  return Boolean(archivedTaskTargetId.value && (
    task.internal_id === archivedTaskTargetId.value || task.display_id === archivedTaskTargetId.value
  ))
}

function showPlanSaved(): void {
  successMessage.value = t('plans.saved')
  notifyToast(t('plans.saved'), 'success')
}

let stopWorkspaceListener: (() => void) | null = null

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

function sectionDisplayLetter(index: number): string {
  let value = Math.max(0, Math.trunc(index))
  let result = ''
  do {
    result = String.fromCharCode(65 + (value % 26)) + result
    value = Math.floor(value / 26) - 1
  } while (value >= 0)
  return result
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

function templateDisplayName(template: PlanTemplateSummary): string {
  if (!template.built_in) return template.name
  if (template.type === 'workday') return t('plans.templateTypes.workdayName')
  if (template.type === 'weekend') return t('plans.templateTypes.weekendName')
  if (template.type === 'exam') return t('plans.templateTypes.examName')
  return template.name
}

function templateDisplayDescription(template: PlanTemplateSummary): string {
  if (!template.built_in) return template.description
  if (template.type === 'workday') return t('plans.templateTypes.workdayDescription')
  if (template.type === 'weekend') return t('plans.templateTypes.weekendDescription')
  if (template.type === 'exam') return t('plans.templateTypes.examDescription')
  return template.description
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
  if (!source || !['plans', 'archive', 'network'].includes(source)) return
  if (selectedPlan.value && (source === 'plans' || source === 'archive' || source === 'network')) {
    try {
      selectedPlan.value = await getPlanFull(selectedPlan.value.id)
    } catch {
      // The plan may have been archived or removed in another window. Do not
      // leave the user on a detail screen whose source no longer exists.
      selectedPlan.value = null
      view.value = 'events'
      await router.replace({ path: '/plans', query: {} })
      await loadPlans()
    }
    return
  }
  if (view.value === 'events') await loadPlans()
}

// Keep external changes observed while a local plan mutation is in flight.
// Dropping the event would leave this window stale until a later navigation.
const pendingWorkspaceSources = new Set<string>()
let workspaceRefreshRunning = false

async function drainWorkspaceRefresh(): Promise<void> {
  if (workspaceRefreshRunning || isLoading.value) return
  workspaceRefreshRunning = true
  try {
    while (pendingWorkspaceSources.size > 0) {
      const sources = [...pendingWorkspaceSources]
      pendingWorkspaceSources.clear()
      for (const source of sources) {
        try {
          await refreshFromWorkspace(source)
        } catch (error) {
          console.warn('Failed to refresh plans after external change:', error)
        }
      }
      if (isLoading.value) return
    }
  } finally {
    workspaceRefreshRunning = false
    if (pendingWorkspaceSources.size > 0 && !isLoading.value) void drainWorkspaceRefresh()
  }
}

function queueWorkspaceRefresh(source?: string): void {
  if (!source || !['plans', 'archive', 'network'].includes(source)) return
  pendingWorkspaceSources.add(source)
  void drainWorkspaceRefresh()
}

stopWorkspaceListener = onWorkspaceChanged(queueWorkspaceRefresh)
watch(isLoading, (loading) => {
  if (!loading) void drainWorkspaceRefresh()
})

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
    const restoredId = await restorePlanArchive(archive.file)
    await loadPlans()
    if (restoredId) await router.replace({ path: '/plans', query: { plan: restoredId } })
    await revealSearchTarget()
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
  createSections.value = [{ name: '', info: '', tasks: [{ content: '', time_minutes: 0 }] }]
  errorMessage.value = ''
  showCreate.value = true
  void nextTick(() => createNameInput.value?.focus())
}

function closeCreatePlan() {
  showCreate.value = false
  createSections.value = []
  const returnTarget = createReturnFocus.value
  createReturnFocus.value = null
  void nextTick(() => {
    if (returnTarget?.isConnected) returnTarget.focus()
  })
}

function addCreateSection(): void {
  createSections.value.push({ name: '', info: '', tasks: [{ content: '', time_minutes: 0 }] })
}

function removeCreateSection(index: number): void {
  createSections.value.splice(index, 1)
}

function addCreateTask(section: InitialPlanSection): void {
  section.tasks.push({ content: '', time_minutes: 0 })
}

function removeCreateTask(section: InitialPlanSection, index: number): void {
  section.tasks.splice(index, 1)
}

function closeTemplatePicker() {
  showTemplatePicker.value = false
  templateDraftId.value = ''
  templateOptions.value = []
}

function openTemplatePicker() {
  templateDraftName.value = ''
  templateDraftDate.value = toDateInput(new Date())
  templateDraftId.value = ''
  templateOptions.value = []
  templateLoading.value = true
  showTemplatePicker.value = true
  void listPlanTemplates()
    .then((templates) => {
      templateOptions.value = templates
      if (templates.length === 1) templateDraftId.value = templates[0].id
    })
    .catch(() => { templateOptions.value = [] })
    .finally(() => { templateLoading.value = false })
}

async function createFromTemplate() {
  if (isLoading.value || templateLoading.value) return
  const name = templateDraftName.value.trim()
  if (!name || !templateDraftDate.value || !templateDraftId.value) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    selectedPlan.value = await createEventPlanFromTemplate(
      templateDraftId.value,
      name,
      toDateTuple(templateDraftDate.value),
      locale.value,
    )
    const createdId = selectedPlan.value.id
    closeTemplatePicker()
    view.value = 'detail'
    await router.replace({ path: '/plans', query: { plan: String(createdId) } })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
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
  const sections = createSections.value
    .map((section) => ({
      ...section,
      name: section.name.trim(),
      info: section.info.trim(),
      tasks: section.tasks
        .map((task) => ({ content: task.content.trim(), time_minutes: Math.max(0, Number(task.time_minutes) || 0) }))
        .filter((task) => task.content),
    }))
    .filter((section) => section.name && section.tasks.length > 0)
  if (!name || !planDate.value || sections.length === 0) {
    errorMessage.value = t('plans.createTaskRequired')
    return
  }
  isLoading.value = true
  errorMessage.value = ''
  try {
    const created = await createEventPlan(name, toDateTuple(planDate.value), sections)
    const createdId = created.id
    selectedPlan.value = await getPlanFull(createdId)
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
    await updateEventPlan(planId, planName.value.trim(), toDateTuple(planDate.value))
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
    } else if (taskSectionIndex.value !== null) {
      await addPlanTask(planId, taskSectionIndex.value, taskContent.value.trim(), minutes)
    }
    taskContent.value = ''
    taskMinutes.value = 0
    taskSectionIndex.value = null
    editingTaskId.value = null
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

function groupDisplayRange(section: PlanFull['sections'][number], group: ReturnType<typeof groupEntries>[number]): string {
  const visibleTasks = section.tasks.filter((task) => task.is_active !== false)
  const first = visibleTasks.find((task) => task.internal_index >= group.start && task.internal_index <= group.end)
  const last = [...visibleTasks].reverse().find((task) => task.internal_index >= group.start && task.internal_index <= group.end)
  if (!first || !last) return t('plans.groupNoActiveTasks')
  return first.display_id === last.display_id ? first.display_id : `${first.display_id}–${last.display_id}`
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
  editingTaskSectionIndex.value = sectionIndex
  taskContent.value = task.content
  taskMinutes.value = task.time_minutes
}

function cancelTaskEdit() {
  taskSectionIndex.value = null
  editingTaskId.value = null
  editingTaskSectionIndex.value = null
  taskContent.value = ''
  taskMinutes.value = 0
}

async function completeTask(taskId: string) {
  if (isLoading.value) return
  if (!selectedPlan.value) return
  const planId = selectedPlan.value.id
  isLoading.value = true
  errorMessage.value = ''
  try {
    await completePlanTask(planId, taskId)
    selectedPlan.value = await getPlanFull(planId)
    showPlanSaved()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('plans.unavailable')
  } finally {
    isLoading.value = false
  }
}

async function deleteTask(taskId: string) {
  if (isLoading.value) return
  if (!selectedPlan.value || !(await requestConfirm(`${t('plans.delete')}?`, { tone: 'danger' }))) return
  const planId = selectedPlan.value.id
  isLoading.value = true
  errorMessage.value = ''
  try {
    await deletePlanTask(planId, taskId)
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

function planProgress(plan: PlanSummary): number {
  const total = Number(plan.total_tasks || 0)
  return total > 0 ? Math.round((Number(plan.completed_tasks || 0) / total) * 100) : 0
}

async function revealSearchTarget(): Promise<void> {
  if (route.query.archive) {
    // An archive search result can be opened while the user is already in an
    // active-plan detail view. Clear that transient selection so the archive
    // preview is not hidden behind stale active-plan state.
    if (selectedPlan.value || view.value === 'detail') {
      selectedPlan.value = null
      editingMeta.value = false
      view.value = 'events'
      searchTargetTaskId.value = null
    }
    return
  }
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

watch(() => [route.query.plan, route.query.task, route.query.archive], () => {
  if (plans.value.length > 0) void revealSearchTarget()
})

onUnmounted(() => {
  stopWorkspaceListener()
})
</script>

<template>
  <div class="plans-hub">
    <header class="plans-header">
      <button type="button" class="plans-back" @click="AudioManager.playSound('click'); router.push('/')" :aria-label="t('plans.back')">
        <ArrowLeft :size="18" />
      </button>
      <div class="plans-title-block">
        <p class="plans-eyebrow">{{ t('plans.moduleLabel') }}</p>
        <h1>{{ view === 'detail' ? selectedPlan?.name : t('plans.center') }}</h1>
        <p v-if="view !== 'detail'" class="plans-module-description">{{ t('plans.moduleDescription') }}</p>
      </div>
      <div v-if="view === 'events' && canEditPlan" class="plan-entry-actions"><button type="button" class="plans-secondary" @click="openTemplatePicker">{{ t('plans.fromTemplate') }}</button><button type="button" class="plans-primary" @click="openCreatePlan"><Plus :size="16" /> {{ t('plans.create') }}</button></div>
    </header>

    <main class="plans-content">

      <section v-if="showTemplatePicker && view === 'events'" class="template-workspace theme-card">
        <header class="template-workspace-header">
          <div><p class="plans-eyebrow">{{ t('plans.template') }}</p><h2>{{ t('plans.templateWorkspaceTitle') }}</h2><p>{{ t('plans.templateWorkspaceHint') }}</p></div>
          <button type="button" class="plans-secondary" @click="closeTemplatePicker">{{ t('plans.cancel') }}</button>
        </header>
        <div v-if="templateLoading" class="plans-empty template-workspace-empty">{{ t('plans.templateLoading') }}</div>
        <div v-else-if="templateOptions.length === 0" class="plans-empty template-workspace-empty">{{ t('plans.templateEmpty') }}</div>
        <form v-else class="template-workspace-form" @submit.prevent="createFromTemplate">
          <label>{{ t('plans.templateChoose') }}<select v-model="templateDraftId" required><option value="" disabled>{{ t('plans.templateChoose') }}</option><option v-for="template in templateOptions" :key="template.id" :value="template.id">{{ templateDisplayName(template) }} · {{ templateDisplayDescription(template) }}</option></select></label>
          <label>{{ t('plans.name') }}<input v-model="templateDraftName" required /></label>
          <label>{{ t('plans.date') }}<input v-model="templateDraftDate" type="date" required /></label>
          <div class="template-workspace-actions"><button type="button" class="plans-secondary" @click="closeTemplatePicker">{{ t('plans.cancel') }}</button><button type="submit" class="plans-primary" :disabled="isLoading || !templateDraftId">{{ isLoading ? t('plans.loading') : t('plans.templateCreate') }}</button></div>
        </form>
      </section>

      <template v-if="view === 'events'">
        <p v-if="errorMessage" class="plans-error">{{ errorMessage }}</p>
        <div v-if="archivedPlanTarget" class="plans-readonly-note archive-target-note">
          <strong>{{ t('plans.archivedTargetTitle') }}</strong>
          <span>{{ t('plans.archivedTargetDescription') }}</span>
          <div v-if="archivedPlanTarget.tasks?.length" class="archive-task-preview">
            <div v-for="task in archivedPlanTarget.tasks" :key="task.internal_id" class="archive-task-preview-row" :class="{ 'search-target': isArchivedTaskTarget(task) }">
              <span>{{ task.display_id }}</span><strong>{{ task.content }}</strong><small>{{ task.time_minutes }} {{ t('plans.minutesShort') }}</small>
            </div>
          </div>
          <button v-if="canArchivePlan" type="button" class="plans-secondary plans-retry" :disabled="isLoading" @click="restoreArchive(archivedPlanTarget)">{{ t('plans.restore') }}</button>
        </div>
        <div v-if="!isMobilePlanRuntime && planDataSource === 'cache'" class="plans-readonly-note plans-list-source-note">
          <div><strong>{{ t('plans.cachedTitle') }}</strong><span>{{ t('plans.cachedDescription') }}</span></div>
          <button type="button" class="plans-secondary plans-retry" :disabled="isLoading" @click="retryPlanService">{{ isLoading ? t('plans.loading') : t('plans.retryService') }}</button>
        </div>
        <label v-if="plans.length > 1 || archives.length > 1" class="plans-search">
          <span>{{ t('plans.searchLabel') }}</span>
          <input v-model="planSearch" type="search" :placeholder="t('plans.searchPlaceholder')" />
        </label>
        <section v-if="isLoading" class="plans-empty theme-card">{{ t('plans.loading') }}</section>
        <section v-else-if="plans.length === 0" class="plans-empty theme-card">
          <FolderPlus :size="34" />
          <strong>{{ t('plans.empty') }}</strong>
          <span>{{ t('plans.emptyHint') }}</span>
          <button v-if="canEditPlan" type="button" class="plans-primary" @click="openCreatePlan"><Plus :size="16" /> {{ t('plans.create') }}</button>
        </section>
        <section v-else-if="filteredPlans.length" class="event-plan-grid">
          <button v-for="plan in filteredPlans" :key="plan.id" type="button" class="event-plan-card theme-card" @click="openPlan(plan)">
            <div class="event-plan-card-top"><span>#{{ plan.id }}</span><ChevronRight :size="17" /></div>
            <strong>{{ plan.name }}</strong>
            <span>{{ formatPlanDate(plan.date) }}</span>
            <div class="plan-progress-meta"><small>{{ plan.completed_tasks || 0 }}/{{ plan.total_tasks || 0 }} {{ t('plans.tasks') }}</small><small>{{ planProgress(plan) }}%</small></div>
            <div class="plan-progress-track"><span :style="{ width: `${planProgress(plan)}%` }" /></div>
          </button>
        </section>
        <section v-else class="plans-empty theme-card"><strong>{{ t('plans.searchEmpty') }}</strong><span>{{ t('plans.searchEmptyHint') }}</span></section>
        <section class="archives-panel theme-card">
          <header><div><h2>{{ t('plans.archived') }}</h2><p>{{ t('plans.archivedAt') }}</p></div></header>
          <p v-if="isMobilePlanRuntime" class="plans-readonly-note archive-capability-note">{{ t('plans.mobileLocalDescription') }}</p>
          <div v-else-if="archivesUnavailable" class="section-empty archive-unavailable" role="status" aria-live="polite">
            <span>{{ t('plans.archivesUnavailable') }}</span>
            <button type="button" class="plans-secondary plans-retry" :disabled="isLoading" @click="retryPlanService">{{ t('plans.retryArchives') }}</button>
          </div>
          <p v-else-if="archives.length === 0" class="section-empty">{{ t('plans.noArchives') }}</p>
          <p v-else-if="filteredArchives.length === 0" class="section-empty">{{ t('plans.searchEmpty') }}</p>
          <div v-for="archive in filteredArchives" :key="archive.file" class="archive-row">
            <div><strong>{{ archive.name || archive.file }}</strong><span>{{ formatPlanDate(archive.date) }}</span></div>
            <button v-if="canArchivePlan" type="button" class="plans-secondary" :disabled="isLoading" @click="restoreArchive(archive)">{{ t('plans.restore') }}</button>
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
          <button type="button" class="plans-secondary plans-retry" :disabled="isLoading" @click="retryPlanService">{{ isLoading ? t('plans.loading') : t('plans.retryService') }}</button>
        </div>
        <div class="detail-toolbar">
          <button type="button" class="plans-link" @click="backFromDetail">← {{ t('plans.back') }}</button>
          <div v-if="canEditPlan" class="detail-actions">
            <button type="button" class="plans-secondary" @click="startMetaEdit"><Pencil :size="15" /> {{ t('plans.edit') }}</button>
            <button v-if="canArchivePlan" type="button" class="plans-secondary" :disabled="isLoading" @click="archiveSelectedPlan">{{ t('plans.archive') }}</button>
          </div>
        </div>
        <form v-if="editingMeta && canEditPlan" class="meta-editor theme-card" @submit.prevent="savePlanMeta">
          <label>{{ t('plans.name') }}<input v-model="planName" required /></label>
          <label>{{ t('plans.date') }}<input v-model="planDate" type="date" required /></label>
          <div><button type="button" class="plans-secondary" @click="editingMeta = false">{{ t('plans.cancel') }}</button><button type="submit" class="plans-primary">{{ t('plans.save') }}</button></div>
        </form>
        <div class="plan-detail-layout">
          <aside class="plan-detail-aside">
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
          </aside>
          <div class="plan-detail-main">
        <form v-if="canEditPlan" class="section-editor theme-card" @submit.prevent="saveSection">
          <label for="plan-section-name">{{ t('plans.sectionName') }}</label>
          <input id="plan-section-name" v-model="sectionName" :placeholder="t('plans.sectionName')" required />
          <label for="plan-section-info">{{ t('plans.sectionInfo') }}</label>
          <input id="plan-section-info" v-model="sectionInfo" :placeholder="t('plans.sectionInfo')" />
          <div class="section-editor-actions"><button v-if="editingSectionIndex !== null" type="button" class="plans-secondary" :disabled="isLoading" @click="cancelSectionEdit">{{ t('plans.cancel') }}</button><button type="submit" class="plans-secondary" :disabled="isLoading"><Pencil v-if="editingSectionIndex !== null" :size="15" /><Plus v-else :size="15" /> {{ editingSectionIndex !== null ? t('plans.saveSection') : t('plans.addSection') }}</button></div>
        </form>
        <section v-if="selectedPlan.sections.length === 0" class="plans-empty theme-card">{{ t('plans.noSections') }}</section>
        <section v-for="section in selectedPlan.sections" :key="section.index" class="plan-section theme-card">
          <header><div><span class="section-letter">{{ section.letter }}</span><strong>{{ section.name }}</strong><small>{{ section.info }}</small></div><div v-if="canEditPlan" class="section-actions"><button type="button" class="plans-secondary" :disabled="isLoading" @click="startSectionEdit(section)"><Pencil :size="15" /> {{ t('plans.editSection') }}</button><button type="button" class="plans-secondary" :disabled="isLoading" @click="deleteSection(section)"><Trash2 :size="15" /> {{ t('plans.deleteSection') }}</button><button type="button" class="plans-secondary" :disabled="isLoading" @click="taskSectionIndex = section.index"><Plus :size="15" /> {{ t('plans.addTask') }}</button><button type="button" class="plans-secondary" :disabled="isLoading || !section.tasks.length" @click="startNewGroup(section)"><Plus :size="15" /> {{ t('plans.addGroup') }}</button></div></header>
          <form v-if="canEditPlan && (taskSectionIndex === section.index || editingTaskSectionIndex === section.index)" class="task-editor" @submit.prevent="saveTask">
            <label>{{ t('plans.taskContent') }}<input v-model="taskContent" required autofocus /></label>
            <label class="task-minutes-field"><span>{{ t('plans.taskMinutes') }}</span><small>{{ t('plans.taskMinutesHint') }}</small><input v-model.number="taskMinutes" type="number" min="0" step="1" /></label>
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
            <button type="button" class="task-complete" :disabled="!!task.finish || isLoading || !canEditPlan" :aria-label="t('plans.completeTaskLabel', { id: task.display_id, content: task.content })" @click="completeTask(task.internal_id)"><Check v-if="task.finish" :size="15" /></button>
            <div><strong>{{ task.display_id }}</strong><span>{{ task.content }}</span></div>
            <small>{{ task.time_minutes }} {{ t('plans.minutesShort') }}</small>
            <button v-if="canEditPlan" type="button" class="task-log" :disabled="isLoading" :aria-label="t('plans.recordTaskLabel', { id: task.display_id, content: task.content })" @click="startLog(task.internal_id)">{{ t('plans.record') }}</button>
            <button v-if="canEditPlan" type="button" class="task-edit" :disabled="isLoading" :aria-label="t('plans.editTaskLabel', { id: task.display_id, content: task.content })" @click="startTaskEdit(section.index, task)"><Pencil :size="15" /></button>
            <button v-if="canEditPlan" type="button" class="task-delete" :disabled="isLoading" :aria-label="t('plans.deleteTaskLabel', { id: task.display_id, content: task.content })" @click="deleteTask(task.internal_id)"><Trash2 :size="15" /></button>
          </article>
          <div v-if="groupEntries(section).length" class="group-list">
            <div v-for="group in groupEntries(section)" :key="group.key" class="group-item" :style="{ '--group-depth': group.depth }">
              <span class="group-range">{{ groupDisplayRange(section, group) }}</span>
              <div><strong>{{ group.title }}</strong><small v-if="group.description">{{ group.description }}</small></div>
              <button v-if="canEditPlan" type="button" class="group-action" :aria-label="t('plans.editGroup')" @click="startGroupEdit(section, group)"><Pencil :size="13" /></button>
              <button v-if="canEditPlan" type="button" class="group-action danger" :aria-label="t('plans.deleteGroup')" @click="deleteGroup(section.index, group.key)"><Trash2 :size="13" /></button>
            </div>
          </div>
        </section>
          </div>
        </div>
      </template>
    </main>

    <div v-if="showCreate" class="modal-backdrop" @click.self="closeCreatePlan">
      <form class="create-modal theme-card" role="dialog" aria-modal="true" aria-labelledby="plan-create-title" @submit.prevent="createPlan" @keydown.esc.prevent.stop="closeCreatePlan">
        <h2 id="plan-create-title">{{ t('plans.create') }}</h2>
        <p>{{ t('plans.createHint') }}</p>
        <label>{{ t('plans.name') }}<input ref="createNameInput" v-model="planName" required /></label>
        <label>{{ t('plans.date') }}<input v-model="planDate" type="date" required /></label>
        <div class="create-editor-note">
          <strong>{{ t('plans.createSections') }}</strong>
          <span>{{ t('plans.createSectionsHint') }}</span>
        </div>
        <div class="create-sections">
          <div v-for="(section, sectionIndex) in createSections" :key="sectionIndex" class="create-section">
            <div class="create-section-header">
              <strong>{{ t('plans.section') }} {{ sectionDisplayLetter(sectionIndex) }}</strong>
              <button v-if="createSections.length > 1" type="button" class="plans-link danger" @click="removeCreateSection(sectionIndex)">{{ t('plans.deleteSection') }}</button>
            </div>
            <label>{{ t('plans.sectionName') }}<input v-model="section.name" required /></label>
            <label>{{ t('plans.sectionInfo') }}<input v-model="section.info" /></label>
            <div v-for="(task, taskIndex) in section.tasks" :key="taskIndex" class="create-task-row">
              <label>{{ t('plans.taskContent') }}<input v-model="task.content" required /></label>
              <label class="create-task-minutes">{{ t('plans.taskMinutes') }}<input v-model.number="task.time_minutes" type="number" min="0" step="1" /></label>
              <button v-if="section.tasks.length > 1" type="button" class="plans-link danger" @click="removeCreateTask(section, taskIndex)">{{ t('plans.deleteTask') }}</button>
            </div>
            <button type="button" class="plans-link" @click="addCreateTask(section)"><Plus :size="14" /> {{ t('plans.addTask') }}</button>
          </div>
          <button type="button" class="plans-secondary create-add-section" @click="addCreateSection"><Plus :size="14" /> {{ t('plans.addSection') }}</button>
        </div>
        <div class="modal-actions"><button type="button" class="plans-secondary" @click="closeCreatePlan">{{ t('plans.cancel') }}</button><button class="plans-primary" type="submit" :disabled="isLoading">{{ t('plans.createAndEdit') }}</button></div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.plans-hub { min-height: 100vh; color: var(--color-text-primary); background: var(--color-bg); }
.plans-header { display: flex; flex-wrap: wrap; align-items: center; gap: 15px; max-width: 1080px; margin: 0 auto; padding: 30px 28px 20px; }
.plans-title-block { flex: 1 1 220px; min-width: 0; }
.plans-back { display: grid; place-items: center; width: 36px; height: 36px; border: 1px solid var(--color-border); border-radius: 12px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; }
.plans-eyebrow { margin: 0 0 4px; color: var(--color-text-tertiary); font-size: 12px; letter-spacing: .08em; }
.plans-module-description { margin: 5px 0 0; color: var(--color-text-secondary); font-size: 12px; line-height: 1.5; }
.plans-header h1 { margin: 0; font-size: 25px; }
.plans-primary, .plans-secondary, .plans-link { display: inline-flex; align-items: center; justify-content: center; gap: 6px; border-radius: 9px; padding: 8px 12px; cursor: pointer; font-weight: 600; }
.plan-entry-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; margin-left: auto; }
.plans-primary { margin-left: auto; border: 1px solid var(--color-primary); color: var(--color-button-text); background: var(--color-primary); }
.plan-entry-actions .plans-primary { margin-left: 0; }
.plans-secondary { border: 1px solid var(--color-border); color: var(--color-text-secondary); background: var(--color-bg-secondary); }
.plans-link { border: 0; padding-left: 0; color: var(--color-primary); background: transparent; }
.icon-button { display: grid; place-items: center; border: 1px solid var(--color-border); border-radius: 8px; padding: 7px; color: var(--color-text-tertiary); background: var(--color-bg-secondary); cursor: pointer; }
.icon-button:hover { color: var(--color-error); border-color: var(--color-error); }
.plans-content { max-width: 1080px; margin: 0 auto; padding: 10px 28px 50px; }
.template-workspace { display: grid; gap: 18px; margin-bottom: 20px; padding: 20px; border: 1px solid var(--color-border); border-radius: 16px; }
.template-workspace-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.template-workspace-header h2, .template-workspace-header p { margin: 0; }
.template-workspace-header h2 { font-size: 20px; }
.template-workspace-header p:last-child { margin-top: 5px; color: var(--color-text-secondary); font-size: 12px; }
.template-workspace-form { display: grid; grid-template-columns: minmax(220px, 1.6fr) minmax(160px, 1fr) minmax(150px, .8fr) auto; align-items: end; gap: 10px; }
.template-workspace-form label { display: grid; gap: 6px; color: var(--color-text-secondary); font-size: 12px; }
.template-workspace-form input, .template-workspace-form select { min-width: 0; border: 1px solid var(--color-border); border-radius: 8px; padding: 8px 10px; color: var(--color-text-primary); background: var(--color-bg-secondary); }
.template-workspace-actions { display: flex; gap: 8px; }
.template-workspace-empty { min-height: 90px; }
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
.plans-search { display: grid; gap: 6px; margin-bottom: 14px; color: var(--color-text-tertiary); font-size: 12px; font-weight: 650; }
.plans-search input { width: 100%; box-sizing: border-box; border: 1px solid var(--color-border); border-radius: 10px; padding: 10px 12px; color: var(--color-text-primary); background: var(--color-bg-secondary); font: inherit; font-weight: 400; outline: 0; }
.plans-search input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-muted); }
.plans-error, .plans-success { margin-bottom: 14px; font-size: 13px; }
.plans-error { color: var(--color-error); }
.plans-success { color: var(--color-success, #16a34a); }
.plans-readonly-note { display: grid; gap: 4px; margin-bottom: 14px; padding: 12px 14px; border: 1px solid var(--color-primary); border-radius: 12px; color: var(--color-text-secondary); background: var(--color-bg-secondary); font-size: 13px; line-height: 1.5; }
.plans-readonly-note strong { color: var(--color-text-primary); }
.plans-retry { justify-self: start; }
.detail-toolbar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.detail-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.meta-editor, .section-editor { display: flex; align-items: flex-end; gap: 10px; margin-bottom: 14px; padding: 14px; border: 1px solid var(--color-border); border-radius: 14px; }
.meta-editor label, .section-editor label, .task-editor label, .create-modal label { display: grid; gap: 6px; color: var(--color-text-secondary); font-size: 12px; }
.meta-editor input, .section-editor input, .task-editor input, .create-modal input { min-width: 0; border: 1px solid var(--color-border); border-radius: 8px; padding: 8px 10px; color: var(--color-text-primary); background: var(--color-bg-secondary); outline: none; }
.meta-editor input:focus, .section-editor input:focus, .task-editor input:focus, .create-modal input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-muted); }
.create-modal { width: min(440px, calc(100vw - 32px)); }
.plan-detail-summary { display: flex; flex-wrap: wrap; gap: 18px 38px; margin-bottom: 14px; padding: 17px 20px; border: 1px solid var(--color-border); border-radius: 14px; }
.plan-detail-summary div { display: grid; gap: 4px; }
.plan-detail-summary span { color: var(--color-text-tertiary); font-size: 12px; }
.plan-detail-progress { min-width: 130px; }
.plan-detail-layout { display: grid; gap: 14px; }
.plan-detail-aside, .plan-detail-main { min-width: 0; }
.plan-detail-aside { display: grid; align-content: start; gap: 14px; }
.plan-detail-aside .plan-detail-summary, .plan-detail-aside .log-editor, .plan-detail-aside .log-list { margin-bottom: 0; }
.plan-detail-aside .plan-detail-summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.plan-detail-aside .plan-detail-progress { min-width: 0; grid-column: 1 / -1; }
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
.plan-section > header { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }
.plan-section > header > div { display: flex; align-items: center; gap: 9px; min-width: 0; }
.section-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 7px; }
.section-letter { display: grid; place-items: center; width: 26px; height: 26px; border-radius: 8px; color: var(--color-button-text); background: var(--color-primary); font-size: 12px; font-weight: 700; }
.plan-section header small { overflow: hidden; color: var(--color-text-tertiary); text-overflow: ellipsis; white-space: nowrap; }
.task-editor { display: flex; align-items: flex-end; gap: 9px; margin: 15px 0 8px; padding: 10px; border-radius: 10px; background: var(--color-bg-secondary); }
.task-editor label:first-child { flex: 1; }
.task-minutes-field { flex: 0 0 110px; }
.task-minutes-field small { color: var(--color-text-tertiary); font-size: 10px; line-height: 1.3; }
.task-minutes-field input { width: 100%; box-sizing: border-box; }
.group-editor { display: grid; grid-template-columns: minmax(120px, .8fr) minmax(160px, 1.4fr) 110px 110px auto auto; align-items: end; gap: 8px; margin: 10px 0; padding: 10px; border: 1px dashed var(--color-border); border-radius: 10px; background: var(--color-bg-secondary); }
.group-editor label { display: grid; gap: 5px; color: var(--color-text-tertiary); font-size: 11px; }
.group-editor input, .group-editor select { width: 100%; min-width: 0; box-sizing: border-box; border: 1px solid var(--color-border); border-radius: 7px; padding: 7px 8px; color: var(--color-text-primary); background: var(--color-bg); outline: none; }
.section-empty { color: var(--color-text-tertiary); font-size: 13px; }
.archive-unavailable { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.event-task-row { display: grid; grid-template-columns: 24px minmax(0, 1fr) auto 64px auto 64px 28px 28px; align-items: center; gap: 8px; padding: 12px 0; border-top: 1px solid var(--color-border); }
.event-task-row > div { display: flex; align-items: baseline; gap: 10px; min-width: 0; }
.event-task-row > div strong { color: var(--color-primary); font-size: 12px; }
.event-task-row > div span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.event-task-row > small { color: var(--color-text-tertiary); white-space: nowrap; }
.task-log { border: 0; border-radius: 7px; padding: 5px 7px; color: var(--color-primary); background: var(--color-primary-muted); cursor: pointer; font-size: 11px; white-space: nowrap; }
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
.archive-task-preview { display: grid; gap: 5px; margin-top: 10px; width: 100%; }
.archive-task-preview-row { display: grid; grid-template-columns: 40px minmax(0, 1fr) auto; align-items: center; gap: 8px; border: 1px solid transparent; border-radius: 8px; padding: 6px 8px; color: var(--color-text-secondary); background: var(--color-bg); font-size: 12px; }
.archive-task-preview-row > span { color: var(--color-primary); font-family: var(--font-mono); font-size: 11px; font-weight: 700; }
.archive-task-preview-row strong { min-width: 0; overflow: hidden; color: var(--color-text-primary); text-overflow: ellipsis; white-space: nowrap; }
.archive-task-preview-row small { color: var(--color-text-tertiary); white-space: nowrap; }
.archive-task-preview-row.search-target { border-color: var(--color-primary); background: var(--color-primary-muted); box-shadow: 0 0 0 2px var(--color-primary-muted); }
.modal-backdrop { position: fixed; inset: 0; z-index: 20; display: grid; place-items: center; padding: 20px; background: rgba(0,0,0,.3); }
.create-modal { display: grid; gap: 14px; width: min(440px, calc(100vw - 40px)); max-height: calc(100vh - 40px); box-sizing: border-box; overflow-y: auto; padding: 24px; border: 1px solid var(--color-border); border-radius: 18px; background: var(--color-bg); box-shadow: var(--shadow-lg, 0 18px 50px rgba(0,0,0,.2)); }
.create-modal h2, .create-modal p { margin: 0; }
.create-modal p { color: var(--color-text-secondary); font-size: 13px; }
.create-editor-note { border: 1px solid var(--color-primary-muted); border-radius: 10px; padding: 10px 12px; color: var(--color-text-secondary); background: var(--color-primary-muted); line-height: 1.5; }
.create-editor-note span { display: block; margin-top: 3px; font-size: 12px; }
.create-sections { display: grid; gap: 10px; max-height: min(42vh, 360px); overflow-y: auto; padding-right: 2px; }
.create-section { display: grid; gap: 8px; border: 1px solid var(--color-border); border-radius: 11px; padding: 11px; background: var(--color-bg-secondary); }
.create-section-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.create-section label, .create-task-row label { display: grid; gap: 4px; color: var(--color-text-secondary); font-size: 11px; }
.create-section input { min-width: 0; border: 1px solid var(--color-border); border-radius: 7px; padding: 7px 8px; color: var(--color-text-primary); background: var(--color-bg); outline: none; }
.create-task-row { display: grid; grid-template-columns: minmax(0, 1fr) 120px auto; align-items: end; gap: 7px; }
.create-task-minutes input { width: 100%; box-sizing: border-box; }
.create-section .plans-link { justify-self: start; margin: 0; padding: 4px 0; }
.create-section .plans-link.danger, .create-section-header .plans-link.danger { color: var(--color-error); }
.create-add-section { justify-self: start; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; }
@media (min-width: 1100px) {
  .plan-detail-layout { grid-template-columns: minmax(250px, .34fr) minmax(0, 1fr); align-items: start; gap: 20px; }
}
@media (prefers-reduced-motion: reduce) { .domain-card, .event-plan-card { transition: none; } }
/* The two-column detail workspace starts at 1100px. Tablet keeps the task
   row horizontal with compact controls; only the mobile breakpoint stacks
   actions below the task title. */
@media (max-width: 1099px) {
  .meta-editor, .section-editor, .task-editor, .log-editor { align-items: stretch; flex-direction: column; }
  .log-editor { display: flex; }
}
@media (min-width: 761px) and (max-width: 1099px) {
  .group-editor { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); align-items: end; }
  .group-editor label:nth-child(1), .group-editor label:nth-child(2) { grid-column: 1 / -1; }
  .group-editor button { min-height: 38px; }
  .event-task-row { grid-template-columns: 24px minmax(120px, 1fr) auto 58px auto 58px 28px 28px; gap: 5px; }
}
@media (max-width: 760px) { .plans-header, .plans-content { padding-left: 18px; padding-right: 18px; } .plan-entry-actions { margin-left: auto; } .template-workspace-header { flex-direction: column; } .template-workspace-form { grid-template-columns: 1fr; } .template-workspace-actions { justify-content: flex-end; } .plan-domain-grid, .event-plan-grid { grid-template-columns: 1fr; } .meta-editor > div { display: flex; justify-content: flex-end; } .plan-detail-summary { gap: 18px; justify-content: space-between; } .section-actions { justify-content: flex-end; } .group-editor { grid-template-columns: 1fr; } .group-editor label:nth-child(1), .group-editor label:nth-child(2) { grid-column: auto; } .group-editor button { width: 100%; } .event-task-row { grid-template-columns: 24px minmax(0, 1fr) auto auto; } .event-task-row > div { grid-column: 2; grid-row: 1; } .event-task-row > small { grid-column: 2; grid-row: 2; } .event-task-row .task-log { grid-column: 2; grid-row: 3; justify-self: start; } .event-task-row .task-edit { grid-column: 3; grid-row: 1; } .event-task-row .task-delete { grid-column: 4; grid-row: 1; } .create-task-row { grid-template-columns: 1fr; } }
</style>
