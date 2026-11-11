<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import type { Todo, TodoStatus } from '../../domain/models'
import { current, dispatch } from '../../application/runtime'
import { priorityScore } from '../../domain/priority'
import { dateKey } from '../../domain/time'
import { t, calendarDate, errorMessage } from '../../i18n'
import { confirmAction, notify } from '../../ui/state'
import PageHeader from '../../ui/PageHeader.vue'
import UiButton from '../../ui/UiButton.vue'
import Panel from '../../ui/Panel.vue'
import EmptyState from '../../ui/EmptyState.vue'
import ActionMenu from '../../ui/ActionMenu.vue'
import Icon from '../../ui/Icon.vue'
import TodoEditor from './TodoEditor.vue'

const status = ref<TodoStatus>('pending')
const quick = ref('')
const busy = ref(false)
const editing = ref<Todo>()
const editorOpen = ref(false)
const search = ref('')
const now = ref(new Date().toISOString())
let timer: ReturnType<typeof setInterval>
onMounted(() => { timer = setInterval(() => { now.value = new Date().toISOString() }, 30000) })
onUnmounted(() => clearInterval(timer))
function score(todo: Todo) { return priorityScore(todo, current.value.categories.find(category => category.id === todo.categoryId)!, now.value) }
const todos = computed(() => current.value.todos.filter(todo => todo.status === status.value && todo.title.toLowerCase().includes(search.value.toLowerCase())).sort((a, b) => score(b) - score(a) || Date.parse(b.createdAt) - Date.parse(a.createdAt)))
async function capture() {
  if (!quick.value.trim() || busy.value) return
  busy.value = true
  try { await dispatch({ type: 'saveTodo', title: quick.value }); quick.value = ''; notify(t('common.saved')) } catch (failure) { notify(errorMessage(failure), 'error') } finally { busy.value = false }
}
function edit(todo?: Todo) { editing.value = todo; editorOpen.value = true }
async function complete(todo: Todo) {
  try { await dispatch({ type: 'setTodoStatus', todoId: todo.id, status: todo.status === 'completed' ? 'pending' : 'completed' }) } catch (failure) { notify(errorMessage(failure), 'error') }
}
async function remove(todo: Todo) {
  if (!await confirmAction(t('todos.deleteConfirm'))) return
  try { await dispatch({ type: 'deleteTodo', todoId: todo.id }) } catch (failure) { notify(errorMessage(failure), 'error') }
}
function menu(todo: Todo) {
  return [
    { label: t('common.edit'), icon: 'edit', action: () => edit(todo) },
    { label: t('common.delete'), icon: 'delete', danger: true, action: () => remove(todo) },
  ]
}
</script>
<template>
  <PageHeader :title="t('todos.title')" :subtitle="t('todos.subtitle')"><UiButton @click="edit()"><Icon name="plus" :size="18" />{{ t('todos.add') }}</UiButton></PageHeader>
  <Panel>
    <div class="panel-body stack">
      <form class="quick-capture" @submit.prevent="capture"><label class="field grow"><span class="sr-only">{{ t('todos.placeholder') }}</span><input v-model="quick" class="input" :placeholder="t('todos.placeholder')" /></label><UiButton type="submit" variant="primary" :disabled="busy || !quick.trim()"><Icon name="plus" :size="18" />{{ t('todos.add') }}</UiButton></form>
      <div class="cluster spread"><div class="filter-tabs"><button type="button" class="filter-tab" :aria-pressed="status === 'pending'" @click="status = 'pending'">{{ t('todos.pending') }}</button><button type="button" class="filter-tab" :aria-pressed="status === 'completed'" @click="status = 'completed'">{{ t('todos.completed') }}</button></div><label class="field"><span class="sr-only">{{ t('common.search') }}</span><input v-model="search" type="search" class="input" :placeholder="t('common.search')" /></label></div>
    </div>
    <div v-for="todo in todos" :key="todo.id" class="list-row"><button type="button" class="todo-check" :aria-pressed="todo.status === 'completed'" :aria-label="(todo.status === 'completed' ? t('todos.reopen') : t('todos.complete')) + ': ' + todo.title" @click="complete(todo)"><Icon v-if="todo.status === 'completed'" name="check" :size="16" /></button><div class="grow"><p class="row-title" :class="{ 'todo-complete': todo.status === 'completed' }">{{ todo.title }}</p><p v-if="todo.description" class="muted small">{{ todo.description }}</p><div class="row-detail"><span>{{ score(todo) < 0 ? t('todos.overdue') : t('todos.rank', { score: score(todo) }) }}</span><span v-if="todo.deadline">{{ calendarDate(dateKey(todo.deadline, current.preferences.timeZone)) }}</span><span v-if="todo.important"><Icon name="flag" :size="13" /></span></div></div><ActionMenu :items="menu(todo)" /></div>
    <EmptyState v-if="!todos.length" :title="t('todos.emptyTitle')" :description="t('todos.emptyBody')" icon="todos" />
  </Panel>
  <TodoEditor :open="editorOpen" :todo="editing" @close="editorOpen = false" />
</template>

