# 0664：GitHub Actions 失败初步诊断

## 背景

用户反馈持续收到 GitHub Actions run failure 通知，需要先区分仓库代码失败、工作流环境失败和历史运行重复通知。当前未获得邮件中的具体 run 链接或 job 日志，GitHub Actions API 也因远端限流返回 403。

## 已检查范围

- `.github/workflows/ci.yml`
- `.github/workflows/tauri-mobile-boundary.yml`
- `.github/workflows/tauri-desktop-release.yml`
- 桌面端依赖安装与构建契约
- `to-dos` 兼容 UI 依赖安装与构建
- 受保护工作区文件状态

## 结果

- 普通 `main` 推送会触发主 CI；移动端边界工作流按路径触发。
- 桌面安装包发布工作流只由手动触发或 `v*` tag 触发，不应由普通代码推送触发。
- 桌面端 `npm ci --dry-run --ignore-scripts` 成功。
- `to-dos/ui` 的 `npm ci --dry-run --ignore-scripts` 与 `npm run build` 成功。
- `python scripts/check_release_config.py` 成功。
- `python scripts/check_mobile_release_config.py` 成功。
- GitHub API 请求返回 403，当前无法读取具体失败 job 的错误行。

## 结论与后续

当前本地证据不足以证明最近提交导致工作流失败。需要邮件中的 Actions run URL、run 编号或失败 job 的最后一段日志，才能进行定点修复；不能仅凭“run fail”通知修改发布流程。

受保护的 `time-helper/desk/package-lock.json` 与 `docs/HOTL/` 未被提交或修改。

## 提交状态

本报告随诊断提交；未修改工作流配置。
