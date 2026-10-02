# 1084 CI 启动冒烟 JSON 空白兼容修复

## 问题

主 CI 的统一工作区启动冒烟门禁连续两次失败，失败步骤均为 `Run unified workspace startup smoke check`。本地 Windows 实测通过，但 plan-helper 健康接口在不同 Python/runner 输出环境下可能返回带空格的 JSON，例如 `"service": "plan-helper"`；初版检查器只匹配紧凑形式 `"service":"plan-helper"`。

## 修复

- PH 健康检查在匹配服务身份和状态前移除所有 JSON 空白字符（包括空格和换行），兼容紧凑与格式化 JSON。
- 不放宽 HTTP 身份要求，仍必须同时包含 `service=plan-helper` 与 `status=ok`。
- 增加契约测试，锁定空白兼容逻辑。

## 证据

- 失败 run：`93df50a`、`471be24`，共同失败步骤为统一启动冒烟。
- 修复后本地冒烟检查：前端与 PH 均通过，端口释放通过。
- 修复后继续执行全量 pytest 和桌面构建；新的主 CI 负责 Ubuntu runner 复验。
