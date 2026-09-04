// 轻音乐生成器 - 使用 Web Audio API 合成柔和的轻音乐
export class MusicGenerator {
  private ctx: AudioContext
  private masterGain: GainNode
  private isPlaying = false
  private intervalId: number | null = null
  private scheduledNotes: Array<{
    oscillator: OscillatorNode
    gain: GainNode
    endTime: number
  }> = []

  constructor(ctx: AudioContext) {
    this.ctx = ctx
    this.masterGain = ctx.createGain()
    this.masterGain.gain.value = 0.15
    this.masterGain.connect(ctx.destination)
  }

  // 音符频率映射
  private noteFreq(note: string): number {
    const notes: Record<string, number> = {
      'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
      'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
      'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46,
      'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
      'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61,
      'G3': 196.00, 'A3': 220.00, 'B3': 246.94
    }
    return notes[note] || 440
  }

  // 播放单个音符（带包络）
  private playNote(note: string, startTime: number, duration: number, volume: number = 1) {
    const osc = this.ctx.createOscillator()
    const gain = this.ctx.createGain()

    // 使用正弦波模拟柔和音色
    osc.type = 'sine'
    osc.frequency.value = this.noteFreq(note)

    // 添加轻微的二倍泛音，让音色更丰富
    const osc2 = this.ctx.createOscillator()
    osc2.type = 'sine'
    osc2.frequency.value = this.noteFreq(note) * 2
    const gain2 = this.ctx.createGain()
    gain2.gain.value = 0.1
    osc2.connect(gain2)
    gain2.connect(gain)

    // ADSR 包络
    const attackTime = 0.05
    const decayTime = 0.1
    const sustainLevel = 0.6
    const releaseTime = Math.min(0.3, duration * 0.3)

    gain.gain.setValueAtTime(0, startTime)
    gain.gain.linearRampToValueAtTime(volume, startTime + attackTime)
    gain.gain.linearRampToValueAtTime(volume * sustainLevel, startTime + attackTime + decayTime)
    gain.gain.setValueAtTime(volume * sustainLevel, startTime + duration - releaseTime)
    gain.gain.linearRampToValueAtTime(0, startTime + duration)

    osc.connect(gain)
    gain.connect(this.masterGain)

    osc.start(startTime)
    osc.stop(startTime + duration)
    osc2.start(startTime)
    osc2.stop(startTime + duration)

    this.scheduledNotes.push({
      oscillator: osc,
      gain: gain,
      endTime: startTime + duration
    })
  }

  // 播放和弦
  private playChord(notes: string[], startTime: number, duration: number, volume: number = 0.5) {
    notes.forEach(note => {
      this.playNote(note, startTime, duration, volume / notes.length)
    })
  }

  // 风格1：轻柔钢琴
  private playSoftPiano() {
    const now = this.ctx.currentTime
    const bpm = 70
    const beatDuration = 60 / bpm

    // 简单而优美的旋律
    const melody = [
      { note: 'E4', time: 0, duration: 1.5 },
      { note: 'G4', time: 1.5, duration: 1 },
      { note: 'A4', time: 2.5, duration: 1.5 },
      { note: 'G4', time: 4, duration: 1 },
      { note: 'E4', time: 5, duration: 2 },
      { note: 'D4', time: 7, duration: 1.5 },
      { note: 'C4', time: 8.5, duration: 2.5 },
      { note: 'E4', time: 11, duration: 1.5 },
      { note: 'G4', time: 12.5, duration: 1 },
      { note: 'A4', time: 13.5, duration: 1.5 },
      { note: 'B4', time: 15, duration: 2 },
      { note: 'A4', time: 17, duration: 1.5 },
      { note: 'G4', time: 18.5, duration: 2.5 }
    ]

    // 伴奏和弦
    const chords = [
      { notes: ['C3', 'E3', 'G3'], time: 0, duration: 4 },
      { notes: ['A3', 'C4', 'E4'], time: 4, duration: 4 },
      { notes: ['F3', 'A3', 'C4'], time: 8, duration: 4 },
      { notes: ['G3', 'B3', 'D4'], time: 12, duration: 4 },
      { notes: ['C3', 'E3', 'G3'], time: 16, duration: 5 }
    ]

    // 播放旋律
    melody.forEach(({ note, time, duration }) => {
      this.playNote(note, now + time * beatDuration, duration * beatDuration, 0.8)
    })

    // 播放和弦伴奏
    chords.forEach(({ notes, time, duration }) => {
      this.playChord(notes, now + time * beatDuration, duration * beatDuration, 0.3)
    })

    return 21 * beatDuration // 总时长
  }

