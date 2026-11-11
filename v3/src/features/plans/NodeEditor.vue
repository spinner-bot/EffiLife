<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { dispatch } from '../../application/runtime'
import type { PlanNode, NodeKind } from '../../domain/models'
import { t, errorMessage } from '../../i18n'
import { confirmAction } from '../../ui/state'
import CategorySelect from '../categories/CategorySelect.vue'
import UiDialog from '../../ui/UiDialog.vue'
import UiButton from '../../ui/UiButton.vue'
const props = defineProps<{ open: boolean; planId: string; node?: PlanNode; parentId: string | null; kind: NodeKind }>()
const emit = defineEmits<{ close: [] }>()
const form = reactive({ title: '', description: '', estimatedMinutes: 0, categoryId: '' })
const error = ref('')
const busy = ref(false)
let initial = ''
watch(() => props.open, value => {
  if (value) { Object.assign(form, { title: props.node?.title || '', description: props.node?.description || '', estimatedMinutes: props.node?.estimatedMinutes || 0, categoryId: props.node?.categoryId || '' }); error.value = ''; initial = JSON.stringify(form) }
})
async function close() {
  if (busy.value) return
  if (JSON.stringify(form) !== initial && !await confirmAction(t('common.discardConfirm'), t('common.discardBody'))) return
  emit('close')
}
async function save() {
  busy.value = true
  try {
    if (props.node) await dispatch({ type: 'updateNode', planId: props.planId, nodeId: props.node.id, ...form, categoryId: form.categoryId || null })
    else await dispatch({ type: 'addNode', planId: props.planId, parentId: props.parentId, kind: props.kind, ...form, categoryId: form.categoryId || undefined })
    emit('close')
  } catch (failure) { error.value = errorMessage(failure) } finally { busy.value = false }
}
</script>
<template>
  <UiDialog :open="open" :title="node ? t('common.edit') : t(kind === 'section' ? 'plans.addSection' : kind === 'group' ? 'plans.addGroup' : 'plans.addTask')" @close="close">
    <form class="stack" @submit.prevent="save">
      <label class="field"><span>{{ t('form.title') }}</span><input v-model="form.title" class="input" required /></label>
      <label class="field"><span>{{ t('form.description') }}</span><textarea v-model="form.description" class="textarea" /></label>
      <label v-if="kind === 'task'" class="field"><span>{{ t('form.estimated') }}</span><input v-model.number="form.estimatedMinutes" type="number" min="0" class="input" /></label>
      <label class="field"><span>{{ t(kind === 'task' ? 'form.category' : 'plans.defaultCategory') }}</span><CategorySelect v-model="form.categoryId" inherit /><span class="small muted">{{ t('plans.defaultHelp') }}</span></label>
      <p v-if="error" role="alert" class="form-error">{{ error }}</p>
      <div class="dialog-footer"><UiButton :disabled="busy" @click="close">{{ t('common.cancel') }}</UiButton><UiButton type="submit" variant="primary" :disabled="busy">{{ t('common.save') }}</UiButton></div>
    </form>
  </UiDialog>
</template>

