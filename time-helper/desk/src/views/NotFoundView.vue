<script setup lang="ts">
import { Home, Compass } from 'lucide-vue-next'
import { useI18n } from '@/i18n'

const { t } = useI18n()
</script>

<template>
  <main class="not-found-page" role="main">
    <section class="not-found-card theme-card" aria-labelledby="not-found-title">
      <div class="not-found-icon" aria-hidden="true"><Compass :size="30" /></div>
      <p class="not-found-code">404</p>
      <h1 id="not-found-title">{{ t('notFound.title') }}</h1>
      <p class="not-found-description">{{ t('notFound.description') }}</p>
      <RouterLink class="not-found-home" to="/">
        <Home :size="16" />
        {{ t('notFound.backHome') }}
      </RouterLink>
    </section>
  </main>
</template>

<style scoped>
.not-found-page {
  display: grid;
  min-height: min(70vh, 720px);
  place-items: center;
  padding: 32px 16px;
}

.not-found-card {
  display: grid;
  justify-items: center;
  width: min(460px, 100%);
  padding: clamp(28px, 6vw, 52px) 24px;
  border: 1px solid var(--color-border);
  border-radius: 22px;
  background: color-mix(in srgb, var(--color-bg-elevated) 88%, transparent);
  box-shadow: var(--theme-box-shadow, 0 18px 48px rgb(0 0 0 / 8%));
  text-align: center;
}

.not-found-icon {
  display: grid;
  width: 58px;
  height: 58px;
  place-items: center;
  border-radius: 18px;
  color: var(--color-primary);
  background: var(--color-primary-muted);
}

.not-found-code {
  margin: 20px 0 4px;
  color: var(--color-primary);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .18em;
}

h1 { margin: 0; color: var(--color-text-primary); font-size: clamp(22px, 4vw, 30px); }
.not-found-description { max-width: 340px; margin: 10px 0 24px; color: var(--color-text-secondary); line-height: 1.6; }
.not-found-home { display: inline-flex; align-items: center; gap: 7px; border-radius: 10px; padding: 9px 14px; color: var(--color-button-text); background: var(--color-primary); font-size: 13px; font-weight: 650; text-decoration: none; }
.not-found-home:hover { filter: brightness(1.06); }
.not-found-home:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 3px; }
</style>
