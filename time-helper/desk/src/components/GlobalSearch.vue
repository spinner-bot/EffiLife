<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, ClipboardList, Clock3, ListTodo, Search, X } from 'lucide-vue-next'
import { useI18n } from '@/i18n'
import { getAll, STORE_NAMES } from '@/storage'
import { TodoService, type UnifiedTodo } from '@/services/todoService'
import { getPlanTasks, listPlanSummaries, type PlanSummary, type PlanTaskSummary } from '@/services/planGateway'
import type { TimeRecord } from '@/types'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: [] }>()
const router = useRouter()
const { t } = useI18n()
const query = ref('')
const isLoading = ref(false)
const input = ref<HTMLInputElement | null>(null)
const todos = ref<UnifiedTodo[]>([])
const plans = ref<PlanSummary[]>([])
const planTasks = ref<Array<{ plan: PlanSummary; task: PlanTaskSummary }>>([])
const records = ref<TimeRecord[]>([])
const selectedIndex = ref(0)
let searchRequestId = 0

type SearchResult = {
  id: string
  kind: 'todo' | 'plan' | 'planTask' | 'record'
  title: string
  detail: string
  searchText: string
  route: string
}

const allResults = computed<SearchResult[]>(() => [
  ...todos.value.map((todo) => ({
    id: `todo:${todo.id}`,
    kind: 'todo' as const,
    title: todo.title,
    detail: todo.description || todo.tags?.join(', ') || todo.deadline || t('search.todoDetail'),
    searchText: `${todo.description || ''} ${(todo.tags || []).join(' ')}`,
    route: `/tasks?todo=${encodeURIComponent(todo.id)}`,
  })),
  ...plans.value.map((plan) => ({
    id: `plan:${plan.id}`,
    kind: 'plan' as const,
    title: plan.name,
    detail: t('search.planDetail'),
    searchText: '',
    route: `/plans?plan=${encodeURIComponent(String(plan.id))}`,
  })),
  ...planTasks.value.map(({ plan, task }) => ({
    id: `plan-task:${plan.id}:${task.internal_id}`,
    kind: 'planTask' as const,
    title: task.content,
    detail: `${t('search.planTaskDetail')} · ${plan.name} · ${task.display_id}`,
    searchText: `${task.content} ${plan.name} ${task.display_id}`,
    route: `/plans?plan=${encodeURIComponent(String(plan.id))}&task=${encodeURIComponent(task.internal_id)}`,
  })),
  ...records.value.map((record, index) => ({
    id: `record:${record.id || `${record.date}-${index}`}`,
    kind: 'record' as const,
    title: record.content || record.tag,
    detail: `${record.date} · ${record.tag}`,
    searchText: `${record.content} ${record.tag}`,
    route: `/day/${record.date}?record=${encodeURIComponent(record.id || `${record.date}-${index}`)}`,
  })),
])

const filteredResults = computed(() => {
  const normalized = query.value.trim().toLocaleLowerCase()
  if (!normalized) return []
  return allResults.value
    .filter((result) => `${result.title} ${result.detail} ${result.searchText}`.toLocaleLowerCase().includes(normalized))
    .map((result, index) => {
      const title = result.title.toLocaleLowerCase()
      const detail = result.detail.toLocaleLowerCase()
      const searchText = result.searchText.toLocaleLowerCase()
      const score = title === normalized ? 1000
        : title.startsWith(normalized) ? 800
          : title.includes(normalized) ? 600
            : detail.includes(normalized) ? 400
              : searchText.includes(normalized) ? 200 : 0
      return { result, score, index }
    })
    .sort((left, right) => right.score - left.score || left.index - right.index)
    .map(({ result }) => result)
    .slice(0, 12)
})

watch(query, () => {
  selectedIndex.value = 0
})

async function loadPlanTaskIndex(planList: PlanSummary[], requestId: number) {
  if (planList.length === 0) {
    planTasks.value = []
    return
  }
  const taskResults = await Promise.allSettled(planList.map(async (plan) => {
    const tasks = await getPlanTasks(plan.id)
    return tasks.map((task) => ({ plan, task }))
  }))
  if (requestId !== searchRequestId) return
  planTasks.value = taskResults.flatMap((result) => result.status === 'fulfilled' ? result.value : [])
}

async function loadIndex() {
  const requestId = ++searchRequestId
  isLoading.value = true
  try {
    const [todoResult, planResult, recordResult] = await Promise.allSettled([
      TodoService.list(),
      listPlanSummaries(),
      getAll<TimeRecord[]>(STORE_NAMES.RECORDS),
    ])
    if (requestId !== searchRequestId) return
    todos.value = todoResult.status === 'fulfilled' ? todoResult.value : []
    plans.value = planResult.status === 'fulfilled' ? planResult.value : []
    planTasks.value = []
    records.value = recordResult.status === 'fulfilled' ? recordResult.value.flat() : []
    // Keep the primary index usable even when the plan service is slow or offline.
    void loadPlanTaskIndex(plans.value, requestId)
  } finally {
    if (requestId === searchRequestId) isLoading.value = false
  }
}

function close() {
  emit('close')
}

function openResult(result: SearchResult) {
  close()
  router.push(result.route)
}

