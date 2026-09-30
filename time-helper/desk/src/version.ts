// 版本管理 - 构建时自动生成
// 此文件由 vite 插件在每次构建时更新
import { currentLocale, translate } from './i18n'

// 以下值会在构建时被替换
export const APP_VERSION = '__APP_VERSION__'
export const BUILD_TIMESTAMP = '__BUILD_TIMESTAMP__'
export const BUILD_MODE = '__BUILD_MODE__'
export const GIT_COMMIT_HASH = '__GIT_COMMIT_HASH__'
export const GIT_COMMIT_COUNT = '__GIT_COMMIT_COUNT__'

export const APP_NAME = 'EffiLife'

// 是否是开发版本
export const isDevVersion = (BUILD_MODE as string) === 'development' || APP_VERSION.includes('-dev') || APP_VERSION.startsWith('__')

// 获取完整版本信息
export function getVersionInfo(): string {
  const version = APP_VERSION.startsWith('__') ? '0.0.0-dev' : APP_VERSION
  const hash = GIT_COMMIT_HASH.startsWith('__') ? 'unknown' : GIT_COMMIT_HASH
  if (isDevVersion) {
    return `${APP_NAME} v${version} (${hash})`
  }
  return `${APP_NAME} v${version}`
}

// 获取简短版本信息
export function getShortVersion(): string {
  const version = APP_VERSION.startsWith('__') ? '0.0.0-dev' : APP_VERSION
  return `v${version}`
}

// 获取构建信息（用于调试）
export function getBuildInfo(): string {
  const commitCount = GIT_COMMIT_COUNT.startsWith('__') ? '0' : GIT_COMMIT_COUNT
  const timestamp = BUILD_TIMESTAMP.startsWith('__') ? Date.now().toString() : BUILD_TIMESTAMP

  if (isDevVersion) {
    const date = new Date(parseInt(timestamp) || Date.now())
    const dateStr = isNaN(date.getTime()) ? new Date().toLocaleString(currentLocale.value) : date.toLocaleString(currentLocale.value)
    return `${translate('version.build.development')} #${commitCount} · ${dateStr}`
  }
  const releaseDate = new Date(parseInt(timestamp) || Date.now())
  const displayTimestamp = isNaN(releaseDate.getTime())
    ? new Date().toLocaleDateString(currentLocale.value)
    : releaseDate.toLocaleDateString(currentLocale.value)
  return `${translate('version.build.release')} · ${displayTimestamp}`
}

