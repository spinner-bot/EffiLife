<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import type { TimeRule } from '../../domain/models'
import { current, dispatch } from '../../application/runtime'
import { planningOf } from '../../domain/time-planning'
import { t, errorMessage } from '../../i18n'
import { confirmAction } from '../../ui/state'
import UiDialog from '../../ui/UiDialog.vue'
import UiButton from '../../ui/UiButton.vue'
const props = defineProps<{ open: boolean; rule?: TimeRule; planId?: string }>()
const emit = defineEmits<{ close: [] }>()
const form = reactive({ kind: 'week' as TimeRule['kind'], planId: '', weekdays: [1, 2, 3, 4, 5], months: [1], yearlyDate: '2026-01-01', weekOfMonth: '1', weekday: '1' })
const busy = ref(false)
const error = ref('')
let initial = ''
let operationId = ''
function range(value: string) {
  return value.split(',').flatMap(part => { const [a, b = a] = part.split('-').map(Number); return Array.from({ length: Math.max(0, b! - a! + 1) }, (_, index) => a! + index) })
}
watch(() => props.open, open => {
  if (!open) return
  const rule = props.rule
  Object.assign(form, { kind: rule?.kind || 'week', planId: rule?.planId || props.planId || planningOf(current.value).plans[0]?.id || '', weekdays: rule?.kind === 'week' ? range(rule.value) : [1, 2, 3, 4, 5], months: rule?.kind === 'month' ? range(rule.value) : [1], yearlyDate: '2026-' + (rule?.kind === 'year' ? rule.value.split(',')[0] : '01-01'), weekOfMonth: rule?.kind === 'month_week' ? rule.value.split('-')[0] : '1', weekday: rule?.kind === 'month_week' ? rule.value.split('-')[1] : '1' })
  initial = JSON.stringify(form); operationId = crypto.randomUUID(); error.value = ''
})
async function close() {
  if (busy.value) return
  if (JSON.stringify(form) !== initial && !await confirmAction(t('common.discardConfirm'), t('common.discardBody'))) return
  emit('close')
}
async function save() {
  busy.value = true; error.value = ''
  const value = form.kind === 'week' ? [...form.weekdays].sort().join(',') : form.kind === 'month' ? [...form.months].sort((a, b) => a - b).join(',') : form.kind === 'year' ? form.yearlyDate.slice(5) : form.kind === 'month_week' ? form.weekOfMonth + '-' + form.weekday : ''
  try { await dispatch({ type: 'saveTimeRule', ruleId: props.rule?.id || undefined, kind: form.kind, value, timePlanId: form.planId }, operationId); emit('close') } catch (failure) { error.value = errorMessage(failure) } finally { busy.value = false }
}
</script>
<template>
  <UiDialog :open="open" :title="t('planning.ruleEditor')" @close="close">
    <form class="stack" @submit.prevent="save">
      <label class="field"><span>{{ t('planning.template') }}</span><select v-model="form.planId" class="select" required><option v-for="plan in planningOf(current).plans" :key="plan.id" :value="plan.id">{{ plan.name }}</option></select></label>
      <label class="field"><span>{{ t('planning.repeat') }}</span><select v-model="form.kind" class="select" :disabled="rule?.kind === 'default'"><option v-for="kind in rule?.kind === 'default' ? ['default'] : ['week', 'month', 'year', 'month_week']" :key="kind" :value="kind">{{ t('planning.rule.' + kind) }}</option></select></label>
      <div v-if="form.kind === 'week'" class="cluster"><label v-for="day in 7" :key="day" class="check-field"><input v-model="form.weekdays" type="checkbox" :value="day" />{{ t('weekday.' + day) }}</label></div>
      <div v-if="form.kind === 'month'" class="cluster"><label v-for="month in 12" :key="month" class="check-field"><input v-model="form.months" type="checkbox" :value="month" />{{ t('planning.monthNumber', { month }) }}</label></div>
      <label v-if="form.kind === 'year'" class="field"><span>{{ t('planning.yearDate') }}</span><input v-model="form.yearlyDate" type="date" class="input" required /></label>
      <div v-if="form.kind === 'month_week'" class="form-grid"><label class="field"><span>{{ t('planning.weekOfMonth') }}</span><select v-model="form.weekOfMonth" class="select"><option v-for="week in 5" :key="week" :value="String(week)">{{ week }}</option></select></label><label class="field"><span>{{ t('planning.weekday') }}</span><select v-model="form.weekday" class="select"><option v-for="day in 7" :key="day" :value="String(day)">{{ t('weekday.' + day) }}</option></select></label></div>
      <p class="muted small">{{ t('planning.ruleOrderHelp') }}</p><p v-if="error" role="alert" class="form-error">{{ error }}</p>
      <div class="dialog-footer"><UiButton :disabled="busy" @click="close">{{ t('common.cancel') }}</UiButton><UiButton type="submit" variant="primary" :disabled="busy">{{ t('common.save') }}</UiButton></div>
    </form>
  </UiDialog>
</template>

