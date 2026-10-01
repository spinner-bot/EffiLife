# 0823 IndexedDB 启动降级修复

日期：2026-10-01

## 根因定位

最新构建产物在独立浏览器 profile 中等待 15 秒后进入错误页，错误详情为 `Core workspace initialization timed out after 15 seconds`。核心启动依赖 IndexedDB；此前 `openDB()` 对 `indexedDB.open()` 没有超时边界，浏览器数据库被阻塞或 WebView 存储异常时，既有的 localStorage fallback 根本无法执行。

## 修复

- 为 IndexedDB 打开请求增加 3 秒超时。
- 超时清空共享连接 promise 并抛出错误，使 `get()`/`set()` 等现有存储操作进入 localStorage fallback。
- 正常成功与错误路径均清理 timeout，避免定时器泄漏。
- 增加源码契约测试，锁定降级边界。

## 验证

- `python -m pytest -q tests/test_indexeddb_startup_resilience.py`：本轮执行
- 前端 `npm run build`：本轮执行
- 全量 Python 测试：修复后执行
- 独立浏览器启动：修复前已确认 15 秒后显示核心初始化超时；修复后将重新验证，不提前宣称通过。

## 边界

本轮不删除 IndexedDB 数据、不改变统一归档格式；当 IndexedDB 可用时仍优先使用 IndexedDB，只有打开失败时才使用既有 localStorage 兼容路径。
