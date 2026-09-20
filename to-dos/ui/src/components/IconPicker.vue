<script setup lang="ts">
/**
 * 图标选择器组件 (v0.5.0)
 *
 * 支持选择：
 * - 100+ lucide 图标
 * - 62 种 ASCII 图标（A-Z, a-z, 0-9）
 * - 20 种预设颜色 + 自定义颜色
 */

import { ref, computed } from 'vue'
import {
  Circle, Briefcase, BookOpen, Home, Heart, Star, Zap, Target,
  Clock, Calendar, Flag, Trophy, Rocket, Lightbulb, Music,
  Camera, Code, FileText, Globe, GraduationCap, Headphones,
  Image, Key, Laptop, Mail, MapPin, MessageSquare, Mic,
  Palette, Phone, Pin, Printer, Puzzle, Radio, RefreshCw,
  Save, Search, Settings, Shield, ShoppingBag, Smartphone,
  Speaker, Tool, Tv, Umbrella, User, Video, Wallet, Wifi,
  Award, Battery, Bell, Bookmark, BriefcaseBusiness, Cake,
  Car, Coffee, Compass, Cookie, Cpu, Dumbbell, Flame,
  Gamepad2, Gem, GitBranch, Hammer, Joystick, Leaf,
  Lock, Magnet, Megaphone, Mountain, NotebookPen, Package,
  Plane, Plant, Pocket, Projector, Radar, Rainbow,
  Smile, Snowflake, Sparkles, Sprout, Sun, Sunrise,
  Tent, Timer, Truck, Watch, Wine, Wrench,
} from 'lucide-vue-next'
import type { LucideIcon } from 'lucide-vue-next'
import { PRESET_COLORS, ASCII_ICONS } from '@/types'

const props = defineProps<{
  modelValue: string          // 当前选中的图标名
  modelColor: string          // 当前选中的颜色
  modelAscii?: string         // 当前选中的 ASCII 图标
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'update:modelColor', value: string): void
  (e: 'update:modelAscii', value: string): void
}>()

// 标签页: icons | ascii | colors
const activeTab = ref<'icons' | 'ascii' | 'colors'>('icons')

// lucide 图标列表
const lucideIcons: { name: string; component: LucideIcon }[] = [
  { name: 'circle', component: Circle },
  { name: 'briefcase', component: Briefcase },
  { name: 'book-open', component: BookOpen },
  { name: 'home', component: Home },
  { name: 'heart', component: Heart },
  { name: 'star', component: Star },
  { name: 'zap', component: Zap },
  { name: 'target', component: Target },
  { name: 'clock', component: Clock },
  { name: 'calendar', component: Calendar },
  { name: 'flag', component: Flag },
  { name: 'trophy', component: Trophy },
  { name: 'rocket', component: Rocket },
  { name: 'lightbulb', component: Lightbulb },
  { name: 'music', component: Music },
  { name: 'camera', component: Camera },
  { name: 'code', component: Code },
  { name: 'file-text', component: FileText },
  { name: 'globe', component: Globe },
  { name: 'graduation-cap', component: GraduationCap },
  { name: 'headphones', component: Headphones },
  { name: 'image', component: Image },
  { name: 'key', component: Key },
  { name: 'laptop', component: Laptop },
  { name: 'mail', component: Mail },
  { name: 'map-pin', component: MapPin },
  { name: 'message-square', component: MessageSquare },
  { name: 'mic', component: Mic },
  { name: 'palette', component: Palette },
  { name: 'phone', component: Phone },
  { name: 'pin', component: Pin },
  { name: 'printer', component: Printer },
  { name: 'puzzle', component: Puzzle },
  { name: 'radio', component: Radio },
  { name: 'refresh-cw', component: RefreshCw },
  { name: 'save', component: Save },
  { name: 'search', component: Search },
  { name: 'settings', component: Settings },
  { name: 'shield', component: Shield },
  { name: 'shopping-bag', component: ShoppingBag },
  { name: 'smartphone', component: Smartphone },
  { name: 'speaker', component: Speaker },
  { name: 'wrench', component: Tool },
  { name: 'tv', component: Tv },
  { name: 'umbrella', component: Umbrella },
  { name: 'user', component: User },
  { name: 'video', component: Video },
  { name: 'wallet', component: Wallet },
  { name: 'wifi', component: Wifi },
  { name: 'award', component: Award },
  { name: 'battery', component: Battery },
  { name: 'bell', component: Bell },
  { name: 'bookmark', component: Bookmark },
  { name: 'cake', component: Cake },
  { name: 'car', component: Car },
  { name: 'coffee', component: Coffee },
  { name: 'compass', component: Compass },
  { name: 'cookie', component: Cookie },
  { name: 'cpu', component: Cpu },
  { name: 'dumbbell', component: Dumbbell },
  { name: 'flame', component: Flame },
  { name: 'gamepad-2', component: Gamepad2 },
  { name: 'gem', component: Gem },
  { name: 'git-branch', component: GitBranch },
  { name: 'hammer', component: Hammer },
  { name: 'joystick', component: Joystick },
  { name: 'leaf', component: Leaf },
  { name: 'lock', component: Lock },
  { name: 'magnet', component: Magnet },
  { name: 'megaphone', component: Megaphone },
  { name: 'mountain', component: Mountain },
  { name: 'notebook-pen', component: NotebookPen },
  { name: 'package', component: Package },
  { name: 'plane', component: Plane },
  { name: 'plant', component: Plant },
  { name: 'pocket', component: Pocket },
  { name: 'projector', component: Projector },
  { name: 'radar', component: Radar },
  { name: 'rainbow', component: Rainbow },
  { name: 'smile', component: Smile },
  { name: 'snowflake', component: Snowflake },
  { name: 'sparkles', component: Sparkles },
  { name: 'sprout', component: Sprout },
  { name: 'sun', component: Sun },
  { name: 'sunrise', component: Sunrise },
  { name: 'tent', component: Tent },
  { name: 'timer', component: Timer },
  { name: 'truck', component: Truck },
  { name: 'watch', component: Watch },
  { name: 'wine', component: Wine },
]

