# 0083 Tauri 侧车生命周期管理

## 问题

正式桌面版通过 `tauri-plugin-shell` 启动 Plan Helper。当前代码只保留 `CommandChild` 以维持进程运行，没有把句柄纳入应用状态，也没有在 Tauri 退出事件中显式终止侧车。若插件或操作系统不替应用回收子进程，可能留下 8765 端口占用。

## 决策

1. 将桌面版 `CommandChild` 放入受 Tauri 管理的 `Mutex<Option<_>>` 状态。
2. 继续异步消费 stdout/stderr 事件，避免管道阻塞。
3. 收到 `RunEvent::ExitRequested` 时取出句柄并调用 `kill()`；句柄取出后只执行一次清理。
4. 仅在 release desktop 编译条件下启用，开发模式和移动端不改变现有行为。
5. sidecar 自身异常退出不触发应用退出；前端继续通过 HTTP 探活显示服务不可用状态。

## 验收

- Rust 源码包含受控 sidecar 状态与退出清理路径。
- Python/前端现有测试不受影响。
- 有 Rust/Cargo 的 CI 环境中由 Tauri 编译验证；当前开发机没有 Cargo，只能完成静态审查与其他测试。
