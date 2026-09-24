# to-dos 兼容入口构建契约方案

**文档性质**：工程构建修复方案  
**创建时间**：2026-09-25（Asia/Shanghai）

## 问题

旧 to-dos Web 的根 TypeScript 配置把 `vite.config.ts` 同时纳入 noEmit 项目，又引用了一个同样 noEmit 且未启用 composite 的 Node 项目，导致 `vue-tsc` 直接报 TS6305、TS6306、TS6310。

## 决策

- 根应用项目只检查 `src`，保持 noEmit。
- Vite 配置使用独立的 composite 项目，并将生成物输出到 `node_modules/.vite-tsc`，不污染源代码目录。
- 兼容入口继续保留独立 package，便于迁移期运行和验证。
