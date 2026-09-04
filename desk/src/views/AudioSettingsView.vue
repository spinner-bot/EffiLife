<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Volume2, Music, Plus, Trash2, Play } from 'lucide-vue-next'
import { AudioManager } from '@/audio'
import type { SoundType, AudioSettings } from '@/audio'

const router = useRouter()

const audioSettings = ref<AudioSettings>(AudioManager.getSettings())

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

const allBgm = computed(() => AudioManager.getAllBgm())

// ========= 音效操作 =========

function testSound(type: SoundType) {
  AudioManager.playSound(type)
}

function updateAudioSetting<K extends keyof AudioSettings>(key: K, value: AudioSettings[K]) {
  audioSettings.value[key] = value
  AudioManager.updateSettings({ [key]: value })
}

function updateSfxVolume(type: SoundType, volume: number) {
  audioSettings.value.sfxVolumes[type] = volume
  AudioManager.updateSettings({ sfxVolumes: audioSettings.value.sfxVolumes })
}

function selectBgm(bgmId: string) {
  updateAudioSetting('currentBgm', bgmId)
}

function addCustomBgm() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'audio/*'
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      const base64 = reader.result as string
      const name = file.name.replace(/\.[^/.]+$/, '')
      AudioManager.addCustomBgm(name, base64)
      audioSettings.value = AudioManager.getSettings()
    }
    reader.readAsDataURL(file)
  }
  input.click()
}

function removeCustomBgm(id: string) {
  AudioManager.removeCustomBgm(id)
  audioSettings.value = AudioManager.getSettings()
}

type SettingTab = 'audio'
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
        <button class="tab-btn active">
          <Volume2 :size="18" />
          <span>音效</span>
        </button>
      </div>

      <!-- ============ 音效设置 ============ -->
      <template v-if="currentTab === 'audio'">
        <section class="settings-section">
          <div class="section-header">
            <h2>总开关</h2>
          </div>
          <label class="toggle-row">
            <span>启用声音</span>
            <input type="checkbox" :checked="audioSettings.enabled" @change="updateAudioSetting('enabled', ($event.target as HTMLInputElement).checked)" />
          </label>
        </section>

        <section class="settings-section">
          <div class="section-header">
            <h2>音效</h2>
            <label class="toggle-inline">
              <input type="checkbox" :checked="audioSettings.sfxEnabled" @change="updateAudioSetting('sfxEnabled', ($event.target as HTMLInputElement).checked)" />
              <span>启用</span>
            </label>
          </div>

          <div class="volume-row">
            <span>主音量</span>
            <input type="range" min="0" max="100" :value="audioSettings.sfxVolume" @input="updateAudioSetting('sfxVolume', Number(($event.target as HTMLInputElement).value))" />
            <span class="volume-value">{{ audioSettings.sfxVolume }}%</span>
          </div>

          <div class="sfx-list">
            <div v-for="sfx in soundTypes" :key="sfx.type" class="sfx-item">
              <div class="sfx-info">
                <span class="sfx-name">{{ sfx.name }}</span>
                <span class="sfx-desc">{{ sfx.description }}</span>
              </div>
              <div class="sfx-controls">
                <input type="range" min="0" max="100" :value="audioSettings.sfxVolumes[sfx.type]" @input="updateSfxVolume(sfx.type, Number(($event.target as HTMLInputElement).value))" />
                <button class="test-btn" @click="testSound(sfx.type)"><Play :size="14" /></button>
              </div>
            </div>
          </div>
        </section>

        <section class="settings-section">
          <div class="section-header">
            <h2>背景音乐</h2>
            <label class="toggle-inline">
              <input type="checkbox" :checked="audioSettings.bgmEnabled" @change="updateAudioSetting('bgmEnabled', ($event.target as HTMLInputElement).checked)" />
              <span>启用</span>
            </label>
          </div>

          <div class="volume-row">
            <span>音量</span>
            <input type="range" min="0" max="100" :value="audioSettings.bgmVolume" @input="updateAudioSetting('bgmVolume', Number(($event.target as HTMLInputElement).value))" />
            <span class="volume-value">{{ audioSettings.bgmVolume }}%</span>
          </div>

          <div class="bgm-list">
            <div class="bgm-section-title">内置音乐</div>
            <button v-for="bgm in allBgm.filter(b => !b.custom)" :key="bgm.id" class="bgm-item" :class="{ active: audioSettings.currentBgm === bgm.id }" @click="selectBgm(bgm.id)">
              <Music :size="16" />
              <span>{{ bgm.name }}</span>
              <span v-if="audioSettings.currentBgm === bgm.id" class="check-mark">✓</span>
            </button>

            <div class="bgm-section-title">
              自定义音乐
              <button class="add-bgm-btn" @click="addCustomBgm"><Plus :size="14" /></button>
            </div>
            <button v-for="bgm in allBgm.filter(b => b.custom)" :key="bgm.id" class="bgm-item" :class="{ active: audioSettings.currentBgm === bgm.id }" @click="selectBgm(bgm.id)">
              <Music :size="16" />
              <span>{{ bgm.name }}</span>
              <span v-if="audioSettings.currentBgm === bgm.id" class="check-mark">✓</span>
              <button class="remove-btn" @click.stop="removeCustomBgm(bgm.id)"><Trash2 :size="14" /></button>
            </button>
            <div v-if="allBgm.filter(b => b.custom).length === 0" class="empty-hint">点击 + 添加本地音乐文件</div>
          </div>
        </section>
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

