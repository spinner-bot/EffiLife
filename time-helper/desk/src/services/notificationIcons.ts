import {
  BellRing,
  CalendarClock,
  CheckCircle2,
  FileText,
  Inbox,
  Trophy,
  type LucideIcon,
} from 'lucide-vue-next'

/** Map legacy event types to theme-aware icons without rendering stored emoji strings. */
export function getNotificationIcon(type?: string): LucideIcon {
  switch (type) {
    case 'plan_complete_100':
    case 'achievement_unlocked':
    case 'checkin_complete':
    case 'streak_milestone':
      return Trophy
    case 'plan_complete_90':
    case 'plan_complete_50':
      return CheckCircle2
    case 'record_added':
    case 'record_deleted':
    case 'daily_first_record':
      return FileText
    case 'plan_changed':
    case 'weekly_summary':
      return CalendarClock
    case 'progress_warning':
    case 'idle_reminder':
    case 'reminder':
      return BellRing
    default:
      return Inbox
  }
}
