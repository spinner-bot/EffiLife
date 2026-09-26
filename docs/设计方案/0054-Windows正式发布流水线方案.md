# Windows 正式发布流水线方案

## 目的

当前开发机没有 Rust/Cargo，不能本地验收 Tauri 安装包。为避免正式构建依赖个人开发机状态，建立可重复的 Windows 发布流水线。

## 流程

1. 手工触发或推送 `v*` 标签。
2. 在 Windows runner 安装 Python 3.13、Node.js 22 和稳定版 Rust。
3. 使用锁文件执行 `npm ci`，安装 PyInstaller。
4. `npm run tauri build` 先执行既有 `build:sidecar`，再构建 Vue 前端和 NSIS/MSI 构件。
5. 将安装包上传为 workflow artifact，供签名、验收和后续发布步骤使用。

## 边界

- 当前流水线只负责构建和留存构件，不自动签名、发布或推送更新。
- 签名证书、更新服务器和发布权限在产品发布阶段注入，不写入仓库。
- 安装后数据迁移、sidecar 生命周期和多语言视觉验收仍需在 runner 或实际设备上执行。

