<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Check, ChevronDown, ChevronUp, ListTodo, Pencil, Pin, Plus, Settings2, Trash2 } from 'lucide-vue-next'
import { AudioManager } from '@/audio'
import { DataService, parseStoredDate } from '@/services/dataService'
import {
  TodoCategoryService,
  TodoSettingsService,
  TodoService,
  type TodoCategory,
  type TodoPriority,
  type TodoRecurrence,
  type TodoSettings,
  type UnifiedTodo,
} from '@/services/todoService'
import { completePlanTask, getPlanTasks, listPlanArchives, listPlanSummaries, planDataSource, updatePlanTask, type PlanArchiveSummary, type PlanGatewayState, type PlanSummary, type PlanTaskSummary } from '@/services/planGateway'
import { getPriorityScore } from '@/services/priority'
import { notifyToast } from '@/services/toastService'
import { requestConfirm } from '@/services/confirmService'
import { onWorkspaceChanged } from '@/services/workspaceEvents'
import { useI18n } from '@/i18n'
const CategoryIconPicker = defineAsyncComponent(() => import('@/components/CategoryIconPicker.vue'))
const CategoryIconPreview = defineAsyncComponent(() => import('@/components/CategoryIconPreview.vue'))

const router = useRouter()
const route = useRoute()
const { t, locale } = useI18n()

function parseTodoTags(value: string): string[] {
  return [...new Set(value.split(',').map((tag) => tag.trim()).filter(Boolean))]
}

const todos = ref<UnifiedTodo[]>([])
const title = ref('')
const description = ref('')
const tagsInput = ref('')
const priorityRank = ref(0)
const urgent = ref(false)
const important = ref(false)
const estimatedTime = ref(60)
const deadline = ref('')
const recurrence = ref<TodoRecurrence>('none')
const category = ref('default')
const selectedPlanId = ref('')
const selectedPlanTaskId = ref('')
const filter = ref<'all' | 'active' | 'completed'>('active')
const categoryFilter = ref('')
const isLoading = ref(true)
const errorMessage = ref('')
const editingId = ref<string | null>(null)
const editingTitle = ref('')
const editingDescription = ref('')
const editingTagsInput = ref('')
const editingPriorityRank = ref(0)
const editingUrgent = ref(false)
const editingImportant = ref(false)
const editingEstimatedTime = ref(60)
const editingDeadline = ref('')
const editingRecurrence = ref<TodoRecurrence>('none')
const editingCategory = ref('default')
const editingPlanId = ref('')
const editingPlanTaskId = ref('')
const isSaving = ref(false)
const creatingTodo = ref(false)
const completingTodoId = ref<string | null>(null)
const selectedTodoIds = ref<Set<string>>(new Set())
const bulkWorking = ref(false)
const expandedTodoId = ref<string | null>(null)
const searchTargetTodoId = ref<string | null>(null)
const subtaskTitle = ref('')
const subtaskSaving = ref(false)
const trackedMinutes = ref(25)
const trackingTodoId = ref<string | null>(null)
const focusTodoId = ref<string | null>(null)
const focusStartedAt = ref<number | null>(null)
const focusElapsedSeconds = ref(0)
const planSummaries = ref<PlanSummary[]>([])
const planArchives = ref<PlanArchiveSummary[]>([])
const planGatewayState = ref<PlanGatewayState>('idle')
const planTasks = ref<PlanTaskSummary[]>([])
const planTaskState = ref<PlanGatewayState>('idle')
const categories = ref<TodoCategory[]>([])
const showCategoryManager = ref(false)
const categoryName = ref('')
const categoryColor = ref('#6366f1')
const categoryIcon = ref('circle')
const categoryAsciiIcon = ref('')
const categoryDifficulty = ref(5)
const editingCategoryId = ref<string | null>(null)
const editingCategoryName = ref('')
const editingCategoryColor = ref('#6366f1')
const editingCategoryIcon = ref('circle')
const editingCategoryAsciiIcon = ref('')
const editingCategoryDifficulty = ref(5)
const priorityClock = ref(Date.now())
const todoSettings = ref<TodoSettings>({ updateFrequency: 60_000, expandCount: 5 })
const settingsSaving = ref(false)
let priorityTimer: number | null = null
let focusTimer: number | null = null

const activeTodos = computed(() => todos.value.filter((todo) => !['completed', 'archived', 'cancelled'].includes(todo.status)))
const completedTodos = computed(() => todos.value.filter((todo) => todo.status === 'completed'))
const categoryById = computed(() => new Map(categories.value.map((item) => [item.id, item])))

function categoryLabel(item: Pick<TodoCategory, 'id' | 'name'>): string {
  return item.id === 'default' && (item.name === '默认' || item.name === 'Default')
    ? t('tasks.defaultCategory')
    : item.name
}

function todoCategoryLabel(categoryId: string): string {
  const item = categoryById.value.get(categoryId)
  return item ? categoryLabel(item) : categoryId
}

function scoreFor(todo: UnifiedTodo) {
  return getPriorityScore(todo, categoryById.value.get(todo.category), new Date(priorityClock.value))
}

const visibleTodos = computed(() => {
  const source = filter.value === 'active'
    ? activeTodos.value
    : filter.value === 'completed'
      ? completedTodos.value
      : todos.value
  const filtered = categoryFilter.value
    ? source.filter((todo) => todo.category === categoryFilter.value)
    : source
  return [...filtered].sort((left, right) => {
    if (Boolean(right.pinned) !== Boolean(left.pinned)) {
      return Number(Boolean(right.pinned)) - Number(Boolean(left.pinned))
    }
    const scoreDelta = scoreFor(right).score - scoreFor(left).score
    if (scoreDelta !== 0) return scoreDelta
    return right.updated_at.localeCompare(left.updated_at)
  })
})

const selectedTodoCount = computed(() => selectedTodoIds.value.size)
const allVisibleTodosSelected = computed(() => visibleTodos.value.length > 0 && visibleTodos.value.every((todo) => selectedTodoIds.value.has(todo.id)))

const categorySummaries = computed(() => categories.value.map((category) => {
  const items = activeTodos.value.filter((todo) => todo.category === category.id)
  const score = items.reduce((total, todo) => total + Math.max(0, scoreFor(todo).score), 0)
  return {
    category,
    count: items.length,
    score: items.length > 0 ? score / Math.sqrt(items.length) : 0,
  }
}).sort((left, right) => {
  if (Boolean(right.category.pinned) !== Boolean(left.category.pinned)) {
    return Number(Boolean(right.category.pinned)) - Number(Boolean(left.category.pinned))
  }
  if ((right.count > 0) !== (left.count > 0)) return Number(right.count > 0) - Number(left.count > 0)
  return right.score - left.score || left.category.name.localeCompare(right.category.name)
}))

const activeCategorySummaries = computed(() => categorySummaries.value.filter((item) => item.count > 0))
const emptyCategorySummaries = computed(() => categorySummaries.value.filter((item) => item.count === 0))
const showAllCategories = ref(false)
const showEmptyCategories = ref(false)
const visibleCategorySummaries = computed(() => showAllCategories.value
  ? activeCategorySummaries.value
  : activeCategorySummaries.value.slice(0, Math.max(1, todoSettings.value.expandCount)))

const recurrenceLabels = computed<Record<TodoRecurrence, string>>(() => ({
  none: t('tasks.recurrenceNone'),
  daily: t('tasks.recurrenceDaily'),
  weekly: t('tasks.recurrenceWeekly'),
  monthly: t('tasks.recurrenceMonthly'),
  custom: t('tasks.recurrenceCustom'),
}))

function priorityKind(isUrgent: boolean, isImportant: boolean): TodoPriority {
  if (isUrgent && isImportant) return 'urgent-important'
  if (isImportant) return 'important'
  if (isUrgent) return 'urgent'
  return 'normal'
}

function restartPriorityTimer() {
  if (priorityTimer !== null) window.clearInterval(priorityTimer)
  if (todoSettings.value.updateFrequency <= 0) return
  priorityTimer = window.setInterval(() => { priorityClock.value = Date.now() }, todoSettings.value.updateFrequency)
}

async function loadTodoSettings() {
  todoSettings.value = await TodoSettingsService.get()
  restartPriorityTimer()
}

async function saveTodoSettings() {
  settingsSaving.value = true
  try {
    todoSettings.value = await TodoSettingsService.save(todoSettings.value)
    restartPriorityTimer()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.settings')
  } finally {
    settingsSaving.value = false
  }
}

const planNameById = computed(() => Object.fromEntries([
  ...planSummaries.value.map((plan) => [plan.id, plan.name] as const),
  ...planArchives.value.filter((archive) => archive.plan_id !== undefined).map((archive) => [String(archive.plan_id), archive.name || `#${archive.plan_id}`] as const),
]))
const archivedPlanById = computed(() => Object.fromEntries(
  planArchives.value
    .filter((archive) => archive.plan_id !== undefined)
    .map((archive) => [String(archive.plan_id), archive] as const),
))
const planTaskById = computed(() => Object.fromEntries(
  planTasks.value.flatMap((task) => [
    [task.internal_id, task] as const,
    [task.display_id, task] as const,
  ]),
))

async function loadTodos() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    todos.value = await TodoService.list()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.load')
  } finally {
    isLoading.value = false
  }
}

