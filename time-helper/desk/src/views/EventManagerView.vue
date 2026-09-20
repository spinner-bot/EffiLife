<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Bell, Clock, Inbox, Check, Trash2 } from 'lucide-vue-next'
import { EventSystem } from '@/audio'
import { CheckinSystem } from '@/data'
import type { EventType, WarningRule, InboxEntry } from '@/audio'

const router = useRouter()

const eventSettings = ref(EventSystem.getSettings())

// 基础事件
const baseEventTypes: Array<{ type: EventType; name: string; description: string }> = [
  { type: 'plan_complete_100', name: '计划完美完成', description: '当天计划完成度达到100%' },
  { type: 'plan_complete_90', name: '计划即将完成', description: '当天计划完成度达到90%' },
  { type: 'plan_complete_50', name: '半程完成', description: '当天计划完成度达到50%' },
  { type: 'record_added', name: '记录添加', description: '添加时间记录时' },
  { type: 'plan_changed', name: '计划切换', description: '切换日计划时' },
  { type: 'achievement_unlocked', name: '成就解锁', description: '解锁新成就时' },
  { type: 'checkin_complete', name: '打卡完成', description: '成功打卡时' },
  { type: 'streak_milestone', name: '连续打卡里程碑', description: '达到7/14/30/60/90/180/365天' },
  { type: 'idle_reminder', name: '空闲提醒', description: '长时间未操作时' },
  { type: 'weekly_summary', name: '周报摘要', description: '每周汇总数据' },
  { type: 'daily_first_record', name: '每日首条记录', description: '当天第一条记录添加时' }
]

// 收件箱
const inbox = computed(() => EventSystem.getEventInbox())
const unreadCount = computed(() => EventSystem.getUnreadCount())
const readCount = computed(() => inbox.value.filter(e => e.read).length)
const totalCount = computed(() => inbox.value.length)
const warningRules = computed(() => eventSettings.value.warningRules)
const sortedRules = computed(() =>
  [...warningRules.value].sort((a, b) => (a.hour * 60 + a.minute) - (b.hour * 60 + b.minute))
)

// 当前视图
type ViewType = 'inbox' | 'events' | 'warnings'
const currentView = ref<ViewType>('inbox')

// 收件箱分类过滤
type InboxFilter = 'all' | 'achievement' | 'event' | 'reminder'
const inboxFilter = ref<InboxFilter>('all')

// 分类过滤后的收件箱
const filteredInbox = computed(() => {
  if (inboxFilter.value === 'all') return inbox.value
  return inbox.value.filter(entry => {
    switch (inboxFilter.value) {
      case 'achievement':
        return entry.type === 'plan_complete_100' ||
               entry.type === 'achievement_unlocked' ||
               entry.type === 'checkin_complete' ||
               entry.type === 'streak_milestone'
      case 'event':
        return entry.type === 'plan_complete_90' ||
               entry.type === 'plan_complete_50' ||
               entry.type === 'record_added' ||
               entry.type === 'record_deleted' ||
               entry.type === 'plan_changed' ||
               entry.type === 'weekly_summary' ||
               entry.type === 'daily_first_record'
      case 'reminder':
        return entry.type === 'progress_warning' ||
               entry.type === 'idle_reminder' ||
               !!entry.checkinPlanName
      default:
        return true
    }
  })
})

// 各分类的未读数
const filterCounts = computed(() => {
  const all = inbox.value.length
  const achievement = inbox.value.filter(e =>
    e.type === 'plan_complete_100' || e.type === 'achievement_unlocked' ||
    e.type === 'checkin_complete' || e.type === 'streak_milestone'
  ).length
  const event = inbox.value.filter(e =>
    e.type === 'plan_complete_90' || e.type === 'plan_complete_50' ||
    e.type === 'record_added' || e.type === 'record_deleted' ||
    e.type === 'plan_changed' || e.type === 'weekly_summary' ||
    e.type === 'daily_first_record'
  ).length
  const reminder = inbox.value.filter(e =>
    e.type === 'progress_warning' || e.type === 'idle_reminder' || !!e.checkinPlanName
  ).length
  return { all, achievement, event, reminder }
})

