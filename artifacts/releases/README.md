# 本地发布产物

此目录用于收纳本机生成或临时取得的安装包、便携版和测试发布文件，避免二进制产物散落在仓库根目录。

发布产物默认被 `.gitignore` 忽略；正式版本应通过 `.github/workflows/tauri-desktop-release.yml` 生成并从 CI 产物下载，不应把本机二进制直接提交到源码仓库。