async function addTodo() {
  if (!title.value.trim() || creatingTodo.value) return
  creatingTodo.value = true
  try {
    const todo = await TodoService.create({
      title: title.value,
      description: description.value,
      tags: parseTodoTags(tagsInput.value),
      priority: priorityKind(urgent.value, important.value),
      priority_rank: Math.max(0, Math.trunc(Number(priorityRank.value) || 0)),
      urgent: urgent.value,
      important: important.value,
      estimated_time: Math.max(1, Math.trunc(Number(estimatedTime.value) || 60)),
      deadline: deadline.value ? new Date(`${deadline.value}T23:59:59`).toISOString() : undefined,
      recurrence: recurrence.value,
      category: category.value,
      related_plan_id: selectedPlanId.value || undefined,
      related_plan_task_id: selectedPlanId.value ? selectedPlanTaskId.value || undefined : undefined,
    })
    todos.value = [todo, ...todos.value]
    title.value = ''
    description.value = ''
    tagsInput.value = ''
    priorityRank.value = 0
    urgent.value = false
    important.value = false
    estimatedTime.value = 60
    deadline.value = ''
    recurrence.value = 'none'
    category.value = 'default'
    selectedPlanId.value = ''
    selectedPlanTaskId.value = ''
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.create')
  } finally {
    creatingTodo.value = false
  }
}

async function loadCategories() {
  try {
    categories.value = await TodoCategoryService.ensureDefaults(todos.value)
  } catch {
    categories.value = []
  }
}

function beginCategoryEdit(item: TodoCategory) {
  editingCategoryId.value = item.id
  editingCategoryName.value = item.name
  editingCategoryColor.value = item.color
  editingCategoryIcon.value = item.icon || 'circle'
  editingCategoryAsciiIcon.value = item.ascii_icon || ''
  editingCategoryDifficulty.value = item.difficulty
}

function cancelCategoryEdit() {
  editingCategoryId.value = null
  editingCategoryAsciiIcon.value = ''
}

async function createCategory() {
  if (!categoryName.value.trim()) return
  try {
    const created = await TodoCategoryService.create({
      name: categoryName.value,
      color: categoryColor.value,
      icon: categoryIcon.value,
      ascii_icon: categoryAsciiIcon.value || undefined,
      difficulty: categoryDifficulty.value,
    })
    categories.value = [...categories.value, created].sort((a, b) => a.name.localeCompare(b.name))
    categoryName.value = ''
    categoryColor.value = '#6366f1'
    categoryIcon.value = 'circle'
    categoryAsciiIcon.value = ''
    categoryDifficulty.value = 5
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.category')
  }
}

async function saveCategory(item: TodoCategory) {
  try {
    const updated = await TodoCategoryService.update(item.id, {
      name: editingCategoryName.value,
      color: editingCategoryColor.value,
      icon: editingCategoryIcon.value,
      ascii_icon: editingCategoryAsciiIcon.value || undefined,
      difficulty: editingCategoryDifficulty.value,
    })
    categories.value = categories.value.map((categoryItem) => categoryItem.id === updated.id ? updated : categoryItem)
    editingCategoryId.value = null
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.category')
  }
}

async function removeCategory(item: TodoCategory) {
  if (item.id === 'default' || !(await requestConfirm(`${t('tasks.deleteCategory')}?`, { tone: 'danger' }))) return
  try {
    const affected = todos.value.filter((todo) => todo.category === item.id)
    for (const todo of affected) {
      const updated = await TodoService.update(todo.id, { category: 'default' })
      replaceTodo(updated)
    }
    await TodoCategoryService.remove(item.id)
    categories.value = categories.value.filter((categoryItem) => categoryItem.id !== item.id)
    if (categoryFilter.value === item.id) categoryFilter.value = ''
    if (category.value === item.id) category.value = 'default'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.category')
  }
}

async function toggleCategoryPinned(item: TodoCategory) {
  try {
    const updated = await TodoCategoryService.update(item.id, { pinned: !item.pinned })
    categories.value = categories.value.map((categoryItem) => categoryItem.id === updated.id ? updated : categoryItem)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.category')
  }
}

async function loadPlanSummaries() {
  planGatewayState.value = 'loading'
  try {
    const [activePlans, archivedPlans] = await Promise.all([listPlanSummaries(), listPlanArchives()])
    planSummaries.value = activePlans
    planArchives.value = archivedPlans
    planGatewayState.value = planDataSource.value === 'cache' ? 'unavailable' : 'ready'
  } catch {
    planSummaries.value = []
    planGatewayState.value = 'unavailable'
  }
}

async function loadPlanTasks(planId: string) {
  planTasks.value = []
  if (!planId) {
    planTasks.value = []
    planTaskState.value = 'idle'
    return
  }
  planTaskState.value = 'loading'
  try {
    planTasks.value = await getPlanTasks(planId)
    planTaskState.value = planDataSource.value === 'cache' ? 'unavailable' : 'ready'
    if (planDataSource.value === 'cache') planGatewayState.value = 'unavailable'
  } catch {
    planTasks.value = []
    planTaskState.value = 'unavailable'
  }
}

async function retryPlanGateway(): Promise<void> {
  if (planGatewayState.value === 'loading') return
  await loadPlanSummaries()
  if (selectedPlanId.value) await loadPlanTasks(selectedPlanId.value)
}

async function refreshFromWorkspace(source?: string): Promise<void> {
  if (!source || !['todos', 'plans', 'records', 'archive', 'settings'].includes(source)) return
  if (source === 'settings') {
    await loadTodoSettings()
    return
  }
  await loadTodos()
  await loadCategories()
  if (source === 'plans' || source === 'archive') await loadPlanSummaries()
  if (selectedPlanId.value) await loadPlanTasks(selectedPlanId.value)
}

async function completeTodo(todo: UnifiedTodo) {
  if (todo.status === 'completed' || completingTodoId.value === todo.id) return
  completingTodoId.value = todo.id
  try {
    // Complete the source plan task first. Without a transaction spanning
    // IndexedDB and plan-helper, this prevents a failed plan sync from
    // silently leaving the local todo in a completed state.
    if (todo.related_plan_id && todo.related_plan_task_id) {
      try {
        await completePlanTask(todo.related_plan_id, todo.related_plan_task_id)
      } catch {
        errorMessage.value = t('tasks.planSyncFailed')
        return
      }
    }
    const updated = await TodoService.complete(todo.id)
    const index = todos.value.findIndex((item) => item.id === todo.id)
    if (index >= 0) todos.value[index] = updated
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.update')
  } finally {
    completingTodoId.value = null
  }
}

function startEdit(todo: UnifiedTodo) {
  editingId.value = todo.id
  editingTitle.value = todo.title
  editingDescription.value = todo.description || ''
  editingTagsInput.value = (todo.tags || []).join(', ')
  editingPriorityRank.value = todo.priority_rank ?? 0
  editingUrgent.value = todo.urgent ?? (todo.priority === 'urgent' || todo.priority === 'urgent-important')
  editingImportant.value = todo.important ?? (todo.priority === 'important' || todo.priority === 'urgent-important')
  editingEstimatedTime.value = todo.estimated_time ?? todo.time_estimate ?? 60
  editingDeadline.value = todo.deadline ? todo.deadline.slice(0, 10) : ''
  editingRecurrence.value = todo.recurrence || 'none'
  editingCategory.value = todo.category || 'default'
  editingPlanId.value = todo.related_plan_id || ''
  editingPlanTaskId.value = todo.related_plan_task_id || ''
  loadPlanTasks(editingPlanId.value)
  errorMessage.value = ''
}

function cancelEdit() {
  editingId.value = null
  editingTitle.value = ''
  editingDescription.value = ''
  editingTagsInput.value = ''
  editingPriorityRank.value = 0
  editingUrgent.value = false
  editingImportant.value = false
  editingEstimatedTime.value = 60
  editingDeadline.value = ''
  editingRecurrence.value = 'none'
  editingCategory.value = 'default'
  editingPlanId.value = ''
  editingPlanTaskId.value = ''
  loadPlanTasks(selectedPlanId.value)
}

async function saveEdit(todo: UnifiedTodo) {
  if (!editingTitle.value.trim() || isSaving.value) return
  isSaving.value = true
  try {
    const linkedTaskChanged = Boolean(
      todo.related_plan_id
      && todo.related_plan_task_id
      && editingPlanId.value === todo.related_plan_id
      && editingPlanTaskId.value === todo.related_plan_task_id
      && (editingTitle.value.trim() !== todo.title || Math.max(1, Math.trunc(Number(editingEstimatedTime.value) || 60)) !== (todo.estimated_time ?? todo.time_estimate ?? 60)),
    )
    if (linkedTaskChanged) {
      try {
        await updatePlanTask(todo.related_plan_id as string, todo.related_plan_task_id as string, editingTitle.value.trim(), Math.max(1, Math.trunc(Number(editingEstimatedTime.value) || 60)))
      } catch {
        errorMessage.value = t('tasks.planSyncFailed')
        return
      }
    }
    const updated = await TodoService.update(todo.id, {
      title: editingTitle.value,
      description: editingDescription.value,
      tags: parseTodoTags(editingTagsInput.value),
      priority: priorityKind(editingUrgent.value, editingImportant.value),
      priority_rank: Math.max(0, Math.trunc(Number(editingPriorityRank.value) || 0)),
      urgent: editingUrgent.value,
      important: editingImportant.value,
      estimated_time: Math.max(1, Math.trunc(Number(editingEstimatedTime.value) || 60)),
      deadline: editingDeadline.value ? new Date(`${editingDeadline.value}T23:59:59`).toISOString() : undefined,
      recurrence: editingRecurrence.value,
      category: editingCategory.value,
      related_plan_id: editingPlanId.value || undefined,
      related_plan_task_id: editingPlanId.value ? editingPlanTaskId.value || undefined : undefined,
    })
    const index = todos.value.findIndex((item) => item.id === todo.id)
    if (index >= 0) todos.value[index] = updated
    cancelEdit()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.save')
  } finally {
    isSaving.value = false
  }
}

