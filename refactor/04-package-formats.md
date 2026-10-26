# 04 扩展包格式

## 1. 四类包

| 类型 | 扩展名（暂定） | 用途 | 可执行内容 | 默认权限 |
|---|---|---|---|---|
| 数据包 | `d3el` | 存档、导入导出、备份 | 否 | 导入需用户确认 |
| 资源包 | `r3el` | 字体、图片、纹理、音频、语言资源 | 否 | L0 |
| 主题包 | `t3el` | 皮肤、token、装饰层、CSS/JS、可选布局 | 按权限 | L0 |
| 功能包 | `f3el` | 扩展功能、自动化、复杂交互 | 是 | L2 起，具体待定 |

数据包兼容旧 `.efl`：新版本默认导出 `d3el`，导入同时接受 `.efl`，直到明确的弃用版本。

## 2. 扩展名必须集中配置

不把 `d3el` / `r3el` / `t3el` / `f3el` 写死在各处。建议唯一事实源：

```json
// shared/package-formats.json（规划路径）
{
  "formats": {
    "data":     { "current": "d3el", "accepted": ["d3el", "efl"], "mime": "application/x-effilife-data" },
    "resource": { "current": "r3el", "accepted": ["r3el"],         "mime": "application/x-effilife-resource" },
    "theme":    { "current": "t3el", "accepted": ["t3el"],         "mime": "application/x-effilife-theme" },
    "function": { "current": "f3el", "accepted": ["f3el"],         "mime": "application/x-effilife-function" }
  },
  "formatVersion": 1
}
```

要求：

- TypeScript、Python、Rust 都从同一文件读取或由构建步骤生成常量；
- 文件对话框过滤器、导出默认名、导入校验、测试全部引用常量；
- 测试断言：除该文件外不得出现这些扩展名字面量；
- 修改扩展名只改这一处；`accepted` 保留旧值，保证旧包继续可导入；
- 扩展名大小写不敏感匹配，导出统一使用小写。

## 3. 通用容器

四类包统一为 ZIP（deflate）压缩包。建议结构：

```
manifest.json          必需：身份、类型、版本、兼容范围、权限、入口
payload/               类型数据（或 manifest 指定的根级文件）
assets/                本地资源
signature/             可选：签名与校验和
```

主题包为作者方便，允许把 `tokens.json` / `layers.json` / `motion.json` / `styles/` / `scripts/` / `layout.json` 放在根目录，由 manifest 声明路径。

### manifest 通用字段

```json
{
  "type": "theme",
  "name": { "zh-CN": "极光", "en": "Aurora" },
  "version": "1.0.0",
  "formatVersion": 1,
  "apiVersion": 1,
  "minAppVersion": "3.0.0",
  "permissions": ["l0", "l1"],
  "author": "...",
  "license": "MIT",
  "homepage": "...",
  "description": { "zh-CN": "...", "en": "..." },
  "preview": "preview.webp",
  "entrypoints": {},
  "checksums": {},
  "signature": null,
  "slug": "aurora"
}
```

- **0–99999（系统自带/系统可选/云端）**：包可以携带稳定 `id`；安装时校验区段与来源，沿用该 ID。
- **100000–999999（本地导入）**：包不得携带 `id`；由注册表动态分配（见 09）。
- `slug` 可选，仅用于更新识别，不作为身份；缺失时按名称+作者匹配。

### 类型专属字段

- **d3el**：`schemaVersion`、`exportedAt`、`dataFiles`、`appVersion`。
- **r3el**：`resources[]`（`kind`、`path`、`alias`、`license`）。
- **t3el**：`tokens`、`layers`、`motion`、`styles`、`scripts`、`layout`、`optionsSchema`、`extends`。
- **f3el**：`entry`、`capabilities[]`、`permissions[]`、`dependencies[]`。

## 4. 安全不变量

即使暂时不设包体积上限，以下结构性校验仍建议保留：

| 风险 | 处理 |
|---|---|
| 路径穿越 | 拒绝绝对路径、`..`、盘符路径 |
| 符号链接 | 拒绝 |
| 大小写冲突 | 拒绝同名不同大小写条目 |
| ZIP 炸弹 | 即使不设总大小上限，也限制条目数与压缩比异常 |
| 外部资源 | 默认禁止 `http(s)://`、`@import`、外部 `url()` |
| 可执行内容 | 只在沙箱运行；按权限启用 |
| 完整性 | 可选校验和/签名；内置包与第三方包区分信任级别 |
| 解压位置 | 只写入应用数据目录下的受控路径 |

“不设大小限制”与上述结构安全校验是两件事，见 07 待确认。

## 5. 生命周期

1. 选择文件 → 读取 manifest
2. 校验格式、兼容性、结构安全
3. 展示作者、版本、许可、声明权限、预览
4. 用户确认安装与授权
5. 安装到应用数据目录（内置包除外）
6. 启用：解析器加载，失败则禁用并说明原因
7. 升级：按注册表 ID + 版本替换，保留用户 options；更新识别规则见 09
8. 卸载：删除包与缓存，回退到默认主题/资源

## 6. 版本维度

| 版本 | 含义 |
|---|---|
| 包 `version` | 内容版本（作者维护） |
| `formatVersion` | 容器与 manifest 结构版本 |
| `apiVersion` | 宿主能力/主题 DSL 版本 |
| `minAppVersion` / `maxAppVersion` | 与 EffiLife 主版本的兼容范围 |

应用 3.0.0 时主题 API 建议从 `apiVersion: 1` 开始，不与应用版本绑定。

## 7. 待确认

- MIME 类型是否按上表固定；
- 是否启用签名与校验和；
- 功能包与主题包是否共用权限模型；
- 功能包是否允许依赖其他包；
- `.efl` 的兼容期限；
- 资源包是否可以被主题/功能包引用，以及引用方式。
