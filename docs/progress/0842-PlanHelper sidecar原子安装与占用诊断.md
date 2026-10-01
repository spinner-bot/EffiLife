# 0842 Plan Helper sidecar 原子安装与占用诊断

## 发现

本机执行 `python scripts/build_plan_helper_sidecar.py` 时，PyInstaller 已成功生成 sidecar，但最终复制到 `src-tauri/binaries/` 的步骤因目标可执行文件被占用而抛出裸 `WinError 32`。这会让开发启动器和正式构建难以区分“生成失败”和“旧进程锁定产物”。

## 调整

- 先将生成的 sidecar 写入同目录临时文件。
- 使用 `os.replace` 原子替换正式目标，避免暴露半成品。
- 捕获 Windows 可执行文件占用错误，提示关闭 EffiLife 或 Plan Helper 后重试。
- 增加原子安装成功和锁定目标诊断测试。

## 边界

原子替换无法绕过操作系统对正在运行的可执行文件的锁定；它只能保证失败时不破坏原有产物，并提供可执行的恢复路径。

