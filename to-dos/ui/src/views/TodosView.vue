<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useTodosStore } from '@/stores/todos'
import CategorySidebar from '@/components/CategorySidebar.vue'
import TodoList from '@/components/TodoList.vue'
import TodoForm from '@/components/TodoForm.vue'
import FilterBar from '@/components/FilterBar.vue'
import SettingsPanel from '@/components/SettingsPanel.vue'
import {
  Plus, Search, Moon, Sun, Monitor, Download, Upload,
  CheckSquare, X, Trash2, CheckCircle, Settings,
} from 'lucide-vue-next'

const store = useTodosStore()

const showForm = ref(false)
const searchQuery = ref('')
const editingTodoId = ref<string | null>(null)
const focusedIndex = ref(-1)
const showImportModal = ref(false)
const importText = ref('')
const importMessage = ref('')
const showSettings = ref(false)  // v0.5.0

// 键盘快捷键 + 导航
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
    showImportModal.value = false
  }
  // 按 / 聚焦搜索
  if (e.key === '/' && !isInputFocused()) {
    e.preventDefault()
    const input = document.querySelector('.search-input') as HTMLInputElement
    input?.focus()
  }
  // 按 Ctrl+E 导出
  if ((e.ctrlKey || e.metaKey) && e.key === 'e' && !isInputFocused()) {
    e.preventDefault()
    handleExport()
  }
  // 按 Ctrl+I 导入
  if ((e.ctrlKey || e.metaKey) && e.key === 'i' && !isInputFocused()) {
    e.preventDefault()
    showImportModal.value = true
  }
  // 按 Ctrl+D 切换深色模式
  if ((e.ctrlKey || e.metaKey) && e.key === 'd' && !isInputFocused()) {
    e.preventDefault()
    cycleDarkMode()
  }
  // v0.5.0: 按 Ctrl+, 打开设置
  if ((e.ctrlKey || e.metaKey) && e.key === ',' && !isInputFocused()) {
    e.preventDefault()
    showSettings.value = !showSettings.value
  }
  // 上下箭头导航
  if ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && !isInputFocused()) {
    e.preventDefault()
    const items = store.filteredTodos
    if (items.length === 0) return
    if (e.key === 'ArrowDown') {
      focusedIndex.value = Math.min(focusedIndex.value + 1, items.length - 1)
    } else {
      focusedIndex.value = Math.max(focusedIndex.value - 1, 0)
    }
  }
  // Enter 编辑当前聚焦项
  if (e.key === 'Enter' && !isInputFocused() && focusedIndex.value >= 0) {
    const item = store.filteredTodos[focusedIndex.value]
    if (item) openEditForm(item.id)
  }
  // Space 切换完成状态
  if (e.key === ' ' && !isInputFocused() && focusedIndex.value >= 0) {
    e.preventDefault()
    const item = store.filteredTodos[focusedIndex.value]
    if (item) {
      if (item.status === 'completed') {
        store.updateTodo(item.id, { status: 'pending' })
      } else {
        store.completeTodo(item.id)
      }
    }
  }
}

