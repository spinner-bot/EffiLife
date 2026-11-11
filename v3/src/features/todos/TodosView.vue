<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import type { Todo, TodoStatus } from '../../domain/models'
import { current, dispatch } from '../../application/runtime'
import { priorityScore } from '../../domain/priority'
import { activeTodo, matchesTodo, sortTodos, todoMinutes, type TodoSort } from '../../domain/todos'
import { dateKey } from '../../domain/time'
import { t, calendarDate, categoryName, duration, errorMessage } from '../../i18n'
import { useNow } from '../../ui/useNow'
import { confirmAction, notify, openRecord } from '../../ui/state'
import PageHeader from '../../ui/PageHeader.vue'
import UiButton from '../../ui/UiButton.vue'
import Panel from '../../ui/Panel.vue'
import EmptyState from '../../ui/EmptyState.vue'
import ActionMenu from '../../ui/ActionMenu.vue'
import Icon from '../../ui/Icon.vue'
import CategoryBadge from '../categories/CategoryBadge.vue'
import TodoEditor from './TodoEditor.vue'

const status = ref<TodoStatus>('pending')
const quick = ref('')
const busy = ref(false)
const editing = ref<Todo>()
const editorOpen = ref(false)
const search = ref('')
const categoryId = ref('')
const tag = ref('')
const sort = ref<TodoSort>('priority')
const filterCount = computed(() => Number(Boolean(categoryId.value)) + Number(Boolean(tag.value)) + Number(sort.value !== 'priority'))
const now = useNow()
const route = useRoute()
const selected = computed(() => String(route.query.todo || ''))
const tags = computed(() => [...new Set(current.value.todos.flatMap(todo => todo.tags))].sort())
function score(todo: Todo) { return priorityScore(todo, current.value.categories.find(category => category.id === todo.categoryId)!, now.value) }
const todos = computed(() => sortTodos(current.value, current.value.todos.filter(todo => (status.value === 'pending' ? activeTodo(todo) : status.value === 'archived' ? ['archived', 'cancelled'].includes(todo.status) : todo.status === status.value) && matchesTodo(todo, search.value, categoryId.value, tag.value)), now.value, sort.value))
watch([selected, () => current.value.todos.length], async () => {
  const todo = current.value.todos.find(todo => todo.id === selected.value)
  if (!todo) return
  status.value = activeTodo(todo) ? 'pending' : todo.status === 'cancelled' ? 'archived' : todo.status
  search.value = ''; categoryId.value = ''; tag.value = ''
  await nextTick()
  document.querySelector<HTMLElement>('[data-todo-id="' + CSS.escape(todo.id) + '"]')?.scrollIntoView({ block: 'center' })
}, { immediate: true, flush: 'post' })
async function capture() {
  if (!quick.value.trim() || busy.value) return
  busy.value = true
  try { await dispatch({ type: 'saveTodo', title: quick.value }); quick.value = ''; notify(t('common.saved')) } catch (failure) { notify(errorMessage(failure), 'error') } finally { busy.value = false }
}
function edit(todo?: Todo) { editing.value = todo; editorOpen.value = true }
async function complete(todo: Todo) {
  try { await dispatch({ type: 'setTodoStatus', todoId: todo.id, status: todo.status === 'completed' ? 'pending' : 'completed' }) } catch (failure) { notify(errorMessage(failure), 'error') }
}
async function changeStatus(todo: Todo, value: TodoStatus) { try { await dispatch({ type: 'setTodoStatus', todoId: todo.id, status: value }) } catch (failure) { notify(errorMessage(failure), 'error') } }
async function pin(todo: Todo) { try { await dispatch({ type: 'setTodoPinned', todoId: todo.id, pinned: !todo.pinned }) } catch (failure) { notify(errorMessage(failure), 'error') } }
async function check(todo: Todo, subtaskId: string, completed: boolean) { try { await dispatch({ type: 'setTodoSubtask', todoId: todo.id, subtaskId, completed }) } catch (failure) { notify(errorMessage(failure), 'error') } }
function timeLink(todo: Todo) { const record = current.value.records.filter(record => todo.recordIds.includes(record.id)).sort((a, b) => Date.parse(b.endAt) - Date.parse(a.endAt))[0]; return { path: '/time', query: record ? { date: dateKey(record.startAt, current.value.preferences.timeZone), record: record.id } : {} } }
function dueSoon(todo: Todo) { const remaining = todo.deadline ? Date.parse(todo.deadline) - Date.parse(now.value) : Infinity; return activeTodo(todo) && remaining > 0 && remaining <= (todo.deadlineWarningDays ?? 3) * 86400000 }
async function remove(todo: Todo) {
  if (!await confirmAction(t('todos.deleteConfirm'))) return
  try { await dispatch({ type: 'deleteTodo', todoId: todo.id }) } catch (failure) { notify(errorMessage(failure), 'error') }
}
function menu(todo: Todo) {
  return [
    { label: t('common.edit'), icon: 'edit', action: () => edit(todo) },
    ...(!['archived', 'cancelled'].includes(todo.status) ? [{ label: t('todos.recordTime'), icon: 'time', action: () => openRecord({ todoId: todo.id }) }] : []),
    { label: t(todo.pinned ? 'todos.unpin' : 'todos.pin'), icon: 'pin', action: () => pin(todo) },
    ...(activeTodo(todo) ? [{ label: t(todo.status === 'in-progress' ? 'todos.pause' : 'todos.start'), icon: 'activity', action: () => changeStatus(todo, todo.status === 'in-progress' ? 'pending' : 'in-progress') }] : []),
    { label: todo.status === 'archived' || todo.status === 'cancelled' ? t('common.restore') : t('common.archive'), icon: 'archive', action: () => changeStatus(todo, todo.status === 'archived' || todo.status === 'cancelled' ? 'pending' : 'archived') },
    { label: t('common.delete'), icon: 'delete', danger: true, action: () => remove(todo) },
  ]
}
</script>
<template>
  <PageHeader :title="t('todos.title')" :subtitle="t('todos.subtitle')"><UiButton @click="edit()"><Icon name="plus" :size="18" />{{ t('todos.add') }}</UiButton></PageHeader>
  <Panel>
    <div class="panel-body stack">
      <form class="quick-capture" @submit.prevent="capture"><label class="field grow"><span class="sr-only">{{ t('todos.placeholder') }}</span><input v-model="quick" class="input" :placeholder="t('todos.placeholder')" /></label><UiButton type="submit" variant="primary" :disabled="busy || !quick.trim()"><Icon name="plus" :size="18" />{{ t('todos.add') }}</UiButton></form>
      <div class="cluster spread"><div class="filter-tabs"><button type="button" class="filter-tab" :aria-pressed="status === 'pending'" @click="status = 'pending'">{{ t('todos.pending') }}</button><button type="button" class="filter-tab" :aria-pressed="status === 'completed'" @click="status = 'completed'">{{ t('todos.completed') }}</button><button type="button" class="filter-tab" :aria-pressed="status === 'archived'" @click="status = 'archived'">{{ t('common.archive') }}</button></div><label class="field"><span class="sr-only">{{ t('common.search') }}</span><input v-model="search" type="search" class="input" :placeholder="t('common.search')" /></label></div>
      <details class="todo-filter-panel"><summary>{{ t('todos.filters') }} <span v-if="filterCount" class="badge">{{ filterCount }}</span></summary><div class="todo-filters"><label class="field"><span class="sr-only">{{ t('todos.filterCategory') }}</span><select v-model="categoryId" class="select"><option value="">{{ t('todos.allCategories') }}</option><option v-for="category in current.categories" :key="category.id" :value="category.id">{{ categoryName(category) }}</option></select></label><label class="field"><span class="sr-only">{{ t('todos.filterTag') }}</span><select v-model="tag" class="select"><option value="">{{ t('todos.allTags') }}</option><option v-for="value in tags" :key="value" :value="value">{{ value }}</option></select></label><label class="field"><span class="sr-only">{{ t('todos.sort') }}</span><select v-model="sort" class="select"><option value="priority">{{ t('todos.sort.priority') }}</option><option value="deadline">{{ t('todos.sort.deadline') }}</option><option value="created">{{ t('todos.sort.created') }}</option><option value="manual">{{ t('todos.sort.manual') }}</option></select></label></div></details>
    </div>
    <div v-for="todo in todos" :key="todo.id" class="list-row" :data-todo-id="todo.id" :data-selected="todo.id === selected"><button type="button" class="todo-check" :aria-pressed="todo.status === 'completed'" :aria-label="(todo.status === 'completed' ? t('todos.reopen') : t('todos.complete')) + ': ' + todo.title" @click="complete(todo)"><Icon v-if="todo.status === 'completed'" name="check" :size="16" /></button><div class="grow"><p class="row-title" :class="{ 'todo-complete': todo.status === 'completed' }"><CategoryBadge :category-id="todo.categoryId" /><Icon v-if="todo.pinned" name="pin" :size="14" />{{ todo.title }}</p><div class="row-detail"><span>{{ score(todo) < 0 ? t('todos.overdue') : t('todos.rank', { score: score(todo) }) }}</span><strong v-if="todo.deadline">{{ calendarDate(dateKey(todo.deadline, current.preferences.timeZone)) }}</strong><span v-if="todo.description" class="todo-description" :title="todo.description">{{ todo.description }}</span><span v-if="todo.status === 'in-progress'" class="badge">{{ t('todos.inProgress') }}</span><span v-if="dueSoon(todo)" class="badge">{{ t('todos.dueSoon') }}</span><span v-if="todo.important"><Icon name="flag" :size="13" /></span><span v-if="todo.recurrence"><Icon name="repeat" :size="13" />{{ t('todos.every.' + todo.recurrence.frequency, { interval: todo.recurrence.interval }) }}</span><span v-for="value in todo.tags" :key="value" class="badge">{{ value }}</span><RouterLink v-if="todo.recordIds.length" :to="timeLink(todo)" class="text-link">{{ t('todos.recorded', { duration: duration(todoMinutes(current, todo)) }) }}</RouterLink><RouterLink v-if="todo.relatedPlanId" :to="{ name: 'plan', params: { id: todo.relatedPlanId }, query: { task: todo.relatedTaskId } }" class="text-link">{{ t('todos.relatedPlan') }}</RouterLink></div><details v-if="todo.subtasks?.length" class="todo-checklist"><summary>{{ t('todos.checkProgress', { done: todo.subtasks.filter(item => item.completed).length, total: todo.subtasks.length }) }}</summary><label v-for="item in todo.subtasks" :key="item.id" class="check-field small"><input type="checkbox" :checked="item.completed" @change="check(todo, item.id, ($event.target as HTMLInputElement).checked)" /><span :class="{ 'todo-complete': item.completed }">{{ item.title }}</span></label></details></div><ActionMenu :items="menu(todo)" /></div>
    <EmptyState v-if="!todos.length" :title="t('todos.emptyTitle')" :description="t('todos.emptyBody')" icon="todos" />
  </Panel>
  <TodoEditor :open="editorOpen" :todo="editing" @close="editorOpen = false" />
</template>

<style scoped>.todo-description { max-width: 28rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.row-detail strong { font-weight: 650; }</style>
