# 0405｜Tauri 统一数据根目录环境变量方案

## 背景

launcher 和 Python DataManager 已支持 `EFFILIFE_DATA_DIR`，Plan Helper 也能通过 `--data-dir` 接收该根目录。但 Tauri 原生层此前始终使用平台默认目录，配置和原生能力可能落到另一份数据中。

## 设计决策

- Tauri `get_data_dir()` 优先读取非空 `EFFILIFE_DATA_DIR`。
- 环境变量为空或未设置时继续使用平台默认的 `<local-data>/EffiLife/data`，不改变现有安装用户路径。
- Tauri 启动 Plan Helper 时继续将数据目录的父目录作为 Plan Helper runtime root，保持既有 `plan/` 与 `data/system/registry/` 布局。
- 环境变量表示 Tauri 的 `data` 目录；正式 launcher 若设置该变量，必须让同一目录契约贯穿原生配置和 sidecar。

## 验收标准

1. Rust 原生层包含环境变量优先分支。
2. 空环境变量不会覆盖平台默认路径。
3. 未配置环境变量的旧安装路径保持不变。
