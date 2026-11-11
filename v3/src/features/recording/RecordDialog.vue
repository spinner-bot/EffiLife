<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { current, dispatch } from '../../application/runtime'
import { categoryFor, displayCode } from '../../domain/plans'
import { referenceFor, minutesBetween } from '../../domain/time'
import { dateTimeInput, parseDateTimeInput } from '../../ui/datetime'
import { recording, confirmAction, notify } from '../../ui/state'
import { t, categoryName, errorMessage } from '../../i18n'
import UiDialog from '../../ui/UiDialog.vue'
import UiButton from '../../ui/UiButton.vue'
import Icon from '../../ui/Icon.vue'

const blank = () => ({
  title: '', content: '', planId: '', taskId: '', categoryId: 'life',
  startAt: '', endAt: dateTimeInput(new Date().toISOString(), current.value.preferences.timeZone),
  withTime: true, complete: false, reference: false,
})
const form = reactive(blank())
const error = ref('')
const saving = ref(false)
let initial = ''
let operationId = ''
const plans = computed(() => current.value.plans.filter(plan => !plan.archivedAt))
const plan = computed(() => plans.value.find(item => item.id === form.planId))
const tasks = computed(() => plan.value?.nodes.filter(node => node.kind === 'task' && !node.deletedAt) || [])
const reference = computed(() => referenceFor(current.value, new Date().toISOString()))
const elapsed = computed(() => {
  try { return minutesBetween(parseDateTimeInput(form.startAt, current.value.preferences.timeZone), parseDateTimeInput(form.endAt, current.value.preferences.timeZone)) } catch { return 0 }
})
watch(() => recording.sequence, () => {
  Object.assign(form, blank(), { planId: recording.planId, taskId: recording.taskId })
  if (recording.planId && recording.taskId) {
    const selected = plans.value.find(item => item.id === recording.planId)
    if (selected) form.categoryId = categoryFor(selected, recording.taskId)
  }
  initial = JSON.stringify(form)
  operationId = crypto.randomUUID()
  error.value = ''
})
function changePlan() {
  form.taskId = ''
  form.complete = false
}
function changeTask() {
  if (plan.value && form.taskId) form.categoryId = categoryFor(plan.value, form.taskId)
  form.complete = false
}
function useReference() {
  if (!reference.value) return
  form.startAt = dateTimeInput(reference.value.startAt, current.value.preferences.timeZone)
  form.endAt = dateTimeInput(reference.value.endAt, current.value.preferences.timeZone)
  form.withTime = true
  form.reference = true
}
function setDuration(event: Event) {
  const minutes = Number((event.target as HTMLInputElement).value)
  if (!Number.isFinite(minutes) || minutes <= 0 || !form.endAt) return
  const end = parseDateTimeInput(form.endAt, current.value.preferences.timeZone)
  form.startAt = dateTimeInput(new Date(Date.parse(end) - minutes * 60000).toISOString(), current.value.preferences.timeZone)
  form.reference = false
}
async function close() {
  if (saving.value) return
  if (JSON.stringify(form) !== initial && !await confirmAction(t('common.discardConfirm'), t('common.discardBody'))) return
  recording.open = false
}
async function save() {
  error.value = ''
  saving.value = true
  try {
    const timeZone = current.value.preferences.timeZone
    await dispatch({
      type: 'recordAction', title: form.title || undefined, content: form.content,
      planId: form.planId || undefined, taskId: form.taskId || undefined,
      categoryId: form.categoryId, completeTask: Boolean(form.taskId && form.complete),
      occurredAt: parseDateTimeInput(form.endAt, timeZone),
      startAt: form.withTime ? parseDateTimeInput(form.startAt, timeZone) : undefined,
      endAt: form.withTime ? parseDateTimeInput(form.endAt, timeZone) : undefined,
      timing: form.reference ? 'confirmed-reference' : 'actual',
    }, operationId)
    recording.open = false
    notify(t('record.saved'))
  } catch (failure) { error.value = errorMessage(failure) } finally { saving.value = false }
}
</script>
<template>
  <UiDialog :open="recording.open" :title="t('record.title')" :description="t('record.subtitle')" @close="close">
    <form class="stack" @submit.prevent="save">
      <div class="form-grid">
        <label class="field"><span>{{ t('form.plan') }}</span><select v-model="form.planId" class="select" @change="changePlan"><option value="">{{ t('form.noPlan') }}</option><option v-for="item in plans" :key="item.id" :value="item.id">{{ item.title }}</option></select></label>
        <label v-if="plan" class="field"><span>{{ t('form.task') }}</span><select v-model="form.taskId" class="select" @change="changeTask"><option value="">{{ t('form.planNote') }}</option><option v-for="item in tasks" :key="item.id" :value="item.id">{{ displayCode(plan, item.id) }} · {{ item.title }}</option></select></label>
        <label v-else class="field"><span>{{ t('form.title') }}</span><input v-model="form.title" class="input" required /></label>
      </div>
      <label class="field"><span>{{ t('form.content') }}</span><textarea v-model="form.content" class="textarea" :placeholder="t('form.contentPlaceholder')" :required="!form.taskId && Boolean(form.planId)" /></label>
      <label class="field"><span>{{ t('form.category') }}</span><select v-model="form.categoryId" class="select"><option v-for="item in current.categories" :key="item.id" :value="item.id">{{ categoryName(item) }}</option></select></label>
      <label v-if="plan" class="check-field"><input v-model="form.withTime" type="checkbox" /><span>{{ t('form.withTime') }}</span></label>
      <label v-if="!form.withTime" class="field"><span>{{ t('form.logTime') }}</span><input v-model="form.endAt" class="input" type="datetime-local" required /></label>
      <div v-if="form.withTime" class="stack">
        <div class="form-grid">
          <label class="field"><span>{{ t('form.start') }}</span><input v-model="form.startAt" class="input" type="datetime-local" required @input="form.reference = false" /></label>
          <label class="field"><span>{{ t('form.end') }}</span><input v-model="form.endAt" class="input" type="datetime-local" required @input="form.reference = false" /></label>
          <label class="field"><span>{{ t('form.duration') }} · {{ t('common.minutes', { value: '' }).trim() }}</span><input class="input" type="number" min="1" step="1" :value="elapsed || ''" @change="setDuration" /></label>
        </div>
        <div v-if="reference" class="notice stack"><p>{{ t('record.reference', { minutes: Math.round(reference.minutes) }) }}</p><UiButton variant="ghost" @click="useReference"><Icon name="timer" :size="17" />{{ t('record.useReference') }}</UiButton></div>
        <p v-if="form.reference" class="small muted">{{ t('record.referenceConfirmed') }}</p>
      </div>
      <label v-if="form.taskId" class="check-field"><input v-model="form.complete" type="checkbox" /><span>{{ t('form.markComplete') }}</span></label>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <div class="dialog-footer"><UiButton :disabled="saving" @click="close">{{ t('common.cancel') }}</UiButton><UiButton type="submit" variant="primary" :disabled="saving"><Icon name="check" :size="18" />{{ t('common.save') }}</UiButton></div>
    </form>
  </UiDialog>
</template>

