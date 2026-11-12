@echo off
setlocal
cd /d "%~dp0"

where node >nul 2>nul
if errorlevel 1 (
  echo [EffiLife v3] Node.js was not found in PATH. Install Node 22 or newer first.
  pause
  exit /b 1
)

if not exist "node_modules" (
  echo [EffiLife v3] Installing dependencies with npm ci ...
  call npm ci
  if errorlevel 1 (
    echo [EffiLife v3] npm ci failed.
    pause
    exit /b 1
  )
)

netstat -ano | findstr ":3420" | findstr "LISTENING" >nul 2>nul
if not errorlevel 1 (
  echo [EffiLife v3] Port 3420 is already serving. Opening the app.
  start "" http://127.0.0.1:3420/
  exit /b 0
)

echo [EffiLife v3] Starting http://127.0.0.1:3420 ... close this window to stop.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep 5; Start-Process 'http://127.0.0.1:3420/'"
call npm run dev

if errorlevel 1 (
  echo [EffiLife v3] The dev server exited with an error.
  pause
)
