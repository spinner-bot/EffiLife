<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Check, ListTodo, Plus, Trash2 } from 'lucide-vue-next'
import { AudioManager } from '@/audio'
import { TodoService, type TodoPriority, type UnifiedTodo } from '@/services/todoService'

const router = useRouter()
const todos = ref<UnifiedTodo[]>([])
const title = ref('')
const priority = ref<TodoPriority>('normal')
const filter = ref<'all' | 'active' | 'completed'>('active')
const isLoading = ref(true)
const errorMessage = ref('')

const activeTodos = computed(() => todos.value.filter((todo) => !['completed', 'archived', 'cancelled'].includes(todo.status)))
const completedTodos = computed(() => todos.value.filter((todo) => todo.status === 'completed'))
const visibleTodos = computed(() => {
  if (filter.value === 'active') return activeTodos.value
  if (filter.value === 'completed') return completedTodos.value
  return todos.value
})

const priorityLabels: Record<TodoPriority, string> = {
  'urgent-important': '紧急重要',
  important: '重要',
  urgent: '紧急',
  normal: '普通',
}

async function loadTodos() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    todos.value = await TodoService.list()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '待办加载失败'
  } finally {
    isLoading.value = false
  }
}

async function addTodo() {
  if (!title.value.trim()) return
  try {
    const todo = await TodoService.create({ title: title.value, priority: priority.value })
    todos.value = [todo, ...todos.value]
    title.value = ''
    priority.value = 'normal'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '待办创建失败'
  }
}

async function completeTodo(todo: UnifiedTodo) {
  try {
    const updated = await TodoService.complete(todo.id)
    const index = todos.value.findIndex((item) => item.id === todo.id)
    if (index >= 0) todos.value[index] = updated
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '待办更新失败'
  }
}

async function removeTodo(todo: UnifiedTodo) {
  try {
    await TodoService.remove(todo.id)
    todos.value = todos.value.filter((item) => item.id !== todo.id)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '待办删除失败'
  }
}

function formatDeadline(deadline?: string): string {
  if (!deadline) return ''
  const date = new Date(deadline)
  return Number.isNaN(date.getTime()) ? deadline : date.toLocaleDateString('zh-CN')
}

onMounted(loadTodos)
</script>

<template>
  <div class="task-center">
    <header class="task-header">
      <button class="task-back" @click="AudioManager.playSound('click'); router.push('/')" aria-label="返回首页">
        <ArrowLeft :size="18" />
      </button>
      <div>
        <p class="task-eyebrow">统一工作台</p>
        <h1><ListTodo :size="24" /> 待办中心</h1>
      </div>
      <div class="task-counts">
        <span>{{ activeTodos.length }} 项待处理</span>
        <span>{{ completedTodos.length }} 项已完成</span>
      </div>
    </header>

    <main class="task-content">
      <section class="task-create theme-card">
        <input v-model="title" class="task-input" placeholder="添加一个可执行的任务…" @keyup.enter="addTodo" />
        <select v-model="priority" class="task-select" aria-label="优先级">
          <option v-for="(label, value) in priorityLabels" :key="value" :value="value">{{ label }}</option>
        </select>
        <button class="task-add" @click="AudioManager.playSound('click'); addTodo()">
          <Plus :size="17" /> 添加
        </button>
      </section>

      <section class="task-toolbar">
        <div class="task-tabs" role="tablist" aria-label="待办筛选">
          <button :class="{ active: filter === 'active' }" @click="filter = 'active'">待处理</button>
          <button :class="{ active: filter === 'all' }" @click="filter = 'all'">全部</button>
          <button :class="{ active: filter === 'completed' }" @click="filter = 'completed'">已完成</button>
        </div>
        <span v-if="errorMessage" class="task-error">{{ errorMessage }}</span>
      </section>

      <section v-if="isLoading" class="task-empty theme-card">正在加载待办…</section>
      <section v-else-if="visibleTodos.length === 0" class="task-empty theme-card">
        <ListTodo :size="34" />
        <strong>{{ filter === 'completed' ? '还没有完成的任务' : '今天没有待办' }}</strong>
        <span>把下一步写下来，时间管理从行动开始。</span>
      </section>
      <section v-else class="task-list">
        <article v-for="todo in visibleTodos" :key="todo.id" class="task-item theme-card" :class="{ completed: todo.status === 'completed' }">
          <button class="task-check" :aria-label="todo.status === 'completed' ? '已完成' : '完成任务'" @click="completeTodo(todo)">
            <Check v-if="todo.status === 'completed'" :size="16" />
          </button>
          <div class="task-main">
            <div class="task-title-row">
              <h2>{{ todo.title }}</h2>
              <span class="task-priority">{{ priorityLabels[todo.priority] }}</span>
            </div>
            <p v-if="todo.description">{{ todo.description }}</p>
            <span v-if="todo.deadline" class="task-deadline">截止 {{ formatDeadline(todo.deadline) }}</span>
          </div>
          <button class="task-delete" aria-label="删除任务" @click="removeTodo(todo)"><Trash2 :size="16" /></button>
        </article>
      </section>
    </main>
  </div>
