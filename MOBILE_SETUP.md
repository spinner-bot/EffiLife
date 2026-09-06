# 浪兮效率时钟 - 移动端开发指南

## 环境要求

### 必需软件

1. **Java JDK 17+**
   - 下载：https://www.oracle.com/java/technologies/downloads/
   - 设置环境变量 `JAVA_HOME`

2. **Android Studio**
   - 下载：https://developer.android.com/studio
   - 安装时勾选 Android SDK 和 Android NDK

3. **环境变量配置**
   ```bash
   # Windows (PowerShell)
   $env:JAVA_HOME = "C:\Program Files\Java\jdk-17"
   $env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
   $env:NDK_HOME = "$env:ANDROID_HOME\ndk\25.2.9519653"  # 版本号可能不同
   
   # 添加到 PATH
   $env:PATH += ";$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools"
   ```

### 验证安装

```bash
java --version       # 应该显示 17+
adb --version        # Android Debug Bridge
```

## 初始化 Android 项目

```bash
cd desk
npm run tauri android init
```

这会创建 `src-tauri/gen/android/` 目录，包含 Android 项目文件。

## 开发模式

### 连接设备

1. **模拟器**：在 Android Studio 中启动模拟器
2. **真机**：
   - 开启开发者选项 → USB 调试
   - 用 USB 连接电脑
   - 运行 `adb devices` 确认设备已连接

### 运行

```bash
npm run tauri android dev
```

首次构建需要下载依赖，可能需要 5-10 分钟。

## 构建 APK

### 重要：Windows 构建需要分步执行

由于 Tauri CLI 在 Windows 上的已知问题（`rustBuildArm64Release` 任务崩溃），
需要手动分离 Rust 编译和 Gradle 打包步骤：

```bash
# 步骤 1：构建前端
npm run build

# 步骤 2：编译 Rust 库（如果还没编译）
cargo build --release --lib --features tauri/custom-protocol --target aarch64-linux-android

# 步骤 3：复制 .so 文件到 Android 项目
mkdir -p src-tauri/gen/android/app/src/main/jniLibs/arm64-v8a
cp src-tauri/target/aarch64-linux-android/release/libefflife_desk_lib.so \
   src-tauri/gen/android/app/src/main/jniLibs/arm64-v8a/

# 步骤 4：复制前端资源到 Android assets（关键！否则闪退）
rm -rf src-tauri/gen/android/app/src/main/assets/*
cp -r dist/* src-tauri/gen/android/app/src/main/assets/

# 步骤 5：设置环境变量
export JAVA_HOME="/d/dev-tools/jdk-17.0.2"
export ANDROID_HOME="/d/dev-tools/android-sdk"
export NDK_HOME="/d/dev-tools/android-sdk/ndk/25.2.9519653"

# 步骤 6：执行 Gradle 打包，跳过 Rust 构建任务
cd src-tauri/gen/android
./gradlew assembleArm64Release \
  -x rustBuildArm64Release \
  -x rustBuildArmRelease \
  -x rustBuildX86Release \
  -x rustBuildX86_64Release \
  -x rustBuildUniversalRelease \
  --no-daemon \
  -Pkotlin.incremental=false
```

**注意：** 步骤 4 是必须的！跳过 Rust 构建任务意味着前端资源不会被自动打包，
必须手动复制 `dist/` 到 Android assets 目录，否则应用启动时会闪退。

输出位置：`src-tauri/gen/android/app/build/outputs/apk/arm64/release/`

### 注意

- APK 默认为未签名版本（`-unsigned.apk`），可直接用于测试安装
- 如需发布到应用商店，需要配置签名密钥
- 参考：https://github.com/tauri-apps/tauri/issues/6502

## 已知问题

- 文件对话框在移动端使用浏览器下载方式
- 邮件反馈使用 `mailto:` 协议
- 所有 UI 和逻辑与桌面版保持一致

## 平台检测代码

```typescript
// 检测移动端
function isMobile(): boolean {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

// 检测 Tauri 环境
function isTauri(): boolean {
  return !!(window as any).__TAURI__
}
```

## 后续优化（可选）

- [ ] 推送通知
- [ ] 手势操作
- [ ] 原生分享
- [ ] 生物识别解锁
