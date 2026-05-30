@echo off
setlocal
cd /d "%~dp0"

set "BOOTSTRAP_PY="

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
    if not errorlevel 1 set "BOOTSTRAP_PY=py -3"
)

if not defined BOOTSTRAP_PY (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
        if not errorlevel 1 set "BOOTSTRAP_PY=python"
    )
)

if not defined BOOTSTRAP_PY (
    echo Python 3.11 or newer was not found.
    echo Install Python from https://www.python.org/downloads/ and enable "Add python.exe to PATH".
    pause
    exit /b 1
)

%BOOTSTRAP_PY% bootstrap.py
pause
