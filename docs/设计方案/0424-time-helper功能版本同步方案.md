# time-helper 功能版本同步方案

## 背景

统一工作台在 `1.6.1` 之后增加了首页待办与计划双向入口、创建计划首个行动以及正式桌面发布汇总。若继续沿用旧版本号，安装包、启动器诊断和 README 无法准确表达能力边界。

## 方案

- 将 `time-helper` 版本从 `1.6.1` 升至 `1.7.0`，表示向后兼容的统一工作台功能扩展。
- 以 `time-helper/VERSION` 作为桌面发布版本源，使用既有同步脚本更新 `package.json`、Tauri 配置和 Cargo crate。
- 在 `time-helper/CHANGELOG.md` 记录本轮统一工作台与发布链路变化。
- README 版本表同步到 `1.7.0`；不修改用户已有的 `package-lock.json` 本地变更。
- `plan-helper` 与 `to-dos` 本轮没有内部模块发布变化，保持各自版本。

## 验收

- 发布配置预检确认四个桌面元数据版本一致。
- README 版本契约、版本元数据测试和全量 Python 测试通过。
