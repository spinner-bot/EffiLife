# EffiLife 重构工作区

本目录是前端/主题/包系统重构的设计工作区。**在用户的设计文档到位并评审通过之前，这里只写文档，不改业务代码。**

## 状态

- 阶段：Phase 0（设计）
- 最后更新：2026-10-26
- 当前产品版本：1.7.0
- 重构完成后目标版本：**3.0.0**
- 审计报告：[../docs/audit/2026-10-26-视觉审计.md](../docs/audit/2026-10-26-视觉审计.md)

## 文档索引

| 文档 | 内容 |
|---|---|
| [01-context-and-decisions.md](01-context-and-decisions.md) | 现状、审计结论、重构范围、已确认决策 |
| [02-refactor-process.md](02-refactor-process.md) | 重构流程、阶段划分、质量门槛、提交策略 |
| [03-theme-and-permission-system.md](03-theme-and-permission-system.md) | 主题系统、解析器、0–3 级权限、CSS/JS 策略 |
| [04-package-formats.md](04-package-formats.md) | d3el / r3el / t3el / f3el 包格式与扩展名机制 |
| [05-versioning-and-architecture.md](05-versioning-and-architecture.md) | 3.0.0 版本策略、取消三模块、桌面优先 |
| [06-archive-plan.md](06-archive-plan.md) | 归档区结构与 1/2 代快照策略 |
| [07-open-questions.md](07-open-questions.md) | 待确认事项与建议默认值 |

## 工作规则

1. **设计先行**：Phase 0 只产文档；实现从 Phase 1 开始，且需要用户确认。
2. **质量优先**：重构期间软件可以不可用；不以“先能跑”为借口降低结构质量。
3. **密集提交**：每个文件创建/修改、每次目录结构调整都单独 commit；直接落 `main`，需要合并历史分支时使用 `--no-ff`。
4. **决策可追溯**：已确认决策写入 01；未确认事项写入 07；两者状态必须明确。
5. **不改数据层**：主题持久化字段、`.efl` 迁移等依赖数据大改的部分，等数据 schema 定稿后再实现。
6. **桌面优先**：本轮重构只考虑桌面端；移动端与 iOS 不进入实现范围。
