<script setup lang="ts">
import { computed } from 'vue'
import { useTodosStore } from '@/stores/todos'
import TodoItem from './TodoItem.vue'
import { Inbox, CheckCircle2, ClipboardList, Sparkles } from 'lucide-vue-next'

const store = useTodosStore()

const emit = defineEmits<{
  (e: 'edit', id: string): void
  (e: 'delete', id: string): void
  (e: 'archive', id: string): void
}>()

// 将待办按状态分组
const pendingTodos = computed(() =>
  store.filteredTodos.filter(t => t.status === 'pending' || t.status === 'in-progress')
)

const completedTodos = computed(() =>
  store.filteredTodos.filter(t => t.status === 'completed')
)

const hasAny = computed(() => store.filteredTodos.length > 0)
const hasActive = computed(() => pendingTodos.value.length > 0)
const hasCompleted = computed(() => completedTodos.value.length > 0)

const searchQuery = computed(() => store.filters.search)

function handleDelete(id: string) {
  store.deleteTodo(id)
}

function handleArchive(id: string) {
  store.deleteTodo(id)
}
</script>

<template>
  <div class="todo-list">
    <!-- 空状态 -->
    <Transition name="fade" mode="out-in">
      <div v-if="!hasAny" key="empty" class="empty-state">
        <div class="empty-illustration">
          <div class="empty-circle">
            <Inbox :size="36" class="empty-icon" />
          </div>
          <Sparkles :size="16" class="empty-sparkle" />
        </div>
        <h3 class="empty-title">暂无待办事项</h3>
        <p class="empty-desc">一切就绪！点击下方按钮或按 <kbd>N</kbd> 键创建第一个待办</p>
        <div class="empty-tips">
          <div class="tip">
            <ClipboardList :size="14" />
            <span>使用分类和标签组织待办</span>
          </div>
          <div class="tip">
            <CheckCircle2 :size="14" />
            <span>设置截止日期跟踪进度</span>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 待处理列表 -->
    <div v-if="hasActive" class="list-section">
      <div class="section-header">
        <span class="section-title">待处理</span>
        <span class="section-count">{{ pendingTodos.length }}</span>
      </div>
      <TransitionGroup name="list" tag="div" class="section-items">
        <TodoItem
          v-for="todo in pendingTodos"
          :key="todo.id"
          :todo="todo"
          :search-query="searchQuery"
          @edit="emit('edit', $event)"
          @delete="handleDelete"
          @archive="handleArchive"
        />
      </TransitionGroup>
    </div>

    <!-- 已完成列表 -->
    <Transition name="slide-up">
      <div v-if="hasCompleted" class="list-section completed-section">
        <div class="section-header">
          <CheckCircle2 :size="16" class="section-icon" />
          <span class="section-title">已完成</span>
          <span class="section-count">{{ completedTodos.length }}</span>
        </div>
        <TransitionGroup name="list" tag="div" class="section-items">
          <TodoItem
            v-for="todo in completedTodos"
            :key="todo.id"
            :todo="todo"
            :search-query="searchQuery"
            @edit="emit('edit', $event)"
            @delete="handleDelete"
            @archive="handleArchive"
          />
        </TransitionGroup>
      </div>
    </Transition>
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
  padding: 80px 24px;
  text-align: center;
}

.empty-illustration {
  position: relative;
  margin-bottom: 24px;
}

.empty-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--color-bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed var(--color-border);
}

.empty-icon {
  color: var(--color-text-tertiary);
  opacity: 0.5;
}

.empty-sparkle {
  position: absolute;
  top: -4px;
  right: -8px;
  color: var(--color-primary);
  opacity: 0.6;
  animation: sparkleRotate 8s linear infinite;
}

@keyframes sparkleRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 13px;
  color: var(--color-text-tertiary);
  max-width: 280px;
  line-height: 1.6;
}

.empty-desc kbd {
  display: inline-block;
  padding: 1px 6px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 11px;
  font-family: var(--font-mono, monospace);
  color: var(--color-text-secondary);
}

.empty-tips {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 24px;
  padding: 16px 20px;
  background: var(--color-bg-secondary);
  border-radius: 10px;
  border: 1px solid var(--color-border-subtle);
}

.tip {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.tip svg {
  color: var(--color-primary);
  opacity: 0.7;
}

/* 列表分组 */
.list-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.completed-section {
  opacity: 0.7;
}

.completed-section:hover {
  opacity: 1;
  transition: opacity 0.3s;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 4px;
}

.section-icon {
  color: var(--color-success);
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
