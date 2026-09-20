# 安卓移动端归档(开发暂时搁置)

> **归档日期**:2026-09-10
> **状态**:🧊 冻结 —— 待条件具备后恢复开发
> **所在分支**:安卓开发的全部提交位于 `mobile-android` 分支(领先 `main` 14 个提交);`main` 分支不含任何安卓内容

---

## 一、归档原因

Android APK 在真机上**反复出现致命闪退(启动即崩溃)**,历经 4 个版本(1.0.12 → 1.0.15)的修复尝试均无法正常运行:

| 版本 | 日期 | 修复尝试 | 结果 |
|------|------|----------|------|
| 1.0.12 | 2026-09-06 | 首次构建 APK(Tauri Mobile),存档/反馈功能移动端适配 | 启动闪退 |
| 1.0.13 | 2026-09-06 | Rust 库启用 `tauri/custom-protocol` 特性内嵌前端资源;改用 debug 密钥签名 | 仍闪退 |
| 1.0.14 | 2026-09-07 | 添加崩溃日志捕获(panic 时写入 crash.log);修复 Windows cargo 链接器配置 | 仍闪退,且 crash.log 未捕获到有效信息 |
| 1.0.15 | 2026-09-07 | 构建时手动将 `dist/` 复制到 Android assets 目录 | 仍闪退 |

**关键限制**:测试手机**未开启安卓开发者模式**(USB 调试 / logcat 不可用),导致:

1. 无法通过 `adb logcat` 获取启动崩溃的原生堆栈,定位不到崩溃点;
2. Rust 侧的 panic 捕获(crash.log)也未产出日志,说明崩溃大概率发生在 **Rust 初始化之前的原生/WebView 层**(Gradle 打包产物、AndroidManifest、系统 WebView 兼容性等环节),应用层代码无从介入;
3. 只能进行"盲改"(内嵌资源、签名方式、手动复制 assets),反复测试无效。

在缺少调试手段的前提下继续投入产出比过低,故决定**暂时搁置安卓开发**,将相关内容整体隔离归档,主项目回归桌面端(Windows)开发。

---

## 二、归档内容清单

| 归档路径 | 原位置 | 说明 |
|----------|--------|------|
| `gen-android/` | `desk/src-tauri/gen/android/` | 完整 Android 工程(Gradle 项目、MainActivity.kt、资源、图标等) |
| `apk/浪兮效率时钟_v1.0.14_arm64.apk` | 项目根目录 | v1.0.14 构建产物(未签名) |
| `apk/浪兮效率时钟_v1.0.15_arm64.apk` | 项目根目录 | v1.0.15 构建产物(最后一次尝试) |
| `apk/*.idsig`(3 个) | 项目根目录 | v1.0.12 / v1.0.15 的 APK 签名校验文件 |
| `cargo-config.toml` | `desk/src-tauri/.cargo/config.toml` | Android 四个 target 的交叉编译链接器配置(NDK 路径为 `D:/dev-tools/android-sdk/ndk/25.2.9519653`,恢复时需按实际环境调整) |
| `MOBILE_SETUP.md` | 项目根目录 | 移动端开发指南(环境要求、Windows 分步构建 APK 的完整流程) |

**体积说明**:`gen-android/` 共约 161M,其中 `app/build/`(~110M)和 `.gradle/`(~4M)为 Gradle 可再生构建产物,**如需精简归档体积可直接删除这两个目录**,不影响工程恢复。

---

## 三、保留在主项目中的内容(未归档)

以下移动端适配代码保留在 `desk/` 源码中,对桌面版运行**无任何影响**,恢复开发时可直接复用:

- `desk/src/services/ArchiveService.ts` —— `isMobile()` 检测,移动端存档回退为浏览器下载方式
- `desk/src/views/SettingsView.vue` —— 移动端反馈使用 `mailto:` 协议
- `desk/src-tauri/src/lib.rs` —— 崩溃日志处理器(panic hook 写 crash.log,属通用代码)
- `desk/src-tauri/Cargo.toml` —— `crate-type` 中的 `cdylib`/`staticlib`(移动端动态库所需,保留无害)

---

## 四、如何恢复开发

### 1. 还原文件到原位置

```bash
git mv archive/android/gen-android desk/src-tauri/gen/android
mkdir -p desk/src-tauri/.cargo
git mv archive/android/cargo-config.toml desk/src-tauri/.cargo/config.toml
git mv archive/android/MOBILE_SETUP.md MOBILE_SETUP.md
# APK 产物按需还原到根目录(或保持归档)
```

还原后,或直接在 `desk/` 下重新执行 `npm run tauri android init` 重新生成工程(将丢失已做的手动修改,不推荐)。

### 2. 环境准备

见 `MOBILE_SETUP.md`:JDK 17+、Android SDK/NDK(`JAVA_HOME`、`ANDROID_HOME`、`NDK_HOME`),并按本机实际路径修正 `cargo-config.toml` 中的 NDK 链接器路径。

### 3. 恢复后优先排查方向(重要)

上一轮失败的根本教训是**没有日志、盲改**。恢复开发时请优先解决调试手段:

1. **开启开发者模式 + USB 调试**,用 `adb logcat` 捕获启动崩溃的完整堆栈 —— 这是定位问题的前提,没有它不建议继续尝试修复;
2. 先用 **Android Studio 模拟器**复现问题,排除真机特有因素(系统 WebView 版本、厂商 ROM 限制);
3. 核对 `tauri.conf.json` 的 `frontendDist` 配置与 Tauri 2 Mobile 的资源打包约定是否一致;
4. 检查 `AndroidManifest.xml` 权限与 WebView 兼容性(崩溃发生在 Rust 初始化之前,重点怀疑原生层);
5. Windows 构建绕过方案(Tauri CLI `rustBuildArm64Release` 崩溃)参考:https://github.com/tauri-apps/tauri/issues/6502

---

## 五、相关历史记录

- 开发过程完整记录见根目录 `CHANGELOG.md` 的 1.0.12 ~ 1.0.15 条目
- 本分支(`mobile-android`)提交历史:`git log main..mobile-android --oneline`
