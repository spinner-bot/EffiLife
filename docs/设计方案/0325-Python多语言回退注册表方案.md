# Python 多语言回退注册表方案

- 状态：[已实现并验证]
- 创建时间：2026-09-29
- 执行者：Codex
- 关联目标：统一前端与 Python 集成层的多语言 fallback 语义

## 1. 问题

统一前端语言注册表规定 `en-US` 缺失键回退到 `zh-CN`，但 `common/i18n.py` 仍使用固定的 `FALLBACK_LOCALE = en-US`。同一个缺失键在前端和 Python sidecar/迁移工具中可能显示不同语言，且新增语言时必须修改硬编码分支。

## 2. 方案

- 在 Python 多语言基础层增加 `LOCALE_FALLBACKS` 注册表。
- 当前注册 `zh-CN -> zh-CN`、`en-US -> zh-CN`，与前端 `LocaleDefinition` 保持一致。
- 翻译时先查请求语言，再按注册表查 fallback，最后返回 key。
- 未知语言使用默认语言作为 fallback，不再隐式偏向英文。

## 3. 约束

- 不改变现有 JSON 目录结构、插值语法和 `I18n.t()` API。
- 保留无配置时默认使用 `zh-CN` 的行为。
- 新增语言只需添加目录文件和对应 fallback 注册，不修改翻译算法。

## 4. 验收

- Python fallback 与前端语言注册表语义一致。
- 自定义目录测试能验证 fallback 顺序，不依赖现有文案编码。
- 全量测试通过。
