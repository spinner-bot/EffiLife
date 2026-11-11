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
python3 v3/scripts/install-native-driver.py
python3 v3/tests/native/desktop_smoke.py
```

安装位置自动使用当前项目的 v3/.tools/tauri-driver；固定版本见 toolchain.json。测试使用独立数据目录、Xvfb 与软件渲染。以 root 运行时仅测试进程关闭 WebKit 的 Linux 进程沙箱，不能据此宣称操作系统沙箱验收通过。实际已通过的范围见阶段记录，Windows/macOS/移动端尚未实测。

版本事实源是 VERSION，更新列表见 CHANGELOG.md。实现计划见 docs/implementation-plan.md；阶段证据和当前限制记录在 docs/progress/。旧版代码保留在仓库其他目录，新版后续工作统一在本目录进行。

## 验收交付

当前为 v3.0.0 本地验收候选。[HTML 使用指南](docs/user-guide.html)覆盖完整产品动线；[桌面验收记录](docs/progress/0009-native-desktop.md)列出实际通过范围及平台边界。

准备好上述工具链后，按以下顺序重建交付：

```bash
python3 v3/scripts/run.py npm run verify
python3 v3/scripts/native.py tauri build --bundles deb
dpkg-deb -x v3/.cache/native-target/release/bundle/deb/EffiLife_3.0.0_amd64.deb v3/.cache/desktop-package
python3 v3/tests/native/desktop_smoke.py v3/.cache/desktop-package/usr/bin/effilife-desktop
python3 v3/tests/native/webkit_smoke.py
python3 v3/scripts/run.py node scripts/build-examples.mjs
python3 v3/scripts/package-delivery.py
```

打包前提交全部 v3 改动。交付工具核对版本、包内实际程序 SHA-256 与原生验收结果、生产入口与 WebKit 结果；把安装包、前端、指南、示例、依赖许可和逐文件校验和一起保存至 `.cache/delivery/`。每个提交的交付目录与 ZIP 不覆盖，ZIP 完成后再次校验全部文件。它不上传或公开发布产物。

解开交付 ZIP 后，先阅读 `docs/user-guide.html`。浏览器预览可在解压目录执行 `python3 -m http.server 3420 --bind 127.0.0.1 --directory web`，再访问 `http://127.0.0.1:3420`；不要直接以 file:// 打开前端。源码与长期验证记录以仓库提交为准。

