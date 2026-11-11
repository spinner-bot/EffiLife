<script setup lang="ts">
import { ref } from 'vue'
import { current } from '../../application/runtime'
import { t } from '../../i18n'
import PageHeader from '../../ui/PageHeader.vue'
import UiButton from '../../ui/UiButton.vue'
import Icon from '../../ui/Icon.vue'
import CategoryEditor from './CategoryEditor.vue'
import CategoryBadge from './CategoryBadge.vue'
const editing = ref<string>(), open = ref(false)
function edit(id?: string) { editing.value = id; open.value = true }
</script>
<template>
  <PageHeader :title="t('settings.categories')" :subtitle="t('category.difficultyHelp')"><UiButton variant="primary" @click="edit()"><Icon name="plus" :size="18" />{{ t('settings.addCategory') }}</UiButton></PageHeader>
  <section class="panel"><div v-for="category in current.categories" :key="category.id" class="list-row"><span class="grow"><CategoryBadge :category-id="category.id" /></span><UiButton variant="ghost" :aria-label="t('common.edit') + ': ' + (category.name || t(category.labelKey!))" @click="edit(category.id)"><Icon name="edit" :size="18" /></UiButton></div></section>
  <CategoryEditor :open="open" :category-id="editing" @close="open = false" />
</template>
