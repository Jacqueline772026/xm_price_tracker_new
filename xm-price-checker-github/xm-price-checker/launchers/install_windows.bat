@echo off
chcp 65001 >nul
cd /d "%~dp0.."
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
%PY% --version || (echo 没有找到 Python。请先安装 Python 3.10 或更新版本 & pause & exit /b 1)
%PY% -m venv .venv || (echo 建立环境失败 & pause & exit /b 1)
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt || (echo 安装依赖失败 & pause & exit /b 1)
.venv\Scripts\python -m playwright install chromium || (echo 安装浏览器失败 & pause & exit /b 1)
echo.
echo 安装完成。以后双击 launchers\run_windows.bat 即可。
pause