// 版本历史（手动维护）
export const VERSION_HISTORY = [
  {
    version: '1.5.0',
    date: '2026-09-20',
    changes: [
      '新增 4 个顶级质量主题：北欧极夜、日式庭院、维多利亚书房、海底神殿',
      '每个主题含 9-10 层 Canvas 效果叠加，精心设计的粒子系统和环境光效',
      '色彩心理学应用、物理模拟粒子、有机动画（非机械循环）'
    ]
  },
  {
    version: '1.4.0',
    date: '2026-09-20',
    changes: [
      '新增 5 个高品质主题：午夜图书馆、星际航行、雨夜城市、沙漠黄昏、竹林清晨',
      '每个主题含独特 Canvas 背景动画、粒子效果、精心设计的配色方案'
    ]
  },
  {
    version: '1.3.0',
    date: '2026-09-20',
    changes: [
      '主页导航重构：合并记录+管理为全新「计划」视图',
      '全新 PlanView 界面：Tab 切换、卡片式设计、毛玻璃弹窗',
      '引导系统适配新导航结构'
    ]
  },
  {
    version: '1.1.0',
    date: '2026-09-20',
    changes: [
      '主页图表化：SVG 环形进度条 + 分类可视化进度条',
      '收件箱下拉面板：主页右上角一键展开消息预览',
      '活跃度热力图：GitHub 风格 26 周可视化',
      '日期详情弹窗：点击日期查看环形完成度 + 分类统计',
      '月份切换动画：左右滑动过渡效果',
      '打卡热力图：26 周火焰主题反馈',
      '收件箱分类过滤：成就/事件/提醒三类标签',
      '专用打卡界面：连续/累计天数、等级系统、粒子动画',
      '事件系统扩展：+7 种事件类型和触发机制',
      '完整 API 层：7 大模块接口 + API 文档',
      '可复用 ContributionHeatmap 热力图组件'
    ]
  },
  {
    version: '1.0.15',
    date: '开发中',
    changes: [
      '安卓开发暂时搁置：APK 反复启动闪退，多轮修复无效，相关内容已归档至 archive/android/',
      '主项目回归桌面端开发'
    ]
  },
  {
    version: '1.0.11',
    date: '2026-09-05',
    changes: [
      '添加预警规则验证：小时0-23、分钟0-59、阈值0-100',
      '添加计划管理验证：每个时间类别时长不能为负或超过24小时'
    ]
  },
  {
    version: '1.0.10',
    date: '2026-09-05',
    changes: [
      '添加记录创建时的完整验证：时间范围、小时/分钟边界、时长限制等',
      '防止创建结束时间早于开始时间的无效记录'
    ]
  },
  {
    version: '1.0.9',
    date: '2026-09-05',
    changes: [
      '修复记录创建：修改时间后无法保存的问题',
      '原因是 input[type=number] 返回数字类型，调用字符串方法 padStart 报错'
    ]
  },
  {
    version: '1.0.8',
    date: '2026-09-05',
    changes: [
      '修复打卡逻辑：确保只有任务100%完成才能打卡',
      '连续天数断开时，完成的计划仍可在收件箱中手动打卡',
      '补打卡前验证该日期确实有完成的任务记录'
    ]
  },
  {
    version: '1.0.7',
    date: '2026-09-05',
    changes: [
      '新增自动补打卡：进入新一天时若昨天完成了计划但未打卡，自动补打',
      '新增收件箱打卡：遗漏的打卡可在事件管理收件箱中补打',
      '打卡提醒会以特殊样式显示在收件箱中，点击即可补打卡'
    ]
  },
  {
    version: '1.0.6',
    date: '2026-09-05',
    changes: [
      'Tauri 环境下存档导出使用原生对话框选择保存路径',
      'Tauri 环境下存档导入使用原生文件选择对话框',
      '浏览器环境自动回退到默认下载/文件选择'
    ]
  },
  {
    version: '1.0.5',
    date: '2026-09-05',
    changes: [
      '重构存档系统：使用 .efl 格式（ZIP 压缩），包含所有数据',
      '新增数据统计展示（记录天数、条数等）',
      '重构恢复功能：分类清除（全部/记录/计划/设置）',
      '修复存档功能在非 Tauri 环境下无法使用的问题'
    ]
  },
  {
    version: '1.0.4',
    date: '2026-09-05',
    changes: [
      '设置导航支持层级返回，不会直接跳回主页',
      '"更多设置"排版优化，与主设置保持一致',
      '"恢复"移入"更多设置"，"更多设置"移至主设置底部'
    ]
  },
  {
    version: '1.0.3',
    date: '2026-09-05',
    changes: [
      '设置页面优化：不常用选项收纳至"更多设置"',
      '新增"版本信息"页面，突出显示当前版本和历史记录'
    ]
  },
  {
    version: '1.0.1',
    date: '2026-09-05',
    changes: [
      '默认背景音乐改为爵士'
    ]
  },
  {
    version: '1.0.0',
    date: '2026-09-05',
    changes: [
      '首次正式发布',
      '核心功能：时间记录、历史统计、计划管理',
      '12种主题风格（含水墨、赛博朋克、樱花等）',
      '9种背景音乐 + 自定义音乐',
      '动效设置（帧率30/60/90/120 FPS）',
      '事件预警系统',
      '打卡连续天数统计',
      '使用引导系统'
    ]
  }
]

