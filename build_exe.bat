@echo off
@chcp 65001 >nul 2>&1
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Luna Dimmer - Build System

REM Check Python Environment
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    goto :RUN_BUILD
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=py -3"
    goto :RUN_BUILD
)

echo.
echo ================================================================
echo [ERROR] Python environment not found in PATH!
echo [错误] 未在系统环境中找到 Python 运行环境！
echo.
echo 请确保已在电脑上安装 Python 3.8+，并在安装时勾选了：
echo "Add python.exe to PATH" (添加 Python 至系统环境变量)。
echo ================================================================
echo.
pause
exit /b 1

:RUN_BUILD
%PYTHON_EXE% scripts\builder.py %*
if %errorlevel% neq 0 (
    echo.
    echo ================================================================
    echo [ERROR] Build process failed. Please check output logs above.
    echo [错误] 构建未能完成，请向上翻阅检查详细日志。
    echo ================================================================
    echo.
    if not "%1"=="nopause" pause
    exit /b 1
)

endlocal
