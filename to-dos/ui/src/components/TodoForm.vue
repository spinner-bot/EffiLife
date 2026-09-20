<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useTodosStore } from '@/stores/todos'
import { X, Calendar, Tag, Clock, AlignLeft } from 'lucide-vue-next'
import type { Priority } from '@/types'
import { PRIORITY_CONFIG } from '@/types'

const props = defineProps<{
  todoId?: string | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const store = useTodosStore()

// 表单数据
const title = ref('')
const description = ref('')
const deadline = ref('')
const priority = ref<Priority>('normal')
const category = ref('default')
const tags = ref<string[]>([])
const tagInput = ref('')
const timeEstimate = ref<number | null>(null)

// 编辑模式
const isEditing = computed(() => !!props.todoId)
const existingTodo = computed(() => {
  if (!props.todoId) return null
  return store.todos.find(t => t.id === props.todoId)
})

// 初始化表单数据
onMounted(() => {
  if (existingTodo.value) {
    title.value = existingTodo.value.title
    description.value = existingTodo.value.description || ''
    deadline.value = existingTodo.value.deadline
      ? existingTodo.value.deadline.slice(0, 16)
      : ''
    priority.value = existingTodo.value.priority
    category.value = existingTodo.value.category
    tags.value = [...existingTodo.value.tags]
    timeEstimate.value = existingTodo.value.time_estimate || null
  }
  // 自动聚焦标题输入框
  setTimeout(() => {
    const input = document.querySelector('.form-input.title') as HTMLInputElement
    input?.focus()
  }, 100)
})

// 标签操作
function addTag() {
  const tag = tagInput.value.trim()
  if (tag && !tags.value.includes(tag)) {
    tags.value.push(tag)
    tagInput.value = ''
  }
}

function removeTag(tag: string) {
  tags.value = tags.value.filter(t => t !== tag)
}

function handleTagKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    addTag()
  }
}

// 提交表单
function handleSubmit() {
  if (!title.value.trim()) return

  const data = {
    title: title.value.trim(),
    description: description.value.trim() || undefined,
    deadline: deadline.value ? new Date(deadline.value).toISOString() : undefined,
    priority: priority.value,
    category: category.value,
    tags: tags.value,
    time_estimate: timeEstimate.value || undefined,
  }

  if (isEditing.value && props.todoId) {
    store.updateTodo(props.todoId, data)
  } else {
    store.addTodo(data)
  }

  emit('close')
}

// 点击遮罩关闭
function handleBackdropClick(e: MouseEvent) {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}
</script>

<template>
  <div class="form-backdrop" @click="handleBackdropClick">
    <div class="form-modal">
      <!-- 头部 -->
      <header class="form-header">
        <h2 class="form-title">{{ isEditing ? '编辑待办' : '新建待办' }}</h2>
        <button class="close-btn" @click="emit('close')" aria-label="关闭">
          <X :size="20" />
        </button>
      </header>

      <!-- 表单内容 -->
      <form @submit.prevent="handleSubmit" class="form-body">
        <!-- 标题 -->
        <div class="form-group">
          <label class="form-label">标题</label>
          <input
            v-model="title"
            type="text"
            class="form-input title"
            placeholder="输入待办标题..."
            required
          />
        </div>

        <!-- 描述 -->
        <div class="form-group">
          <label class="form-label">
            <AlignLeft :size="14" />
            描述
          </label>
          <textarea
            v-model="description"
            class="form-input textarea"
            placeholder="添加详细描述（可选）..."
            rows="3"
          ></textarea>
        </div>

        <!-- 行：优先级 + 分类 -->
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">优先级</label>
            <select v-model="priority" class="form-input select">
              <option v-for="(config, key) in PRIORITY_CONFIG" :key="key" :value="key">
                {{ config.label }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">分类</label>
            <select v-model="category" class="form-input select">
              <option v-for="cat in store.categories" :key="cat.id" :value="cat.id">
                {{ cat.name }}
              </option>
            </select>
          </div>
        </div>

        <!-- 截止日期 -->
        <div class="form-group">
          <label class="form-label">
            <Calendar :size="14" />
            截止日期
          </label>
          <input
            v-model="deadline"
            type="datetime-local"
            class="form-input"
          />
        </div>

        <!-- 预估时间 -->
        <div class="form-group">
          <label class="form-label">
            <Clock :size="14" />
            预估时间（分钟）
          </label>
          <input
            v-model.number="timeEstimate"
            type="number"
            class="form-input"
            placeholder="例如：60"
            min="0"
          />
        </div>

        <!-- 标签 -->
        <div class="form-group">
          <label class="form-label">
            <Tag :size="14" />
            标签
          </label>
          <div class="tags-input">
            <div class="tags-list">
              <span v-for="tag in tags" :key="tag" class="tag-chip">
                #{{ tag }}
                <button type="button" @click="removeTag(tag)" class="tag-remove">×</button>
              </span>
            </div>
            <input
              v-model="tagInput"
              type="text"
              class="form-input tag-input"
              placeholder="输入标签后按 Enter..."
              @keydown="handleTagKeydown"
            />
          </div>
        </div>

        <!-- 提交按钮 -->
        <div class="form-actions">
          <button type="button" class="btn btn-secondary" @click="emit('close')">
            取消
          </button>
          <button type="submit" class="btn btn-primary" :disabled="!title.trim()">
            {{ isEditing ? '保存' : '创建' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.form-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.form-modal {
  width: 100%;
  max-width: 520px;
  max-height: 90vh;
  background: var(--color-bg);
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideUp 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.form-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--color-border);
}

.form-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.15s;
}

.close-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.form-body {
  padding: 20px 24px;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 14px;
  color: var(--color-text-primary);
  transition: all 0.15s;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  background: var(--color-bg);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.form-input::placeholder {
  color: var(--color-text-tertiary);
}

.form-input.title {
  font-size: 16px;
  font-weight: 500;
}

.form-input.textarea {
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
}

.form-input.select {
  cursor: pointer;
}

/* 标签输入 */
.tags-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--color-primary);
  border-radius: 14px;
  font-size: 12px;
}

.tag-remove {
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--color-primary);
  font-size: 14px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.tag-remove:hover {
  background: rgba(99, 102, 241, 0.2);
}

.tag-input {
  margin-top: 4px;
}

/* 操作按钮 */
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-secondary {
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
}

.btn-secondary:hover {
  background: var(--color-bg-tertiary);
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