function setFilter(filter: InboxFilter) {
  inboxFilter.value = filter
}

// 预警规则编辑
const showRuleForm = ref(false)
const editingRuleId = ref<string | null>(null)
const newRule = ref({ hour: 12, minute: 0, threshold: 50, enabled: true })

// 自动清空时限选项
const autoCleanOptions: Array<{ value: 1 | 3 | 7 | 30 | -1; label: string }> = [
  { value: 1, label: '24小时' },
  { value: 3, label: '72小时' },
  { value: 7, label: '7天' },
  { value: 30, label: '30天' },
  { value: -1, label: '永不' }
]

function setAutoCleanDays(days: 1 | 3 | 7 | 30 | -1) {
  const currentDays = eventSettings.value.autoCleanDays

  // 如果是相同的设置，不需要确认
  if (currentDays === days) return

  // 计算会被删除的事件数量
  // 只有当新时限比旧时限更短时，才会删除事件
  let willDeleteCount = 0
  let willDelete = false

  if (days !== -1) {
    const cutoffTime = Date.now() - days * 24 * 60 * 60 * 1000
    willDeleteCount = inbox.value.filter(entry => {
      if (!entry.read) return false
      return new Date(entry.triggeredAt).getTime() <= cutoffTime
    }).length
    willDelete = willDeleteCount > 0
  }

  // 生成确认信息
  let confirmMsg = `将已读事件自动清空时间修改为"${autoCleanOptions.find(o => o.value === days)?.label}"？`

  if (willDelete) {
    confirmMsg += `\n\n⚠️ 注意：这会导致 ${willDeleteCount} 个已读事件被立即删除，且无法恢复！`
  } else if (days !== -1 && currentDays !== -1 && days < currentDays) {
    // 新时限更短，但当前没有符合条件的事件
    confirmMsg += `\n\n当前没有符合新时限的已读事件，设置后将立即生效。`
  }

  if (!confirm(confirmMsg)) return

  EventSystem.updateSettings({ autoCleanDays: days })
  eventSettings.value = EventSystem.getSettings()
}

// ========= 事件开关 =========
function toggleEvent(type: EventType | string) {
  eventSettings.value.enabled[type] = !eventSettings.value.enabled[type]
  EventSystem.updateSettings({ enabled: eventSettings.value.enabled })
}

function testEvent(type: EventType) {
  switch (type) {
    case 'plan_complete_100':
      EventSystem.triggerEvent('plan_complete_100', '完美达成！', '今天的计划已100%完成！')
      break
    case 'plan_complete_90':
      EventSystem.triggerEvent('plan_complete_90', '即将达成！', '计划已完成90%，加油！')
      break
    case 'plan_complete_50':
      EventSystem.triggerEvent('plan_complete_50', '半程完成！', '计划已完成50%，继续加油！')
      break
    case 'progress_warning':
      EventSystem.triggerEvent('progress_warning', '进度预警', '已是18:00，完成度仅30%（目标50%）')
      break
    case 'record_added':
      EventSystem.triggerEvent('record_added', '记录已添加', '新的时间记录已保存')
      break
    case 'record_deleted':
      EventSystem.triggerEvent('record_deleted', '记录已删除', '一条时间记录已被删除')
      break
    case 'plan_changed':
      EventSystem.triggerEvent('plan_changed', '计划已切换', '已切换到新的日计划')
      break
    case 'achievement_unlocked':
      EventSystem.triggerEvent('achievement_unlocked', '成就解锁！', '恭喜你达成新成就！')
      break
    case 'checkin_complete':
      EventSystem.triggerEvent('checkin_complete', '打卡成功！', '连续打卡 7 天 🔥')
      break
    case 'streak_milestone':
      EventSystem.triggerEvent('streak_milestone', '一周坚持！', '连续打卡7天，这是一个了不起的里程碑！🔥')
      break
    case 'idle_reminder':
      EventSystem.triggerEvent('idle_reminder', '休息一下？', '你已经30分钟没有操作了，记得记录时间哦')
      break
    case 'weekly_summary':
      EventSystem.triggerEvent('weekly_summary', '本周摘要', '记录25条，共38.5小时，平均完成85%，打卡6天')
      break
    case 'daily_first_record':
      EventSystem.triggerEvent('daily_first_record', '新的一天', '今天的第一条记录已开始，「工作日」加油！')
      break
  }
}

