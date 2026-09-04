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
  private noiseNodes: Array<{
    source: AudioBufferSourceNode
    gain: GainNode
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

  // 生成白噪声缓冲区
  private createNoiseBuffer(duration: number, type: 'white' | 'pink' | 'brown' = 'white'): AudioBuffer {
    const sampleRate = this.ctx.sampleRate
    const length = sampleRate * duration
    const buffer = this.ctx.createBuffer(1, length, sampleRate)
    const data = buffer.getChannelData(0)

    if (type === 'white') {
      // 白噪声：完全随机
      for (let i = 0; i < length; i++) {
        data[i] = Math.random() * 2 - 1
      }
    } else if (type === 'pink') {
      // 粉噪声：低频增强
      let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0
      for (let i = 0; i < length; i++) {
        const white = Math.random() * 2 - 1
        b0 = 0.99886 * b0 + white * 0.0555179
        b1 = 0.99332 * b1 + white * 0.0750759
        b2 = 0.96900 * b2 + white * 0.1538520
        b3 = 0.86650 * b3 + white * 0.3104856
        b4 = 0.55000 * b4 + white * 0.5329522
        b5 = -0.7616 * b5 - white * 0.0168980
        data[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362) * 0.11
        b6 = white * 0.115926
      }
    } else if (type === 'brown') {
      // 棕噪声：低频更强
      let lastOut = 0
      for (let i = 0; i < length; i++) {
        const white = Math.random() * 2 - 1
        data[i] = (lastOut + 0.02 * white) / 1.02
        lastOut = data[i]
        data[i] *= 3.5
      }
    }

    return buffer
  }

  // 播放噪声
  private playNoise(type: 'white' | 'pink' | 'brown', volume: number, filterFreq?: number): AudioBufferSourceNode {
    const buffer = this.createNoiseBuffer(10, type) // 10秒循环
    const source = this.ctx.createBufferSource()
    source.buffer = buffer
    source.loop = true

    const gain = this.ctx.createGain()
    gain.gain.value = volume

    // 添加滤波器让声音更柔和
    if (filterFreq) {
      const filter = this.ctx.createBiquadFilter()
      filter.type = 'lowpass'
      filter.frequency.value = filterFreq
      source.connect(filter)
      filter.connect(gain)
    } else {
      source.connect(gain)
    }

    gain.connect(this.masterGain)
    source.start()

    this.noiseNodes.push({ source, gain })
    return source
  }

  // 风格：雨声
  private playRain(): number {
    // 粉色噪声作为基础雨声
    this.playNoise('pink', 0.4, 800)
    // 加一点白噪声作为细雨
    this.playNoise('white', 0.15, 2000)
    // 加一点棕噪声作为远处雷声
    this.playNoise('brown', 0.2, 200)
    return 60 // 持续60秒
  }

  // 风格：海浪
  private playOcean(): number {
    // 棕噪声作为海浪基础
    const brownGain = this.ctx.createGain()
    brownGain.gain.value = 0
    brownGain.connect(this.masterGain)

    const buffer = this.createNoiseBuffer(10, 'brown')
    const source = this.ctx.createBufferSource()
    source.buffer = buffer
    source.loop = true

    const filter = this.ctx.createBiquadFilter()
    filter.type = 'lowpass'
    filter.frequency.value = 400
    source.connect(filter)
    filter.connect(brownGain)
    source.start()

    // 海浪起伏效果
    const now = this.ctx.currentTime
    for (let i = 0; i < 12; i++) {
      const t = now + i * 5
      brownGain.gain.setValueAtTime(0.1, t)
      brownGain.gain.linearRampToValueAtTime(0.4, t + 2)
      brownGain.gain.linearRampToValueAtTime(0.1, t + 4)
    }

    this.noiseNodes.push({ source, gain: brownGain })

    // 加一点白噪声作为浪花
    this.playNoise('white', 0.08, 3000)

    return 60
  }

  // 风格：森林
  private playForest(): number {
    // 轻柔的棕噪声作为风声
    this.playNoise('brown', 0.15, 300)

    // 添加鸟鸣效果（使用振荡器模拟）
    const now = this.ctx.currentTime
    for (let i = 0; i < 20; i++) {
      const time = now + Math.random() * 55
      const freq = 2000 + Math.random() * 2000
      const duration = 0.1 + Math.random() * 0.3

      const osc = this.ctx.createOscillator()
      osc.type = 'sine'
      osc.frequency.setValueAtTime(freq, time)
      osc.frequency.linearRampToValueAtTime(freq * 1.2, time + duration * 0.5)
      osc.frequency.linearRampToValueAtTime(freq * 0.8, time + duration)

      const gain = this.ctx.createGain()
      gain.gain.setValueAtTime(0, time)
      gain.gain.linearRampToValueAtTime(0.05, time + 0.02)
      gain.gain.linearRampToValueAtTime(0, time + duration)

      osc.connect(gain)
      gain.connect(this.masterGain)
      osc.start(time)
      osc.stop(time + duration)

      this.scheduledNotes.push({ oscillator: osc, gain, endTime: time + duration })
    }

    return 60
  }

  // 风格：咖啡厅
  private playCafe(): number {
    // 粉噪声作为背景人声
    this.playNoise('pink', 0.25, 1000)
    // 加一点白噪声作为杯碟声
    this.playNoise('white', 0.05, 4000)

    // 添加轻柔的爵士和弦
    const now = this.ctx.currentTime
    const bpm = 80
    const beat = 60 / bpm

    const chords = [
      ['C4', 'E4', 'G4', 'B4'],
      ['A3', 'C4', 'E4', 'G4'],
      ['F3', 'A3', 'C4', 'E4'],
      ['G3', 'B3', 'D4', 'F4']
    ]

    for (let i = 0; i < 16; i++) {
      const chord = chords[i % chords.length]
      const time = now + i * beat * 4
      this.playChord(chord, time, beat * 3.5, 0.15)
    }

    return 64 * beat
  }

  // 风格：篝火
  private playCampfire(): number {
    // 棕噪声作为火焰噼啪声
    const buffer = this.createNoiseBuffer(10, 'brown')
    const source = this.ctx.createBufferSource()
    source.buffer = buffer
    source.loop = true

    const filter = this.ctx.createBiquadFilter()
    filter.type = 'bandpass'
    filter.frequency.value = 600
    filter.Q.value = 2

    const gain = this.ctx.createGain()
    gain.gain.value = 0.3

    source.connect(filter)
    filter.connect(gain)
    gain.connect(this.masterGain)
    source.start()

    this.noiseNodes.push({ source, gain })

    // 添加噼啪声
    const now = this.ctx.currentTime
    for (let i = 0; i < 30; i++) {
      const time = now + Math.random() * 55
      const duration = 0.05 + Math.random() * 0.1

      const osc = this.ctx.createOscillator()
      osc.type = 'square'
      osc.frequency.value = 100 + Math.random() * 200

      const crackGain = this.ctx.createGain()
      crackGain.gain.setValueAtTime(0, time)
      crackGain.gain.linearRampToValueAtTime(0.1, time + 0.01)
      crackGain.gain.linearRampToValueAtTime(0, time + duration)

      osc.connect(crackGain)
      crackGain.connect(this.masterGain)
      osc.start(time)
      osc.stop(time + duration)

      this.scheduledNotes.push({ oscillator: osc, gain: crackGain, endTime: time + duration })
    }

    return 60
  }

  // 风格：爵士
  private playJazz(): number {
    const now = this.ctx.currentTime
    const bpm = 120
    const beat = 60 / bpm

    // walking bass
    const bassNotes = ['C3', 'E3', 'G3', 'A3', 'C3', 'F3', 'A3', 'G3']
    for (let i = 0; i < 32; i++) {
      const note = bassNotes[i % bassNotes.length]
      const time = now + i * beat
      this.playNote(note, time, beat * 0.8, 0.4)
    }

    // 爵士和弦
    const chords = [
      ['C4', 'E4', 'G4', 'B4'],
      ['A3', 'C4', 'E4', 'G4'],
      ['F3', 'A3', 'C4', 'E4'],
      ['G3', 'B3', 'D4', 'F4']
    ]

    for (let i = 0; i < 8; i++) {
      const chord = chords[i % chords.length]
      const time = now + i * beat * 4
      this.playChord(chord, time, beat * 3.5, 0.2)
    }

    return 32 * beat
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
  start(style: string = 'ambient') {
    if (this.isPlaying) return

    this.isPlaying = true
    const playLoop = () => {
      if (!this.isPlaying) return

      let duration: number
      switch (style) {
        case 'piano':
          duration = this.playSoftPiano()
          break
        case 'night':
          duration = this.playPeacefulNight()
          break
        case 'rain':
          duration = this.playRain()
          break
        case 'ocean':
          duration = this.playOcean()
          break
        case 'forest':
          duration = this.playForest()
          break
        case 'cafe':
          duration = this.playCafe()
          break
        case 'campfire':
          duration = this.playCampfire()
          break
        case 'jazz':
          duration = this.playJazz()
          break
        case 'ambient':
        default:
          duration = this.playDreamyAmbient()
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

    // 停止所有噪声
    this.noiseNodes.forEach(({ source, gain }) => {
      try {
        gain.gain.cancelScheduledValues(this.ctx.currentTime)
        gain.gain.linearRampToValueAtTime(0, this.ctx.currentTime + 0.5)
        source.stop(this.ctx.currentTime + 0.5)
      } catch (e) {
        // 忽略已停止的噪声
      }
    })
    this.noiseNodes = []
  }

  // 设置音量
  setVolume(volume: number) {
    this.masterGain.gain.value = volume * 0.15
  }
}
