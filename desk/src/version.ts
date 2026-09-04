// 版本管理
export const APP_VERSION = '1.0.0'
export const APP_NAME = '浪兮效率时钟'
export const BUILD_DATE = new Date().toISOString().split('T')[0]

// 版本历史
export const VERSION_HISTORY = [
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

// 获取完整版本信息
export function getVersionInfo(): string {
  return `${APP_NAME} v${APP_VERSION}`
}

// 获取简短版本信息
export function getShortVersion(): string {
  return `v${APP_VERSION}`
}
