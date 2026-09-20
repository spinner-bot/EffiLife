# plan-helper

计划助手 — EffLife 效率工具集的计划管理模块

## 功能

- **现代化 Web UI**：卡片式布局、甘特图、日历视图、拖拽排序
- **模板系统**：工作日/休息日/备考冲刺模板，快速复制昨日计划
- **智能建议**：基于历史数据推荐模板和高频任务
- **冲突检测**：时间溢出、重复任务、不合理分配提醒
- **进展记录**：快速完成标记、实时进度条、时间线日志
- **统一 API**：供 time-helper/to-dos 调用的完整接口
- **数据健壮性**：导入/导出、自动备份、数据验证、边界测试

## 快速开始

```bash
# 启动 Web UI
cd plan-helper
python -m web.server

# 或指定端口
python -m web.server --port 8080
```

打开浏览器访问 `http://127.0.0.1:8765`

## 模块结构

```
plan-helper/
├── modules/
│   ├── plan.py       # 核心计划类（Plan）
│   ├── manager.py    # 计划管理器（Plans）
│   ├── api.py        # 统一 API 层
│   ├── template.py   # 模板系统
│   ├── data.py       # 数据健壮性工具
│   ├── chat.py       # LLM 对话模块
│   ├── wizard.py     # CLI 交互向导
│   ├── text.py       # JSON → 文本转换
│   ├── prompt.py     # LLM 提示词
│   └── file.py       # 文件系统管理
├── web/
│   ├── server.py     # Web 服务器
│   ├── index.html    # SPA 入口
│   └── static/
│       ├── styles.css # 样式
│       └── app.js    # Vue 3 应用
├── docs/
│   ├── DESIGN_SPEC.md # UI 设计方案
│   └── API_SPEC.md   # API 文档
├── main.py           # 入口
├── VERSION           # 0.2.0
└── CHANGELOG.md      # 更新日志
```

## API 使用

```python
from modules import api

# 创建计划
resp = api.create_plan(name="学习计划")
plan_id = resp.data["id"]

# 添加任务
api.add_task(plan_id, 0, "阅读30分钟", 30)

# 查看进度
progress = api.get_progress(plan_id)
print(f"完成: {progress.data['progress_percentage']}%")
```

## 文档

- [UI 设计方案](docs/DESIGN_SPEC.md)
- [API 文档](docs/API_SPEC.md)
- [UX 设计理念](../docs/spec/UX%20设计理念.md)
- [UI 设计理念](../docs/spec/UI%20设计理念.md)
