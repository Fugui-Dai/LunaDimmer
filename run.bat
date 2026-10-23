@echo off
title Luna Dimmer
echo Starting Luna Dimmer...
python -m src.main
if %errorlevel% neq 0 (
    echo.
    echo Failed to start Luna Dimmer. Make sure dependencies are installed:
    echo pip install -r requirements.txt
    pause
)
