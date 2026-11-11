<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import type { Todo, TodoRecurrence } from '../../domain/models'
import { current, dispatch } from '../../application/runtime'
import { dateTimeInput, parseDateTimeInput } from '../../ui/datetime'
import { t, categoryName, errorMessage } from '../../i18n'
import { confirmAction } from '../../ui/state'
import UiDialog from '../../ui/UiDialog.vue'
import UiButton from '../../ui/UiButton.vue'
import Icon from '../../ui/Icon.vue'
const props = defineProps<{ open: boolean; todo?: Todo }>()
const emit = defineEmits<{ close: [] }>()
const form = reactive({ title: '', description: '', categoryId: 'life', deadline: '', priorityRank: 5, urgent: false, important: false, estimatedMinutes: 0, tags: '', pinned: false, sortOrder: 0, deadlineWarningDays: 3, repeat: 'none' as 'none' | TodoRecurrence['frequency'], interval: 1, subtasks: [] as Array<{ id: string; title: string; completed: boolean }> })
const checklistTitle = ref('')
const error = ref('')
const busy = ref(false)
let initial = ''
let operationId = ''
watch(() => props.open, value => {
  if (!value) return
  const todo = props.todo
  Object.assign(form, { title: todo?.title || '', description: todo?.description || '', categoryId: todo?.categoryId || 'life', deadline: todo?.deadline ? dateTimeInput(todo.deadline, current.value.preferences.timeZone) : '', priorityRank: todo?.priorityRank ?? 5, urgent: todo?.urgent || false, important: todo?.important || false, estimatedMinutes: todo?.estimatedMinutes || 0, tags: todo?.tags.join(', ') || '' })
  Object.assign(form, { pinned: todo?.pinned || false, sortOrder: todo?.sortOrder || 0, deadlineWarningDays: todo?.deadlineWarningDays ?? 3, repeat: todo?.recurrence?.frequency || 'none', interval: todo?.recurrence?.interval || 1, subtasks: (todo?.subtasks || []).map(item => ({ id: item.id, title: item.title, completed: item.completed })) })
  checklistTitle.value = ''; operationId = crypto.randomUUID()
  initial = JSON.stringify(form); error.value = ''
})
async function close() {
  if (busy.value) return
  if ((JSON.stringify(form) !== initial || checklistTitle.value.trim()) && !await confirmAction(t('common.discardConfirm'), t('common.discardBody'))) return
  emit('close')
}
async function save() {
  busy.value = true; error.value = ''
  try {
    if (checklistTitle.value.trim()) addChecklist()
    const recurrence = form.repeat === 'none' ? null : { frequency: form.repeat, interval: form.interval, anchorDay: props.todo?.recurrence?.frequency === form.repeat ? props.todo.recurrence.anchorDay : undefined }
    await dispatch({ ...form, type: 'saveTodo', todoId: props.todo?.id, deadline: form.deadline ? parseDateTimeInput(form.deadline, current.value.preferences.timeZone) : null, tags: form.tags.split(/[,，]/).map(item => item.trim()).filter(Boolean), recurrence }, operationId)
    emit('close')
  } catch (failure) { error.value = errorMessage(failure) } finally { busy.value = false }
}
function addChecklist() {
  if (!checklistTitle.value.trim()) return
  form.subtasks.push({ id: crypto.randomUUID(), title: checklistTitle.value.trim(), completed: false })
  checklistTitle.value = ''
}
</script>
<template>
  <UiDialog :open="open" :title="todo ? t('common.edit') : t('todos.add')" @close="close">
    <form class="stack" @submit.prevent="save">
      <label class="field"><span>{{ t('form.title') }}</span><input v-model="form.title" class="input" required /></label>
      <label class="field"><span>{{ t('form.description') }}</span><textarea v-model="form.description" class="textarea" /></label>
      <section class="stack" style="gap: 8px"><h3>{{ t('todos.checklist') }}</h3>
        <div v-for="(item, index) in form.subtasks" :key="item.id" class="cluster" style="flex-wrap: nowrap"><input v-model="item.completed" type="checkbox" :aria-label="t('todos.checkItem') + ': ' + item.title" /><input v-model="item.title" class="input grow" :aria-label="t('todos.checkTitle') + ' ' + (index + 1)" required /><UiButton variant="ghost" icon :aria-label="t('common.delete') + ': ' + item.title" @click="form.subtasks.splice(index, 1)"><Icon name="delete" :size="16" /></UiButton></div>
        <div class="cluster" style="flex-wrap: nowrap"><input v-model="checklistTitle" class="input grow" :placeholder="t('todos.addCheck')" :aria-label="t('todos.addCheck')" @keydown.enter.prevent="addChecklist" /><UiButton icon :aria-label="t('todos.addCheck')" :disabled="!checklistTitle.trim()" @click="addChecklist"><Icon name="plus" :size="17" /></UiButton></div>
      </section>
      <div class="form-grid">
        <label class="field"><span>{{ t('form.category') }}</span><select v-model="form.categoryId" class="select"><option v-for="category in current.categories" :key="category.id" :value="category.id">{{ categoryName(category) }}</option></select></label>
        <label class="field"><span>{{ t('form.deadline') }} · {{ t('common.optional') }}</span><input v-model="form.deadline" type="datetime-local" class="input" /></label>
      </div>
      <details><summary>{{ t('todos.scheduling') }}</summary><div class="stack" style="padding-top: 16px"><div class="form-grid">
        <label class="field"><span>{{ t('form.priority') }}</span><input v-model.number="form.priorityRank" class="input" type="number" min="0" step="1" required /></label><label class="field"><span>{{ t('form.estimated') }}</span><input v-model.number="form.estimatedMinutes" class="input" type="number" min="0" /></label>
        <label class="field"><span>{{ t('todos.repeat') }}</span><select v-model="form.repeat" class="select"><option value="none">{{ t('todos.repeat.none') }}</option><option value="day">{{ t('todos.repeat.day') }}</option><option value="week">{{ t('todos.repeat.week') }}</option><option value="month">{{ t('todos.repeat.month') }}</option></select></label>
        <label v-if="form.repeat !== 'none'" class="field"><span>{{ t('todos.repeatInterval') }}</span><input v-model.number="form.interval" type="number" class="input" min="1" step="1" required /></label>
        <label class="field"><span>{{ t('todos.sort.manual') }}</span><input v-model.number="form.sortOrder" class="input" type="number" step="1" required /></label>
        <label class="field"><span>{{ t('todos.warningDays') }}</span><input v-model.number="form.deadlineWarningDays" class="input" type="number" min="0" step="1" required /></label><label class="field"><span>{{ t('todos.tags') }}</span><input v-model="form.tags" class="input" :placeholder="t('todos.tagsHint')" /></label>
      </div><p v-if="form.repeat !== 'none'" class="small muted">{{ t('todos.repeatBody') }}</p><div class="cluster"><label class="check-field"><input v-model="form.important" type="checkbox" />{{ t('form.important') }}</label><label class="check-field"><input v-model="form.urgent" type="checkbox" />{{ t('form.urgent') }}</label><label class="check-field"><input v-model="form.pinned" type="checkbox" />{{ t('todos.pin') }}</label></div></div></details>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p><div class="dialog-footer"><UiButton :disabled="busy" @click="close">{{ t('common.cancel') }}</UiButton><UiButton type="submit" variant="primary" :disabled="busy">{{ t('common.save') }}</UiButton></div>
    </form>
  </UiDialog>
</template>

