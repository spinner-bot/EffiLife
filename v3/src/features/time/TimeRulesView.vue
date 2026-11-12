<script setup lang="ts">
import { computed, ref } from 'vue'
import { current, dispatch } from '../../application/runtime'
import { planningOf } from '../../domain/time-planning'
import type { TimeRule } from '../../domain/models'
import { t, errorMessage } from '../../i18n'
import { notify, confirmAction } from '../../ui/state'
import PageHeader from '../../ui/PageHeader.vue'
import UiButton from '../../ui/UiButton.vue'
import Icon from '../../ui/Icon.vue'
import ActionMenu from '../../ui/ActionMenu.vue'
import SortableList from '../../ui/SortableList.vue'
import TimeRuleEditor from './TimeRuleEditor.vue'
const planning = computed(() => planningOf(current.value))
const ordinary = computed(() => planning.value.rules.filter(rule => rule.kind !== 'default'))
const fallback = computed(() => [...planning.value.rules].reverse().find(rule => rule.kind === 'default') || (planning.value.plans[0] ? { id: '', kind: 'default' as const, value: '', planId: planning.value.plans[0].id } : undefined))
const editing = ref<TimeRule>(), open = ref(false)
function edit(rule?: TimeRule) { editing.value = rule; open.value = true }
function description(rule: TimeRule) {
  let value = rule.value
  if (rule.kind === 'week') value = value.split(',').map(day => /^\d$/.test(day) ? t('weekday.' + day) : day).join(' · ')
  return t('planning.rule.' + rule.kind) + (value ? ' · ' + value : '') + ' → ' + (planning.value.plans.find(plan => plan.id === rule.planId)?.name || '')
}
async function remove(rule: TimeRule) {
  if (!await confirmAction(t('planning.deleteRuleConfirm'))) return
  try { await dispatch({ type: 'deleteTimeRule', ruleId: rule.id }) } catch (failure) { notify(errorMessage(failure), 'error') }
}
async function reorder(ruleIds: string[]) {
  try { await dispatch({ type: 'reorderTimeRules', ruleIds }) } catch (failure) { notify(errorMessage(failure), 'error') }
}
function menu(rule: TimeRule) { return [{ label: t('common.edit'), icon: 'edit', action: () => edit(rule) }, { label: t('common.delete'), icon: 'delete', danger: true, action: () => remove(rule) }] }
</script>
<template>
  <PageHeader :title="t('planning.rules')" :subtitle="t('planning.ruleOrderHelp')" back="/more"><UiButton variant="primary" :disabled="!planning.plans.length" @click="edit()"><Icon name="plus" :size="18" />{{ t('planning.addRule') }}</UiButton></PageHeader>
  <section class="panel"><SortableList :ids="ordinary.map(rule => rule.id)" @reorder="reorder"><template #default="{ id }"><div class="cluster spread"><p class="small grow">{{ description(ordinary.find(rule => rule.id === id)!) }}</p><ActionMenu :items="menu(ordinary.find(rule => rule.id === id)!)" /></div></template></SortableList>
    <div class="list-row fallback-rule"><Icon name="lock" :size="18" /><div class="grow"><p class="row-title">{{ t('planning.fallback') }}</p><p class="row-detail">{{ fallback ? description(fallback) : t('planning.fallbackEmpty') }}</p><p class="small muted">{{ t('planning.fallbackHelp') }}</p></div><UiButton v-if="fallback" variant="ghost" :aria-label="t('planning.editFallback')" @click="edit(fallback)"><Icon name="edit" :size="18" /></UiButton><RouterLink v-else to="/more/time-plans" class="text-link">{{ t('planning.manage') }}</RouterLink></div>
  </section>
  <TimeRuleEditor :open="open" :rule="editing" @close="open = false" />
</template>
<style scoped>.fallback-rule { background: var(--subtle); border-radius: 0 0 var(--radius) var(--radius); }</style>
