<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, ClipboardList, Clock3, ListTodo, Search, X } from 'lucide-vue-next'
import { useI18n } from '@/i18n'
import { getAll, STORE_NAMES } from '@/storage'
import { TodoService, type UnifiedTodo } from '@/services/todoService'
import { getPlanTasks, listPlanArchives, listPlanSummaries, planArchivesState, type PlanArchiveSummary, type PlanSummary, type PlanTaskSummary } from '@/services/planGateway'
import { onWorkspaceChanged } from '@/services/workspaceEvents'
import type { TimeRecord } from '@/types'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: [] }>()
const router = useRouter()
const { t } = useI18n()
const query = ref('')
const isLoading = ref(false)
const indexUnavailable = ref(false)
const indexPartial = ref(false)
const input = ref<HTMLInputElement | null>(null)
const dialog = ref<HTMLElement | null>(null)
const todos = ref<UnifiedTodo[]>([])
const plans = ref<PlanSummary[]>([])
const archivedPlans = ref<PlanArchiveSummary[]>([])
const planTasks = ref<Array<{ plan: PlanSummary; task: PlanTaskSummary }>>([])
const records = ref<TimeRecord[]>([])
const selectedIndex = ref(0)
let searchRequestId = 0
let returnFocus: HTMLElement | null = null

type SearchResult = {
  id: string
  kind: 'todo' | 'plan' | 'archivedPlan' | 'planTask' | 'record'
  title: string
  detail: string
  searchText: string
  route: string
}

type SearchFilter = 'all' | 'th' | 'ph' | 'td'

const searchFilter = ref<SearchFilter>('all')

function resultMatchesFilter(result: SearchResult): boolean {
  if (searchFilter.value === 'all') return true
  if (searchFilter.value === 'th') return result.kind === 'record'
  if (searchFilter.value === 'td') return result.kind === 'todo'
  return result.kind === 'plan' || result.kind === 'planTask' || result.kind === 'archivedPlan'
}

function todoSearchDetail(todo: UnifiedTodo): string {
  const planContext = todo.related_plan_id && todo.related_plan_task_id
    ? `${t('search.todoPlanContext')} ${todo.related_plan_id} · ${todo.related_plan_task_id}`
    : ''
  return [todo.description || todo.tags?.join(', ') || todo.deadline || t('search.todoDetail'), planContext]
    .filter(Boolean)
    .join(` ${t('search.detailSeparator')} `)
}

function searchModuleLabel(kind: SearchResult['kind']): string {
  return t({
    todo: 'search.module.todo',
    plan: 'search.module.plan',
    archivedPlan: 'search.module.archivedPlan',
    planTask: 'search.module.planTask',
    record: 'search.module.record',
  }[kind])
}

function linkedTodoTitle(record: TimeRecord): string {
  if (!record.todo_id) return ''
  return todos.value.find((todo) => todo.id === record.todo_id)?.title || ''
}