// ========= 收件箱 =========
function markAsRead(entry: InboxEntry) {
  EventSystem.markAsRead(entry.id)
}

function markAllAsRead() {
  EventSystem.markAllAsRead()
}

function deleteEntry(entryId: string) {
  EventSystem.deleteInboxEntry(entryId)
}

function clearRead() {
  if (!confirm('确定清空所有已读事件记录？此操作不可恢复。')) return
  EventSystem.clearReadInbox()
}

// 从收件箱条目进行补打卡
function handleCheckinFromInbox(entry: InboxEntry) {
  if (!entry.checkinPlanName || !entry.checkinDate) return

  // 执行补打卡
  const result = CheckinSystem.checkinForDate(entry.checkinDate, entry.checkinPlanName, 100)

  if (result !== null) {
    // 打卡成功，显示成功提示
    alert(`补打卡成功！\n日期：${entry.checkinDate}\n计划：${entry.checkinPlanName}\n连续 ${result} 天 🔥`)

    // 删除这个收件箱条目
    EventSystem.removeCheckinReminder(entry.id)
  } else {
    alert('打卡失败，可能已经打过卡或日期无效')
  }
}

function formatTriggerTime(entry: InboxEntry): string {
  const d = new Date(entry.triggeredAt)
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const hour = d.getHours().toString().padStart(2, '0')
  const minute = d.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hour}:${minute}`
}

function getEventIcon(type: EventType): string {
  switch (type) {
    case 'plan_complete_100': return '🎉'
    case 'plan_complete_90': return '⭐'
    case 'progress_warning': return '⚠️'
    case 'record_added': return '📝'
    case 'plan_changed': return '🔄'
    case 'achievement_unlocked': return '🏆'
    default: return '🔔'
  }
}

function getEventStyle(type: EventType): string {
  switch (type) {
    case 'plan_complete_100':
    case 'achievement_unlocked':
      return 'achievement'
    case 'plan_complete_90':
      return 'success'
    case 'progress_warning':
      return 'warning'
    default:
      return 'info'
  }
}

// ========= 预警规则管理 =========
function startAddRule() {
  editingRuleId.value = null
  newRule.value = { hour: 12, minute: 0, threshold: 50, enabled: true }
  showRuleForm.value = true
}

function startEditRule(rule: WarningRule) {
  editingRuleId.value = rule.id
  newRule.value = { hour: rule.hour, minute: rule.minute, threshold: rule.threshold, enabled: rule.enabled }
  showRuleForm.value = true
}

function saveRule() {
  // 验证小时
  if (newRule.value.hour < 0 || newRule.value.hour > 23) {
    alert('小时必须在 0-23 之间')
    return
  }
  // 验证分钟
  if (newRule.value.minute < 0 || newRule.value.minute > 59) {
    alert('分钟必须在 0-59 之间')
    return
  }
  // 验证阈值
  if (newRule.value.threshold < 0 || newRule.value.threshold > 100) {
    alert('阈值必须在 0-100 之间')
    return
  }

  if (editingRuleId.value) {
    EventSystem.updateWarningRule(editingRuleId.value, { ...newRule.value })
  } else {
    EventSystem.addWarningRule({ ...newRule.value })
  }
  eventSettings.value = EventSystem.getSettings()
  showRuleForm.value = false
}

function cancelRule() {
  showRuleForm.value = false
  editingRuleId.value = null
}

function deleteRule(id: string) {
  if (!confirm('确定删除这条预警规则？')) return
  EventSystem.removeWarningRule(id)
  eventSettings.value = EventSystem.getSettings()
}

function toggleRule(rule: WarningRule) {
  EventSystem.updateWarningRule(rule.id, { enabled: !rule.enabled })
  eventSettings.value = EventSystem.getSettings()
}

function formatTime(rule: WarningRule): string {
  return `${rule.hour.toString().padStart(2, '0')}:${rule.minute.toString().padStart(2, '0')}`
}

function testWarning(rule: WarningRule) {
  const timeStr = formatTime(rule)
  EventSystem.triggerEvent('progress_warning', '进度预警', `已是${timeStr}，完成度仅${rule.threshold - 10}%（目标${rule.threshold}%）`)
}
</script>

<template>
  <div class="event-manager-view">
    <header class="header">
      <button class="back-btn" @click="router.push('/settings')">
        <ArrowLeft :size="16" />
        <span>返回设置</span>
      </button>
      <h1>事件管理</h1>
    </header>

    <main class="main-content">
      <div class="tab-bar">
        <button class="tab-btn" :class="{ active: currentView === 'inbox' }" @click="currentView = 'inbox'">
          <Inbox :size="18" />
          <span>收件箱</span>
          <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
        </button>
        <button class="tab-btn" :class="{ active: currentView === 'events' }" @click="currentView = 'events'">
          <Bell :size="18" />
          <span>事件</span>
        </button>
        <button class="tab-btn" :class="{ active: currentView === 'warnings' }" @click="currentView = 'warnings'">
          <Clock :size="18" />
          <span>预警</span>
        </button>
      </div>

      <!-- ============ 收件箱 ============ -->
      <template v-if="currentView === 'inbox'">
        <section class="section-card">
          <div class="section-header">
            <h2>事件历史</h2>
            <div class="header-actions">
              <span v-if="inbox.length > 0" class="inbox-stats">
                已读：{{ readCount }}/{{ totalCount }}
              </span>
              <button v-if="unreadCount > 0" class="text-btn" @click="markAllAsRead">
                <Check :size="14" />
                全部已读
              </button>
              <button v-if="readCount > 0" class="text-btn danger" @click="clearRead">
                <Trash2 :size="14" />
                清空已读
              </button>
            </div>
          </div>

          <!-- 分类过滤器 -->
          <div class="inbox-filters" v-if="inbox.length > 0">
            <button
              class="filter-pill"
              :class="{ active: inboxFilter === 'all' }"
              @click="setFilter('all')"
            >
              全部
              <span class="filter-count">{{ filterCounts.all }}</span>
            </button>
            <button
              class="filter-pill"
              :class="{ active: inboxFilter === 'achievement' }"
              @click="setFilter('achievement')"
            >
              🏆 成就
              <span class="filter-count">{{ filterCounts.achievement }}</span>
            </button>
            <button
              class="filter-pill"
              :class="{ active: inboxFilter === 'event' }"
              @click="setFilter('event')"
            >
              📋 事件
              <span class="filter-count">{{ filterCounts.event }}</span>
            </button>
            <button
              class="filter-pill"
              :class="{ active: inboxFilter === 'reminder' }"
              @click="setFilter('reminder')"
            >
              🔔 提醒
              <span class="filter-count">{{ filterCounts.reminder }}</span>
            </button>
          </div>

          <div v-if="filteredInbox.length === 0" class="empty-state">
            <Inbox :size="48" class="empty-icon" />
            <p v-if="inbox.length === 0">暂无事件记录</p>
            <p v-else>该分类下暂无事件</p>
            <p class="hint" v-if="inbox.length === 0">触发的事件会显示在这里</p>
          </div>

          <div v-else class="inbox-list">
            <div
              v-for="entry in filteredInbox"
              :key="entry.id"
              class="inbox-item"
              :class="[getEventStyle(entry.type), { unread: !entry.read, checkinable: entry.checkinPlanName }]"
              @click="markAsRead(entry)"
            >
              <div class="inbox-icon">
                {{ entry.icon || getEventIcon(entry.type) }}
              </div>
              <div class="inbox-body">
                <div class="inbox-title">
                  {{ entry.title }}
                  <span v-if="!entry.read" class="unread-dot"></span>
                </div>
                <div class="inbox-message">{{ entry.message }}</div>
                <div class="inbox-meta">
                  <span class="inbox-time">{{ formatTriggerTime(entry) }}</span>
                  <span v-if="entry.scheduledTime" class="inbox-scheduled">
                    预定 {{ entry.scheduledTime }}
                  </span>
                </div>
              </div>
              <!-- 打卡按钮（仅对可打卡条目显示） -->
              <button
                v-if="entry.checkinPlanName && entry.checkinDate"
                class="checkin-btn"
                @click.stop="handleCheckinFromInbox(entry)"
                title="补打卡"
              >
                <Check :size="14" />
                <span>打卡</span>
              </button>
              <button class="delete-btn" @click.stop="deleteEntry(entry.id)" title="删除">
                <Trash2 :size="14" />
              </button>
            </div>
          </div>

          <!-- 自动清空设置 -->
          <div class="auto-clean-setting" v-if="inbox.length > 0">
            <span class="setting-label">已读事件自动清空：</span>
            <div class="option-pills">
              <button
                v-for="opt in autoCleanOptions"
                :key="opt.value"
                class="pill-btn"
                :class="{ active: eventSettings.autoCleanDays === opt.value }"
                @click="setAutoCleanDays(opt.value)"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>
        </section>
      </template>

      <!-- ============ 事件设置 ============ -->
      <template v-else-if="currentView === 'events'">
        <section class="section-card">
          <div class="section-header">
            <h2>事件通知</h2>
          </div>
          <p class="section-desc">
            配置哪些事件触发时显示弹窗并播放音效。所有事件都会记录在收件箱中。
          </p>

          <div class="event-list">
            <div v-for="event in baseEventTypes" :key="event.type" class="event-item">
              <div class="event-info">
                <span class="event-name">{{ event.name }}</span>
                <span class="event-desc">{{ event.description }}</span>
              </div>
              <div class="event-controls">
                <label class="toggle-inline">
                  <input type="checkbox" :checked="eventSettings.enabled[event.type]" @change="toggleEvent(event.type)" />
                </label>
                <button class="test-btn" @click="testEvent(event.type)" title="测试">
                  <Bell :size="14" />
                </button>
              </div>
            </div>
          </div>
        </section>
      </template>

      <!-- ============ 预警规则 ============ -->
      <template v-else-if="currentView === 'warnings'">
        <section class="section-card">
          <div class="section-header">
            <h2>进度预警</h2>
            <label class="toggle-inline">
              <input type="checkbox" :checked="eventSettings.enabled.progress_warning" @change="toggleEvent('progress_warning')" />
              <span>启用</span>
            </label>
          </div>
          <p class="section-desc">
            到达指定时间后，若完成度低于阈值则发出预警。软件期间关闭，重新打开后也会补发遗漏的预警。
          </p>

          <div class="warning-list">
            <div
              v-for="rule in sortedRules"
              :key="rule.id"
              class="warning-item"
              :class="{ disabled: !rule.enabled }"
            >
              <div class="warning-main" @click="startEditRule(rule)">
                <div class="warning-time">
                  <Clock :size="16" />
                  <span class="time-text">{{ formatTime(rule) }}</span>
                </div>
                <div class="warning-detail">
                  完成度低于 <strong>{{ rule.threshold }}%</strong> 时预警
                </div>
              </div>
              <div class="warning-actions">
                <label class="toggle-inline">
                  <input type="checkbox" :checked="rule.enabled" @change="toggleRule(rule)" />
                </label>
                <button class="test-btn" @click="testWarning(rule)" title="测试">
                  <Bell :size="14" />
                </button>
                <button class="test-btn danger" @click="deleteRule(rule.id)" title="删除">
                  <Trash2 :size="14" />
                </button>
              </div>
            </div>

            <button class="add-rule-btn" @click="startAddRule">
              <span class="plus">+</span>
              <span>添加预警规则</span>
            </button>
          </div>
        </section>

        <!-- 规则编辑弹窗 -->
        <div v-if="showRuleForm" class="modal-overlay" @click.self="cancelRule">
          <div class="modal">
            <h3>{{ editingRuleId ? '编辑预警规则' : '添加预警规则' }}</h3>

            <div class="form-row">
              <label>触发时间</label>
              <div class="time-picker">
                <div class="time-unit">
                  <label>时</label>
                  <input type="number" v-model.number="newRule.hour" min="0" max="23" />
                </div>
                <span class="time-sep">:</span>
                <div class="time-unit">
                  <label>分</label>
                  <input type="number" v-model.number="newRule.minute" min="0" max="59" step="5" />
                </div>
              </div>
            </div>

            <div class="form-row">
              <label>完成度阈值</label>
              <div class="threshold-picker">
                <input type="range" v-model.number="newRule.threshold" min="0" max="100" step="5" />
                <span class="threshold-value">{{ newRule.threshold }}%</span>
              </div>
              <p class="form-hint">当时间到达设定时刻，若完成度低于此值则发出预警</p>
            </div>

            <div class="modal-actions">
              <button class="btn secondary" @click="cancelRule">取消</button>
              <button class="btn primary" @click="saveRule">保存</button>
            </div>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<style scoped>
.event-manager-view {
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

.back-btn:hover { background: var(--color-bg-tertiary); }

.header h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.main-content {
  flex: 1;
  max-width: 700px;
  margin: 0 auto;
  width: 100%;
}

.tab-bar {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-xs);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.tab-btn:hover { color: var(--color-text-primary); }

.tab-btn.active {
  background: var(--color-bg);
  color: var(--color-text-primary);
  box-shadow: var(--shadow-sm);
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: var(--color-error);
  color: white;
  font-size: 0.6875rem;
  font-weight: 600;
  border-radius: 9px;
  margin-left: 2px;
}

.section-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.section-header h2 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.inbox-stats {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
}

.text-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 0.8125rem;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.text-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.text-btn.danger:hover {
  background: var(--color-error);
  color: white;
}

.section-desc {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-md) 0;
  line-height: 1.5;
}

/* 收件箱过滤器 */
.inbox-filters {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-xs);
  background: var(--color-bg);
  border-radius: var(--radius-md);
  flex-wrap: wrap;
}

.filter-pill {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.filter-pill:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.filter-pill.active {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  box-shadow: var(--shadow-sm);
  font-weight: 500;
}

.filter-count {
  font-size: 0.6875rem;
  font-family: var(--font-mono);
  padding: 0 4px;
  background: var(--color-bg-tertiary);
  border-radius: 8px;
  min-width: 16px;
  text-align: center;
  line-height: 16px;
}

.filter-pill.active .filter-count {
  background: var(--color-primary);
  color: white;
}

/* 收件箱 */
.empty-state {
  text-align: center;
  padding: var(--spacing-2xl) var(--spacing-lg);
  color: var(--color-text-tertiary);
}

.empty-icon {
  opacity: 0.3;
  margin-bottom: var(--spacing-md);
}

.empty-state p {
  margin: var(--spacing-xs) 0;
}

.empty-state .hint {
  font-size: 0.8125rem;
}

.inbox-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.inbox-item {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-left: 3px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.inbox-item:hover {
  border-color: var(--color-border-hover);
}

.inbox-item.unread {
  background: var(--color-bg);
  border-left-color: var(--color-primary);
}

.inbox-item.achievement { border-left-color: #ffd700; }
.inbox-item.achievement.unread { border-left-color: #ffd700; }
.inbox-item.success { border-left-color: #4ade80; }
.inbox-item.warning { border-left-color: #fbbf24; }
.inbox-item.info { border-left-color: #60a5fa; }

.inbox-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
  width: 32px;
  text-align: center;
}

.inbox-body {
  flex: 1;
  min-width: 0;
}

.inbox-title {
  font-size: 0.9375rem;
  font-weight: 600;
  margin-bottom: 2px;
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.unread-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
}

.inbox-message {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
  margin-bottom: var(--spacing-xs);
}

.inbox-meta {
  display: flex;
  gap: var(--spacing-md);
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.inbox-scheduled {
  color: var(--color-warning);
}

.delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
  align-self: flex-start;
}

.delete-btn:hover {
  background: var(--color-error);
  color: white;
}

/* 可打卡条目样式 */
.inbox-item.checkinable {
  border-left-color: var(--color-primary, #f59e0b);
  background: linear-gradient(90deg, rgba(var(--color-primary-rgb, 245, 158, 11), 0.05) 0%, transparent 50%);
}

.checkin-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--color-primary, #f59e0b);
  color: white;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
  align-self: center;
}

.checkin-btn:hover {
  background: var(--color-primary-hover, #d97706);
  transform: scale(1.05);
}

.checkin-btn:active {
  transform: scale(0.95);
}

.auto-clean-setting {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.setting-label {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.option-pills {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.pill-btn {
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.pill-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.pill-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

/* 事件列表 */
.event-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.event-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg);
  border-radius: var(--radius-md);
}

.event-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.event-name { font-size: 0.875rem; font-weight: 500; }
.event-desc { font-size: 0.75rem; color: var(--color-text-tertiary); }

.event-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.toggle-inline {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
}

.toggle-inline input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.test-btn {
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

.test-btn:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.test-btn.danger:hover {
  background: var(--color-error);
  border-color: var(--color-error);
}

/* 预警规则 */
.warning-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.warning-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.warning-item:hover { border-color: var(--color-border-hover); }
.warning-item.disabled { opacity: 0.5; }

.warning-main {
  flex: 1;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.warning-time {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  color: var(--color-primary);
}

.time-text {
  font-size: 1.25rem;
  font-weight: 700;
  font-family: var(--font-mono);
}

.warning-detail {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}

.warning-detail strong {
  color: var(--color-text-primary);
  font-weight: 600;
}

.warning-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.add-rule-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-top: var(--spacing-sm);
}

.add-rule-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.add-rule-btn .plus {
  font-size: 1.25rem;
  font-weight: bold;
}

/* 弹窗 */
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
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  width: 90%;
  max-width: 420px;
  animation: slideUp var(--transition-normal);
}

.modal h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-lg) 0;
}

.form-row {
  margin-bottom: var(--spacing-lg);
}

.form-row > label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.time-picker {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.time-unit {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.time-unit label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.time-unit input {
  width: 60px;
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  text-align: center;
  font-size: 1.125rem;
  font-family: var(--font-mono);
}

.time-sep {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--color-text-secondary);
  margin-top: 16px;
}

.threshold-picker {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.threshold-picker input[type="range"] {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  outline: none;
}

.threshold-picker input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
}

.threshold-value {
  width: 50px;
  text-align: right;
  font-size: 1.125rem;
  font-weight: 600;
  font-family: var(--font-mono);
  color: var(--color-primary);
}

.form-hint {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin: var(--spacing-xs) 0 0 0;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-xl);
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
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

.btn.secondary:hover { background: var(--color-bg-tertiary); }

.btn.primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.btn.primary:hover { background: var(--color-primary-hover); }

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
