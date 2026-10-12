# 0799 发布 Manifest 内容校验门禁

## 问题

发布工作流此前会生成并上传 manifest，但没有在生成后重新读取并校验文件内容。若构建目录在生成后变化，或 manifest 被错误修改，CI 仍可能继续发布不一致的元数据。

## 调整

- 新增 `scripts/verify_release_manifest.py`；
- 校验 schema、产品名、版本、target、相对路径、文件大小和 SHA-256；
- 桌面、Android、iOS 工作流均在生成 manifest 后立即执行校验；
- 发布配置预检与单元测试覆盖该门禁。

## 验证

- 篡改文件和路径穿越均会使校验失败；
- 真实平台构建仍需在对应 runner 上执行。
