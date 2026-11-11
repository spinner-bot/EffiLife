<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import type { TimeRecord } from '../../domain/models'
import { current, dispatch } from '../../application/runtime'
import { dateKey, dayBounds, overlapMinutes, minutesBetween } from '../../domain/time'
import { t, clock, duration, categoryName, errorMessage } from '../../i18n'
import { openRecord, confirmAction, notify } from '../../ui/state'
import PageHeader from '../../ui/PageHeader.vue'
import Panel from '../../ui/Panel.vue'
import EmptyState from '../../ui/EmptyState.vue'
import UiButton from '../../ui/UiButton.vue'
import ActionMenu from '../../ui/ActionMenu.vue'
import Icon from '../../ui/Icon.vue'
import TimeOverview from './TimeOverview.vue'
import EditRecordDialog from './EditRecordDialog.vue'

const route = useRoute()
const date = ref(String(route.query.date || dateKey(new Date(), current.value.preferences.timeZone)))
const editing = ref<TimeRecord>()
watch(() => route.query.date, value => { if (typeof value === 'string') date.value = value })
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
</script>
<template>
  <PageHeader :title="t('time.title')" :subtitle="t('time.subtitle')"><label class="field"><span class="sr-only">{{ t('form.date') }}</span><input v-model="date" type="date" class="input" required /></label></PageHeader>
  <div class="stack">
    <Panel :title="t('home.dayBalance')"><TimeOverview v-if="date" :date="date" /></Panel>
    <p v-if="overlaps > 0" class="notice">{{ t('time.overlap', { minutes: Math.round(overlaps) }) }}</p>
    <Panel :title="t('time.records')">
      <div v-for="record in records" :key="record.id" class="list-row" :data-selected="route.query.record === record.id || undefined">
        <span class="row-mark"><Icon name="time" :size="18" /></span>
        <div class="grow"><p class="row-title">{{ record.title }}</p><div class="row-detail"><span>{{ clock(record.startAt, current.preferences.timeZone) }} — {{ clock(record.endAt, current.preferences.timeZone) }}</span><span>{{ duration(minutesBetween(record.startAt, record.endAt)) }}</span><span>{{ t(record.timing === 'actual' ? 'record.actual' : 'record.estimated') }}</span></div><p v-if="record.note" class="muted small">{{ record.note }}</p>
          <div class="row-detail"><span v-if="current.categories.find(item => item.id === record.categoryId)" class="badge">{{ categoryName(current.categories.find(item => item.id === record.categoryId)!) }}</span><RouterLink v-if="record.planId" :to="{ name: 'plan', params: { id: record.planId }, query: { task: record.taskId } }" class="text-link small">{{ current.plans.find(item => item.id === record.planId)?.title }}<Icon name="arrow" :size="14" /></RouterLink></div>
        </div><ActionMenu :items="menu(record)" />
      </div>
      <EmptyState v-if="!records.length" :title="t('time.emptyTitle')" :description="t('time.emptyBody')" icon="time"><UiButton variant="primary" @click="openRecord()">{{ t('common.record') }}<Icon name="plus" :size="17" /></UiButton></EmptyState>
    </Panel>
  </div>
  <EditRecordDialog :record="editing" @close="editing = undefined" />
</template>

