<script setup lang="ts">
import { computed } from 'vue'
import { useTodosStore } from '@/stores/todos'
import TodoItem from './TodoItem.vue'
import { Inbox, CheckCircle2 } from 'lucide-vue-next'

const store = useTodosStore()

const emit = defineEmits<{
  (e: 'edit', id: string): void
}>()

// 将待办按状态分组
const pendingTodos = computed(() =>
  store.filteredTodos.filter(t => t.status === 'pending' || t.status === 'in-progress')
)

const completedTodos = computed(() =>
  store.filteredTodos.filter(t => t.status === 'completed')
)

const hasAny = computed(() => store.filteredTodos.length > 0)
</script>

<template>
  <div class="todo-list">
    <!-- 空状态 -->
    <div v-if="!hasAny" class="empty-state">
      <Inbox :size="48" class="empty-icon" />
      <h3 class="empty-title">暂无待办</h3>
      <p class="empty-desc">点击"新建待办"或按 N 键创建第一个待办事项</p>
    </div>

    <!-- 待处理列表 -->
    <div v-if="pendingTodos.length > 0" class="list-section">
      <div class="section-header">
        <span class="section-title">待处理</span>
        <span class="section-count">{{ pendingTodos.length }}</span>
      </div>
      <div class="section-items">
        <TodoItem
          v-for="todo in pendingTodos"
          :key="todo.id"
          :todo="todo"
          @edit="emit('edit', $event)"
        />
      </div>
    </div>

    <!-- 已完成列表 -->
    <div v-if="completedTodos.length > 0" class="list-section">
      <div class="section-header">
        <CheckCircle2 :size="16" class="section-icon" />
        <span class="section-title">已完成</span>
        <span class="section-count">{{ completedTodos.length }}</span>
      </div>
      <div class="section-items">
        <TodoItem
          v-for="todo in completedTodos"
          :key="todo.id"
          :todo="todo"
          @edit="emit('edit', $event)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.todo-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.empty-icon {
  color: var(--color-text-tertiary);
  opacity: 0.3;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

/* 列表分组 */
.list-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 4px;
}

.section-icon {
  color: var(--color-text-tertiary);
}

.section-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.section-count {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  background: var(--color-bg-secondary);
  padding: 1px 6px;
  border-radius: 10px;
}

.section-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
