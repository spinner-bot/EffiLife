# Tauri 移动端构建入口落地

日期：2026-09-30

## 已完成

在 `time-helper/desk/package.json` 增加统一移动端命令：

- `npm run mobile:android:init`
- `npm run mobile:android:build`
- `npm run mobile:ios:init`
- `npm run mobile:ios:build`

Android/iOS 构建命令都显式加载 `src-tauri/tauri.mobile.conf.json`，不执行桌面端 `build:sidecar`。桌面端仍保持原有 `tauri.conf.json` 与 Plan Helper sidecar 链路。

## 验证

- 新增移动构建命令契约测试。
- `python -m pytest -q`：462 passed。
- `npm run release:mobile-check`：`ok: true`。
- 前端生产构建已通过。

## 未完成边界

本机没有 Cargo/Rust、Android SDK 或 iOS 工具链，因此尚未执行 `init`、移动构建、签名、安装升级和真机验收。新增命令是下一阶段的标准入口，不代表移动安装包已经生成。
