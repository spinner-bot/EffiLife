<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { hoursToHm, rgbToHex, autoBalance } from '@/services/dataService'
import { ArrowLeft, Plus, Pencil, Trash2, X, Check, Calendar, FolderKanban, RefreshCw } from 'lucide-vue-next'
import type { DayPlan, PlanItem, ScheduleRule } from '@/types'

const router = useRouter()
const appStore = useAppStore()

const plans = computed(() => appStore.plans)
const todayPlan = computed(() => appStore.todayPlan)
const scheduleRules = computed(() => appStore.scheduleRules)

// 当前视图
type ViewType = 'main' | 'plans' | 'editPlan' | 'rules' | 'editRule' | 'tempChange'
const currentView = ref<ViewType>('main')

// ============ 日计划管理 ============
const editingPlanName = ref('')
const editingPlanType = ref<'切分制' | '分配制'>('切分制')
const editingPlanBgTag = ref('')
const editingPlanColor = ref([128, 128, 128])
const editingPlanItems = ref<PlanItem[]>([{ name: '', hours: 0 }, { name: '', hours: 0 }])

function openPlanList() {
  currentView.value = 'plans'
}

function openCreatePlan() {
  editingPlanName.value = ''
  editingPlanType.value = '切分制'
  editingPlanBgTag.value = ''
  editingPlanColor.value = [128, 128, 128]
  editingPlanItems.value = [{ name: '', hours: 0 }, { name: '', hours: 0 }]
  currentView.value = 'editPlan'
}

function openEditPlan(name: string) {
  const plan = plans.value[name]
  if (!plan) return
  editingPlanName.value = name
  editingPlanType.value = plan.plan_type
  editingPlanBgTag.value = plan.bg_tag
  editingPlanColor.value = [...plan.color]
  editingPlanItems.value = plan.items.map(item => ({ ...item }))
  currentView.value = 'editPlan'
}

function addPlanItem() {
  editingPlanItems.value.push({ name: '', hours: 0 })
}

function removePlanItem(index: number) {
  const minCount = editingPlanType.value === '切分制' ? 2 : 1
  if (editingPlanItems.value.length <= minCount) return
  editingPlanItems.value.splice(index, 1)
}

async function savePlan() {
  const name = editingPlanName.value.trim()
  if (!name) {
    alert('请输入计划名称')
    return
  }

  const items = editingPlanItems.value.filter(item => item.name.trim())
  if (items.length === 0) {
    alert('请至少添加一个时间类别')
    return
  }

  if (editingPlanType.value === '切分制') {
    const total = items.reduce((sum, item) => sum + item.hours, 0)
    if (Math.abs(total - 24) > 0.01) {
      if (confirm(`总和 ${total}h ≠ 24h，是否自动平衡？`)) {
        const balanced = autoBalance(items, 24)
        editingPlanItems.value = balanced
      } else {
        return
      }
    }
    if (!editingPlanBgTag.value) {
      alert('切分制必须选择背景类别')
      return
    }
  }

  const newPlans = { ...plans.value }
  newPlans[name] = {
    plan_type: editingPlanType.value,
    items: editingPlanItems.value,
    bg_tag: editingPlanType.value === '切分制' ? editingPlanBgTag.value : '',
    color: editingPlanColor.value
  }

  await appStore.savePlans(newPlans)
  currentView.value = 'plans'
}

async function deletePlan(name: string) {
  if (!confirm(`确定删除计划"${name}"？`)) return
  const newPlans = { ...plans.value }
  delete newPlans[name]
  await appStore.savePlans(newPlans)
}

// ============ 日程规则管理 ============
const editingRuleIndex = ref(-1)
const editingRuleType = ref<'week' | 'month' | 'year' | 'month_week' | 'default'>('week')
const editingRuleValue = ref('')
const editingRulePlan = ref('')

function openRuleList() {
  currentView.value = 'rules'
}

function openCreateRule() {
  editingRuleIndex.value = -1
  editingRuleType.value = 'week'
  editingRuleValue.value = ''
  editingRulePlan.value = Object.keys(plans.value)[0] || ''
  currentView.value = 'editRule'
}

function openEditRule(index: number) {
  const rule = scheduleRules.value[index]
  if (!rule) return
  editingRuleIndex.value = index
  editingRuleType.value = rule.rule_type
  editingRuleValue.value = rule.value
  editingRulePlan.value = rule.plan_name
  currentView.value = 'editRule'
}

