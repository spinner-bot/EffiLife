# EffiLife v3

面向个人持续生活管理，以时间和事件两条主线关联实际行动，保留主题计划、进展日志与零散待办的独立价值。

## 开发与验证

在仓库根执行：

```bash
python3 v3/scripts/run.py npm install
python3 v3/scripts/run.py npm run dev
python3 v3/scripts/run.py npm test
python3 v3/scripts/run.py npm run build
```

首次执行从 Node 官方源下载并校验独立工具链，存放 v3/.tools/，不改系统 Node。锁文件建立后采用 npm ci 安装。开发入口为 http://127.0.0.1:3420。

版本事实源是 VERSION，更新列表见 CHANGELOG.md。实现计划见 docs/implementation-plan.md；阶段证据和当前限制记录在 docs/progress/。旧版代码保留在仓库其他目录，新版后续工作统一在本目录进行。

当前状态：正式重构开发中。已完成能力以 CHANGELOG 与验证记录为准。

