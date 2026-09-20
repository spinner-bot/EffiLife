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
    const dateStr = isNaN(date.getTime()) ? new Date().toLocaleString('zh-CN') : date.toLocaleString('zh-CN')
    return `开发版 #${commitCount} · ${dateStr}`
  }
  const displayTimestamp = BUILD_TIMESTAMP.startsWith('__') ? new Date().toISOString().split('T')[0] : BUILD_TIMESTAMP
  return `正式版 · ${displayTimestamp}`
}

// 版本历史（手动维护）
export const VERSION_HISTORY = [
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
