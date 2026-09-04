<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Volume2, Music, Bell, Plus, Trash2, Play, Upload } from 'lucide-vue-next'
import { AudioManager, EventSystem, BGM_LIST } from '@/audio'
import type { SoundType, AudioSettings, EventSettings, EventType } from '@/audio'

const router = useRouter()

// 音频设置
const audioSettings = ref<AudioSettings>(AudioManager.getSettings())
// 事件设置
const eventSettings = ref<EventSettings>(EventSystem.getSettings())

// 音效类型列表
const soundTypes: Array<{ type: SoundType; name: string; description: string }> = [
  { type: 'click', name: '点击音效', description: '按钮点击时播放' },
  { type: 'hover', name: '悬停音效', description: '鼠标悬停时播放' },
  { type: 'toggle', name: '开关音效', description: '切换开关时播放' },
  { type: 'success', name: '成功音效', description: '操作成功时播放' },
  { type: 'error', name: '错误音效', description: '操作失败时播放' },
  { type: 'notification', name: '通知音效', description: '收到通知时播放' },
  { type: 'achievement', name: '成就音效', description: '达成成就时播放' },
  { type: 'warning', name: '警告音效', description: '警告提示时播放' }
]

// 事件类型列表
const eventTypes: Array<{ type: EventType; name: string; description: string }> = [
  { type: 'plan_complete_100', name: '计划完美完成', description: '当天计划完成度达到100%' },
  { type: 'plan_complete_90', name: '计划即将完成', description: '当天计划完成度达到90%' },
  { type: 'plan_low_progress', name: '低完成度预警', description: '时间已晚但完成度较低' },
  { type: 'record_added', name: '记录添加', description: '添加时间记录时' },
  { type: 'plan_changed', name: '计划切换', description: '切换日计划时' },
  { type: 'achievement_unlocked', name: '成就解锁', description: '解锁新成就时' }
]

// 所有背景音乐
const allBgm = computed(() => AudioManager.getAllBgm())

// 测试音效
function testSound(type: SoundType) {
  AudioManager.playSound(type)
}

// 更新音频设置
function updateAudioSetting<K extends keyof AudioSettings>(key: K, value: AudioSettings[K]) {
  audioSettings.value[key] = value
  AudioManager.updateSettings({ [key]: value })
}

// 更新事件设置
function updateEventSetting<K extends keyof EventSettings>(key: K, value: EventSettings[K]) {
  eventSettings.value[key] = value
  EventSystem.updateSettings({ [key]: value })
}

// 更新单个音效音量
function updateSfxVolume(type: SoundType, volume: number) {
  audioSettings.value.sfxVolumes[type] = volume
  AudioManager.updateSettings({ sfxVolumes: audioSettings.value.sfxVolumes })
}

// 切换事件开关
function toggleEvent(type: EventType) {
  eventSettings.value.enabled[type] = !eventSettings.value.enabled[type]
  EventSystem.updateSettings({ enabled: eventSettings.value.enabled })
}

// 选择背景音乐
function selectBgm(bgmId: string) {
  updateAudioSetting('currentBgm', bgmId)
}

// 添加自定义背景音乐
function addCustomBgm() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'audio/*'
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file) return

    // 读取文件为 base64
    const reader = new FileReader()
    reader.onload = () => {
      const base64 = reader.result as string
      const name = file.name.replace(/\.[^/.]+$/, '')
      const id = AudioManager.addCustomBgm(name, base64)
      audioSettings.value = AudioManager.getSettings()
    }
    reader.readAsDataURL(file)
  }
  input.click()
}

// 删除自定义背景音乐
function removeCustomBgm(id: string) {
  AudioManager.removeCustomBgm(id)
  audioSettings.value = AudioManager.getSettings()
}

// 测试事件
function testEvent(type: EventType) {
  switch (type) {
    case 'plan_complete_100':
      EventSystem.triggerEvent('plan_complete_100', '完美达成！', '今天的计划已100%完成！')
      break
    case 'plan_complete_90':
      EventSystem.triggerEvent('plan_complete_90', '即将达成！', '计划已完成90%，加油！')
      break
    case 'plan_low_progress':
      EventSystem.triggerEvent('plan_low_progress', '时间不早了', '完成度较低，需要加把劲！')
      break
    case 'record_added':
      EventSystem.triggerEvent('record_added', '记录已添加', '新的时间记录已保存')
      break
    case 'plan_changed':
      EventSystem.triggerEvent('plan_changed', '计划已切换', '已切换到新的日计划')
      break
    case 'achievement_unlocked':
      EventSystem.triggerEvent('achievement_unlocked', '成就解锁！', '恭喜你达成新成就！')
      break
  }
}

