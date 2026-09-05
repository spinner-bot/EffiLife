// 引导系统管理器 - 重新设计
import { reactive } from 'vue'

export interface GuideStep {
  id: string
  title: string
  description: string
  target?: string  // CSS 选择器，指向要高亮的元素
  actionRequired?: boolean  // 是否需要用户操作才能继续
  actionType?: 'click' | 'navigate' | 'input' | 'wait'
  actionTarget?: string  // 需要点击的元素选择器
  validateAction?: () => boolean  // 验证操作是否完成的函数
  navigateTo?: string  // 导航目标路由
  highlight?: boolean  // 是否高亮目标元素
  position?: 'top' | 'bottom' | 'left' | 'right'
  isDemo?: boolean  // 是否是演示步骤（不需要操作）
  skippable?: boolean  // 是否允许跳过此步骤（复杂操作）
  autoAdvance?: boolean  // 完成后是否自动进入下一步（点击类任务）
}

export interface GuideConfig {
  id: string
  name: string
  steps: GuideStep[]
}

const STORAGE_KEY = 'efflife_guide_completed'
const BACKUP_KEY = 'efflife_guide_data_backup'

// 全局响应式状态
export const guideState = reactive({
  isActive: false,
  currentStepIndex: 0,
  currentGuide: null as GuideConfig | null,
  completed: false,
  canProceed: false,  // 是否可以进入下一步
  version: 0
})

// 数据备份
interface DataBackup {
  records: Record<string, any[]>
  plans: any
  scheduleRules: any[]
  config: any
  manualPlans: Record<string, string>
}

