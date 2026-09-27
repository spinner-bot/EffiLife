# 0072 Tauri 多端发布矩阵

## 目标

统一应用正式发布不再依赖测试启动器。发布工作流需要在原生 runner 上构建前端、plan-helper sidecar 和对应平台安装包。

## 矩阵

| 平台 | runner | Tauri bundle | 产物 |
| --- | --- | --- | --- |
| Windows | `windows-latest` | `nsis` | `.exe` |
| Linux | `ubuntu-22.04` | `deb` | `.deb` |
| macOS | `macos-latest` | `dmg` | `.dmg` |

## 约束

- 每个 runner 使用本机 Python、Node 和 Rust，PyInstaller 只负责构建当前平台的 sidecar，不做交叉编译假设。
- 通过 `--bundles` 显式选择当前平台产物，避免一个平台的 bundle 配置误应用到另一个平台。
- Windows 继续保留手动触发和 `v*` tag 触发；矩阵任务分别上传对应产物。
- Android/Tauri Mobile 仍使用独立移动端工程和只读事件计划快照边界，不与桌面 sidecar 构建混合。

## 验收

CI 配置静态检查确认三个平台的 runner、bundle 参数和 artifact 路径一一对应；真实安装包构建需在各平台 runner 上执行。
