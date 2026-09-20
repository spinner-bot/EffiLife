<script setup lang="ts">
import { useTodosStore } from '@/stores/todos'
import { X } from 'lucide-vue-next'
import type { Priority, TodoStatus } from '@/types'
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

function togglePriority(p: Priority) {
  store.setFilter('priority', store.filters.priority === p ? null : p)
}

function toggleStatus(s: TodoStatus) {
  store.setFilter('status', store.filters.status === s ? null : s)
}

function clearAll() {
  store.clearFilters()
}

const hasFilters = () => {
  return store.filters.priority !== null ||
    store.filters.status !== null ||
    store.filters.category !== null
}
</script>

<template>
  <div class="filter-bar" v-if="hasFilters()">
    <div class="filter-section">
      <span class="filter-label">筛选:</span>

      <!-- 优先级筛选 -->
      <div class="filter-group">
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
      </div>

      <div class="filter-divider"></div>

      <!-- 状态筛选 -->
      <div class="filter-group">
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
    </div>

    <button class="clear-btn" @click="clearAll">
      <X :size="14" />
      清除筛选
    </button>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-bottom: 16px;
}

.filter-section {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
  font-weight: 500;
}

.filter-group {
  display: flex;
  gap: 4px;
}

.filter-divider {
  width: 1px;
  height: 20px;
  background: var(--color-border);
}

.filter-chip {
  display: flex;
  align-items: center;
  gap: 6px;
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
  background: rgba(99, 102, 241, 0.08);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.chip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.clear-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 12px;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.15s;
}

.clear-btn:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-secondary);
}
</style>
