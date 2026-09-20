# EffiLife 跨模块集成文档

> 版本: 1.0.0 | 更新日期: 2026-09-20

## 概述

EffiLife 集成层（`common/`）提供三个模块（time-helper、plan-helper、to-dos）之间的协同工作能力。通过统一的数据格式、API 网关、事件系统和身份认证，实现跨模块数据流和自动化联动。

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                   EffiLife Integration                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────┐   │
│  │ time-    │   │ plan-    │   │ to-dos           │   │
│  │ helper   │   │ helper   │   │                  │   │
│  │ v1.2.0   │   │ v0.3.0   │   │ v0.4.0           │   │
│  └────┬─────┘   └────┬─────┘   └────┬─────────────┘   │
│       │               │               │                  │
│  ─────┴───────────────┴───────────────┴──────────────    │
│       │        API Gateway (统一入口)      │              │
│  ─────┴───────────────┬───────────────┴──────────────    │
│                       │                                   │
│  ┌────────────────────┴────────────────────────────┐    │
│  │              事件总线 (EventBus)                  │    │
│  │  plan.created → auto-create todos                │    │
│  │  todo.completed → auto-record time               │    │
│  │  time.record → update todo time_spent            │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ DataManager  │  │ AuthManager  │  │  Schemas     │  │
│  │ 跨模块引用   │  │ 统一身份认证 │  │  统一数据格式 │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ───────────────── common/data/ ──────────────────────  │
│  user/ cross_refs/ events/ backups/ modules/            │
└─────────────────────────────────────────────────────────┘
```

## 目录结构

```
common/
├── __init__.py              # 包入口
├── VERSION                  # 集成层版本 (1.0.0)
├── bootstrap.py             # 集成启动器
├── data_manager.py          # 统一数据管理器
├── event_bus.py             # 事件总线
├── schemas/                 # 统一数据模型
│   ├── __init__.py
│   ├── core.py              # 核心类型（CrossReference, UnifiedTimestamp）
│   └── models.py            # 统一模型（UnifiedPlan/Todo/TimeRecord/User）
├── api_gateway/             # API 网关
│   ├── __init__.py
│   ├── gateway.py           # 网关核心
│   └── adapters.py          # 模块适配器
├── events/                  # 事件处理器
│   ├── __init__.py
│   ├── plan_todo.py         # Plan-Todo 联动
│   ├── todo_time.py         # Todo-Time 联动
│   ├── stats_correlation.py # 统计关联
│   └── registry.py          # 处理器注册
├── auth/                    # 身份认证
│   ├── __init__.py
│   └── manager.py           # 用户管理
└── data/                    # 共享数据目录
    ├── user/                # 用户数据
    ├── cross_refs/          # 跨模块引用
    ├── events/              # 事件日志
    ├── backups/             # 全局备份
    └── modules/             # 模块目录注册
```

## 快速开始

### 1. 初始化集成系统

```python
from common.bootstrap import EffiLifeIntegration

integration = EffiLifeIntegration()
integration.initialize()
```

### 2. 注册模块 API

```python
# 注册 to-dos
from to-dos.src.api import TodoAPI
todo_api = TodoAPI()
integration.register_todo_api(todo_api)

# 注册 plan-helper
# (通过其 API 模块)
integration.register_plan_api(plan_api)

# 注册 time-helper
# (通过其 DataCore)
integration.register_time_api(time_api)
```

### 3. 使用 API 网关

```python
# 调用模块方法
result = integration.gateway.call('to-dos', 'list_todos', status='pending')

# 跨模块查询：获取计划的所有待办
result = integration.gateway.query_plan_todos(plan_id='1')

# 每日总结
result = integration.gateway.query_daily_summary('2026-09-20')

# 用户仪表盘
result = integration.gateway.query_user_dashboard()
```

### 4. 发布事件

```python
from common.event_bus import EventType

