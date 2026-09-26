# 0100-T-2026-09-27 Tauri sidecar 构建链落地

## 变更

- 新增 `scripts/build_plan_helper_sidecar.py`，按 Tauri target triple 使用 PyInstaller 生成单文件 Plan Helper sidecar。
- Tauri bundle 声明 `binaries/efflife-plan-helper`，正式构建前自动执行 `build:sidecar`。
- release Tauri 进程通过 shell sidecar 启动 Plan Helper，并传入平台数据目录；debug 构建继续由测试 launcher 提供 companion。
- 增加 shell spawn 权限和本地 sidecar 构件忽略规则。
- 新增构建契约测试，校验目标后缀、Tauri externalBin 和构建钩子。

## 验证

- sidecar dry-run：通过。
- Windows PyInstaller 实际构建：通过，生成 `efflife-plan-helper-x86_64-pc-windows-msvc.exe`（本地忽略构件）。
- sidecar HTTP smoke：通过，`/api/plans` 可用且 POST 后注册表落盘。
- 修正 Tauri sidecar 传入的运行根目录，保持旧计划数据的 `plan/` 与 `data/system/registry/` 相对布局，避免产生重复 `data/data` 层级。
- 前端 `npm run build`：通过。
- Python 全量测试：提交前执行。

## 未完成边界

当前开发机没有 Rust/Cargo，Tauri Rust 编译和 NSIS 安装包生成仍需在发布环境验收；本次不把该验证结果虚报为已完成。
