# 0355 启动器 POSIX 进程组回收方案

## 问题

统一启动器在 Windows 上通过 `taskkill /T` 回收子进程树，但 Linux/macOS 的旧实现只调用父进程 `terminate()`。Vite、Node 或 Python 服务可能继续存活，导致下一次启动遭遇端口占用。

## 决策

- POSIX 子进程继续使用 `start_new_session=True` 启动。
- 终止时向该进程组发送 `SIGTERM`，超时后发送 `SIGKILL`。
- 进程组操作失败时回退到单进程终止，保证兼容测试替身和异常环境。
- Windows 继续使用已有 `taskkill /T /F` 路径。
