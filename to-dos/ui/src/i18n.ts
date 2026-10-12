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
    emptyTitle: '暂无待办事项', emptyDescription: '一切就绪！点击下方按钮或按 N 键创建第一个待办', organizeTip: '使用分类和标签组织待办', deadlineTip: '设置截止日期跟踪进度',
    overdueDays: '已逾期 {count} 天', dueToday: '今天截止', dueTomorrow: '明天截止', dueInDays: '{count} 天后截止', cancelComplete: '取消完成', markComplete: '标记完成', moreActions: '更多操作',
    subtasksDone: '子任务已完成', minutes: '分钟', edit: '编辑', archive: '归档', priorityScore: '优先排位分', expired: '过期',
    close: '关闭', editTodo: '编辑待办', title: '标题', titlePlaceholder: '输入待办标题...', description: '描述', descriptionPlaceholder: '添加详细描述（可选）...', category: '分类',
    priorityAttributes: '优先属性', rank: '排位', rankTitle: '优先级排位，0 为最高', deadline: '截止日期', startTime: '开始时间', estimatedMinutes: '预估时间（分钟）',
    exampleMinutes: '例如：120', deadlineReminder: '截止提醒', recurrence: '重复', timeRecord: '时间记录（分钟）', actualTime: '实际花费的时间', tag: '标签', tagPlaceholder: '输入标签后按 Enter...', notes: '备注', markdown: '支持 Markdown',
    notesPlaceholder: '添加备注或笔记（支持 Markdown 语法）...', save: '保存', create: '创建', noRepeat: '不重复', daily: '每日', weekly: '每周', monthly: '每月', sameDay: '当天', daysBefore: '{count} 天前', weekBefore: '1 周前',
    settingsTitle: '设置', scoreFrequency: '分数更新频率', manual: '手动', scoreFrequencyDescription: '优先排位分实时计算的刷新间隔。设为“手动”需手动刷新。', categoryExpandCount: '分类展开数量', categoryExpandDescription: '侧栏中按分数排序后，前 X 名分类展开显示，其余折叠收纳。', manualActions: '手动操作', refreshScores: '立即刷新分数',
    iconTab: '图标', asciiTab: 'ASCII', colorsTab: '颜色', searchIcons: '搜索图标...', customColor: '自定义颜色',
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
    emptyTitle: 'No to-dos yet', emptyDescription: 'All clear! Click below or press N to create your first to-do', organizeTip: 'Organize to-dos with categories and tags', deadlineTip: 'Set deadlines to track progress',
    overdueDays: '{count} days overdue', dueToday: 'Due today', dueTomorrow: 'Due tomorrow', dueInDays: 'Due in {count} days', cancelComplete: 'Mark incomplete', markComplete: 'Mark complete', moreActions: 'More actions',
    subtasksDone: 'subtasks complete', minutes: 'min', edit: 'Edit', archive: 'Archive', priorityScore: 'Priority score', expired: 'Expired',
    close: 'Close', editTodo: 'Edit to-do', title: 'Title', titlePlaceholder: 'Enter a to-do title...', description: 'Description', descriptionPlaceholder: 'Add a description (optional)...', category: 'Category',
    priorityAttributes: 'Priority attributes', rank: 'Rank', rankTitle: 'Priority rank; 0 is highest', deadline: 'Deadline', startTime: 'Start time', estimatedMinutes: 'Estimated time (minutes)',
    exampleMinutes: 'e.g. 120', deadlineReminder: 'Deadline reminder', recurrence: 'Repeat', timeRecord: 'Time recorded (minutes)', actualTime: 'Actual time spent', tag: 'Tags', tagPlaceholder: 'Enter a tag and press Enter...', notes: 'Notes', markdown: 'Markdown supported',
    notesPlaceholder: 'Add notes (Markdown supported)...', save: 'Save', create: 'Create', noRepeat: 'No repeat', daily: 'Daily', weekly: 'Weekly', monthly: 'Monthly', sameDay: 'Same day', daysBefore: '{count} days before', weekBefore: '1 week before',
    settingsTitle: 'Settings', scoreFrequency: 'Score update frequency', manual: 'Manual', scoreFrequencyDescription: 'How often priority scores refresh. Manual requires an explicit refresh.', categoryExpandCount: 'Expanded categories', categoryExpandDescription: 'Show the top X scored categories in the sidebar and collapse the rest.', manualActions: 'Manual actions', refreshScores: 'Refresh scores now',
    iconTab: 'Icons', asciiTab: 'ASCII', colorsTab: 'Colors', searchIcons: 'Search icons...', customColor: 'Custom color',
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
