// 引导系统管理器
import { ref, reactive } from 'vue'

export interface GuideStep {
  id: string
  title: string
  description: string
  target?: string  // CSS 选择器，指向要高亮的元素
  action?: 'click' | 'navigate' | 'wait'  // 期望的用户行为
  actionTarget?: string  // 要点击的元素选择器
  navigateTo?: string  // 导航目标路由
  highlight?: boolean  // 是否高亮目标元素
  position?: 'top' | 'bottom' | 'left' | 'right'  // 提示框位置
}

export interface GuideConfig {
  id: string
  name: string
  steps: GuideStep[]
}

const STORAGE_KEY = 'efflife_guide_completed'

// 全局响应式状态
export const guideState = reactive({
  isActive: false,
  currentStepIndex: 0,
  currentGuide: null as GuideConfig | null,
  completed: false,
  version: 0
})

// 主引导流程
export const MAIN_GUIDE: GuideConfig = {
  id: 'main',
  name: '主要功能引导',
  steps: [
    {
      id: 'welcome',
      title: '欢迎使用浪兮效率时钟！',
      description: '这是一款帮助你管理时间、追踪效率的工具。让我们花一分钟了解核心功能吧！',
      position: 'bottom'
    },
    {
      id: 'home-overview',
      title: '主页概览',
      description: '这里是你的效率中心。显示当前时间、今日计划完成度和连续打卡天数。',
      target: '.clock-section',
      highlight: true,
      position: 'bottom'
    },
    {
      id: 'nav-records',
      title: '记录时间',
      description: '点击这里开始记录你的时间。试试添加一条记录吧！',
      target: '.nav-btn:nth-child(1)',
      action: 'click',
      navigateTo: '/records',
      highlight: true,
      position: 'bottom'
    },
    {
      id: 'add-record',
      title: '添加记录',
      description: '点击"新增"按钮，填写内容、选择类别、设置时间，然后保存。',
      target: '.add-btn',
      action: 'click',
      highlight: true,
      position: 'bottom'
    },
    {
      id: 'record-form',
      title: '填写记录',
      description: '在这里填写你的活动内容和时间。完成后点击保存，然后返回主页继续引导。',
      target: '.modal, .form-section',
      highlight: true,
      position: 'bottom'
    },
    {
      id: 'nav-calendar',
      title: '查看日历',
      description: '点击这里查看日历视图，了解你的历史记录和完成度。',
      target: '.nav-btn:nth-child(2)',
      action: 'click',
      navigateTo: '/calendar',
      highlight: true,
      position: 'bottom'
    },
    {
      id: 'calendar-view',
      title: '日历视图',
      description: '这里展示你每天的完成度。点击任意日期查看详情。',
      target: '.calendar-grid',
      highlight: true,
      position: 'bottom'
    },
    {
      id: 'nav-management',
      title: '计划管理',
      description: '点击这里管理你的日计划和预警规则。',
      target: '.nav-btn:nth-child(3)',
      action: 'click',
      navigateTo: '/management',
      highlight: true,
      position: 'bottom'
    },
    {
      id: 'management-view',
      title: '管理中心',
      description: '在这里可以设置日程安排、管理日计划、配置临时变更。完成后返回主页。',
      target: '.action-grid',
      highlight: true,
      position: 'bottom'
    },
    {
      id: 'nav-settings',
      title: '个性化设置',
      description: '最后，点击这里探索主题、音效、动效等个性化设置。',
      target: '.nav-btn:nth-child(4)',
      action: 'click',
      navigateTo: '/settings',
      highlight: true,
      position: 'bottom'
    },
    {
      id: 'settings-view',
      title: '设置中心',
      description: '你可以在这里切换主题、调整音效、配置动效、查看帮助等。点击"帮助"了解更多。',
      target: '.settings-list',
      action: 'click',
      actionTarget: '.settings-item:nth-child(5)',  // 帮助按钮
      navigateTo: '/settings',
      highlight: true,
      position: 'bottom'
    },
    {
      id: 'guide-end',
      title: '引导完成！',
      description: '恭喜你完成了引导！现在你已了解核心功能。开始使用吧，祝你效率满满！',
      position: 'bottom'
    }
  ]
}

class GuideManagerClass {
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

  // 开始引导
  startGuide(guide: GuideConfig = MAIN_GUIDE) {
    guideState.currentGuide = guide
    guideState.currentStepIndex = 0
    guideState.isActive = true
    guideState.version++
  }

  // 进入下一步
  nextStep() {
    if (!guideState.currentGuide) return

    const steps = guideState.currentGuide.steps
    if (guideState.currentStepIndex < steps.length - 1) {
      guideState.currentStepIndex++
      guideState.version++
    } else {
      // 引导结束
      this.endGuide()
    }
  }

  // 跳到指定步骤
  goToStep(index: number) {
    if (!guideState.currentGuide) return
    if (index >= 0 && index < guideState.currentGuide.steps.length) {
      guideState.currentStepIndex = index
      guideState.version++
    }
  }

  // 结束引导
  endGuide() {
    guideState.isActive = false
    guideState.currentGuide = null
    guideState.currentStepIndex = 0
    this.saveCompleted()
    guideState.version++
  }

  // 跳过引导
  skipGuide() {
    this.endGuide()
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

  // 重置引导状态（用于重新体验）
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