.back-btn:hover { background: var(--color-bg-tertiary); }

.header h1 { font-size: 1.5rem; font-weight: 600; }

.main-content { flex: 1; max-width: 600px; margin: 0 auto; width: 100%; }

.tab-bar {
  display: flex;
  gap: var(--spacing-xs);
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
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover { color: var(--color-text-primary); }

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

.section-header h2 { font-size: 1rem; font-weight: 600; margin: 0; }

.section-desc {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-md) 0;
  line-height: 1.5;
}

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.toggle-row input[type="checkbox"],
.toggle-inline input[type="checkbox"] {
  width: 16px;
  height: 16px;
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
  font-family: var(--font-mono);
}

.sfx-list, .event-list, .warning-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.sfx-item, .event-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm);
  background: var(--color-bg);
  border-radius: var(--radius-md);
}

.sfx-info, .event-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sfx-name, .event-name { font-size: 0.875rem; font-weight: 500; }
.sfx-desc, .event-desc { font-size: 0.75rem; color: var(--color-text-tertiary); }

.sfx-controls, .event-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.sfx-controls input[type="range"] { width: 80px; }

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

.test-btn.danger:hover {
  background: var(--color-error);
  border-color: var(--color-error);
}

/* 背景音乐 */
.bgm-list { display: flex; flex-direction: column; gap: var(--spacing-xs); }

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

.bgm-item:hover { background: var(--color-bg-tertiary); }

.bgm-item.active {
  border-color: var(--color-primary);
  background: rgba(99, 102, 241, 0.1);
}

.check-mark { margin-left: auto; color: var(--color-primary); font-weight: bold; }

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

.remove-btn:hover { background: var(--color-error); color: white; }

.empty-hint {
  text-align: center;
  padding: var(--spacing-md);
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
}

/* 预警规则 */
.warning-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.warning-item:hover { border-color: var(--color-border-hover); }

.warning-item.disabled { opacity: 0.5; }

.warning-main {
  flex: 1;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.warning-time {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  color: var(--color-primary);
}

.time-text {
  font-size: 1.25rem;
  font-weight: 700;
  font-family: var(--font-mono);
}

.warning-detail {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}

.warning-detail strong {
  color: var(--color-text-primary);
  font-weight: 600;
}

.warning-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.add-rule-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-top: var(--spacing-sm);
}

.add-rule-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: rgba(99, 102, 241, 0.05);
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn var(--transition-fast);
}

.modal {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  width: 90%;
  max-width: 420px;
  animation: slideUp var(--transition-normal);
}

.modal h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-lg) 0;
}

.form-row {
  margin-bottom: var(--spacing-lg);
}

.form-row > label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.time-picker {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.time-unit {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.time-unit label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.time-unit input {
  width: 60px;
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  text-align: center;
  font-size: 1.125rem;
  font-family: var(--font-mono);
}

.time-sep {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--color-text-secondary);
  margin-top: 16px;
}

.threshold-picker {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.threshold-picker input[type="range"] {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  outline: none;
}

.threshold-picker input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
}

.threshold-value {
  width: 50px;
  text-align: right;
  font-size: 1.125rem;
  font-weight: 600;
  font-family: var(--font-mono);
  color: var(--color-primary);
}

.form-hint {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin: var(--spacing-xs) 0 0 0;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-xl);
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn.secondary {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.btn.secondary:hover { background: var(--color-bg-tertiary); }

.btn.primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.btn.primary:hover { background: var(--color-primary-hover); }

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
