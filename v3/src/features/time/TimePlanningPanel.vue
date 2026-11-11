<script setup lang="ts">
import { computed, ref } from 'vue'
import type { TimePlan } from '../../domain/models'
import { current, dispatch } from '../../application/runtime'
import { planningOf, resolveTimePlan, timePlanSummary } from '../../domain/time-planning'
import { t, duration, categoryName, errorMessage } from '../../i18n'
import { notify } from '../../ui/state'
import { useNow } from '../../ui/useNow'
import Panel from '../../ui/Panel.vue'
import UiButton from '../../ui/UiButton.vue'
import ActionMenu from '../../ui/ActionMenu.vue'
import EmptyState from '../../ui/EmptyState.vue'
import Icon from '../../ui/Icon.vue'
import TimePlanEditor from './TimePlanEditor.vue'
import UiDialog from '../../ui/UiDialog.vue'
const props = defineProps<{ date: string }>()
const now = useNow()
const planning = computed(() => planningOf(current.value))
const plan = computed(() => resolveTimePlan(current.value, props.date))
const summary = computed(() => timePlanSummary(current.value, props.date, now.value))
const editorOpen = ref(false)
const editing = ref<TimePlan>()
const selectionOpen = ref(false), selectedPlan = ref('auto')
function edit(value?: TimePlan) { editing.value = value; editorOpen.value = true }
function choose() { selectedPlan.value = planning.value.overrides[props.date] || 'auto'; selectionOpen.value = true }
async function select() {
  try { await dispatch({ type: 'setDateTimePlan', date: props.date, timePlanId: selectedPlan.value === 'auto' ? null : selectedPlan.value }); selectionOpen.value = false } catch (error) { notify(errorMessage(error), 'error') }
}
const actions = computed(() => [
  { label: t('planning.changeSchedule'), icon: 'calendar', action: choose },
  { label: t('planning.create'), icon: 'plus', action: () => edit() },
  ...(plan.value ? [{ label: t('planning.edit'), icon: 'edit', action: () => edit(plan.value) }] : []),
])
</script>
<template>
  <Panel :title="t('planning.title')">
    <template #actions><ActionMenu :items="actions" /></template>
    <div class="panel-body stack">
      <template v-if="summary">
        <div class="cluster spread"><h3>{{ summary.plan.name }}</h3><span class="badge">{{ t('planning.progress') }} {{ Math.round(summary.progress) }}%</span></div>
        <div class="progress-track"><div class="progress-fill" :style="{ width: Math.min(100, summary.progress) + '%' }" /></div>
        <div v-for="item in summary.items" :key="item.categoryId" class="stack" style="gap: var(--space-2)">
          <div class="cluster spread small"><span class="category-label"><i class="color-dot" :style="{ background: current.categories.find(category => category.id === item.categoryId)?.color }" />{{ categoryName(current.categories.find(category => category.id === item.categoryId)!) }}</span><span>{{ duration(item.total) }} / {{ duration(item.minutes) }}</span></div>
          <p v-if="item.derived > 0" class="muted small">{{ t('planning.derived', { minutes: duration(item.derived) }) }}</p>
        </div>
        <p v-if="summary.plan.mode === 'partition'" class="notice">{{ t('planning.partitionHelp') }}</p>
      </template>
      <EmptyState v-else :title="t('planning.emptyTitle')" :description="t('planning.emptyBody')" icon="calendar"><UiButton @click="edit()">{{ t('planning.create') }}</UiButton></EmptyState>

    </div>
  </Panel>
  <TimePlanEditor :open="editorOpen" :plan="editing" :date="date" @close="editorOpen = false" />
  <UiDialog :open="selectionOpen" :title="t('planning.changeSchedule')" :description="date" @close="selectionOpen = false"><form class="stack" @submit.prevent="select">      <label class="field"><span>{{ t('planning.forDate') }}</span><select v-model="selectedPlan" class="select"><option value="auto">{{ t('planning.automatic') }}</option><option v-for="item in planning.plans" :key="item.id" :value="item.id">{{ item.name }}</option></select></label>
<p class="muted small">{{ t('planning.dateChoiceHelp') }}</p><RouterLink to="/more/time-plans" class="text-link" @click="selectionOpen = false">{{ t('planning.manage') }}</RouterLink><div class="dialog-footer"><UiButton type="submit" variant="primary">{{ t('common.save') }}</UiButton></div></form></UiDialog>
</template>

