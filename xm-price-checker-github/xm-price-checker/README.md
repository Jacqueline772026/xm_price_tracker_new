# XM Price Checker

每周检查小米(Xiaomi)手机和平板在波兰各零售商的价格与库存,并和"促销后建议零售价(RRP after Promotion)"对比,生成报告。
Weekly competitor price check for Xiaomi phones/tablets across Polish retailers (MediaMarkt, Media Expert, Avans, Electro, RTV Euro AGD alternatives…), driven by an Excel workbook and Playwright scrapers.

> 原始工具由同事 **Garlie Li** 开发。之后增加了:MSH(MediaMarkt)修复、统一的名称/价格匹配、自动检查报告、链接自动生成、一条命令运行、测试。详见 [docs/CHANGES.md](docs/CHANGES.md)。

## 流程 / How it works
```
Excel (Products / Links / Results)
   → run_all.py → run_price_check.py (one subprocess per link) → scrapers/<site>.py (Playwright)
   → RawData → price_checks.py (自动检查报告) → Results sheet
```
- `scrapers/matching.py`:机型名/4G-5G/价格/卖家的共用匹配规则(有单元测试)。
- `price_checks.py`:每次运行后的自动检查(缺数据、促销价高于零售价、价格离群、链接与 Products 不一致…)。
- `link_builder.py`:由 Products 表自动生成搜索链接,不手写。

## 快速开始 / Quick start
需要 Python 3.9+ 和 Google Chrome。

1. **准备表格**:把 `templates/XM_Price_Checker_Python.template.xlsm` 复制到项目根目录,改名为 `XM_Price_Checker_Python.xlsm`,在 Results 表填入本周的 RRP、`RRP after Promotion` 和促销起止日期。**真实价格表不要提交到 Git**(已在 `.gitignore` 中)。
2. **安装(一次)**
   - Mac:双击 `launchers/install_mac.command`  ·  Windows:`launchers\install_windows.bat`
   - 或命令行:
     ```bash
     python3 -m venv .venv
     .venv/bin/pip install -r requirements.txt        # Windows: .venv\Scripts\pip
     .venv/bin/python -m playwright install chromium   # 下载不动时会自动改用本机 Chrome/Edge
     ```
3. **先测 MSH(不写表格)**:`python run_all.py --sites MSH --dry-run`(或双击 `launchers/test_msh_*`)
   (只测 KTR:`python run_all.py --sites KTR --dry-run`,或双击 `launchers/test_ktr_*`)
4. **全部运行**:`python run_all.py`(或双击 `launchers/run_*`)。运行前先关闭 Excel。
5. 先看 `XM_Price_Checker_Python_check_report.txt`,只处理 HIGH / MEDIUM;结果在 Excel 的 Results 表。

PyCharm:打开**仓库根文件夹**,解释器选项目 `.venv`,右上角运行配置里有"1 跑全部价格 / 2 只测MSH / 3 检查链接 / 4 运行测试"。详见 [docs/USAGE.md](docs/USAGE.md)。

## 文档 / Docs
| 文件 | 内容 |
|---|---|
| [docs/USAGE.md](docs/USAGE.md) | 每周使用流程、命令、新机型怎么加链接、PyCharm 用法 |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | 安装/PyCharm/浏览器/保存/结果不对 的排错 |
| [docs/CHANGES.md](docs/CHANGES.md) | 改动记录和已知限制 |
| [skill/](skill/xm-price-checker-weekly/) | 给 Claude 用的技能说明(可忽略) |

## 业务规则 / Business rules
- **MSH 只统计官方店**。卡片上写 `Sprzedaż i wysyłka przez XX`(XX 不是 MediaMarkt)的是第三方,排除;没有卖家字样视为官方。
- 机型要对但不要太严:`RM` = Redmi;标题没写 5G 不算不匹配;只有明确冲突(5G ↔ 4G/LTE)才排除;Products 里同时有 4G/5G 同名机型时才严格区分。Pro / Max / Ultra / Lite 后缀永远区分机型。
- 价格只取当前售价,不取划线价、最低价、分期价、翻新价。

## 测试 / Tests
```bash
python -m unittest tests.test_msh tests.test_price_checks tests.test_link_builder tests.test_ktr   # 见 docs/USAGE.md
```
(离线,不访问网站。`tests/test_msh_browser.py` 需要本机 Chrome,手动运行。)

## 已知限制
- 除 MSH 外的 7 个网站(MEX、Electro、Avans、KTR、XKOM、Neonet、Max electro)仍是原作者的识别逻辑,尚未重新梳理。
- `scrapers/euro.py` 未完成(Euro 反爬),未启用。
- 零售网站会改版;某个网站整列空白或 ERROR 时需要更新对应 `scrapers/<site>.py`。
- 必须在本机运行(云端/沙箱通常访问不了这些网站)。

## License
未指定。公开发布前请先确认原作者与公司的授权,并选择合适的许可证。