async function saveRule() {
  if (!editingRulePlan.value) {
    alert('请选择关联计划')
    return
  }

  if (editingRuleType.value === 'default') {
    alert('默认规则不可编辑')
    return
  }

  if (!editingRuleValue.value) {
    alert('请设置规则参数')
    return
  }

  const newRule: ScheduleRule = {
    rule_type: editingRuleType.value,
    value: editingRuleValue.value,
    plan_name: editingRulePlan.value
  }

  const newRules = [...scheduleRules.value]
  if (editingRuleIndex.value === -1) {
    // 新增（插入到默认规则前）
    newRules.splice(newRules.length - 1, 0, newRule)
  } else {
    newRules[editingRuleIndex.value] = newRule
  }

  await appStore.saveScheduleRules(newRules)
  currentView.value = 'rules'
}

async function deleteRule(index: number) {
  if (!confirm('确定删除此规则？')) return
  const newRules = [...scheduleRules.value]
  newRules.splice(index, 1)
  await appStore.saveScheduleRules(newRules)
}

async function moveRuleUp(index: number) {
  if (index <= 0) return
  const newRules = [...scheduleRules.value]
  ;[newRules[index], newRules[index - 1]] = [newRules[index - 1], newRules[index]]
  await appStore.saveScheduleRules(newRules)
}

// ============ 临时计划变更 ============
async function changeTodayPlan(planName: string) {
  if (planName === todayPlan.value.name) return
  await appStore.changeTodayPlan(planName)
  alert(`今日计划已切换为：${planName}`)
}

// ============ 周选择器 ============
const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const selectedWeekDays = ref<Set<string>>(new Set())

function toggleWeekDay(day: string) {
  const num = (weekDays.indexOf(day) + 1).toString()
  if (selectedWeekDays.value.has(num)) {
    selectedWeekDays.value.delete(num)
  } else {
    selectedWeekDays.value.add(num)
  }
}

function isSelectedWeekDay(day: string): boolean {
  const num = (weekDays.indexOf(day) + 1).toString()
  return selectedWeekDays.value.has(num)
}
</script>

