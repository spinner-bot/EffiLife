# EffiLife 重构工作区

本目录是前端/主题/包系统重构的设计工作区。设计稿由 Codex 依据用户的背景说明与关键决策起草，用户审计修订。**在设计稿评审通过之前，这里只写文档，不改业务代码。**

## 状态

- 阶段：Phase 0（设计）
- 最后更新：2026-11-10
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
| [05-versioning-and-architecture.md](05-versioning-and-architecture.md) | 3.0.0 版本策略、单一软件、桌面优先与多端准备 |
| [06-archive-plan.md](06-archive-plan.md) | 归档区结构与 1/2 代快照策略 |
| [07-open-questions.md](07-open-questions.md) | 待确认事项与已解决决策 |
| [09-package-registry.md](09-package-registry.md) | 软件分配的包 ID、注册表、权限登记与生命周期 |
| [10-design-doc-template.md](10-design-doc-template.md) | 设计文档模板，供 Codex 组织草案参考 |
| [11-user-design.md](11-user-design.md) | 产品设计审阅稿：定位、统一录入、内容层级、使用动线与扩展约束 |
| [12-long-term-goals.md](12-long-term-goals.md) | 远期产品化与商业化、日报/周报统计、智能穿戴、AI 与语音输入、多端交付 |
| [13-system-architecture.md](13-system-architecture.md) | 多端与系统可扩展性：职责边界、语言/主题/字体机制、适配契约与验收提案 |

## 工作规则

1. **设计先行**：Phase 0 只产文档；实现从 Phase 1 开始，且需要用户确认。
2. **质量优先**：重构期间软件可以不可用；不以“先能跑”为借口降低结构质量。
3. **密集提交**：每个文件创建/修改、每次目录结构调整都单独 commit；直接落 `main`，需要合并历史分支时使用 `--no-ff`。
4. **决策可追溯**：已确认决策写入 01；未确认事项写入 07；两者状态必须明确。
5. **不改数据层**：主题持久化字段、`.efl` 迁移等依赖数据大改的部分，等数据 schema 定稿后再实现。
6. **桌面优先、多端准备**：首期交付以桌面端为主，系统架构从当前开始划清多端适配边界；具体其他端的交付后续安排。
7. **主动拟稿**：常规细节由 Codex 依据产品背景先提出完整方案，标明已确认要求与待审提案；用户按文档审计，关键方向存在无法合理判断的冲突时再提问。
8. **可扩展架构**：多语言、主题、字体等通过模块化的登记、加载和版本契约管理，避免扩展时需要遍改页面与业务逻辑。