// Release notes are product metadata rather than runtime state. Keep the
// original Chinese history for compatibility and provide a parallel English
// catalog with the same release/bullet shape for the settings view.
const VERSION_HISTORY_EN: Record<string, string[]> = {
  '1.5.0': [
    'Added four flagship quality themes: Nordic Polar Night, Japanese Garden, Victorian Study, and Underwater Temple',
    'Each theme includes layered Canvas effects, a dedicated particle system, and ambient lighting',
    'Applied color psychology, physics-inspired particles, and organic animation rather than mechanical loops',
  ],
  '1.4.0': [
    'Added five high-quality themes: Midnight Library, Star Voyage, Rainy City, Desert Dusk, and Bamboo Dawn',
    'Each theme includes a unique Canvas background animation, particle effects, and a designed color palette',
  ],
  '1.3.0': [
    'Rebuilt primary navigation by combining records and management into the new Plans view',
    'Introduced the PlanView interface with tabs, card layouts, and glass-morphism dialogs',
    'Updated the onboarding system for the new navigation structure',
  ],
  '1.1.0': [
    'Added a visual dashboard with an SVG completion ring and category progress bars',
    'Added an inbox panel with one-click message previews from the home page',
    'Added a GitHub-style 26-week activity heatmap',
    'Added date details with completion rings and category statistics',
    'Added animated month transitions',
    'Added a 26-week check-in heatmap with a flame theme',
    'Added inbox filtering for achievements, events, and reminders',
    'Added a dedicated check-in page with streaks, levels, and particle animation',
    'Expanded the event system with seven event types and trigger mechanisms',
    'Added a complete API layer with seven module interfaces and API documentation',
    'Added the reusable ContributionHeatmap component',
  ],
  '1.0.15': [
    'Paused Android development after repeated APK startup crashes; related work was archived under archive/android/',
    'Returned the primary project focus to desktop development',
  ],
  '1.0.11': [
    'Added validation for warning rules: hours 0–23, minutes 0–59, and thresholds 0–100',
    'Added plan validation to prevent negative or over-24-hour category durations',
  ],
  '1.0.10': [
    'Added complete validation for record creation, including time ranges, boundaries, and duration limits',
    'Prevented invalid records whose end time precedes their start time',
  ],
  '1.0.9': [
    'Fixed records failing to save after editing their time',
    'Fixed a numeric input type issue that caused padStart to fail',
  ],
  '1.0.8': [
    'Fixed check-in logic so only 100% completed tasks can be checked in',
    'Preserved manual make-up check-in from the inbox after a streak breaks',
    'Validated that completed task records exist before make-up check-in',
  ],
  '1.0.7': [
    'Added automatic make-up check-in when yesterday was completed but not checked in',
    'Added inbox make-up check-in for missed check-ins',
    'Styled missed check-in reminders as actionable inbox entries',
  ],
  '1.0.6': [
    'Added a native save-path dialog for archive export in Tauri',
    'Added a native file picker for archive import in Tauri',
    'Added browser fallbacks for downloads and file selection',
  ],
  '1.0.5': [
    'Rebuilt the archive system around the compressed .efl format',
    'Added data statistics such as record days and record count',
    'Rebuilt recovery with separate reset scopes for all, records, plans, and settings',
    'Fixed archive operations in non-Tauri environments',
  ],
  '1.0.4': [
    'Added hierarchical back navigation to settings instead of always returning home',
    'Improved the More Settings layout to match the main settings page',
    'Moved recovery into More Settings and moved More Settings to the bottom of the main settings page',
  ],
  '1.0.3': [
    'Moved less-used options into More Settings',
    'Added a version information page with the current version and release history',
  ],
  '1.0.1': [
    'Changed the default background music to jazz',
  ],
  '1.0.0': [
    'First official release',
    'Core features: time records, history statistics, and plan management',
    'Twelve visual themes including ink, cyberpunk, and sakura',
    'Nine background music tracks plus custom music',
    'Motion settings with 30/60/90/120 FPS options',
    'Event warning system',
    'Check-in streak statistics',
    'Onboarding guide system',
  ],
}

export function getVersionChanges(
  release: (typeof VERSION_HISTORY)[number],
  locale: string,
): string[] {
  return locale.toLowerCase().startsWith('en')
    ? VERSION_HISTORY_EN[release.version] || release.changes
    : release.changes
}
