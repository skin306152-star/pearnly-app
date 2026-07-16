# Express Push · 工程总纲(PM 主导 · 施工窗口先读这页)

> ⚠️ **2026-07-15 companion 源码已迁 GitHub**:本页及所有子文档里写的 `D:\pearnly-companion`(旧 U 盘/本地路径)**一律作废**。companion 源码现在 = 私有仓 **`https://github.com/skin306152-star/pearnly-companion`**(master + feature 分支 + 标签;RPA 变体 = 该仓 `feature/express-rpa` 分支,不是独立仓)。要改 companion:先 `git clone` 该仓,本地改 → `git push`。prod 部署仍走 `packaging/release.ps1`(scp,未改成拉 GitHub)。详见记忆 companion-reliability-1128-and-source-location。

> PM:Claude(Opus 4.8)。Owner:skin3。施工模式:PM 出施工单 → 施工窗口实现 → PM 验收 → 发下一棒,直到闭环。
> 五字要求(Owner 定):**简单 · 方便 · 快捷 · 精准 · 兜底**。
> 设计定稿:`01-ui-design-brief.md` + `prototype.html`(可双击看交互)。本页是真相与边界,冲突时以本页为准。

---

## 1. 这个项目要做什么(一段话)

Pearnly 识别好的采购发票,**自动记账进客户本地的 Express 财务软件**;AI 没把握/推失败的留人工审核。Express 是 2016 年的 FoxPro/DBF 桌面程序、**无 API、数据在客户局域网或个人电脑上**,所以架构 = **云端发件箱队列 + 客户本地 Agent 拉取并录入**。

## 2. 架构(命名清晰,别自创)

```
Pearnly 云(多租户)                          客户本地(每家事务所一个)
┌──────────────────────────┐               ┌──────────────────────────┐
│ OCR 识别 → 置信闸门         │   出站拉取     │ 本地 Agent(token 限租户)  │
│ 高置信 → erp_push_jobs 队列 │◀────轮询───── │  · RPA 录入 ExpressI       │
│ 低置信/异常 → 人工审核       │ ──返回单据──▶ │  · 或 DBF 直写(高级)      │
│ 管理 API(配置/重试/设置)   │   ack 回报    │  → 写进目标账套             │
└──────────────────────────┘               └──────────────────────────┘
```