function isInputFocused(): boolean {
  const el = document.activeElement
  return el?.tagName === 'INPUT' || el?.tagName === 'TEXTAREA' || el?.tagName === 'SELECT'
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

// 深色模式循环: auto -> dark -> light -> auto
function cycleDarkMode() {
  const modes: ('auto' | 'light' | 'dark')[] = ['auto', 'dark', 'light']
  const current = modes.indexOf(store.darkMode)
  const next = modes[(current + 1) % modes.length]
  store.setDarkMode(next)
}

const darkModeIcon = computed(() => {
  if (store.darkMode === 'dark') return Moon
  if (store.darkMode === 'light') return Sun
  return Monitor
})

const darkModeLabel = computed(() => {
  if (store.darkMode === 'dark') return '深色'
  if (store.darkMode === 'light') return '浅色'
  return '自动'
})

// 数据导出
function handleExport() {
  const json = store.exportData()
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `todos-backup-${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
}

// 数据导入
function handleImport() {
  if (!importText.value.trim()) return
  const result = store.importData(importText.value)
  importMessage.value = result.message
  if (result.success) {
    setTimeout(() => {
      showImportModal.value = false
      importText.value = ''
      importMessage.value = ''
    }, 1500)
  }
}

function handleFileImport(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    importText.value = reader.result as string
  }
  reader.readAsText(file)
}

// 批量操作
const hasSelection = computed(() => store.selectedIds.size > 0)

function handleBatchComplete() {
  store.batchComplete()
}

function handleBatchDelete() {
  store.batchDelete()
}

// 应用深色模式
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  store.loadFromStorage()
  store.applyDarkMode()
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

        <div class="top-actions">
          <!-- 深色模式切换 -->
          <button
            class="icon-btn"
            @click="cycleDarkMode"
            :title="`主题: ${darkModeLabel} (Ctrl+D)`"
          >
            <component :is="darkModeIcon" :size="18" />
          </button>

          <!-- v0.5.0: 设置 -->
          <button
            class="icon-btn"
            @click="showSettings = !showSettings"
            title="设置 (Ctrl+,)"
          >
            <Settings :size="18" />
          </button>

          <!-- 导出 -->
          <button
            class="icon-btn"
            @click="handleExport"
            title="导出 JSON (Ctrl+E)"
          >
            <Download :size="18" />
          </button>

          <!-- 导入 -->
          <button
            class="icon-btn"
            @click="showImportModal = true"
            title="导入 JSON (Ctrl+I)"
          >
            <Upload :size="18" />
          </button>

          <!-- 新建按钮 -->
          <button class="add-btn" @click="openAddForm">
            <Plus :size="18" />
            <span>新建待办</span>
            <kbd>N</kbd>
          </button>
        </div>
      </header>

      <!-- 批量操作栏 -->
      <Transition name="slide-up">
        <div v-if="hasSelection" class="batch-bar">
          <div class="batch-info">
            <CheckSquare :size="16" />
            <span>已选择 <strong>{{ store.selectedIds.size }}</strong> 项</span>
          </div>
          <div class="batch-actions">
            <button class="batch-btn" @click="handleBatchComplete">
              <CheckCircle :size="14" />
              完成
            </button>
            <button class="batch-btn danger" @click="handleBatchDelete">
              <Trash2 :size="14" />
              删除
            </button>
            <button class="batch-btn" @click="store.clearSelection">
              <X :size="14" />
              取消
            </button>
          </div>
        </div>
      </Transition>

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

    <!-- 导入弹窗 -->
    <Transition name="fade">
      <div v-if="showImportModal" class="import-backdrop" @click.self="showImportModal = false">
        <div class="import-modal">
          <header class="import-header">
            <h3>导入数据</h3>
            <button class="close-btn" @click="showImportModal = false">
              <X :size="18" />
            </button>
          </header>
          <div class="import-body">
            <p class="import-desc">粘贴 JSON 数据或选择文件导入</p>
            <textarea
              v-model="importText"
              class="import-textarea"
              placeholder='粘贴 JSON 数据（格式: {"todos": [...], "categories": [...]}）...'
              rows="8"
            ></textarea>
            <div class="import-file">
              <label class="file-label">
                <Upload :size="14" />
                选择文件
                <input type="file" accept=".json" @change="handleFileImport" class="file-input" />
              </label>
            </div>
            <p v-if="importMessage" class="import-message" :class="{ success: importMessage.includes('成功') }">
              {{ importMessage }}
            </p>
          </div>
          <footer class="import-footer">
            <button class="btn-secondary" @click="showImportModal = false">取消</button>
            <button class="btn-primary" @click="handleImport" :disabled="!importText.trim()">
              导入
            </button>
          </footer>
        </div>
      </div>
    </Transition>

    <!-- v0.5.0: 设置面板 -->
    <SettingsPanel :show="showSettings" @close="showSettings = false" />
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
  box-shadow: 0 0 0 3px var(--color-primary-muted);
}

.search-input::placeholder {
  color: var(--color-text-tertiary);
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.icon-btn:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-border-hover);
  color: var(--color-text-primary);
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

/* 批量操作栏 */
.batch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: var(--color-primary-muted);
  border: 1px solid var(--color-primary);
  border-radius: 10px;
  margin-bottom: 16px;
}

.batch-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-primary);
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.batch-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background: var(--color-bg-elevated, var(--color-bg));
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.batch-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.batch-btn.danger:hover {
  background: var(--color-error-bg);
  color: var(--color-error);
}

/* 导入弹窗 */
.import-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.import-modal {
  width: 100%;
  max-width: 480px;
  background: var(--color-bg-elevated, var(--color-bg));
  border-radius: 14px;
  box-shadow: var(--shadow-xl);
  overflow: hidden;
}

.import-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}

.import-header h3 {
  font-size: 15px;
  font-weight: 600;
}

.close-btn {
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
}

.close-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.import-body {
  padding: 20px;
}

.import-desc {
  font-size: 13px;
  color: var(--color-text-tertiary);
  margin-bottom: 12px;
}

.import-textarea {
  width: 100%;
  padding: 12px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-family: var(--font-mono, monospace);
  font-size: 12px;
  color: var(--color-text-primary);
  resize: vertical;
}

.import-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-muted);
}

.import-file {
  margin-top: 12px;
}

.file-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.file-label:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-border-hover);
}

.file-input {
  display: none;
}

.import-message {
  margin-top: 12px;
  font-size: 13px;
  color: var(--color-error);
}

.import-message.success {
  color: var(--color-success);
}

.import-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid var(--color-border);
}

.btn-secondary {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.btn-secondary:hover {
  background: var(--color-bg-tertiary);
}

.btn-primary {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: var(--color-primary);
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
