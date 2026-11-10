# 排错手册 —— 我们实际遇到过的问题和解决办法

按“看到的现象”查。每一条都是交接前真实踩过的坑。

## A. 安装 / 环境

### A1. Mac 终端提示 `command not found: pip` 或 `command not found: python`
- 原因:Mac 上命令叫 `python3`,而且还没进入虚拟环境。
- 解决:直接双击 `launchers/install_mac.command`。PyCharm 版见 B 部分,进入项目后终端最前面有 `(venv)` 或 `(.venv)` 才能用 `pip` / `python`。没有的话改用:
  ```
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
  ```

### A2. `ModuleNotFoundError: No module named 'requests'`(或 openpyxl / pandas / playwright)
- 原因:依赖没装全,或者解释器选错了。
- 解决:在项目文件夹的终端里运行 `pip install -r requirements.txt`(requirements.txt 里已经包含 requests)。

### A3. `BrowserType.launch: Executable doesn't exist ... playwright install`
- 原因:Playwright 的库装了,但它自带的 Chromium 浏览器没下载。
- 解决:运行 `python -m playwright install chromium`。
- 如果下载一直超时(报 `storage.googleapis.com ... timed out`):不用再折腾。本工具已经改为:找不到自带 Chromium 时,自动使用电脑上已安装的 **Google Chrome**,再不行用 **Edge**。只要这台电脑装了 Chrome,直接运行即可。日志里看到 `Browser: chrome` 就说明在用 Chrome。
- 如果提示 `No browser could be started`:安装 Google Chrome,或换个网络(公司网络/VPN)再运行 `python -m playwright install chromium`。

### A4. Mac 双击 `.command` 提示“无法打开,因为来自未知开发者”
- 解决:右键点击文件 → 打开 → 打开。如果提示没有执行权限,在终端对文件夹运行 `chmod +x *.command`。

### A5. Windows 双击 `.bat` 一闪而过
- 先运行 `launchers\install_windows.bat`。需要先装 Python 3.9 或更新版本,并勾选 “Add Python to PATH”。

## B. PyCharm

### B1. 项目名很奇怪(如 `run_all.py1157734...`),终端报找不到 `requirements.txt`,右上角没有运行配置
- 原因:打开的不是正确的项目。常见两种:只打开了一个文件;或者打开了上一层文件夹。
- 解决:File → Close Project。再 File → Open,选中 **仓库根文件夹本身(里面有 `run_all.py` 的那一层)**(不要点进去选文件,也不要选它的上一层),弹窗选 Trust Project。打开后左边根目录应该就是这个文件夹,里面能看到 `run_all.py` 和 `scrapers`。

### B2. 添加解释器时提示 `Environment location directory is not empty`
- 原因:它要新建的 `venv` 文件夹已经存在。
- 解决:不要选 New。切到 **Existing**,解释器选 `…/venv/bin/python`(Windows 是 `…\venv\Scripts\python.exe`)。如果右下角已经显示了解释器,直接取消这个对话框即可。

### B3. 右上角下拉框里没有“1 跑全部价格”等配置
- 解决:确认按 B1 打开了正确的文件夹。仍然没有:右键 `run_all.py` → Run 'run_all'。参数(如 `--sites MSH --dry-run`)在 Run → Edit Configurations → Parameters 里填。

### B4. 右下角解释器是 Python 3.9
- 可以用,代码兼容 3.9 及以上。

## C. 运行

### C1. 保存时报权限错误 / 表格没更新
- 原因:Excel 里还开着这个 xlsm。关掉再跑。

### C2. 所有链接都显示 `price check failed`
- 看检查报告 `XM_Price_Checker_Python_check_report.txt`,每条错误后面写了具体原因,按上面 A 部分对应处理。

### C3. 跑的时候会弹出浏览器窗口
- 这是正常的,逐个打开零售网站。**中途不要手动关闭**。如果弹出 Cookie 提示,不用管。

### C4. 日志太长看不清
- 不用看日志。只看项目文件夹里的 `XM_Price_Checker_Python_check_report.txt`,先看 HIGH 和 MEDIUM。

### C5. 想先试一下,不动表格
- 运行 `python run_all.py --sites MSH --dry-run`(双击 `launchers/test_msh_*`,或 PyCharm 里选“2 只测MSH”)。这样只抓取和检查,不写表格。正常的话:所有链接 0 个 ERROR。

### C6. 想只跑某几个网站
- `python run_all.py --sites MSH,MEX`。

### C7. 表格被改坏了怎么办
- 每次保存前会自动备份成 `XM_Price_Checker_Python_backup_日期时间.xlsm`,把备份改回原名即可。

## D. 结果看起来不对

### D1. MSH 某个机型显示“无货/没找到”
- 先别急着判定是程序错了。MSH(MediaMarkt)我们只看官方店,页面上写着 `Sprzedaż i wysyłka przez XX`(XX 不是 MediaMarkt)的是第三方卖家,会被排除。很多机型在 MSH 只有第三方在卖,这时“没找到”是正确的。
- 核实方法:在浏览器打开该机型的 MSH 搜索链接(Links 表里有),看每张卡片下面有没有 `Sprzedaż i wysyłka przez ...`。没有这行的才是官方店。

### D2. 机型名称写法不一样(RM = Redmi,标题没写 5G)
- 已经处理:`RM` 当作 Redmi;标题没写 5G 不算不匹配。只有标题明确写了相反的(目标 5G、标题写 4G/LTE,或反过来)才排除。
- 唯一严格区分 4G/5G 的,是产品表里同时有两个版本的同名机型(Redmi Note 17 / Redmi Note 17 5G,Redmi Pad 2 Pro / Redmi Pad 2 Pro 5G)。
- Pro、Max、Ultra、Lite 这些后缀不同永远是不同机型。

### D3. 报告里 HIGH:`promo-above-rrp`
- 意思是 Results 表里的“RRP after Promotion”比 RRP 还高,很可能是填错了。确认后在 Excel 里改。是有意设置的就忽略。

### D4. 新机型没有链接
- 在 Products 表加一行,然后运行:
  `python link_builder.py new XM_Price_Checker_Python.xlsm <TargetID> --sites MEX,MSH`
  把输出的行粘贴进 Links 表。不要手写搜索词。

### D5. 报告里提示链接和 Products 对不上(`link-differs`)
- 说明这条链接的搜索词和 Products 里的名称/内存不一致,通常是手误(例如 8+512 写成了 8256)。按提示改正。故意写的特殊搜索词,登记到 `link_overrides.json`。

### D6. 某个网站整列空白
- 报告里会出现 `site-empty` 或 `scraper-error`。多半是该网站改版或拦截了访问,需要有人更新对应的 `scrapers/xxx.py`。

## E. 其他说明
- 除了 MSH,其他 7 个网站(MEX、Electro、Avans、KTR、XKOM、Neonet、Max electro)的识别逻辑是原作者的,尚未按 MSH 的方式重新梳理。第一次跑完请认真看检查报告。
- `euro.py` 没有完成(Euro 有反爬),没有启用,不用管。
- 云端环境/沙箱访问不了这些零售网站,必须在本机运行。
