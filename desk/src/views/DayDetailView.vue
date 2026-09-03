<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { DataService, hoursToHm } from '@/services/dataService'
import { ArrowLeft, Calendar, List, Pencil, Trash2 } from 'lucide-vue-next'
import type { TimeRecord, RealTimeStat } from '@/types'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()

const dateStr = computed(() => route.params.date as string)
const plans = computed(() => appStore.plans)

const stat = ref<RealTimeStat | null>(null)
const records = ref<TimeRecord[]>([])
const dayPlanName = ref('')
const dayPlanType = ref('')

// 加载数据
async function loadData() {
  const day = dateStr.value
  stat.value = await DataService.calcRealTimeStat(day)
  records.value = await DataService.loadRecords(day)

  const planInfo = await DataService.getDayPlan(day)
  dayPlanName.value = planInfo.name
  dayPlanType.value = planInfo.type
}

// 完成度颜色
function getProgressColor(progress: number): string {
  if (progress === 0) return 'var(--color-text-primary)'
  if (progress < 40) return 'var(--color-progress-low)'
  if (progress < 70) return 'var(--color-progress-medium)'
  if (progress < 90) return 'var(--color-progress-good)'
  return 'var(--color-progress-high)'
}

// 删除记录
async function deleteRecord(index: number) {
  if (!confirm('确定删除这条记录？')) return
  await DataService.deleteRecord(index, dateStr.value)
  await loadData()
}

// 切换日计划
async function changePlan() {
  const planNames = Object.keys(plans.value)
  const newPlan = prompt(`当前计划：${dayPlanName.value}\n请输入新计划名称：\n可选：${planNames.join('、')}`)

  if (newPlan && plans.value[newPlan]) {
    await DataService.saveDayPlan(newPlan, dateStr.value)
    await loadData()
    alert(`计划已切换为：${newPlan}`)
  } else if (newPlan) {
    alert('计划名称无效')
  }
}

onMounted(loadData)
</script>

<template>
  <div class="day-detail-view">
    <header class="header">
      <button class="back-btn" @click="router.push('/calendar')">
        <ArrowLeft :size="16" />
        <span>返回日历</span>
      </button>
      <h1>{{ dateStr }} 详情</h1>
    </header>

    <main class="main-content">
      <!-- 计划信息 -->
      <section class="info-card">
        <div class="info-header">
          <h2>日计划</h2>
          <button class="change-btn" @click="changePlan">切换</button>
        </div>
        <p class="plan-name">{{ dayPlanName }}（{{ dayPlanType }}）</p>

        <!-- 统计信息 -->
        <div class="stats" v-if="stat">
          <div class="progress-row">
            <span class="progress-label">总完成度：</span>
            <span class="progress-value" :style="{ color: getProgressColor(stat.progress) }">
              {{ stat.progress }}%
            </span>
          </div>

          <div class="stat-items" v-if="stat.plan_exists">
            <div
              v-for="(target, tag) in stat.target"
              :key="tag"
              class="stat-item"
            >
              <span class="stat-tag">{{ tag === stat.bg_tag ? '🟢' : '🔹' }} {{ tag }}</span>
              <span class="stat-value">{{ hoursToHm(stat.stat[tag] || 0) }} / {{ hoursToHm(target) }}</span>
            </div>
          </div>

          <div class="no-plan" v-else>
            <p>无有效计划</p>
            <p class="hint">总记录时长：{{ hoursToHm(stat.total_used_hours) }}</p>
          </div>
        </div>
      </section>

      <!-- 记录列表 -->
      <section class="records-section">
        <h2>时间记录</h2>
        <div class="records-list" v-if="records.length > 0">
          <div
            v-for="(record, index) in records"
            :key="index"
            class="record-item"
          >
            <div class="record-info">
              <span class="record-tag">[{{ record.tag }}]</span>
              <span class="record-time">{{ record.start }} - {{ record.end }}</span>
              <span class="record-duration">({{ hoursToHm(record.duration) }})</span>
            </div>
            <div class="record-content">{{ record.content }}</div>
            <button class="delete-btn" @click="deleteRecord(index)">
              <Trash2 :size="14" />
            </button>
          </div>
        </div>
        <div class="empty-state" v-else>
          <p>暂无记录</p>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.day-detail-view {
  min-height: 100vh;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
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
  cursor: pointer;
  transition: all var(--transition-fast);
}

.back-btn:hover {
  background: var(--color-bg-tertiary);
}

.header h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.main-content {
  flex: 1;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.info-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.info-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.info-header h2 {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.change-btn {
  padding: var(--spacing-xs) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.change-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.plan-name {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: var(--spacing-md);
}

.stats {
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.progress-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.progress-label {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.progress-value {
  font-size: 1.25rem;
  font-weight: 700;
}

.stat-items {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.stat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-xs) 0;
  font-size: 0.875rem;
}

.stat-tag {
  color: var(--color-text-primary);
}

.stat-value {
  color: var(--color-text-secondary);
  font-family: var(--font-mono);
}

.no-plan {
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
}

.no-plan .hint {
  margin-top: var(--spacing-xs);
}

.records-section h2 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--spacing-md);
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.record-item {
  position: relative;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  padding-right: 40px;
}

.record-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.record-tag {
  font-weight: 600;
  color: var(--color-primary);
}

.record-time {
  font-family: var(--font-mono);
  color: var(--color-text-secondary);
}

.record-duration {
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
}

.record-content {
  color: var(--color-text-primary);
}

.delete-btn {
  position: absolute;
  top: var(--spacing-md);
  right: var(--spacing-md);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.delete-btn:hover {
  background: var(--color-error);
  border-color: var(--color-error);
  color: white;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--color-text-tertiary);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
</style>
