<script setup lang="ts">
import { DropdownMenuRoot, DropdownMenuTrigger, DropdownMenuPortal, DropdownMenuContent, DropdownMenuItem } from 'reka-ui'
import Icon from './Icon.vue'
import UiButton from './UiButton.vue'
import { t } from '../i18n'
defineProps<{ items: Array<{ label: string; icon?: string; danger?: boolean; action: () => unknown }> }>()
</script>
<template>
  <DropdownMenuRoot>
    <DropdownMenuTrigger as-child><UiButton variant="ghost" icon :aria-label="t('common.actions')"><Icon name="more" /></UiButton></DropdownMenuTrigger>
    <DropdownMenuPortal><DropdownMenuContent class="menu-content" :side-offset="5" align="end">
      <DropdownMenuItem v-for="item in items" :key="item.label" class="menu-item" :class="{ danger: item.danger }" @select="item.action">
        <Icon v-if="item.icon" :name="item.icon" :size="16" />{{ item.label }}
      </DropdownMenuItem>
    </DropdownMenuContent></DropdownMenuPortal>
  </DropdownMenuRoot>
</template>

