// 音频管理器 - 统一管理音效和背景音乐
import { ref, computed } from 'vue'
import { MusicGenerator } from './MusicGenerator'

export type SoundType =
  | 'click'           // 普通点击
  | 'hover'           // 悬停
  | 'toggle'          // 开关切换
  | 'success'         // 成功
  | 'error'           // 错误
  | 'notification'    // 通知
  | 'achievement'     // 成就达成
  | 'warning'         // 警告

export interface AudioSettings {
  // 主开关
  enabled: boolean

  // 音效设置
  sfxEnabled: boolean
  sfxVolume: number  // 0-100

  // 背景音乐设置
  bgmEnabled: boolean
  bgmVolume: number  // 0-100
  currentBgm: string  // 背景音乐ID或自定义文件路径

  // 各音效单独音量控制
  sfxVolumes: Record<SoundType, number>

  // 自定义背景音乐列表
  customBgmList: Array<{
    id: string
    name: string
    path: string  // base64 或文件路径
  }>
}

export const DEFAULT_AUDIO_SETTINGS: AudioSettings = {
  enabled: true,
  sfxEnabled: true,
  sfxVolume: 70,
  bgmEnabled: true,
  bgmVolume: 30,
  currentBgm: 'ambient',
  sfxVolumes: {
    click: 80,
    hover: 30,
    toggle: 60,
    success: 100,
    error: 80,
    notification: 90,
    achievement: 100,
    warning: 85
  },
  customBgmList: []
}

// 可用的背景音乐列表
export const BGM_LIST = [
  { id: 'ambient', name: '梦幻氛围', builtIn: true },
  { id: 'piano', name: '轻柔钢琴', builtIn: true },
  { id: 'night', name: '宁静夜晚', builtIn: true },
  { id: 'rain', name: '雨声', builtIn: true },
  { id: 'ocean', name: '海浪', builtIn: true },
  { id: 'forest', name: '森林', builtIn: true },
  { id: 'cafe', name: '咖啡厅', builtIn: true },
  { id: 'campfire', name: '篝火', builtIn: true },
  { id: 'jazz', name: '爵士', builtIn: true },
  { id: 'none', name: '无背景音乐', builtIn: true }
]

class AudioManagerClass {
  private audioContext: AudioContext | null = null
  private settings = ref<AudioSettings>({ ...DEFAULT_AUDIO_SETTINGS })
  private bgmAudio: HTMLAudioElement | null = null
  private musicGenerator: MusicGenerator | null = null
  private currentBgmId = ref('')

  constructor() {
    this.loadSettings()
  }

  private getAudioContext(): AudioContext {
    if (!this.audioContext) {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    }
    return this.audioContext
  }

  // 加载设置
  private loadSettings() {
    try {
      const saved = localStorage.getItem('efflife_audio_settings')
      if (saved) {
        const parsed = JSON.parse(saved)
        this.settings.value = { ...DEFAULT_AUDIO_SETTINGS, ...parsed }
      }
    } catch (e) {
      console.warn('Failed to load audio settings:', e)
    }
  }

  // 保存设置
  saveSettings() {
    try {
      localStorage.setItem('efflife_audio_settings', JSON.stringify(this.settings.value))
    } catch (e) {
      console.warn('Failed to save audio settings:', e)
    }
  }

  // 获取设置
  getSettings() {
    return this.settings.value
  }

  // 更新设置
  updateSettings(newSettings: Partial<AudioSettings>) {
    this.settings.value = { ...this.settings.value, ...newSettings }
    this.saveSettings()

    // 如果背景音乐设置改变，重新播放
    if (newSettings.currentBgm !== undefined || newSettings.bgmEnabled !== undefined) {
      this.updateBgm()
    }
  }

  // 生成合成音效
  private playSynthesizedSound(type: SoundType) {
    const ctx = this.getAudioContext()
    const oscillator = ctx.createOscillator()
    const gainNode = ctx.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(ctx.destination)

    // 根据类型设置不同的音效参数
    const volume = (this.settings.value.sfxVolumes[type] / 100) * (this.settings.value.sfxVolume / 100)

    switch (type) {
      case 'click':
        oscillator.frequency.value = 800
        oscillator.type = 'sine'
        gainNode.gain.setValueAtTime(volume * 0.3, ctx.currentTime)
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.1)
        oscillator.start(ctx.currentTime)
        oscillator.stop(ctx.currentTime + 0.1)
        break

      case 'hover':
        oscillator.frequency.value = 600
        oscillator.type = 'sine'
        gainNode.gain.setValueAtTime(volume * 0.1, ctx.currentTime)
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.05)
        oscillator.start(ctx.currentTime)
        oscillator.stop(ctx.currentTime + 0.05)
        break