function resultDomId(result: SearchResult): string {
  return `search-result-${result.id.replace(/[^a-zA-Z0-9_-]/g, '-')}`
}

function handleSearchKeydown(event: KeyboardEvent) {
  const count = filteredResults.value.length
  if (event.key === 'ArrowDown' && count > 0) {
    event.preventDefault()
    selectedIndex.value = (selectedIndex.value + 1) % count
  } else if (event.key === 'ArrowUp' && count > 0) {
    event.preventDefault()
    selectedIndex.value = (selectedIndex.value - 1 + count) % count
  } else if (event.key === 'Enter' && count > 0) {
    event.preventDefault()
    openResult(filteredResults.value[selectedIndex.value])
  }
}

watch(() => props.open, async (open) => {
  if (!open) return
  query.value = ''
  selectedIndex.value = 0
  await loadIndex()
  await nextTick()
  input.value?.focus()
})
</script>

<template>
  <div v-if="open" class="search-backdrop" @click.self="close">
    <section class="search-dialog theme-card" role="dialog" aria-modal="true" :aria-label="t('search.title')" @keydown.esc="close">
      <header class="search-header">
        <div class="search-heading"><Search :size="18" /><strong>{{ t('search.title') }}</strong></div>
        <button class="search-close" type="button" :aria-label="t('search.close')" @click="close"><X :size="17" /></button>
      </header>
      <input ref="input" v-model="query" class="search-input" type="search" role="combobox" :aria-expanded="filteredResults.length > 0" aria-controls="global-search-results" :aria-activedescendant="filteredResults.length ? resultDomId(filteredResults[selectedIndex]) : undefined" :placeholder="t('search.placeholder')" :aria-label="t('search.placeholder')" @keydown="handleSearchKeydown" />
      <div v-if="isLoading" class="search-state">{{ t('search.loading') }}</div>
      <div v-else-if="query.trim() && filteredResults.length === 0" class="search-state">{{ t('search.empty') }}</div>
      <div v-else-if="!query.trim()" class="search-state search-hint">{{ t('search.hint') }}</div>
      <div v-else id="global-search-results" class="search-results" role="listbox" :aria-label="t('search.results')">
        <button v-for="(result, index) in filteredResults" :id="resultDomId(result)" :key="result.id" class="search-result" :class="{ selected: selectedIndex === index }" type="button" role="option" :aria-selected="selectedIndex === index" @click="openResult(result)">
          <span class="search-result-icon">
            <ListTodo v-if="result.kind === 'todo'" :size="16" />
            <ClipboardList v-else-if="result.kind === 'plan' || result.kind === 'planTask'" :size="16" />
            <Clock3 v-else :size="16" />
          </span>
          <span class="search-result-copy"><strong>{{ result.title }}</strong><small>{{ result.detail }}</small></span>
          <ArrowRight :size="15" class="search-result-arrow" />
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.search-backdrop { position: fixed; inset: 0; z-index: 20; display: grid; place-items: start center; padding: 12vh 18px 24px; background: rgba(8, 12, 24, .42); backdrop-filter: blur(8px); }
.search-dialog { width: min(620px, 100%); overflow: hidden; border: 1px solid var(--color-border); border-radius: 18px; box-shadow: 0 24px 70px rgba(0, 0, 0, .24); }
.search-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px 10px; }
.search-heading { display: inline-flex; align-items: center; gap: 8px; color: var(--color-text-primary); }
.search-close { display: grid; place-items: center; border: 0; border-radius: 8px; padding: 5px; color: var(--color-text-tertiary); background: transparent; cursor: pointer; }
.search-close:hover { color: var(--color-text-primary); background: var(--color-primary-muted); }
.search-input { width: calc(100% - 32px); box-sizing: border-box; margin: 0 16px 12px; border: 1px solid var(--color-border); border-radius: 11px; padding: 11px 13px; outline: 0; color: var(--color-text-primary); background: var(--color-bg-secondary); font-size: 14px; }
.search-input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-muted); }
.search-state { padding: 28px 18px 32px; color: var(--color-text-tertiary); text-align: center; font-size: 13px; }
.search-hint { border-top: 1px solid var(--color-border); }
.search-results { display: grid; max-height: min(55vh, 440px); overflow-y: auto; padding: 2px 8px 10px; }
.search-result { display: flex; align-items: center; gap: 10px; border: 0; border-radius: 11px; padding: 10px 9px; color: var(--color-text-primary); background: transparent; text-align: left; cursor: pointer; }
.search-result:hover, .search-result:focus-visible, .search-result.selected { outline: 0; background: var(--color-primary-muted); }
.search-result-icon { display: grid; place-items: center; width: 29px; height: 29px; flex: 0 0 29px; border-radius: 9px; color: var(--color-primary); background: var(--color-bg-secondary); }
.search-result-copy { display: grid; min-width: 0; gap: 3px; flex: 1; }
.search-result-copy strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; }
.search-result-copy small { overflow: hidden; color: var(--color-text-tertiary); text-overflow: ellipsis; white-space: nowrap; font-size: 11px; }
.search-result-arrow { color: var(--color-text-tertiary); }
</style>
