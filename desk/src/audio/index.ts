// 音频系统导出
export { AudioManager, DEFAULT_AUDIO_SETTINGS, BGM_LIST } from './AudioManager'
export type { SoundType, AudioSettings } from './AudioManager'

export { EventSystem, DEFAULT_EVENT_SETTINGS, DEFAULT_WARNING_RULES } from './EventSystem'
export type { EventType, AppEvent, EventSettings, WarningRule, WarningRecord } from './EventSystem'

export { default as EventPopup } from './EventPopup.vue'
