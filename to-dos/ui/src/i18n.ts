import { computed, ref } from 'vue'

export type LegacyLocale = 'zh-CN' | 'en-US'

const STORAGE_KEY = 'efflife_locale'
const messages = {
  'zh-CN': {
    all: '全部', today: '今日', overdue: '逾期', categories: '分类', otherCategories: '其他 {count} 个分类',
    emptyCategories: '空闲 {count} 个', completionRate: '完成率', completed: '已完成', total: '总计', pending: '待处理',
    inProgress: '进行中', cancelled: '已取消', shortcuts: '快捷键', new: '新建', search: '搜索', navigate: '导航', filter: '筛选', tags: '标签',
    clear: '清除{count}', sort: '排序', urgentImportant: '紧急且重要', important: '重要', urgent: '紧急', normal: '普通',
    score: '⚡ 优先排位分', newest: '最新创建', oldest: '最早创建', deadlineAsc: '截止日期 ↑', deadlineDesc: '截止日期 ↓',
    priority: '优先级', custom: '自定义', todoTitle: '待办事项', searchPlaceholder: '搜索待办... (按 / 聚焦)',
    dark: '深色', light: '浅色', auto: '自动', settings: '设置', exportJson: '导出 JSON', importJson: '导入 JSON',
    newTodo: '新建待办', selected: '已选择', items: '项', completeAction: '完成', deleteAction: '删除', cancel: '取消',
    importData: '导入数据', importDescription: '粘贴 JSON 数据或选择文件导入', pasteJson: '粘贴 JSON 数据（格式: {"todos": [...], "categories": [...]}）...', chooseFile: '选择文件', importAction: '导入',
  },
  'en-US': {
    all: 'All', today: 'Today', overdue: 'Overdue', categories: 'Categories', otherCategories: '{count} other categories',
    emptyCategories: '{count} idle categories', completionRate: 'Completion', completed: 'completed', total: 'total', pending: 'Pending',
    inProgress: 'In progress', cancelled: 'Cancelled', shortcuts: 'Shortcuts', new: 'New', search: 'Search', navigate: 'Navigate', filter: 'Filter', tags: 'Tags',
    clear: 'Clear {count}', sort: 'Sort', urgentImportant: 'Urgent & important', important: 'Important', urgent: 'Urgent', normal: 'Normal',
    score: '⚡ Priority score', newest: 'Newest', oldest: 'Oldest', deadlineAsc: 'Deadline ↑', deadlineDesc: 'Deadline ↓',
    priority: 'Priority', custom: 'Custom', todoTitle: 'To-dos', searchPlaceholder: 'Search to-dos... (press / to focus)',
    dark: 'Dark', light: 'Light', auto: 'Auto', settings: 'Settings', exportJson: 'Export JSON', importJson: 'Import JSON',
    newTodo: 'New to-do', selected: 'Selected', items: 'items', completeAction: 'Complete', deleteAction: 'Delete', cancel: 'Cancel',
    importData: 'Import data', importDescription: 'Paste JSON data or choose a file to import', pasteJson: 'Paste JSON data (format: {"todos": [...], "categories": [...]})...', chooseFile: 'Choose file', importAction: 'Import',
  },
} as const

type MessageKey = keyof typeof messages['zh-CN']
const locale = ref<LegacyLocale>(readLocale())

function readLocale(): LegacyLocale {
  if (typeof window === 'undefined') return 'zh-CN'
  const stored = window.localStorage.getItem(STORAGE_KEY)
  return stored === 'en-US' ? 'en-US' : 'zh-CN'
}

export function useLegacyI18n() {
  const t = (key: MessageKey, values: Record<string, string | number> = {}): string => {
    let value: string = messages[locale.value][key] || messages['zh-CN'][key]
    for (const [name, replacement] of Object.entries(values)) value = value.replace(`{${name}}`, String(replacement))
    return value
  }
  const setLocale = (next: LegacyLocale) => {
    locale.value = next
    if (typeof window !== 'undefined') window.localStorage.setItem(STORAGE_KEY, next)
  }
  return { locale: computed(() => locale.value), t, setLocale }
}

export function getLegacyLocale(): LegacyLocale {
  return locale.value
}
