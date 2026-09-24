import { ref } from 'vue'

export type Locale = 'zh-CN' | 'en-US'

const STORAGE_KEY = 'efflife_locale'

const catalogs: Record<Locale, Record<string, string>> = {
  'zh-CN': {
    'locale.label': '语言',
    'locale.zh-CN': '简体中文',
    'locale.en-US': 'English',
    'nav.plan': '计划',
    'nav.calendar': '日历',
    'nav.checkin': '打卡',
    'nav.tasks': '待办',
    'nav.settings': '设置',
    'tasks.workspace': '统一工作台',
    'tasks.title': '待办中心',
    'tasks.pending': '项待处理',
    'tasks.completed': '项已完成',
    'tasks.new': '新建待办',
    'tasks.priority': '优先级',
    'tasks.plan': '关联计划',
    'tasks.planTask': '计划任务',
    'tasks.noPlan': '不关联',
    'tasks.noTask': '不指定',
    'tasks.addPlaceholder': '添加一个可执行的任务…',
    'tasks.add': '添加',
    'tasks.active': '待处理',
    'tasks.all': '全部',
    'tasks.completedTab': '已完成',
    'tasks.loading': '正在加载待办…',
    'tasks.emptyCompleted': '还没有完成的任务',
    'tasks.emptyActive': '今天没有待办',
    'tasks.emptyHint': '把下一步写下来，时间管理从行动开始。',
    'tasks.serviceUnavailable': '计划服务未连接，仍可正常管理待办',
    'tasks.edit': '编辑任务',
    'tasks.editContent': '编辑待办内容',
    'tasks.cancel': '取消',
    'tasks.save': '保存',
    'tasks.saving': '保存中…',
    'tasks.unlinked': '不关联',
    'priority.urgentImportant': '紧急重要',
    'priority.important': '重要',
    'priority.urgent': '紧急',
    'priority.normal': '普通',
    'tasks.error.load': '待办加载失败',
    'tasks.error.create': '待办创建失败',
    'tasks.error.update': '待办更新失败',
    'tasks.error.save': '待办保存失败',
    'tasks.error.delete': '待办删除失败',
  },
  'en-US': {
    'locale.label': 'Language',
    'locale.zh-CN': '简体中文',
    'locale.en-US': 'English',
    'nav.plan': 'Plans',
    'nav.calendar': 'Calendar',
    'nav.checkin': 'Check-in',
    'nav.tasks': 'Tasks',
    'nav.settings': 'Settings',
    'tasks.workspace': 'Unified workspace',
    'tasks.title': 'Task center',
    'tasks.pending': 'pending',
    'tasks.completed': 'completed',
    'tasks.new': 'New task',
    'tasks.priority': 'Priority',
    'tasks.plan': 'Linked plan',
    'tasks.planTask': 'Plan task',
    'tasks.noPlan': 'Unlinked',
    'tasks.noTask': 'No specific task',
    'tasks.addPlaceholder': 'Add an actionable task…',
    'tasks.add': 'Add',
    'tasks.active': 'Active',
    'tasks.all': 'All',
    'tasks.completedTab': 'Completed',
    'tasks.loading': 'Loading tasks…',
    'tasks.emptyCompleted': 'No completed tasks yet',
    'tasks.emptyActive': 'Nothing is pending today',
    'tasks.emptyHint': 'Write down the next action to get started.',
    'tasks.serviceUnavailable': 'Plan service unavailable; task management still works',
    'tasks.edit': 'Edit task',
    'tasks.editContent': 'Task content',
    'tasks.cancel': 'Cancel',
    'tasks.save': 'Save',
    'tasks.saving': 'Saving…',
    'tasks.unlinked': 'Unlinked',
    'priority.urgentImportant': 'Urgent & important',
    'priority.important': 'Important',
    'priority.urgent': 'Urgent',
    'priority.normal': 'Normal',
    'tasks.error.load': 'Unable to load tasks',
    'tasks.error.create': 'Unable to create task',
    'tasks.error.update': 'Unable to update task',
    'tasks.error.save': 'Unable to save task',
    'tasks.error.delete': 'Unable to delete task',
  },
}

function readLocale(): Locale {
  const stored = localStorage.getItem(STORAGE_KEY)
  return stored === 'en-US' ? 'en-US' : 'zh-CN'
}

export const currentLocale = ref<Locale>(readLocale())

export function setLocale(next: string): void {
  currentLocale.value = next === 'en-US' ? 'en-US' : 'zh-CN'
  localStorage.setItem(STORAGE_KEY, currentLocale.value)
}

export function translate(key: string, params: Record<string, string | number> = {}): string {
  const value = catalogs[currentLocale.value][key] || catalogs['zh-CN'][key] || key
  return value.replace(/\{(\w+)\}/g, (_match, name: string) => String(params[name] ?? `{${name}}`))
}

export function useI18n() {
  return {
    locale: currentLocale,
    setLocale,
    t: translate,
    localeOptions: ['zh-CN', 'en-US'] as Locale[],
  }
}
