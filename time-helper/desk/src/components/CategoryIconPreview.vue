<script setup lang="ts">
import { computed } from 'vue'
import { categoryIconRegistry } from './categoryIcons'
import { Circle } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  name?: string
  ascii?: string
  size?: number
}>(), {
  size: 14,
})

const iconComponent = computed(() => categoryIconRegistry[props.name || ''] || Circle)
</script>

<template>
  <span class="category-icon-preview" :aria-label="name || ascii || 'category'">
    <span v-if="ascii" class="category-icon-ascii">{{ ascii }}</span>
    <component :is="iconComponent" v-else :size="size" :stroke-width="2" />
  </span>
</template>

<style scoped>
.category-icon-preview { display: inline-grid; place-items: center; width: 20px; height: 20px; flex: 0 0 20px; border-radius: 6px; color: var(--category-color, var(--color-primary)); background: color-mix(in srgb, var(--category-color, var(--color-primary)) 14%, transparent); }
.category-icon-ascii { font: 700 12px var(--font-mono, monospace); line-height: 1; }
</style>
