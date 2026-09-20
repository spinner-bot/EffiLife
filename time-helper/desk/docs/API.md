# time-helper API 文档

> time-helper 模块的统一对外接口层，供 plan-helper / to-dos 等外部模块调用。

## 快速开始

```ts
import { TimeHelperApi } from '@/api'

// 获取今日摘要
const summary = await TimeHelperApi.analytics.getSummary()
console.log(summary.data?.todayProgress) // 今日完成度
```

## 统一响应格式

所有 API 返回 `ApiResponse<T>`：

```ts
interface ApiResponse<T> {
  success: boolean
  data?: T          // 成功时包含数据
  error?: string    // 失败时包含错误信息
  timestamp: string // ISO 时间戳
}
```

---

## 1. ConfigApi — 配置管理

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `getConfig()` | - | `Config` | 获取当前配置 |
| `saveConfig(config)` | `Config` | `void` | 保存完整配置 |
| `patchConfig(patch)` | `Partial<Config>` | `Config` | 更新部分配置 |
| `resetConfig()` | - | `Config` | 重置为默认配置 |

---

## 2. PlanApi — 计划管理

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `getPlans()` | - | `Plans` | 获取所有计划 |
| `savePlans(plans)` | `Plans` | `void` | 保存所有计划 |
| `getPlan(name)` | `string` | `Plans[string] \| null` | 获取指定计划 |
| `upsertPlan(name, plan)` | `string, Plans[string]` | `void` | 添加/更新计划 |
| `deletePlan(name)` | `string` | `void` | 删除计划 |
| `getTodayPlan()` | - | `DayPlanInfo` | 获取今日计划 |
| `getDayPlan(date)` | `string` | `DayPlanInfo` | 获取指定日期计划 |
| `setDayPlan(planName, date?)` | `string, string?` | `void` | 设置日计划 |
| `getScheduleRules()` | - | `ScheduleRule[]` | 获取日程规则 |
| `saveScheduleRules(rules)` | `ScheduleRule[]` | `void` | 保存日程规则 |

---

## 3. RecordApi — 时间记录

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `getRecords(date?)` | `string?` | `TimeRecord[]` | 获取记录（默认今天） |
| `addRecord(record)` | `TimeRecord` | `void` | 添加记录 |
| `deleteRecord(index, date?)` | `number, string?` | `void` | 删除记录 |
| `updateRecord(index, record, date?)` | `number, TimeRecord, string?` | `void` | 更新记录 |
| `getRecordsInRange(start, end)` | `string, string` | `Record<string, TimeRecord[]>` | 范围查询 |
| `getRealTimeStat(date?)` | `string?` | `RealTimeStat` | 实时统计 |
| `getStatsSummary(start, end)` | `string, string` | `{ dates, progress, totalHours, planNames }` | 统计摘要 |

---

## 4. CheckinApi — 打卡系统

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `getCheckinData()` | - | `CheckinData` | 完整打卡数据 |
| `getCurrentStreak()` | - | `number` | 当前连续天数 |
| `getLongestStreak()` | - | `number` | 最长连续天数 |
| `getTotalCheckins()` | - | `number` | 累计打卡数 |
| `hasCheckedInToday()` | - | `boolean` | 今日是否已打卡 |
| `checkin(planName, progress?)` | `string, number?` | `number \| null` | 执行打卡 |
| `checkinForDate(date, planName, progress?)` | `string, string, number?` | `number \| null` | 补打卡 |
| `getCheckinRecords()` | - | `CheckinRecord[]` | 打卡记录列表 |
| `getCheckinStatus(date)` | `string` | `{ checkedIn, planName? }` | 日期打卡状态 |
| `getCheckinsInRange(start, end)` | `string, string` | `CheckinRecord[]` | 范围打卡记录 |
| `reset()` | - | `void` | 重置（调试用） |

---

## 5. EventApi — 事件/收件箱

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `getSettings()` | - | `EventSettings` | 事件设置 |
| `updateSettings(patch)` | `Partial<EventSettings>` | `void` | 更新设置 |
| `getInbox()` | - | `InboxEntry[]` | 收件箱条目 |
| `getUnreadCount()` | - | `number` | 未读数量 |
| `markAsRead(entryId)` | `string` | `void` | 标记已读 |
| `markAllAsRead()` | - | `void` | 全部标记已读 |
| `deleteInboxEntry(entryId)` | `string` | `void` | 删除条目 |
| `clearInbox()` | - | `void` | 清空收件箱 |
| `getWarningRules()` | - | `WarningRule[]` | 预警规则 |
| `addWarningRule(rule)` | `Omit<WarningRule, 'id'>` | `string` | 添加规则 |
| `updateWarningRule(id, updates)` | `string, Partial<WarningRule>` | `void` | 更新规则 |
| `deleteWarningRule(id)` | `string` | `void` | 删除规则 |
| `triggerEvent(type, title, message, data?)` | `string, string, string, any?` | `void` | 手动触发事件 |

---

## 6. AnalyticsApi — 数据分析

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `getWeeklyReport(weekStart?)` | `string?` | `WeeklyReport` | 周报 |
| `getMonthlyTrend(year, month)` | `number, number` | `MonthlyTrend` | 月度趋势 |
| `getSummary()` | - | `Summary` | 综合摘要 |

### WeeklyReport 结构

```ts
{
  period: { start: string; end: string }
  totalRecords: number
  totalHours: number
  avgProgress: number
  checkinDays: number
  topTags: Array<{ tag: string; hours: number }>
  dailyProgress: Array<{ date: string; progress: number }>
}
```

### MonthlyTrend 结构

```ts
{
  dailyProgress: number[]
  dailyHours: number[]
  totalHours: number
  avgProgress: number
  checkinCount: number
}
```

### Summary 结构

```ts
{
  todayProgress: number
  todayPlanName: string
  currentStreak: number
  totalCheckins: number
  unreadEvents: number
  todayRecords: number
}
```

---

## 7. UtilsApi — 工具函数

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `hoursToHm(hours)` | `number` | `string` | 小时转可读格式 |
| `getTodayDate()` | - | `string` | 今天日期 YYYY-MM-DD |
| `addDays(dateStr, days)` | `string, number` | `string` | 日期加减 |
| `formatTimeRange(start, end)` | `string, string` | `string` | 格式化时间范围 |

---

## 模块间通信示例

### plan-helper 获取今日进度

```ts
import { TimeHelperApi } from 'time-helper/api'

async function showTodayProgress() {
  const res = await TimeHelperApi.analytics.getSummary()
  if (res.success && res.data) {
    return `${res.data.todayPlanName}: ${res.data.todayProgress}%`
  }
}
```

### to-dos 检查打卡状态

```ts
import { TimeHelperApi } from 'time-helper/api'

function canShowCheckinReminder() {
  const res = TimeHelperApi.checkin.hasCheckedInToday()
  return res.success && !res.data  // 今天未打卡时提醒
}
```

---

## 文件位置

```
src/api/index.ts       # API 统一入口
src/types/index.ts     # 数据类型定义
src/audio/EventSystem.ts  # 事件系统
src/data/CheckinSystem.ts # 打卡系统
src/services/dataService.ts # 数据服务
```
