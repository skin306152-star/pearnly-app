# 配对 & 账套体验修复批次(Owner 真机一轮揪出 · 一次重打全修)

> Owner 2026-06-22 真机实测一轮找出 4 个问题。**合并成一批 · 一次 companion+web 改 · 一次重打重发 · 一次验收**。
> 吸收并取代:`22-companion-i18n-th-zh.md`、`23-account-list-from-express-registry.md`(内容并入本单)。
> companion `D:\pearnly-companion` + pearnly-app FE。免费·无付费项。

---

## A. ★账套真名单:读 Express「公司登记表」(核心 · 保证任何事务所都扫得准)

**病(实证)**:`account_probe.py` 是**扫文件夹**(遍历 `express_root` 下所有带 `ISINFO.DBF` 的子目录)。后果:
- 捞进 Express 自带演示/空模板(`เอ็กซ์เพรสซอฟท์แวร์กรุ๊ป ข้อมูลเปล่า`)+ 未登记目录 → 小助手显示 **5 个**;
- 真 Express 登录 grid 只 **3 个**(它读自己的公司登记表),且真账套路径可能在**别的盘**(如 `S:\2558\EXP58\58ASIASP`)→ 扫一个文件夹**既捞垃圾又漏真账套**。
- 客户若选了演示/未登记的 → 直写能写、但 PACK 在 grid 里找不到 → **发票永不显示 / 写进垃圾**。

**★登记表已 PM 定位(2026-06-22 实读 · 但比预想复杂,看清坑)**:
- 文件 = **`<express_root>/secure/SCCOMP.DBF`**(字段 `COMPNAM`/`COMPCOD`/`PATH`/`GENDAT`/`CANDEL`)。70EXP 那份 **107 行**。
- ⚠️ **`COMPCOD` 不是唯一账套 ID**:107 行里绝大多数 `COMPCOD='DATAT'`(少数 PDATAT/DATAZ)——它是"槽位/类型"不是身份。**真正区分账套 = `PATH`**(如 `TEST`、`S:\2558\EXP58\58ASIASP`)。`PATH` 相对则相对 express_root(`TEST`→`<root>\test`)、绝对则跨盘原样。
- ⚠️ **SCCOMP(107) ≠ 登录 grid(3)**:grid 是**当前/筛选子集**。**绝不能直接 dump SCCOMP**(会显 107·更糟)。
- 实证锚:grid 的 DATAT 行 = SCCOMP 中 `COMPNAM='9.ข้อมูลทดสอบเวอร์ชั่น 1' / PATH='TEST'`(=我们的 DATAT·公司 มานะชัยบริการ/`0735527000289`)。

**修(通用 · 不瞎搞 · 任何事务所一致)**:
1. **施工窗口反查"107→3"的过滤逻辑**:Express 登录 grid 怎么从 SCCOMP 选出当前那几个(候选:`secure/` 里另有"当前/活跃 per code"指针文件 / `CANDEL` 标志 / PATH 在本机可达性过滤 / 其它)。在真机实验(切换 Express 当前公司→看哪个文件/字段变)定位真规则,**记进 probe 注释固化**。account_probe 改成**只列与登录 grid 完全一致的那几个**(含 row 顺序·供 PACK/RPA 导航)。
2. **唯一键用 `PATH` 不用 `COMPCOD`**:T2 白名单/所选账套之前用 `account_set='DATAT'`(=COMPCOD·非唯一)→ **改以 `PATH` 为账套唯一身份**(account_dir);显示名用 `COMPNAM` 或该 PATH 的 ISINFO 公司名。**与 T2 端侧锁定对齐复核**(别让"DATAT"这个非唯一码当锁)。
2. **`account_probe` 改为读这张登记表**(不再扫文件夹):列出**登记过的账套**,每条取 `code / 公司名 / 存储路径(原样·支持跨盘绝对/相对)`;按该路径读 `ISINFO` 补 `tax_id`;查该路径 OS 可写。**结果必须与 Express 登录 grid 完全一致**(同账套、同名、同序)。
3. **`account_set_row` 顺便定死**:行号 = grid 排序后的位置(grid 按 `ชื่อข้อมูล` 名称排+排序标记)→ 读登记表 + 同样排序即得行号 → **PACK/RPA 导航的行号从此确定性可得**(原"行号读不出只能隐藏默认"的坑一并解决)。
4. **通用性来源**:登记表路径**由自动定位的 Express 安装(`express_locate`)推导**,不硬编码本机路径 → 换任何事务所自动找对。
5. **fail-safe**:登记表找不到/读不出 → **明确报错**"未能读取 Express 公司列表,请确认 Express 路径",**绝不回退扫文件夹捞垃圾**。

