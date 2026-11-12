@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

where node >nul 2>nul
if errorlevel 1 (
  echo [浪兮效率 EffiLife] 未在 PATH 中找到 Node.js，请先安装 Node 22 或更新版本。
  pause
  exit /b 1
)

if not exist "node_modules" (
  echo [浪兮效率 EffiLife] 正在安装依赖：npm ci ...
  call npm ci
  if errorlevel 1 (
    echo [浪兮效率 EffiLife] npm ci 失败。
    pause
    exit /b 1
  )
)

netstat -ano | findstr ":3420" | findstr "LISTENING" >nul 2>nul
if not errorlevel 1 (
  echo [浪兮效率 EffiLife] 3420 端口已在提供服务，直接打开应用。
  start "" http://127.0.0.1:3420/
  exit /b 0
)

echo [浪兮效率 EffiLife] 正在启动 http://127.0.0.1:3420 ... 关闭此窗口即可停止。
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep 5; Start-Process 'http://127.0.0.1:3420/'"
call npm run dev

if errorlevel 1 (
  echo [浪兮效率 EffiLife] 开发服务器异常退出。
  pause
)
