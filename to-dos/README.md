# to-dos / 待办事项

EffLife 效率工具集的轻量任务清单模块。

## 功能

- 待办事项 CRUD（创建、读取、更新、删除/归档）
- 四级优先级：紧急且重要 / 重要 / 紧急 / 普通
- 五种状态：待处理 / 进行中 / 已完成 / 已归档 / 已取消
- 子任务管理
- 分类系统（颜色 + 图标）
- 全文搜索（标题 + 描述 + 标签）
- 统计面板（完成率、按分类/优先级统计）
- 逾期待办 + 今日待办
- 批量操作
- 跨模块联动（plan-helper / time-helper 预留接口）
- 命令行交互界面

## 快速开始

```bash
cd to-dos
python main.py          # 交互模式
python test_api.py      # 运行测试
```

## 命令行用法

```bash
python main.py list          # 列出所有待办
python main.py stats         # 统计
python main.py add "新任务"   # 创建
python main.py done TODO-xxx # 完成
python main.py overdue       # 逾期
```

## 作为库使用

```python
from src import TodoAPI

api = TodoAPI()

# 创建
result = api.create_todo(title="写报告", priority="important", category="work")
todo_id = result["data"]["id"]

# 完成
api.complete_todo(todo_id)

# 统计
stats = api.get_stats()
```

## 技术栈

- Python 3
- dataclass 数据模型
- JSON 文件持久化
- 统一 API 响应格式

## 版本

当前版本：0.1.0（见 `VERSION`）