// 主引导流程 - 核心功能操作 + 非核心功能介绍
export const MAIN_GUIDE: GuideConfig = {
  id: 'main',
  name: '主要功能引导',
  steps: [
    // ========== 欢迎 ==========
    {
      id: 'welcome',
      title: '欢迎使用浪兮效率时钟！',
      description: '让我们通过实际操作来了解核心功能。你将亲手体验记录时间、查看日历等功能。准备好了吗？',
      position: 'bottom',
      isDemo: true
    },

    // ========== 核心功能：记录时间 ==========
    {
      id: 'go-records',
      title: '第一步：记录时间',
      description: '点击下方的"记录"按钮，开始体验时间记录功能。',
      target: '.nav-btn:nth-child(1)',
      highlight: true,
      actionRequired: true,
      actionType: 'click',
      actionTarget: '.nav-btn:nth-child(1)',
      navigateTo: '/records',
      autoAdvance: true,
      position: 'bottom'
    },
    {
      id: 'add-record',
      title: '添加一条记录',
      description: '点击"新增"按钮，添加一条时间记录。试试填写"测试活动"，时间设为1小时。',
      target: '.add-btn',
      highlight: true,
      actionRequired: true,
      actionType: 'click',
      actionTarget: '.add-btn',
      autoAdvance: true,
      position: 'bottom'
    },
    {
      id: 'fill-record',
      title: '填写记录内容',
      description: '填写内容（如"测试活动"），选择类别，设置时间为1小时，然后点击"保存"。',
      target: '.modal, .form-section',
      highlight: true,
      actionRequired: true,
      actionType: 'input',
      skippable: true,
      validateAction: () => {
        // 检查是否回到了记录列表（说明保存成功）
        return !document.querySelector('.modal')
      },
      position: 'bottom'
    },
    {
      id: 'record-saved',
      title: '记录已保存！',
      description: '很好！你刚刚添加了一条时间记录。现在点击"返回"回到主页，继续下一步。',
      target: '.back-btn',
      highlight: true,
      actionRequired: true,
      actionType: 'click',
      actionTarget: '.back-btn',
      navigateTo: '/',
      autoAdvance: true,
      position: 'bottom'
    },

    // ========== 核心功能：日历视图 ==========
    {
      id: 'go-calendar',
      title: '第二步：查看日历',
      description: '点击"日历"按钮，查看你的时间记录在日历中的展示。',
      target: '.nav-btn:nth-child(2)',
      highlight: true,
      actionRequired: true,
      actionType: 'click',
      actionTarget: '.nav-btn:nth-child(2)',
      navigateTo: '/calendar',
      autoAdvance: true,
      position: 'bottom'
    },
    {
      id: 'calendar-view',
      title: '日历视图',
      description: '这里展示你每天的记录。点击今天的日期，查看当天的详细记录。',
      target: '.day-cell.today',
      highlight: true,
      actionRequired: true,
      actionType: 'click',
      actionTarget: '.day-cell.today',
      autoAdvance: true,
      position: 'bottom'
    },
    {
      id: 'day-detail',
      title: '日期详情',
      description: '这里显示当天的计划和记录。你可以切换日计划、查看记录详情。点击"返回日历"继续。',
      target: '.back-btn',
      highlight: true,
      actionRequired: true,
      actionType: 'click',
      actionTarget: '.back-btn',
      navigateTo: '/calendar',
      autoAdvance: true,
      position: 'bottom'
    },
    {
      id: 'back-home',
      title: '返回主页',
      description: '点击"返回"回到主页，继续探索管理功能。',
      target: '.back-btn',
      highlight: true,
      actionRequired: true,
      actionType: 'click',
      actionTarget: '.back-btn',
      navigateTo: '/',
      autoAdvance: true,
      position: 'bottom'
    },

    // ========== 核心功能：计划管理 ==========
    {
      id: 'go-management',
      title: '第三步：计划管理',
      description: '点击"管理"按钮，了解如何设置日计划和预警规则。',
      target: '.nav-btn:nth-child(3)',
      highlight: true,
      actionRequired: true,
      actionType: 'click',
      actionTarget: '.nav-btn:nth-child(3)',
      navigateTo: '/management',
      autoAdvance: true,
      position: 'bottom'
    },
    {
      id: 'management-overview',
      title: '管理中心',
      description: '这里有三个功能：日程安排、日计划管理、临时计划变更。点击"日计划管理"查看详情。',
      target: '.action-btn:nth-child(2)',
      highlight: true,
      actionRequired: true,
      actionType: 'click',
      actionTarget: '.action-btn:nth-child(2)',
      autoAdvance: true,
      position: 'bottom'
    },
    {
      id: 'plan-list',
      title: '日计划列表',
      description: '这里管理你的所有日计划。你可以创建新计划、编辑现有计划。点击"返回"回到管理中心。',
      target: '.btn.secondary',
      highlight: true,
      actionRequired: true,
      actionType: 'click',
      actionTarget: '.btn.secondary',
      autoAdvance: true,
      position: 'bottom'
    },
    {
      id: 'back-home-2',
      title: '返回主页',
      description: '点击管理中心的"返回"按钮回到主页，继续探索设置功能。',
      target: '.back-btn',
      highlight: true,
      actionRequired: true,
      actionType: 'click',
      actionTarget: '.back-btn',
      navigateTo: '/',
      autoAdvance: true,
      position: 'bottom'
    },

    // ========== 非核心功能：设置介绍 ==========
    {
      id: 'go-settings',
      title: '探索设置',
      description: '点击"设置"按钮，了解个性化选项。这些功能不需要操作，只需了解即可。',
      target: '.nav-btn:nth-child(4)',
      highlight: true,
      actionRequired: true,
      actionType: 'click',
      actionTarget: '.nav-btn:nth-child(4)',
      navigateTo: '/settings',
      position: 'bottom'
    },
    {
      id: 'settings-theme',
      title: '主题切换',
      description: '在"主题"中，你可以选择12种不同风格的主题，包括水墨、赛博朋克、樱花等。每种主题都有独特的视觉效果。',
      target: '.settings-item:nth-child(2)',
      highlight: true,
      actionRequired: false,
      isDemo: true,
      position: 'bottom'
    },
    {
      id: 'settings-audio',
      title: '声音设置',
      description: '在"声音"中，你可以配置音效和背景音乐。支持9种环境音，也可以添加自定义音乐文件。',
      target: '.settings-item:nth-child(3)',
      highlight: true,
      actionRequired: false,
      isDemo: true,
      position: 'bottom'
    },
    {
      id: 'settings-motion',
      title: '动效设置',
      description: '在"动效"中，你可以调整帧率（30/60/90/120 FPS）、动画速度，还可以运行自动优化测试。',
      target: '.settings-item:nth-child(4)',
      highlight: true,
      actionRequired: false,
      isDemo: true,
      position: 'bottom'
    },
    {
      id: 'settings-events',
      title: '事件管理',
      description: '在"事件管理"中，你可以配置事件通知、设置预警规则（如12点完成20%、18点完成50%等）。',
      target: '.settings-item:nth-child(5)',
      highlight: true,
      actionRequired: false,
      isDemo: true,
      position: 'bottom'
    },
    {
      id: 'settings-help',
      title: '帮助与反馈',
      description: '在"帮助"中查看详细的使用指南和常见问题。如果遇到问题，可以通过"反馈"联系开发者。',
      target: '.settings-item:nth-child(7)',
      highlight: true,
      actionRequired: false,
      isDemo: true,
      position: 'bottom'
    },

    // ========== 完成 ==========
    {
      id: 'guide-complete',
      title: '🎉 引导完成！',
      description: '恭喜你完成了所有核心功能的体验！现在你已掌握：\n• 记录时间\n• 查看日历\n• 管理计划\n• 个性化设置\n\n开始你的效率之旅吧！',
      position: 'bottom',
      isDemo: true
    }
  ]
}

class GuideManagerClass {
  private backup: DataBackup | null = null
  private validationInterval: number | null = null

  constructor() {
    this.loadCompleted()
  }

  private loadCompleted() {
    try {
      const completed = localStorage.getItem(STORAGE_KEY)
      guideState.completed = completed === 'true'
      guideState.version++
    } catch (e) {
      console.warn('Failed to load guide state:', e)
    }
  }

