<script setup lang="ts">
import { ArrowLeft, Archive, ClipboardList, Clock3, Palette, PlayCircle } from 'lucide-vue-next'
import { useI18n } from '@/i18n'

defineEmits<{ back: [] }>()
const { t } = useI18n()
</script>

<template>
  <section class="help-panel" @keydown.esc="$emit('back')">
    <header class="help-panel-header">
      <button class="help-back" type="button" :aria-label="t('settings.back')" @click="$emit('back')">
        <ArrowLeft :size="18" />
      </button>
      <div>
        <p class="help-eyebrow">{{ t('settings.help.eyebrow') }}</p>
        <h2>{{ t('settings.help.title') }}</h2>
      </div>
    </header>

    <div class="help-grid">
      <article class="help-card help-card-wide">
        <div class="help-card-heading"><PlayCircle :size="20" /><h3>{{ t('settings.help.quickTitle') }}</h3></div>
        <ol class="help-steps">
          <li><strong>{{ t('settings.help.stepPlanTitle') }}</strong><span>{{ t('settings.help.stepPlanDescription') }}</span></li>
          <li><strong>{{ t('settings.help.stepTodoTitle') }}</strong><span>{{ t('settings.help.stepTodoDescription') }}</span></li>
          <li><strong>{{ t('settings.help.stepTimeTitle') }}</strong><span>{{ t('settings.help.stepTimeDescription') }}</span></li>
        </ol>
      </article>

      <article class="help-card">
        <div class="help-card-heading"><ClipboardList :size="20" /><h3>{{ t('settings.help.planTitle') }}</h3></div>
        <p>{{ t('settings.help.planDescription') }}</p>
      </article>
      <article class="help-card">
        <div class="help-card-heading"><Clock3 :size="20" /><h3>{{ t('settings.help.timeTitle') }}</h3></div>
        <p>{{ t('settings.help.timeDescription') }}</p>
      </article>
      <article class="help-card">
        <div class="help-card-heading"><Palette :size="20" /><h3>{{ t('settings.help.themeTitle') }}</h3></div>
        <p>{{ t('settings.help.themeDescription') }}</p>
      </article>
      <article class="help-card">
        <div class="help-card-heading"><Archive :size="20" /><h3>{{ t('settings.help.archiveTitle') }}</h3></div>
        <p>{{ t('settings.help.archiveDescription') }}</p>
      </article>
    </div>

    <button class="help-close" type="button" @click="$emit('back')">{{ t('settings.back') }}</button>
  </section>
</template>

<style scoped>
.help-panel { color: var(--color-text-primary); }
.help-panel-header { display: flex; align-items: center; gap: 12px; margin-bottom: var(--spacing-lg); }
.help-back { display: grid; place-items: center; width: 36px; height: 36px; border: 1px solid var(--color-border); border-radius: var(--radius-md); color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; }
.help-back:hover { color: var(--color-primary); border-color: var(--color-primary); }
.help-eyebrow { margin: 0 0 3px; color: var(--color-text-tertiary); font-size: 0.75rem; letter-spacing: .08em; }
.help-panel h2 { margin: 0; font-size: 1.45rem; }
.help-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--spacing-md); }
.help-card { padding: var(--spacing-lg); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-bg-secondary); }
.help-card-wide { grid-column: 1 / -1; }
.help-card-heading { display: flex; align-items: center; gap: 9px; color: var(--color-primary); }
.help-card-heading h3 { margin: 0; color: var(--color-text-primary); font-size: 1rem; }
.help-card p { margin: var(--spacing-sm) 0 0; color: var(--color-text-secondary); line-height: 1.65; }
.help-steps { display: grid; gap: var(--spacing-md); margin: var(--spacing-md) 0 0; padding-left: 1.25rem; }
.help-steps li { padding-left: 0.35rem; }
.help-steps strong, .help-steps span { display: block; }
.help-steps span { margin-top: 3px; color: var(--color-text-secondary); line-height: 1.55; }
.help-close { width: 100%; margin-top: var(--spacing-lg); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 0.7rem 1rem; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; }
.help-close:hover { border-color: var(--color-primary); color: var(--color-primary); }
@media (max-width: 680px) { .help-grid { grid-template-columns: 1fr; } .help-card-wide { grid-column: auto; } }
</style>
