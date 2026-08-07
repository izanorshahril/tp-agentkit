@echo off
setlocal EnableExtensions

REM Runs ls_updater.py using uv.
REM - With args: forwards args to the python script (non-interactive mode supported)
REM - No args: runs interactive mode in the CURRENT directory
REM
REM NOTE: This script intentionally does NOT cd into the script folder so that
REM ls_updater.py's auto-detection looks in the caller's current directory.

set "SCRIPT_DIR=%~dp0"
set "PY_FILE=%SCRIPT_DIR%ls_updater.py"

if not exist "%PY_FILE%" goto :MissingPy

where uv >nul 2>&1
if errorlevel 1 (
	set "RUNNER=python"
) else (
	set "RUNNER=uv run -- python"
)

if "%~1"=="" goto :Interactive
goto :RunWithArgs

:Interactive
echo [INFO] No arguments provided. Running in interactive mode...
%RUNNER% "%PY_FILE%"
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
	pause
	exit /b %EXITCODE%
)
pause
exit /b 0

:RunWithArgs
%RUNNER% "%PY_FILE%" %*
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
	pause
	exit /b %EXITCODE%
)
pause
exit /b 0

:MissingPy
echo [ERROR] Could not find ls_updater.py next to this script.
pause 1
exit /b 1

:MissingPy
echo [ERROR] Could not find ls_updater.py next to this script.
pause 1
exit /b 1
