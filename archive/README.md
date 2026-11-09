# EffiLife 归档区

本目录保存不再参与开发、构建、测试与发布的历史代际与一次性文件。归档内容只读，不接收修复；如需修改，请在新主线进行。

## 代际索引

| 目录 | 内容 | 状态 |
|---|---|---|
| `v1-time-helper/` | 1 代单文件 Tkinter 时间助手 | 已归档 |
| `v2-unified-workspace/` | 2 代统一工作台的最终快照 | 待 3 代合并前补齐 |
| `misc/` | 早期练习脚本与不可归类文件 | 已归档 |

## 规则

1. 所有历史文件只放在本目录，不在各模块下另建归档目录。
2. 归档后不修改、不修复、不更新依赖。
3. 本目录不进入前端构建、Python 测试与发布矩阵。
4. 每个代际/子目录必须有 README，说明来源、日期、用途、限制。
5. 用户数据、缓存、`node_modules`、构建产物不入归档；二进制只记录路径与校验和。
6. 目录创建、README、文件移动分别提交。

## 相关文档

- 归档规划：[../refactor/06-archive-plan.md](../refactor/06-archive-plan.md)
- 当前版本策略：[../refactor/05-versioning-and-architecture.md](../refactor/05-versioning-and-architecture.md)
