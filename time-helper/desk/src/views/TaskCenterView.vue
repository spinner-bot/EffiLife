<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Check, ListTodo, Pencil, Plus, Trash2 } from 'lucide-vue-next'
import { AudioManager } from '@/audio'
import { TodoService, type TodoPriority, type UnifiedTodo } from '@/services/todoService'
import { getPlanTasks, listPlanSummaries, type PlanGatewayState, type PlanSummary, type PlanTaskSummary } from '@/services/planGateway'
import { useI18n } from '@/i18n'

const router = useRouter()
const { t, locale } = useI18n()
const todos = ref<UnifiedTodo[]>([])
const title = ref('')
const priority = ref<TodoPriority>('normal')
const selectedPlanId = ref('')
const selectedPlanTaskId = ref('')
const filter = ref<'all' | 'active' | 'completed'>('active')
const isLoading = ref(true)
const errorMessage = ref('')
const editingId = ref<string | null>(null)
const editingTitle = ref('')
const editingPriority = ref<TodoPriority>('normal')
const editingPlanId = ref('')
const editingPlanTaskId = ref('')
const isSaving = ref(false)
const planSummaries = ref<PlanSummary[]>([])
const planGatewayState = ref<PlanGatewayState>('idle')
const planTasks = ref<PlanTaskSummary[]>([])
const planTaskState = ref<PlanGatewayState>('idle')

const activeTodos = computed(() => todos.value.filter((todo) => !['completed', 'archived', 'cancelled'].includes(todo.status)))
const completedTodos = computed(() => todos.value.filter((todo) => todo.status === 'completed'))
const visibleTodos = computed(() => {
  if (filter.value === 'active') return activeTodos.value
  if (filter.value === 'completed') return completedTodos.value
  return todos.value
})

const priorityLabels = computed<Record<TodoPriority, string>>(() => ({
  'urgent-important': t('priority.urgentImportant'),
  important: t('priority.important'),
  urgent: t('priority.urgent'),
  normal: t('priority.normal'),
}))

const planNameById = computed(() => Object.fromEntries(planSummaries.value.map((plan) => [plan.id, plan.name])))
const planTaskById = computed(() => Object.fromEntries(planTasks.value.map((task) => [task.internal_id, task])))

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
  if (!title.value.trim()) return
  try {
    const todo = await TodoService.create({
      title: title.value,
      priority: priority.value,
      related_plan_id: selectedPlanId.value || undefined,
      related_plan_task_id: selectedPlanId.value ? selectedPlanTaskId.value || undefined : undefined,
    })
    todos.value = [todo, ...todos.value]
    title.value = ''
    priority.value = 'normal'
    selectedPlanId.value = ''
    selectedPlanTaskId.value = ''
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.create')
  }
}

async function loadPlanSummaries() {
  planGatewayState.value = 'loading'
  try {
    planSummaries.value = await listPlanSummaries()
    planGatewayState.value = 'ready'
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
    planTaskState.value = 'ready'
  } catch {
    planTasks.value = []
    planTaskState.value = 'unavailable'
  }
}

async function completeTodo(todo: UnifiedTodo) {
  if (todo.status === 'completed') return
  try {
    const updated = await TodoService.complete(todo.id)
    const index = todos.value.findIndex((item) => item.id === todo.id)
    if (index >= 0) todos.value[index] = updated
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.update')
  }
}

function startEdit(todo: UnifiedTodo) {
  editingId.value = todo.id
  editingTitle.value = todo.title
  editingPriority.value = todo.priority
  editingPlanId.value = todo.related_plan_id || ''
  editingPlanTaskId.value = todo.related_plan_task_id || ''
  loadPlanTasks(editingPlanId.value)
  errorMessage.value = ''
}

function cancelEdit() {
  editingId.value = null
  editingTitle.value = ''
  editingPriority.value = 'normal'
  editingPlanId.value = ''
  editingPlanTaskId.value = ''
  loadPlanTasks(selectedPlanId.value)
}

