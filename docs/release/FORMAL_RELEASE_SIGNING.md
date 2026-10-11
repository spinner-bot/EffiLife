# EffiLife 正式发布签名配置

本文档描述 GitHub Actions 的正式签名边界。证书、keystore、密码和别名只能配置在 GitHub Secrets，不得写入仓库、进展报告或 workflow 明文。

## 总开关

在仓库 Settings → Secrets and variables → Actions → Variables 中设置：

```text
EFFILIFE_FORMAL_RELEASE_ENABLED=true
```

默认不设置或设置为其他值时：

- Windows workflow 只生成内部验收安装包，不创建公开 GitHub Release。
- Android workflow 只生成 unsigned 内部 APK。
- checksums 和 manifest 仍用于内部产物验收。

## Windows NSIS

配置以下 Secrets：

```text
EFFILIFE_WINDOWS_CERT_BASE64      # PFX/PKCS#12 文件的 base64 内容
EFFILIFE_WINDOWS_CERT_PASSWORD    # PFX 密码
```

正式 workflow 会使用 Windows SDK 的 `signtool.exe`：

1. 构建 NSIS 安装包。
2. 将 PFX 写入 runner 临时目录。
3. 使用 SHA-256 和时间戳签名。
4. 执行 `signtool verify /pa`。
5. 删除临时 PFX。
6. 只在签名成功后生成 checksum、manifest 和公开 Release。

## Android APK

配置以下 Secrets：

```text
EFFILIFE_ANDROID_KEYSTORE_BASE64       # release keystore 的 base64 内容
EFFILIFE_ANDROID_KEYSTORE_PASSWORD     # keystore 密码
EFFILIFE_ANDROID_KEY_ALIAS              # release key alias
EFFILIFE_ANDROID_KEY_PASSWORD           # key 密码
```

正式 workflow 会使用 Android SDK 的 `zipalign` 和 `apksigner`：

1. 构建 unsigned APK。
2. 写入 runner 临时 keystore。
3. 对齐并签名 APK。
4. 执行 `apksigner verify`。
5. 删除 unsigned 输入和临时 keystore。
6. 只对最终签名 APK 生成 checksum 和 manifest。

## 安全检查

- 不要在日志中打印 Secret 环境变量。
- 不要把 keystore、PFX、密码或解码后的临时文件提交仓库。
- 首次配置后先使用 workflow artifact 验证，再创建匹配 `time-helper/VERSION` 的 tag。
- 当前项目暂不配置 iOS 签名；iOS 端仍按项目边界延期。
