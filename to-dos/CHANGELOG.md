# to-dos - 更新日志

## [0.2.0] - 2026-09-20

### 新增
- Vue 3 前端界面：
  - 主视图（看板布局）
  - 分类侧栏组件（CategorySidebar）
  - 待办列表组件（TodoList）
  - 待办卡片组件（TodoItem）
  - 新建/编辑表单弹窗（TodoForm）
  - 筛选栏组件（FilterBar）
- TypeScript 类型定义
- Pinia 状态管理
- Tailwind CSS 样式系统
- Vite 构建配置
- 键盘快捷键支持（N 新建、Esc 关闭）

### 技术栈
- 前端：Vue 3 + TypeScript + Tailwind CSS + Pinia
- 图标：Lucide Vue Next
- 构建：Vite 6

## [0.1.0] - 2026-09-20

### 新增
- 核心数据模型：Todo、Subtask、Category（dataclass 实现）
- 优先级系统：urgent-important / important / urgent / normal
- 状态系统：pending / in-progress / completed / archived / cancelled
- 完整 CRUD API（TodoStorage 存储层 + TodoAPI 服务层）
- 子任务管理：添加、切换完成状态、删除
- 分类管理：创建、更新、删除（删除时自动迁移至默认分类）
- 搜索功能：按标题、描述、标签全文搜索
- 统计接口：按状态、优先级、分类统计，计算完成率
- 逾期待办查询
- 今日待办查询
- 批量操作（complete / cancel / archive / delete）
- 跨模块接口（预留）：
  - 与 plan-helper 联动：按计划查询/创建关联待办
  - 与 time-helper 联动：记录任务耗时
- 命令行交互界面（CLI）
- 统一 API 响应格式：`{success, data, message}`
- ID 生成器：TODO-YYYYMMDD-XXXX 格式
- 时间工具：相对时间显示、截止日期状态判断
- 数据持久化：JSON 文件存储，按月归档
- 36 项 API 自动化测试全部通过
- API 规范文档（docs/API_SPEC.md）
- 设计文档（docs/设计文档.md）
