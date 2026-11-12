<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { current, dispatch } from '../../application/runtime'
import { t, categoryName, errorMessage } from '../../i18n'
import { confirmAction } from '../../ui/state'
import UiDialog from '../../ui/UiDialog.vue'
import UiButton from '../../ui/UiButton.vue'
const props = defineProps<{ open: boolean; categoryId?: string }>()
const emit = defineEmits<{ close: []; saved: [id: string] }>()
const form = reactive({ name: '', description: '', color: '#526ac9', difficulty: 5 })
const busy = ref(false), error = ref('')
let initial = '', originalName = ''
watch(() => props.open, open => {
  if (!open) return
  const category = current.value.categories.find(item => item.id === props.categoryId)
  Object.assign(form, { name: category ? categoryName(category) : '', description: category?.description || '', color: category?.color || '#526ac9', difficulty: category?.difficulty ?? 5 })
  originalName = form.name; initial = JSON.stringify(form); error.value = ''
})
async function close() {
  if (busy.value) return
  if (JSON.stringify(form) !== initial && !await confirmAction(t('common.discardConfirm'), t('common.discardBody'))) return
  emit('close')
}
async function save() {
  busy.value = true
  try {
    const result = await dispatch({ type: 'saveCategory', ...form, categoryId: props.categoryId, name: props.categoryId && form.name === originalName ? undefined : form.name })
    emit('saved', result.entityId!); emit('close')
  } catch (failure) { error.value = errorMessage(failure) } finally { busy.value = false }
}
</script>
<template>
  <UiDialog :open="open" :title="categoryId ? t('common.edit') : t('settings.addCategory')" @close="close">
    <form class="stack" @submit.prevent="save">
      <label class="field"><span>{{ t('form.title') }}</span><input v-model="form.name" class="input" required /></label>
      <label class="field"><span>{{ t('form.description') }} <span class="muted">{{ t('common.optional') }}</span></span><textarea v-model="form.description" class="input" rows="3" :placeholder="t('category.descriptionPlaceholder')" /></label>
      <div class="form-grid"><label class="field"><span>{{ t('form.color') }}</span><input v-model="form.color" type="color" class="input" /></label><label class="field"><span>{{ t('form.difficulty') }}</span><input v-model.number="form.difficulty" type="number" min="0" class="input" required /></label></div>
      <p class="small muted">{{ t('category.difficultyHelp') }}</p>
      <p v-if="error" role="alert" class="form-error">{{ error }}</p>
      <div class="dialog-footer"><UiButton :disabled="busy" @click="close">{{ t('common.cancel') }}</UiButton><UiButton type="submit" variant="primary" :disabled="busy">{{ t('common.save') }}</UiButton></div>
    </form>
  </UiDialog>
</template>
