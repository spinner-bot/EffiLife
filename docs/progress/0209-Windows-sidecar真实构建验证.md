# 0610｜Windows Sidecar 真实构建验证

## 背景

Tauri 桌面发布配置要求先构建 `plan-helper` sidecar。此前已有构建脚本契约和 HTTP 源码测试，但仍缺少本机真实可执行产物的启动验证。

## 目标与范围

- 在当前 Windows 环境实际执行 sidecar 构建脚本。
- 使用生成的 Tauri target-suffixed exe 启动服务并检查 health endpoint。
- 不把本机生成的二进制纳入 Git；最终 Tauri 安装包仍由发布 workflow 负责验证。

## 实现与验证

执行：

```text
python scripts/build_plan_helper_sidecar.py
```

结果：PyInstaller 6.14.1 构建成功，生成：

```text
time-helper/desk/src-tauri/binaries/efflife-plan-helper-x86_64-pc-windows-msvc.exe
```

随后直接启动该 exe，传入独立临时 `--data-dir`，请求：

```text
GET /api/health
```

结果：`sidecar smoke test passed: plan-helper/ok`。

## 兼容性与限制

PH 的 legacy `plan/` 与 `data/system/registry/` 布局仍由 sidecar 运行时目录承载。当前环境没有 Rust/Cargo，因此未在本机执行 Tauri installer 构建；该项由 GitHub desktop release workflow 的矩阵任务负责，不能以本次 sidecar 验证替代。

## 提交状态

待提交。生成的 exe 位于 Tauri 忽略目录；受保护的 `time-helper/desk/package-lock.json` 与 `docs/HOTL/` 未修改、未纳入提交。
