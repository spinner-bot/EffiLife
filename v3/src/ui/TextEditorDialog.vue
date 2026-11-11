<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import UiDialog from './UiDialog.vue'
import UiButton from './UiButton.vue'
import { t, errorMessage } from '../i18n'
import { confirmAction } from './state'
const props = withDefaults(defineProps<{
  open: boolean; title: string; initialTitle?: string; initialDescription?: string
  descriptionField?: boolean; multiline?: boolean
  save: (value: { title: string; description: string }) => Promise<void>
}>(), { initialTitle: '', initialDescription: '', descriptionField: true })
const emit = defineEmits<{ close: [] }>()
const form = reactive({ title: '', description: '' })
const error = ref('')
const busy = ref(false)
let initial = ''
watch(() => props.open, value => {
  if (value) { form.title = props.initialTitle; form.description = props.initialDescription; initial = JSON.stringify(form); error.value = '' }
})
async function close() {
  if (busy.value) return
  if (JSON.stringify(form) !== initial && !await confirmAction(t('common.discardConfirm'), t('common.discardBody'))) return
  emit('close')
}
async function submit() {
  busy.value = true
  error.value = ''
  try { await props.save({ ...form }); emit('close') } catch (failure) { error.value = errorMessage(failure) } finally { busy.value = false }
}
</script>
<template>
  <UiDialog :open="open" :title="title" @close="close">
    <form class="stack" @submit.prevent="submit">
      <label class="field"><span>{{ multiline ? t('form.content') : t('form.title') }}</span><textarea v-if="multiline" v-model="form.title" class="textarea" required /><input v-else v-model="form.title" class="input" required /></label>
      <label v-if="descriptionField" class="field"><span>{{ t('form.description') }}</span><textarea v-model="form.description" class="textarea" /></label>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <div class="dialog-footer"><UiButton :disabled="busy" @click="close">{{ t('common.cancel') }}</UiButton><UiButton type="submit" variant="primary" :disabled="busy">{{ t('common.save') }}</UiButton></div>
    </form>
  </UiDialog>
</template>

