// 版本管理 - 构建时自动生成
// 此文件由 vite 插件在每次构建时更新

// 以下值会在构建时被替换
export const APP_VERSION = '__APP_VERSION__'
export const BUILD_TIMESTAMP = '__BUILD_TIMESTAMP__'
export const BUILD_MODE = '__BUILD_MODE__'
export const GIT_COMMIT_HASH = '__GIT_COMMIT_HASH__'
export const GIT_COMMIT_COUNT = '__GIT_COMMIT_COUNT__'

export const APP_NAME = '浪兮效率时钟'

// 是否是开发版本
export const isDevVersion = BUILD_MODE === 'development' || APP_VERSION.includes('-dev')

// 获取完整版本信息
export function getVersionInfo(): string {
  if (isDevVersion) {
    return `${APP_NAME} v${APP_VERSION} (${GIT_COMMIT_HASH})`
  }
  return `${APP_NAME} v${APP_VERSION}`
}

// 获取简短版本信息
export function getShortVersion(): string {
  return `v${APP_VERSION}`
}

// 获取构建信息（用于调试）
export function getBuildInfo(): string {
  if (isDevVersion) {
    const date = new Date(parseInt(BUILD_TIMESTAMP) || Date.now())
    const dateStr = date.toLocaleString('zh-CN')
    return `开发版 #${GIT_COMMIT_COUNT} · ${dateStr}`
  }
  return `正式版 · ${BUILD_TIMESTAMP}`
}

// 版本历史（手动维护）
export const VERSION_HISTORY = [
  {
    version: '1.0.2',
    date: '开发中',
    changes: [
      '新增"更新记录"页面，可在设置中查看版本历史'
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
      '核心功能：时间记录、日历视图、计划管理',
      '12种主题风格（含水墨、赛博朋克、樱花等）',
      '9种背景音乐 + 自定义音乐',
      '动效设置（帧率30/60/90/120 FPS）',
      '事件预警系统',
      '打卡连续天数统计',
      '使用引导系统'
    ]
  }
]
