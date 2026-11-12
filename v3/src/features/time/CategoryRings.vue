<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { current } from '../../application/runtime'
import { categoryDetails, ringLayout } from '../../domain/time-details'
import { t, duration, categoryName } from '../../i18n'
import CategoryBadge from '../categories/CategoryBadge.vue'
const props = defineProps<{ date: string }>()
const groups = computed(() => categoryDetails(current.value, props.date).map(group => ({ ...group, ...ringLayout(group) })))
const active = ref('')
function centerLabel(target: number, remaining: number) {
  if (!target) return t('stats.recorded')
  return remaining > 0 ? t('time.remaining', { minutes: duration(remaining) }) : t('time.targetMet')
}
</script>
<template>
  <div v-if="groups.length" class="category-rings panel-body" :data-single="groups.length === 1"><section v-for="group in groups" :key="group.category.id" class="category-ring-card" :data-started="group.started" :data-target="group.target"><h3><CategoryBadge :category-id="group.category.id" /></h3><div class="time-ring" role="img" :aria-label="group.started ? categoryName(group.category) + ': ' + duration(group.total) : categoryName(group.category) + ': ' + t('time.notStarted')"><svg viewBox="0 0 160 160" aria-hidden="true"><circle cx="80" cy="80" r="68" fill="none" stroke="var(--subtle)" stroke-width="12" /><circle v-for="segment in group.segments" :key="segment.record.id" cx="80" cy="80" r="68" fill="none" :stroke="segment.color" stroke-width="12" pathLength="100" :stroke-dasharray="segment.length + ' 100'" :stroke-dashoffset="-segment.offset" :opacity="active && active !== segment.record.id ? .3 : 1" @mouseenter="active = segment.record.id" @mouseleave="active = ''"><title>{{ segment.record.title }} · {{ duration(segment.minutes) }}</title></circle></svg><div class="ring-center"><template v-if="group.started"><strong class="ring-value">{{ duration(group.total) }}</strong><span class="small muted">{{ centerLabel(group.target, group.remaining) }}</span></template><strong v-else class="ring-value ring-idle">{{ t('time.notStarted') }}</strong></div></div><div v-if="group.segments.length" class="stack record-legend"><RouterLink v-for="segment in group.segments" :key="segment.record.id" :to="{ name: 'record', params: { id: segment.record.id } }" class="category-row record-legend-link" @mouseenter="active = segment.record.id" @mouseleave="active = ''" @focus="active = segment.record.id" @blur="active = ''"><span class="category-label"><i class="color-dot" :style="{ background: segment.color }" /><span>{{ segment.record.title }}</span></span><span>{{ duration(segment.minutes) }}</span></RouterLink></div><p v-else class="small muted ring-target">{{ t('time.targetLabel', { minutes: duration(group.target) }) }}</p><p v-if="group.overlap > .001" class="small muted">{{ t('time.ringOverlap') }}</p></section></div>
  <div v-else class="panel-body muted small">{{ t('home.emptyRecordsBody') }}</div>
</template>
<style scoped>
.category-rings { display: grid; grid-template-columns: repeat(auto-fit,minmax(min(100%,260px),1fr)); gap: 1.5rem; align-items: start; }.category-ring-card { min-width: 0; display: grid; justify-items: center; gap: 1rem; padding: .5rem; }.record-legend { width: 100%; gap: .5rem; }.record-legend-link { color: var(--ink); text-decoration: none; border-radius: .4rem; padding: .3rem; gap: .75rem; }.record-legend-link:hover,.record-legend-link:focus-visible { background: var(--subtle); }.category-label { min-width: 0; }.category-label span { overflow-wrap: anywhere; }circle { transition: opacity 160ms ease; }.ring-idle { font-size: 1rem; font-weight: 650; }.ring-target { margin: 0; }
.category-rings[data-single="true"] .category-ring-card { grid-template-columns: 180px minmax(0,1fr); grid-template-rows: auto 1fr; gap: .75rem 1.5rem; align-items: center; padding-block: 0; }.category-rings[data-single="true"] .category-ring-card h3 { grid-column: 2; grid-row: 1; justify-self: start; align-self: end; }.category-rings[data-single="true"] .time-ring { grid-column: 1; grid-row: 1 / 3; }.category-rings[data-single="true"] .record-legend { grid-column: 2; grid-row: 2; align-self: start; }.category-rings[data-single="true"] .category-ring-card > p { grid-column: 2; }
@media(max-width: 520px) { .category-rings[data-single="true"] .category-ring-card { grid-template-columns: 1fr; justify-items: center; }.category-rings[data-single="true"] .category-ring-card h3,.category-rings[data-single="true"] .time-ring,.category-rings[data-single="true"] .record-legend,.category-rings[data-single="true"] .category-ring-card > p { grid-column: 1; grid-row: auto; }.category-rings[data-single="true"] .category-ring-card h3 { justify-self: center; } }
</style>
