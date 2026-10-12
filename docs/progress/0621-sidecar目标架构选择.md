# 1127 sidecar 目标架构选择

日期：2026-10-05  
类型：实现报告

## 背景与目标

桌面 Tauri 构建的 `beforeBuildCommand` 需要为 Plan Helper sidecar 生成与 Tauri 当前目标一致的文件名。原脚本仅读取项目自定义的 `TAURI_TARGET_TRIPLE`，在官方 Tauri 构建环境提供 `TAURI_ENV_TARGET_TRIPLE` 时可能退回宿主架构。

## 实现与兼容性

- sidecar 构建脚本优先读取 Tauri 官方的 `TAURI_ENV_TARGET_TRIPLE`；
- 保留 `TAURI_TARGET_TRIPLE` 作为手动构建和旧工具链兼容回退；
- 未设置环境变量时仍使用 `rustc -vV` 和平台架构推断；
- 不改变 PH 数据结构、启动端口、统一归档协议或移动端无 sidecar 边界。

## 实际验证

- `python -m pytest -q tests/test_sidecar_build.py` → 8 passed；
- 前端构建和统一启动冒烟验证沿用 `1126-构建与启动器验证` 的结果；
- `python -m pytest -q` → `879 passed`；

## 提交与推送

- 实现提交：`fb13aa1 fix(release): honor tauri target triple`；
- 报告提交后推送至 `origin/main`。
- 工作直接在 `main`，不创建分支。

## 未验证项与边界

- 当前 Windows 环境未执行真实 Tauri 原生打包；
- 多平台 sidecar 实际产物仍需对应 CI runner 验证；
- 主题保存后退出恢复问题继续暂缓。
