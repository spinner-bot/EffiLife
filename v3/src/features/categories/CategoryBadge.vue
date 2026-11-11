<script setup lang="ts">
import { computed } from 'vue'
import { current } from '../../application/runtime'
import { categoryName } from '../../i18n'
const props = defineProps<{ categoryId: string }>()
const category = computed(() => current.value.categories.find(item => item.id === props.categoryId))
</script>
<template><span v-if="category" class="category-badge" :style="{ '--category-color': category.color }">{{ categoryName(category) }}</span></template>
<style scoped>
.category-badge { display: inline-flex; align-items: center; flex: 0 0 auto; max-width: 12rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: .72rem; font-weight: 550; line-height: 1.6; padding: .08rem .5rem; border-radius: .45rem; border: 1px solid color-mix(in srgb, var(--category-color) 65%, transparent); background: color-mix(in srgb, var(--category-color) 16%, transparent); color: var(--ink); vertical-align: middle; margin-inline-end: .45rem; }
</style>