      case 'toggle':
        oscillator.frequency.value = 500
        oscillator.type = 'square'
        gainNode.gain.setValueAtTime(volume * 0.2, ctx.currentTime)
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15)
        oscillator.start(ctx.currentTime)
        oscillator.stop(ctx.currentTime + 0.15)
        break

      case 'success':
        oscillator.frequency.setValueAtTime(523, ctx.currentTime) // C5
        oscillator.frequency.setValueAtTime(659, ctx.currentTime + 0.1) // E5
        oscillator.frequency.setValueAtTime(784, ctx.currentTime + 0.2) // G5
        oscillator.type = 'sine'
        gainNode.gain.setValueAtTime(volume * 0.3, ctx.currentTime)
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4)
        oscillator.start(ctx.currentTime)
        oscillator.stop(ctx.currentTime + 0.4)
        break

      case 'error':
        oscillator.frequency.value = 200
        oscillator.type = 'sawtooth'
        gainNode.gain.setValueAtTime(volume * 0.3, ctx.currentTime)
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3)
        oscillator.start(ctx.currentTime)
        oscillator.stop(ctx.currentTime + 0.3)
        break

      case 'notification':
        oscillator.frequency.setValueAtTime(880, ctx.currentTime) // A5
        oscillator.frequency.setValueAtTime(1047, ctx.currentTime + 0.15) // C6
        oscillator.type = 'sine'
        gainNode.gain.setValueAtTime(volume * 0.25, ctx.currentTime)
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3)
        oscillator.start(ctx.currentTime)
        oscillator.stop(ctx.currentTime + 0.3)
        break

      case 'achievement':
        // 成就音效 - 更长的旋律
        oscillator.frequency.setValueAtTime(523, ctx.currentTime) // C5
        oscillator.frequency.setValueAtTime(659, ctx.currentTime + 0.15) // E5
        oscillator.frequency.setValueAtTime(784, ctx.currentTime + 0.3) // G5
        oscillator.frequency.setValueAtTime(1047, ctx.currentTime + 0.45) // C6
        oscillator.type = 'sine'
        gainNode.gain.setValueAtTime(volume * 0.35, ctx.currentTime)
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.7)
        oscillator.start(ctx.currentTime)
        oscillator.stop(ctx.currentTime + 0.7)
        break

      case 'warning':
        // 警告音效 - 两声短促
        oscillator.frequency.value = 440
        oscillator.type = 'square'
        gainNode.gain.setValueAtTime(volume * 0.3, ctx.currentTime)
        gainNode.gain.setValueAtTime(0, ctx.currentTime + 0.1)
        gainNode.gain.setValueAtTime(volume * 0.3, ctx.currentTime + 0.2)
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3)
        oscillator.start(ctx.currentTime)
        oscillator.stop(ctx.currentTime + 0.4)
        break
    }
  }

  // 播放音效
  playSound(type: SoundType) {
    if (!this.settings.value.enabled || !this.settings.value.sfxEnabled) {
      return
    }

    try {
      this.playSynthesizedSound(type)
    } catch (e) {
      console.warn('Failed to play sound:', e)
    }
  }

  // 更新背景音乐
  private updateBgm() {
    // 停止当前背景音乐
    if (this.bgmAudio) {
      this.bgmAudio.pause()
      this.bgmAudio = null
    }

    // 停止音乐生成器
    if (this.musicGenerator) {
      this.musicGenerator.stop()
      this.musicGenerator = null
    }

    if (!this.settings.value.enabled || !this.settings.value.bgmEnabled) {
      return
    }

    const bgmId = this.settings.value.currentBgm

    if (bgmId === 'none') {
      return
    }

    // 检查是否是自定义背景音乐
    const customBgm = this.settings.value.customBgmList.find(b => b.id === bgmId)
    if (customBgm) {
      this.bgmAudio = new Audio(customBgm.path)
      this.bgmAudio.loop = true
      this.bgmAudio.volume = this.settings.value.bgmVolume / 100
      this.bgmAudio.play().catch(e => console.warn('Failed to play custom BGM:', e))
      this.currentBgmId.value = bgmId
      return
    }

    // 使用 MusicGenerator 播放内置轻音乐
    const ctx = this.getAudioContext()
    this.musicGenerator = new MusicGenerator(ctx)
    this.musicGenerator.setVolume(this.settings.value.bgmVolume / 100)

    // 根据 bgmId 选择风格
    this.musicGenerator.start(bgmId)
    this.currentBgmId.value = bgmId
  }

  // 开始播放背景音乐
  startBgm() {
    this.updateBgm()
  }

  // 停止背景音乐
  stopBgm() {
    if (this.bgmAudio) {
      this.bgmAudio.pause()
      this.bgmAudio = null
    }
    if (this.musicGenerator) {
      this.musicGenerator.stop()
      this.musicGenerator = null
    }
    this.currentBgmId.value = ''
  }

  // 添加自定义背景音乐
  addCustomBgm(name: string, path: string): string {
    const id = `custom_${Date.now()}`
    this.settings.value.customBgmList.push({ id, name, path })
    this.saveSettings()
    return id
  }

  // 删除自定义背景音乐
  removeCustomBgm(id: string) {
    this.settings.value.customBgmList = this.settings.value.customBgmList.filter(b => b.id !== id)
    if (this.settings.value.currentBgm === id) {
      this.settings.value.currentBgm = 'default'
      this.updateBgm()
    }
    this.saveSettings()
  }

  // 获取所有可用的背景音乐
  getAllBgm() {
    const builtIn = BGM_LIST.map(b => ({ ...b, custom: false }))
    const custom = this.settings.value.customBgmList.map(b => ({
      id: b.id,
      name: b.name,
      builtIn: false,
      custom: true
    }))
    return [...builtIn, ...custom]
  }
}

// 导出单例
export const AudioManager = new AudioManagerClass()
