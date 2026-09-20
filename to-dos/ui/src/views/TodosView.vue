<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useTodosStore } from '@/stores/todos'
import CategorySidebar from '@/components/CategorySidebar.vue'
import TodoList from '@/components/TodoList.vue'
import TodoForm from '@/components/TodoForm.vue'
import FilterBar from '@/components/FilterBar.vue'
import { Plus, Search } from 'lucide-vue-next'

const store = useTodosStore()

const showForm = ref(false)
const searchQuery = ref('')
const editingTodoId = ref<string | null>(null)

// 键盘快捷键
function handleKeydown(e: KeyboardEvent) {
  // 按 N 键快速添加
  if (e.key === 'n' && !e.ctrlKey && !e.metaKey && !isInputFocused()) {
    e.preventDefault()
    openAddForm()
  }
  // 按 Esc 关闭弹窗
  if (e.key === 'Escape') {
    showForm.value = false
    editingTodoId.value = null
  }
}

function isInputFocused(): boolean {
  const el = document.activeElement
  return el?.tagName === 'INPUT' || el?.tagName === 'TEXTAREA'
}

function openAddForm() {
  editingTodoId.value = null
  showForm.value = true
}

function openEditForm(id: string) {
  editingTodoId.value = id
  showForm.value = true
}

function handleSearch(e: Event) {
  const value = (e.target as HTMLInputElement).value
  store.setFilter('search', value)
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="todos-view">
    <!-- 侧栏 -->
    <CategorySidebar />

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 顶部栏 -->
      <header class="top-bar">
        <div class="search-box">
          <Search :size="18" class="search-icon" />
          <input
            type="text"
            v-model="searchQuery"
            @input="handleSearch"
            placeholder="搜索待办... (按 / 聚焦)"
            class="search-input"
          />
        </div>

        <button class="add-btn" @click="openAddForm">
          <Plus :size="18" />
          <span>新建待办</span>
          <kbd>N</kbd>
        </button>
      </header>

      <!-- 筛选栏 -->
      <FilterBar />

      <!-- 待办列表 -->
      <TodoList @edit="openEditForm" />
    </main>

    <!-- 新建/编辑弹窗 -->
    <TodoForm
      v-if="showForm"
      :todo-id="editingTodoId"
      @close="showForm = false; editingTodoId = null"
    />
  </div>
</template>

<style scoped>
.todos-view {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px 32px;
  overflow-y: auto;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.search-box {
  position: relative;
  flex: 1;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-tertiary);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 10px 12px 10px 40px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 14px;
  color: var(--color-text-primary);
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary);
  background: var(--color-bg);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.search-input::placeholder {
  color: var(--color-text-tertiary);
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.add-btn:hover {
  background: var(--color-primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.add-btn:active {
  transform: translateY(0);
}

.add-btn kbd {
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  font-size: 11px;
  font-family: inherit;
}
</style>