async function removeTodo(todo: UnifiedTodo) {
  if (!(await requestConfirm(t('tasks.deleteConfirm'), { tone: 'danger' }))) return
  try {
    try {
      await DataService.unlinkTodoFromRecords(todo.id)
    } catch (error) {
      console.warn('Failed to clean deleted todo record links', error)
    }
    await TodoService.remove(todo.id)
    todos.value = todos.value.filter((item) => item.id !== todo.id)
    notifyToast(t('tasks.deleted'), 'success')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.delete')
  }
}

function toggleTodoSelection(todoId: string) {
  const next = new Set(selectedTodoIds.value)
  if (next.has(todoId)) next.delete(todoId)
  else next.add(todoId)
  selectedTodoIds.value = next
}

function toggleVisibleTodoSelection() {
  const next = new Set(selectedTodoIds.value)
  if (allVisibleTodosSelected.value) {
    visibleTodos.value.forEach((todo) => next.delete(todo.id))
  } else {
    visibleTodos.value.forEach((todo) => next.add(todo.id))
  }
  selectedTodoIds.value = next
}

function clearTodoSelection() {
  selectedTodoIds.value = new Set()
}

async function bulkCompleteTodos() {
  if (bulkWorking.value || selectedTodoCount.value === 0) return
  bulkWorking.value = true
  let completed = 0
  let failed = 0
  try {
    for (const todo of todos.value.filter((item) => selectedTodoIds.value.has(item.id))) {
      if (todo.status === 'completed') continue
      if (todo.related_plan_id && todo.related_plan_task_id) {
        try {
          await completePlanTask(todo.related_plan_id, todo.related_plan_task_id)
        } catch {
          failed += 1
          continue
        }
      }
      replaceTodo(await TodoService.complete(todo.id))
      completed += 1
    }
    notifyToast(t('tasks.bulkCompleted', { count: completed }), 'success')
    if (failed > 0) errorMessage.value = t('tasks.bulkPlanSyncFailed', { count: failed })
    clearTodoSelection()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.update')
  } finally {
    bulkWorking.value = false
  }
}

async function bulkDeleteTodos() {
  if (bulkWorking.value || selectedTodoCount.value === 0 || !(await requestConfirm(t('tasks.bulkDeleteConfirm', { count: selectedTodoCount.value }), { tone: 'danger' }))) return
  bulkWorking.value = true
  let deleted = 0
  try {
    for (const todo of todos.value.filter((item) => selectedTodoIds.value.has(item.id))) {
      try {
        await DataService.unlinkTodoFromRecords(todo.id)
      } catch (error) {
        console.warn('Failed to clean deleted todo record links', error)
      }
      await TodoService.remove(todo.id)
      deleted += 1
    }
    todos.value = todos.value.filter((todo) => !selectedTodoIds.value.has(todo.id))
    clearTodoSelection()
    notifyToast(t('tasks.bulkDeleted', { count: deleted }), 'success')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.delete')
  } finally {
    bulkWorking.value = false
  }
}

async function toggleTodoPinned(todo: UnifiedTodo) {
  try {
    replaceTodo(await TodoService.update(todo.id, { pinned: !todo.pinned }))
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.update')
  }
}

async function adjustTodoRank(todo: UnifiedTodo, delta: number) {
  const nextRank = Math.max(0, Math.trunc(Number(todo.priority_rank) || 0) + delta)
  if (nextRank === (todo.priority_rank ?? 0)) return
  try {
    replaceTodo(await TodoService.update(todo.id, { priority_rank: nextRank }))
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.update')
  }
}

function replaceTodo(updated: UnifiedTodo) {
  const index = todos.value.findIndex((item) => item.id === updated.id)
  if (index >= 0) todos.value[index] = updated
}

function toggleTodoDetails(todo: UnifiedTodo) {
  expandedTodoId.value = expandedTodoId.value === todo.id ? null : todo.id
  subtaskTitle.value = ''
  errorMessage.value = ''
}

function subtaskProgress(todo: UnifiedTodo): string {
  const completed = todo.subtasks.filter((subtask) => subtask.completed).length
  return `${completed}/${todo.subtasks.length}`
}

function makeTimeRecordId(): string {
  const suffix = typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID().slice(0, 8)
    : Math.random().toString(36).slice(2, 10)
  return `TR-${suffix.toUpperCase()}`
}