integration.emit_event(
    event_type=EventType.TODO_COMPLETED.value,
    source_module='to-dos',
    data={'todo_id': 'TODO-001', 'time_spent': 25},
)
```

## 统一数据模型

### UnifiedTodo

```json
{
  "id": "TODO-20260920-0001",
  "title": "完成任务",
  "priority": "important",
  "status": "pending",
  "related_plan_id": "1",
  "time_estimate": 30,
  "time_spent": 25,
  "schema_version": "1.0.0"
}
```

### UnifiedPlan

```json
{
  "id": "1",
  "name": "工作计划",
  "module": "plan-helper",
  "plan_type": "standard",
  "total_tasks": 5,
  "completed_tasks": 2,
  "progress_percentage": 40.0,
  "schema_version": "1.0.0"
}
```

### UnifiedTimeRecord

```json
{
  "id": "TR-20260920-0800",
  "date": "2026-09-20",
  "start_time": "08:00",
  "end_time": "09:00",
  "duration_hours": 1.0,
  "content": "编写代码",
  "tag": "工作",
  "related_todo_id": "TODO-001",
  "schema_version": "1.0.0"
}
```

## 跨模块引用

通过 `DataManager` 管理模块之间的关联关系：

```python
from common.data_manager import DataManager

dm = DataManager.get_instance()

# 创建关联
dm.link_entities(
    source_module='to-dos',
    source_id='TODO-001',
    target_module='plan-helper',
    target_id='1',
    relation_type='belongs_to',
)

# 查询关联
todo_ids = dm.find_linked_ids('1', 'to-dos')  # 查找计划下的待办
```

### 引用类型

| relation_type | 含义 | 示例 |
|---|---|---|
| `belongs_to` | 属于 | todo → plan |
| `tracks` | 追踪 | time_record → todo |
| `generates` | 生成 | plan → todo (auto) |

## 事件系统

### 事件类型

| 事件 | 说明 | 触发器 |
|---|---|---|
| `plan.created` | 计划创建 | plan-helper |
| `plan.task_added` | 任务添加 | plan-helper |
| `plan.task_completed` | 任务完成 | plan-helper |
| `todo.created` | 待办创建 | to-dos |
| `todo.completed` | 待办完成 | to-dos |
| `time.record_created` | 时间记录创建 | time-helper |

### 自动联动

| 触发事件 | 自动动作 |
|---|---|
| `plan.created` + `auto_create_todos` | 为每个任务创建关联待办 |
| `plan.task_added` + `auto_todo` | 创建关联待办 |
| `todo.completed` | 在 time-helper 记录时间 |
| `time.record_created` | 更新待办的 time_spent |

### 订阅事件

```python
from common.event_bus import EventBus, EventType

eb = EventBus.get_instance()

def on_todo_completed(event):
    print(f"Todo completed: {event.data.get('todo_id')}")

eb.subscribe(EventType.TODO_COMPLETED.value, on_todo_completed)
```

## 身份认证

```python
from common.auth import AuthManager

auth = AuthManager.get_instance()

# 注册
auth.register('username', 'password', '显示名称')

# 登录
result = auth.login('username', 'password')

# 获取当前用户
user = auth.get_current_user()

# 登出
auth.logout()
```

## API 网关路由

### 直接调用

```python
gateway.call(module, method, **kwargs)
```

### 跨模块查询

| 路径 | 说明 |
|---|---|
| `/api/integration/plan-detail/{id}` | 计划完整信息 |
| `/api/integration/plan-todos/{id}` | 计划关联待办 |
| `/api/integration/todo-time/{id}` | 待办时间统计 |
| `/api/integration/daily-summary/{date}` | 每日总结 |
| `/api/integration/user-dashboard` | 用户仪表盘 |
| `/api/integration/stats` | 全部统计 |

## 测试

```bash
# 运行集成测试
python tests/test_integration.py

# 55 个测试用例，覆盖：
# - Schema 模型序列化
# - DataManager 引用管理
# - EventBus 发布订阅
# - AuthManager 用户管理
# - TodoAPI 基础功能
# - 完整集成流程
# - 跨模块引用链
# - API 网关路由
```

## 版本兼容

| 模块 | 版本 | 变更 |
|---|---|---|
| time-helper | 1.1.0 → 1.2.0 | 增加集成接口 |
| plan-helper | 0.2.0 → 0.3.0 | 增加集成接口 |
| to-dos | 0.3.0 → 0.4.0 | 增加集成接口 |
| common | 新增 1.0.0 | 集成层 |

## 设计原则

1. **非侵入性**: 各模块保留原有数据结构和 API，集成层通过适配器桥接
2. **松耦合**: 通过事件系统通信，模块不直接依赖其他模块
3. **可扩展**: 新增模块只需注册到网关，无需修改现有代码
4. **向后兼容**: 不修改现有模块的功能和数据格式
