# 使用说明

## 每周流程
1. **更新表格**(`XM_Price_Checker_Python.xlsm`):
   - Results 表:更新 `RRP`、`RRP after Promotion`、促销起止日期。
   - 有新机型:Products 表加一行,再生成链接(见下)。
   - 保存并**关闭 Excel**。
2. **先测 MSH**:`python run_all.py --sites MSH --dry-run`。不写表格;看底部汇总里 `errors` 是否都是 0。
3. **全部运行**:`python run_all.py`。会弹出浏览器窗口逐个网站查询,**不要手动关**。保存前自动备份成 `XM_Price_Checker_Python_backup_日期时间.xlsm`。
4. **看报告**:`XM_Price_Checker_Python_check_report.txt`。先 HIGH,再 MEDIUM,LOW 仅供参考。最终结果在 Excel 的 Results 表。

## 命令
```bash
python run_all.py                       # 全部已启用的链接
python run_all.py --sites MSH,MEX       # 只跑某些网站
python run_all.py --dry-run             # 抓取+检查,不写表格
python run_all.py --excel other.xlsm    # 使用另一个表格
python link_builder.py check XM_Price_Checker_Python.xlsm              # Links 表 vs 程序生成的链接(只读)
python link_builder.py new XM_Price_Checker_Python.xlsm <TargetID> --sites MEX,MSH   # 新机型的链接
python -m unittest tests.test_msh tests.test_price_checks tests.test_link_builder tests.test_ktr    # 离线测试
```
(Windows 把 `python` 换成 `.venv\Scripts\python`;Mac 用 `.venv/bin/python`。)

## 新机型怎么加链接
1. Products 表加一行(型号、名称、内存、存储)。
2. 运行 `link_builder.py new ...`,把输出的行粘贴到 Links 表(Enable 填 yes)。
3. 不要手写搜索词。手调过的特殊写法登记在 `link_overrides.json`。

## 检查报告怎么读
| 级别 | 含义 |
|---|---|
| HIGH | 结果很可能缺失或错误:促销价高于零售价、抓取报错、整个网站无数据… |
| MEDIUM | 可疑,看一眼网页:价格高于零售价、价格离群、链接与 Products 不一致、有货但没读到价格… |
| LOW | 仅供参考 |
促销开始日期之前抓取的旧数据会被忽略,报告开头会注明。

## PyCharm
1. File → Open,选**仓库根文件夹**。
2. 右下角添加解释器:Virtualenv → New(或 Existing,选 `.venv/bin/python`)。
3. Terminal 里 `pip install -r requirements.txt` 和 `python -m playwright install chromium`。
4. 右上角运行配置:`1 跑全部价格` / `2 只测MSH(不写表格)` / `3 检查链接` / `4 运行测试`。
遇到问题看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)。

## 不要提交的东西
真实价格表(`*.xlsm`)、备份表格、检查报告、`.venv`——均已在 `.gitignore`。仓库里只有 `templates/` 下的空白模板。