const allResults = computed<SearchResult[]>(() => [
  ...todos.value.map((todo) => ({
    id: `todo:${todo.id}`,
    kind: 'todo' as const,
    title: todo.title,
    detail: todoSearchDetail(todo),
    searchText: `${todo.description || ''} ${(todo.tags || []).join(' ')} ${todo.related_plan_id || ''} ${todo.related_plan_task_id || ''}`,
    route: `/tasks?todo=${encodeURIComponent(todo.id)}`,
  })),
  ...plans.value.map((plan) => ({
    id: `plan:${plan.id}`,
    kind: 'plan' as const,
    title: plan.name,
    detail: t('search.planDetail'),
    searchText: `${plan.name} ${plan.id} ${plan.date?.join('-') || ''}`,
    route: `/plans?plan=${encodeURIComponent(String(plan.id))}`,
  })),
  ...archivedPlans.value.map((plan) => ({
    id: `archived-plan:${plan.file}`,
    kind: 'archivedPlan' as const,
    title: plan.name || plan.file,
    detail: t('search.archivedPlanDetail'),
    searchText: `${plan.name || ''} ${plan.plan_id || ''} ${plan.file}`,
    route: `/plans?archive=${encodeURIComponent(plan.file)}`,
  })),
  ...archivedPlans.value.flatMap((plan) => (plan.tasks || []).map((task) => ({
    id: `archived-plan-task:${plan.file}:${task.internal_id}`,
    kind: 'planTask' as const,
    title: task.content,
    detail: `${t('search.planTaskDetail')} ${t('search.detailSeparator')} ${plan.name || plan.file} ${t('search.detailSeparator')} ${task.display_id} ${t('search.detailSeparator')} ${t('search.archivedPlanDetail')}`,
    searchText: `${task.content} ${plan.name || ''} ${task.display_id} ${plan.file}`,
    route: `/plans?archive=${encodeURIComponent(plan.file)}&task=${encodeURIComponent(task.internal_id)}`,
  }))),
  ...planTasks.value.map(({ plan, task }) => ({
    id: `plan-task:${plan.id}:${task.internal_id}`,
    kind: 'planTask' as const,
    title: task.content,
    detail: `${t('search.planTaskDetail')} ${t('search.detailSeparator')} ${plan.name} ${t('search.detailSeparator')} ${task.display_id}`,
    searchText: `${task.content} ${plan.name} ${task.display_id} ${plan.date?.join('-') || ''}`,
    route: `/plans?plan=${encodeURIComponent(String(plan.id))}&task=${encodeURIComponent(task.internal_id)}`,
  })),
  ...records.value.map((record, index) => ({
    id: `record:${record.id || `${record.date}-${index}`}`,
    kind: 'record' as const,
    title: record.content || record.tag,
    detail: `${record.date} ${t('search.detailSeparator')} ${record.tag}${record.todo_id ? ` ${t('search.detailSeparator')} ${record.todo_id}${linkedTodoTitle(record) ? ` ${t('search.detailSeparator')} ${linkedTodoTitle(record)}` : ''}` : ''}`,
    searchText: `${record.content} ${record.tag} ${record.todo_id || ''} ${linkedTodoTitle(record)}`,
    route: `/day/${record.date}?record=${encodeURIComponent(record.id || `${record.date}-${index}`)}`,
  })),
])

