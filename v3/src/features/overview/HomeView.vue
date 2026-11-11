<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { current, dispatch } from '../../application/runtime'
import { dateKey } from '../../domain/time'
import { daySummary, recentActivities } from '../../domain/selectors'
import { planProgress } from '../../domain/plans'
import { priorityScore } from '../../domain/priority'
import { t, duration, calendarDate, clock, errorMessage } from '../../i18n'
import { openRecord, notify } from '../../ui/state'
import PageHeader from '../../ui/PageHeader.vue'
import Panel from '../../ui/Panel.vue'
import EmptyState from '../../ui/EmptyState.vue'
import Icon from '../../ui/Icon.vue'
import TimeOverview from '../time/TimeOverview.vue'

const date = computed(() => dateKey(new Date(), current.value.preferences.timeZone))
const summary = computed(() => daySummary(current.value, date.value))
const plans = computed(() => current.value.plans.filter(plan => !plan.archivedAt))
const todos = computed(() => current.value.todos.filter(todo => todo.status === 'pending').sort((a, b) => {
  const category = (id: string) => current.value.categories.find(item => item.id === id)!
  return priorityScore(b, category(b.categoryId), new Date().toISOString()) - priorityScore(a, category(a.categoryId), new Date().toISOString())
}))
const recent = computed(() => recentActivities(current.value).slice(0, 5))
async function completeTodo(id: string) {
  try { await dispatch({ type: 'setTodoStatus', todoId: id, status: 'completed' }); notify(t('common.saved')) } catch (error) { notify(errorMessage(error), 'error') }
}
</script>
<template>
  <PageHeader :title="t('home.title')" :subtitle="t('home.subtitle')" :eyebrow="t('home.eyebrow')" />
  <div class="stats-grid">
    <section class="panel stat"><div><p class="stat-label">{{ t('stats.recorded') }}</p><strong class="stat-value">{{ duration(summary.total) }}</strong></div><span class="stat-icon"><Icon name="time" /></span></section>
    <section class="panel stat"><div><p class="stat-label">{{ t('stats.activePlans') }}</p><strong class="stat-value">{{ plans.length }}</strong></div><span class="stat-icon"><Icon name="plans" /></span></section>
    <section class="panel stat"><div><p class="stat-label">{{ t('stats.pendingTodos') }}</p><strong class="stat-value">{{ todos.length }}</strong></div><span class="stat-icon"><Icon name="todos" /></span></section>
  </div>
  <div class="dashboard-grid">
    <div class="dashboard-left">
      <Panel :title="t('home.timeTitle')" :subtitle="calendarDate(date, { weekday: 'long' })"><template #actions><RouterLink to="/time" class="text-link">{{ t('home.viewTime') }}<Icon name="arrow" :size="16" /></RouterLink></template><TimeOverview :date="date" /></Panel>
      <Panel :title="t('home.activePlans')">
        <template #actions><RouterLink to="/plans" class="text-link">{{ t('home.viewPlans') }}<Icon name="arrow" :size="16" /></RouterLink></template>
        <template v-if="plans.length"><RouterLink v-for="plan in plans.slice(0, 4)" :key="plan.id" :to="'/plans/' + plan.id" class="list-row">
          <span class="row-mark"><Icon name="plans" :size="18" /></span><div class="grow"><p class="row-title">{{ plan.title }}</p><div class="row-detail"><span>{{ t('stats.progress', { done: planProgress(plan).completed, total: planProgress(plan).total }) }}</span><span>{{ t('stats.logs', { count: plan.logs.length }) }}</span></div></div><Icon name="next" :size="16" />
        </RouterLink></template>
        <EmptyState v-else :title="t('home.emptyPlansTitle')" :description="t('home.emptyPlansBody')" icon="plans"><RouterLink to="/plans" class="text-link">{{ t('plans.create') }}<Icon name="arrow" :size="16" /></RouterLink></EmptyState>
      </Panel>
    </div>
    <div class="dashboard-right">
      <Panel :title="t('home.todoTitle')">
        <template #actions><RouterLink to="/todos" class="text-link"><Icon name="arrow" :size="18" /><span class="sr-only">{{ t('nav.todos') }}</span></RouterLink></template>
        <div v-for="todo in todos.slice(0, 4)" :key="todo.id" class="list-row"><button type="button" class="todo-check" :aria-label="t('todos.complete') + ': ' + todo.title" @click="completeTodo(todo.id)" /><div class="grow"><p class="row-title">{{ todo.title }}</p><p v-if="todo.deadline" class="row-detail">{{ calendarDate(dateKey(todo.deadline, current.preferences.timeZone)) }}</p></div></div>
        <div v-if="!todos.length" class="panel-body muted small">{{ t('home.noTodos') }}</div>
      </Panel>
      <Panel :title="t('home.recent')">
        <div v-for="activity in recent" :key="activity.id" class="list-row"><span class="row-mark"><Icon :name="activity.minutes ? 'time' : 'log'" :size="18" /></span><div class="grow"><RouterLink v-if="activity.planId" :to="{ path: '/plans/' + activity.planId, query: { task: activity.taskId } }" class="row-title">{{ activity.title }}</RouterLink><p v-else class="row-title">{{ activity.title }}</p><div class="row-detail"><span>{{ clock(activity.at, current.preferences.timeZone) }}</span><span>{{ activity.minutes ? duration(activity.minutes) : t('form.logOnly') }}</span></div></div></div>
        <EmptyState v-if="!recent.length" :title="t('home.emptyRecordsTitle')" icon="log"><button type="button" class="button ghost" @click="openRecord()">{{ t('common.record') }}<Icon name="arrow" :size="16" /></button></EmptyState>
      </Panel>
    </div>
  </div>
</template>

