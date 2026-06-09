@echo off
REM SPDX-License-Identifier: Apache-2.0

set "SCRIPT_DIR=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run_auto_mfa_windows.ps1"
set "AUTO_MFA_EXIT=%ERRORLEVEL%"

echo.
if not "%AUTO_MFA_EXIT%"=="0" (
    echo Auto-MFA exited with code %AUTO_MFA_EXIT%.
)
echo Press any key to close this window.
pause >nul
exit /b %AUTO_MFA_EXIT%
