# Tauri 移动端真实构建工作流

## 目标

把移动端从“配置可用、前端可编译”的边界检查推进到可在平台 runner 上实际生成构建产物，同时保持移动端不携带桌面 Python Plan Helper sidecar。

## 方案

- 新增 `.github/workflows/tauri-mobile-build.yml`，只通过 `workflow_dispatch` 启动，避免每次前端提交都消耗 Android/macOS 构建资源。
- Android runner 安装 Java 17、Android SDK、Rust Android targets，初始化 Tauri Android 工程并上传 APK。
- macOS runner 初始化 Tauri iOS 工程，使用 Rust Apple targets 构建 debug app，并上传 `.app`/`.ipa` 构建结果。
- Tauri iOS 生成的原生工程和产物目录使用 `src-tauri/gen/apple`；工作流不能按 Android 的 `gen/ios` 目录猜测路径。
- 两个平台均使用 `tauri.mobile.conf.json`；移动配置的 `externalBin` 保持为空，不调用 `build:sidecar`。
- 初始化工程位于 CI 临时工作区，不把平台生成目录强行提交到源码仓库。

## 验收边界

该工作流验证“能否生成未签名/调试构建产物”，不等同于商店签名、正式发布、设备安装升级或权限验收。正式签名需要后续接入 Android keystore、Apple signing certificate/provisioning profile，并另设保护凭据。
