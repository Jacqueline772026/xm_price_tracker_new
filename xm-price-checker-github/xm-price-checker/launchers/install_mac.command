#!/bin/bash
# 第一次使用只需要运行一次:建立独立环境 + 安装依赖 + 安装 Chromium 浏览器
cd "$(dirname "$0")/.." || exit 1
PY=$(command -v python3)
if [ -z "$PY" ]; then
  echo "没有找到 python3。请先安装 Python 3.10 或更新版本: https://www.python.org/downloads/"
  read -n 1 -s -r -p "按任意键关闭"; exit 1
fi
echo "使用 Python: $($PY --version)"
$PY -m venv .venv || { echo "建立环境失败"; read -n 1 -s -r -p "按任意键关闭"; exit 1; }
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt || { echo "安装依赖失败"; read -n 1 -s -r -p "按任意键关闭"; exit 1; }
.venv/bin/python -m playwright install chromium || { echo "安装浏览器失败"; read -n 1 -s -r -p "按任意键关闭"; exit 1; }
echo
echo "安装完成。以后双击 launchers/run_mac.command 即可。"
read -n 1 -s -r -p "按任意键关闭"
