# 移动端不依赖 Python sidecar 边界

## 发现

Tauri 的 release/debug 条件不能单独代表桌面平台。若只使用 `not(debug_assertions)`，Android/iOS release 也会尝试启动 Windows/macOS/Linux 侧的 Python Plan Helper sidecar。

## 决策

- Plan Helper sidecar 只允许在 `desktop` 且非 debug 构建中启动。
- Tauri mobile 构建不启动外部 Python 进程，也不假设 `127.0.0.1:8765` 存在。
- 移动端计划功能必须通过后续的同源/原生运行时适配提供；在适配完成前，客户端应明确显示计划服务不可用，而不是伪造空计划或静默失败。
- Windows 发布流水线继续只负责桌面 NSIS/MSI；移动端发布单独建立数据、文件和计划服务验收矩阵。

## 验证

- Rust 源码静态检查确认 sidecar 函数与调用均使用 `all(not(debug_assertions), desktop)`。
- 当前开发机没有 Cargo，移动端 Tauri 编译仍需发布环境验收。

