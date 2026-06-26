# 模拟录入(RPA)· 研究判断 + 施工方案(第二录入方式)

> **★结局(Owner 2026-06-22 拍板):RPA 泊在「安全转人工」状态,不再追。** 两次结构性硬墙:① 非存货采购 RR = 货品 grid 模型不符(→ 销项only);② 连销项 IV 服务项的 **qty/price 格 = Codejock 自绘·读不出+光标不可定位**,纯键盘盲打打不通(每路弄丢光标/清行/弹 picker),只能靠会 Express 的操作员真机录一次键序。安全网已兜死(`enter_amount` 录完比对 grid 合计 vs 期望 total·不符即 abort·绝不存错额)→ RPA 销项**安全转人工不记错账**。**判断:DBF 直写已覆盖采购+销项、稳、已上线 → RPA 不增产品价值且脆,收手。** 已交付的真东西(零坐标框架/批量韧性/worker 接线/服务项解析/Codejock 剪贴板录入端/单号/21 测/onboarding·worktree 9 commits)合并作**已泊功能**(method=rpa·安全降级·默认不启)。单价键序 = 待操作员收尾项。**复活条件**:某客户坚持界面录入 + 能拿到其 Express 操作员 → 部署期录一次 qty/price 键序为该客户开。下方为历史研究/施工记录。


> 来源:Owner 2026-06-22「研究模拟录入怎么做,给新窗口去做」。companion `D:\pearnly-companion`。
> 目标流程(Owner):用户配好 ERP → 小助手连上 → 收到 OCR 好的发票 → 自动录进 Express,销项/采购自动判。
> ⚠️ **隔离**:与"最后 companion 棒(T6/T7/T9/T4)"并行 → **本任务在 git worktree 里做**,避免撞 companion master;两边都落地后再合。**RPA 不阻塞 DBF 直录上线**(直录先发·RPA 是 `method=rpa` 第二方式·后发)。

---

## 1. PM 研究判断(已读半成品真码 · 直接采信)

**现有半成品 = 计算机视觉路子,盲做的,核心已过时**:
- `calibration.py`/`field_engine.py`/`matching/`(template_match/sift_fallback/calibrated_locator)/`ocr_verifier.py` + cv2/numpy = **截屏 → SIFT/模板匹配找字段 → 像素坐标输入 → OCR 验证**。当时无真机、只有假空白截图,只能"看图认位置"。脆(DPI/分辨率/字号敏感·要校准·OCR 验证不稳)。
- **我们已有更稳的路**:`pack_runner.py` + `D:\_express_audit\p32_*.py` 用 **pywinauto 驱动真 Express Win32 控件**(读真控件/点真菜单/真输入框),不靠看图,**真机已跑通**(登录→grid→菜单→对话框)。

**裁决**:
- 🔁 **重做录入引擎 = pywinauto 控件驱动**(对齐 pack_runner)。**丢** SIFT/模板/校准/cv2 那套(正好与 T6 砍 opencv 一致)。
- ✅ **捡**:① 字段模型概念 ② 纪律「**OCR 仅验证·绝不从屏读数据回填·数据永远来自 Pearnly payload**」(`ocr_verifier` docstring 那条·保留) ③ 流程骨架(领单→驱动→验证→回报)。
- 🔁 **input_executor**(打键)部分可留。

## 2. 架构(大部分已就绪 · 可扩展性契约回本)

RPA = 同队列同 payload 的**新消费方**,不另起炉灶:
- **方向(销项/采购)自动判 = 云端已做**(`direction.py` 税号锚点)。payload 带 `direction` → RPA 路由到对应菜单(采购 `1.ซื้อ`→RR/HP · 销项 `2.ขาย`→IV/HS)。**不重做方向判定。**
- **领单 / 字段映射 = 与 DBF 同**(同 `erp_push_logs` 队列 lease · 同 mapper/sales_mapper 映射好的字段)。RPA 只把**同一份映射字段打进 GUI**(而非写 DBF)。
- **设置共用 = `load_express_settings()` seam**(Express 位置 + 登录 + 所选账套 + workdate · T1/T5/契约已建)。`account_set_row` 正是 RPA 登录后 grid 导航要的。
- **凭证 = T1 共用**(DPAPI · pack_runner 同款 ctypes 解密)。
- → 净增 = `rpa_flow`(驱动录入)+ `main.py` 的 `method=='rpa'` 分支(与 `_handle_dbf_task` 并列)。

## 3. 阶段(先勘探后建 · 之前缺的就是真机勘探)

