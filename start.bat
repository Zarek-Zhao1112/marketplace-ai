@echo off
cd /d "%~dp0"
chcp 65001 >nul
title Marketplace AI

where py >nul 2>nul
if %errorlevel%==0 (
    py launcher.py
    exit /b %errorlevel%
)
where python >nul 2>nul
if %errorlevel%==0 (
    python launcher.py
    exit /b %errorlevel%
)

echo ============================================
echo  [ERROR] Python 3.10+ not found.
echo  Install from https://www.python.org/downloads/
echo  (check "Add to PATH" during install)
echo ============================================
pause
