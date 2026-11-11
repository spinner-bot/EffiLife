<script setup lang="ts">
import { ref } from 'vue'
import { current } from '../../application/runtime'
import { t, categoryName } from '../../i18n'
import CategoryEditor from './CategoryEditor.vue'
defineOptions({ inheritAttrs: false })
defineProps<{ modelValue: string; inherit?: boolean; required?: boolean; allowed?: string[] }>()
const emit = defineEmits<{ 'update:modelValue': [id: string]; created: [id: string] }>()
const creating = ref(false)
function change(event: Event) {
  const select = event.target as HTMLSelectElement
  if (select.value === '__create__') { creating.value = true; select.value = select.dataset.value || '' }
  else emit('update:modelValue', select.value)
}
function created(id: string) { emit('created', id); emit('update:modelValue', id) }
</script>
<template>
  <select v-bind="$attrs" class="select" :value="modelValue" :data-value="modelValue" :required="required" @change="change">
    <option v-if="inherit" value="">{{ t('category.inherit') }}</option>
    <option v-for="category in current.categories.filter(item => !allowed || allowed.includes(item.id))" :key="category.id" :value="category.id">{{ categoryName(category) }}</option>
    <option value="__create__">{{ t('category.createInline') }}</option>
  </select>
  <CategoryEditor :open="creating" @saved="created" @close="creating = false" />
</template>
