<script setup lang="ts">
import { computed } from 'vue'
import { useTodosStore } from '@/stores/todos'
import {
  ListTodo, Calendar, AlertTriangle, Circle, Briefcase,
  BookOpen, Home, Heart, BarChart3, TrendingUp,
} from 'lucide-vue-next'
import type { LucideIcon } from 'lucide-vue-next'

const store = useTodosStore()

const iconMap: Record<string, LucideIcon> = {
  circle: Circle,
  briefcase: Briefcase,
  'book-open': BookOpen,
  home: Home,
  heart: Heart,
}

interface SidebarItem {
  id: string | null
  label: string
  count: number
  icon: LucideIcon
  color: string
  isSpecial?: boolean
}

const sidebarItems = computed((): SidebarItem[] => {
  const items: SidebarItem[] = [
    {
      id: null,
      label: '全部',
      count: store.stats.total,
      icon: ListTodo,
      color: '#6366f1',
      isSpecial: true,
    },
    {
      id: '__today',
      label: '今日',
      count: store.todayTodos.length,
      icon: Calendar,
      color: '#3b82f6',
      isSpecial: true,
    },
    {
      id: '__overdue',
      label: '逾期',
      count: store.overdueTodos.length,
      icon: AlertTriangle,
      color: '#ef4444',
      isSpecial: true,
    },
  ]

  // 分隔线后添加分类
  for (const cat of store.categories) {
    items.push({
      id: cat.id,
      label: cat.name,
      count: store.todos.filter(t => t.category === cat.id).length,
      icon: iconMap[cat.icon] || Circle,
      color: cat.color,
    })
  }

  return items
})

const stats = computed(() => store.stats)

function selectCategory(id: string | null) {
  if (id === '__today' || id === '__overdue') {
    store.clearFilters()
    return
  }
  store.setFilter('category', id)
}

function isActive(id: string | null): boolean {
  if (id === null) return store.filters.category === null
  return store.filters.category === id
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1 class="logo">待办事项</h1>
      <span class="version-tag">v0.3.0</span>
    </div>

    <nav class="sidebar-nav">
      <div class="nav-section">
        <div
          v-for="item in sidebarItems"
          :key="item.id ?? '__all'"
          class="nav-item"
          :class="{ active: isActive(item.id), special: item.isSpecial }"
          @click="selectCategory(item.id)"
        >
          <div class="nav-icon-wrap" :style="{ background: item.color + '15' }">
            <component :is="item.icon" :size="16" :color="item.color" />
          </div>
          <span class="nav-label">{{ item.label }}</span>
          <span
            class="nav-count"
            :class="{ 'has-value': item.count > 0 }"
          >{{ item.count || '' }}</span>
        </div>
      </div>

      <div class="nav-divider"></div>

      <!-- 统计卡片 -->
      <div class="stats-card">
        <div class="stats-header">
          <BarChart3 :size="14" class="stats-icon" />
          <span class="stats-label">完成率</span>
          <span class="stats-value">{{ stats.completion_rate }}%</span>
        </div>
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: stats.completion_rate + '%' }"
          ></div>
        </div>
        <div class="stats-detail">
          <span>{{ stats.completed }} 已完成</span>
          <span>{{ stats.total }} 总计</span>
        </div>

        <!-- 迷你指标 -->
        <div class="mini-stats">
          <div class="mini-stat">
            <span class="mini-value">{{ stats.pending }}</span>
            <span class="mini-label">待处理</span>
          </div>
          <div class="mini-stat">
            <span class="mini-value">{{ stats.in_progress }}</span>
            <span class="mini-label">进行中</span>
          </div>
          <div class="mini-stat" :class="{ warning: stats.overdue > 0 }">
            <span class="mini-value">{{ stats.overdue }}</span>
            <span class="mini-label">逾期</span>
          </div>
        </div>
      </div>

      <!-- 快捷键提示 -->
      <div class="shortcuts-card">
        <div class="shortcut-hint">
          <kbd>N</kbd> 新建
        </div>
        <div class="shortcut-hint">
          <kbd>/</kbd> 搜索
        </div>
        <div class="shortcut-hint">
          <kbd>↑↓</kbd> 导航
        </div>
      </div>
    </nav>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 250px;
  min-width: 250px;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  padding: 20px 0;
}

.sidebar-header {
  padding: 0 20px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.version-tag {
  font-size: 10px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  background: var(--color-bg-tertiary);
  padding: 1px 6px;
  border-radius: 10px;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.nav-item:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.nav-item.active {
  background: var(--color-primary-muted);
  color: var(--color-primary);
  font-weight: 500;
}

.nav-item.special {
  font-weight: 500;
}

.nav-icon-wrap {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-label {
  flex: 1;
}

.nav-count {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  min-width: 20px;
  text-align: right;
}

.nav-count.has-value {
  color: var(--color-text-secondary);
}

.nav-item.active .nav-count {
  color: var(--color-primary);
}

.nav-divider {
  height: 1px;
  background: var(--color-border);
  margin: 12px 12px;
}

/* 统计卡片 */
.stats-card {
  margin: 8px 12px;
  padding: 14px;
  background: var(--color-bg);
  border-radius: 10px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-xs);
}

.stats-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.stats-icon {
  color: var(--color-text-tertiary);
}

.stats-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  flex: 1;
}

.stats-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
  font-family: var(--font-mono, monospace);
}

.progress-bar {
  height: 4px;
  background: var(--color-border);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 2px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.stats-detail {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--color-text-tertiary);
  margin-bottom: 10px;
}

/* 迷你指标 */
.mini-stats {
  display: flex;
  gap: 4px;
  padding-top: 10px;
  border-top: 1px solid var(--color-border-subtle);
}

.mini-stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.mini-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  font-family: var(--font-mono, monospace);
}

.mini-stat.warning .mini-value {
  color: var(--color-error);
}

.mini-label {
  font-size: 10px;
  color: var(--color-text-tertiary);
}

/* 快捷键卡片 */
.shortcuts-card {
  margin: 8px 12px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.shortcut-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.shortcut-hint kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 4px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 10px;
  font-family: var(--font-mono, monospace);
  color: var(--color-text-secondary);
}
</style>
