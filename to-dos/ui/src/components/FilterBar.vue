<script setup lang="ts">
import { computed } from 'vue'
import { useTodosStore } from '@/stores/todos'
import { X, ArrowUpDown, Tag, Filter } from 'lucide-vue-next'
import type { Priority, TodoStatus, SortOption } from '@/types'
import { PRIORITY_CONFIG, STATUS_CONFIG } from '@/types'

const store = useTodosStore()

const priorityOptions: { value: Priority; label: string }[] = [
  { value: 'urgent-important', label: '紧急且重要' },
  { value: 'important', label: '重要' },
  { value: 'urgent', label: '紧急' },
  { value: 'normal', label: '普通' },
]

const statusOptions: { value: TodoStatus; label: string }[] = [
  { value: 'pending', label: '待处理' },
  { value: 'in-progress', label: '进行中' },
  { value: 'completed', label: '已完成' },
  { value: 'cancelled', label: '已取消' },
]

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'created_desc', label: '最新创建' },
  { value: 'created_asc', label: '最早创建' },
  { value: 'deadline_asc', label: '截止日期 ↑' },
  { value: 'deadline_desc', label: '截止日期 ↓' },
  { value: 'priority_desc', label: '优先级' },
  { value: 'custom', label: '自定义' },
]

function togglePriority(p: Priority) {
  store.setFilter('priority', store.filters.priority === p ? null : p)
}

function toggleStatus(s: TodoStatus) {
  store.setFilter('status', store.filters.status === s ? null : s)
}

function toggleTag(tag: string) {
  store.toggleTagFilter(tag)
}

function setSort(option: SortOption) {
  store.setSortBy(option)
}

function clearAll() {
  store.clearFilters()
}

const hasFilters = computed(() => {
  return store.filters.priority !== null ||
    store.filters.status !== null ||
    store.filters.category !== null ||
    (store.filters.tags && store.filters.tags.length > 0)
})

const activeFilterCount = computed(() => {
  let count = 0
  if (store.filters.priority !== null) count++
  if (store.filters.status !== null) count++
  if (store.filters.category !== null) count++
  if (store.filters.tags && store.filters.tags.length > 0) count += store.filters.tags.length
  return count
})

// 当前排序标签
const currentSortLabel = computed(() => {
  const opt = sortOptions.find(o => o.value === store.sortBy)
  return opt?.label || '排序'
})
</script>

<template>
  <div class="filter-bar" v-if="hasFilters || store.allTags.length > 0">
    <!-- 筛选区域 -->
    <div class="filter-section">
      <div class="filter-group" v-if="hasFilters">
        <span class="filter-label">
          <Filter :size="12" />
          筛选
        </span>

        <!-- 优先级筛选 -->
        <button
          v-for="opt in priorityOptions"
          :key="opt.value"
          class="filter-chip"
          :class="{ active: store.filters.priority === opt.value }"
          @click="togglePriority(opt.value)"
        >
          <span class="chip-dot" :style="{ background: PRIORITY_CONFIG[opt.value].color }"></span>
          {{ opt.label }}
        </button>

        <div class="filter-divider"></div>

        <!-- 状态筛选 -->
        <button
          v-for="opt in statusOptions"
          :key="opt.value"
          class="filter-chip"
          :class="{ active: store.filters.status === opt.value }"
          @click="toggleStatus(opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>

      <!-- 标签筛选 -->
      <div class="filter-group tags-filter" v-if="store.allTags.length > 0">
        <span class="filter-label">
          <Tag :size="12" />
          标签
        </span>
        <button
          v-for="tag in store.allTags"
          :key="tag"
          class="filter-chip tag-chip"
          :class="{ active: store.filters.tags?.includes(tag) }"
          @click="toggleTag(tag)"
        >
          #{{ tag }}
        </button>
      </div>
    </div>

    <!-- 右侧操作 -->
    <div class="filter-actions">
      <!-- 排序选择 -->
      <div class="sort-dropdown">
        <button class="sort-trigger">
          <ArrowUpDown :size="14" />
          <span>{{ currentSortLabel }}</span>
        </button>
        <div class="sort-menu">
          <button
            v-for="opt in sortOptions"
            :key="opt.value"
            class="sort-item"
            :class="{ active: store.sortBy === opt.value }"
            @click="setSort(opt.value)"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <!-- 清除筛选 -->
      <button v-if="hasFilters" class="clear-btn" @click="clearAll">
        <X :size="14" />
        清除{{ activeFilterCount }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.filter-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--color-text-tertiary);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  min-width: 32px;
}

.filter-divider {
  width: 1px;
  height: 20px;
  background: var(--color-border);
  margin: 0 4px;
}

.filter-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  background: transparent;
  font-size: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.filter-chip:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-border-hover);
}

.filter-chip.active {
  background: var(--color-primary-muted);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.chip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.tag-chip {
  font-size: 11px;
  padding: 3px 8px;
}

/* 右侧操作区 */
.filter-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* 排序下拉 */
.sort-dropdown {
  position: relative;
}

.sort-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: transparent;
  font-size: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.sort-trigger:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-border-hover);
}

.sort-menu {
  display: none;
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  background: var(--color-bg-elevated, var(--color-bg));
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: var(--shadow-lg);
  padding: 4px;
  z-index: 20;
  min-width: 120px;
}

.sort-dropdown:hover .sort-menu {
  display: flex;
  flex-direction: column;
}

.sort-item {
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.1s;
  text-align: left;
}

.sort-item:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.sort-item.active {
  background: var(--color-primary-muted);
  color: var(--color-primary);
}

.clear-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 12px;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.15s;
}

.clear-btn:hover {
  background: var(--color-error-bg);
  color: var(--color-error);
}
</style>
