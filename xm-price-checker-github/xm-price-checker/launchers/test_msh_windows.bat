@echo off
chcp 65001 >nul
cd /d "%~dp0.."
.venv\Scripts\python run_all.py --sites MSH --dry-run
pause