### P0 · 真机勘探(DATAT · 这是之前盲做的根因 · 现在能做)
用 `D:\_express_audit` 工具链(32 位 pywinauto)在真 DATAT 上,把**采购 + 销项**两条录入路径的精确控件+按键序列录下来,写进 `rpa_flow_map.md`:
- 菜单进入(采购 `1.ซื้อ→4.ซื้อเงินเชื่อ`RR / 现购 HP;销项 `2.ขาย→…`IV/HS)。
- 每个字段:控件 identity(可读 Win32?)/ Tab 顺序 / F 键 / 日期格式(佛历 DD/MM/YY)/ 供应商或客户码(查无则建档 APMAS/ARMAS 的入口)。
- **⚠️ Codejock 自绘 grid 坑**(PITFALLS §3.1):明细行很可能是读不出单元格的 Codejock grid → 这些字段**键盘盲打**(逐行 type+Tab+Enter)·不靠读控件;识别哪些字段是可读控件、哪些必须键盘盲打。
- 保存键 + **读回 Express 真单号**的途径(回 ack 用·若单号在不可读 grid 则另想:状态栏/弹窗/查询)。

### P1 · 建 rpa_flow(pywinauto · 控件优先·grid 键盘盲打)
- `rpa_flow.enter_document(settings, payload)`:登录(复用 secret_store)→ 选账套(grid row)→ 按 `direction` 进菜单 → 填字段(可读控件读回校验·grid 键盘盲打) → 保存 → 读回单号 → 返回结果。
- 接 `main.py` `method=='rpa'` 分支;`worker`/poll loop 与 DBF 同壳(T4 抽的共享壳正好用)。
- 验证沿用纪律:输入后能读控件就读控件比对·读不出的关键字段用 OCR **仅验证**(`ocr_verifier` 保留用途)·数据源永远 payload。

### P1.5 · 自适应硬要求(★Owner 2026-06-22 点名:不同显示器/分辨率/缩放)
**这是旧半成品被弃的根因(像素/图像匹配对屏幕尺寸/DPI 敏感·要逐机校准)。新建必须解决,作硬红线**:
- **只按控件身份 + 键盘导航(Tab/F 键/type),绝不按像素坐标点击**。控件身份与屏幕尺寸/分辨率无关 → 天然自适应、**零逐机校准**。
- **DPI 感知**:进程声明 DPI-aware(`SetProcessDpiAwareness`/manifest);Windows 缩放 100/125/150% 下控件驱动仍准。**唯一要专门回归的就是缩放档位**。
- Codejock grid 走键盘盲打(本就与分辨率无关·非点坐标)。
- **禁**:重新引入"截图找位置/像素坐标点击/per-user 校准"那套(那是旧路子的病)。
- P3 验收**额外加一档**:在**不同分辨率 + 一个非 100% 缩放(如 150%)**下各跑通一遍,证自适应。

### P2 · 安全闸(RPA 特有)
- **独占/占用**:与 PACK 同理——驱动 GUI 时不能有人在用 Express(占用检测·复用 `pack_scheduler.express_is_running`)。
- **幂等**:录入前按 `ref_no`+供应商查 Express 是否已存在该单 → 已存不重录(防 Agent 重启/重领重复记账)。
- **所选账套**:只在登录所选账套里录(沿用三重一致性精神·登录选错账套不录)。
- **失败安全**:任一步异常 → 不保存/撤出 → ack failed 留人工·绝不留半张脏单。
- **诚实状态**:只有 Express 真保存+读回单号才 ack success。
- **★批量韧性(Owner 2026-06-22 点名·100 张别卡死整批)**:**每张独立处理、失败隔离**——单张异常(未预期弹窗/数据坏/校验不过)→ 干净取消那一张(发 53512 撤当前编辑·不留半单)→ 该张 ack failed 进人工队列 → **继续下一张,绝不停整批**。未预期弹窗有**超时兜底**(等控件超时 → 截断该张当失败·不无限挂)。Express 崩/卡 → 检测(超时)→ 该 lease 到期回 pending 下次重领(队列模型·不丢不重)。批末汇总:N 成功 / M 失败转人工。**100 张目标 = 多数自动成、少数转人工·永不整批冻死。**

### P3 · 真机验收(DATAT)
一张采购 + 一张销项 payload → RPA 各录一张 → Express 里真出现、字段对、单号读回 → 幂等(重领不重录)→ 占用时跳过 → 还原 DATAT 回基线。

## 4. 诚实边界(PM)
- **DBF 直录更稳**(不碰 GUI·已上线主路)。RPA 价值 = Express 自己过账/校验(部分事务所偏好)、不依赖 DBF schema;但**驱动 30 年老 GUI 天生更脆**,维护成本高。定位为**第二可选方式**,非取代直录。
- 一套 Express 版本的键序**录一次全客户复用**(部署期与操作员一次性勘探·真客户账套无 DATAT 账期限制)。
- cv2/校准那套重做后可彻底删(与 T6 一致·进一步瘦身)。

## 5. 交付
- worktree 内:`rpa_flow_map.md`(P0 勘探)+ `rpa_flow.py` + `method=rpa` 分支 + 安全闸 + 测试。
- 报告:P0 勘探序列 + P3 真机(采购/销项各一张 + 幂等 + 占用)+ 单测 + commit。**与最后 companion 棒都落地后合 master。**
