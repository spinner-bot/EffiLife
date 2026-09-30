# 桌面 Plan Helper sidecar 非空发布门禁

日期：2026-09-30

## 本次处理

正式 Tauri 桌面构建通过 `build:sidecar` 生成并携带 Plan Helper。构建脚本原先只检查 PyInstaller 输出路径存在，现在增加两道非空普通文件校验：

- PyInstaller 输出必须非空；
- 复制到 Tauri `binaries` 目录后的 sidecar 也必须非空。

这样可以在 Tauri 打包前阻断损坏或空 sidecar，避免安装包构建成功但运行时无法启动计划服务。

## 验证

- 新增 sidecar 空文件判定测试。
- 提交前执行 sidecar 专项与全量 Python 回归。
