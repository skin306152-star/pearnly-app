# 小助手 GUI 配图生成(setup 章 14 张)

教程的图全部脚本生成,界面一改重跑就换新。网页那部分由 `scripts/_guide_shots*.cjs`(Playwright)负责;
小助手是 Windows 桌面 Qt 程序,浏览器截不到,由本目录这套负责。

产出 7 个 shot × 2 语种 = 14 张,落在 `static/guide/shots/`:

| shot                   | 内容                   | 抓法                        |
| ---------------------- | ---------------------- | --------------------------- |
| `setup-01-pairwindow`  | 配对窗整窗             | PrintWindow                 |
| `setup-02-paircode`    | 配对码输入段           | Qt `grab()` 按控件几何裁    |
| `setup-03-accountpick` | 账套下拉展开           | Qt `grab()` 窗口 + 弹层合成 |
| `setup-04-advanced`    | 高级设置(六个科目下拉) | PrintWindow                 |
| `setup-05-actions`     | 底部状态行与按钮       | Qt `grab()` 按控件几何裁    |
| `setup-06-traymenu`    | 托盘右键菜单           | PrintWindow(按句柄)         |
| `setup-07-noexpress`   | 未自动找到 Express 态  | PrintWindow                 |

## 红线(先读这段)

- **绝不点配对窗里的「配对」按钮。** 配对会连云端换 token 重新注册 endpoint,可能把 Zihao
  在用的那个实例踢下线,并写 HKCU 开机自启。`driver.py` 已把该按钮的 clicked 信号拆掉做硬保险,
  但人手在旁边跑的时候别去点。
- **绝不停在用的小助手进程。** 这套方案的全部意义就是不用停它。看到「已有实例在跑」不是让你去杀进程。
- **绝不碰真 `%APPDATA%\Pearnly`。** 配置、日志、快照备份都在那里;跑之前 `orchestrate.ps1` 会把
  `APPDATA` 重定向到 scratch 副本,不要绕过它直接跑 `driver.py`。
- **绝不碰注册表。** Express 路径探测和开机自启都读写注册表,本套用 `PEARNLY_EXPRESS_ROOT`
  环境变量走探测链第一档,不落注册表。
- **绝不指向真账套。** 配图会公开发布,只用 `make_fixture.py` 造的虚构数据(公司名
  ตัวอย่าง/ทดสอบ/สาธิต,税号是不存在的号段)。
- **跑的时候屏幕上会弹窗。** 别在 Zihao 用机器的时候跑。

## 跑之前确认

1. 装了 companion 源码:默认 `C:\Users\skin3\Desktop\pearnly-companion`,否则设
   `PEARNLY_COMPANION_SRC` 指过去(源码在私有仓库 `skin306152-star/pearnly-companion`)。
2. Python 装了 `PySide6` 和 `dbf`。
3. 在用的小助手实例可以照常开着 —— 本套不与它抢单实例互斥量。确认的是**不要**为此去停它。
4. 界面文案改过的话,四语文案先落地再出图,否则截出来的还是旧字。

## 怎么跑

```powershell
# 1. 造虚构 Express 数据根(只跑一次,除非要改演示账套/科目)
python scripts\companion-shots\make_fixture.py $env:TEMP\pearnly-companion-shots\express\69EXP

# 2. 出图:两个语种各跑一遍常规态,再各跑一遍空态
powershell -NoProfile -File scripts\companion-shots\orchestrate.ps1 -Lang zh
powershell -NoProfile -File scripts\companion-shots\orchestrate.ps1 -Lang th
powershell -NoProfile -File scripts\companion-shots\orchestrate.ps1 -Lang zh -Empty
powershell -NoProfile -File scripts\companion-shots\orchestrate.ps1 -Lang th -Empty

# 3. 校验教程闸仍 0 违规(会检查 14 张都在、中泰都齐)
PYTHONIOENCODING=utf-8 python scripts\check_guide.py
```

`-Work` 可换工作目录(默认 `%TEMP%\pearnly-companion-shots`),`-Python` 可换解释器。
中间产物(隔离的 APPDATA 副本、握手文件、driver 日志)都在工作目录里,可随手删。

## 三个命门(改这套之前先看懂)

- **为什么不跑 `main.py`**:它开头就拿命名互斥量 `PearnlyCompanionSingleInstance`,在用实例持着,
  第二个进程直接退出。所以 `driver.py` 绕过 `main.py`,直接构造 `PairingDialog` / 复用
  `TrayApp._build_menu` —— 控件是生产真件,但不碰互斥量、不建托盘图标、不起 poll worker。
- **为什么重定向 `APPDATA`**:`config.py` 在 import 期就按 `%APPDATA%/Pearnly` 定死配置与日志路径
  并 mkdir,`PairingDialog` 会读写这份配置。不重定向 = 截图过程改写在用实例的 `companion.json`。
- **为什么用 `PrintWindow` 不用截屏裁剪**:截屏拿的是桌面合成结果,被遮挡或滚出屏幕的部分截不到,
  还会把桌面上别的东西录进公开教程图;`PrintWindow` 让窗口自己重绘到指定 HDC,与叠放次序和屏幕
  大小无关。必须带 `PW_RENDERFULLCONTENT`,否则现代控件画成黑块。窗口边界取 DWM 扩展边框,
  `GetWindowRect` 会多算不可见阴影边距。

## 一个约束的由来

`setup-04-advanced` 展开后内容高过屏幕,窗口自适应封顶在 94% 屏高,滚动条一出顶部会切出半行残影。
`driver.py` 解开高度上限让窗口按内容长满再抓 —— `PrintWindow` 抓的是窗口自身绘制表面,超出屏幕
的部分照样完整,等同会计在更高屏幕上看到的样子。
