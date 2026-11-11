# EffiLife v3

面向个人持续生活管理，以时间和事件两条主线关联实际行动，保留主题计划、进展日志与零散待办的独立价值。

## 开发与验证

在仓库根执行：

```bash
python3 v3/scripts/run.py npm ci
python3 v3/scripts/run.py npm run dev
python3 v3/scripts/run.py npm run verify
```

首次执行从 Node 官方源下载并校验独立工具链，存放 v3/.tools/，不改系统 Node。npm ci 使用锁文件及完整性校验；安装入口内置 Python HTTPS 转发，适配本工作站的网络。开发入口为 http://127.0.0.1:3420。

首次准备浏览器测试时执行 `python3 v3/scripts/install-browser.py`。verify 依次运行领域/存储测试、类型和版本检查、生产构建与真实 Chromium 测试。测试会重新建立 test-results，请先保存需要留存的原生验收结果。

## Linux 桌面构建

下列准备流程适用于当前 Ubuntu x86_64 工作站；工具和 SDK 仅写入 v3/，不执行系统软件包安装。

```bash
python3 v3/scripts/install-rust.py
python3 v3/scripts/install-native-sdk.py
python3 v3/scripts/native.py info
python3 v3/scripts/native.py tauri build --debug --no-bundle
python3 v3/tests/native/webkit_smoke.py
```

debug 程序位于 `.cache/native-target/debug/effilife-desktop`。生产 Linux 包使用 `python3 v3/scripts/native.py tauri build --bundles deb`，产物位于 `.cache/native-target/release/bundle/deb/`。本地 SDK 是构建/验收环境；安装目标机仍需要包中声明的 GTK/WebKit 系统依赖。

实际 Tauri 窗口测试另外使用固定的原生驱动：

```bash
python3 v3/scripts/native.py cargo install tauri-driver --version 2.1.0 --locked --root /data/Users/zrh/repo/EffiLife/v3/.tools/tauri-driver
python3 v3/tests/native/desktop_smoke.py
```

其他工作站将安装路径替换为自己的 v3/.tools/tauri-driver；固定版本见 toolchain.json。测试使用独立数据目录、Xvfb 与软件渲染。以 root 运行时仅测试进程关闭 WebKit 的 Linux 进程沙箱，不能据此宣称操作系统沙箱验收通过。实际已通过的范围见阶段记录，Windows/macOS/移动端尚未实测。

版本事实源是 VERSION，更新列表见 CHANGELOG.md。实现计划见 docs/implementation-plan.md；阶段证据和当前限制记录在 docs/progress/。旧版代码保留在仓库其他目录，新版后续工作统一在本目录进行。

当前状态：正式重构开发中。已完成能力以 CHANGELOG 与验证记录为准。

