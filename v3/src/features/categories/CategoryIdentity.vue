<script setup lang="ts">
import { computed } from 'vue'
import { current } from '../../application/runtime'
import { categoryName } from '../../i18n'
const props = defineProps<{ categoryId: string }>()
const category = computed(() => current.value.categories.find(item => item.id === props.categoryId))
</script>
<template>
  <span v-if="category" class="category-identity" :style="{ '--category-color': category.color }"><i class="identity-dot" />{{ categoryName(category) }}</span>
</template>
<style scoped>
.category-identity { display: inline-flex; align-items: center; gap: .55rem; min-width: 0; font-weight: 700; font-size: 1.02rem; line-height: 1.5; color: var(--ink); }
.identity-dot { flex: 0 0 auto; width: .8rem; height: .8rem; border-radius: 50%; background: var(--category-color); box-shadow: 0 0 0 3px color-mix(in srgb, var(--category-color) 22%, transparent); }
</style>
