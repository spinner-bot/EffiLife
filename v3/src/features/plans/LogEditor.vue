<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ProgressLog } from '../../domain/models'
import { dispatch } from '../../application/runtime'
import { t, errorMessage } from '../../i18n'
import { confirmAction } from '../../ui/state'
import UiDialog from '../../ui/UiDialog.vue'
import UiButton from '../../ui/UiButton.vue'

const props = defineProps<{ planId: string; log?: ProgressLog }>()
const emit = defineEmits<{ close: [] }>()
const content = ref(''), error = ref(''), busy = ref(false)
let initial = '', operationId = ''
watch(() => props.log?.id, id => {
  if (!id) return
  content.value = props.log!.content; initial = content.value
  error.value = ''; operationId = crypto.randomUUID()
}, { immediate: true })
async function close() {
  if (busy.value) return
  if (content.value !== initial && !await confirmAction(t('common.discardConfirm'), t('common.discardBody'))) return
  emit('close')
}
async function save() {
  if (!props.log) return
  busy.value = true; error.value = ''
  try { await dispatch({ type: 'updateLog', planId: props.planId, logId: props.log.id, content: content.value }, operationId); emit('close') }
  catch (failure) { error.value = errorMessage(failure) } finally { busy.value = false }
}
</script>
<template>
  <UiDialog :open="Boolean(log)" :title="t('plans.editLog')" :description="t('plans.editLogBody')" @close="close">
    <form class="stack" @submit.prevent="save">
      <label class="field"><span>{{ t('form.content') }}</span><textarea v-model="content" class="textarea" rows="5" required /></label>
      <p v-if="error" role="alert" class="form-error">{{ error }}</p>
      <div class="dialog-footer"><UiButton :disabled="busy" @click="close">{{ t('common.cancel') }}</UiButton><UiButton type="submit" variant="primary" :disabled="busy">{{ t('common.save') }}</UiButton></div>
    </form>
  </UiDialog>
</template>

