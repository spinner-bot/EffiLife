<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="settings-view">
    <header class="header">
      <button class="back-btn" @click="router.push('/')">
        <span>←</span> 返回
      </button>
      <h1>设置</h1>
    </header>

    <main class="main-content">
      <section class="settings-list">
        <button class="settings-item">
          <span>自定义</span>
          <span class="arrow">→</span>
        </button>
        <button class="settings-item">
          <span>外观</span>
          <span class="arrow">→</span>
        </button>
        <button class="settings-item">
          <span>帮助</span>
          <span class="arrow">→</span>
        </button>
        <button class="settings-item">
          <span>存档管理</span>
          <span class="arrow">→</span>
        </button>
        <button class="settings-item">
          <span>恢复</span>
          <span class="arrow">→</span>
        </button>
      </section>

      <footer class="settings-footer">
        <p>开发者：浪兮spinner_bot</p>
        <p>抖音@浪兮有点浪</p>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.settings-view {
  min-height: 100vh;
  padding: var(--spacing-lg);
}

.header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: 0.875rem;
}

.back-btn:hover {
  background: var(--color-bg-tertiary);
}

.header h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.main-content {
  max-width: 500px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.settings-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.settings-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: 1rem;
  transition: all var(--transition-fast);
}

.settings-item:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-hover);
}

.arrow {
  color: var(--color-text-tertiary);
}

.settings-footer {
  text-align: center;
  padding: var(--spacing-lg) 0;
  color: var(--color-text-tertiary);
  font-size: 0.75rem;
  line-height: 1.8;
}
</style>
