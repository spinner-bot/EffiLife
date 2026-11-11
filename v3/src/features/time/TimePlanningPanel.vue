<script setup lang="ts">
import { computed, ref } from 'vue'
import type { TimePlan, TimeRule } from '../../domain/models'
import { current, dispatch } from '../../application/runtime'
import { planningOf, resolveTimePlan, timePlanSummary } from '../../domain/time-planning'
import { t, duration, categoryName, errorMessage } from '../../i18n'
import { notify, confirmAction } from '../../ui/state'
import { useNow } from '../../ui/useNow'
import Panel from '../../ui/Panel.vue'
import UiButton from '../../ui/UiButton.vue'
import ActionMenu from '../../ui/ActionMenu.vue'
import EmptyState from '../../ui/EmptyState.vue'
import Icon from '../../ui/Icon.vue'
import TimePlanEditor from './TimePlanEditor.vue'
import TimeRuleEditor from './TimeRuleEditor.vue'
const props = defineProps<{ date: string }>()
const now = useNow()
const planning = computed(() => planningOf(current.value))
const plan = computed(() => resolveTimePlan(current.value, props.date))
const summary = computed(() => timePlanSummary(current.value, props.date, now.value))
const editorOpen = ref(false)
const editing = ref<TimePlan>()
const ruleOpen = ref(false)
const editingRule = ref<TimeRule>()
function edit(value?: TimePlan) { editing.value = value; editorOpen.value = true }
function editRule(value?: TimeRule) { editingRule.value = value; ruleOpen.value = true }
async function select(event: Event) {
  const id = (event.target as HTMLSelectElement).value
  try { await dispatch({ type: 'setDateTimePlan', date: props.date, timePlanId: id === 'auto' ? null : id }) } catch (error) { notify(errorMessage(error), 'error') }
}
async function remove() {
  if (!plan.value || !await confirmAction(t('planning.deleteConfirm'))) return
  try { await dispatch({ type: 'deleteTimePlan', timePlanId: plan.value.id }) } catch (error) { notify(errorMessage(error), 'error') }
}
async function removeRule(rule: TimeRule) {
  if (!await confirmAction(t('planning.deleteRuleConfirm'))) return
  try { await dispatch({ type: 'deleteTimeRule', ruleId: rule.id }) } catch (error) { notify(errorMessage(error), 'error') }
}
const actions = computed(() => [
  { label: t('planning.create'), icon: 'plus', action: () => edit() },
  ...(plan.value ? [{ label: t('planning.edit'), icon: 'edit', action: () => edit(plan.value) }, { label: t('common.delete'), icon: 'delete', danger: true, action: remove }] : []),
])
function ruleDescription(rule: TimeRule) {
  const name = planning.value.plans.find(item => item.id === rule.planId)?.name || ''
  let expression = rule.value
  if (rule.kind === 'week') expression = rule.value.split(',').map(item => /^\d$/.test(item) ? t('weekday.' + item) : item).join(' · ')
  return t('planning.rule.' + rule.kind) + (expression ? ' · ' + expression : '') + ' → ' + name
}
</script>
<template>
  <Panel :title="t('planning.title')">
    <template #actions><ActionMenu :items="actions" /></template>
    <div class="panel-body stack">
      <label v-if="planning.plans.length" class="field"><span>{{ t('planning.forDate') }}</span><select :value="planning.overrides[date] || 'auto'" class="select" @change="select"><option value="auto">{{ t('planning.automatic') }}</option><option v-for="item in planning.plans" :key="item.id" :value="item.id">{{ item.name }}</option></select></label>
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
      <details v-if="planning.plans.length" class="stack">
        <summary class="text-link" style="cursor: pointer">{{ t('planning.rules') }}</summary>
        <div class="stack" style="margin-top: var(--space-4)"><p class="muted small">{{ t('planning.ruleOrderHelp') }}</p><div v-for="rule in planning.rules" :key="rule.id" class="cluster spread"><p class="small grow">{{ ruleDescription(rule) }}</p><ActionMenu :items="[{ label: t('common.edit'), icon: 'edit', action: () => editRule(rule) }, { label: t('common.delete'), icon: 'delete', danger: true, action: () => removeRule(rule) }]" /></div><UiButton @click="editRule()"><Icon name="plus" :size="16" />{{ t('planning.addRule') }}</UiButton></div>
      </details>
    </div>
  </Panel>
  <TimePlanEditor :open="editorOpen" :plan="editing" :date="date" @close="editorOpen = false" />
  <TimeRuleEditor :open="ruleOpen" :rule="editingRule" :plan-id="plan?.id" @close="ruleOpen = false" />
</template>

