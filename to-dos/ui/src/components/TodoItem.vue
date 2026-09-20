<script setup lang="ts">
import { computed } from 'vue'
import { useTodosStore } from '@/stores/todos'
import {
  Check, Circle, AlertCircle, Star, Zap,
  ChevronRight, Clock, Calendar as CalendarIcon,
} from 'lucide-vue-next'
import type { Todo } from '@/types'
import { PRIORITY_CONFIG } from '@/types'

const props = defineProps<{
  todo: Todo
}>()

const emit = defineEmits<{
  (e: 'edit', id: string): void
}>()

const store = useTodosStore()

const isCompleted = computed(() => props.todo.status === 'completed')
const isOverdue = computed(() => {
  if (!props.todo.deadline || isCompleted.value || props.todo.status === 'cancelled') return false
  return new Date(props.todo.deadline) < new Date()
})

const deadlineText = computed(() => {
  if (!props.todo.deadline) return ''
  const dl = new Date(props.todo.deadline)
  const now = new Date()
  const diff = dl.getTime() - now.getTime()
  const days = Math.ceil(diff / (1000 * 60 * 60 * 24))

  if (days < 0) return `已逾期 ${Math.abs(days)} 天`
  if (days === 0) return '今天截止'
  if (days === 1) return '明天截止'
  if (days <= 7) return `${days} 天后截止`
  return dl.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
})

const subtaskProgress = computed(() => {
  if (!props.todo.subtasks.length) return null
  const done = props.todo.subtasks.filter(s => s.completed).length
  return { done, total: props.todo.subtasks.length }
})

const category = computed(() => store.getCategoryById(props.todo.category))

function toggleComplete() {
  if (isCompleted.value) {
    store.updateTodo(props.todo.id, { status: 'pending' })
  } else {
    store.completeTodo(props.todo.id)
  }
}
</script>

<template>
  <div
    class="todo-item"
    :class="{
      completed: isCompleted,
      overdue: isOverdue,
      selected: store.selectedIds.has(todo.id),
    }"
    @click="emit('edit', todo.id)"
  >
    <!-- 复选框 -->
    <button
      class="checkbox"
      :class="{ checked: isCompleted }"
      @click.stop="toggleComplete"
      :aria-label="isCompleted ? '取消完成' : '标记完成'"
    >
      <Check v-if="isCompleted" :size="14" />
    </button>

    <!-- 内容区 -->
    <div class="todo-content">
      <div class="todo-header">
        <span class="todo-title">{{ todo.title }}</span>
        <div class="todo-meta">
          <!-- 优先级标记 -->
          <span
            v-if="todo.priority !== 'normal'"
            class="priority-badge"
            :style="{ color: PRIORITY_CONFIG[todo.priority].color }"
            :title="PRIORITY_CONFIG[todo.priority].label"
          >
            <AlertCircle v-if="todo.priority === 'urgent-important'" :size="14" />
            <Star v-else-if="todo.priority === 'important'" :size="14" />
            <Zap v-else-if="todo.priority === 'urgent'" :size="14" />
          </span>

          <!-- 分类标记 -->
          <span
            v-if="category"
            class="category-badge"
            :style="{ background: category.color + '20', color: category.color }"
          >
            {{ category.name }}
          </span>

          <!-- 截止日期 -->
          <span
            v-if="deadlineText"
            class="deadline-badge"
            :class="{ overdue: isOverdue, today: deadlineText === '今天截止' }"
          >
            <CalendarIcon :size="12" />
            {{ deadlineText }}
          </span>
        </div>
      </div>

      <!-- 子任务进度 -->
      <div v-if="subtaskProgress" class="subtask-progress">
        <ChevronRight :size="12" class="progress-icon" />
        <span class="progress-text">
          {{ subtaskProgress.done }}/{{ subtaskProgress.total }} 子任务已完成
        </span>
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: (subtaskProgress.done / subtaskProgress.total * 100) + '%' }"
          ></div>
        </div>
      </div>

      <!-- 标签 -->
      <div v-if="todo.tags.length" class="todo-tags">
        <span v-for="tag in todo.tags" :key="tag" class="tag">#{{ tag }}</span>
      </div>

      <!-- 时间预估 -->
      <div v-if="todo.time_estimate" class="time-estimate">
        <Clock :size="12" />
        <span>{{ todo.time_estimate }}分钟</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.todo-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.todo-item:hover {
  border-color: var(--color-border-hover);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transform: translateY(-1px);
}

.todo-item.completed {
  opacity: 0.6;
}

.todo-item.completed .todo-title {
  text-decoration: line-through;
  color: var(--color-text-tertiary);
}

.todo-item.overdue {
  border-color: rgba(239, 68, 68, 0.3);
}

.todo-item.selected {
  border-color: var(--color-primary);
  background: rgba(99, 102, 241, 0.04);
}

/* 复选框 */
.checkbox {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border: 2px solid var(--color-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 1px;
  background: transparent;
  padding: 0;
}

.checkbox:hover {
  border-color: var(--color-primary);
  background: rgba(99, 102, 241, 0.08);
}

.checkbox.checked {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.checkbox.checked:hover {
  background: var(--color-primary-hover);
}

/* 内容区 */
.todo-content {
  flex: 1;
  min-width: 0;
}

.todo-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.todo-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  line-height: 1.4;
  word-break: break-word;
}

.todo-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.priority-badge {
  display: flex;
  align-items: center;
}

.category-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.deadline-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
}

.deadline-badge.overdue {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.deadline-badge.today {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

/* 子任务进度 */
.subtask-progress {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.progress-icon {
  opacity: 0.5;
}

.progress-bar {
  flex: 1;
  max-width: 80px;
  height: 3px;
  background: var(--color-border);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* 标签 */
.todo-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.tag {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

/* 时间预估 */
.time-estimate {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
  font-size: 11px;
  color: var(--color-text-tertiary);
}
</style>
