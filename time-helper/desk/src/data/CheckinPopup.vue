<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { CheckinSystem } from './CheckinSystem'
import { AudioManager } from '@/audio'
import { X, Flame } from 'lucide-vue-next'

const props = defineProps<{
  show: boolean
  planName: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'checkin', streak: number): void
}>()

// 阶段：'ready' | 'animating' | 'done'
const phase = ref<'ready' | 'animating' | 'done'>('ready')
const displayStreak = ref(0)
const targetStreak = ref(0)
const showBurst = ref(false)
let animationTimer: number | null = null

const currentStreak = computed(() => CheckinSystem.getCurrentStreak())

// 执行打卡
function doCheckin() {
  if (phase.value !== 'ready') return

  // 播放打卡音效
  AudioManager.playSound('achievement')

  const result = CheckinSystem.checkin(props.planName, 100)
  if (result === null) {
    // 今天已经打卡过
    emit('close')
    return
  }

  const newStreak = result
  targetStreak.value = newStreak
  phase.value = 'animating'

  // 数字递增动画
  const startStreak = newStreak - 1
  displayStreak.value = startStreak
  const duration = 1200
  const startTime = Date.now()

  function animate() {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    // easeOutCubic
    const eased = 1 - Math.pow(1 - progress, 3)
    displayStreak.value = Math.round(startStreak + (newStreak - startStreak) * eased)

    if (progress < 1) {
      animationTimer = requestAnimationFrame(animate)
    } else {
      displayStreak.value = newStreak
      showBurst.value = true
      setTimeout(() => {
        phase.value = 'done'
      }, 300)
    }
  }

  animationTimer = requestAnimationFrame(animate)
}

function close() {
  if (animationTimer) {
    cancelAnimationFrame(animationTimer)
  }
  const wasDone = phase.value === 'done'
  phase.value = 'ready'
  displayStreak.value = 0
  targetStreak.value = 0
  showBurst.value = false
  emit('close')
  if (wasDone) {
    emit('checkin', targetStreak.value)
  }
}

onUnmounted(() => {
  if (animationTimer) {
    cancelAnimationFrame(animationTimer)
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="checkin-overlay" @click.self="phase === 'done' && close()">
        <div class="checkin-popup">
          <button v-if="phase === 'done'" class="close-btn" @click="close">
            <X :size="20" />
          </button>

          <div class="popup-content">
            <!-- 准备阶段 -->
            <template v-if="phase === 'ready'">
              <div class="ready-content">
                <div class="ready-icon">🎯</div>
                <h2 class="ready-title">今日计划已完成！</h2>
                <p class="ready-desc">「{{ planName }}」计划100%达成</p>
                <div class="streak-preview" v-if="currentStreak > 0">
                  <Flame :size="20" class="flame-icon" />
                  <span>当前连续 <strong>{{ currentStreak }}</strong> 天</span>
                </div>
                <button class="checkin-btn" @click="doCheckin">
                  <span class="btn-icon">👆</span>
                  <span class="btn-text">点击打卡</span>
                </button>
              </div>
            </template>

            <!-- 动画阶段 -->
            <template v-else>
              <div class="anim-content">
                <div class="streak-display" :class="{ burst: showBurst }">
                  <Flame :size="48" class="big-flame" />
                  <div class="streak-number">{{ displayStreak }}</div>
                  <div class="streak-unit">天</div>
                </div>
                <h2 class="anim-title">
                  {{ phase === 'done' ? '打卡成功！' : '打卡中...' }}
                </h2>
                <p class="anim-desc" v-if="phase === 'done'">
                  已连续打卡 {{ displayStreak }} 天，继续保持！
                </p>
                <p class="anim-desc" v-else>
                  累计 +1
                </p>
                <!-- 粒子爆发 -->
                <div v-if="showBurst" class="burst-particles">
                  <span v-for="i in 12" :key="i" class="particle" :style="{ '--i': i }"></span>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.checkin-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.checkin-popup {
  position: relative;
  width: 90%;
  max-width: 420px;
  background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
  border: 1px solid rgba(255, 215, 0, 0.3);
  border-radius: 24px;
  padding: 48px 32px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 40px rgba(255, 215, 0, 0.1);
  animation: popupIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.popup-content {
  text-align: center;
  color: white;
}

/* 准备阶段 */
.ready-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.ready-icon {
  font-size: 48px;
  animation: bounce 2s ease-in-out infinite;
}

.ready-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.ready-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.streak-preview {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(255, 215, 0, 0.1);
  border: 1px solid rgba(255, 215, 0, 0.2);
  border-radius: 20px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}

.streak-preview strong {
  color: #ffd700;
  font-weight: 700;
  font-size: 16px;
}

.flame-icon {
  color: #ff8c00;
}

.checkin-btn {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px 48px;
  background: linear-gradient(135deg, #ffd700 0%, #ffb700 100%);
  border: none;
  border-radius: 32px;
  color: #1a1a2e;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 20px rgba(255, 215, 0, 0.4);
}

.checkin-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 30px rgba(255, 215, 0, 0.6);
}

.checkin-btn:active {
  transform: translateY(0);
}

.btn-icon {
  font-size: 20px;
}

/* 动画阶段 */
.anim-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.streak-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.streak-display.burst {
  animation: pulse 0.5s ease;
}

.big-flame {
  color: #ff8c00;
  filter: drop-shadow(0 0 20px rgba(255, 140, 0, 0.8));
  animation: flameFlicker 1.5s ease-in-out infinite;
}

.streak-number {
  font-size: 96px;
  font-weight: 800;
  line-height: 1;
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 50%, #ffd700 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  font-family: var(--font-mono);
  text-shadow: 0 0 40px rgba(255, 215, 0, 0.5);
  filter: drop-shadow(0 0 20px rgba(255, 215, 0, 0.3));
}

.streak-unit {
  font-size: 24px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  letter-spacing: 4px;
}

.anim-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.anim-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

/* 粒子爆发 */
.burst-particles {
  position: absolute;
  top: 50%;
  left: 50%;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #ffd700;
  border-radius: 50%;
  animation: particleBurst 0.8s ease-out forwards;
  transform: translate(-50%, -50%);
}

.particle:nth-child(even) {
  background: #ff8c00;
}

.particle:nth-child(3n) {
  background: #ffed4e;
  width: 6px;
  height: 6px;
}

/* 动画 */
@keyframes popupIn {
  from {
    transform: scale(0.8);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.15); }
  100% { transform: scale(1); }
}

@keyframes flameFlicker {
  0%, 100% { transform: scale(1) rotate(-2deg); }
  50% { transform: scale(1.05) rotate(2deg); }
}

@keyframes particleBurst {
  0% {
    transform: translate(-50%, -50%) translate(0, 0) scale(1);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%)
      translate(
        calc(cos(var(--i) * 30deg) * 100px),
        calc(sin(var(--i) * 30deg) * 100px)
      )
      scale(0);
    opacity: 0;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
