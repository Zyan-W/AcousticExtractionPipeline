@echo off
rem SPDX-License-Identifier: Apache-2.0

set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run_auto_mfa_windows_offline.ps1" %*
if errorlevel 1 (
    echo.
    echo Auto-MFA offline launcher failed.
    pause
    exit /b %errorlevel%
)
