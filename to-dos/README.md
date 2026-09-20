# to-dos / 待办事项

EffLife 效率工具集的轻量任务清单模块，专注于待办追踪与完成度管理。

## 功能

### 核心功能
- 待办事项 CRUD（创建、读取、更新、删除/归档）
- 四级优先级：紧急且重要 / 重要 / 紧急 / 普通
- 五种状态：待处理 / 进行中 / 已完成 / 已归档 / 已取消
- 子任务管理（带进度条）
- 分类系统（颜色 + 图标）
- 标签系统（支持多标签筛选）
- 时间预估与实际花费记录
- 截止日期与逾期提醒（可配置提前 N 天警告）
- 重复任务（每日/每周/每月）
- 备注/笔记（支持 Markdown）
- 置顶功能

### 查询与统计
- 全文搜索（标题 + 描述 + 标签 + 备注）
- 搜索高亮匹配文字
- 统计面板（完成率、按分类/优先级统计）
- 逾期待办 + 今日待办 + 即将到期
- 按状态/优先级/分类/标签筛选
- 多种排序：创建时间/截止日期/优先级/自定义
- 批量操作（选择 + 批量完成/删除）

### 数据管理
- 数据导出：JSON / CSV 格式
- 数据导入：JSON 合并/替换模式
- 自动备份（带数量限制）
- localStorage 持久化

### 界面
- 命令行交互界面（CLI）
- Vue 3 现代 Web 界面
- 深色模式支持（自动/浅色/深色）
- 流畅过渡动画（列表增删、状态切换）
- 精致卡片设计（多层阴影、悬浮效果）
- 友好空状态设计

### 跨模块联动
- 与 plan-helper 联动：关联计划 ID
- 与 time-helper 联动：记录任务耗时

## 快速开始

### 命令行界面

```bash
cd to-dos
python main.py          # 交互模式
```

交互模式命令：
```
list [status]     - 列出待办 (all/pending/progress/done/archived)
add <标题>        - 添加待办
done <id>         - 完成待办
cancel <id>       - 取消待办
rm <id>           - 删除(归档)待办
show <id>         - 显示详情
overdue           - 显示逾期
today             - 显示今日待办
stats             - 统计信息
cats              - 列出分类
search <关键词>   - 搜索
sub <id> <标题>   - 添加子任务
help              - 显示帮助
q                 - 退出
```

### Web 界面

```bash
cd to-dos/ui
npm install
npm run dev
```

访问 `http://localhost:1421`

**快捷键：**
- `N` - 新建待办
- `/` - 聚焦搜索框
- `↑` / `↓` - 导航待办列表
- `Enter` - 编辑当前聚焦的待办
- `Space` - 切换当前待办完成状态
- `Ctrl+D` - 切换深色/浅色主题
- `Ctrl+E` - 导出 JSON 数据
- `Ctrl+I` - 打开导入面板
- `Esc` - 关闭弹窗/取消操作

## 作为库使用

```python
from src import TodoAPI

api = TodoAPI()

# 创建待办
result = api.create_todo(
    title="写报告",
    priority="important",
    category="work",
    deadline="2026-09-25T18:00:00"
)
todo_id = result["data"]["id"]

# 添加子任务
api.add_subtask(todo_id, "收集资料")

# 完成待办
api.complete_todo(todo_id, time_spent=60)

# 统计
stats = api.get_stats()
print(f"完成率: {stats['data']['completion_rate']}%")
```

## 数据结构

### Todo 核心字段

```python
{
    "id": "TODO-20260920-0001",     # 唯一编号
    "title": "完成任务",
    "priority": "urgent-important",  # 优先级
    "status": "pending",             # 状态
    "category": "work",              # 分类
    "deadline": "2026-09-25T18:00:00",
    "tags": ["紧急", "项目"],
    "subtasks": [...],
    "time_estimate": 120,            # 预估分钟
    "time_spent": 60,                # 实际分钟
    "recurrence": "none",            # 重复 (none/daily/weekly/monthly)
    "deadline_warning_days": 3,      # 提前几天警告
    "sort_order": 0,                 # 自定义排序
    "pinned": false,                 # 是否置顶
    "notes": "Markdown 笔记..."      # 备注
}
```

### 优先级
- `urgent-important` - 紧急且重要 🔴
- `important` - 重要 🟠
- `urgent` - 紧急 🟡
- `normal` - 普通 ⚪

### 状态
- `pending` - 待处理
- `in-progress` - 进行中
- `completed` - 已完成
- `archived` - 已归档
- `cancelled` - 已取消

## 技术栈

### 后端
- **Python 3** - dataclasses + JSON 存储
- 无第三方依赖

### 前端
- **Vue 3** - Composition API
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式系统
- **Pinia** - 状态管理
- **Vite** - 构建工具
- **Lucide Vue Next** - 图标库

## 数据存储

所有数据存储在 `data/` 目录：

```
data/
├── todos.json       # 所有待办事项
├── categories.json  # 分类配置
└── archive/         # 归档目录
    └── YYYY-MM/     # 按月归档
        └── todos.json
```

## 界面设计

参考 **Linear** 和 **Notion** 的设计语言：
- 极简、克制、信息密度高
- 清晰的层级和留白
- 支持亮色/暗色主题
- 键盘友好交互

详细设计方案见 [docs/UI_DESIGN.md](docs/UI_DESIGN.md)

## API 文档

完整的 API 规范见 [docs/API_SPEC.md](docs/API_SPEC.md)

## 版本

当前版本：**0.3.0**（见 `VERSION`）

## 开发计划

- [x] 核心数据模型和 API
- [x] 命令行界面
- [x] Vue 前端基础框架
- [x] 主要 UI 组件
- [x] 过渡动画系统
- [x] 深色模式支持
- [x] 数据导入/导出（JSON/CSV）
- [x] 自动备份机制
- [x] 排序系统
- [x] 标签筛选
- [x] 批量操作
- [x] 重复任务
- [x] 备注/笔记 (Markdown)
- [x] 截止日期提醒
- [ ] 与 plan-helper 深度集成
- [ ] 与 time-helper 时间追踪集成
- [ ] 拖拽排序（UI 组件）
- [ ] 桌面端适配（Tauri）

## 许可证

EffLife 项目的一部分
