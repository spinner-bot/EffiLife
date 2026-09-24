# Plan Helper 跨源访问契约方案

## 背景

统一工作台前端默认运行在 `127.0.0.1:1420`，Plan Helper API 运行在 `127.0.0.1:8765`。浏览器因此会把工作台对计划创建、编辑、归档、完成和导入等 JSON 请求视为跨源请求。

## 约定

- API JSON 响应统一返回 `Access-Control-Allow-Origin: *`。
- API 预检请求 `OPTIONS` 返回 `204`。
- 允许的方法为 `GET, POST, PUT, DELETE, OPTIONS`。
- 允许请求头为 `Accept, Content-Type`。
- 当前 API 不使用 Cookie 或其他凭据，因此不启用 `Access-Control-Allow-Credentials`。
- 仅对 `/api/` 路径响应预检，静态资源仍由普通静态文件服务处理。

这样既覆盖统一前端的 JSON API 调用，又不扩大静态资源路由的行为范围。
