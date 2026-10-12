# 0627-Tauri sidecar 端口隔离

## 背景

正式 Tauri 壳固定使用 `127.0.0.1:8765` 启动 Plan Helper。此前壳只在启动后检查健康接口；若旧进程或其他服务已经占用该端口，健康检查可能连接到错误实例，形成“界面正常但数据根错误”的隐蔽风险。

## 实现

- sidecar 启动前增加端口占用探测。
- 端口已被占用时立即拒绝启动，并返回明确错误，不连接既有服务。
- 原有 sidecar 健康接口身份校验仍保留，作为启动后的第二道检查。
- 不改变 PH 端口、数据结构或开发 launcher 的兼容行为。

## 验证

- `python -m pytest -q tests/test_sidecar_build.py tests/test_tauri_data_root_contract.py`。
- `python -m pytest -q`。
- Rust/Tauri 安装包构建仍需具备 Rust/Cargo 的发布环境完成；当前开发机只做源代码契约验证。

## 提交状态

待验证后提交；`docs/HOTL/` 与 `time-helper/desk/package-lock.json` 不纳入提交。
