@echo off
cd /d "%~dp0.."
if defined EFFILIFE_PYTHON (
    if not exist "%EFFILIFE_PYTHON%" (
        echo EFFILIFE_PYTHON does not exist: %EFFILIFE_PYTHON% 1>&2
        exit /b 127
    )
    "%EFFILIFE_PYTHON%" launcher\start.py --unified %*
    goto :finish
)

where py >nul 2>nul
if errorlevel 1 goto :use_python
py -3 -c "import sys" >nul 2>nul
if errorlevel 1 goto :use_python
py -3 launcher\start.py --unified %*
goto :finish

:use_python
python launcher\start.py --unified %*

:finish
set "EFFILIFE_LAUNCH_EXIT=%errorlevel%"
if /i not "%EFFILIFE_NO_PAUSE%"=="1" pause
exit /b %EFFILIFE_LAUNCH_EXIT%