  private saveCompleted() {
    try {
      localStorage.setItem(STORAGE_KEY, 'true')
      guideState.completed = true
      guideState.version++
    } catch (e) {
      console.warn('Failed to save guide state:', e)
    }
  }

  // 备份数据
  backupData() {
    try {
      this.backup = {
        records: {},
        plans: JSON.parse(localStorage.getItem('efflife_plans') || '{}'),
        scheduleRules: JSON.parse(localStorage.getItem('efflife_schedule_rules') || '[]'),
        config: JSON.parse(localStorage.getItem('efflife_config') || '{}'),
        manualPlans: JSON.parse(localStorage.getItem('efflife_manual_plans') || '{}')
      }

      // 备份所有记录
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith('efflife_records_')) {
          this.backup.records[key] = JSON.parse(localStorage.getItem(key) || '[]')
        }
      }

      localStorage.setItem(BACKUP_KEY, JSON.stringify(this.backup))
      console.log('Guide: Data backed up')
    } catch (e) {
      console.warn('Failed to backup data:', e)
    }
  }

  // 还原数据
  restoreData() {
    try {
      if (!this.backup) {
        const backupStr = localStorage.getItem(BACKUP_KEY)
        if (backupStr) {
          this.backup = JSON.parse(backupStr)
        }
      }

      if (this.backup) {
        // 还原记录
        for (const [key, records] of Object.entries(this.backup.records)) {
          localStorage.setItem(key, JSON.stringify(records))
        }

        // 还原其他数据
        localStorage.setItem('efflife_plans', JSON.stringify(this.backup.plans))
        localStorage.setItem('efflife_schedule_rules', JSON.stringify(this.backup.scheduleRules))
        localStorage.setItem('efflife_config', JSON.stringify(this.backup.config))
        localStorage.setItem('efflife_manual_plans', JSON.stringify(this.backup.manualPlans))

        // 清除备份
        localStorage.removeItem(BACKUP_KEY)
        this.backup = null
        console.log('Guide: Data restored')
      }
    } catch (e) {
      console.warn('Failed to restore data:', e)
    }
  }

  // 开始引导
  startGuide(guide: GuideConfig = MAIN_GUIDE) {
    // 备份数据
    this.backupData()

    guideState.currentGuide = guide
    guideState.currentStepIndex = 0
    guideState.isActive = true
    guideState.canProceed = !guide.steps[0].actionRequired
    guideState.version++
  }

  // 检查当前步骤是否可以继续
  checkCanProceed() {
    const step = this.getCurrentStep()
    if (!step) return

    if (!step.actionRequired) {
      guideState.canProceed = true
    } else if (step.validateAction) {
      guideState.canProceed = step.validateAction()
    } else {
      // 默认：如果是点击操作，检查是否已经点击过
      guideState.canProceed = false
    }
    guideState.version++
  }

  // 标记操作完成
  markActionComplete() {
    guideState.canProceed = true
    guideState.version++
  }

  // 进入下一步
  nextStep() {
    if (!guideState.currentGuide) return

    const steps = guideState.currentGuide.steps
    if (guideState.currentStepIndex < steps.length - 1) {
      guideState.currentStepIndex++
      const nextStep = steps[guideState.currentStepIndex]
      guideState.canProceed = !nextStep.actionRequired
      guideState.version++
    } else {
      // 引导结束
      this.endGuide()
    }
  }

  // 结束引导
  endGuide() {
    // 还原数据
    this.restoreData()

    guideState.isActive = false
    guideState.currentGuide = null
    guideState.currentStepIndex = 0
    guideState.canProceed = false
    this.saveCompleted()
    guideState.version++
  }

  // 跳过引导
  skipGuide() {
    this.restoreData()
    this.endGuide()
  }

  // 跳过当前步骤（仅用于允许跳过的步骤）
  skipStep() {
    const step = this.getCurrentStep()
    if (!step || !step.skippable) return

    // 停止验证
    if (this.validationInterval) {
      clearInterval(this.validationInterval)
      this.validationInterval = null
    }

    // 进入下一步
    this.nextStep()
  }

  // 获取当前步骤
  getCurrentStep(): GuideStep | null {
    if (!guideState.currentGuide) return null
    return guideState.currentGuide.steps[guideState.currentStepIndex] || null
  }

  // 获取进度
  getProgress(): { current: number; total: number } {
    if (!guideState.currentGuide) return { current: 0, total: 0 }
    return {
      current: guideState.currentStepIndex + 1,
      total: guideState.currentGuide.steps.length
    }
  }

  // 是否已完成引导
  isCompleted(): boolean {
    return guideState.completed
  }

  // 重置引导状态
  resetCompleted() {
    try {
      localStorage.removeItem(STORAGE_KEY)
      guideState.completed = false
      guideState.version++
    } catch (e) {
      console.warn('Failed to reset guide state:', e)
    }
  }
}

export const GuideManager = new GuideManagerClass()
