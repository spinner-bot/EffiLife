# 启动器 companion 健康诊断

日期：2026-09-30

## 背景

统一工作区启动时会由启动器按需拉起 `plan-helper` companion API。此前 `--diagnose` 只检查顶层模块 URL，无法区分“统一前端不可用”和“前端依赖的 companion 端口被其他不健康进程占用”，导致启动失败时定位信息不足。

## 本次变更

- `launcher/start.py` 递归读取模块声明的 `companions`，将 companion 的命令、工作目录、URL、健康检查 URL、端口占用和健康状态纳入诊断 JSON。
- companion 端口已被占用但健康检查失败时，诊断结果增加 `companion-port-conflict` 阻塞项，并提供停止冲突服务后重试的提示。
- `--doctor` 以 `ready`、`stopped` 或 `port conflict` 展示 companion 状态，避免把“依赖服务问题”误判为前端问题。
- 诊断保持只读，不会启动、停止或修改任何服务。

## 验证

- `python -m pytest -q tests/test_launcher.py`：49 passed。
- 全量 Python 回归与前端构建在本次提交前后继续执行；原有 protected `time-helper/desk/package-lock.json` 与 `docs/HOTL/` 未纳入变更。

## 验收边界

本地只验证诊断逻辑和测试替身；正式 Tauri 安装包及真实设备仍需在对应发布/设备环境验收。
