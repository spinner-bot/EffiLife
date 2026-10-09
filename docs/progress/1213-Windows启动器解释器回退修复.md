# 1213｜Windows 启动器解释器回退修复

日期：2026-10-10  
状态：已完成并推送

## 背景与问题

Windows 测试启动入口会优先检测 `py.exe`。此前只要系统存在 `py.exe` 就直接执行 `py -3`；当 Python Launcher 存在但没有可用的 Python 3 运行时，启动器会失败，即使系统仍有可用的 `python` 命令。这会造成“有时启动不了”的误导性体验。

## 实施内容

1. `launcher/start.bat` 在调用 `py -3` 前先执行轻量 `import sys` 探针。
2. 探针失败或找不到 `py.exe` 时，自动回退到 `python launcher\\start.py --unified`。
3. 用户显式设置 `EFFILIFE_PYTHON` 时仍保持原有优先级，不自动替换用户指定解释器。
4. 增加 Windows 启动脚本回退契约测试。

## 验证

- 集成测试：`55/55 passed`。
- 启动冒烟：前端、Plan Helper 健康检查和端口释放均通过。
- 启动器/环境定向测试：`87 passed`。
- 全量 Python 测试：`961 passed`。
- 桌面与移动发布配置检查均通过。

## 提交与推送

- `9dd98ed fix(launcher): fall back when py lacks Python 3`：Windows 启动脚本和回归测试，已推送。
- `fac1951 docs(launcher): record interpreter fallback fix`：本报告，已推送。

## 边界

本修复只增强开发/测试启动入口，不改变正式 Tauri 安装包入口；正式桌面和移动构建仍需在具备对应原生工具链的环境中验证。
