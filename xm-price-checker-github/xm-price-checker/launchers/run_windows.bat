@echo off
chcp 65001 >nul
cd /d "%~dp0.."
if not exist .venv\Scripts\python.exe (echo 还没有安装环境,请先双击 launchers\install_windows.bat & pause & exit /b 1)
echo 提醒:请先关闭 Excel 里的 XM_Price_Checker_Python.xlsm,否则保存会失败。
pause
.venv\Scripts\python run_all.py %*
echo.
echo 跑完了。检查报告: XM_Price_Checker_Python_check_report.txt (先看 HIGH 和 MEDIUM)
pause
