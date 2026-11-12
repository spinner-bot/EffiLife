<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import type { TimeRecord } from '../../domain/models'
import { current, dispatch } from '../../application/runtime'
import { dateKey, minutesBetween } from '../../domain/time'
import { t, calendarDate, clock, duration, categoryName, errorMessage } from '../../i18n'
import { confirmAction, notify } from '../../ui/state'
import PageHeader from '../../ui/PageHeader.vue'
import Panel from '../../ui/Panel.vue'
import EmptyState from '../../ui/EmptyState.vue'
import UiButton from '../../ui/UiButton.vue'
import Icon from '../../ui/Icon.vue'
import CategoryIdentity from '../categories/CategoryIdentity.vue'
import EditRecordDialog from './EditRecordDialog.vue'

const route = useRoute(), router = useRouter()
const record = computed<TimeRecord | undefined>(() => current.value.records.find(item => item.id === route.params.id))
const day = computed(() => record.value ? dateKey(record.value.startAt, current.value.preferences.timeZone) : '')
const backTo = computed(() => day.value ? { path: '/time', query: { date: day.value } } : { path: '/time' })
const editing = ref<TimeRecord>()
const plan = computed(() => record.value?.planId ? current.value.plans.find(item => item.id === record.value!.planId) : undefined)
const task = computed(() => plan.value?.nodes.find(node => node.id === record.value?.taskId))
const log = computed(() => plan.value?.logs.find(item => item.id === record.value?.logId))
const todo = computed(() => {
  const id = record.value?.id
  if (!id) return undefined
  return current.value.todos.find(item => item.id === record.value?.todoId || item.recordIds.includes(id))
})
async function remove() {
  if (!record.value || !await confirmAction(t('record.deleteConfirm'))) return
  try {
    await dispatch({ type: 'deleteRecord', recordId: record.value.id })
    notify(t('common.saved'))
    await router.push(backTo.value)
  } catch (failure) { notify(errorMessage(failure), 'error') }
}
</script>
<template>
  <template v-if="record">
    <PageHeader :title="record.title" :subtitle="calendarDate(day, { weekday: 'long' })" :back="'/time?date=' + day">
      <UiButton @click="editing = record"><Icon name="edit" :size="17" />{{ t('common.edit') }}</UiButton>
      <UiButton variant="ghost" @click="remove"><Icon name="delete" :size="17" />{{ t('common.delete') }}</UiButton>
    </PageHeader>
    <div class="stack">
      <Panel :title="t('record.detailTitle')">
        <div class="panel-body stack record-detail">
          <CategoryIdentity :category-id="record.categoryId" />
          <dl class="detail-grid">
            <dt>{{ t('form.date') }}</dt><dd>{{ calendarDate(day, { weekday: 'long' }) }}</dd>
            <dt>{{ t('form.start') }}</dt><dd>{{ clock(record.startAt, current.preferences.timeZone) }}</dd>
            <dt>{{ t('form.end') }}</dt><dd>{{ clock(record.endAt, current.preferences.timeZone) }}</dd>
            <dt>{{ t('form.duration') }}</dt><dd><strong>{{ duration(minutesBetween(record.startAt, record.endAt)) }}</strong></dd>
            <dt>{{ t('record.timingLabel') }}</dt><dd>{{ t(record.timing === 'actual' ? 'record.actual' : 'record.estimated') }}</dd>
          </dl>
        </div>
      </Panel>
      <Panel v-if="record.note" :title="t('record.note')"><p class="panel-body record-note">{{ record.note }}</p></Panel>
      <Panel v-if="plan || todo" :title="t('record.context')">
        <div class="panel-body stack">
          <RouterLink v-if="plan" :to="{ name: 'plan', params: { id: plan.id }, query: { task: record.taskId, log: record.logId } }" class="list-row detail-link">
            <span class="row-mark"><Icon name="plans" :size="18" /></span>
            <span class="grow"><strong>{{ plan.title }}</strong><span class="row-detail" style="display: block">{{ task?.title || t('form.planNote') }}</span></span>
            <Icon name="next" :size="16" />
          </RouterLink>
          <RouterLink v-if="todo" :to="{ path: '/todos', query: { todo: todo.id } }" class="list-row detail-link">
            <span class="row-mark"><Icon name="todos" :size="18" /></span>
            <span class="grow"><strong>{{ todo.title }}</strong><span class="row-detail" style="display: block">{{ categoryName(current.categories.find(item => item.id === todo!.categoryId)!) }}</span></span>
            <Icon name="next" :size="16" />
          </RouterLink>
          <p v-if="log" class="muted small detail-log">{{ log.content }}</p>
        </div>
      </Panel>
    </div>
    <EditRecordDialog :record="editing" @close="editing = undefined" />
  </template>
  <EmptyState v-else :title="t('record.missingTitle')" :description="t('record.missingBody')" icon="time">
    <RouterLink to="/time" class="text-link">{{ t('common.back') }}</RouterLink>
  </EmptyState>
</template>
<style scoped>
.record-detail { gap: 1rem; }.detail-grid { display: grid; grid-template-columns: auto 1fr; gap: .45rem 1.25rem; margin: 0; }.detail-grid dt { color: var(--muted); font-size: .82rem; }.detail-grid dd { margin: 0; }.record-note { white-space: pre-wrap; overflow-wrap: anywhere; }.detail-link { text-decoration: none; color: var(--ink); }.detail-link:hover { background: var(--subtle); }.detail-log { margin: 0; }
</style>