> 验收(任何事务所通用证据):小助手下拉的账套 == Express 登录 grid 的(本机=3 个 · code/名/路径/顺序逐一对上);演示/未登记的不再出现;换一个不同 `express_root`(或模拟另一套登记表)仍正确列出该套的真实账套。

## B. 配对窗"正在查找你的账套…"标签卡住

**病**:下拉里已加载出账套,但收起的框一直显示"正在查找…"(探测完没更新选中文案)。
**修**:探测完成 → 更新为"请选择账套"(或"已找到 {n} 个账套,请选择");失败 → 显示 A.5 的报错文案。

## C. 网页 ↔ 小助手 账套不同步(去掉 DATAT 硬默认)

**病**:网页 step3"已选:DATAT"是**写死默认**(向导建端点塞 `account_set='DATAT'`、`_finish` 用 `S.account||'DATAT'`),非小助手真报。→ 与小助手脱节、误导。
**修**:
- 向导建端点**不再硬塞 DATAT**;`_finish` 不用 `||'DATAT'` 兜底。
- step3 镜像**小助手真报的所选账套**(`cfg.account_set`):有 → "已选账套:{真公司名}(在小助手里选/改)✓";无 → "请在小助手窗口里选择账套"(不显示假默认)。
- `account_set` 唯一真相源 = 小助手所选(经 heartbeat 上报)。两边显示从此一致。

## D. i18n 泰语+中文切换 + 文案重写(吸收 22 · 客户看得见的都译 + 去甩锅口语)

- 新 `i18n.py`:**只泰语 TH + 中文 ZH**。中文用下方【权威文案】(非现有写死烂文案);泰语按含义写**地道专业泰语**(客户语言 · 非机翻 · ship 前过一遍)。
- 所有客户可见文案(配对窗 + 托盘 + 提示/报错)改读 `t(key,lang)`。默认按 Windows 语言(泰→TH/中→ZH/其它默认 TH)+ 右上角 `ไทย/中文` 切换 + 存 config 记住。
- **红线**:界面绝不出现「是你的责任」「自动干活」「选你自家那个」这类甩锅/口语。

| key | 中文(权威) |
|---|---|
| win_title | Pearnly 小助手 · 首次设置 |
| intro | Pearnly 小助手会将识别后的发票自动录入本地 Express。完成以下设置后,小助手将在后台自动运行,全程无需手动操作 Express。 |
| lbl_code / ph_code | 配对码 / 在 Pearnly 网页「连接 Express」中获取 |
| lbl_user / lbl_pw / ph_pw | Express 登录账号 / Express 登录密码 / 请输入 Express 登录密码 |
| help_pw | 用于登录 Express 并在夜间整理数据,使录入的发票正常显示在报表中。密码经加密后仅保存在本机,其他设备无法读取。 |
| lbl_acct / ph_acct_loading | 选择账套 / 正在加载账套列表… |
| help_acct | 请选择贵公司对应的账套。发票将准确录入您所选的账套,请在配对前确认无误。 |
| status_found | 已找到 {n} 个账套,请选择贵公司对应的账套。 |
| chk_autostart / btn_cancel / btn_pair | 开机时自动启动小助手 / 取消 / 配对 |

## 边界 / 红线
- 只动:账套探测来源(A)、配对窗 UI(B/D)、网页 step3 镜像 + 去默认(C)、i18n 层(D)。
- **不碰**:写盘/PACK/三重一致性闸/凭证逻辑。全程**只读** Express 数据。

## 验收(真机)
1. A:小助手下拉 == Express 登录 grid(3 个 · 逐项对上)· 演示/未登记不出现 · row 与 grid 一致。
2. B:加载完标签不再卡"正在查找"。
3. C:网页 step3 显示小助手真报的所选账套(没选则提示去小助手选)· 不再假 DATAT · 两边一致。
4. D:TH/ZH 两套渲染全切换无残留 · 默认/记住正确 · 泰语地道 · 无甩锅口语。
5. 回归:DATAT 直写→PACK→报表→还原 ALL_MATCH 链不退化 · companion 单测全绿。

## 交付 + 上线(全在直录这一个窗口顺序做)
- companion:`account_probe` 改读登记表 + `account_set_row` 确定性 + 配对窗标签/`i18n.py` + config(`ui_lang`)+ 测试 → master。
- pearnly-app FE:向导去 DATAT 硬默认 + step3 镜像真选择 → build+dist。
- 重打瘦身版三件套(不含 PyArmor)→ scp prod `static/companion/` → bump `home.html ?v=` → push。
- 报告:小助手 vs Express grid 对比截图 + 网页 step3 一致 + TH/ZH 截图 + 体积 + prod 健康 + 单测。
