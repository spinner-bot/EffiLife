# 0608｜Sidecar 数据目录运行时契约

## 背景

正式 Tauri 桌面包通过 sidecar 启动 plan-helper。此前已有启动参数、构建产物和基础 health 检查，但测试没有证明 HTTP 写入会落到 sidecar 接收的 `--data-dir`，存在“检查通过、数据写错目录”的回归风险。

## 目标与范围

- 验证 sidecar 以显式 `--data-dir` 启动后，PH 计划写入该目录。
- 保留 PH 既有 `plan/` 和 `data/system/registry/` 存储布局。
- 不改变 PH 数据结构、删除语义或桌面/移动端边界。

## 实现

- 为 `tests/test_plan_server_health.py` 增加真实 HTTP 进程测试。
- 测试通过 `/api/plans` 创建带 section/task 的计划，并检查显式数据根下的两个持久化文件。
- 同时确认仓库根目录不会被误写入，覆盖 sidecar 独立进程的 cwd/data-dir 约定。

## 兼容性与架构决策

PH 仍使用原有相对路径布局；`server.py` 在收到 `--data-dir` 后将该目录作为运行时根目录。Tauri 的默认平台目录和 `EFFILIFE_DATA_DIR` 约定保持不变。本次仅增加验证，不迁移既有数据。

## 验证

```text
python -m pytest -q tests/test_plan_server_health.py
```

结果：`10 passed in 1.52s`（包含 sidecar health、HTTP 数据根持久化、构建配置和 Tauri 数据根契约测试）。

## 提交状态

待提交。受保护的 `time-helper/desk/package-lock.json` 与 `docs/HOTL/` 未修改、未纳入提交。
