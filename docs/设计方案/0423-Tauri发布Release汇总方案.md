# Tauri 发布 Release 汇总方案

## 背景

桌面发布矩阵已经在 GitHub Actions 中构建 Windows NSIS、Linux DEB、Linux AppImage 和 macOS DMG，并上传为 Actions artifact。用户仍需进入工作流页面取包，标签发布没有形成正式 Release 页面。

## 方案

- 保留现有矩阵构建、包校验和 checksum 生成步骤。
- 增加独立 `publish` job，等待全部平台构建成功后下载所有 artifact。
- 仅当 `github.ref` 是 `v*` 标签时创建 GitHub Release；`workflow_dispatch` 只执行构建，不产生意外发布。
- 使用仓库内生成的安装包和 `.sha256` 文件作为 Release assets，并由 GitHub 自动生成变更说明。
- 发布 job 使用最小的 `contents: write` 权限，构建 job 继续保持 `contents: read`。

## 不变约束

- 不改变 Tauri target、sidecar、移动端无 sidecar 边界或本地 launcher 语义。
- 不把未通过 `verify_release_artifacts.py` 的构件发布出去。
- 不依赖本地 Rust/Cargo 环境；实际安装包仍由 CI runner 构建。