// 搜索过滤
const searchQuery = ref('')

const filteredIcons = computed(() => {
  if (!searchQuery.value) return lucideIcons
  const q = searchQuery.value.toLowerCase()
  return lucideIcons.filter(i => i.name.includes(q))
})

function selectIcon(name: string) {
  emit('update:modelValue', name)
}

function selectAscii(char: string) {
  emit('update:modelAscii', char)
}

function selectColor(color: string) {
  emit('update:modelColor', color)
}

const tabs = [
  { key: 'icons' as const, label: '图标' },
  { key: 'ascii' as const, label: 'ASCII' },
  { key: 'colors' as const, label: '颜色' },
]
</script>

<template>
  <div class="icon-picker">
    <!-- 标签页 -->
    <div class="picker-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 图标标签页 -->
    <div v-if="activeTab === 'icons'" class="picker-content">
      <input
        v-model="searchQuery"
        type="text"
        class="picker-search"
        placeholder="搜索图标..."
      />
      <div class="icon-grid">
        <button
          v-for="icon in filteredIcons"
          :key="icon.name"
          class="icon-btn"
          :class="{ selected: modelValue === icon.name }"
          @click="selectIcon(icon.name)"
          :title="icon.name"
        >
          <component :is="icon.component" :size="20" />
        </button>
      </div>
    </div>

    <!-- ASCII 标签页 -->
    <div v-if="activeTab === 'ascii'" class="picker-content">
      <div class="ascii-grid">
        <button
          v-for="char in ASCII_ICONS"
          :key="char"
          class="ascii-btn"
          :class="{ selected: modelAscii === char }"
          @click="selectAscii(char)"
        >
          {{ char }}
        </button>
      </div>
    </div>

    <!-- 颜色标签页 -->
    <div v-if="activeTab === 'colors'" class="picker-content">
      <div class="color-grid">
        <button
          v-for="color in PRESET_COLORS"
          :key="color"
          class="color-btn"
          :class="{ selected: modelColor === color }"
          :style="{ background: color }"
          @click="selectColor(color)"
          :title="color"
        />
      </div>
      <div class="custom-color">
        <label class="color-label">自定义颜色</label>
        <input
          type="color"
          :value="modelColor"
          @input="selectColor(($event.target as HTMLInputElement).value)"
          class="color-input"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.icon-picker {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  overflow: hidden;
}

.picker-tabs {
  display: flex;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
}

.tab-btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  background: transparent;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.15s;
}

.tab-btn:hover {
  color: var(--color-text-primary);
  background: var(--color-bg-hover);
}

.tab-btn.active {
  color: var(--color-primary);
  background: var(--color-bg);
  box-shadow: inset 0 -2px 0 var(--color-primary);
}

.picker-content {
  padding: 12px;
  max-height: 280px;
  overflow-y: auto;
}

.picker-search {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg);
  font-size: 12px;
  color: var(--color-text-primary);
  margin-bottom: 10px;
}

.picker-search:focus {
  outline: none;
  border-color: var(--color-primary);
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(36px, 1fr));
  gap: 4px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.icon-btn:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-border);
  color: var(--color-text-primary);
}

.icon-btn.selected {
  background: var(--color-primary-muted);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.ascii-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(32px, 1fr));
  gap: 4px;
}

.ascii-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: 4px;
  background: transparent;
  font-size: 14px;
  font-weight: 600;
  font-family: var(--font-mono, monospace);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.ascii-btn:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-border);
}

.ascii-btn.selected {
  background: var(--color-primary-muted);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.color-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(28px, 1fr));
  gap: 6px;
  margin-bottom: 12px;
}

.color-btn {
  width: 28px;
  height: 28px;
  border: 2px solid transparent;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.15s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.color-btn:hover {
  transform: scale(1.15);
}

.color-btn.selected {
  border-color: var(--color-text-primary);
  box-shadow: 0 0 0 2px var(--color-bg), 0 0 0 4px currentColor;
}

.custom-color {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--color-border);
}

.color-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.color-input {
  width: 36px;
  height: 28px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  cursor: pointer;
  padding: 0;
}
</style>
