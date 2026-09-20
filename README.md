# EffLife - 浪兮效率工具集

一站式个人效率管理工具集，涵盖时间记录、计划管理与任务追踪三大场景。

## 模块架构

```
EffLife/
├── time-helper/         # 时间记录与统计 (v1.2.0)
├── plan-helper/         # 计划制定与日程管理 (v0.3.0)
├── to-dos/              # 任务清单与待办追踪 (v0.4.0)
├── common/              # 跨模块集成层 (v1.0.0)
├── tests/               # 集成测试与性能基准
├── data/                # 共享数据目录
└── docs/                # 设计规范与版本管理文档
```

三个模块通过 `common/` 集成层协同工作，提供统一 API 网关、事件总线、跨模块引用和身份认证。详见 [集成文档](docs/INTEGRATION.md)。

---

## time-helper / 时间助手

核心时间记录模块，支持多类别时间追踪、日历视图、连续打卡与事件预警。

**实现版本**

| 目录 | 技术栈 | 说明 |
|------|--------|------|
| `time-helper/python/` | Python 3 + Tkinter | 原生桌面版，单文件实现 |
| `time-helper/desk/` | Vue 3 + Tauri (Rust) | 桌面版，支持主题、音频、动效系统 |
| `time-helper/android/` | Tauri Mobile (Kotlin) | 移动端适配（已搁置） |

**功能概览**

- 时间记录：快速记录各类活动时间，按类别统计
- 日历视图：直观查看历史记录与完成情况
- 计划管理：创建切分制 / 分配制日常计划
- 打卡系统：连续天数统计，支持自动补打卡
- 主题系统：12 种内置主题，动态粒子效果
- 音频系统：9 种背景音乐 + 8 种音效反馈
- 动效系统：可调帧率（30/60/90/120 FPS）
- 事件预警：进度监控与多级提醒
- 数据导入导出：`.efl` 存档格式（ZIP 压缩）

**启动方式（桌面版）**

```bash
cd time-helper/desk
npm install
npm run tauri dev
```

---

## plan-helper / 计划助手

计划制定与日程编排模块，支持周期性计划模板、日程规则配置与手动覆盖。

**技术栈**: Python 3

**功能概览**

- 工作日 / 休息日 / 自定义计划模板
- 周、月、年、月周等多维度日程规则
- 手动指定日期计划覆盖
- LLM 辅助计划生成
- 与 time-helper 联动，自动匹配当日计划

---

## to-dos / 待办事项

轻量任务清单模块，专注于待办追踪与完成度管理。

**技术栈**: 待定

**功能概览**

- 任务创建、编辑、删除
- 优先级与截止日期设置
- 完成状态追踪
- 与计划模块协同，关联每日任务

---

## 共享数据

`data/` 目录存放三个模块的运行时数据，格式统一为 JSON：

```
data/
├── config.json            # 全局配置
├── plans.json             # 计划模板
├── schedule_rules.json    # 日程规则
├── manual_plans.json      # 手动计划覆盖
└── 数据/                   # 按日期存储的记录
    └── YYYY-MM-DD/
        ├── day_plan.json
        └── records.json
```

---

## 跨模块集成

`common/` 提供三个模块的集成层，实现：

- **统一 API 网关**: 跨模块查询（计划详情+待办+时间记录）
- **事件总线**: 自动化联动（计划创建→生成待办，待办完成→记录时间）
- **跨模块引用**: 数据关联追踪（todo→plan, time→todo）
- **统一身份认证**: 本地用户系统，三模块共享
- **统一数据模型**: JSON Schema 规范化

**快速开始**

```bash
# 运行集成测试（55 个测试用例）
python tests/test_integration.py

# 运行性能基准
python tests/test_benchmark.py

# 启动集成系统
python run_integration.py stats
python run_integration.py dashboard
```

---

## 技术栈总览

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite |
| 桌面框架 | Tauri 2.x (Rust) |
| 状态管理 | Pinia |
| 样式 | Tailwind CSS |
| 图表 | Chart.js |
| Python 原生版 | Python 3 + Tkinter |
| 集成层 | Python 3 (common/) |

---

## 版本说明

| 模块 | 版本 | 说明 |
|------|------|------|
| time-helper | 1.2.0 | 时间记录与统计 |
| plan-helper | 0.3.0 | 计划制定与日程管理 |
| to-dos | 0.4.0 | 任务清单与待办追踪 |
| common | 1.0.0 | 跨模块集成层 |

版本号格式：`主版本.次版本.修订号`
- 主版本：重大更新，不兼容的改动
- 次版本：新增功能，向下兼容
- 修订号：问题修复，向下兼容
