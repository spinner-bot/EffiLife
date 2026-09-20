# to-dos API 规范

## 数据结构定义

### Todo 核心结构

```typescript
interface Todo {
  id: string;              // 唯一标识符，格式：TODO-YYYYMMDD-XXXX（4位序号）
  title: string;           // 任务标题
  description?: string;    // 任务详细描述
  created_at: string;      // 创建时间，ISO 8601 格式
  updated_at: string;      // 最后更新时间
  deadline?: string;       // 截止日期，ISO 8601 格式
  priority: Priority;      // 优先级
  category: string;        // 分类标签
  status: TodoStatus;      // 状态
  completed_at?: string;   // 完成时间
  tags: string[];          // 自定义标签
  subtasks: Subtask[];     // 子任务列表
  related_plan_id?: string; // 关联的 plan-helper 计划 ID
  time_estimate?: number;  // 预估时间（分钟）
  time_spent?: number;     // 实际花费时间（分钟）
  notes?: string;          // 备注
}

interface Subtask {
  id: string;
  title: string;
  completed: boolean;
  completed_at?: string;
}

type Priority = 'urgent-important' | 'important' | 'urgent' | 'normal';
type TodoStatus = 'pending' | 'in-progress' | 'completed' | 'archived' | 'cancelled';
```

### 分类系统

```typescript
interface Category {
  id: string;
  name: string;
  color: string;        // HEX 颜色
  icon: string;         // Lucide 图标名
  description?: string;
  created_at: string;
}
```

## API 端点设计

### 1. Todo 基础操作

#### GET /api/todos
获取所有待办事项

**查询参数：**
- `status`: 状态过滤（pending/in-progress/completed/archived）
- `priority`: 优先级过滤
- `category`: 分类过滤
- `date_from`: 创建时间起始
- `date_to`: 创建时间截止
- `search`: 搜索关键词

**响应：**
```json
{
  "success": true,
  "data": [Todo],
  "total": 100,
  "page": 1,
  "page_size": 50
}
```

#### POST /api/todos
创建新待办事项

**请求体：**
```json
{
  "title": "完成项目文档",
  "description": "编写 API 文档和用户手册",
  "deadline": "2026-09-25T18:00:00Z",
  "priority": "urgent-important",
  "category": "work",
  "tags": ["文档", "紧急"],
  "time_estimate": 120
}
```

**响应：**
```json
{
  "success": true,
  "data": Todo,
  "message": "待办创建成功"
}
```

#### GET /api/todos/:id
获取单个待办详情

**响应：**
```json
{
  "success": true,
  "data": Todo
}
```

#### PUT /api/todos/:id
更新待办事项

**请求体：** 同 POST，可部分更新

#### DELETE /api/todos/:id
删除待办事项（软删除，移至归档）

#### POST /api/todos/:id/complete
标记为完成

**请求体：**
```json
{
  "time_spent": 90  // 实际花费时间（分钟）
}
```

#### POST /api/todos/:id/cancel
标记为取消

### 2. 子任务操作

#### POST /api/todos/:id/subtasks
添加子任务

**请求体：**
```json
{
  "title": "编写目录结构"
}
```

#### PUT /api/todos/:id/subtasks/:subtaskId
更新子任务

#### DELETE /api/todos/:id/subtasks/:subtaskId
删除子任务

#### POST /api/todos/:id/subtasks/:subtaskId/toggle
切换子任务完成状态

### 3. 分类管理

#### GET /api/categories
获取所有分类

**响应：**
```json
{
  "success": true,
  "data": [Category]
}
```

#### POST /api/categories
创建分类

**请求体：**
```json
{
  "name": "工作",
  "color": "#6366f1",
  "icon": "briefcase",
  "description": "工作任务"
}
```

#### PUT /api/categories/:id
更新分类

#### DELETE /api/categories/:id
删除分类（会提示用户重新分配或删除该分类下的 todos）

### 4. 统计与查询

#### GET /api/todos/stats
获取统计信息

**响应：**
```json
{
  "success": true,
  "data": {
    "total": 100,
    "pending": 30,
    "in_progress": 20,
    "completed": 45,
    "archived": 5,
    "by_priority": {
      "urgent-important": 10,
      "important": 20,
      "urgent": 15,
      "normal": 55
    },
    "by_category": {
      "work": 40,
      "study": 30,
      "life": 30
    },
    "completion_rate": 67.5,
    "avg_completion_time": 180
  }
}
```

#### GET /api/todos/overdue
获取逾期待办

**响应：**
```json
{
  "success": true,
  "data": [Todo]
}
```

#### GET /api/todos/today
获取今日待办

**响应：**
```json
{
  "success": true,
  "data": [Todo]
}
```

### 5. 批量操作

#### POST /api/todos/batch
批量操作

**请求体：**
```json
{
  "action": "complete" | "cancel" | "archive" | "delete",
  "ids": ["TODO-20260920-0001", "TODO-20260920-0002"]
}
```

### 6. 导入导出

#### POST /api/todos/export
导出待办数据

**请求体：**
```json
{
  "format": "json" | "csv",
  "filters": {
    "status": ["completed"],
    "date_from": "2026-01-01"
  }
}
```

**响应：** 文件下载

#### POST /api/todos/import
导入待办数据

**请求体：** FormData，包含文件

## 跨模块接口

### 与 plan-helper 联动

#### GET /api/integration/plans/:planId/todos
获取关联到指定计划的 todos

#### POST /api/integration/plans/:planId/todos
为计划创建关联 todo

### 与 time-helper 联动

#### POST /api/integration/time-tracking
记录时间到指定 todo

**请求体：**
```json
{
  "todo_id": "TODO-20260920-0001",
  "start_time": "2026-09-20T14:00:00Z",
  "end_time": "2026-09-20T15:30:00Z",
  "duration": 90
}
```

## 错误码规范

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权（预留） |
| 403 | 禁止访问（预留） |
| 404 | 资源不存在 |
| 409 | 冲突（如重复创建） |
| 500 | 服务器内部错误 |

## 数据存储

所有数据存储在 `data/todos/` 目录：

```
data/todos/
├── todos.json           # 所有待办事项
├── categories.json      # 分类配置
└── archive/             # 归档目录
    └── YYYY-MM/         # 按月归档
        └── todos.json
```
