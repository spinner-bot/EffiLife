<script setup lang="ts">
import { computed, ref } from 'vue'
import { categoryIcons } from './categoryIcons'
import { useI18n } from '@/i18n'

const props = defineProps<{
  modelValue: string
  modelColor: string
  modelAscii?: string
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void
  (event: 'update:modelColor', value: string): void
  (event: 'update:modelAscii', value: string): void
}>()

const { t } = useI18n()
const activeTab = ref<'icons' | 'ascii' | 'colors'>('icons')
const search = ref('')
const tabs = ['icons', 'ascii', 'colors'] as const

const icons = categoryIcons

const colors = [
  '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e', '#10b981', '#14b8a6',
  '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899',
  '#f43f5e', '#78716c', '#64748b', '#334155',
]
const ascii = Array.from('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
const filteredIcons = computed(() => {
  const query = search.value.trim().toLowerCase()
  return query ? icons.filter((icon) => icon.name.includes(query)) : icons
})

function selectColor(color: string) {
  emit('update:modelColor', color)
}
</script>

<template>
  <div class="category-icon-picker">
    <div class="picker-tabs">
      <button v-for="tab in tabs" :key="tab" type="button" :class="{ active: activeTab === tab }" @click="activeTab = tab">{{ t(`tasks.iconTab.${tab}`) }}</button>
    </div>
    <div v-if="activeTab === 'icons'" class="picker-content">
      <input v-model="search" class="picker-search" :placeholder="t('tasks.iconSearch')" :aria-label="t('tasks.iconSearch')" />
      <div class="icon-grid">
        <button v-for="icon in filteredIcons" :key="icon.name" type="button" class="icon-choice" :class="{ selected: props.modelValue === icon.name }" :title="icon.name" :aria-label="t('tasks.iconLabel', { name: icon.name })" :aria-pressed="props.modelValue === icon.name" @click="emit('update:modelValue', icon.name)">
          <component :is="icon.component" :size="18" />
        </button>
      </div>
    </div>
    <div v-else-if="activeTab === 'ascii'" class="picker-content">
      <div class="ascii-grid">
        <button v-for="character in ascii" :key="character" type="button" class="ascii-choice" :class="{ selected: props.modelAscii === character }" @click="emit('update:modelAscii', character)">{{ character }}</button>
      </div>
    </div>
    <div v-else class="picker-content">
      <div class="color-grid">
        <button v-for="color in colors" :key="color" type="button" class="color-choice" :class="{ selected: props.modelColor === color }" :style="{ background: color }" :title="color" :aria-label="t('tasks.colorLabel', { color })" :aria-pressed="props.modelColor === color" @click="selectColor(color)" />
      </div>
      <label class="custom-color">{{ t('tasks.customColor') }} <input type="color" :value="props.modelColor" @input="selectColor(($event.target as HTMLInputElement).value)" /></label>
    </div>
  </div>
</template>

<style scoped>
.category-icon-picker { overflow: hidden; border: 1px solid var(--color-border); border-radius: 10px; background: var(--color-bg); }
.picker-tabs { display: flex; border-bottom: 1px solid var(--color-border); background: var(--color-bg-secondary); }
.picker-tabs button { flex: 1; border: 0; padding: 7px 10px; color: var(--color-text-tertiary); background: transparent; cursor: pointer; font-size: 11px; }
.picker-tabs button.active { color: var(--color-primary); box-shadow: inset 0 -2px 0 var(--color-primary); }
.picker-content { max-height: 220px; overflow-y: auto; padding: 10px; }
.picker-search { width: 100%; box-sizing: border-box; margin-bottom: 8px; border: 1px solid var(--color-border); border-radius: 7px; padding: 6px 8px; color: var(--color-text-primary); background: var(--color-bg-secondary); outline: none; font-size: 11px; }
.icon-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(32px, 1fr)); gap: 4px; }
.icon-choice, .ascii-choice { display: grid; place-items: center; border: 1px solid transparent; border-radius: 6px; color: var(--color-text-secondary); background: transparent; cursor: pointer; }
.icon-choice { width: 32px; height: 32px; }
.icon-choice:hover, .ascii-choice:hover, .icon-choice.selected, .ascii-choice.selected { border-color: var(--color-primary); color: var(--color-primary); background: var(--color-primary-muted); }
.ascii-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(28px, 1fr)); gap: 4px; }
.ascii-choice { width: 28px; height: 28px; font: 600 13px var(--font-mono, monospace); }
.color-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(28px, 1fr)); gap: 6px; }
.color-choice { width: 28px; height: 28px; border: 2px solid transparent; border-radius: 7px; cursor: pointer; }
.color-choice.selected { border-color: var(--color-text-primary); box-shadow: 0 0 0 2px var(--color-primary); }
.custom-color { display: flex; align-items: center; gap: 8px; margin-top: 12px; color: var(--color-text-tertiary); font-size: 11px; }
.custom-color input { width: 30px; height: 24px; border: 0; padding: 0; background: transparent; cursor: pointer; }
</style>