<template>
  <div class="management-view">
    <header class="header">
      <button class="back-btn" @click="router.push('/')">
        <ArrowLeft :size="16" />
        <span>返回</span>
      </button>
      <h1>计划管理</h1>
    </header>

    <main class="main-content">
      <!-- 主视图 -->
      <template v-if="currentView === 'main'">
        <section class="info-card">
          <h2>今日计划</h2>
          <p class="plan-name">{{ todayPlan.name }}（{{ todayPlan.type }}）</p>
          <p class="plan-desc" v-if="plans[todayPlan.name]">
            背景类别：{{ plans[todayPlan.name].bg_tag || '无' }}
          </p>
          <div class="plan-items" v-if="plans[todayPlan.name]">
            <div v-for="item in plans[todayPlan.name].items" :key="item.name" class="plan-item">
              • {{ item.name }}：{{ item.hours }}h
            </div>
          </div>
        </section>

        <section class="action-grid">
          <button class="action-btn" @click="openRuleList">
            <Calendar :size="32" />
            <span>日程安排</span>
          </button>
          <button class="action-btn" @click="openPlanList">
            <FolderKanban :size="32" />
            <span>日计划管理</span>
          </button>
          <button class="action-btn" @click="currentView = 'tempChange'">
            <RefreshCw :size="32" />
            <span>临时计划变更</span>
          </button>
        </section>
      </template>

      <!-- 日计划列表 -->
      <template v-else-if="currentView === 'plans'">
        <div class="list-header">
          <h2>日计划管理</h2>
          <button class="btn primary" @click="openCreatePlan">
            <Plus :size="16" />
            <span>创建计划</span>
          </button>
        </div>
        <div class="plan-list">
          <div v-for="(plan, name) in plans" :key="name" class="plan-card">
            <div class="plan-color" :style="{ background: rgbToHex(...plan.color) }"></div>
            <div class="plan-info">
              <div class="plan-title">{{ name }} | {{ plan.plan_type }}</div>
              <div class="plan-meta" v-if="plan.plan_type === '分配制'">
                总时长：{{ plan.items.reduce((sum, i) => sum + i.hours, 0).toFixed(1) }}h
              </div>
              <div class="plan-meta" v-else>背景：{{ plan.bg_tag || '无' }}</div>
            </div>
            <div class="plan-actions">
              <button class="icon-btn" @click="openEditPlan(name as string)" title="编辑">
                <Pencil :size="14" />
              </button>
              <button class="icon-btn danger" @click="deletePlan(name as string)" title="删除">
                <Trash2 :size="14" />
              </button>
            </div>
          </div>
        </div>
        <button class="btn secondary full" @click="currentView = 'main'">返回</button>
      </template>

      <!-- 编辑日计划 -->
      <template v-else-if="currentView === 'editPlan'">
        <h2>{{ editingPlanName ? '编辑计划' : '创建计划' }}</h2>

        <div class="form-section">
          <label>计划名称</label>
          <input type="text" v-model="editingPlanName" class="text-input" placeholder="输入计划名称" />
        </div>

        <div class="form-section">
          <label>计划类型</label>
          <div class="radio-group">
            <label>
              <input type="radio" v-model="editingPlanType" value="切分制" />
              <span>切分制</span>
            </label>
            <label>
              <input type="radio" v-model="editingPlanType" value="分配制" />
              <span>分配制</span>
            </label>
          </div>
        </div>

        <div class="form-section">
          <label>时间类别</label>
          <div class="items-list">
            <div v-for="(item, index) in editingPlanItems" :key="index" class="item-row">
              <input type="text" v-model="item.name" placeholder="类别名称" class="text-input" />
              <input type="number" v-model="item.hours" placeholder="时长" class="time-input" step="0.5" />
              <span>h</span>
              <button
                v-if="editingPlanType === '切分制'"
                class="radio-btn"
                :class="{ active: editingPlanBgTag === item.name }"
                @click="editingPlanBgTag = item.name"
              >
                背景
              </button>
              <button class="icon-btn" @click="removePlanItem(index)">
                <X :size="14" />
              </button>
            </div>
          </div>
          <button class="btn secondary" @click="addPlanItem">
            <Plus :size="14" />
            <span>添加类别</span>
          </button>
        </div>

        <div class="form-actions">
          <button class="btn secondary" @click="currentView = 'plans'">取消</button>
          <button class="btn primary" @click="savePlan">
            <Check :size="16" />
            <span>保存</span>
          </button>
        </div>
      </template>

      <!-- 日程规则列表 -->
      <template v-else-if="currentView === 'rules'">
        <div class="list-header">
          <h2>日程自动分配规则</h2>
          <button class="btn primary" @click="openCreateRule">
            <Plus :size="16" />
            <span>添加规则</span>
          </button>
        </div>
        <div class="rule-list">
          <div v-for="(rule, index) in scheduleRules" :key="index" class="rule-card">
            <div class="rule-info">
              <template v-if="rule.rule_type === 'week'">
                星期 {{ rule.value.split(',').map(v => weekDays[parseInt(v) - 1]).join('、') }} → {{ rule.plan_name }}
              </template>
              <template v-else-if="rule.rule_type === 'month'">
                {{ rule.value.split(',').map(v => v + '月').join('、') }} → {{ rule.plan_name }}
              </template>
              <template v-else-if="rule.rule_type === 'year'">
                每年 {{ rule.value }} → {{ rule.plan_name }}
              </template>
              <template v-else-if="rule.rule_type === 'month_week'">
                每月第{{ rule.value.split('-')[0] }}个{{ weekDays[parseInt(rule.value.split('-')[1]) - 1] }} → {{ rule.plan_name }}
              </template>
              <template v-else>
                【默认兜底规则】→ {{ rule.plan_name }}
              </template>
            </div>
            <div class="rule-actions" v-if="rule.rule_type !== 'default'">
              <button class="icon-btn" @click="openEditRule(index)" title="编辑">
                <Pencil :size="14" />
              </button>
              <button class="icon-btn" @click="moveRuleUp(index)" title="上移">↑</button>
              <button class="icon-btn danger" @click="deleteRule(index)" title="删除">
                <Trash2 :size="14" />
              </button>
            </div>
          </div>
        </div>
        <button class="btn secondary full" @click="currentView = 'main'">返回</button>
      </template>

      <!-- 编辑规则 -->
      <template v-else-if="currentView === 'editRule'">
        <h2>{{ editingRuleIndex === -1 ? '添加规则' : '编辑规则' }}</h2>

        <div class="form-section">
          <label>规则类型</label>
          <div class="radio-group">
            <label>
              <input type="radio" v-model="editingRuleType" value="week" />
              <span>按星期</span>
            </label>
            <label>
              <input type="radio" v-model="editingRuleType" value="month" />
              <span>按月份</span>
            </label>
            <label>
              <input type="radio" v-model="editingRuleType" value="year" />
              <span>按年度</span>
            </label>
            <label>
              <input type="radio" v-model="editingRuleType" value="month_week" />
              <span>按月周几</span>
            </label>
          </div>
        </div>

        <div class="form-section" v-if="editingRuleType === 'week'">
          <label>选择星期</label>
          <div class="week-selector">
            <button
              v-for="day in weekDays"
              :key="day"
              class="week-btn"
              :class="{ active: isSelectedWeekDay(day) }"
              @click="toggleWeekDay(day)"
            >
              {{ day }}
            </button>
          </div>
        </div>

        <div class="form-section">
          <label>关联计划</label>
          <select v-model="editingRulePlan" class="select-input">
            <option v-for="name in Object.keys(plans)" :key="name" :value="name">{{ name }}</option>
          </select>
        </div>

        <div class="form-actions">
          <button class="btn secondary" @click="currentView = 'rules'">取消</button>
          <button class="btn primary" @click="saveRule">
            <Check :size="16" />
            <span>保存</span>
          </button>
        </div>
      </template>

      <!-- 临时计划变更 -->
      <template v-else-if="currentView === 'tempChange'">
        <h2>临时计划变更</h2>
        <p class="current-plan">当前今日计划：{{ todayPlan.name }}（{{ todayPlan.type }}）</p>
        <div class="plan-select-list">
          <button
            v-for="(plan, name) in plans"
            :key="name"
            class="plan-select-btn"
            :class="{ current: name === todayPlan.name }"
            :disabled="name === todayPlan.name"
            @click="changeTodayPlan(name as string)"
          >
            {{ name === todayPlan.name ? '✓ ' : '' }}{{ name }} | {{ plan.plan_type }}
          </button>
        </div>
        <button class="btn secondary full" @click="currentView = 'main'">返回</button>
      </template>
    </main>
  </div>
