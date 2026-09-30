# Tauri 与开发启动器数据根一致性

日期：2026-09-30

## 问题

开发启动器把 `EFFILIFE_DATA_DIR` 原值传给 Plan Helper；Tauri sidecar 之前总是把 `get_data_dir()` 的父目录作为 Plan Helper 根目录。显式配置数据根时，二者因此会使用不同的 `plan/` 与 `data/` 目录。

## 修正

新增 `get_plan_helper_data_dir()`：

- 存在非空 `EFFILIFE_DATA_DIR` 时，直接使用显式根目录。
- 未配置环境变量时，沿用平台默认 `<app-data>/EffiLife/data` 的父目录作为 Plan Helper 兼容根。

这样开发启动器、Tauri 正式包和 Python sidecar 对显式数据根的解释一致，同时保留原有默认目录布局。

## 验证

- 新增 Tauri 数据根契约测试。
- `python -m pytest -q`：应覆盖显式根与平台默认回退契约。
- 本机缺少 Cargo/Rust，未声称完成新的 Tauri 原生编译。
