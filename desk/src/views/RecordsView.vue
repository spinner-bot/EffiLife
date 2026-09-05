<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { hoursToHm, timeStrToMinutes, isTimeOverlap, getTodayDate } from '@/services/dataService'
import { ArrowLeft, Plus, Pencil, Trash2, X, Check } from 'lucide-vue-next'
import type { TimeRecord } from '@/types'

const router = useRouter()
const appStore = useAppStore()

const records = computed(() => appStore.todayRecords)
const todayPlan = computed(() => appStore.todayPlan)
const plans = computed(() => appStore.plans)

// 获取当前计划的标签列表
const availableTags = computed(() => {
  const plan = plans.value[todayPlan.value.name]
  return plan?.items.map(item => item.name) || []
})

// 编辑状态
const isEditing = ref(false)
const editingIndex = ref(-1)
const showForm = ref(false)

// 表单数据
const formMode = ref<'time' | 'duration'>('time')
const formStart = ref({ h: '09', m: '00' })
const formEnd = ref({ h: '10', m: '00' })
const formDuration = ref({ h: '1', m: '0' })
const formDurationRef = ref<'start' | 'end'>('start')
const formDurationTime = ref({ h: '09', m: '00' })
const formContent = ref('')
const formTag = ref('')

// 重置表单
function resetForm() {
  formMode.value = 'time'
  formStart.value = { h: '09', m: '00' }
  formEnd.value = { h: '10', m: '00' }
  formDuration.value = { h: '1', m: '0' }
  formDurationRef.value = 'start'
  formDurationTime.value = { h: '09', m: '00' }
  formContent.value = ''
  formTag.value = availableTags.value[0] || ''
  isEditing.value = false
  editingIndex.value = -1
}

// 打开新增表单
function openAddForm() {
  resetForm()
  formTag.value = availableTags.value[0] || ''
  showForm.value = true
}

// 打开编辑表单
function openEditForm(index: number) {
  const record = records.value[index]
  if (!record) return

  const [sh, sm] = record.start.split(':')
  const [eh, em] = record.end.split(':')

  formStart.value = { h: sh, m: sm }
  formEnd.value = { h: eh, m: em }
  formContent.value = record.content
  formTag.value = record.tag
  isEditing.value = true
  editingIndex.value = index
  showForm.value = true
}

// 检查时间冲突
function checkConflict(start: string, end: string, tag: string, excludeIndex = -1): string | null {
  const plan = plans.value[todayPlan.value.name]
  const planType = plan?.plan_type || '切分制'

  for (let i = 0; i < records.value.length; i++) {
    if (i === excludeIndex) continue
    const r = records.value[i]

    if (planType === '切分制') {
      if (isTimeOverlap(start, end, r.start, r.end)) {
        return `与 [${r.tag}] ${r.start}-${r.end} 冲突`
      }
    } else {
      if (r.tag === tag && isTimeOverlap(start, end, r.start, r.end)) {
        return `与 [${r.tag}] ${r.start}-${r.end} 冲突`
      }
    }
  }
  return null
}

// 保存记录
async function saveRecord() {
  if (!formContent.value.trim()) {
    alert('请填写内容')
    return
  }

  let start: string, end: string

  if (formMode.value === 'time') {
    const sh = String(formStart.value.h).padStart(2, '0')
    const sm = String(formStart.value.m).padStart(2, '0')
    const eh = String(formEnd.value.h).padStart(2, '0')
    const em = String(formEnd.value.m).padStart(2, '0')
    start = `${sh}:${sm}`
    end = `${eh}:${em}`
  } else {
    const dh = parseInt(formDuration.value.h) || 0
    const dm = parseInt(formDuration.value.m) || 0
    const durationHours = dh + dm / 60
    const refH = parseInt(formDurationTime.value.h) || 0
    const refM = parseInt(formDurationTime.value.m) || 0
    const refMinutes = refH * 60 + refM

    if (formDurationRef.value === 'start') {
      start = `${String(refH).padStart(2, '0')}:${String(refM).padStart(2, '0')}`
      const endMinutes = refMinutes + durationHours * 60
      const eh = Math.floor(endMinutes / 60) % 24
      const em = Math.floor(endMinutes % 60)
      end = `${String(eh).padStart(2, '0')}:${String(em).padStart(2, '0')}`
    } else {
      end = `${String(refH).padStart(2, '0')}:${String(refM).padStart(2, '0')}`
      const startMinutes = refMinutes - durationHours * 60
      const sh = Math.floor((startMinutes + 24 * 60) / 60) % 24
      const sm = Math.floor(((startMinutes + 24 * 60) % 60))
      start = `${String(sh).padStart(2, '0')}:${String(sm).padStart(2, '0')}`
    }
  }

  // 检查冲突
  const conflict = checkConflict(start, end, formTag.value, editingIndex.value)
  if (conflict) {
    alert('时间冲突：' + conflict)
    return
  }

  const duration = (timeStrToMinutes(end) - timeStrToMinutes(start)) / 60

  const record: TimeRecord = {
    date: getTodayDate(),
    start,
    end,
    duration,
    content: formContent.value.trim(),
    tag: formTag.value
  }

  if (isEditing.value) {
    await appStore.updateRecord(editingIndex.value, record)
  } else {
    await appStore.addRecord(record)
  }

  showForm.value = false
  resetForm()
}

