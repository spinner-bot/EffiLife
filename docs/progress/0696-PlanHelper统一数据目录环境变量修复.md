# 1202 Plan Helper 统一数据目录环境变量修复

日期：2026-10-10  
类型：启动与数据目录边界修复

## 问题

统一启动器在设置 `EFFILIFE_DATA_DIR` 时会将数据根目录作为 `--data-dir` 参数传给 Plan Helper。但直接启动 `plan-helper/web/server.py` 时，服务此前只读取命令行参数，不读取同一环境变量，导致开发脚本或测试 companion 可能回写项目默认目录，造成数据目录分叉。

## 修复

- `run_server()` 在缺少 `--data-dir` 时读取 `EFFILIFE_DATA_DIR`。
- 命令行参数优先于环境变量，保持启动器显式参数的确定性。
- 统一数据根目录下的 registry、计划文件和归档目录继续由同一 runtime root 管理。
- 新增启动契约测试，防止环境变量路径被遗漏。

## 验证

- Plan Helper 数据目录契约测试通过。
- 后续应在真实 sidecar/安装包环境中继续验证应用数据目录和升级迁移。
