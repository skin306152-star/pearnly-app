# 小助手 i18n · 泰语 + 中文切换(去写死中文)

> 来源:Owner 2026-06-22 真机——配对窗全是写死中文,泰国客户看不懂。**只做泰语 + 中文,其它语言不要。**
> companion `D:\pearnly-companion`(GUI)。免费·要重打+重发安装包。**不挡 Owner 自己实测(他看中文),接真泰国客户前必须有。**

## 1. 现状
- `gui_pairing.py` / `gui_tray.py` / `tray.py` 字符串**写死中文**,**无 i18n 模块**。

## 2. 做法
- 新建 `i18n.py`:`TH` + `ZH` 两份字典 + `t(key, lang)`。**只这两种语言**(无 EN/其它)。
- **默认语言**:开窗时按 Windows 显示语言自动选(泰→TH·中→ZH·其它→**默认 TH**·客户是泰国人);**右上角切换控件**(ComboBox「ไทย / 中文」)即时重渲染;**所选语言存 config**(下次记住·Owner 切中文即长留中文)。
- **范围 = 所有客户可见文案**:配对窗(标题/标签/占位/提示/按钮/状态行)+ 托盘菜单项 + 通知/状态/报错气泡。**内部日志不译**(给我们看的)。
- 泰语文案要**地道**(给泰国会计看·非机翻腔);中文沿用现有。两套 key 一一对应,缺译回落另一种不崩。

## 2.5 ★权威文案(Owner 2026-06-22:现有写死中文不专业·重写)

> 现有文案有甩锅式/口语化(如「选错账套是你的责任」「后台自动干活」「选你自家那个」)——**官方产品不这么写**。以下为重写后的**权威中文(ZH)**,各 key 照此;**泰语(TH)须按此含义写地道专业泰语**(客户语言·非机翻腔·ship 前 Owner/泰语母语过一遍)。

| key | 中文(权威) | 含义(给写 TH 用) |
|---|---|---|
| win_title | Pearnly 小助手 · 首次设置 | Pearnly Companion · First-time setup |
| intro | Pearnly 小助手会将识别后的发票自动录入本地 Express。完成以下设置后,小助手将在后台自动运行,全程无需手动操作 Express。 | auto-enters recognized invoices into local Express; runs in background after setup; no manual Express work |
| lbl_code | 配对码 | Pairing code |
| ph_code | 在 Pearnly 网页「连接 Express」中获取 | Get it on the Pearnly web "Connect Express" page |
| lbl_user | Express 登录账号 | Express login username |
| lbl_pw | Express 登录密码 | Express login password |
| ph_pw | 请输入 Express 登录密码 | Enter your Express login password |
| help_pw | 用于登录 Express 并在夜间整理数据,使录入的发票正常显示在报表中。密码经加密后仅保存在本机,其他设备无法读取。 | used to log into Express and tidy data nightly so entered invoices show in reports; password encrypted, stored only on this machine, unreadable elsewhere |
| lbl_acct | 选择账套 | Select account set |
| ph_acct_loading | 正在加载账套列表… | Loading account sets… |
| help_acct | 请选择贵公司对应的账套。发票将准确录入您所选的账套,请在配对前确认无误。 | select your company's account set; invoices go exactly to the one you choose; please confirm before pairing |
| status_found | 已检测到 {n} 个账套,请选择贵公司对应的账套。 | found {n} account sets; choose your company's |
| chk_autostart | 开机时自动启动小助手 | Start companion automatically on boot |
| btn_cancel | 取消 | Cancel |
| btn_pair | 配对 | Pair |

托盘/通知文案同口径(专业·去口语·去甩锅)·按现有功能项一并译。**红线:界面绝不出现「是你的责任」「自动干活」这类甩锅/口语表达。**

## 3. 边界
- 只动 GUI 文案层 + 新 i18n 模块,**不碰**配对/写盘/PACK/安全闸逻辑。
- DPAPI 密码框、账套下拉等控件行为不变,只换 label/提示文字。

## 4. 测试 / 验收
- TH/ZH 两套渲染:配对窗、托盘、提示气泡全部跟随切换、无残留写死中文。
- 切换即时生效 + 重开记住上次语言(config 持久)。
- 泰语真机截图(配对窗三态)+ 中文对照。
- 缺某 key 回落不崩。companion 单测全绿。

## 5. 交付 + 上线
- companion:`i18n.py` + gui_pairing/gui_tray/tray 改读 `t()` + config 加 `ui_lang` + 测试 → 推 master。
- **重打瘦身版三件套(不含 PyArmor)** → scp prod `static/companion/` → bump `home.html ?v=` → push 部署。**全在直录这一个窗口顺序做,无撞树。**
- 报告:TH/ZH 截图 + 切换/记住验证 + 体积 + prod 健康。
