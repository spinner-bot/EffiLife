# 0796 正式 Release 元数据发布门禁

## 复核结论

桌面 tag 发布任务会等待兼容 UI 与四个平台构建，下载各构建 artifact，并把安装包、SHA-256 文件和机器可读 manifest 一起传给 `gh release create`。

## 调整

- 发布配置预检现在明确要求 release manifest 生成步骤；
- 契约测试明确检查 manifest/checksum 会随 installer artifact 下载并进入正式 Release；
- 不改变 tag 版本匹配、四平台矩阵或发布权限边界。

## 验证

- 本地 release metadata、checksum 与 artifact 测试通过后再运行全量回归；
- 真实 tag 发布仍需使用匹配 `time-helper/VERSION` 的 tag 执行。
