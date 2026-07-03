@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" main.py
) else (
    echo Virtual environment not found. Please run install first.
    pause
)
# by denchir