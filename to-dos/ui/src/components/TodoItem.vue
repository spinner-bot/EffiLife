<script setup lang="ts">
import { computed, ref } from 'vue'
import { useTodosStore } from '@/stores/todos'
import {
  Check, Circle, AlertCircle, Star, Zap,
  ChevronRight, Clock, Calendar as CalendarIcon,
  MoreHorizontal, Edit3, Trash2, Archive,
} from 'lucide-vue-next'
import type { Todo } from '@/types'
import { PRIORITY_CONFIG } from '@/types'
import { formatScoreDisplay } from '@/utils/priority'

const props = defineProps<{
  todo: Todo
  searchQuery?: string
}>()

const emit = defineEmits<{
  (e: 'edit', id: string): void
  (e: 'toggle-select', id: string): void
  (e: 'delete', id: string): void
  (e: 'archive', id: string): void
}>()

const store = useTodosStore()
const showActions = ref(false)

const isCompleted = computed(() => props.todo.status === 'completed')
const isCancelled = computed(() => props.todo.status === 'cancelled')
const isOverdue = computed(() => {
  if (!props.todo.deadline || isCompleted.value || isCancelled.value) return false
  return new Date(props.todo.deadline) < new Date()
})

// 截止日期距离天数（用于高亮）
const daysUntilDeadline = computed(() => {
  if (!props.todo.deadline || isCompleted.value || isCancelled.value) return null
  const dl = new Date(props.todo.deadline)
  const now = new Date()
  return Math.ceil((dl.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
})

const isDeadlineSoon = computed(() => {
  const days = daysUntilDeadline.value
  return days !== null && days >= 0 && days <= 3
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

// v0.5.0: 优先排位分显示
const scoreDisplay = computed(() => {
  if (props.todo._score_display) return props.todo._score_display
  if (props.todo._score !== undefined) return formatScoreDisplay(props.todo._score)
  return ''
})

function toggleComplete() {
  if (isCompleted.value) {
    store.updateTodo(props.todo.id, { status: 'pending' })
  } else {
    store.completeTodo(props.todo.id)
  }
}

function toggleActionMenu() {
  showActions.value = !showActions.value
}

function handleDelete() {
  emit('delete', props.todo.id)
  showActions.value = false
}

function handleArchive() {
  emit('archive', props.todo.id)
  showActions.value = false
}

// 搜索高亮
function highlightText(text: string, query: string): string {
  if (!query || !text) return text
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${escaped})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}
</script>

<template>
  <div
    class="todo-item"
    :class="{
      completed: isCompleted,
      cancelled: isCancelled,
      overdue: isOverdue,
      'deadline-soon': isDeadlineSoon,
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
        <!-- v0.5.0: 优先排位分 -->
        <span
          v-if="scoreDisplay && scoreDisplay !== '0'"
          class="score-badge"
          :class="{ 'score-high': (todo._score ?? 0) >= 1000, 'score-expired': scoreDisplay === '过期' }"
          :title="`优先排位分: ${todo._score ?? 0}`"
        >
          {{ scoreDisplay }}
        </span>
        <span class="todo-title" v-html="highlightText(todo.title, searchQuery || '')"></span>
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
            :class="{ overdue: isOverdue, today: deadlineText === '今天截止', soon: isDeadlineSoon && !isOverdue }"
          >
            <CalendarIcon :size="12" />
            {{ deadlineText }}
          </span>

          <!-- 操作菜单 -->
          <button
            class="action-trigger"
            @click.stop="toggleActionMenu"
            aria-label="更多操作"
          >
            <MoreHorizontal :size="16" />
          </button>
        </div>
      </div>

      <!-- 描述预览 -->
      <p v-if="todo.description" class="todo-description" v-html="highlightText(todo.description.slice(0, 80), searchQuery || '')"></p>

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

    <!-- 弹出操作菜单 -->
    <Transition name="scale-fade">
      <div v-if="showActions" class="action-menu" @click.stop>
        <button @click="emit('edit', todo.id); showActions = false" class="action-item">
          <Edit3 :size="14" />
          编辑
        </button>
        <button @click="handleArchive" class="action-item">
          <Archive :size="14" />
          归档
        </button>
        <button @click="handleDelete" class="action-item danger">
          <Trash2 :size="14" />
          删除
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.todo-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  background: var(--color-bg-elevated, var(--color-bg));
  border: 1px solid var(--color-border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-xs);
  position: relative;
}

.todo-item:hover {
  border-color: var(--color-border-hover);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.todo-item:active {
  transform: translateY(0);
  box-shadow: var(--shadow-sm);
}

.todo-item.completed {
  opacity: 0.55;
}

.todo-item.completed .todo-title {
  text-decoration: line-through;
  color: var(--color-text-tertiary);
}

.todo-item.cancelled {
  opacity: 0.4;
}

.todo-item.cancelled .todo-title {
  text-decoration: line-through;
  color: var(--color-text-disabled);
}

.todo-item.overdue {
  border-color: rgba(239, 68, 68, 0.3);
  background: color-mix(in srgb, var(--color-error-bg) 30%, var(--color-bg-elevated, var(--color-bg)));
}

.todo-item.deadline-soon {
  border-color: rgba(245, 158, 11, 0.3);
}

.todo-item.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-muted);
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
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin-top: 1px;
  background: transparent;
  padding: 0;
}

.checkbox:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-muted);
  transform: scale(1.1);
}

.checkbox.checked {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
  animation: checkBounce 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes checkBounce {
  0% { transform: scale(0.8); }
  50% { transform: scale(1.15); }
  100% { transform: scale(1); }
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

/* v0.5.0: 优先排位分 */
.score-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  font-family: var(--font-mono, monospace);
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
  flex-shrink: 0;
  letter-spacing: -0.02em;
}

.score-badge.score-high {
  background: rgba(99, 102, 241, 0.1);
  color: var(--color-primary);
  border-color: rgba(99, 102, 241, 0.3);
}

.score-badge.score-expired {
  background: var(--color-error-bg);
  color: var(--color-error);
  border-color: rgba(239, 68, 68, 0.3);
}

.todo-description {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 4px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  background: var(--color-error-bg);
  color: var(--color-error);
}

.deadline-badge.today {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.deadline-badge.soon {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

/* 操作菜单 */
.action-trigger {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.15s;
  opacity: 0;
}

.todo-item:hover .action-trigger {
  opacity: 1;
}

.action-trigger:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.action-menu {
  position: absolute;
  top: 8px;
  right: 8px;
  background: var(--color-bg-elevated, var(--color-bg));
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: var(--shadow-lg);
  padding: 4px;
  z-index: 10;
  min-width: 120px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.1s;
  text-align: left;
}

.action-item:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.action-item.danger:hover {
  background: var(--color-error-bg);
  color: var(--color-error);
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
  padding: 1px 6px;
  background: var(--color-bg-secondary);
  border-radius: 4px;
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
