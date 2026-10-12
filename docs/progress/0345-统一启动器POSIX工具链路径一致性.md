# 0769 统一启动器 POSIX 工具链路径一致性

## 问题

统一启动器和构建环境诊断都支持 `EFFILIFE_NODE_DIR`，但启动器此前仅在 Windows 分支查找自定义目录；Linux/macOS 即使配置了自定义 Node/npm，仍会退回系统 PATH。

## 处理

- POSIX 启动器现在优先查找配置目录下的 `node` 和 `npm`。
- 未配置自定义目录时，POSIX 不再尝试 Windows 专用默认路径。
- 增加 POSIX 自定义工具链回归测试，保持 Windows 行为不变。

## 验证

启动器专项测试和完整 Python 测试覆盖该路径；正式 Linux/macOS 原生安装包仍需在对应 runner 上验收。
