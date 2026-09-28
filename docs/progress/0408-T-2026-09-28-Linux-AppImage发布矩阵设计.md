# Linux AppImage 发布矩阵设计

## 背景

正式桌面交付方案将 Linux AppImage 作为便携式安装入口，但现有 CI 仅构建 `.deb`。这会让不使用 Debian 系包管理器的用户缺少统一产物。

## 方案

- 在现有 Linux runner 上增加独立 `linux-appimage` 矩阵项。
- 安装 AppImage 打包所需的 `libfuse2`，与现有 WebKit、图标和 patchelf 依赖共用。
- 复用同一 sidecar、测试、Tauri 构建、非空产物校验和 SHA-256 校验链路。
- 产物路径固定为 `bundle/appimage/*.AppImage`，并由发布预检和契约测试共同守护。
- 不改变 Windows NSIS、Linux DEB、macOS DMG 的现有任务。
