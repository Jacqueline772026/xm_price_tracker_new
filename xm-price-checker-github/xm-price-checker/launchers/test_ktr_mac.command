#!/bin/bash
# 只跑 KTR 并且不写入表格 —— 用来快速验证 KTR 是否正常
cd "$(dirname "$0")/.." || exit 1
.venv/bin/python run_all.py --sites KTR --dry-run
read -n 1 -s -r -p "按任意键关闭"
