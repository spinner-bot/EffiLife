# 0754 桌面版本同步补齐 lockfile

## 发现

桌面发布版本以 `time-helper/VERSION` 为源，但同步脚本此前只更新 `package.json`、Tauri 配置和 Cargo manifest。`package-lock.json` 的根版本及其 `packages[""]` 版本可能因此滞后，形成发布元数据漂移。

## 处理

- 扩展 `scripts/sync_desktop_version.py`，在 lockfile 存在时仅更新版本字段。
- 不重新解析依赖、不改动 integrity 或依赖树，避免版本同步带来非必要的 lockfile 重写。
- 增加临时仓库测试，验证 package manifest、lockfile、Tauri 和 Cargo 四类元数据同时同步。
- 未直接修改当前工作区已有的 `time-helper/desk/package-lock.json` 用户改动。

## 验证

- 发布元数据测试：已覆盖 lockfile 同步路径。
- 后续全量 Python 测试与 GitHub Actions 作为提交前验证。
