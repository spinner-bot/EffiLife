# Tauri Plan Helper sidecar 交付方案

## 目标

正式桌面安装包不能要求用户单独安装 Python 或手动启动 `plan-helper/web/server.py`。保留现有 Python plan 数据核心，通过受控 sidecar 随 EffiLife 安装包分发。

## 方案

1. 使用 PyInstaller 将 `plan-helper/web/server.py` 打包为单文件 sidecar。
2. 按 Tauri 目标三元组输出到 `time-helper/desk/src-tauri/binaries/efflife-plan-helper-<target-triple>`，由 `externalBin` 声明纳入安装包。
3. release Tauri 启动时通过 shell sidecar API 启动服务，传入 `--host 127.0.0.1`、`--port 8765` 和平台应用数据目录；debug 构建不启动 sidecar，继续使用测试 launcher。
4. sidecar 使用 0099 方案的 `--data-dir` 和启动加载/写后持久化能力。前端 API 契约保持不变，正式构建不依赖项目目录。
5. 构建脚本只生成本机/目标平台构件，不把二进制提交到源码仓库；发布流水线在 Tauri 构建前执行构建脚本。

## 生命周期与失败边界

- sidecar 启动失败应阻止 release 应用继续进入计划功能的假成功状态，并在日志中记录原因。
- debug 环境仍由 launcher 负责 companion，避免开发环境因缺少构件而无法运行。
- sidecar 的 stdout/stderr 由 Tauri 异步消费，避免子进程管道阻塞。
- 移动端暂不复用该 Python sidecar；移动端后续需要同源/原生实现，这是独立适配边界。

## 验证

- PyInstaller 脚本参数和输出命名测试。
- Python 计划服务回归测试。
- 前端构建。
- Rust/Tauri 构建需在具备 Rust/Cargo 的发布环境执行；当前开发机缺少该工具链，不能在本机宣称已完成安装包验收。

