# Tauri 移动端构建入口方案

日期：2026-09-30

## 决策

在 `time-helper/desk/package.json` 提供四个显式脚本：

- `mobile:android:init` / `mobile:ios:init`：在具备对应 Tauri Mobile 工具链时生成平台工程。
- `mobile:android:build` / `mobile:ios:build`：使用 `tauri.mobile.conf.json` 构建移动端，并明确不调用 Python Plan Helper sidecar。

桌面端继续使用 `build:sidecar` 和 `tauri.conf.json`。移动端与桌面端共用 Vue 前端和数据协议，但不共用桌面 sidecar 构建链。

## 诚实边界

这些脚本只统一命令入口，不代表 Android/iOS 工程、签名、安装升级或真机验收已经完成。实际执行仍需要：

1. 目标平台 SDK 与 Rust/Tauri 工具链。
2. 先完成对应 `init` 并提交或管理生成的平台工程。
3. 配置签名、权限、文件访问和升级迁移测试。

契约测试只保证命令不会错误地带入桌面 sidecar，并且构建使用移动配置。
