# README 主题数量与注册表同步

日期：2026-10-09

## 背景

统一工作台继续扩展 TH 的主题架构后，README 仍写着 21 种主题，而 `ThemeEngine` 注册表已经包含 25 种。文档与产品能力不一致，会让用户低估可用主题，也不利于后续发布审计。

## 目标与非目标

目标是让项目入口文档准确反映当前注册表数量。

本次不修改主题定义、视觉效果、主题持久化逻辑或任何用户数据。

## 实现

将 README 的主题数量从 21 更新为 25；主题列表仍由 `ThemeEngine` 作为唯一运行时注册源，避免在文档中复制具体主题名称。

## 验证

```text
python -m pytest -q tests/test_frontend_i18n_coverage.py tests/test_settings_theme_i18n.py tests/test_theme_catalog_layout_contract.py
# Theme registry entries: 25
# 26 passed in 0.63s

另增 README 数量与运行时注册表的一致性契约，防止后续主题扩展再次造成入口文档漂移。
```

## 提交与推送

提交与推送：本次文档校正及一致性测试随提交 `test(theme): keep README theme count in sync` 推送至 `origin/main`。

## 未验证项与边界

- README 数量与源码注册项同步，但未进行逐主题的人工视觉验收。
- 真实桌面安装包和移动端主题渲染仍需对应平台验收。
