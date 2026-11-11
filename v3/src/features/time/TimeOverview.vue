<script setup lang="ts">
import { computed } from 'vue'
import { current } from '../../application/runtime'
import { daySummary } from '../../domain/selectors'
import { categoryName, duration, t } from '../../i18n'
const props = defineProps<{ date: string }>()
const summary = computed(() => daySummary(current.value, props.date))
const circumference = 2 * Math.PI * 68
const arcs = computed(() => {
  let offset = 0
  const total = summary.value.categories.reduce((sum, item) => sum + item.minutes, 0)
  const denominator = Math.max(summary.value.dayMinutes, total)
  return summary.value.categories.map(item => {
    const length = item.minutes / denominator * circumference
    const arc = { ...item, length, offset }
    offset += length
    return arc
  })
})
</script>
<template>
  <div class="time-overview">
    <div class="time-ring" role="img" :aria-label="t('stats.recorded') + ': ' + duration(summary.total)">
      <svg viewBox="0 0 160 160" aria-hidden="true">
        <circle cx="80" cy="80" r="68" fill="none" stroke="var(--subtle)" stroke-width="12" />
        <circle v-for="arc in arcs" :key="arc.category.id" cx="80" cy="80" r="68" fill="none" :stroke="arc.category.color" stroke-width="12" :stroke-dasharray="arc.length + ' ' + circumference" :stroke-dashoffset="-arc.offset" />
      </svg>
      <div class="ring-center"><span class="ring-value">{{ duration(summary.total) }}</span><span class="small muted">{{ t('stats.recorded') }}</span></div>
    </div>
    <div class="stack">
      <div v-for="item in summary.categories" :key="item.category.id" class="category-row"><span class="category-label"><i class="color-dot" :style="{ background: item.category.color }" />{{ categoryName(item.category) }}</span><span>{{ duration(item.minutes) }}</span></div>
      <div v-if="!summary.categories.length" class="stack"><h3>{{ t('home.emptyRecordsTitle') }}</h3><p class="muted small">{{ t('home.emptyRecordsBody') }}</p></div>
      <div class="category-row muted"><span>{{ t('home.notRecorded') }}</span><span>{{ duration(Math.max(0, summary.dayMinutes - summary.total)) }}</span></div>
    </div>
  </div>
</template>

