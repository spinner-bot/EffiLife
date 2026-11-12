<script setup lang="ts">
import { ref } from 'vue'
import { current } from '../../application/runtime'
import { t } from '../../i18n'
import PageHeader from '../../ui/PageHeader.vue'
import UiButton from '../../ui/UiButton.vue'
import Icon from '../../ui/Icon.vue'
import CategoryEditor from './CategoryEditor.vue'
import CategoryIdentity from './CategoryIdentity.vue'
const editing = ref<string>(), open = ref(false)
function edit(id?: string) { editing.value = id; open.value = true }
</script>
<template>
  <PageHeader :title="t('settings.categories')" :subtitle="t('more.categoriesHelp')" back="/more"><UiButton variant="primary" @click="edit()"><Icon name="plus" :size="18" />{{ t('settings.addCategory') }}</UiButton></PageHeader>
  <section class="panel">
    <div v-for="category in current.categories" :key="category.id" class="list-row category-manage-row">
      <span class="grow category-manage-body">
        <span class="cluster category-manage-heading"><CategoryIdentity :category-id="category.id" /><span class="badge">{{ t('category.difficultyLabel') }} {{ category.difficulty }}</span></span>
        <p class="row-detail category-manage-description" :class="{ muted: !category.description }">{{ category.description || t('category.descriptionEmpty') }}</p>
      </span>
      <UiButton variant="ghost" :aria-label="t('common.edit') + ': ' + (category.name || t(category.labelKey!))" @click="edit(category.id)"><Icon name="edit" :size="18" /></UiButton>
    </div>
  </section>
  <CategoryEditor :open="open" :category-id="editing" @close="open = false" />
</template>
<style scoped>
.category-manage-body { display: grid; gap: .35rem; min-width: 0; }.category-manage-heading { gap: .75rem; flex-wrap: wrap; }.category-manage-description { margin: 0; overflow-wrap: anywhere; }
</style>