</template>

<style scoped>
.task-center { min-height: 100vh; color: var(--color-text-primary); background: var(--color-bg); }
.task-header { display: flex; align-items: center; gap: 16px; max-width: 980px; margin: 0 auto; padding: 32px 28px 20px; }
.task-back { display: grid; place-items: center; width: 36px; height: 36px; border: 1px solid var(--color-border); border-radius: 12px; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; }
.task-eyebrow { margin: 0 0 3px; color: var(--color-text-tertiary); font-size: 12px; letter-spacing: .08em; }
.task-header h1 { display: flex; align-items: center; gap: 9px; margin: 0; font-size: 25px; }
.task-counts { display: flex; gap: 8px; margin-left: auto; color: var(--color-text-secondary); font-size: 13px; }
.task-counts span { padding: 7px 10px; border: 1px solid var(--color-border); border-radius: 999px; background: var(--color-bg-secondary); }
.task-content { max-width: 980px; margin: 0 auto; padding: 8px 28px 48px; }
.task-create { display: flex; gap: 10px; padding: 13px; border: 1px solid var(--color-border); border-radius: 16px; }
.task-input { min-width: 0; flex: 1; border: 0; outline: 0; color: var(--color-text-primary); background: transparent; font-size: 15px; }
.task-select { border: 1px solid var(--color-border); border-radius: 10px; padding: 0 10px; color: var(--color-text-secondary); background: var(--color-bg-secondary); }
.task-add { display: inline-flex; align-items: center; gap: 6px; border: 0; border-radius: 10px; padding: 0 15px; color: var(--color-button-text); background: var(--color-primary); cursor: pointer; font-weight: 600; }
.task-toolbar { display: flex; align-items: center; justify-content: space-between; padding: 24px 2px 12px; }
.task-tabs { display: flex; gap: 4px; padding: 4px; border-radius: 10px; background: var(--color-bg-secondary); }
.task-tabs button { border: 0; border-radius: 7px; padding: 7px 13px; color: var(--color-text-secondary); background: transparent; cursor: pointer; }
.task-tabs button.active { color: var(--color-text-primary); background: var(--color-bg-elevated); box-shadow: var(--shadow-sm, 0 1px 3px rgba(0,0,0,.08)); }
.task-error { color: var(--color-error); font-size: 13px; }
.task-list { display: grid; gap: 10px; }
.task-item { display: flex; align-items: center; gap: 13px; padding: 16px; border: 1px solid var(--color-border); border-radius: 14px; transition: border-color .2s, transform .2s; }
.task-item:hover { border-color: var(--color-border-hover); transform: translateY(-1px); }
.task-item.completed { opacity: .68; }
.task-check { display: grid; place-items: center; width: 23px; height: 23px; flex: 0 0 23px; border: 2px solid var(--color-border-hover); border-radius: 50%; color: var(--color-button-text); background: var(--color-primary); cursor: pointer; }
.task-main { min-width: 0; flex: 1; }
.task-title-row { display: flex; align-items: center; gap: 9px; }
.task-title-row h2 { overflow: hidden; margin: 0; font-size: 15px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.completed .task-title-row h2 { text-decoration: line-through; }
.task-priority { padding: 3px 7px; border-radius: 6px; color: var(--color-primary); background: var(--color-primary-muted); font-size: 11px; white-space: nowrap; }
.task-main p { margin: 5px 0 0; color: var(--color-text-secondary); font-size: 13px; }
.task-deadline { display: inline-block; margin-top: 7px; color: var(--color-text-tertiary); font-size: 12px; }
.task-delete { display: grid; place-items: center; border: 0; color: var(--color-text-tertiary); background: transparent; cursor: pointer; }
.task-delete:hover { color: var(--color-error); }
.task-empty { display: grid; place-items: center; gap: 9px; min-height: 220px; border: 1px dashed var(--color-border); border-radius: 16px; color: var(--color-text-tertiary); text-align: center; }
.task-empty strong { color: var(--color-text-secondary); }
@media (max-width: 700px) { .task-header { padding: 24px 18px 16px; } .task-content { padding: 8px 18px 36px; } .task-counts { display: none; } .task-create { flex-wrap: wrap; } .task-input { flex-basis: 100%; height: 38px; } .task-select, .task-add { height: 38px; } }
</style>
