@echo off
setlocal
cd /d "%~dp0"
python -c "import PySide6" >nul 2>nul
if errorlevel 1 (
  echo PySide6 is not available in this Python environment.
  echo Install it once or run this app from an environment that already includes PySide6.
  pause
  exit /b 1
)
python app.py
