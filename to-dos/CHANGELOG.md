# to-dos - 更新日志

## [0.5.0] - 2026-09-20

### 新增 - 优先排位分算法（核心）
- **算法实现**：创建 `src/priority.py` 模块，实现完整的优先排位分计算
  - `calc_priority_score`: 计算单个待办的优先排位分
  - `format_score_display`: 格式化分数显示（EL 前缀 + 对数压缩）
  - `calc_category_score`: 计算分类分数（sum/sqrt(count)）
  - `calc_all_scores`: 批量计算所有待办分数
- **对数域计算**：全程使用对数域，避免大数溢出
- **软封顶机制**：超过 1e10 使用对数压缩显示
- **前端同步**：创建 `ui/src/utils/priority.ts`，TypeScript 版本算法与后端一致

### 新增 - 数据模型增强
- **Todo 新增字段**：
  - `priority_rank`: 优先级排位（int，0 最高）
  - `urgent`: 是否紧急（boolean）
  - `important`: 是否重要（boolean）
  - `start_time`: 开始时间（默认=创建时间）
  - `estimated_time`: 用户填写的预估时间（分钟）
- **Category 新增字段**：
  - `difficulty`: 类别难度（int，默认 5）
  - `ascii_icon`: ASCII 图标（A-Z, a-z, 0-9）
  - `pinned`: 分类置顶

### 新增 - 图标选择器
- 创建 `IconPicker.vue` 图标选择器组件
- 96 种 lucide 图标
- 62 种 ASCII 图标（A-Z, a-z, 0-9）
- 20 种预设颜色 + 自定义颜色选择
- 搜索过滤功能

### 新增 - UI 重大变化
- **左侧栏重构**：
  - 分类按优先排位分动态排序
  - 前 X 名展开显示（X 可设置，默认 5）
  - X+1 及以后折叠收纳
  - 无有效待办的类别单独折叠
  - 支持分类置顶
  - 显示分类分数和待办数量
- **任务卡片**：
  - 直接显示优先排位分数字
  - 高分数（≥1000）使用主题色高亮
  - 已过期分数显示红色
- **设置面板**：
  - 分数更新频率（1秒/5秒/30秒/手动）
  - 分类展开数量（3/5/8/10/全部）
  - 手动刷新按钮

### 新增 - 实时更新
- 优先排位分实时计算
- 设置中指定更新频率
- 使用 setInterval 定时刷新
- 数据变更后自动重算

### 新增 - 日期格式统一
- TimeHelper 统一使用 `yyyy/mm/dd` 格式
- 新增 `format_date`、`format_datetime`、`parse_display` 方法
- 新增 `iso_to_display`、`display_to_iso` 转换方法
- 内部存储保持 ISO 格式，显示时转换

### 技术改进
- 后端：新增 `priority.py` 模块（242 行）
- 后端：Todo/Category dataclass 新增字段
- 后端：storage.py 支持新字段的 CRUD
- 后端：utils.py 新增日期格式工具
- 前端：新增 `utils/priority.ts`（150 行）
- 前端：新增 `IconPicker.vue`、`SettingsPanel.vue`
- 前端：types/index.ts 新增类型定义
- 前端：Pinia Store 新增分数计算和设置管理
- 前端：TodoItem 显示分数徽章
- 前端：CategorySidebar 动态排序 + 折叠
- 前端：TodoForm 添加新字段表单
- 前端：FilterBar 添加分数排序选项
- 43 项优先排位分算法测试全部通过

### 向后兼容
- 旧数据自动使用默认值迁移
- 新字段都有合理的默认值
- ISO 日期格式仍可解析

## [0.3.0] - 2026-09-20

### 新增 - UI 视觉打磨
- 过渡动画系统：列表项添加/删除/状态切换动画（TransitionGroup）
- 卡片精致化：多层级阴影、圆角优化、悬浮效果增强
- 空状态重设计：带插画的友好提示、使用建议卡片
- 深色模式完整支持：手动切换（自动/浅色/深色），CSS 变量全覆盖
- 操作菜单：悬浮显示操作按钮（编辑/归档/删除）
- 搜索高亮：匹配文字 <mark> 高亮显示

### 新增 - 交互优化
- 排序系统：创建时间/截止日期/优先级/自定义排序
- 标签筛选：从所有标签中选择多标签过滤
- 批量操作：选择多个待办后批量完成/删除
- 键盘导航增强：↑↓箭头切换、Enter编辑、Space切换完成
- 快捷键：N新建、/搜索、Ctrl+D主题、Ctrl+E导出、Ctrl+I导入

### 新增 - 实用功能
- 截止日期提醒：设置提前 N 天警告（0/1/3/7天）
- 重复任务：支持每日/每周/每月重复类型
- 备注/笔记：支持 Markdown 语法
- 置顶功能：重要待办一键置顶
- 数据导出：JSON 和 CSV 格式
- 数据导入：支持 JSON 合并/替换模式
- 自动备份：带数量限制的自动备份机制

### 新增 - 数据健壮性
- 46 项自动化测试全部通过（v0.3.0 新功能）
- 边界测试：空标题、特殊字符、超长输入、无效 ID
- 导入/导出模块：TodoExporter / TodoImporter
- 自动备份：AutoBackup 类，含清理和恢复功能

### 新增 - 跨模块集成
- 测试 plan-helper / time-helper 预留接口
- 导出/导入集成示例

### 技术改进
- 后端：新增 RecurrenceType 枚举
- 后端：Todo 新增 recurrence/deadline_warning_days/sort_order/pinned 字段
- 后端：新增 needs_warning()、toggle_pin() 方法
- 后端：新增 9 个 API 端点（pin/reorder/warning/export/import/backup）
- 前端：localStorage 持久化存储
- 前端：CSS 变量体系重构，增加 5 个层级的背景/阴影
- 前端：Pinia Store 扩展排序/标签/导出/深色模式功能

### Bug 修复
- 修复 @dataclass 装饰器放置错误（原本误放在 RecurrenceType 上）

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
