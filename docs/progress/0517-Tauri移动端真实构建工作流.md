# Tauri 移动端真实构建工作流

日期：2026-09-30

## 本次进展

- 新增手动触发的 Android/iOS Tauri 构建工作流。
- Android 侧准备 Java 17、SDK、Rust Android targets，生成并上传 APK。
- iOS 侧使用 macOS runner、Rust Apple targets，生成并上传 debug app/ipa 构建结果。
- 已按 Tauri 实际目录约定使用 `src-tauri/gen/apple` 作为 iOS 产物路径。
- 移动构建显式使用移动配置，不构建或携带桌面 Plan Helper sidecar。
- 新增工作流契约测试，防止移动构建退化为仅执行前端构建。

## 未宣称完成的事项

当前仓库环境没有 Android SDK、Xcode 和 Rust，因此本机无法替代 GitHub runner 完成真实移动构建。工作流尚未代表签名、真机安装、升级迁移或商店发布验收；这些属于下一阶段平台验收。
