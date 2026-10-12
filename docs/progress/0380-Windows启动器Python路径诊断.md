# 0806 Windows 启动器 Python 路径诊断

## 日期

2026-10-01

## 背景

统一启动器允许通过 `EFFILIFE_PYTHON` 指定 Python 解释器。POSIX 启动脚本已经在执行前检查该路径；Windows `start.bat` 原先直接调用失效路径，用户只能看到系统级的模糊启动错误。

## 实施

- Windows 启动器在调用显式 Python 路径前增加存在性检查。
- 路径不存在时输出包含实际路径的错误信息并返回退出码 `127`，不进入后续模块检测。
- 保留统一工作区参数转发和 `EFFILIFE_NO_PAUSE` 行为。

## 验证

- `python -m pytest -q tests/test_launcher.py`：`63 passed`。
- `python -m pytest -q`：`673 passed`。
- `git diff --check`：通过，仅有 Git 的换行符提示。

## 未验证项

当前环境未启动 Windows 批处理文件的独立进程验收；契约测试覆盖脚本内容，真实安装包启动仍需原生发布环境验证。