// 当前设置项
type SettingTab = 'audio' | 'events'
const currentTab = ref<SettingTab>('audio')
</script>

<template>
  <div class="audio-settings-view">
    <header class="header">
      <button class="back-btn" @click="router.push('/settings')">
        <ArrowLeft :size="16" />
        <span>返回设置</span>
      </button>
      <h1>声音设置</h1>
    </header>

    <main class="main-content">
      <!-- 标签切换 -->
      <div class="tab-bar">
        <button
          class="tab-btn"
          :class="{ active: currentTab === 'audio' }"
          @click="currentTab = 'audio'"
        >
          <Volume2 :size="18" />
          <span>音效设置</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: currentTab === 'events' }"
          @click="currentTab = 'events'"
        >
          <Bell :size="18" />
          <span>事件设置</span>
        </button>
      </div>

      <!-- 音效设置 -->
      <template v-if="currentTab === 'audio'">
        <!-- 主开关 -->
        <section class="settings-section">
          <div class="section-header">
            <h2>总开关</h2>
          </div>
          <label class="toggle-row">
            <span>启用声音</span>
            <input
              type="checkbox"
              :checked="audioSettings.enabled"
              @change="updateAudioSetting('enabled', ($event.target as HTMLInputElement).checked)"
            />
          </label>
        </section>

        <!-- 音效设置 -->
        <section class="settings-section">
          <div class="section-header">
            <h2>音效</h2>
            <label class="toggle-inline">
              <input
                type="checkbox"
                :checked="audioSettings.sfxEnabled"
                @change="updateAudioSetting('sfxEnabled', ($event.target as HTMLInputElement).checked)"
              />
              <span>启用音效</span>
            </label>
          </div>

          <div class="volume-row">
            <span>主音量</span>
            <input
              type="range"
              min="0"
              max="100"
              :value="audioSettings.sfxVolume"
              @input="updateAudioSetting('sfxVolume', Number(($event.target as HTMLInputElement).value))"
            />
            <span class="volume-value">{{ audioSettings.sfxVolume }}%</span>
          </div>

          <div class="sfx-list">
            <div v-for="sfx in soundTypes" :key="sfx.type" class="sfx-item">
              <div class="sfx-info">
                <span class="sfx-name">{{ sfx.name }}</span>
                <span class="sfx-desc">{{ sfx.description }}</span>
              </div>
              <div class="sfx-controls">
                <input
                  type="range"
                  min="0"
                  max="100"
                  :value="audioSettings.sfxVolumes[sfx.type]"
                  @input="updateSfxVolume(sfx.type, Number(($event.target as HTMLInputElement).value))"
                />
                <button class="test-btn" @click="testSound(sfx.type)">
                  <Play :size="14" />
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- 背景音乐设置 -->
        <section class="settings-section">
          <div class="section-header">
            <h2>背景音乐</h2>
            <label class="toggle-inline">
              <input
                type="checkbox"
                :checked="audioSettings.bgmEnabled"
                @change="updateAudioSetting('bgmEnabled', ($event.target as HTMLInputElement).checked)"
              />
              <span>启用背景音乐</span>
            </label>
          </div>

          <div class="volume-row">
            <span>音量</span>
            <input
              type="range"
              min="0"
              max="100"
              :value="audioSettings.bgmVolume"
              @input="updateAudioSetting('bgmVolume', Number(($event.target as HTMLInputElement).value))"
            />
            <span class="volume-value">{{ audioSettings.bgmVolume }}%</span>
          </div>

          <div class="bgm-list">
            <div class="bgm-section-title">内置音乐</div>
            <button
              v-for="bgm in allBgm.filter(b => !b.custom)"
              :key="bgm.id"
              class="bgm-item"
              :class="{ active: audioSettings.currentBgm === bgm.id }"
              @click="selectBgm(bgm.id)"
            >
              <Music :size="16" />
              <span>{{ bgm.name }}</span>
              <span v-if="audioSettings.currentBgm === bgm.id" class="check-mark">✓</span>
            </button>

            <div class="bgm-section-title">
              自定义音乐
              <button class="add-bgm-btn" @click="addCustomBgm">
                <Plus :size="14" />
              </button>
            </div>
            <button
              v-for="bgm in allBgm.filter(b => b.custom)"
              :key="bgm.id"
              class="bgm-item"
              :class="{ active: audioSettings.currentBgm === bgm.id }"
              @click="selectBgm(bgm.id)"
            >
              <Music :size="16" />
              <span>{{ bgm.name }}</span>
              <span v-if="audioSettings.currentBgm === bgm.id" class="check-mark">✓</span>
              <button class="remove-btn" @click.stop="removeCustomBgm(bgm.id)">
                <Trash2 :size="14" />
              </button>
            </button>
            <div v-if="allBgm.filter(b => b.custom).length === 0" class="empty-hint">
              点击 + 添加本地音乐文件
            </div>
          </div>
        </section>
      </template>

      <!-- 事件设置 -->
      <template v-else>
        <section class="settings-section">
          <div class="section-header">
            <h2>事件通知</h2>
          </div>
          <p class="section-desc">配置哪些事件触发时显示通知弹窗并播放音效</p>

          <div class="event-list">
            <div v-for="event in eventTypes" :key="event.type" class="event-item">
              <div class="event-info">
                <span class="event-name">{{ event.name }}</span>
                <span class="event-desc">{{ event.description }}</span>
              </div>
              <div class="event-controls">
                <label class="toggle-inline">
                  <input
                    type="checkbox"
                    :checked="eventSettings.enabled[event.type]"
                    @change="toggleEvent(event.type)"
                  />
                </label>
                <button class="test-btn" @click="testEvent(event.type)">
                  <Bell :size="14" />
                </button>
              </div>
            </div>
          </div>
        </section>

        <section class="settings-section">
          <div class="section-header">
            <h2>预警设置</h2>
          </div>

          <div class="setting-row">
            <span>低完成度阈值</span>
            <div class="input-group">
              <input
                type="number"
                min="0"
                max="100"
                :value="eventSettings.lowProgressThreshold"
                @input="updateEventSetting('lowProgressThreshold', Number(($event.target as HTMLInputElement).value))"
              />
              <span>%</span>
            </div>
          </div>

          <div class="setting-row">
            <span>预警时间（24小时制）</span>
            <div class="input-group">
              <input
                type="number"
                min="0"
                max="23"
                :value="eventSettings.warningHour"
                @input="updateEventSetting('warningHour', Number(($event.target as HTMLInputElement).value))"
              />
              <span>时</span>
            </div>
          </div>

          <p class="setting-hint">
            当时间超过 {{ eventSettings.warningHour }}:00 且完成度低于 {{ eventSettings.lowProgressThreshold }}% 时触发预警
          </p>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.audio-settings-view {
  min-height: 100vh;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.back-btn:hover {
  background: var(--color-bg-tertiary);
}

.header h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.main-content {
  flex: 1;
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
}

.tab-bar {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-xs);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--color-text-primary);
}