> **复用既有骨架(PM 已读真代码)**:产品里已有成熟 ERP 推送系统 —— 连接 `erp_endpoints`、状态唯一源 `erp_push_logs`(铁律 #12)、adapter 注册表 `push_to_endpoint`、4 张映射表、kms 加密、前端 cards/logs/push-exc 三 Tab + 失败复核队列。**Express 不另起炉灶**:它 = 注册一个 `"express"` adapter,其"推送"动作 = 写入待领取队列(`erp_push_logs` status=pending),由本地 Agent 拉取执行。**唯一净增 = 本地 Agent + 出站拉取接口**(因为 Express 在客户内网,云端 Playwright 够不着;现有 mrerp 也是 Playwright,但跑在云端)。源是 `ocr_history`(对齐 `flatten_history_for_mrerp`),不是 purchase_docs。

- **出站拉取(Agent-initiated polling)**:Agent 向外连 Pearnly,Pearnly 永不向内连客户。无需开端口/公网 IP。
- **发件箱模式(Outbox)+ 幂等键 + 至少一次投递 + 死信→人工**:不重、不丢、不假成功。
- **置信闸门**:复用 Pearnly 现有 STP/HITL 三态。高置信自动进队列;低置信/异常进人工审核,永不自动写账。
- 一家事务所 = 一个 Agent(单机版装在那台电脑、局域网版装在常开机器)。不同配置 = 安装时选,不是不同程序。

## 3. Express 记账真相(施工窗口拿不到内网,以下为 PM 实测,直接采信)

PM 已用真实测试账套 `DATAT`(`\\accserver\ACCOUNT\70EXP\test`)逆向出真相:

- **采购单两类**(由付款状态决定):
  - `RR` = ซื้อเงินเชื่อ 赊购(**未付**)· RECTYP=3
  - `HP` = ซื้อเงินสด 现购(**已付**)· RECTYP=1
  - 均过 **采购日记账 JNLTYP=04**(สมุดรายวันซื้อ)
- **单号格式**:`PREFIX + 佛历YY + MMDD + "-" + 序号`,例 `RR581231-002`(58=佛历2558=公历2015)。**公历年 +543 = 佛历年**;取末两位。
- **一张赊购发票,Express 同时写 5 处表**(`70EXP/<账套>` 下的 DBF):
  | 表 | 作用 | 关键列 |
  |---|---|---|
  | `APTRN` | 单据头(1 行) | DOCNUM, DOCDAT, REFNUM(供应商票号), SUPCOD, VATRAT, AMOUNT(税前), VATAMT, NETAMT(含税), VATPRD(税期) |
  | `ISVAT` | 进项税(喂 ภ.พ.30) | VATREC='P', TAXID(供应商税号), DESCRP(供应商名), AMT01(税前), VAT01(税额) |
  | `GLJNL` | 采购凭证头 | JNLTYP='04', VOUCHER(=单号), VOUDAT, DESCRP |
  | `GLJNLIT` | 总账分录(≥3 行) | VOUCHER, ACCNUM, TRNTYP('0'=借/'1'=贷), AMOUNT |
  | `APBAL`/`STCRD` | 供应商应付余额 / 库存卡(是存货时) | — |
- **复式分录范式**(实测 PTT 那张):
  ```
  Dr 11-04-02-00 采购/存货   375,347.20   (TRNTYP=0)
  Dr 11-05-04-01 进项税ภาษีซื้อ 26,274.30   (TRNTYP=0)  = 税前×7%
  Cr 21-02-01-00 应付账款เจ้าหนี้      401,621.50  (TRNTYP=1)
  ```
- **科目来源**:采购科目按供应商定 —— `APMAS`(供应商主档)每个供应商带默认 `ACCNUM` + `TAXID`。新供应商首次推送需先在 APMAS 建档。
- **单号自增**:`ISRUN` 表按文档类型存"下一号"+默认科目;DBF 直写须推进它。
- **金额/税额由确定性引擎算,绝不用 LLM**(铁律,见 [[line-accounting-honest-status-boundary]])。

## 4. 全局边界与兜底(每一棒都必须守)

1. **账套白名单**:每个连接锁死一个目标账套;**代码级拒绝写入其它账套**(本期只允许 `DATAT`)。真账套 `PDATAT/58ASIASP`、空模板 `DATAZ`、其它 `57ASCRD/korn` —— 一律禁写。
2. **特性开关**:`ERP_PUSH_ENABLED` 默认 **off**;未验收不影响任何现有功能。
3. **net-new 隔离**:全部走新模块,**不碰登录/OCR/计费/现有推送/对账/home.js**。改这些主路径前必须先报 PM。
4. **DBF 直写护栏**:写前自动备份该账套 → 单事务 → 校验借贷平衡 → 重建 `.CDX` → 失败回滚。默认 RPA,DBF 仅高级用户勾选风险后可用。
5. **幂等**:`idempotency_key`(租户+供应商票号+金额指纹)唯一约束,推过不再推。
6. **状态诚实**:只有 Express 真写成功(回 Express 单号)才标"已推送";过程态如实显示。
7. **隔离沿用现有 ERP 模块约定**:per `user_id`(老板可见员工=tenant join),**不为 express 另搞 RLS/新隔离模型**;Agent token 只能取本连接队列。
8. **大厂级硬约束**:单文件<500、单一职责、schema 走迁移不走 ad-hoc、SQL 参数化、钱用 decimal、时间存 UTC、每新文件≥1 测试、去 AI 味注释、Conventional Commits。见 `docs/ENGINEERING_STANDARD.md`。

## 5. 阶段与验收(PM 按此发棒)

| 阶段 | 内容 | 关键验收 | 状态 |
|---|---|---|---|
| **P1 后端** | 复用 erp_endpoints/erp_push_logs/映射/前端日志异常 Tab;净增=express adapter 分支 + 映射器 + 置信入队 + Agent API(lease/ack/token)+ ALTER 两列。全 flag-off | 无头 E2E:建 express 连接→入队 pending→lease→ack→success;失败转 manual;低置信直 manual;白名单拒 PDATAT;映射器 PTT 样例分录平衡;单测齐 | 🔜 施工单 `02-phase1-backend.md`(已按"最大复用"重写) |
| **P2 本地 Agent** | RPA 录入(主)+ DBF 直写(护栏),打通 `DATAT` 测试套 | 真机:一张样例发票从 Pearnly 队列 → Agent → DATAT 里真出现一张 RR 单、分录正确;账套白名单拒写验证 | 待 P1 验收后发 |
| **P3 前端** | 照 `01-ui-design-brief` + 原型,用 Vite/TS/设计令牌重做四 Tab | 真站:连接向导全程、推送中心实时流转、异常审核、暗夜、泰语;过 lint-ui 闸 | 待 P2 验收后发 |
| **P4 闭环** | 真实 OCR 票 → 自动推送 DATAT → 异常回审 全链路 | Owner 真机走一遍 happy/异常/Agent 离线三路 | — |

## 6. 状态追踪(PM 维护)

- 2026-06-20:总纲 + 设计定稿 + 原型存档完成。
- 2026-06-20:PM 实读现有 ERP 代码 → P1 施工单按"最大复用、Express 作新 adapter、只补 Agent 差量"重写。
- 2026-06-20:**P1 施工完成 + PM 验收**(worktree `feat/express-push` `3945c8c2`,未 push)。PM 亲验:① 全量代码 review(4 新模块 + 4 共享件纯加法 diff)= 高质量、合规、additive-only、flag-gated、铁律#12、decimal、SKIP LOCKED 租约、双账套白名单。② 亲跑 32 express 单测 = 通过。③ 亲跑**真 Postgres E2E**(worktree 代码连 prod DB·测试账号 audit_accountant·自清)= **13 PASS / 1 FAIL**,残留 1 endpoint 已手动清,prod 干净。
  - **找到 1 个真 off-by-one(P1.1 必修)**:express 队列行起始 `attempt=1`(沿用通用路由约定),而 `ack` 把 attempt 当"Agent 失败次数",导致 **2 次失败即转 manual**(非设计意图的 3 次;`_MAX_ATTEMPTS=3` 与 docstring 都说 3)。不危险(无重复推送/白名单/幂等均已证),但须修正使"3 次失败→manual"成立、E2E 转绿。
  - **PM 拍板**(Owner 的 4 问):① classify 哨兵接缝 = 批准(additive·其它 adapter 0 影响)。② `manual` 进异常 Tab = **延 P3**(建统一复核 UI 时给 `list_push_exceptions` 加 `status in('failed','manual')`;当前 manual 在 `/api/erp/logs` 可见,不隐形)。③ endpoint 成功计数轻微虚高 = 用户可见 KPI `/api/erp/stats/today` 按 status 派生(pending 不计 success)故对外诚实;内部计数器洁癖**延 P2**修。④ 缺付款默认 RR = 批准(B2B 保守·可配)。
  - 下一步:发 **P1.1 微修**(off-by-one + E2E 转绿)→ 绿后 merge(flag 仍 off)→ 起 **P2 本地 Agent**(RPA + DBF 打通 DATAT)。
- 2026-06-20:**真机情报(Owner 截图)+ P2 RPA 路线修正**。① Express 是**客户的 ERP**,Owner **不是** Express 操作员、看不懂 —— "Owner 录一遍正常录入"的设想作废。② RPA 真键序确认本质是「会 Express 的人 + 真机」的活,且**一套 Express 版本只录一次、全客户复用** → 定为**部署期任务**(与客户 Express 操作员一次性做),不压 Owner。③ **真坑**:DATAT 测试账套会计期 = 01/01/2558–31/12/2559(2015–2016),工作日/单据日超期 Express 直接报错(Message#70/#71)→ 测试票须用该期日期(真客户账套无此限)。④ 菜单路径实证:采购赊购 = `1.ซื้อ → 4.ซื้อเงินเชื่อ`(RR);DATAT 公司名 = บริษัท มานะชัยบริการ จำกัด(P:\70EXP\TEST·DB_ver 1.94)。⑤ 决定:P2-RPA 真机步挂起待操作员;同时**前移 P3 前端**(不碰客户 Express、Owner 能看能验)。
- 2026-06-20:**P3a 前端(连接卡 + 接通向导)PM 验收通过 + 弹窗改双栏**。worktree `feat/express-fe`。初版小弹窗→按 Owner 要求改原型双栏宽布局(左竖排步骤+右内容大卡片·`e482ef0a`)·29/29 真浏览器·令牌纯净·逻辑零改。Owner 抓出第 2 步两张截图是改布局前残留(命名漏洞非渲染 bug)→已重截清残·6/6 补验。19 张全双栏。**未 push**。决定:不加首页入口卡(同 DMS 走 ERP 卡)·不动 lint-ui baseline(既存漂移非本棒)·合并时再 bump。**起 P3b**(分录预览抽屉 + Express 设置区)。
- 2026-06-20:**P2a ①段(本地 Agent 离线核心)PM 验收通过**(worktree `feat/express-agent`)。读真码确认安全闸三重锁(`ALLOWED_ACCOUNT_SETS=("DATAT",)` + `rpa_flow_confirmed=False` 默认拒真录入 + 逐操作白名单);dry-run 输出与映射器一字不差;闸全绿、tools/ 隔离、未 push。②段 RPA 真录入:施工窗口诚实报"Linux 环境无 Express 不能驱动",gated 骨架已布、键序待真机勘探。**不写猜的键序**(改:用 Owner 真截图让施工窗口搭 grounded 草稿,仍锁)。
- 2026-06-20(PM 全链复读 · 真状态盘点):读真码 + 摸 companion 独立 repo,确认整条链当前位置。**已上线 master**:P1 后端(`e0091fe0`+off-by-one `e26fd829`)、express 进 ADAPTER_REGISTRY(`b6d8145b`)、Agent API `routes/erp_agent.py`(lease/ack/heartbeat)、前端 P3a 连接卡+向导 / P3b 分录预览抽屉(`2f1deffc`→`86613669`)。**companion**(`D:\pearnly-companion` 分支 `feature/express-companion-dbf-sales` HEAD `9e2de78`·未并 companion master):queue_client 已接我们 `/api/erp/agent/*`(Bearer);`purchase_adapter` 字段与云端进项载荷**逐字段对齐**;`dbf_writer.write_purchase`+`dbf_sales.write_sale` 六表全写 + 全护栏(DATAT 白名单 `("70exp","test")`/备份/回滚/读回+借贷校验/重建 CDX/ref_no 幂等);111 测试过(4 失败全是 RPA/OCR 真机依赖)。**真机已证**:进项端到端(队列→companion→DBF→ack·`RR581215-004`)、销项 DBF 写盘(`IV581215-001`)。
  - **PM 定位的缺口(按这个发棒)**:① 🔴**唯一未代码层证到的同一件事** = 真 Express 读 DBF 直写的两张单 + CDX 兼容 → 留 Owner 真机验(见 `11-...cheatsheet.md §5`),验完施工窗口从备份还原。② **云端发件箱产不出销项** = `mapper.py` 纯进项、载荷不带 `direction`、`_grade` 写死 purchase → companion 销项路由收不到货(现进项能通只因 companion 默认兜底 purchase,脆)。→ 发**施工单 `12-cloud-sales-mapper-and-direction.md`**(云端加销项 mapper + direction,与 companion `sales_adapter` 契约对齐)。③ companion 默认 `method='rpa'`(旧 P2.7 契约·OCR 真机依赖)→ DBF 是已证主路,部署须 `method='dbf'`;RPA 暂泊(留部署期与操作员)。④ 部署 P4:companion 打包安装 + token(`exp_<endpoint_id>_<secret>`)下发 + 开 flag。
- 2026-06-22:**接真客户前·生产就绪派工**(Owner 拍"四件都做、按序发")→ 见 `11-production-readiness-dispatch.md`。活动队列 **T0→T1→T2→T4**(T3 代码签名 Owner 2026-06-22 暂缓冻结)。★同日 Owner 提醒后修正:`express_pw` 唯一活跃用途是夜间 PACK,而 PACK 默认 off、writer 已设 `CMPLAPP='Y'`+per-write reindex(`PITFALLS_AND_FLOW.md` §0)→ 插 **T0 逆向 spike**(不 PACK 报表是否可见)在前,**T1 由"加密密码"改"删字段优先/加密兜底"**,删掉这个默认用不到的客户会计密码才是首选。**T0 已跑完**(`13-...findings`):PACK 必需(241 报表 PACK 前缺单→PACK 后精确填回)→ Owner 拍 **T1 走加密存**(否决删字段),且定**前瞻共用设计**:`express_pw` 语义=方法无关的「Express 登录」,直录喂 PACK 登录、未来 RPA 当登录口,**一处输入一处 DPAPI 加密双方法共用**(`secret_store.load_express_login()` 收口·单输入框扩展性)。「writer 端免登录复刻 PACK」单列将来优化。T2(2026-06-22 Owner 拍板**翻版**):**账套白名单全开·去逐账套审批·客户自选·选错是客户的事·我们只保证数据正确落入所选账套**(§4.1"只允许 DATAT"边界被此决策覆盖·`16-` 已重写·与 T5 客户选账套合流·保留"写不错地方"的数据正确性闸)。T5 优化小助手配对窗。T6 瘦身·T7 防逆向(昨日讨论补登)。T4 工程债。诚实现状:已"休眠上线"(flag ON)但 0 端点在用、账套写入仍锁 DATAT,本批推到"第一个真客户能真在用"。状态卡那条 `test_adapter_registry_intact` 红点已过期——测试已更新含 `express`、现已绿。
- 2026-06-20:**P1.1 微修完成 + PM 验收**(worktree `70f3ce00`)。PM 读真 diff 确认:`ack` 改为起始 1 校正(`prior=attempt or 1`·`agent_failures=prior`·`>=_MAX_ATTEMPTS(3)` 才 manual)→ 精确 3 次失败转 manual·shared 路由 attempt=1 约定不动·其它 adapter 零影响;E2E 用例改断言 `["pending","pending","manual"]`。**ACCEPTED**。E2E 我按 Owner 指示不自跑;上轮真 PG 已证 13/14(唯一 fail 即此 off-by-one,SQL 路径未变),本修仅改 unit 覆盖的 Python 逻辑 → 残留风险≈0。**14/14 真 PG E2E 设为合并后部署门**(prod venv 跑)。下一步:合并 P1(flag off·部署即休眠)→ 起 P2a。
