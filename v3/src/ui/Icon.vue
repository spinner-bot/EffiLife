<script setup lang="ts">
import type { Component } from 'vue'
import { LayoutDashboard, FolderOpen, Clock3, ListTodo, Settings2, Plus, X, ArrowUpRight, Check, ChevronRight, ChevronDown, MoreHorizontal, CalendarDays, Circle, Activity, CheckCheck, NotebookPen, Trash2, Pencil, Archive, RotateCcw, Upload, Download, Palette, Languages, BookOpen, AlertCircle, CheckCircle2, Timer, Sun, Moon, Flag, Search, Tag, Pin, Repeat2, Menu, LockKeyhole, CircleHelp } from '@lucide/vue'
const props = withDefaults(defineProps<{ name: string; size?: number }>(), { size: 20 })
const icons: Record<string, Component> = {
  overview: LayoutDashboard, plans: FolderOpen, time: Clock3, todos: ListTodo, settings: Settings2,
  plus: Plus, close: X, arrow: ArrowUpRight, check: Check, next: ChevronRight, expand: ChevronDown,
  more: MoreHorizontal, calendar: CalendarDays, circle: Circle, activity: Activity, done: CheckCheck,
  log: NotebookPen, delete: Trash2, edit: Pencil, archive: Archive, restore: RotateCcw,
  upload: Upload, download: Download, theme: Palette, language: Languages, book: BookOpen,
  error: AlertCircle, success: CheckCircle2, timer: Timer, sun: Sun, moon: Moon, flag: Flag, search: Search, tag: Tag,
  pin: Pin, repeat: Repeat2, drag: Menu, lock: LockKeyhole, help: CircleHelp,
}
</script>
<template><component :is="icons[props.name] || Circle" :size="size" :stroke-width="1.7" aria-hidden="true" /></template>

