# 0804 Android 工具链目录门禁

## 日期

2026-10-01

## 背景

HOTL-1 要求移动端构建边界可诊断。原有 `check_build_environment.py` 只检查 `ANDROID_HOME` 或 `ANDROID_SDK_ROOT` 是否存在环境变量值；变量可能指向已经删除的目录，导致本机诊断误报为接近可构建状态。

## 实施

- Android 目标现在要求至少一个 SDK 环境变量指向真实目录。
- 未设置环境变量与路径不存在分别给出不同缺失项，保留现有工具、生成工程和其他平台检查逻辑。
- 增加不存在 SDK 根目录的回归测试，并更新“工具链、SDK、原生工程均存在时 ready”的测试夹具。

## 验证

- `python -m pytest -q tests/test_build_environment.py`：`8 passed`。
- `python -m pytest -q`：`674 passed`。
- `python scripts/check_build_environment.py --target desktop`：当前环境明确报告缺少 `cargo`、`rustc`；该结果符合实际，不伪报 ready。

## 未验证项

当前 Windows 环境仍没有 Android SDK、Cargo/Rust 和 iOS/Xcode 工具链，因此没有宣称真实移动构建或设备验收完成。
