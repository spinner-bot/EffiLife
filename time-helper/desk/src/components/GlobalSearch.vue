<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, ClipboardList, Clock3, ListTodo, Search, X } from 'lucide-vue-next'
import { useI18n } from '@/i18n'
import { getRawAll, STORE_NAMES } from '@/storage'
import { TodoService, type UnifiedTodo } from '@/services/todoService'
import { listPlanSummaries, type PlanSummary } from '@/services/planGateway'
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
const records = ref<TimeRecord[]>([])

type SearchResult = {
  id: string
  kind: 'todo' | 'plan' | 'record'
  title: string
  detail: string
  route: string
}

const allResults = computed<SearchResult[]>(() => [
  ...todos.value.map((todo) => ({
    id: `todo:${todo.id}`,
    kind: 'todo' as const,
    title: todo.title,
    detail: todo.deadline || t('search.todoDetail'),
    route: `/tasks?todo=${encodeURIComponent(todo.id)}`,
  })),
  ...plans.value.map((plan) => ({
    id: `plan:${plan.id}`,
    kind: 'plan' as const,
    title: plan.name,
    detail: t('search.planDetail'),
    route: `/plans?plan=${encodeURIComponent(String(plan.id))}`,
  })),
  ...records.value.map((record, index) => ({
    id: `record:${record.id || `${record.date}-${index}`}`,
    kind: 'record' as const,
    title: record.content || record.tag,
    detail: `${record.date} · ${record.tag}`,
    route: `/day/${record.date}`,
  })),
])

const filteredResults = computed(() => {
  const normalized = query.value.trim().toLocaleLowerCase()
  if (!normalized) return []
  return allResults.value
    .filter((result) => `${result.title} ${result.detail}`.toLocaleLowerCase().includes(normalized))
    .slice(0, 12)
})

async function loadIndex() {
  isLoading.value = true
  try {
    const [todoResult, planResult, recordResult] = await Promise.allSettled([
      TodoService.list(),
      listPlanSummaries(),
      getRawAll<TimeRecord[]>(STORE_NAMES.RECORDS),
    ])
    todos.value = todoResult.status === 'fulfilled' ? todoResult.value : []
    plans.value = planResult.status === 'fulfilled' ? planResult.value : []
    records.value = recordResult.status === 'fulfilled' ? recordResult.value.flat() : []
  } finally {
    isLoading.value = false
  }
}

function close() {
  emit('close')
}

function openResult(result: SearchResult) {
  close()
  router.push(result.route)
}

watch(() => props.open, async (open) => {
  if (!open) return
  query.value = ''
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
      <input ref="input" v-model="query" class="search-input" type="search" :placeholder="t('search.placeholder')" :aria-label="t('search.placeholder')" />
      <div v-if="isLoading" class="search-state">{{ t('search.loading') }}</div>
      <div v-else-if="query.trim() && filteredResults.length === 0" class="search-state">{{ t('search.empty') }}</div>
      <div v-else-if="!query.trim()" class="search-state search-hint">{{ t('search.hint') }}</div>
      <div v-else class="search-results">
        <button v-for="result in filteredResults" :key="result.id" class="search-result" type="button" @click="openResult(result)">
          <span class="search-result-icon">
            <ListTodo v-if="result.kind === 'todo'" :size="16" />
            <ClipboardList v-else-if="result.kind === 'plan'" :size="16" />
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
.search-result:hover, .search-result:focus-visible { outline: 0; background: var(--color-primary-muted); }
.search-result-icon { display: grid; place-items: center; width: 29px; height: 29px; flex: 0 0 29px; border-radius: 9px; color: var(--color-primary); background: var(--color-bg-secondary); }
.search-result-copy { display: grid; min-width: 0; gap: 3px; flex: 1; }
.search-result-copy strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; }
.search-result-copy small { overflow: hidden; color: var(--color-text-tertiary); text-overflow: ellipsis; white-space: nowrap; font-size: 11px; }
.search-result-arrow { color: var(--color-text-tertiary); }
</style>
