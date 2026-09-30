<script setup lang="ts">
import { ArrowLeft, Download, RotateCcw } from 'lucide-vue-next'
import { useI18n } from '@/i18n'
import type { BackupData, DataStatus } from '@/storage'

defineProps<{ dataStatus: DataStatus | null; backups: BackupData[] }>()
defineEmits<{ back: []; restore: [backup: BackupData]; emergencyExport: [] }>()
const { t, locale } = useI18n()

const BACKUP_TYPE_KEYS: Record<string, string> = {
  archive_import: 'settings.restore.backupArchiveImport',
  config: 'settings.restore.backupConfig',
  plans: 'settings.restore.backupPlans',
  records: 'settings.restore.backupRecords',
  schedule_rules: 'settings.restore.backupScheduleRules',
  manual_plans: 'settings.restore.backupManualPlans',
  pre_migration_full: 'settings.restore.backupMigration',
}

function backupTypeLabel(module: string): string {
  const key = BACKUP_TYPE_KEYS[module]
  return key ? t(key) : module
}
</script>

<template>
  <section class="recovery-panel" @keydown.esc="$emit('back')">
    <header class="recovery-header">
      <button class="recovery-back" type="button" :aria-label="t('settings.back')" @click="$emit('back')"><ArrowLeft :size="18" /></button>
      <div><p class="recovery-eyebrow">{{ t('settings.restore.eyebrow') }}</p><h2>{{ t('settings.restore.title') }}</h2></div>
    </header>

    <section class="recovery-card recovery-status-card">
      <h3>{{ t('settings.restore.statusTitle') }}</h3>
      <div v-if="dataStatus" class="recovery-stats">
        <div><strong>{{ dataStatus.localStorageEmpty ? t('settings.restore.empty') : t('settings.restore.available') }}</strong><span>localStorage</span></div>
        <div><strong>{{ dataStatus.indexedDBEmpty ? t('settings.restore.empty') : t('settings.restore.available') }}</strong><span>IndexedDB</span></div>
        <div><strong>{{ dataStatus.backupCount }}</strong><span>{{ t('settings.restore.backupCount') }}</span></div>
      </div>
      <p v-else class="recovery-muted">{{ t('settings.restore.loading') }}</p>
    </section>

    <section class="recovery-card">
      <div class="recovery-card-heading"><div><h3>{{ t('settings.restore.emergencyTitle') }}</h3><p>{{ t('settings.restore.emergencyDescription') }}</p></div></div>
      <button class="recovery-action" type="button" @click="$emit('emergencyExport')"><Download :size="16" /> {{ t('settings.restore.emergencyAction') }}</button>
    </section>

    <section class="recovery-card">
      <h3>{{ t('settings.restore.availableBackups') }} ({{ backups.length }})</h3>
      <div v-if="backups.length" class="backup-list">
        <div v-for="backup in backups" :key="`${backup.module}_${backup.timestamp}`" class="backup-row">
          <div><strong>{{ backupTypeLabel(backup.module) }}</strong><span>{{ new Date(backup.timestamp).toLocaleString(locale) }}</span></div>
          <button class="recovery-action secondary" type="button" @click="$emit('restore', backup)"><RotateCcw :size="15" /> {{ t('settings.restore.action') }}</button>
        </div>
      </div>
      <p v-else class="recovery-muted">{{ t('settings.restore.noBackups') }}</p>
    </section>

    <button class="recovery-close" type="button" @click="$emit('back')">{{ t('settings.back') }}</button>
  </section>
</template>

<style scoped>
.recovery-panel { color: var(--color-text-primary); }
.recovery-header { display: flex; align-items: center; gap: 12px; margin-bottom: var(--spacing-lg); }
.recovery-back { display: grid; place-items: center; width: 36px; height: 36px; border: 1px solid var(--color-border); border-radius: var(--radius-md); color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; }
.recovery-back:hover, .recovery-close:hover { color: var(--color-primary); border-color: var(--color-primary); }
.recovery-eyebrow { margin: 0 0 3px; color: var(--color-text-tertiary); font-size: .75rem; letter-spacing: .08em; }
.recovery-header h2, .recovery-card h3 { margin: 0; }
.recovery-card { margin-bottom: var(--spacing-md); padding: var(--spacing-lg); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-bg-secondary); }
.recovery-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--spacing-sm); margin-top: var(--spacing-md); }
.recovery-stats div { display: grid; gap: 4px; padding: var(--spacing-sm); border-radius: var(--radius-md); background: var(--color-bg); }
.recovery-stats span, .backup-row span, .recovery-card p { color: var(--color-text-secondary); font-size: .85rem; line-height: 1.5; }
.recovery-card-heading { display: flex; justify-content: space-between; gap: 12px; }
.recovery-action { display: inline-flex; align-items: center; gap: 6px; margin-top: var(--spacing-md); border: 1px solid var(--color-primary); border-radius: var(--radius-md); padding: .6rem .8rem; color: var(--color-button-text); background: var(--color-primary); cursor: pointer; }
.recovery-action.secondary { margin-top: 0; border-color: var(--color-border); color: var(--color-text-secondary); background: var(--color-bg); }
.backup-list { display: grid; gap: var(--spacing-sm); margin-top: var(--spacing-md); }
.backup-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: var(--spacing-sm); border-radius: var(--radius-md); background: var(--color-bg); }
.backup-row div { display: grid; gap: 3px; min-width: 0; }
.recovery-muted { margin: var(--spacing-md) 0 0; }
.recovery-close { width: 100%; margin-top: var(--spacing-sm); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: .7rem 1rem; color: var(--color-text-secondary); background: var(--color-bg-secondary); cursor: pointer; }
@media (max-width: 680px) { .recovery-stats { grid-template-columns: 1fr; } .backup-row { align-items: flex-start; flex-direction: column; } }
</style>
