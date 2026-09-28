# 0373 Python 统一数据根目录配置

## 决策

`common.DataManager` 与启动器、plan-helper sidecar 共用 `EFFILIFE_DATA_DIR` 环境变量。显式构造参数仍具有最高优先级；未配置环境变量时继续使用仓库内 `common/data`，保证开发脚本和测试兼容。

## 目的

正式安装包或统一启动环境只需配置一次平台应用数据目录，Python 集成层、sidecar 和诊断工具即可共享同一数据根目录，避免数据写入位置因入口不同而分裂。
