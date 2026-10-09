# 1217｜to-dos 兼容 UI 统一构建入口

日期：2026-10-10  
状态：已完成并推送

## 背景与问题

仓库已有统一桌面前端构建脚本，会复用启动器解析到的 Node/npm 和 PATH 环境；`to-dos/ui` 仍要求开发者直接执行 npm 命令。在 Windows 自定义 Node 目录场景中，npm 子进程可能找不到 `node`，导致 esbuild 安装或兼容 UI 构建失败。

## 实施内容

1. 新增 `scripts/build_todos_ui.py`，复用 `launcher.start.find_npm()` 与 `node_environment()`。
2. 缺少 Node/npm 时输出包含 `EFFILIFE_NODE_DIR` 的可操作诊断。
3. 增加构建入口契约测试，保证工作目录、构建命令和环境传递不回退。

## 验证

- `npm ci`（`to-dos/ui`）：安装锁定依赖成功。
- `python scripts/build_todos_ui.py`：兼容 UI 生产构建通过，Vite 转换 `1767` 个模块。
- 构建入口与启动器定向测试：`78 passed`。
- 全量 Python 测试：`966 passed`。

## 提交与推送

- `56a5700 build: reuse launcher toolchain for todos UI`：实现与测试，已推送至 `origin/main`。

## 边界

该入口用于开发、测试和发布前验证；GitHub CI 仍可继续使用其标准 Node 环境与原有 npm 命令，不改变 to-dos 的模块边界或运行时数据协议。
