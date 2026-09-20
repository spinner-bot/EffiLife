<script setup lang="ts">
/**
 * SettingsPanel (v0.5.0)
 *
 * 设置面板：
 * - 优先排位分更新频率
 * - 分类展开数量
 * - 日期格式
 */

import { ref, computed } from 'vue'
import { useTodosStore } from '@/stores/todos'
import { X, RefreshCw, List, Calendar, Zap } from 'lucide-vue-next'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const store = useTodosStore()

const frequencyOptions = [
  { value: 0, label: '手动' },
  { value: 1000, label: '1 秒' },
  { value: 5000, label: '5 秒' },
  { value: 30000, label: '30 秒' },
]

const expandCountOptions = [
  { value: 3, label: '3' },
  { value: 5, label: '5' },
  { value: 8, label: '8' },
  { value: 10, label: '10' },
  { value: 999, label: '全部' },
]

function updateFrequency(val: number) {
  store.updateSettings({ updateFrequency: val })
}

function updateExpandCount(val: number) {
  store.updateSettings({ expandCount: val })
}

function handleBackdropClick(e: MouseEvent) {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}
</script>

<template>
  <Transition name="fade">
    <div v-if="show" class="settings-backdrop" @click="handleBackdropClick">
      <div class="settings-modal">
        <header class="settings-header">
          <h2 class="settings-title">
            <Zap :size="18" />
            设置
          </h2>
          <button class="close-btn" @click="emit('close')">
            <X :size="18" />
          </button>
        </header>

        <div class="settings-body">
          <!-- 更新频率 -->
          <div class="setting-group">
            <div class="setting-label">
              <RefreshCw :size="14" />
              <span>分数更新频率</span>
            </div>
            <div class="setting-options">
              <button
                v-for="opt in frequencyOptions"
                :key="opt.value"
                class="option-btn"
                :class="{ active: store.settings.updateFrequency === opt.value }"
                @click="updateFrequency(opt.value)"
              >
                {{ opt.label }}
              </button>
            </div>
            <p class="setting-desc">
              优先排位分实时计算的刷新间隔。设为"手动"需手动刷新。
            </p>
          </div>

          <!-- 展开数量 -->
          <div class="setting-group">
            <div class="setting-label">
              <List :size="14" />
              <span>分类展开数量</span>
            </div>
            <div class="setting-options">
              <button
                v-for="opt in expandCountOptions"
                :key="opt.value"
                class="option-btn"
                :class="{ active: store.settings.expandCount === opt.value }"
                @click="updateExpandCount(opt.value)"
              >
                {{ opt.label }}
              </button>
            </div>
            <p class="setting-desc">
              侧栏中按分数排序后，前 X 名分类展开显示，其余折叠收纳。
            </p>
          </div>

          <!-- 手动刷新 -->
          <div class="setting-group">
            <div class="setting-label">
              <Zap :size="14" />
              <span>手动操作</span>
            </div>
            <button class="refresh-btn" @click="store.recalculateScores()">
              <RefreshCw :size="14" />
              立即刷新分数
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.settings-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.settings-modal {
  width: 100%;
  max-width: 440px;
  background: var(--color-bg-elevated, var(--color-bg));
  border-radius: 14px;
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  animation: slideUp 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}

.settings-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
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

.settings-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.setting-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.setting-options {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.option-btn {
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: transparent;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.option-btn:hover {
  border-color: var(--color-border-hover);
  background: var(--color-bg-hover);
}

.option-btn.active {
  background: var(--color-primary-muted);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.setting-desc {
  font-size: 11px;
  color: var(--color-text-tertiary);
  line-height: 1.5;
  margin-top: 2px;
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: transparent;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  align-self: flex-start;
}

.refresh-btn:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-muted);
  color: var(--color-primary);
}
</style>