// 删除记录
async function deleteRecord(index: number) {
  if (!confirm('确定删除这条记录？')) return
  await appStore.deleteRecord(index)
}

onMounted(() => {
  formTag.value = availableTags.value[0] || ''
})
</script>

<template>
  <div class="records-view">
    <header class="header">
      <button class="back-btn" @click="router.push('/')">
        <ArrowLeft :size="16" />
        <span>返回</span>
      </button>
      <h1>记录管理</h1>
      <button class="add-btn" @click="openAddForm">
        <Plus :size="16" />
        <span>新增</span>
      </button>
    </header>

    <main class="main-content">
      <!-- 记录列表 -->
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
          <div class="record-actions">
            <button class="icon-btn" @click="openEditForm(index)" title="编辑">
              <Pencil :size="14" />
            </button>
            <button class="icon-btn danger" @click="deleteRecord(index)" title="删除">
              <Trash2 :size="14" />
            </button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div class="empty-state" v-else>
        <p>暂无记录</p>
        <p class="hint">点击"新增"按钮开始记录时间</p>
      </div>
    </main>

    <!-- 表单弹窗 -->
    <div class="modal-overlay" v-if="showForm" @click.self="showForm = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ isEditing ? '编辑记录' : '新增记录' }}</h2>
          <button class="close-btn" @click="showForm = false">
            <X :size="20" />
          </button>
        </div>

        <div class="modal-body">
          <!-- 输入模式切换 -->
          <div class="mode-switch">
            <button
              :class="['mode-btn', { active: formMode === 'time' }]"
              @click="formMode = 'time'"
            >
              开始 + 结束
            </button>
            <button
              :class="['mode-btn', { active: formMode === 'duration' }]"
              @click="formMode = 'duration'"
            >
              时长 + 单点
            </button>
          </div>

          <!-- 时间模式 -->
          <div class="form-section" v-if="formMode === 'time'">
            <div class="time-input-row">
              <label>开始：</label>
              <input type="number" v-model="formStart.h" min="0" max="23" class="time-input" />
              <span>:</span>
              <input type="number" v-model="formStart.m" min="0" max="59" class="time-input" />
            </div>
            <div class="time-input-row">
              <label>结束：</label>
              <input type="number" v-model="formEnd.h" min="0" max="23" class="time-input" />
              <span>:</span>
              <input type="number" v-model="formEnd.m" min="0" max="59" class="time-input" />
            </div>
          </div>

          <!-- 时长模式 -->
          <div class="form-section" v-else>
            <div class="time-input-row">
              <label>时长：</label>
              <input type="number" v-model="formDuration.h" min="0" class="time-input small" />
              <span>时</span>
              <input type="number" v-model="formDuration.m" min="0" max="59" class="time-input small" />
              <span>分</span>
            </div>
            <div class="time-input-row">
              <label>参考时间：</label>
              <input type="number" v-model="formDurationTime.h" min="0" max="23" class="time-input" />
              <span>:</span>
              <input type="number" v-model="formDurationTime.m" min="0" max="59" class="time-input" />
            </div>
            <div class="radio-group">
              <label>
                <input type="radio" v-model="formDurationRef" value="start" />
                <span>以上为开始时间</span>
              </label>
              <label>
                <input type="radio" v-model="formDurationRef" value="end" />
                <span>以上为结束时间</span>
              </label>
            </div>
          </div>

          <!-- 内容 -->
          <div class="form-section">
            <label>内容：</label>
            <input
              type="text"
              v-model="formContent"
              placeholder="请输入内容"
              class="text-input"
            />
          </div>

          <!-- 标签 -->
          <div class="form-section">
            <label>类别：</label>
            <select v-model="formTag" class="select-input">
              <option v-for="tag in availableTags" :key="tag" :value="tag">{{ tag }}</option>
            </select>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn secondary" @click="showForm = false">取消</button>
          <button class="btn primary" @click="saveRecord">
            <Check :size="16" />
            <span>保存</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.records-view {
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

.back-btn, .add-btn {
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

.back-btn:hover, .add-btn:hover {
  background: var(--color-bg-tertiary);
}

.add-btn {
  margin-left: auto;
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.add-btn:hover {
  background: var(--color-primary-hover);
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

.records-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.record-item {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  transition: all var(--transition-fast);
}

.record-item:hover {
  border-color: var(--color-border-hover);
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
  margin-bottom: var(--spacing-sm);
}

.record-actions {
  display: flex;
  gap: var(--spacing-xs);
  justify-content: flex-end;
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

.empty-state {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-tertiary);
}

.empty-state .hint {
  font-size: 0.875rem;
  margin-top: var(--spacing-sm);
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn var(--transition-fast);
}

.modal {
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideUp var(--transition-normal);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.modal-header h2 {
  font-size: 1.125rem;
  font-weight: 600;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.modal-body {
  padding: var(--spacing-lg);
  overflow-y: auto;
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

.mode-switch {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.mode-btn {
  flex: 1;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mode-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.time-input-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.time-input-row label {
  width: 80px;
  margin-bottom: 0;
}

.time-input {
  width: 60px;
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  text-align: center;
  font-family: var(--font-mono);
}

.time-input.small {
  width: 50px;
}

.time-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.radio-group {
  display: flex;
  gap: var(--spacing-lg);
  margin-top: var(--spacing-sm);
}

.radio-group label {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
  margin-bottom: 0;
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

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
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

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
