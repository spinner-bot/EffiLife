# 0603 启动器原生壳与 sidecar 边界

## 背景

统一启动器同时服务开发浏览器、静态构建和 Tauri 原生二进制三种场景。原实现无论选择哪种前端，都为统一工作台启动外部 plan-helper API；而正式 Tauri 应用已经由应用壳管理 Plan Helper sidecar，重复启动会带来端口占用和偶发启动失败。

## 实现

- 当统一工作台命令带有浏览器 URL（Vite 开发服务器或静态服务器）时，launcher 继续管理外部 plan-helper companion。
- 当命令是原生 Tauri 二进制（无浏览器 URL）时，不再启动外部 companion，由 Tauri 应用壳负责 sidecar 生命周期。
- PH、TD 的兼容入口仍保持独立，未改变其命令或数据目录转发逻辑。

## 兼容性与发布边界

开发模式仍维持 `1420 + 8765` 的可诊断链路；正式原生桌面模式不依赖 launcher 的外部 Python 服务。静态 dist 仍属于测试/迁移 fallback，因此继续使用外部 API。

## 验证

- 新增 launcher 契约测试，验证 packaged native Tauri 只启动原生二进制且 companion 列表为空。
- 待运行 launcher 定向测试、全量 Python 测试与 GitHub CI。