const filteredResults = computed(() => {
  const normalized = query.value.trim().toLocaleLowerCase()
  if (!normalized) return []
  return allResults.value
    .filter((result) => resultMatchesFilter(result))
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

watch(
  [selectedIndex, () => filteredResults.value.length],
  async () => {
    await nextTick()
    const result = filteredResults.value[selectedIndex.value]
    if (!result) return
    document.getElementById(resultDomId(result))?.scrollIntoView({ block: 'nearest' })
  },
)

const stopWorkspaceListener = onWorkspaceChanged(() => {
  if (props.open) void loadIndex()
})

function refreshWhenVisible() {
  if (document.visibilityState === 'visible' && props.open) void loadIndex()
}

onMounted(() => document.addEventListener('visibilitychange', refreshWhenVisible))

onBeforeUnmount(() => {
  stopWorkspaceListener()
  document.removeEventListener('visibilitychange', refreshWhenVisible)
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
  // A plan can remain searchable even when its task endpoint is temporarily
  // unavailable, but the index must disclose that task results are partial.
  if (taskResults.some((result) => result.status === 'rejected')) {
    indexPartial.value = true
  }
  planTasks.value = taskResults.flatMap((result) => result.status === 'fulfilled' ? result.value : [])
}

async function loadIndex() {
  const requestId = ++searchRequestId
  isLoading.value = true
  indexUnavailable.value = false
  indexPartial.value = false
  try {
  const [todoResult, planResult, archiveResult, recordResult] = await Promise.allSettled([
      TodoService.list(),
      listPlanSummaries(),
      listPlanArchives(),
      getAll<TimeRecord[]>(STORE_NAMES.RECORDS),
    ])
    if (requestId !== searchRequestId) return
    const archiveUnavailable = archiveResult.status === 'rejected' || planArchivesState.value === 'unavailable'
    const failedSources = [todoResult, planResult, recordResult].filter((result) => result.status === 'rejected').length + (archiveUnavailable ? 1 : 0)
    indexUnavailable.value = failedSources === 4
    indexPartial.value = failedSources > 0
    todos.value = todoResult.status === 'fulfilled' ? todoResult.value : []
    plans.value = planResult.status === 'fulfilled' ? planResult.value : []
    archivedPlans.value = archiveResult.status === 'fulfilled' ? archiveResult.value : []
    planTasks.value = []
    records.value = recordResult.status === 'fulfilled' ? recordResult.value.flat() : []
    // Keep the primary index usable even when the plan service is slow or offline.
    void loadPlanTaskIndex(plans.value, requestId)
  } finally {
    if (requestId === searchRequestId) isLoading.value = false
  }
}

async function retryIndex(): Promise<void> {
  await loadIndex()
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
  } else if (event.key === 'Home' && count > 0) {
    event.preventDefault()
    selectedIndex.value = 0
  } else if (event.key === 'End' && count > 0) {
    event.preventDefault()
    selectedIndex.value = count - 1
  } else if (event.key === 'Enter' && count > 0) {
    event.preventDefault()
    openResult(filteredResults.value[selectedIndex.value])
  }
}

function handleDialogKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.preventDefault()
    close()
    return
  }
  if (event.key !== 'Tab') return
  const focusable = Array.from(dialog.value?.querySelectorAll<HTMLElement>(
    'button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
  ) || [])
  if (focusable.length === 0) return
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(() => props.open, async (open) => {
  if (!open) {
    await nextTick()
    if (returnFocus?.isConnected) returnFocus.focus()
    returnFocus = null
    return
  }
  returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
  query.value = ''
  searchFilter.value = 'all'
  selectedIndex.value = 0
  await loadIndex()
  await nextTick()
  input.value?.focus()
})
</script>

<template>
  <div v-if="open" class="search-backdrop" @click.self="close">
    <section ref="dialog" id="global-search-dialog" class="search-dialog theme-card" role="dialog" aria-modal="true" aria-labelledby="global-search-title" @keydown="handleDialogKeydown">
      <header class="search-header">
        <div class="search-heading"><Search :size="18" /><strong id="global-search-title">{{ t('search.title') }}</strong></div>
        <button class="search-close" type="button" :aria-label="t('search.close')" @click="close"><X :size="17" /></button>
      </header>
      <label class="search-input-label" for="global-search-input">{{ t('search.inputLabel') }}</label>
      <input id="global-search-input" ref="input" v-model="query" class="search-input" type="search" role="combobox" :aria-expanded="filteredResults.length > 0" aria-controls="global-search-results" :aria-activedescendant="filteredResults.length ? resultDomId(filteredResults[selectedIndex]) : undefined" :placeholder="t('search.placeholder')" @keydown="handleSearchKeydown" />
      <div class="search-filters" role="group" :aria-label="t('search.filterLabel')">
        <button v-for="filter in (['all', 'th', 'ph', 'td'] as SearchFilter[])" :key="filter" type="button" class="search-filter" :class="{ selected: searchFilter === filter }" :aria-pressed="searchFilter === filter" @click="searchFilter = filter; selectedIndex = 0">
          {{ t(`search.filter.${filter}`) }}
        </button>
      </div>
      <div v-if="indexUnavailable" class="search-state search-error" role="status" aria-live="polite">
        <span>{{ t('search.unavailable') }}</span>
        <button type="button" @click="retryIndex">{{ t('search.retry') }}</button>
      </div>
      <template v-else>
      <div v-if="indexPartial" class="search-partial" role="status" aria-live="polite">{{ t('search.partial') }} <button type="button" @click="retryIndex">{{ t('search.retry') }}</button></div>
      <div v-if="isLoading" class="search-state">{{ t('search.loading') }}</div>
      <div v-else-if="query.trim() && filteredResults.length === 0" class="search-state">{{ t('search.empty') }}</div>
      <div v-else-if="!query.trim()" class="search-state search-hint">{{ t('search.hint') }}</div>
      <div v-else id="global-search-results" class="search-results" role="listbox" :aria-label="t('search.results')">
        <button v-for="(result, index) in filteredResults" :id="resultDomId(result)" :key="result.id" class="search-result" :class="{ selected: selectedIndex === index }" type="button" role="option" :aria-selected="selectedIndex === index" @click="openResult(result)">
          <span class="search-result-icon">
            <ListTodo v-if="result.kind === 'todo'" :size="16" />
            <ClipboardList v-else-if="result.kind === 'plan' || result.kind === 'archivedPlan' || result.kind === 'planTask'" :size="16" />
            <Clock3 v-else :size="16" />
          </span>
          <span class="search-result-copy"><strong>{{ result.title }}</strong><small>{{ searchModuleLabel(result.kind) }} {{ t('search.detailSeparator') }} {{ result.detail }}</small></span>
          <ArrowRight :size="15" class="search-result-arrow" />
        </button>
      </div>
      </template>
    </section>
  </div>
</template>

<style scoped>
.search-backdrop { position: fixed; inset: 0; z-index: 20; display: grid; place-items: start center; padding: 12vh 18px 24px; background: rgba(8, 12, 24, .42); backdrop-filter: blur(8px); }
.search-dialog { width: min(620px, 100%); overflow: hidden; border: 1px solid var(--color-border); border-radius: 18px; box-shadow: 0 24px 70px rgba(0, 0, 0, .24); }
.search-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px 10px; }
.search-input-label { display: block; margin: 0 16px 5px; color: var(--color-text-secondary); font-size: 11px; font-weight: 700; letter-spacing: .04em; }
.search-heading { display: inline-flex; align-items: center; gap: 8px; color: var(--color-text-primary); }
.search-close { display: grid; place-items: center; border: 0; border-radius: 8px; padding: 5px; color: var(--color-text-tertiary); background: transparent; cursor: pointer; }
.search-close:hover { color: var(--color-text-primary); background: var(--color-primary-muted); }
.search-input { width: calc(100% - 32px); box-sizing: border-box; margin: 0 16px 12px; border: 1px solid var(--color-border); border-radius: 11px; padding: 11px 13px; outline: 0; color: var(--color-text-primary); background: var(--color-bg-secondary); font-size: 14px; }
.search-input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-muted); }
.search-filters { display: flex; gap: 6px; overflow-x: auto; padding: 0 16px 10px; scrollbar-width: none; }
.search-filters::-webkit-scrollbar { display: none; }
.search-filter { min-height: 34px; flex: 0 0 auto; border: 1px solid var(--color-border); border-radius: 999px; padding: 5px 12px; color: var(--color-text-tertiary); background: var(--color-bg-secondary); cursor: pointer; font: inherit; font-size: 11px; font-weight: 650; transition: border-color var(--transition-fast), color var(--transition-fast), background var(--transition-fast); }
.search-filter:hover, .search-filter:focus-visible { border-color: var(--color-border-hover); color: var(--color-text-primary); outline: 0; }
.search-filter.selected { border-color: var(--color-primary); color: var(--color-primary); background: var(--color-primary-muted); }
.search-filter:disabled { cursor: not-allowed; opacity: .55; }
.search-state { padding: 28px 18px 32px; color: var(--color-text-tertiary); text-align: center; font-size: 13px; }
.search-error { display: grid; gap: 10px; color: var(--color-text-secondary); }
.search-error button, .search-partial button { justify-self: center; border: 1px solid var(--color-border); border-radius: 8px; padding: 6px 10px; color: var(--color-primary); background: var(--color-bg-secondary); cursor: pointer; font: inherit; font-size: 12px; font-weight: 650; }
.search-error button:hover, .search-error button:focus-visible, .search-partial button:hover, .search-partial button:focus-visible { border-color: var(--color-primary); outline: 0; }
.search-partial { display: flex; align-items: center; justify-content: center; gap: 8px; border-top: 1px solid var(--color-border); padding: 8px 16px; color: var(--color-text-tertiary); font-size: 11px; }
.search-partial button { justify-self: auto; padding: 4px 8px; font-size: 11px; }
.search-hint { border-top: 1px solid var(--color-border); }
.search-results { display: grid; max-height: min(55vh, 440px); overflow-y: auto; padding: 2px 8px 10px; }
.search-result { display: flex; align-items: center; gap: 10px; border: 0; border-radius: 11px; padding: 10px 9px; color: var(--color-text-primary); background: transparent; text-align: left; cursor: pointer; }
.search-result:hover, .search-result:focus-visible, .search-result.selected { outline: 0; background: var(--color-primary-muted); }
.search-result-icon { display: grid; place-items: center; width: 29px; height: 29px; flex: 0 0 29px; border-radius: 9px; color: var(--color-primary); background: var(--color-bg-secondary); }
.search-result-copy { display: grid; min-width: 0; gap: 3px; flex: 1; }
.search-result-copy strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; }
.search-result-copy small { overflow: hidden; color: var(--color-text-tertiary); text-overflow: ellipsis; white-space: nowrap; font-size: 11px; }
.search-result-arrow { color: var(--color-text-tertiary); }

@media (max-width: 680px) {
  .search-backdrop { place-items: end center; padding: 0; }
  .search-dialog { width: 100%; max-height: calc(100vh - 56px); border-radius: 18px 18px 0 0; padding-bottom: env(safe-area-inset-bottom); }
  .search-close { min-width: 40px; min-height: 40px; }
  .search-filters { padding-right: 16px; }
  .search-results { max-height: 46vh; padding-bottom: 12px; }
  .search-result { min-height: 48px; padding: 10px 9px; }
}
</style>
