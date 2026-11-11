<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { TimeRecord } from '../../domain/models'
import { current, dispatch } from '../../application/runtime'
import { dateTimeInput, parseDateTimeInput } from '../../ui/datetime'
import { minutesBetween } from '../../domain/time'
import { t, duration, errorMessage } from '../../i18n'
import { confirmAction } from '../../ui/state'
import CategorySelect from '../categories/CategorySelect.vue'
import UiDialog from '../../ui/UiDialog.vue'
import UiButton from '../../ui/UiButton.vue'
const props = defineProps<{ record?: TimeRecord }>()
const emit = defineEmits<{ close: [] }>()
const form = reactive({ title: '', note: '', categoryId: '', startAt: '', endAt: '' })
const error = ref('')
const minutes = computed(() => { try { return minutesBetween(parseDateTimeInput(form.startAt, current.value.preferences.timeZone), parseDateTimeInput(form.endAt, current.value.preferences.timeZone)) } catch { return 0 } })
const busy = ref(false)
let initial = ''
watch(() => props.record, value => {
  if (value) { Object.assign(form, value, { startAt: dateTimeInput(value.startAt, current.value.preferences.timeZone), endAt: dateTimeInput(value.endAt, current.value.preferences.timeZone) }); error.value = ''; initial = JSON.stringify(form) }
})
async function close() {
  if (busy.value) return
  if (JSON.stringify(form) !== initial && !await confirmAction(t('common.discardConfirm'), t('common.discardBody'))) return
  emit('close')
}
async function save() {
  if (!props.record) return
  busy.value = true
  try {
    await dispatch({ ...form, type: 'updateRecord', recordId: props.record.id, expectedMinutes: minutes.value, startAt: parseDateTimeInput(form.startAt, current.value.preferences.timeZone), endAt: parseDateTimeInput(form.endAt, current.value.preferences.timeZone) })
    emit('close')
  } catch (failure) { error.value = errorMessage(failure) } finally { busy.value = false }
}
</script>
<template>
  <UiDialog :open="Boolean(record)" :title="t('common.edit') + ' · ' + t('time.records')" @close="close">
    <form class="stack" @submit.prevent="save">
      <label class="field"><span>{{ t('form.title') }}</span><input v-model="form.title" class="input" required /></label>
      <label class="field"><span>{{ t('form.content') }}</span><textarea v-model="form.note" class="textarea" /></label>
      <label class="field"><span>{{ t('form.category') }}</span><CategorySelect v-model="form.categoryId" required /></label>
      <div class="form-grid"><label class="field"><span>{{ t('form.start') }}</span><input v-model="form.startAt" type="datetime-local" class="input" required /></label><label class="field"><span>{{ t('form.end') }}</span><input v-model="form.endAt" type="datetime-local" class="input" required /></label></div>
      <p class="small muted" aria-live="polite">{{ t('form.duration') }} · {{ duration(minutes) }}</p>
      <p v-if="error" role="alert" class="form-error">{{ error }}</p><div class="dialog-footer"><UiButton :disabled="busy" @click="close">{{ t('common.cancel') }}</UiButton><UiButton type="submit" variant="primary" :disabled="busy">{{ t('common.save') }}</UiButton></div>
    </form>
  </UiDialog>
</template>

