# GitHub 移动边界失败修复设计

## 背景

GitHub Actions 工作流 `EffiLife mobile boundary` 连续失败。最近一次运行中，前端依赖安装和移动端 sidecar 边界检查均成功，但 `Validate mobile command contract` 步骤失败，后续前端构建被跳过。

## 判断

工作流通过 `actions/setup-python` 配置了 Python 3.13，却没有安装 pytest。`pytest` 是仓库测试命令的运行时依赖，但不是 Python 标准库；本地环境之所以通过，是因为开发环境已经预装了 pytest。CI 缺少显式依赖安装，导致环境不可复现。

## 实施方案

1. 在移动边界工作流中增加独立的 Python 测试依赖安装步骤，显式安装 pytest。
2. 将相关 GitHub 官方 action 升级到当前 Node 运行时版本，消除已出现的 Node.js 20 弃用警告。
3. 保持移动端校验范围不变：先验证配置边界，再执行契约测试，最后构建共享前端；不引入 Android/iOS SDK，避免把未具备真实移动构建环境的问题混入本次 CI。
4. 在本地复现工作流中的测试命令和前端构建，并提交后观察 GitHub Actions 新运行结果。

## 验收标准

- `python -m pytest -q tests/test_mobile_build_scripts.py tests/test_mobile_release_config.py` 通过。
- `time-helper/desk` 执行 `npm run build` 通过。
- 推送后的 `EffiLife mobile boundary` 工作流成功，且失败通知停止。