function formatClock(date: Date): string {
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

function formatLocalDate(date: Date): string {
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
}

async function persistTodoTime(todo: UnifiedTodo, minutes: number, startedAt = new Date()) {
  if (trackingTodoId.value) return
  trackingTodoId.value = todo.id
  try {
    const startDate = new Date(startedAt)
    startDate.setSeconds(0, 0)
    let cursor = startDate
    let remaining = minutes
    const recordRefs: Array<{ id: string; day: string }> = []

    try {
      while (remaining > 0) {
        const nextMidnight = new Date(cursor)
        nextMidnight.setHours(24, 0, 0, 0)
        const minutesUntilMidnight = Math.max(1, Math.round((nextMidnight.getTime() - cursor.getTime()) / 60000))
        const chunk = Math.min(remaining, minutesUntilMidnight)
        const endsAtMidnight = chunk === minutesUntilMidnight
        const endDate = endsAtMidnight
          ? nextMidnight
          : new Date(cursor.getTime() + chunk * 60 * 1000)
        const recordId = makeTimeRecordId()
        const recordDay = formatLocalDate(cursor)
        recordRefs.push({ id: recordId, day: recordDay })
        await DataService.saveRecord({
          id: recordId,
          todo_id: todo.id,
          date: recordDay,
          start: formatClock(cursor),
          end: endsAtMidnight ? '24:00' : formatClock(endDate),
          duration: chunk / 60,
          content: todo.title,
          tag: todo.category || 'default',
        }, recordDay)
        remaining -= chunk
        cursor = endDate
      }

      replaceTodo(await TodoService.trackTime(todo.id, minutes, recordRefs.map((record) => record.id)))
      notifyToast(t('tasks.timeRecorded', { minutes }), 'success')
    } catch (error) {
      const rollbackErrors: unknown[] = []
      for (const record of recordRefs) {
        try {
          await DataService.deleteRecordById(record.id, record.day)
        } catch (rollbackError) {
          rollbackErrors.push(rollbackError)
        }
      }
      if (rollbackErrors.length > 0) throw new Error(t('tasks.error.trackTimeRollback'))
      throw error
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.trackTime')
  } finally {
    trackingTodoId.value = null
  }
}

async function trackTodoTime(todo: UnifiedTodo) {
  if (!Number.isInteger(trackedMinutes.value) || trackedMinutes.value < 1 || trackedMinutes.value > 1440) return
  await persistTodoTime(todo, trackedMinutes.value)
  trackedMinutes.value = 25
}

async function openTodoRecords(todo: UnifiedTodo) {
  const dates = await DataService.findRecordDatesByTodoId(todo.id)
  if (dates.length > 0) {
    router.push({ path: `/day/${dates[dates.length - 1]}`, query: { todo: todo.id } })
    return
  }
  router.push({ path: '/records', query: { todo: todo.id } })
}

function openTodoPlan(todo: UnifiedTodo) {
  if (!todo.related_plan_id) return
  router.push({
    path: '/plans',
    query: {
      plan: todo.related_plan_id,
      ...(todo.related_plan_task_id ? { task: todo.related_plan_task_id } : {}),
    },
  })
}

const focusElapsedLabel = computed(() => {
  const minutes = Math.floor(focusElapsedSeconds.value / 60)
  const seconds = focusElapsedSeconds.value % 60
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
})

function clearFocusTimer() {
  if (focusTimer !== null) window.clearInterval(focusTimer)
  focusTimer = null
}

function startFocus(todo: UnifiedTodo) {
  if (focusTodoId.value || trackingTodoId.value) return
  focusTodoId.value = todo.id
  focusStartedAt.value = Date.now()
  focusElapsedSeconds.value = 0
  focusTimer = window.setInterval(() => {
    if (focusStartedAt.value !== null) {
      focusElapsedSeconds.value = Math.floor((Date.now() - focusStartedAt.value) / 1000)
    }
  }, 1000)
}

async function stopFocus(todo: UnifiedTodo) {
  if (focusTodoId.value !== todo.id || focusStartedAt.value === null) return
  const startedAt = new Date(focusStartedAt.value)
  const minutes = Math.max(1, Math.ceil((Date.now() - focusStartedAt.value) / 60000))
  clearFocusTimer()
  focusTodoId.value = null
  focusStartedAt.value = null
  focusElapsedSeconds.value = 0
  await persistTodoTime(todo, minutes, startedAt)
}

async function addSubtask(todo: UnifiedTodo) {
  if (!subtaskTitle.value.trim() || subtaskSaving.value) return
  subtaskSaving.value = true
  try {
    replaceTodo(await TodoService.addSubtask(todo.id, subtaskTitle.value))
    subtaskTitle.value = ''
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.update')
  } finally {
    subtaskSaving.value = false
  }
}

async function toggleSubtask(todo: UnifiedTodo, subtaskId: string) {
  if (subtaskSaving.value) return
  subtaskSaving.value = true
  try {
    replaceTodo(await TodoService.toggleSubtask(todo.id, subtaskId))
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.update')
  } finally {
    subtaskSaving.value = false
  }
}

async function removeSubtask(todo: UnifiedTodo, subtaskId: string) {
  if (subtaskSaving.value || !(await requestConfirm(`${t('tasks.deleteSubtask')}?`, { tone: 'danger' }))) return
  subtaskSaving.value = true
  try {
    replaceTodo(await TodoService.removeSubtask(todo.id, subtaskId))
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.delete')
  } finally {
    subtaskSaving.value = false
  }
}

function formatDeadline(deadline?: string): string {
  if (!deadline) return ''
  const date = parseStoredDate(deadline)
  return Number.isNaN(date.getTime())
    ? deadline
    : new Intl.DateTimeFormat(locale.value, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(date)
}

type DeadlineState = 'overdue' | 'today' | 'upcoming'

function getDeadlineState(deadline?: string): DeadlineState | null {
  if (!deadline) return null
  const date = parseStoredDate(deadline)
  if (Number.isNaN(date.getTime())) return null
  const now = new Date()
  if (date.getTime() < now.getTime()) return 'overdue'
  const localDay = (value: Date) => `${value.getFullYear()}-${value.getMonth()}-${value.getDate()}`
  return localDay(date) === localDay(now) ? 'today' : 'upcoming'
}

function deadlineStateLabel(deadline?: string): string {
  const state = getDeadlineState(deadline)
  if (state === 'overdue') return t('tasks.deadlineOverdue')
  if (state === 'today') return t('tasks.deadlineToday')
  if (state === 'upcoming') return t('tasks.deadlineUpcoming')
  return t('tasks.deadline')
}

async function revealSearchTarget(): Promise<void> {
  const targetId = String(route.query.todo || '')
  if (!targetId || !todos.value.some((todo) => todo.id === targetId)) return
  searchTargetTodoId.value = targetId
  await nextTick()
  document.getElementById(`todo-${targetId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  window.setTimeout(() => { searchTargetTodoId.value = null }, 2200)
}

let stopWorkspaceListener: (() => void) | null = null

onMounted(async () => {
  stopWorkspaceListener = onWorkspaceChanged((source) => {
    void refreshFromWorkspace(source).catch((error) => {
      console.warn('Failed to refresh task center after external change:', error)
    })
  })
  await loadTodos()
  await loadCategories()
  loadPlanSummaries()
  loadTodoSettings()
  await revealSearchTarget()
})

onUnmounted(() => {
  stopWorkspaceListener?.()
  stopWorkspaceListener = null
  if (focusTodoId.value) {
    const activeFocusTodo = todos.value.find((todo) => todo.id === focusTodoId.value)
    if (activeFocusTodo) void stopFocus(activeFocusTodo)
  }
  if (priorityTimer !== null) window.clearInterval(priorityTimer)
  clearFocusTimer()
})

watch(selectedPlanId, (planId) => {
  selectedPlanTaskId.value = ''
  loadPlanTasks(planId)
})

watch(() => route.query.todo, () => {
  if (todos.value.length > 0) void revealSearchTarget()
})
</script>

<template>
  <div class="task-center">
    <header class="task-header">
      <button class="task-back" @click="AudioManager.playSound('click'); router.push('/')" :aria-label="t('common.backHome')">
        <ArrowLeft :size="18" />
      </button>
      <div class="task-title-block">
        <p class="task-eyebrow">{{ t('tasks.moduleLabel') }}</p>
        <h1><ListTodo :size="24" /> {{ t('tasks.title') }}</h1>
        <p class="task-module-description">{{ t('tasks.moduleDescription') }}</p>
      </div>
      <div class="task-counts">
        <span>{{ activeTodos.length }} {{ t('tasks.pending') }}</span>
        <span>{{ completedTodos.length }} {{ t('tasks.completed') }}</span>
      </div>
    </header>

    <main class="task-content">
      <form class="task-create theme-card" @submit.prevent="AudioManager.playSound('click'); addTodo()">
        <label class="task-field-label" for="new-task-title">{{ t('tasks.new') }}</label>
        <input id="new-task-title" v-model="title" class="task-input" :placeholder="t('tasks.addPlaceholder')" />
        <details class="task-create-advanced">
          <summary>{{ t('tasks.advancedOptions') }}</summary>
        <label class="task-field-label task-description-label" for="new-task-description">{{ t('tasks.description') }}</label>
        <textarea id="new-task-description" v-model="description" class="task-description-input" :placeholder="t('tasks.descriptionPlaceholder')" rows="1" />
        <label class="task-field-label" for="new-task-tags">{{ t('tasks.tags') }}</label>
        <input id="new-task-tags" v-model="tagsInput" class="task-tags-input" :placeholder="t('tasks.tagsPlaceholder')" />
        <label class="task-check-label"><input v-model="urgent" type="checkbox" /> {{ t('tasks.urgent') }}</label>
        <label class="task-check-label"><input v-model="important" type="checkbox" /> {{ t('tasks.important') }}</label>
        <label class="task-field-label" for="new-task-estimated-time">{{ t('tasks.estimatedTime') }}</label>
        <input id="new-task-estimated-time" v-model.number="estimatedTime" class="task-number-input task-estimate-input" type="number" min="1" step="1" />
        <label class="task-field-label" for="new-task-category">{{ t('tasks.category') }}</label>
        <select id="new-task-category" v-model="category" class="task-select">
          <option v-for="item in categories" :key="item.id" :value="item.id">{{ categoryLabel(item) }}</option>
        </select>
        <label class="task-field-label" for="new-task-deadline">{{ t('tasks.deadline') }}</label>
        <input id="new-task-deadline" v-model="deadline" class="task-date-input" type="date" />
        <label class="task-field-label" for="new-task-recurrence">{{ t('tasks.recurrence') }}</label>
        <select id="new-task-recurrence" v-model="recurrence" class="task-select">
          <option v-for="(label, value) in recurrenceLabels" :key="value" :value="value">{{ label }}</option>
        </select>
        <label class="task-field-label" for="new-task-plan">{{ t('tasks.plan') }}</label>
        <select id="new-task-plan" v-model="selectedPlanId" class="task-select task-plan-select" :disabled="planGatewayState !== 'ready'">
          <option value="">{{ t('tasks.noPlan') }}</option>
          <option v-for="plan in planSummaries" :key="plan.id" :value="plan.id">{{ plan.name }}</option>
        </select>
        <label class="task-field-label" for="new-task-plan-task">{{ t('tasks.planTask') }}</label>
        <select id="new-task-plan-task" v-model="selectedPlanTaskId" class="task-select task-plan-select" :disabled="!selectedPlanId || planTaskState !== 'ready'">
          <option value="">{{ t('tasks.noTask') }}</option>
          <option v-for="task in planTasks" :key="task.internal_id" :value="task.internal_id">{{ task.display_id }} · {{ task.content }}</option>
        </select>
        </details>
        <button type="submit" class="task-add" :disabled="creatingTodo || !title.trim()">
          <Plus :size="17" /> {{ t('tasks.add') }}
        </button>
      </form>

      <section class="task-toolbar">
        <div class="task-tabs" role="tablist" :aria-label="t('tasks.title')">
          <button :class="{ active: filter === 'active' }" @click="filter = 'active'">{{ t('tasks.active') }}</button>
          <button :class="{ active: filter === 'all' }" @click="filter = 'all'">{{ t('tasks.all') }}</button>
          <button :class="{ active: filter === 'completed' }" @click="filter = 'completed'">{{ t('tasks.completedTab') }}</button>
        </div>
        <select v-model="categoryFilter" class="task-filter-select" :aria-label="t('tasks.categoryFilter')">
          <option value="">{{ t('tasks.allCategories') }}</option>
          <option v-for="item in categories" :key="item.id" :value="item.id">{{ categoryLabel(item) }}</option>
        </select>
        <button class="task-category-manage" @click="showCategoryManager = !showCategoryManager" @keydown.esc="showCategoryManager = false">
          <Settings2 :size="15" /> {{ t('tasks.manageCategories') }}
        </button>
        <label v-if="visibleTodos.length" class="task-select-all">
          <input type="checkbox" :checked="allVisibleTodosSelected" :disabled="bulkWorking" @change="toggleVisibleTodoSelection" />
          {{ t('tasks.selectVisible') }}
        </label>
        <div v-if="selectedTodoCount" class="task-bulk-actions">
          <span>{{ t('tasks.selectedCount', { count: selectedTodoCount }) }}</span>
          <button type="button" :disabled="bulkWorking" @click="bulkCompleteTodos"><Check :size="14" /> {{ t('tasks.bulkComplete') }}</button>
          <button type="button" class="danger" :disabled="bulkWorking" @click="bulkDeleteTodos"><Trash2 :size="14" /> {{ t('tasks.bulkDelete') }}</button>
          <button type="button" class="task-bulk-clear" :disabled="bulkWorking" @click="clearTodoSelection">{{ t('tasks.clearSelection') }}</button>
        </div>
        <span v-if="errorMessage" class="task-error">{{ errorMessage }}</span>
        <div v-else-if="planGatewayState === 'unavailable'" class="task-plan-status task-plan-status-action">
          <span>{{ t('tasks.serviceUnavailable') }}</span>
          <button type="button" class="task-plan-retry" @click="retryPlanGateway">{{ t('tasks.retryPlanService') }}</button>
        </div>
      </section>

      <section v-if="categories.length" class="task-category-nav theme-card">
        <div class="task-category-nav-header">
          <div>
            <strong>{{ t('tasks.categoryRanking') }}</strong>
            <small>{{ t('tasks.categoryRankingHint') }}</small>
          </div>
          <span v-if="activeCategorySummaries.length === 0" class="task-plan-status">{{ t('tasks.noActiveCategory') }}</span>
        </div>
        <div class="task-category-nav-list">
          <button type="button" class="task-category-chip" :class="{ active: !categoryFilter }" @click="categoryFilter = ''">
            {{ t('tasks.allCategories') }}
          </button>
          <button
            v-for="item in visibleCategorySummaries"
            :key="item.category.id"
            type="button"
            class="task-category-chip"
            :class="{ active: categoryFilter === item.category.id }"
            :style="{ '--category-color': item.category.color }"
            @click="categoryFilter = item.category.id"
          >
            <CategoryIconPreview :name="item.category.icon" :ascii="item.category.ascii_icon" />
    <span>{{ categoryLabel(item.category) }}</span><small>{{ item.count }}</small>
          </button>
          <button v-if="activeCategorySummaries.length > Math.max(1, todoSettings.expandCount)" type="button" class="task-category-chip task-category-chip-more" @click="showAllCategories = !showAllCategories">
            {{ showAllCategories ? t('tasks.hideMoreCategories') : t('tasks.showMoreCategories') }}
          </button>
        </div>
        <div v-if="emptyCategorySummaries.length" class="task-empty-category-toggle">
          <button type="button" @click="showEmptyCategories = !showEmptyCategories">
            {{ showEmptyCategories ? t('tasks.hideEmptyCategories') : t('tasks.showEmptyCategories') }} ({{ emptyCategorySummaries.length }})
          </button>
        </div>
        <div v-if="showEmptyCategories" class="task-category-nav-list task-empty-category-list">
          <button v-for="item in emptyCategorySummaries" :key="item.category.id" type="button" class="task-category-chip" :class="{ active: categoryFilter === item.category.id }" :style="{ '--category-color': item.category.color }" @click="categoryFilter = item.category.id">
            <CategoryIconPreview :name="item.category.icon" :ascii="item.category.ascii_icon" />
    <span>{{ categoryLabel(item.category) }}</span><small>0</small>
          </button>
        </div>
      </section>

      <section v-if="showCategoryManager" class="category-manager theme-card" @keydown.esc="showCategoryManager = false">
        <div class="category-manager-header">
          <div>
            <h2>{{ t('tasks.manageCategories') }}</h2>
            <p>{{ t('tasks.categoryHint') }}</p>
          </div>
          <button type="button" class="task-edit-cancel" @click="showCategoryManager = false">{{ t('tasks.cancel') }}</button>
        </div>
        <form class="category-create" @submit.prevent="createCategory">
          <label for="category-name">{{ t('tasks.categoryName') }}</label>
          <input id="category-name" v-model="categoryName" :placeholder="t('tasks.categoryName')" />
          <label for="category-color">{{ t('tasks.categoryColor') }}</label>
          <input id="category-color" v-model="categoryColor" type="color" />
          <label for="category-difficulty">{{ t('tasks.categoryDifficulty') }}</label>
          <input id="category-difficulty" v-model.number="categoryDifficulty" type="number" min="0" max="10" />
          <CategoryIconPicker v-model="categoryIcon" v-model:model-color="categoryColor" v-model:model-ascii="categoryAsciiIcon" />
          <button type="submit" class="task-edit-save" :disabled="!categoryName.trim()"><Plus :size="14" /> {{ t('tasks.add') }}</button>
        </form>
        <div class="category-list">
          <div v-for="item in categories" :key="item.id" class="category-row">
            <template v-if="editingCategoryId === item.id">
              <label :for="`edit-category-name-${item.id}`">{{ t('tasks.categoryName') }}</label>
              <input :id="`edit-category-name-${item.id}`" v-model="editingCategoryName" class="task-edit-input" />
              <label :for="`edit-category-color-${item.id}`">{{ t('tasks.categoryColor') }}</label>
              <input :id="`edit-category-color-${item.id}`" v-model="editingCategoryColor" type="color" />
              <label :for="`edit-category-difficulty-${item.id}`">{{ t('tasks.categoryDifficulty') }}</label>
              <input :id="`edit-category-difficulty-${item.id}`" v-model.number="editingCategoryDifficulty" class="category-difficulty" type="number" min="0" max="10" />
              <CategoryIconPicker v-model="editingCategoryIcon" v-model:model-color="editingCategoryColor" v-model:model-ascii="editingCategoryAsciiIcon" />
              <button type="button" class="task-edit-save" @click="saveCategory(item)">{{ t('tasks.save') }}</button>
              <button type="button" class="task-edit-cancel" @click="cancelCategoryEdit">{{ t('tasks.cancel') }}</button>
            </template>
            <template v-else>
              <span class="category-swatch" :style="{ background: item.color }" />
              <CategoryIconPreview :name="item.icon" :ascii="item.ascii_icon" :style="{ '--category-color': item.color }" />
              <strong>{{ categoryLabel(item) }}</strong>
              <small>{{ t('tasks.categoryDifficulty') }} {{ item.difficulty }}</small>
              <button type="button" class="category-pin" :class="{ active: item.pinned }" :aria-label="item.pinned ? t('tasks.unpinCategory') : t('tasks.pinCategory')" @click="toggleCategoryPinned(item)"><Pin :size="14" /></button>
              <button type="button" class="task-edit" :aria-label="t('tasks.edit')" @click="beginCategoryEdit(item)"><Pencil :size="14" /></button>
              <button v-if="item.id !== 'default'" type="button" class="task-delete" :aria-label="t('tasks.deleteCategory')" @click="removeCategory(item)"><Trash2 :size="14" /></button>
            </template>
          </div>
        </div>
        <div class="task-ranking-settings">
          <span>{{ t('tasks.priorityScore') }}</span>
          <label>{{ t('tasks.scoreRefresh') }}
            <select v-model.number="todoSettings.updateFrequency" :disabled="settingsSaving" @change="saveTodoSettings">
              <option :value="5000">5s</option>
              <option :value="10000">10s</option>
              <option :value="15000">15s</option>
              <option :value="30000">30s</option>
              <option :value="60000">60s</option>
            </select>
          </label>
          <label>{{ t('tasks.categoryExpandCount') }}
            <select v-model.number="todoSettings.expandCount" :disabled="settingsSaving" @change="saveTodoSettings">
              <option :value="3">3</option>
              <option :value="5">5</option>
              <option :value="8">8</option>
              <option :value="10">10</option>
            </select>
          </label>
        </div>
      </section>

      <section v-if="isLoading" class="task-empty theme-card">{{ t('tasks.loading') }}</section>
      <section v-else-if="visibleTodos.length === 0" class="task-empty theme-card">
        <ListTodo :size="34" />
        <strong>{{ filter === 'completed' ? t('tasks.emptyCompleted') : t('tasks.emptyActive') }}</strong>
        <span>{{ t('tasks.emptyHint') }}</span>
      </section>
      <section v-else class="task-list">
        <article v-for="todo in visibleTodos" :id="`todo-${todo.id}`" :key="todo.id" class="task-item theme-card" :class="{ completed: todo.status === 'completed', 'search-target': searchTargetTodoId === todo.id }">
          <input class="task-select-checkbox" type="checkbox" :checked="selectedTodoIds.has(todo.id)" :aria-label="t('tasks.selectTask', { title: todo.title })" :disabled="bulkWorking" @click.stop @change="toggleTodoSelection(todo.id)" />
          <button class="task-check" :disabled="todo.status === 'completed' || completingTodoId === todo.id" :aria-label="todo.status === 'completed' ? t('tasks.completedLabel') : t('tasks.completeLabel')" @click="completeTodo(todo)">
            <Check v-if="todo.status === 'completed'" :size="16" />
          </button>
          <div v-if="editingId === todo.id" class="task-edit-form">
            <label :for="`edit-title-${todo.id}`">{{ t('tasks.editContent') }}</label>
            <input :id="`edit-title-${todo.id}`" v-model="editingTitle" class="task-edit-input" @keyup.enter="saveEdit(todo)" />
            <label :for="`edit-description-${todo.id}`">{{ t('tasks.description') }}</label>
            <textarea :id="`edit-description-${todo.id}`" v-model="editingDescription" class="task-edit-input task-edit-description" :placeholder="t('tasks.descriptionPlaceholder')" rows="2" />
            <label :for="`edit-tags-${todo.id}`">{{ t('tasks.tags') }}</label>
            <input :id="`edit-tags-${todo.id}`" v-model="editingTagsInput" class="task-edit-select" :placeholder="t('tasks.tagsPlaceholder')" />
            <label class="task-edit-check"><input v-model="editingUrgent" type="checkbox" /> {{ t('tasks.urgent') }}</label>
            <label class="task-edit-check"><input v-model="editingImportant" type="checkbox" /> {{ t('tasks.important') }}</label>
            <label :for="`edit-estimated-time-${todo.id}`">{{ t('tasks.estimatedTime') }}</label>
            <input :id="`edit-estimated-time-${todo.id}`" v-model.number="editingEstimatedTime" class="task-edit-select" type="number" min="1" step="1" />
            <label :for="`edit-category-${todo.id}`">{{ t('tasks.category') }}</label>
            <select :id="`edit-category-${todo.id}`" v-model="editingCategory" class="task-edit-select">
              <option v-for="item in categories" :key="item.id" :value="item.id">{{ categoryLabel(item) }}</option>
            </select>
            <label :for="`edit-deadline-${todo.id}`">{{ t('tasks.deadline') }}</label>
            <input :id="`edit-deadline-${todo.id}`" v-model="editingDeadline" class="task-edit-select" type="date" />
            <label :for="`edit-recurrence-${todo.id}`">{{ t('tasks.recurrence') }}</label>
            <select :id="`edit-recurrence-${todo.id}`" v-model="editingRecurrence" class="task-edit-select">
              <option v-for="(label, value) in recurrenceLabels" :key="value" :value="value">{{ label }}</option>
            </select>
            <label :for="`edit-plan-${todo.id}`">{{ t('tasks.plan') }}</label>
            <select :id="`edit-plan-${todo.id}`" v-model="editingPlanId" class="task-edit-select" :disabled="planGatewayState !== 'ready'" @change="editingPlanTaskId = ''; loadPlanTasks(editingPlanId)">
              <option value="">{{ t('tasks.noPlan') }}</option>
              <option v-for="plan in planSummaries" :key="plan.id" :value="plan.id">{{ plan.name }}</option>
            </select>
            <label :for="`edit-plan-task-${todo.id}`">{{ t('tasks.planTask') }}</label>
            <select :id="`edit-plan-task-${todo.id}`" v-model="editingPlanTaskId" class="task-edit-select" :disabled="!editingPlanId || planTaskState !== 'ready'">
              <option value="">{{ t('tasks.noTask') }}</option>
              <option v-for="task in planTasks" :key="task.internal_id" :value="task.internal_id">{{ task.display_id }} · {{ task.content }}</option>
            </select>
            <div class="task-edit-actions">
              <button class="task-edit-cancel" @click="cancelEdit">{{ t('tasks.cancel') }}</button>
              <button class="task-edit-save" :disabled="isSaving || !editingTitle.trim()" @click="saveEdit(todo)">{{ isSaving ? t('tasks.saving') : t('tasks.save') }}</button>
            </div>
          </div>
          <div v-else class="task-main">
            <div class="task-title-row">
              <h2>{{ todo.title }}</h2>
            </div>
            <p v-if="todo.description">{{ todo.description }}</p>
            <span v-if="todo.category" class="task-category" :style="{ '--category-color': categories.find((item) => item.id === todo.category)?.color || '#64748b' }">
              <CategoryIconPreview :name="categories.find((item) => item.id === todo.category)?.icon" :ascii="categories.find((item) => item.id === todo.category)?.ascii_icon" />
              <span>{{ todoCategoryLabel(todo.category) }}</span>
            </span>
            <span v-for="tag in todo.tags" :key="tag" class="task-tag">#{{ tag }}</span>
            <span v-if="todo.time_spent" class="task-time-spent">{{ t('tasks.timeSpent') }} {{ todo.time_spent }} {{ t('tasks.minutesShort') }}</span>
            <button v-if="todo.related_time_record_ids?.length" type="button" class="task-record-link" @click="openTodoRecords(todo)">
              {{ t('tasks.viewTimeRecords') }} ({{ todo.related_time_record_ids.length }})
            </button>
            <span v-if="todo.deadline" class="task-deadline" :class="getDeadlineState(todo.deadline)">{{ deadlineStateLabel(todo.deadline) }} · {{ formatDeadline(todo.deadline) }}</span>
            <span v-if="todo.recurrence && todo.recurrence !== 'none'" class="task-recurrence">{{ t('tasks.recurrence') }}：{{ recurrenceLabels[todo.recurrence] }}</span>
            <button v-if="todo.related_plan_id" type="button" class="task-plan-reference task-plan-link" @click="openTodoPlan(todo)">{{ t('tasks.planReference') }}: {{ planNameById[todo.related_plan_id] || `#${todo.related_plan_id}` }}<small v-if="archivedPlanById[todo.related_plan_id]"> · {{ t('tasks.archivedPlan') }}</small></button>
            <button v-if="todo.related_plan_task_id" type="button" class="task-plan-reference task-plan-link" @click="openTodoPlan(todo)">{{ t('tasks.taskReference') }}: {{ planTaskById[todo.related_plan_task_id]?.display_id || `#${todo.related_plan_task_id}` }}<small v-if="todo.related_plan_id && archivedPlanById[todo.related_plan_id]"> · {{ t('tasks.archivedPlan') }}</small></button>
          </div>
          <div v-if="editingId !== todo.id" class="task-item-actions">
            <div class="task-rank-control" :title="t('tasks.priorityRank')">
              <button type="button" :aria-label="t('tasks.increaseRank')" @click="adjustTodoRank(todo, 1)"><ChevronUp :size="13" /></button>
              <span>{{ todo.priority_rank ?? 0 }}</span>
              <button type="button" :aria-label="t('tasks.decreaseRank')" :disabled="!todo.priority_rank" @click="adjustTodoRank(todo, -1)"><ChevronDown :size="13" /></button>
            </div>
            <span class="task-score" :class="{ expired: scoreFor(todo).expired }" :title="t('tasks.priorityScore')">{{ scoreFor(todo).display }}</span>
            <button class="task-details-toggle" :class="{ expanded: expandedTodoId === todo.id }" :aria-label="t('tasks.details')" @click="toggleTodoDetails(todo)">
              <span>{{ t('tasks.subtasks') }} <small v-if="todo.subtasks.length">{{ subtaskProgress(todo) }}</small></span><ChevronDown :size="16" />
            </button>
            <button class="task-pin" :class="{ active: todo.pinned }" :aria-label="todo.pinned ? t('tasks.unpinTodo') : t('tasks.pinTodo')" @click="toggleTodoPinned(todo)"><Pin :size="16" /></button>
            <button class="task-edit" :aria-label="t('tasks.edit')" @click="startEdit(todo)"><Pencil :size="16" /></button>
            <button class="task-delete" :aria-label="t('tasks.delete')" @click="removeTodo(todo)"><Trash2 :size="16" /></button>
          </div>
          <div v-if="expandedTodoId === todo.id && editingId !== todo.id" class="task-subtasks">
            <div class="task-score-detail"><span>{{ t('tasks.priorityScore') }}</span><strong>{{ scoreFor(todo).score }}</strong></div>
            <div v-if="todo.subtasks.length" class="subtask-list">
              <div v-for="subtask in todo.subtasks" :key="subtask.id" class="subtask-row" :class="{ completed: subtask.completed }">
                <input type="checkbox" :aria-label="subtask.title" :checked="subtask.completed" :disabled="subtaskSaving" @change="toggleSubtask(todo, subtask.id)" />
                <span>{{ subtask.title }}</span>
                <button type="button" class="subtask-delete" :disabled="subtaskSaving" :aria-label="t('tasks.deleteSubtask')" @click.prevent="removeSubtask(todo, subtask.id)"><Trash2 :size="14" /></button>
              </div>
            </div>
            <p v-else class="subtask-empty">{{ t('tasks.noSubtasks') }}</p>
            <form class="time-track-form" @submit.prevent="trackTodoTime(todo)">
              <label :for="`track-time-${todo.id}`">{{ t('tasks.trackTime') }}</label>
              <input :id="`track-time-${todo.id}`" v-model.number="trackedMinutes" type="number" min="1" max="1440" step="1" />
              <span>{{ t('tasks.minutesShort') }}</span>
              <button type="submit" :disabled="trackingTodoId === todo.id">{{ trackingTodoId === todo.id ? t('tasks.saving') : t('tasks.recordTime') }}</button>
            </form>
            <div class="focus-track-form">
              <button type="button" :disabled="Boolean(focusTodoId && focusTodoId !== todo.id) || trackingTodoId === todo.id" @click="focusTodoId === todo.id ? stopFocus(todo) : startFocus(todo)">
                {{ focusTodoId === todo.id ? t('tasks.stopFocus') : t('tasks.startFocus') }}
              </button>
              <span v-if="focusTodoId === todo.id" class="focus-elapsed">{{ focusElapsedLabel }}</span>
              <span v-else class="focus-hint">{{ t('tasks.focusHint') }}</span>
            </div>
            <form class="subtask-add-form" @submit.prevent="addSubtask(todo)">
              <input v-model="subtaskTitle" :placeholder="t('tasks.subtaskPlaceholder')" :disabled="subtaskSaving" />
              <button type="submit" :disabled="subtaskSaving || !subtaskTitle.trim()"><Plus :size="14" /> {{ t('tasks.addSubtask') }}</button>
            </form>
          </div>
        </article>
      </section>
    </main>
  </div>
</template>

<style scoped>
.task-center { min-height: 100vh; color: var(--color-text-primary); background: var(--color-bg); }
.task-header { display: flex; flex-wrap: wrap; align-items: center; gap: 16px; max-width: 980px; margin: 0 auto; padding: 32px 28px 20px; }
.task-title-block { flex: 1 1 220px; min-width: 0; }
.task-back { display: grid; place-items: center; width: 36px; height: 36px; border: 1px solid var(--color-border); border-radius: 12px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; }
.task-eyebrow { margin: 0 0 3px; color: var(--color-text-tertiary); font-size: 12px; letter-spacing: .08em; }
.task-module-description { margin: 5px 0 0; color: var(--color-text-secondary); font-size: 12px; line-height: 1.5; }
.task-header h1 { display: flex; align-items: center; gap: 9px; margin: 0; font-size: 25px; }
.task-counts { display: flex; flex-wrap: wrap; gap: 8px; margin-left: auto; color: var(--color-text-secondary); font-size: 13px; }
.task-counts span { padding: 7px 10px; border: 1px solid var(--color-border); border-radius: 999px; background: var(--color-bg-secondary); }
.task-content { max-width: 980px; margin: 0 auto; padding: 8px 28px 48px; }
.task-create { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; padding: 13px; border: 1px solid var(--color-border); border-radius: 16px; }
.task-create-advanced { flex: 1 1 100%; min-width: 0; order: 3; border-top: 1px solid var(--color-border); }
.task-create-advanced summary { padding: 10px 0 2px; color: var(--color-text-secondary); cursor: pointer; font-size: 12px; user-select: none; }
.task-create-advanced[open] { display: grid; grid-template-columns: minmax(86px, auto) minmax(150px, 1fr) minmax(86px, auto) minmax(150px, 1fr); align-items: center; gap: 9px 10px; padding-top: 2px; }
.task-create-advanced[open] summary { grid-column: 1 / -1; }
.task-create-advanced[open] .task-description-label { align-self: start; padding-top: 8px; }
.task-create-advanced[open] .task-description-input { min-width: 0; }
.task-field-label { color: var(--color-text-tertiary); font-size: 12px; white-space: nowrap; }
.task-input { min-width: 0; flex: 1; border: 0; outline: 0; color: var(--color-text-primary); background: transparent; font-size: 15px; }
.task-description-label { align-self: flex-start; padding-top: 8px; }
.task-description-input { min-width: 180px; flex: 1 1 100%; resize: vertical; border: 1px solid var(--color-border); border-radius: 9px; padding: 7px 9px; outline: 0; color: var(--color-text-primary); background: var(--color-bg-secondary); font: inherit; font-size: 12px; }
.task-tags-input { min-width: 150px; flex: 1 1 100%; border: 1px solid var(--color-border); border-radius: 9px; padding: 7px 9px; outline: 0; color: var(--color-text-primary); background: var(--color-bg-secondary); font: inherit; font-size: 12px; }
.task-select { border: 1px solid var(--color-border); border-radius: 10px; padding: 0 10px; color: var(--color-text-secondary); background: var(--color-bg-secondary); }
.task-date-input { width: 132px; border: 1px solid var(--color-border); border-radius: 10px; padding: 7px 8px; color: var(--color-text-secondary); background: var(--color-bg-secondary); }
.task-number-input { width: 62px; border: 1px solid var(--color-border); border-radius: 10px; padding: 7px 8px; color: var(--color-text-secondary); background: var(--color-bg-secondary); }
.focus-track-form { display: flex; align-items: center; gap: 8px; margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--color-border); }
.focus-track-form button { border: 1px solid var(--color-primary); border-radius: 8px; padding: 6px 10px; color: var(--color-button-text); background: var(--color-primary); cursor: pointer; font-size: 12px; }
.focus-track-form button:disabled { opacity: .55; cursor: not-allowed; }
.focus-elapsed { color: var(--color-primary); font-family: var(--font-mono, monospace); font-size: 13px; font-variant-numeric: tabular-nums; }
.focus-hint { color: var(--color-text-tertiary); font-size: 11px; }
.task-estimate-input { width: 70px; }
.task-check-label { display: inline-flex; align-items: center; gap: 4px; color: var(--color-text-secondary); font-size: 12px; white-space: nowrap; }
.task-add { display: inline-flex; align-items: center; gap: 6px; margin-left: auto; border: 0; border-radius: 10px; padding: 8px 15px; color: var(--color-button-text); background: var(--color-primary); cursor: pointer; font-weight: 600; }
.task-toolbar { display: flex; align-items: center; justify-content: space-between; padding: 24px 2px 12px; }
.task-tabs { display: flex; gap: 4px; padding: 4px; border-radius: 10px; background: var(--color-bg-secondary); }
.task-tabs button { border: 0; border-radius: 7px; padding: 7px 13px; color: var(--color-text-secondary); background: transparent; cursor: pointer; }
.task-tabs button.active { color: var(--color-text-primary); background: var(--color-bg-elevated); box-shadow: var(--shadow-sm, 0 1px 3px rgba(0,0,0,.08)); }
.task-filter-select { min-width: 120px; border: 1px solid var(--color-border); border-radius: 9px; padding: 7px 10px; color: var(--color-text-secondary); background: var(--color-bg-secondary); }
.task-category-manage { display: inline-flex; align-items: center; gap: 5px; border: 1px solid var(--color-border); border-radius: 9px; padding: 7px 10px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; white-space: nowrap; }
.task-select-all { display: inline-flex; align-items: center; gap: 5px; color: var(--color-text-secondary); font-size: 11px; white-space: nowrap; }
.task-bulk-actions { display: inline-flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-left: auto; color: var(--color-text-tertiary); font-size: 11px; }
.task-bulk-actions button { display: inline-flex; align-items: center; gap: 4px; border: 1px solid var(--color-primary); border-radius: 8px; padding: 6px 8px; color: var(--color-button-text); background: var(--color-primary); cursor: pointer; font: inherit; }
.task-bulk-actions button.danger { border-color: var(--color-error); background: var(--color-error); }
.task-bulk-actions button.task-bulk-clear { border-color: var(--color-border); color: var(--color-text-secondary); background: var(--color-bg-secondary); }
.task-bulk-actions button:disabled { cursor: not-allowed; opacity: .55; }
.task-error { color: var(--color-error); font-size: 13px; }
.task-plan-status { color: var(--color-text-tertiary); font-size: 12px; }
.task-plan-status-action { display: inline-flex; align-items: center; flex-wrap: wrap; gap: 7px; }
.task-plan-retry { border: 1px solid var(--color-border); border-radius: 7px; padding: 4px 7px; color: var(--color-primary); background: var(--color-bg-secondary); cursor: pointer; font-size: 11px; }
.task-plan-retry:disabled { cursor: not-allowed; opacity: .55; }
.task-category-nav { display: grid; gap: 10px; margin-bottom: 18px; border: 1px solid var(--color-border); border-radius: 14px; padding: 13px 14px; }
.task-category-nav-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.task-category-nav-header > div { display: grid; gap: 3px; }
.task-category-nav-header strong { color: var(--color-text-primary); font-size: 13px; }
.task-category-nav-header small { color: var(--color-text-tertiary); font-size: 11px; }
.task-category-nav-list { display: flex; flex-wrap: wrap; gap: 7px; }
.task-category-chip { display: inline-flex; align-items: center; gap: 5px; border: 1px solid var(--color-border); border-left: 3px solid var(--category-color, var(--color-border)); border-radius: 9px; padding: 5px 8px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; font-size: 11px; }
.task-category-chip:hover, .task-category-chip.active { border-color: var(--category-color, var(--color-primary)); color: var(--color-text-primary); background: var(--color-primary-muted); }
.task-category-chip small { color: var(--color-text-tertiary); font-size: 10px; }
.task-category-chip-more, .task-empty-category-toggle button { border-style: dashed; color: var(--color-primary); }
.task-empty-category-toggle button { border: 0; padding: 0; background: transparent; cursor: pointer; font-size: 11px; }
.task-empty-category-list { padding-top: 2px; border-top: 1px dashed var(--color-border); }
.task-ranking-settings { display: flex; flex-wrap: wrap; gap: 12px; padding-top: 4px; border-top: 1px solid var(--color-border); color: var(--color-text-tertiary); font-size: 11px; }
.task-ranking-settings label { display: inline-flex; align-items: center; gap: 6px; }
.task-ranking-settings select { border: 1px solid var(--color-border); border-radius: 7px; padding: 4px 7px; color: var(--color-text-secondary); background: var(--color-bg-secondary); font-size: 11px; }
.task-list { display: grid; gap: 10px; }
.task-item { display: flex; flex-wrap: wrap; align-items: flex-start; gap: 13px; padding: 16px; border: 1px solid var(--color-border); border-radius: 14px; transition: border-color .2s, transform .2s; }
.task-select-checkbox { width: 16px; height: 16px; flex: 0 0 16px; accent-color: var(--color-primary); }
.task-item:hover { border-color: var(--color-border-hover); transform: translateY(-1px); }
.task-item.search-target { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-muted); }
.task-item.completed { opacity: .68; }
.task-check { display: grid; place-items: center; width: 23px; height: 23px; flex: 0 0 23px; border: 2px solid var(--color-border-hover); border-radius: 50%; color: var(--color-button-text); background: var(--color-primary); cursor: pointer; }
.task-check:disabled { cursor: default; opacity: .85; }
.task-main { min-width: 0; flex: 1; text-align: left; }
.task-title-row { display: flex; align-items: center; gap: 9px; }
.task-title-row h2 { overflow: hidden; margin: 0; font-size: 15px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.completed .task-title-row h2 { text-decoration: line-through; }
.task-rank-control { display: inline-flex; align-items: center; gap: 2px; min-width: 42px; color: var(--color-text-tertiary); font-size: 11px; font-variant-numeric: tabular-nums; }
.task-rank-control button { display: grid; place-items: center; width: 18px; height: 18px; border: 0; border-radius: 5px; color: var(--color-text-tertiary); background: transparent; cursor: pointer; }
.task-rank-control button:hover:not(:disabled), .task-rank-control button:focus-visible { color: var(--color-primary); background: var(--color-primary-muted); outline: 0; }
.task-rank-control button:disabled { opacity: .35; cursor: not-allowed; }
.task-rank-control span { min-width: 12px; text-align: center; }
.task-score { min-width: 42px; padding: 3px 7px; border-radius: 6px; color: var(--color-primary); background: var(--color-primary-muted); font-size: 11px; font-variant-numeric: tabular-nums; text-align: right; white-space: nowrap; }
.task-score.expired { color: var(--color-text-tertiary); background: var(--color-bg-secondary); }
.task-item-actions { display: flex; align-items: center; justify-content: flex-end; gap: 8px; margin-left: auto; flex: 0 0 auto; align-self: flex-start; }
.task-main p { margin: 5px 0 0; color: var(--color-text-secondary); font-size: 13px; }
.task-category { display: inline-flex; align-items: center; gap: 5px; margin-top: 7px; border-left: 3px solid var(--category-color); padding: 2px 7px; color: var(--color-text-secondary); background: var(--color-bg-secondary); font-size: 11px; }
.task-tag { display: inline-block; margin: 7px 0 0 6px; border-radius: 999px; padding: 2px 7px; color: var(--color-primary); background: var(--color-primary-muted); font-size: 11px; }
.task-time-spent { display: inline-block; margin: 7px 0 0 10px; color: var(--color-primary); font-size: 12px; }
.task-record-link { display: inline-block; margin: 7px 0 0 10px; border: 0; padding: 0; color: var(--color-primary); background: transparent; cursor: pointer; font-size: 12px; text-decoration: underline; text-underline-offset: 2px; }
.task-deadline { display: inline-block; margin-top: 7px; color: var(--color-text-tertiary); font-size: 12px; }
.task-deadline.overdue { color: var(--color-error); font-weight: 600; }
.task-deadline.today { color: var(--color-primary); font-weight: 600; }
.task-deadline.upcoming { color: var(--color-text-secondary); }
.task-recurrence { display: inline-block; margin: 7px 0 0 10px; color: var(--color-primary); font-size: 12px; }
.task-plan-reference { display: inline-block; margin: 7px 0 0 10px; color: var(--color-primary); font-size: 12px; }
.task-plan-link { border: 0; padding: 0; background: transparent; cursor: pointer; text-decoration: underline; text-underline-offset: 2px; }
.task-edit, .task-delete { display: grid; place-items: center; border: 0; color: var(--color-text-tertiary); background: transparent; cursor: pointer; }
.task-pin { display: grid; place-items: center; border: 0; color: var(--color-text-tertiary); background: transparent; cursor: pointer; }
.task-pin.active, .task-pin:hover { color: var(--color-primary); }
.task-details-toggle { display: inline-flex; align-items: center; gap: 4px; border: 0; color: var(--color-text-tertiary); background: transparent; cursor: pointer; font-size: 12px; }
.task-details-toggle svg { transition: transform .2s; }
.task-details-toggle.expanded svg { transform: rotate(180deg); }
.task-details-toggle small { color: var(--color-primary); }
.task-edit:hover { color: var(--color-primary); }
.task-delete:hover { color: var(--color-error); }
.task-edit-form { display: grid; grid-template-columns: auto minmax(160px, 1fr) auto minmax(100px, 140px) auto; align-items: center; gap: 8px; min-width: 0; flex: 1; }
.task-edit-form label { color: var(--color-text-tertiary); font-size: 12px; white-space: nowrap; }
.task-edit-input, .task-edit-select { min-width: 0; border: 1px solid var(--color-border); border-radius: 8px; padding: 7px 9px; color: var(--color-text-primary); background: var(--color-bg-secondary); outline: none; }
.task-edit-description { min-height: 42px; resize: vertical; font: inherit; }
.task-edit-check { display: inline-flex; align-items: center; gap: 4px; color: var(--color-text-secondary); font-size: 12px; white-space: nowrap; }
.task-edit-input:focus, .task-edit-select:focus, .task-input:focus, .task-select:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-muted); }
.task-edit-actions { display: flex; gap: 6px; }
.task-edit-cancel, .task-edit-save { border: 1px solid var(--color-border); border-radius: 8px; padding: 7px 10px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; white-space: nowrap; }
.task-edit-save { border-color: var(--color-primary); color: var(--color-button-text); background: var(--color-primary); }
.task-edit-save:disabled { cursor: wait; opacity: .6; }
.task-subtasks { flex-basis: 100%; margin: 3px 0 0 36px; padding-top: 12px; border-top: 1px solid var(--color-border); }
.task-score-detail { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; color: var(--color-text-tertiary); font-size: 12px; }
.task-score-detail strong { color: var(--color-primary); font-variant-numeric: tabular-nums; }
.subtask-list { display: grid; gap: 7px; }
.subtask-row { display: flex; align-items: center; gap: 8px; color: var(--color-text-secondary); font-size: 13px; }
.subtask-row input { accent-color: var(--color-primary); }
.subtask-row.completed span { color: var(--color-text-tertiary); text-decoration: line-through; }
.subtask-delete { display: grid; place-items: center; margin-left: auto; border: 0; color: var(--color-text-tertiary); background: transparent; cursor: pointer; }
.subtask-delete:hover { color: var(--color-error); }
.subtask-empty { margin: 0 0 10px; color: var(--color-text-tertiary); font-size: 12px; }
.time-track-form { display: flex; align-items: center; gap: 7px; margin: 10px 0; color: var(--color-text-tertiary); font-size: 12px; }
.time-track-form input { width: 66px; border: 1px solid var(--color-border); border-radius: 8px; padding: 6px; color: var(--color-text-primary); background: var(--color-bg-secondary); }
.time-track-form button { border: 1px solid var(--color-primary); border-radius: 8px; padding: 6px 9px; color: var(--color-button-text); background: var(--color-primary); cursor: pointer; }
.time-track-form button:disabled { cursor: wait; opacity: .6; }
.subtask-add-form { display: flex; gap: 7px; margin-top: 10px; }
.subtask-add-form input { min-width: 0; flex: 1; border: 1px solid var(--color-border); border-radius: 8px; padding: 7px 9px; color: var(--color-text-primary); background: var(--color-bg-secondary); outline: none; }
.subtask-add-form button { display: inline-flex; align-items: center; gap: 4px; border: 1px solid var(--color-border); border-radius: 8px; padding: 7px 9px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; white-space: nowrap; }
.subtask-add-form button:disabled { cursor: wait; opacity: .6; }
.task-empty { display: grid; place-items: center; gap: 9px; min-height: 220px; border: 1px dashed var(--color-border); border-radius: 16px; color: var(--color-text-tertiary); text-align: center; }
.task-empty strong { color: var(--color-text-secondary); }
.category-manager { display: grid; gap: 14px; margin-bottom: 18px; border: 1px solid var(--color-border); border-radius: 14px; padding: 16px; }
.category-manager-header { display: flex; align-items: start; justify-content: space-between; gap: 12px; }
.category-manager-header h2 { margin: 0; font-size: 15px; }
.category-manager-header p { margin: 4px 0 0; color: var(--color-text-tertiary); font-size: 12px; }
.category-create { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.category-create input:not([type='color']), .category-create label input { width: 90px; border: 1px solid var(--color-border); border-radius: 8px; padding: 7px 8px; color: var(--color-text-primary); background: var(--color-bg-secondary); }
.category-create input:first-child { min-width: 180px; flex: 1; }
.category-create .category-icon-picker, .category-row .category-icon-picker { flex: 1 1 100%; min-width: 260px; }
.category-create input[type='color'], .category-row input[type='color'] { width: 32px; height: 32px; border: 0; padding: 0; background: transparent; cursor: pointer; }
.category-list { display: grid; gap: 7px; }
.category-row { display: flex; align-items: center; gap: 9px; min-height: 34px; border-top: 1px solid var(--color-border); padding-top: 7px; }
.category-row strong { min-width: 110px; color: var(--color-text-primary); font-size: 13px; }
.category-row small { margin-right: auto; color: var(--color-text-tertiary); font-size: 11px; }
.category-pin { display: grid; place-items: center; border: 0; color: var(--color-text-tertiary); background: transparent; cursor: pointer; }
.category-pin.active, .category-pin:hover { color: var(--color-primary); }
.category-swatch { width: 10px; height: 10px; border-radius: 50%; }
.category-difficulty { width: 55px; border: 1px solid var(--color-border); border-radius: 7px; padding: 6px; color: var(--color-text-primary); background: var(--color-bg-secondary); }
@media (min-width: 1100px) {
  .task-header, .task-content { max-width: 1180px; }
}
@media (prefers-reduced-motion: reduce) { .task-item { transition: none; } }
@media (max-width: 700px) { .task-header { padding: 24px 18px 16px; } .task-content { padding: 8px 18px 36px; } .task-counts { display: none; } .task-create { flex-wrap: wrap; } .task-create-advanced[open] { grid-template-columns: 1fr; } .task-create-advanced[open] .task-description-label { padding-top: 0; } .task-input { flex-basis: 100%; height: 38px; } .task-select, .task-add { height: 38px; } .task-edit-form { grid-template-columns: 1fr; } .task-edit-form label { margin-top: 2px; } .task-edit-actions { justify-content: flex-end; } .task-item-actions { flex-basis: 100%; justify-content: flex-end; margin-left: 36px; } }
</style>