.tab-btn.active {
  background: var(--color-bg);
  color: var(--color-text-primary);
  box-shadow: var(--shadow-sm);
}

.settings-section {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.section-header h2 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.section-desc {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-md) 0;
}

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.toggle-row input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.toggle-inline {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  cursor: pointer;
}

.toggle-inline input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.volume-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.volume-row input[type="range"] {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  outline: none;
}

.volume-row input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
}

.volume-value {
  width: 40px;
  text-align: right;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.sfx-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.sfx-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm);
  background: var(--color-bg);
  border-radius: var(--radius-md);
}

.sfx-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sfx-name {
  font-size: 0.875rem;
  font-weight: 500;
}

.sfx-desc {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.sfx-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.sfx-controls input[type="range"] {
  width: 80px;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  outline: none;
}

.sfx-controls input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
}

.test-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.test-btn:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.bgm-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.bgm-section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin: var(--spacing-sm) 0 var(--spacing-xs);
  text-transform: uppercase;
}

.add-bgm-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.add-bgm-btn:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.bgm-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  color: var(--color-text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.bgm-item:hover {
  background: var(--color-bg-tertiary);
}

.bgm-item.active {
  border-color: var(--color-primary);
  background: var(--color-primary);
  background: rgba(99, 102, 241, 0.1);
}

.check-mark {
  margin-left: auto;
  color: var(--color-primary);
  font-weight: bold;
}

.remove-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-left: auto;
}

.remove-btn:hover {
  background: var(--color-error);
  color: white;
}

.empty-hint {
  text-align: center;
  padding: var(--spacing-md);
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
}

.event-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.event-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm);
  background: var(--color-bg);
  border-radius: var(--radius-md);
}

.event-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.event-name {
  font-size: 0.875rem;
  font-weight: 500;
}

.event-desc {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.event-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) 0;
}

.input-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.input-group input[type="number"] {
  width: 60px;
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-primary);
  text-align: center;
}

.input-group span {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.setting-hint {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin: var(--spacing-sm) 0 0 0;
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--color-border);
}
</style>
