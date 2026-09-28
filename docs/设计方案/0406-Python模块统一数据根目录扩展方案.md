# 0406｜Python 模块统一数据根目录扩展方案

## 背景

DataManager、launcher、Plan Helper 和 Tauri 已建立 `EFFILIFE_DATA_DIR` 契约，但 Python 集成层的 AuthManager 与 to-dos 存储仍在环境变量存在时写入各自历史目录，形成隐式数据分叉。

## 设计决策

- `AuthManager` 在统一根目录模式下写入 `<root>/user`。
- `TodoStorage` 在统一根目录模式下写入 `<root>/modules/to-dos`，与 DataManager 的模块目录规划一致。
- 显式构造参数优先级最高，供测试、迁移和临时隔离使用。
- `EffiLifeIntegration(data_root=...)` 显式传入的根目录继续向认证模块传递，不依赖进程环境变量。
- 集成注册表在统一根目录模式下登记 `<root>/modules/*`；未配置时保留仓库开发环境的历史模块路径。
- 未配置环境变量时不改变历史开发目录，避免破坏已有本地数据。

## 验收标准

1. 统一根目录模式下认证和待办存储路径都位于 `EFFILIFE_DATA_DIR` 下。
2. 未配置或显式传参时维持原有行为。
3. 现有 API CRUD 和集成测试不受影响。
