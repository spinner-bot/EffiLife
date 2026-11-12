<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { current, dispatch } from '../../application/runtime'
import { planProgress } from '../../domain/plans'
import { planMinutes } from '../../domain/selectors'
import { t, duration } from '../../i18n'
import PageHeader from '../../ui/PageHeader.vue'
import UiButton from '../../ui/UiButton.vue'
import EmptyState from '../../ui/EmptyState.vue'
import Icon from '../../ui/Icon.vue'
import TextEditorDialog from '../../ui/TextEditorDialog.vue'

import CategorySelect from '../categories/CategorySelect.vue'

const categoryId = ref('life')
const router = useRouter()
const creating = ref(false)
watch(creating, open => { if (open) categoryId.value = current.value.categories.find(item => item.id === 'life')?.id || current.value.categories[0]?.id || '' })
const archived = ref(false)
const search = ref('')
const plans = computed(() => current.value.plans.filter(plan => Boolean(plan.archivedAt) === archived.value && plan.title.toLowerCase().includes(search.value.toLowerCase())))
async function create(value: { title: string; description: string }) {
  const result = await dispatch({ type: 'createPlan', ...value, categoryId: categoryId.value })
  await router.push({ name: 'plan', params: { id: result.entityId! } })
}
</script>
<template>
  <PageHeader :title="t('plans.title')" :subtitle="t('plans.subtitle')"><UiButton variant="primary" @click="creating = true"><Icon name="plus" :size="18" />{{ t('plans.create') }}</UiButton></PageHeader>
  <div class="cluster spread" style="margin-bottom: var(--space-6)">
    <div class="filter-tabs"><button class="filter-tab" type="button" :aria-pressed="!archived" @click="archived = false">{{ t('plans.active') }}</button><button class="filter-tab" type="button" :aria-pressed="archived" @click="archived = true">{{ t('plans.archived') }}</button></div>
    <label class="field"><span class="sr-only">{{ t('common.search') }}</span><input v-model="search" class="input" type="search" :placeholder="t('common.search')" /></label>
  </div>
  <div v-if="plans.length" class="plan-grid">
    <RouterLink v-for="plan in plans" :key="plan.id" :to="{ name: 'plan', params: { id: plan.id } }" class="panel plan-tile">
      <div class="cluster spread"><span class="row-mark"><Icon name="plans" /></span><Icon name="arrow" :size="18" /></div>
      <div class="stack" style="gap: var(--space-2)"><h2>{{ plan.title }}</h2><p v-if="plan.description" class="muted small">{{ plan.description }}</p></div>
      <div class="stack" style="gap: var(--space-3)"><div class="cluster spread small muted"><span>{{ t('stats.progress', { done: planProgress(plan).completed, total: planProgress(plan).total }) }}</span><span>{{ Math.round(planProgress(plan).percent) }}%</span></div><div class="progress-track"><div class="progress-fill" :style="{ width: planProgress(plan).percent + '%' }" /></div><div class="cluster spread small muted"><span>{{ t('stats.logs', { count: plan.logs.length }) }}</span><span>{{ duration(planMinutes(current, plan)) }}</span></div></div>
    </RouterLink>
  </div>
  <section v-else class="panel"><EmptyState :title="archived ? t('common.empty') : t('home.emptyPlansTitle')" :description="archived ? undefined : t('home.emptyPlansBody')" icon="plans"><UiButton v-if="!archived" variant="primary" @click="creating = true"><Icon name="plus" :size="18" />{{ t('plans.create') }}</UiButton></EmptyState></section>
  <TextEditorDialog :open="creating" :title="t('plans.createTitle')" :save="create" @close="creating = false"><label class="field"><span>{{ t('plans.defaultCategory') }}</span><CategorySelect v-model="categoryId" :aria-label="t('plans.defaultCategory')" required /><span class="small muted">{{ t('plans.defaultHelp') }}</span></label></TextEditorDialog>
</template>