  // 风格2：梦幻氛围
  private playDreamyAmbient() {
    const now = this.ctx.currentTime
    const bpm = 60
    const beatDuration = 60 / bpm

    // 缓慢变化的和弦进程
    const progression = [
      { notes: ['C4', 'E4', 'G4', 'B4'], time: 0, duration: 8 },
      { notes: ['A3', 'C4', 'E4', 'G4'], time: 8, duration: 8 },
      { notes: ['F3', 'A3', 'C4', 'E4'], time: 16, duration: 8 },
      { notes: ['G3', 'B3', 'D4', 'F4'], time: 24, duration: 8 }
    ]

    // 高音点缀
    const sparkles = [
      { note: 'E5', time: 2 },
      { note: 'G5', time: 6 },
      { note: 'A5', time: 10 },
      { note: 'C5', time: 14 },
      { note: 'D5', time: 18 },
      { note: 'E5', time: 22 },
      { note: 'G5', time: 26 },
      { note: 'A5', time: 30 }
    ]

    // 播放和弦
    progression.forEach(({ notes, time, duration }) => {
      this.playChord(notes, now + time * beatDuration, duration * beatDuration, 0.25)
    })

    // 播放高音点缀
    sparkles.forEach(({ note, time }) => {
      this.playNote(note, now + time * beatDuration, 2 * beatDuration, 0.4)
    })

    return 32 * beatDuration
  }

  // 风格3：宁静夜晚
  private playPeacefulNight() {
    const now = this.ctx.currentTime
    const bpm = 65
    const beatDuration = 60 / bpm

    // 低音伴奏
    const bass = [
      { note: 'C3', time: 0, duration: 2 },
      { note: 'G3', time: 2, duration: 2 },
      { note: 'A3', time: 4, duration: 2 },
      { note: 'E3', time: 6, duration: 2 },
      { note: 'F3', time: 8, duration: 2 },
      { note: 'C3', time: 10, duration: 2 },
      { note: 'G3', time: 12, duration: 2 },
      { note: 'C3', time: 14, duration: 2 }
    ]

    // 旋律
    const melody = [
      { note: 'E4', time: 0, duration: 1.5 },
      { note: 'G4', time: 1.5, duration: 1 },
      { note: 'C5', time: 2.5, duration: 2 },
      { note: 'B4', time: 4.5, duration: 1.5 },
      { note: 'A4', time: 6, duration: 2 },
      { note: 'G4', time: 8, duration: 1.5 },
      { note: 'E4', time: 9.5, duration: 1 },
      { note: 'F4', time: 10.5, duration: 2 },
      { note: 'E4', time: 12.5, duration: 1.5 },
      { note: 'D4', time: 14, duration: 2 }
    ]

    // 播放低音
    bass.forEach(({ note, time, duration }) => {
      this.playNote(note, now + time * beatDuration, duration * beatDuration, 0.4)
    })

    // 播放旋律
    melody.forEach(({ note, time, duration }) => {
      this.playNote(note, now + time * beatDuration, duration * beatDuration, 0.7)
    })

    return 16 * beatDuration
  }

  // 开始播放指定风格
  start(style: 'piano' | 'ambient' | 'night' = 'piano') {
    if (this.isPlaying) return

    this.isPlaying = true
    const playLoop = () => {
      if (!this.isPlaying) return

      let duration: number
      switch (style) {
        case 'ambient':
          duration = this.playDreamyAmbient()
          break
        case 'night':
          duration = this.playPeacefulNight()
          break
        case 'piano':
        default:
          duration = this.playSoftPiano()
          break
      }

      // 循环播放
      this.intervalId = window.setTimeout(playLoop, duration * 1000)
    }

    playLoop()
  }

  // 停止播放
  stop() {
    this.isPlaying = false
    if (this.intervalId !== null) {
      clearTimeout(this.intervalId)
      this.intervalId = null
    }

    // 停止所有正在播放的音符
    this.scheduledNotes.forEach(({ oscillator, gain }) => {
      try {
        gain.gain.cancelScheduledValues(this.ctx.currentTime)
        gain.gain.setValueAtTime(0, this.ctx.currentTime)
        oscillator.stop(this.ctx.currentTime + 0.1)
      } catch (e) {
        // 忽略已停止的音符
      }
    })
    this.scheduledNotes = []
  }

  // 设置音量
  setVolume(volume: number) {
    this.masterGain.gain.value = volume * 0.15
  }
}
