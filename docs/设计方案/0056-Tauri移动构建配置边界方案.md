# Tauri 移动构建配置边界方案

## 状态

- 状态：已落地配置层边界，待 Android/iOS 工具链和真机验收
- 日期：2026-09-29
- 范围：`time-helper/desk` 的 Tauri Mobile 构建入口

## 背景

EffiLife 的桌面版通过 Python Plan Helper sidecar 提供完整计划服务。移动运行时已经采用本地计划快照，并在 Rust 入口中排除了桌面 sidecar 启动逻辑。因此移动构建不应继续沿用桌面配置中的 `npm run build:sidecar` 和 `externalBin`。

## 决策

新增 `time-helper/desk/src-tauri/tauri.mobile.conf.json`，作为 Tauri Mobile 命令的显式附加配置：

- `beforeBuildCommand` 只执行 `npm run build`；
- `bundle.externalBin` 显式为空，移动包不携带桌面 Python sidecar；
- 桌面 `tauri.conf.json` 保持不变，桌面发布仍由 sidecar 构建链负责。

移动构建命令约定为在 `time-helper/desk` 目录执行：

```text
npm run tauri android build -- --config src-tauri/tauri.mobile.conf.json
npm run tauri ios build -- --config src-tauri/tauri.mobile.conf.json
```

这只是构建边界修正，不代表 Android/iOS 安装包已经验收。真实验收仍需要对应 SDK、签名配置、模拟器或真机，以及文件权限和升级迁移测试。

## 不变约束

- 移动端继续使用本地快照计划能力，不连接 `127.0.0.1:8765`；
- 桌面端继续使用统一数据根目录和 Plan Helper sidecar；
- 不删除原有桌面配置，不把移动端能力伪装成完整桌面计划服务。
