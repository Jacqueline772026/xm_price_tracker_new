#!/bin/bash
# 跑全部已启用的链接,结果写入 XM_Price_Checker_Python.xlsm(保存前自动备份)
cd "$(dirname "$0")/.." || exit 1
if [ ! -x .venv/bin/python ]; then
  echo "还没有安装环境,请先双击 launchers/install_mac.command"
  read -n 1 -s -r -p "按任意键关闭"; exit 1
fi
if pgrep -f "Microsoft Excel" >/dev/null; then
  echo "提醒:Excel 还开着。请先关闭 XM_Price_Checker_Python.xlsm,否则保存可能失败。"
  read -p "关闭后按回车继续(Ctrl+C 取消)"
fi
.venv/bin/python run_all.py "$@"
echo
echo "跑完了。检查报告: XM_Price_Checker_Python_check_report.txt(先看 HIGH 和 MEDIUM)"
read -n 1 -s -r -p "按任意键关闭"
