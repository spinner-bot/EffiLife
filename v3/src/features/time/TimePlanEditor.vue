<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { TimePlan } from '../../domain/models'
import { current, dispatch } from '../../application/runtime'
import { planningOf } from '../../domain/time-planning'
import { t, categoryName, errorMessage } from '../../i18n'
import { confirmAction } from '../../ui/state'
import UiDialog from '../../ui/UiDialog.vue'
import UiButton from '../../ui/UiButton.vue'
import Icon from '../../ui/Icon.vue'
const props = defineProps<{ open: boolean; plan?: TimePlan; date: string }>()
const emit = defineEmits<{ close: [] }>()
const form = reactive({ name: '', mode: 'allocation' as TimePlan['mode'], items: [] as Array<{ categoryId: string; hours: number }>, backgroundCategoryId: 'life', makeDefault: false, useForDate: false })
const error = ref('')
const busy = ref(false)
let initial = ''
let operationId = ''
const total = computed(() => form.items.reduce((sum, item) => sum + Number(item.hours || 0), 0))
watch(() => props.open, value => {
  if (!value) return
  const plan = props.plan
  Object.assign(form, {
    name: plan?.name || '', mode: plan?.mode || 'allocation',
    items: plan ? plan.items.map(item => ({ categoryId: item.categoryId, hours: item.minutes / 60 })) : current.value.categories.map(category => ({ categoryId: category.id, hours: 0 })),
    backgroundCategoryId: plan?.backgroundCategoryId || 'life',
    makeDefault: Boolean(plan && planningOf(current.value).rules.some(rule => rule.kind === 'default' && rule.planId === plan.id)),
    useForDate: !plan,
  })
  error.value = ''; initial = JSON.stringify(form); operationId = crypto.randomUUID()
})
function addItem() {
  const category = current.value.categories.find(item => !form.items.some(row => row.categoryId === item.id))
  if (category) form.items.push({ categoryId: category.id, hours: 0 })
}
async function close() {
  if (busy.value) return
  if (JSON.stringify(form) !== initial && !await confirmAction(t('common.discardConfirm'), t('common.discardBody'))) return
  emit('close')
}
async function save() {
  busy.value = true; error.value = ''
  try {
    await dispatch({ type: 'saveTimePlan', timePlanId: props.plan?.id, name: form.name, mode: form.mode, items: form.items.map(item => ({ categoryId: item.categoryId, minutes: Number(item.hours) * 60 })), backgroundCategoryId: form.backgroundCategoryId, makeDefault: form.makeDefault, useForDate: form.useForDate ? props.date : undefined }, operationId)
    emit('close')
  } catch (failure) { error.value = errorMessage(failure) } finally { busy.value = false }
}
</script>
<template>
  <UiDialog :open="open" :title="plan ? t('planning.edit') : t('planning.create')" :description="t('planning.editorHelp')" @close="close">
    <form class="stack" @submit.prevent="save">
      <label class="field"><span>{{ t('form.title') }}</span><input v-model="form.name" class="input" required /></label>
      <label class="field"><span>{{ t('planning.mode') }}</span><select v-model="form.mode" class="select"><option value="allocation">{{ t('planning.allocation') }}</option><option value="partition">{{ t('planning.partition') }}</option></select></label>
      <div v-for="(item, index) in form.items" :key="index" class="budget-input-row">
        <label class="field"><span class="sr-only">{{ t('form.category') }} {{ index + 1 }}</span><select v-model="item.categoryId" class="select"><option v-for="category in current.categories" :key="category.id" :value="category.id">{{ categoryName(category) }}</option></select></label>
        <label class="field"><span class="sr-only">{{ categoryName(current.categories.find(category => category.id === item.categoryId)!) }} {{ t('planning.targetHours') }}</span><input v-model.number="item.hours" class="input" type="number" min="0" step="0.25" required /></label>
        <UiButton variant="ghost" icon :aria-label="t('planning.removeItem') + ' ' + (index + 1)" @click="form.items.splice(index, 1)"><Icon name="close" :size="17" /></UiButton>
      </div>
      <div class="cluster spread"><UiButton variant="ghost" :disabled="form.items.length >= current.categories.length" @click="addItem"><Icon name="plus" :size="16" />{{ t('planning.addItem') }}</UiButton><span class="muted small">{{ t('planning.totalHours', { hours: total }) }}</span></div>
      <p v-if="total > 24" class="notice">{{ t('planning.overbooked') }}</p>
      <label v-if="form.mode === 'partition'" class="field"><span>{{ t('planning.background') }}</span><select v-model="form.backgroundCategoryId" class="select"><option v-for="item in form.items" :key="item.categoryId" :value="item.categoryId">{{ categoryName(current.categories.find(category => category.id === item.categoryId)!) }}</option></select></label>
      <p v-if="form.mode === 'partition'" class="notice">{{ t('planning.partitionHelp') }}</p>
      <label class="check-field"><input v-model="form.makeDefault" type="checkbox" />{{ t('planning.makeDefault') }}</label>
      <label class="check-field"><input v-model="form.useForDate" type="checkbox" />{{ t('planning.useForDate') }}</label>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <div class="dialog-footer"><UiButton :disabled="busy" @click="close">{{ t('common.cancel') }}</UiButton><UiButton type="submit" variant="primary" :disabled="busy">{{ t('common.save') }}</UiButton></div>
    </form>
  </UiDialog>
</template>

