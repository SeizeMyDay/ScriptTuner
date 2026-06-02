@echo off
setlocal
cd /d "%~dp0"

set "BOOTSTRAP_PY="

call :try_candidate py -3
if defined BOOTSTRAP_PY goto run_bootstrap

call :try_candidate python
if defined BOOTSTRAP_PY goto run_bootstrap

call :try_candidate python3
if defined BOOTSTRAP_PY goto run_bootstrap

call :try_candidate "%SystemRoot%\py.exe" -3
if defined BOOTSTRAP_PY goto run_bootstrap

for /f "tokens=2,*" %%A in ('reg query HKCU\Software\Python\PythonCore /s /v ExecutablePath 2^>nul ^| findstr /i "ExecutablePath"') do (
    if not defined BOOTSTRAP_PY call :try_candidate "%%B"
)
if defined BOOTSTRAP_PY goto run_bootstrap

for /f "tokens=2,*" %%A in ('reg query HKLM\Software\Python\PythonCore /s /v ExecutablePath 2^>nul ^| findstr /i "ExecutablePath"') do (
    if not defined BOOTSTRAP_PY call :try_candidate "%%B"
)
if defined BOOTSTRAP_PY goto run_bootstrap

for /f "delims=" %%P in ('dir /b /s "%LocalAppData%\Programs\Python\Python3*\python.exe" 2^>nul') do (
    if not defined BOOTSTRAP_PY call :try_candidate "%%P"
)
if defined BOOTSTRAP_PY goto run_bootstrap

for /f "delims=" %%P in ('dir /b /s "%ProgramFiles%\Python3*\python.exe" 2^>nul') do (
    if not defined BOOTSTRAP_PY call :try_candidate "%%P"
)
if defined BOOTSTRAP_PY goto run_bootstrap

for /f "delims=" %%P in ('dir /b /s "%ProgramFiles(x86)%\Python3*\python.exe" 2^>nul') do (
    if not defined BOOTSTRAP_PY call :try_candidate "%%P"
)
if defined BOOTSTRAP_PY goto run_bootstrap

echo Python 3.11 or newer was not found.
echo Install Python from https://www.python.org/downloads/.
echo The launcher checks PATH, py.exe, Python registry entries, and common install folders.
pause
exit /b 1

:run_bootstrap
echo Using Python command: %BOOTSTRAP_PY%
%BOOTSTRAP_PY% bootstrap.py
pause
exit /b %errorlevel%

:try_candidate
%* -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if not errorlevel 1 set "BOOTSTRAP_PY=%*"
exit /b 0