async function saveEdit(todo: UnifiedTodo) {
  if (!editingTitle.value.trim() || isSaving.value) return
  isSaving.value = true
  try {
    const updated = await TodoService.update(todo.id, {
      title: editingTitle.value,
      priority: editingPriority.value,
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
  try {
    await TodoService.remove(todo.id)
    todos.value = todos.value.filter((item) => item.id !== todo.id)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t('tasks.error.delete')
  }
}

function formatDeadline(deadline?: string): string {
  if (!deadline) return ''
  const date = new Date(deadline)
  return Number.isNaN(date.getTime()) ? deadline : date.toLocaleDateString(locale.value)
}

onMounted(() => {
  loadTodos()
  loadPlanSummaries()
})

watch(selectedPlanId, (planId) => {
  selectedPlanTaskId.value = ''
  loadPlanTasks(planId)
})
</script>

<template>
  <div class="task-center">
    <header class="task-header">
      <button class="task-back" @click="AudioManager.playSound('click'); router.push('/')" aria-label="返回首页">
        <ArrowLeft :size="18" />
      </button>
      <div>
        <p class="task-eyebrow">{{ t('tasks.workspace') }}</p>
        <h1><ListTodo :size="24" /> {{ t('tasks.title') }}</h1>
      </div>
      <div class="task-counts">
        <span>{{ activeTodos.length }} {{ t('tasks.pending') }}</span>
        <span>{{ completedTodos.length }} {{ t('tasks.completed') }}</span>
      </div>
    </header>

    <main class="task-content">
      <section class="task-create theme-card">
        <label class="task-field-label" for="new-task-title">{{ t('tasks.new') }}</label>
        <input id="new-task-title" v-model="title" class="task-input" :placeholder="t('tasks.addPlaceholder')" @keyup.enter="addTodo" />
        <label class="task-field-label" for="new-task-priority">{{ t('tasks.priority') }}</label>
        <select id="new-task-priority" v-model="priority" class="task-select">
          <option v-for="(label, value) in priorityLabels" :key="value" :value="value">{{ label }}</option>
        </select>
        <label class="task-field-label" for="new-task-plan">{{ t('tasks.plan') }}</label>
        <select id="new-task-plan" v-model="selectedPlanId" class="task-select task-plan-select" :disabled="planGatewayState === 'loading'">
          <option value="">{{ t('tasks.noPlan') }}</option>
          <option v-for="plan in planSummaries" :key="plan.id" :value="plan.id">{{ plan.name }}</option>
        </select>
        <label class="task-field-label" for="new-task-plan-task">{{ t('tasks.planTask') }}</label>
        <select id="new-task-plan-task" v-model="selectedPlanTaskId" class="task-select task-plan-select" :disabled="!selectedPlanId || planTaskState === 'loading'">
          <option value="">{{ t('tasks.noTask') }}</option>
          <option v-for="task in planTasks" :key="task.internal_id" :value="task.internal_id">{{ task.display_id }} · {{ task.content }}</option>
        </select>
        <button class="task-add" @click="AudioManager.playSound('click'); addTodo()">
          <Plus :size="17" /> {{ t('tasks.add') }}
        </button>
      </section>

      <section class="task-toolbar">
        <div class="task-tabs" role="tablist" :aria-label="t('tasks.title')">
          <button :class="{ active: filter === 'active' }" @click="filter = 'active'">{{ t('tasks.active') }}</button>
          <button :class="{ active: filter === 'all' }" @click="filter = 'all'">{{ t('tasks.all') }}</button>
          <button :class="{ active: filter === 'completed' }" @click="filter = 'completed'">{{ t('tasks.completedTab') }}</button>
        </div>
        <span v-if="errorMessage" class="task-error">{{ errorMessage }}</span>
        <span v-else-if="planGatewayState === 'unavailable'" class="task-plan-status">{{ t('tasks.serviceUnavailable') }}</span>
      </section>

      <section v-if="isLoading" class="task-empty theme-card">{{ t('tasks.loading') }}</section>
      <section v-else-if="visibleTodos.length === 0" class="task-empty theme-card">
        <ListTodo :size="34" />
        <strong>{{ filter === 'completed' ? t('tasks.emptyCompleted') : t('tasks.emptyActive') }}</strong>
        <span>{{ t('tasks.emptyHint') }}</span>
      </section>
      <section v-else class="task-list">
        <article v-for="todo in visibleTodos" :key="todo.id" class="task-item theme-card" :class="{ completed: todo.status === 'completed' }">
          <button class="task-check" :disabled="todo.status === 'completed'" :aria-label="todo.status === 'completed' ? '已完成' : '完成任务'" @click="completeTodo(todo)">
            <Check v-if="todo.status === 'completed'" :size="16" />
          </button>
          <div v-if="editingId === todo.id" class="task-edit-form">
            <label :for="`edit-title-${todo.id}`">{{ t('tasks.editContent') }}</label>
            <input :id="`edit-title-${todo.id}`" v-model="editingTitle" class="task-edit-input" @keyup.enter="saveEdit(todo)" />
            <label :for="`edit-priority-${todo.id}`">{{ t('tasks.priority') }}</label>
            <select :id="`edit-priority-${todo.id}`" v-model="editingPriority" class="task-edit-select">
              <option v-for="(label, value) in priorityLabels" :key="value" :value="value">{{ label }}</option>
            </select>
            <label :for="`edit-plan-${todo.id}`">{{ t('tasks.plan') }}</label>
            <select :id="`edit-plan-${todo.id}`" v-model="editingPlanId" class="task-edit-select" :disabled="planGatewayState === 'loading'" @change="editingPlanTaskId = ''; loadPlanTasks(editingPlanId)">
              <option value="">{{ t('tasks.noPlan') }}</option>
              <option v-for="plan in planSummaries" :key="plan.id" :value="plan.id">{{ plan.name }}</option>
            </select>
            <label :for="`edit-plan-task-${todo.id}`">{{ t('tasks.planTask') }}</label>
            <select :id="`edit-plan-task-${todo.id}`" v-model="editingPlanTaskId" class="task-edit-select" :disabled="!editingPlanId || planTaskState === 'loading'">
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
            <span v-if="todo.deadline" class="task-deadline">截止 {{ formatDeadline(todo.deadline) }}</span>
            <span v-if="todo.related_plan_id" class="task-plan-reference">计划：{{ planNameById[todo.related_plan_id] || `#${todo.related_plan_id}` }}</span>
            <span v-if="todo.related_plan_task_id" class="task-plan-reference">任务：{{ planTaskById[todo.related_plan_task_id]?.display_id || `#${todo.related_plan_task_id}` }}</span>
          </div>
          <span v-if="editingId !== todo.id" class="task-priority">{{ priorityLabels[todo.priority] }}</span>
          <button v-if="editingId !== todo.id" class="task-edit" :aria-label="t('tasks.edit')" @click="startEdit(todo)"><Pencil :size="16" /></button>
          <button class="task-delete" aria-label="删除任务" @click="removeTodo(todo)"><Trash2 :size="16" /></button>
        </article>
      </section>
    </main>
  </div>
</template>

<style scoped>
.task-center { min-height: 100vh; color: var(--color-text-primary); background: var(--color-bg); }
.task-header { display: flex; align-items: center; gap: 16px; max-width: 980px; margin: 0 auto; padding: 32px 28px 20px; }
.task-back { display: grid; place-items: center; width: 36px; height: 36px; border: 1px solid var(--color-border); border-radius: 12px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; }
.task-eyebrow { margin: 0 0 3px; color: var(--color-text-tertiary); font-size: 12px; letter-spacing: .08em; }
.task-header h1 { display: flex; align-items: center; gap: 9px; margin: 0; font-size: 25px; }
.task-counts { display: flex; gap: 8px; margin-left: auto; color: var(--color-text-secondary); font-size: 13px; }
.task-counts span { padding: 7px 10px; border: 1px solid var(--color-border); border-radius: 999px; background: var(--color-bg-secondary); }
.task-content { max-width: 980px; margin: 0 auto; padding: 8px 28px 48px; }
.task-create { display: flex; align-items: center; gap: 10px; padding: 13px; border: 1px solid var(--color-border); border-radius: 16px; }
.task-field-label { color: var(--color-text-tertiary); font-size: 12px; white-space: nowrap; }
.task-input { min-width: 0; flex: 1; border: 0; outline: 0; color: var(--color-text-primary); background: transparent; font-size: 15px; }
.task-select { border: 1px solid var(--color-border); border-radius: 10px; padding: 0 10px; color: var(--color-text-secondary); background: var(--color-bg-secondary); }
.task-add { display: inline-flex; align-items: center; gap: 6px; border: 0; border-radius: 10px; padding: 0 15px; color: var(--color-button-text); background: var(--color-primary); cursor: pointer; font-weight: 600; }
.task-toolbar { display: flex; align-items: center; justify-content: space-between; padding: 24px 2px 12px; }
.task-tabs { display: flex; gap: 4px; padding: 4px; border-radius: 10px; background: var(--color-bg-secondary); }
.task-tabs button { border: 0; border-radius: 7px; padding: 7px 13px; color: var(--color-text-secondary); background: transparent; cursor: pointer; }
.task-tabs button.active { color: var(--color-text-primary); background: var(--color-bg-elevated); box-shadow: var(--shadow-sm, 0 1px 3px rgba(0,0,0,.08)); }
.task-error { color: var(--color-error); font-size: 13px; }
.task-plan-status { color: var(--color-text-tertiary); font-size: 12px; }
.task-list { display: grid; gap: 10px; }
.task-item { display: flex; align-items: center; gap: 13px; padding: 16px; border: 1px solid var(--color-border); border-radius: 14px; transition: border-color .2s, transform .2s; }
.task-item:hover { border-color: var(--color-border-hover); transform: translateY(-1px); }
.task-item.completed { opacity: .68; }
.task-check { display: grid; place-items: center; width: 23px; height: 23px; flex: 0 0 23px; border: 2px solid var(--color-border-hover); border-radius: 50%; color: var(--color-button-text); background: var(--color-primary); cursor: pointer; }
.task-check:disabled { cursor: default; opacity: .85; }
.task-main { min-width: 0; flex: 1; }
.task-title-row { display: flex; align-items: center; gap: 9px; }
.task-title-row h2 { overflow: hidden; margin: 0; font-size: 15px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.completed .task-title-row h2 { text-decoration: line-through; }
.task-priority { padding: 3px 7px; border-radius: 6px; color: var(--color-primary); background: var(--color-primary-muted); font-size: 11px; white-space: nowrap; }
.task-main p { margin: 5px 0 0; color: var(--color-text-secondary); font-size: 13px; }
.task-deadline { display: inline-block; margin-top: 7px; color: var(--color-text-tertiary); font-size: 12px; }
.task-plan-reference { display: inline-block; margin: 7px 0 0 10px; color: var(--color-primary); font-size: 12px; }
.task-edit, .task-delete { display: grid; place-items: center; border: 0; color: var(--color-text-tertiary); background: transparent; cursor: pointer; }
.task-edit:hover { color: var(--color-primary); }
.task-delete:hover { color: var(--color-error); }
.task-edit-form { display: grid; grid-template-columns: auto minmax(160px, 1fr) auto minmax(100px, 140px) auto; align-items: center; gap: 8px; min-width: 0; flex: 1; }
.task-edit-form label { color: var(--color-text-tertiary); font-size: 12px; white-space: nowrap; }
.task-edit-input, .task-edit-select { min-width: 0; border: 1px solid var(--color-border); border-radius: 8px; padding: 7px 9px; color: var(--color-text-primary); background: var(--color-bg-secondary); outline: none; }
.task-edit-input:focus, .task-edit-select:focus, .task-input:focus, .task-select:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-muted); }
.task-edit-actions { display: flex; gap: 6px; }
.task-edit-cancel, .task-edit-save { border: 1px solid var(--color-border); border-radius: 8px; padding: 7px 10px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; white-space: nowrap; }
.task-edit-save { border-color: var(--color-primary); color: var(--color-button-text); background: var(--color-primary); }
.task-edit-save:disabled { cursor: wait; opacity: .6; }
.task-empty { display: grid; place-items: center; gap: 9px; min-height: 220px; border: 1px dashed var(--color-border); border-radius: 16px; color: var(--color-text-tertiary); text-align: center; }
.task-empty strong { color: var(--color-text-secondary); }
@media (prefers-reduced-motion: reduce) { .task-item { transition: none; } }
@media (max-width: 700px) { .task-header { padding: 24px 18px 16px; } .task-content { padding: 8px 18px 36px; } .task-counts { display: none; } .task-create { flex-wrap: wrap; } .task-input { flex-basis: 100%; height: 38px; } .task-select, .task-add { height: 38px; } .task-edit-form { grid-template-columns: 1fr; } .task-edit-form label { margin-top: 2px; } .task-edit-actions { justify-content: flex-end; } }
</style>
