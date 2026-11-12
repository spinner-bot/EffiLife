<script setup lang="ts">
import { computed, ref } from 'vue'
import { current, dispatch } from '../../application/runtime'
import { planningOf } from '../../domain/time-planning'
import { dateKey } from '../../domain/time'
import type { TimePlan } from '../../domain/models'
import { t, duration, errorMessage } from '../../i18n'
import PageHeader from '../../ui/PageHeader.vue'
import UiButton from '../../ui/UiButton.vue'
import UiDialog from '../../ui/UiDialog.vue'
import EmptyState from '../../ui/EmptyState.vue'
import Icon from '../../ui/Icon.vue'
import TimePlanEditor from './TimePlanEditor.vue'
const planning = computed(() => planningOf(current.value))
const open = ref(false), editing = ref<TimePlan>(), removing = ref<TimePlan>()
const replacementId = ref(''), error = ref(''), busy = ref(false)
const date = computed(() => dateKey(new Date(), current.value.preferences.timeZone))
const isDefault = (id: string) => planning.value.rules.some(rule => rule.kind === 'default' && rule.planId === id) || (!planning.value.rules.some(rule => rule.kind === 'default') && planning.value.plans[0]?.id === id)
function edit(plan?: TimePlan) { editing.value = plan; open.value = true }
function remove(plan: TimePlan) { removing.value = plan; replacementId.value = planning.value.plans.find(item => item.id !== plan.id)?.id || ''; error.value = '' }
async function confirmRemove() {
  if (!removing.value) return
  busy.value = true
  try { await dispatch({ type: 'deleteTimePlan', timePlanId: removing.value.id, replacementId: replacementId.value || undefined }); removing.value = undefined } catch (failure) { error.value = errorMessage(failure) } finally { busy.value = false }
}
</script>
<template>
  <PageHeader :title="t('planning.manage')" :subtitle="t('more.plansHelp')" back="/more"><UiButton variant="primary" @click="edit()"><Icon name="plus" :size="18" />{{ t('planning.create') }}</UiButton></PageHeader>
  <section class="panel"><div v-for="plan in planning.plans" :key="plan.id" class="list-row"><div class="grow"><p class="row-title">{{ plan.name }} <span v-if="isDefault(plan.id)" class="badge">{{ t('planning.fallback') }}</span></p><p class="row-detail">{{ t('planning.' + plan.mode) }} · {{ duration(plan.items.reduce((sum, item) => sum + item.minutes, 0)) }}</p></div><UiButton variant="ghost" :aria-label="t('common.edit') + ': ' + plan.name" @click="edit(plan)"><Icon name="edit" :size="18" /></UiButton><UiButton variant="ghost" :aria-label="t('common.delete') + ': ' + plan.name" @click="remove(plan)"><Icon name="delete" :size="18" /></UiButton></div><EmptyState v-if="!planning.plans.length" :title="t('planning.emptyTitle')" :description="t('planning.emptyBody')" icon="calendar" /></section>
  <TimePlanEditor :open="open" :plan="editing" :date="date" @close="open = false" />
  <UiDialog :open="Boolean(removing)" :title="t('planning.deleteConfirm')" @close="!busy && (removing = undefined)"><form class="stack" @submit.prevent="confirmRemove"><p class="small muted">{{ t('planning.deleteHelp') }}</p><label v-if="removing && isDefault(removing.id)" class="field"><span>{{ t('planning.replacement') }}</span><select v-model="replacementId" class="select" required><option value="" disabled>{{ t('planning.replacementRequired') }}</option><option v-for="plan in planning.plans.filter(item => item.id !== removing?.id)" :key="plan.id" :value="plan.id">{{ plan.name }}</option></select><span v-if="planning.plans.length === 1" class="small muted">{{ t('validation.defaultPlanReplacement') }}</span></label><p v-if="error" role="alert" class="form-error">{{ error }}</p><div class="dialog-footer"><UiButton :disabled="busy" @click="removing = undefined">{{ t('common.cancel') }}</UiButton><UiButton variant="primary" type="submit" :disabled="busy || Boolean(removing && isDefault(removing.id) && !replacementId)">{{ t('common.delete') }}</UiButton></div></form></UiDialog>
</template>
