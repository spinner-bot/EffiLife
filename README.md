# EffLife - 浪兮效率工具集

一站式个人效率管理工具集，涵盖时间记录、计划管理与任务追踪三大场景。

## 当前统一工作台

### 当前启动与发布边界

- `launcher/start.bat`、`launcher/start.sh` 和 `python launcher/start.py` 仅用于开发、测试、迁移与回归；正式版本应使用 Tauri 安装包。
- 发布前可执行 `python launcher/start.py --release-check`，该命令只读检查版本、sidecar、发布矩阵和安装包校验链路。
- 当前桌面发布矩阵包含 Windows NSIS、Linux DEB、Linux AppImage 与 macOS DMG。
- 桌面正式包由 Tauri 托管 Plan Helper sidecar；移动端不依赖 Python localhost 服务，使用本地计划快照能力。

项目正在由三个历史模块演进为一个统一的个人时间管理工具。推荐使用统一启动器：

```bash
# Windows
launcher\\start.bat

# Python 直接启动（Windows / POSIX）
python launcher/start.py --unified
```

> 当前 launcher 脚本仅用于开发、测试、迁移与回归验证。正式版本使用 Tauri 安装包启动，不要求用户单独安装 Python 或手动运行 plan-helper。

统一工作台由 `time-helper/desk` 提供应用壳和主题系统，融合以下能力：

- 计划中心：事件计划、分组与嵌套任务组、任务编辑、进展记录和归档恢复
- 待办中心：分类、优先级计算、截止日期、重复任务、子任务、用时记录和计划关联
- 时间记录：历史时间记录、统计、打卡及原有高级主题、音频和动效能力
- 统一数据：`.efl` 存档导入导出，覆盖配置、计划、待办、分类和时间记录
- 基础国际化：中文和 English，主题元数据与核心导航可切换

统一开发前端默认使用 `http://127.0.0.1:1420`，plan-helper companion API 使用 `http://127.0.0.1:8765`。旧 to-dos Web 兼容入口使用 `http://127.0.0.1:1421`，仅用于迁移和调试。

## 当前模块架构

```
EffLife/
├── time-helper/desk/    # 统一工作台：Vue 3 + Tauri，正式产品前端
├── plan-helper/         # 计划领域模型与 HTTP companion/sidecar
├── to-dos/              # 待办领域模型、优先级算法与兼容入口
├── common/              # Python 跨模块适配、事件与数据交换层
├── launcher/            # 开发/测试启动器，不属于正式产品入口
├── tests/               # 集成测试与发布前静态门禁
└── docs/                # 设计方案、需求与进展报告
```

三个领域通过 `time-helper/desk` 的统一服务层和 `.efl` 存档协议协同工作；`common/` 保留给 Python 侧适配与迁移场景。正式桌面版由 Tauri 管理 Plan Helper sidecar，开发阶段才使用 `launcher/`。详见 [集成文档](docs/INTEGRATION.md)。

---

## time-helper / 时间助手

核心时间记录模块，支持多类别时间追踪、历史记录、连续打卡与事件预警。

**实现版本**

| 目录 | 技术栈 | 说明 |
|------|--------|------|
| `time-helper/python/` | Python 3 + Tkinter | 原生桌面版，单文件实现 |
| `time-helper/desk/` | Vue 3 + Tauri (Rust) | 桌面版，支持主题、音频、动效系统 |
| `time-helper/desk/` | Vue 3 + Tauri Mobile candidate | 复用统一前端的移动端适配链路（待 Android/iOS 真机验收） |

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

## plan-helper / 计划助手（领域服务）

计划制定与事件编排领域服务，支持事件计划、嵌套任务组、进展记录、归档和原始快照保真。

**技术栈**: Python 3 领域服务 + Vue 3/TypeScript 统一工作台适配层

**功能概览**

- 原始 `plan` 数据结构的兼容读写
- Section、任务和可嵌套任务组
- 计划进展记录、软删除槽位与归档恢复
- 与统一待办中心的任务关联和完成状态同步
- 桌面端由 Tauri sidecar 托管；移动端使用本地快照适配层

旧版周期规则与日计划模板仍保留在 `time-helper` 的兼容界面中，不是统一事件计划工作台的主数据源。

---

## to-dos / 待办事项

轻量任务清单模块，专注于待办追踪与完成度管理。

**技术栈**: Python 领域模型 + Vue 兼容入口；统一工作台使用 Vue 3 + TypeScript

**功能概览**

- 任务创建、编辑、删除
- 优先级与截止日期设置
- 完成状态追踪
- 与计划模块协同，关联每日任务

---

## 数据与存档

统一工作台以浏览器 IndexedDB（桌面正式版使用应用数据目录）保存运行时数据，并通过 `.efl` ZIP 存档统一交换。存档覆盖配置、时间计划、记录、待办、分类、待办设置及 plan-helper 原始快照。旧 Python 模块仍使用兼容的 JSON 数据目录：

```
data/（兼容运行时目录）
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

## 跨模块集成与正式交付边界

`common/` 提供三个模块的集成层，实现：

- **统一 API 网关**: 跨模块查询（计划详情+待办+时间记录）
- **事件总线**: 自动化联动（计划创建→生成待办，待办完成→记录时间）
- **跨模块引用**: 数据关联追踪（todo→plan, time→todo）
- **统一身份认证**: 本地用户系统，三模块共享
- **统一数据模型**: 领域字段兼容与 `.efl` 存档协议

当前工作台已经是开发集成版，但正式安装包和多端真机验收仍未完成。`launcher/start.py` 仅用于开发、测试、迁移和回归；Windows NSIS、Linux、macOS 的 Tauri 构建链已配置，需在具备 Rust/Cargo 的发布环境完成最终编译、安装和数据迁移验收。

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
| time-helper | 1.6.1 | 时间记录与统一工作台 |
| plan-helper | 0.3.0 | 计划制定与日程管理 |
| to-dos | 0.4.0 | 任务清单与待办追踪 |
| common | 1.0.0 | 跨模块集成层 |

版本号格式：`主版本.次版本.修订号`
- 主版本：重大更新，不兼容的改动
- 次版本：新增功能，向下兼容
- 修订号：问题修复，向下兼容
