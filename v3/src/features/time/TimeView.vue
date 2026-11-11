<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import type { TimeRecord } from '../../domain/models'
import { current, dispatch } from '../../application/runtime'
import { dateKey, dayBounds, overlapMinutes, minutesBetween } from '../../domain/time'
import { t, clock, duration, errorMessage } from '../../i18n'
import { openRecord, confirmAction, notify } from '../../ui/state'
import PageHeader from '../../ui/PageHeader.vue'
import Panel from '../../ui/Panel.vue'
import EmptyState from '../../ui/EmptyState.vue'
import UiButton from '../../ui/UiButton.vue'
import ActionMenu from '../../ui/ActionMenu.vue'
import Icon from '../../ui/Icon.vue'
import CategoryRings from './CategoryRings.vue'
import CategoryBadge from '../categories/CategoryBadge.vue'
import EditRecordDialog from './EditRecordDialog.vue'
import TimePlanningPanel from './TimePlanningPanel.vue'

const route = useRoute()
function validDate(value: unknown) {
  if (typeof value === 'string') {
    try { dayBounds(value, current.value.preferences.timeZone); return value } catch { /* Keep invalid links outside the live query. */ }
  }
  return dateKey(new Date(), current.value.preferences.timeZone)
}
const date = ref(validDate(route.query.date))
const editing = ref<TimeRecord>()
watch(() => route.query.record, async id => {
  if (typeof id !== 'string') return
  await nextTick()
  document.querySelector<HTMLElement>('[data-record-id="' + CSS.escape(id) + '"]')?.scrollIntoView({ block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
}, { immediate: true, flush: 'post' })
watch(() => route.query.date, value => { if (typeof value === 'string') date.value = validDate(value) })
const records = computed(() => {
  try {
    const [start, end] = dayBounds(date.value, current.value.preferences.timeZone)
    return current.value.records.filter(record => Date.parse(record.endAt) > start && Date.parse(record.startAt) < end).sort((a, b) => Date.parse(b.startAt) - Date.parse(a.startAt))
  } catch { return [] }
})
const overlaps = computed(() => {
  try { return overlapMinutes(current.value.records, date.value, current.value.preferences.timeZone) } catch { return 0 }
})
async function remove(record: TimeRecord) {
  if (!await confirmAction(t('record.deleteConfirm'))) return
  try { await dispatch({ type: 'deleteRecord', recordId: record.id }); notify(t('common.saved')) } catch (failure) { notify(errorMessage(failure), 'error') }
}
function menu(record: TimeRecord) {
  return [
    { label: t('common.edit'), icon: 'edit', action: () => { editing.value = record } },
    { label: t('common.delete'), icon: 'delete', danger: true, action: () => remove(record) },
  ]
}
function todoFor(record: TimeRecord) { return current.value.todos.find(todo => todo.id === record.todoId || todo.recordIds.includes(record.id)) }
</script>
<template>
  <PageHeader :title="t('time.title')" :subtitle="t('time.subtitle')"><label class="field"><span class="sr-only">{{ t('form.date') }}</span><input v-model="date" type="date" class="input" required /></label></PageHeader>
  <div class="stack">
    <Panel :title="t('time.categoryBreakdown')"><CategoryRings v-if="date" :date="date" /></Panel>
    <TimePlanningPanel v-if="date" :date="date" />
    <p v-if="overlaps > 0" class="notice">{{ t('time.overlap', { minutes: Math.round(overlaps) }) }}</p>
    <Panel :title="t('time.records')">
      <div v-for="record in records" :key="record.id" class="list-row compact-record" :data-record-id="record.id" :data-selected="route.query.record === record.id || undefined">
        <div class="grow"><div class="cluster spread record-heading"><p class="row-title"><CategoryBadge :category-id="record.categoryId" />{{ record.title }}</p><div class="cluster record-links"><RouterLink v-if="todoFor(record)" :to="{ path: '/todos', query: { todo: todoFor(record)!.id } }" class="text-link small" :aria-label="todoFor(record)!.title" :title="todoFor(record)!.title"><Icon name="todos" :size="16" /></RouterLink><RouterLink v-if="record.planId" :to="{ name: 'plan', params: { id: record.planId }, query: { task: record.taskId, log: record.logId } }" class="text-link small" :aria-label="current.plans.find(item => item.id === record.planId)?.title" :title="current.plans.find(item => item.id === record.planId)?.title"><Icon name="plans" :size="16" /></RouterLink></div></div>
          <p class="row-detail compact-record-detail"><strong :title="record.startAt + ' — ' + record.endAt">{{ clock(record.startAt, current.preferences.timeZone) }} — {{ clock(record.endAt, current.preferences.timeZone) }} · {{ duration(minutesBetween(record.startAt, record.endAt)) }}<span v-if="record.timing !== 'actual'"> · {{ t('record.estimated') }}</span></strong><span v-if="record.note" class="record-description" :title="record.note">{{ record.note }}</span><span class="sr-only">{{ t(record.timing === 'actual' ? 'record.actual' : 'record.estimated') }}</span></p>
        </div><ActionMenu :items="menu(record)" />
      </div>
      <EmptyState v-if="!records.length" :title="t('time.emptyTitle')" :description="t('time.emptyBody')" icon="time"><UiButton variant="primary" @click="openRecord()">{{ t('common.record') }}<Icon name="plus" :size="17" /></UiButton></EmptyState>
    </Panel>
  </div>
  <EditRecordDialog :record="editing" @close="editing = undefined" />
</template>

<style scoped>
.record-heading { gap: .5rem; flex-wrap: nowrap; align-items: baseline; }.record-heading .row-title { min-width: 0; overflow-wrap: anywhere; }.record-links { flex-shrink: 0; }.compact-record-detail { flex-wrap: nowrap; min-width: 0; gap: .6rem; }.compact-record-detail strong { font-weight: 650; flex-shrink: 0; }.record-description { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; min-width: 0; }
@media(max-width: 520px) { .compact-record-detail { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.record-description { margin-inline-start: .5rem; } }
</style>