</template>

<style scoped>
.management-view {
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

.info-card h2 {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.plan-name {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: var(--spacing-xs);
}

.plan-desc {
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
  margin-bottom: var(--spacing-md);
}

.plan-items {
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.plan-item {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  padding: var(--spacing-xs) 0;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-hover);
  transform: translateY(-2px);
}

.action-btn span {
  font-size: 0.875rem;
  font-weight: 500;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.list-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
}

.plan-list, .rule-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.plan-card, .rule-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.plan-color {
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.plan-info {
  flex: 1;
}

.plan-title {
  font-weight: 500;
}

.plan-meta {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.plan-actions, .rule-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.icon-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.icon-btn.danger:hover {
  background: var(--color-error);
  border-color: var(--color-error);
  color: white;
}

.form-section {
  margin-bottom: var(--spacing-lg);
}

.form-section label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.text-input, .select-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-size: 1rem;
}

.text-input:focus, .select-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.radio-group {
  display: flex;
  gap: var(--spacing-lg);
}

.radio-group label {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
  margin-bottom: 0;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.item-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.item-row .text-input {
  flex: 1;
}

.time-input {
  width: 80px;
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  text-align: center;
}

.radio-btn {
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.radio-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.week-selector {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.week-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.week-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-xl);
}

.btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn.secondary {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.btn.secondary:hover {
  background: var(--color-bg-tertiary);
}

.btn.primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.btn.primary:hover {
  background: var(--color-primary-hover);
}

.btn.full {
  width: 100%;
  justify-content: center;
}

.current-plan {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-lg);
}

.plan-select-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.plan-select-btn {
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  text-align: left;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.plan-select-btn:hover:not(:disabled) {
  background: var(--color-bg-tertiary);
}

.plan-select-btn.current {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
  cursor: default;
}

h2 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: var(--spacing-lg);
}
</style>
