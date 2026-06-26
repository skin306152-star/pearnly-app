# Express Push · 接真客户前 · 生产就绪派工总单(PM 主导)

> PM:Claude(Opus 4.8)。Owner:skin3。2026-06-22。
> 背景:Express Push 已"休眠上线"(prod `11850926`·flag `ERP_PUSH_ENABLED` ON·下载/配对/DBF 直写真机证过)。但当前 **0 个 express 端点在用**,且账套写入仍锁死 `DATAT` 测试套——所以现状是"具备接第一个真客户的条件",不是"在用"。
> 本单 = 把"已上线"推到"第一个真客户敢托付、能真在用"之间的全部缺口,Owner 拍板「都做,按顺序发」。
> **五字要求(Owner 定):简单 · 方便 · 快捷 · 精准 · 兜底。** 与 `00-master-plan.md` §4 全局边界冲突时以总纲为准。

---

## 派工顺序与理由(PM 排序)

| 棒 | 施工单 | 为什么这个序 | 外部依赖 |
|---|---|---|---|
| **T0** | 逆向 spike:DBF 直写单不跑 PACK 是否报表可见 | 🔴 **前置 T1 的命门**。`express_pw` 唯一活跃消费者是夜间 PACK(RPA 暂泊),而 `pack_enabled` **默认 OFF**、writer 已设 `CMPLAPP='Y'` + per-write reindex。先证清"不 PACK 能不能见",才知道密码是该**删掉**还是该加密。 | 真 Express(DATAT·工具链已备) |
| **T1** | 凭证处理(删 or 加密·由 T0 定) | 🔴 接真客户的安全门:`express_pw` 是客户 Express 登录密码,当前明文存 APPDATA(`config.py:87` 挂 TODO)。**T0 证 PACK 非必需 → 删字段(首选)**;证必需且 Owner 要无人值守 → 才 DPAPI 机器绑定加密。 | 取决于 T0 |
| **T2** | 账套全开 · 客户自选所选账套(去 DATAT 白名单·去 Owner 审批) | **Owner 2026-06-22 拍板覆盖**:白名单全开·激进上生产·客户从探测列表自选·选错是客户的事·我们只保证数据正确落入所选账套。与 T5 选择合流。`16-` 已翻版重写。 | 无(Owner 已拍全开) |
| **T3** | setup.exe 代码签名 | 装机体验门:124MB 无签名包,会计事务所 SmartScreen 会拦/吓退。**卡在 Owner 采购 OV/EV 证书**——施工单写好,拿到证书才能跑。 | 🔒 Owner 买证书 |
| **T5** | 优化小助手配对窗(砍黑话·自动探测账套·可最小化) | Owner 真机反馈(昨日讨论·之前漏登·补)。客户不该填账套目录/行号/PACK 日期——小助手已能探测,改成"列公司名给客户选"。决定客户第一眼会不会用。`17-t5-companion-pairing-ux.md` | 无 |
| **T6+T7** | 小助手打包收口:瘦身 + 防逆向(合一单 `19-`) | Owner「做完彻底闭环再上线」。瘦身大肥肉=cv2/numpy(~60MB)只服务暂泊的 RPA·DBF 主路不用→懒加载+spec 排除;防逆向=PyArmor 混淆。**改打包·要重打重验**。 | 🔻**排最后**:窗口1+2 功能落地+真机验后才做 |
| **T4** | 工程债收口 | 无客户影响:PollWorker/step_poll_loop 抽共享壳 + pack_contract 共享 exit 码。**Owner 2026-06-22:并入最后 companion 棒一起做**(纯重构·行为不变·单独 commit 可隔离·注意与 T9 同碰 PACK 区·pack_contract 须尊重 pack_runner「不 import companion 包·32 位最小依赖」约束)。 | 无 |

- 2026-06-22:**companion 功能 build 全验过(已知好版本)**。窗口1 重建 64 位 companion.exe(109.7MB·当前码·未瘦身)+ **T5 配对窗真机视觉验收三点全过**(三栏精简/自动探 5 真账套真公司名下拉/最小化非置顶·截图 outputs/t5)+ **DATAT 真机端到端**(选账套→`load_express_settings` seam→三重闸→直写 RR581220-004 CMPLAPP=Y→frozen pack_runner 解密登录→PACK exit0→robocopy 还原 8 表 ALL_MATCH)。PM 读码+consistency.py 三证闸验收通过。坑:本测试机 harness 拦 `taskkill /F`/部分 `Remove-Item`(测试环境怪癖·非产品·数据终 ALL_MATCH)。新 setup.exe 未打(随 T6/T7 重打)。dbf_writer.py 530 留 T6/T7 同拆。
- 2026-06-22:**T9 PACK 前自动备份**(`20-t9-pre-pack-backup.md`·Owner 拍要)。PM 查实:写盘前有 `_backup`、**PACK 前没有**。补:`pack_scheduler` PACK 前备份选定账套整目录·**备份不成不 PACK**(fail-safe)·磁盘守卫·保留最近 K 份·失败留快照。接真客户前堵"PACK 中途异常伤整套账"的唯一口。**与 T6/T7/图标同窗口同次重打重验。**
- 2026-06-22:**T8 网页向导收口**(`18-t8-wizard-consolidation.md`)。Owner 真机两病:① 已装小助手仍被逼每次重下 124MB 才能生成密钥(`_genToken:329` 硬拒 `!downloaded`);② 选账套网页+小助手重复。决策:**账套只在本地小助手选(登录已被迫本地·顺手·不跳转)·网页 step3 改只读状态镜像**;下载可跳过(`connected` 即证已装·"完成"条件去 `downloaded`)。后端小补:heartbeat 收小助手上报的所选账套→`cfg.account_set`。**跨窗依赖:窗口1 选完账套要随 heartbeat 上报 selected account_set**。与 T2-A 同窗(pearnly-app)一起做。

- 2026-06-22:**模拟录入(RPA)研究 + 施工方案**(`21-rpa-simulated-entry-research-and-build.md`·Owner 开第二录入方式)。PM 读半成品真码定:现有 = cv2/SIFT 图像匹配盲做·**核心过时**→ 重做为 **pywinauto 控件驱动**(对齐 pack_runner·真机已验)。捡:字段模型 + "OCR 仅验证不读数据"纪律 + 流程骨架。架构大半就绪(方向云端已判·队列/映射/设置/凭证全共用·契约回本)→ 净增 `rpa_flow` + `method=rpa` 分支。分阶段:P0 真机勘探录入键序(采购+销项·Codejock grid 键盘盲打)→ P1 建 rpa_flow → P2 安全闸(占用/幂等/所选账套/失败安全)→ P3 真机验。**worktree 隔离·不阻塞 DBF 上线·两边落地后合**。诚实:DBF 更稳·RPA 第二可选非取代。

> **昨日讨论复盘(2026-06-22 PM 从会话 `279ebe22` 挖回)**:Owner 昨日把一整包讨论"纳入待定明天做"。对账:套账自动探测=**T5** / PACK 后台驱动免界面=**T0**(验:不行) / 取消密码=**T0/T1**(验:删不掉·改加密) / 凭证扩展性=**T1**(本地输入·共用) / 录完可见=**T0**。**之前漏登、现补**:T6 瘦身 · T7 防逆向 · 背景讨论项「Express 数据导出供用户手动导入 MR.ERP」(Owner 言"只是讨论下"·暂存背景候选·未立单) · 「直录 vs 模拟录入 用户使用说明文案」(并入 T2-C runbook + 面客文档)。**账套白名单**:Owner 昨日言"全部打开"·今日(2026-06-22)明确拍板 **全开·不要逐账套审批·激进上生产·客户自选·选错是客户的事·我们只保证数据正确落入所选账套**。→ **T2 已翻版**:去 DATAT 白名单 + 去审批机制·锁定=客户所选账套(与 T5 合流)·保留数据正确性闸(写不错地方)。前稿"逐账套审批"作废。

> 守门铁律(每一棒都守):net-new 隔离不碰登录/OCR/计费/现有推送(总纲 §4.3);改 dist 必 bump `home.html ?v=`;companion 改动每新文件 ≥1 测试;Conventional Commits;单文件 <500;去 AI 味注释;DBF 白名单护栏一行都不能松。

---

## ★可扩展性契约(直录/模拟录入共用 · Owner 2026-06-22 定 · T5/T8/T2-B/T1 都守)

> Owner:这些配置/向导逻辑必须**方法无关**——将来加模拟录入(RPA)直接插,不返工、不新增配置填写。同 T1 共用凭证的道理,推广到全套设置。

1. **配置 = 方法无关核心 + `method` 开关**。共用字段(两种方式都要):Express 位置(`express_root`/`express_exe`)、登录(`express_user`+`express_pw`·T1 已共用)、**所选账套整组**(`account_dir`+`account_company`+`account_set_row` 公司 grid 行+账套名)、`method∈{dbf,rpa}`。**绝不搞 method 前缀的重复字段**(不要 `dbf_account`/`rpa_account` 两套)。一次配置,两种方式都读。
2. **账套选择(T5)一次产出整组、含 `account_set_row`**。DBF 用 `account_dir` 写文件;RPA 用 `account_set_row` 登录后在公司 grid 导航。客户**选一次账套**就把两者都推出来 → RPA 来了**零新增输入**。
3. **向导(T8)里 `录入方式` 是唯一方法专属 UI**。登录 + 账套状态对两种方式**一视同仁**展示;`method=rpa` 时复用同一份登录 + 同一个账套选择,**不弹新字段、不改 step 文案逻辑**。
4. **消费端留干净 seam(仿 T1 `load_express_login`)**。companion 一个共享"读设置"口(Express 位置 + 登录 + 所选账套),DBF 路径与未来 `rpa_flow` **都调它**;`method` 只切"怎么落账"(直写 vs 驱动 GUI),**不切"读哪份配置"**。
5. **字段别按 method 阉割**。登录/账套/Express 位置三样**无论选哪种方式都收齐**(DBF 也要登录跑 PACK·RPA 也要这三样)→ 别做成"选 DBF 才收 X"导致切 RPA 要补收。
6. **「工作日 `วันที่ทำการ`」= 方法无关的自动值(默认今天)**。Express 登录选账套后必弹"工作日",须落在该账套**会计期**内否则报错(Message#70/#71)。真客户账期=当前年→今天恒有效;测试账套 DATAT 冻在 2558–2559→填该期日期(隐藏/高级·非客户字段)。**直录 DBF 写盘不撞此弹窗**(不开 Express),只 PACK 登录时撞→自动填今天;**未来 RPA 驱动会撞**→同样自动填今天。→ 把现 `pack_workdate`(PACK 专属命名)**泛化为方法无关 `express_workdate`**(默认今天·PACK 与未来 RPA 共用·客户不可见·测试期可隐藏覆盖),别让 RPA 另起一个工作日字段。

---

## T0 · 逆向 spike:不跑 PACK 报表是否可见(先做 · 决定 T1 形态)

**为什么**:`express_pw` 的唯一活跃用途 = 夜间 PACK 登录 Express(`pack_runner.login_and_open` → `type_keys(pw)`)。RPA 已暂泊。而:① `pack_enabled` 默认 OFF;② writer 已设可见性开关 `CMPLAPP='Y'`(`PITFALLS_AND_FLOW.md` §0 实证根因);③ writer 每次写完 `_reindex()` 重建 CDX。**若不 PACK 报表也能见 → 我们在收一个默认用不到的客户会计密码 → 该删不该藏。**

**已有线索(别从零起)**:`D:\_express_audit\diag_flags.py`(量 CMPLAPP/POSTGL 分布)、`patch_cmplapp.py`(补标志 + reindex 验可见)正是这条线,但**没干净隔离验证 "writer 全套护栏 + 不 PACK" 的可见性**。

**spike 步骤(DATAT·写前 robocopy 备份·完事还原回基线)**:
1. `partB_write.py` 写一张全新非存货 RR + IV(落 2558 账期·writer 真实路径·CMPLAPP=Y + per-write reindex 都走)。
2. **跳过 PACK**(不跑 `p32_pack*`)。
3. 全新登录开报表 241(进)/141(销)+ 采购/销售放大镜查这两张单 → **截图存证**(对照 `EVIDENCE_*` 命名)。
4. 判定:
   - **见得到** → PACK 对常规可见性非必需 → 出结论"DBF 部署不需 PACK、不需密码"。
   - **见不到** → 记录"差什么"(再 PACK 一次复现可见,确认差的就是 PACK 那步全系统重整);评估能否由 writer 端补齐(如写 `DBINF` 标志/全表 reindex)避免登录式 PACK。

**交付**:`13-pack-necessity-findings.md`(结论 + 截图证据 + 对 T1 的裁决)。**PM 读证据判,不自跑。**

**裁决树**:
- T0 = 不需 PACK → **T1 = 删 `express_pw` 字段**(配对不再收、config 去字段、pairing/pack 相关入参清理、存量 config 静默丢弃该键)。这是首选——消灭债不是缓解债。
- T0 = 需 PACK 但可由会计手动/在场时跑 → T1 = 仍删密码,onboarding(T2 runbook)写明"PACK 由事务所自理",`pack_enabled` 保持 off。
- T0 = 需无人值守 PACK 且 Owner 要这个便利 → **才** 落下方 T1-加密方案。

---

## T1 · 立 canonical「Express 登录凭证」· DPAPI 加密 · 双录入方式共用

> **Owner 2026-06-22 拍板(T0 证 PACK 必需后)**:存,走加密。且**前瞻设计** —— 这个凭证不是"DBF 专用 PACK 密码",而是**方法无关的「Express 登录」**,一处输入、一处加密存储,按录入方式分流给不同消费方:
> - **直录(DBF)** → 凭证喂**夜间 PACK 登录**(写盘本身不登录·PACK 为让报表可见,见 `13-pack-necessity-findings.md`)。
> - **模拟录入(RPA·后续开发)** → 同一凭证作**驱动 Express 的登录口**(登录→拉套账→录入保存)。
> 输入框 + 存储一次做好扩展性,RPA 上线直接复用,不另起密码框、不返工。

**问题(实测)**:companion 把 `express_pw`(客户 Express 登录密码)明文写在 `%APPDATA%` 的 config 里(`config.py:87`)。任何能读那台机器用户目录的人/进程都能拿到客户会计软件密码。

**目标**:配对时输入的 Express 登录账号/密码,落盘即加密;只有同一台机器、同一 Windows 用户能解密;明文绝不落盘、绝不进日志。**凭证语义 = 方法无关的 Express 登录**,DBF/RPA 共用。

**前瞻设计要点(扩展性·一次做对)**:
- config 的凭证字段语义定为「Express 登录」(`express_user` + `express_pw`),**不绑定到具体方法**;注释/文档别写成"PACK 密码"。
- 统一收口 `secret_store.load_express_login()`(返回 user+pw·解密只在内存)。消费方:① `pack_runner.login_and_open`(DBF 的 PACK)② 未来 `rpa_flow` 的登录步——**都调这一个口**,不各拿各的。
- 配对向导 FE:单个「Express 登录」输入区,选 DBF 或 RPA 都显示同一个框(DBF 也需要它跑 PACK);文案"用于登录你的 Express(夜间数据重整 / 模拟录入)"。**不做两个方法各一个密码框**。
- 加密只到凭证落盘层,与"谁消费"解耦——将来加 RPA 不动加密层。

**实现要点(companion repo `D:\pearnly-companion`)**:
- 用 Windows DPAPI(`CryptProtectData`,`CRYPTPROTECT_LOCAL_MACHINE` 关掉只用用户态 = 机器+用户双绑)。Python 走 `win32crypt.CryptProtectData` 或 `ctypes` 直调,**不引重型加密库**。
- config 里 `express_pw` 字段改存 base64(DPAPI blob);新增 `pw_enc_version` 标记加密方案,便于将来轮换。
- 读路径:`pairing` / 托盘 worker 用到密码处统一走一个 `secret_store.load_express_pw()`,解密只在内存、用完不留。
- **存量迁移**:启动时检测到明文(无 `pw_enc_version`)→ 就地加密回写 → 清明文。一次性、幂等。
- 日志/异常**绝不**打印密码或 blob(沿用既有"只元信息"纪律)。

**边界**:① 只动 companion 凭证存取,不碰云端、不碰 DBF 写盘逻辑。② DPAPI 解密失败(换机器/换用户/profile 损坏)→ 友好提示"请重新配对",不崩、不写脏账。

**验收(真机清单 · 施工窗口跑齐交结果,PM 读报告判)**:
1. 全新配对 → 看 config 文件,`express_pw` 是 DPAPI blob 不是明文;`pw_enc_version` 存在。
2. 托盘 worker 能正常解密并完成一次 DBF 直写冒烟(借贷平、ack success)——证明加密不破功能。
3. 把同一 config 拷到**另一台机器/另一用户**,启动 → 解密失败 → 提示重新配对、不崩、不写账。
4. 存量明文 config 启动一次 → 自动加密回写、明文消失、功能不变。
5. 全程 grep 日志:无密码、无 blob 明文。
6. companion 单测:加密/解密 round-trip + 存量迁移幂等 + 解密失败兜底,≥3 个新断言。

---

## T2 · 账套白名单逐账套审批机制 + onboarding runbook

**问题**:`ALLOWED_ACCOUNT_SETS=("DATAT",)` 写死。真客户的账套(如 `58ASIASP` 等)代码层一律拒写。要接真客户,得放开——但**绝不能一刀放开**(总纲 §4.1:误写别的账套是账务事故)。

**目标**:把"允许写哪个账套"从硬编码常量,改为**云端逐端点配置 + Owner 显式审批**,companion 从配对探测+云端下发拿到"本连接唯一允许账套",仍保留末两段路径+公司名硬闸。

**实现要点**:
- **云端**:`erp_endpoints.config` 增 `approved_account_set`(单值,Owner 审批后写入)+ `account_set_approved_at/by` 审计。配对时 heartbeat 已上报 `reported_account_sets`(候选);Owner 在管理侧从候选里**选一个**批准(不是自由填,防手滑)。
- **companion**:`ALLOWED_ACCOUNT_SETS` 不再写死,改为"配对时云端下发的 `approved_account_set`";DBF 写盘前的**三重硬闸照旧**(末两段路径匹配 + 公司名匹配 + ref_no 幂等),只是允许值来源从常量变下发。下发值缺失/为空 → 拒写(fail-safe)。
- **审批是 Owner 动作**:做一个最小管理入口(可先 API + 一句话操作说明,UI 延后),Owner 一条命令/一次点击把某端点的某候选账套标 approved。**默认仍只 DATAT**,未审批的端点写不进任何真账套。
- **onboarding runbook**(本单交付文档,`14-onboarding-runbook.md`):一家新事务所从 0 到能用的全步骤——装小助手 → 配对(生成 `exp_<endpoint_id>_<secret>`)→ heartbeat 探账套 → Owner 审批账套 → `method=dbf` → 首张票冒烟验收 → 上线。含 RPA 键序与操作员一次性勘探的挂起说明(DBF 是已证主路,RPA 暂泊)。

**边界**:① 不放开成"任意账套",必须 Owner 逐个批。② DATAT 仍是默认/测试通道,机制改造不破现有休眠态。③ 不碰 DBF 写盘三重硬闸的判定逻辑,只换"允许值"的来源。

**验收**:
1. 新建一个 express 端点、不审批 → companion 配对后**写不进任何真账套**(只 DATAT 或拒)。
2. Owner 审批某端点 = `58XXX`(从 heartbeat 候选里选)→ companion 下发拿到 → 能写该账套、且**只能写该账套**(试写别的 → 硬闸拒、不落盘)。
3. 下发值为空/缺失 → fail-safe 拒写。
4. 审计字段(approved_at/by)落库。
5. 云端单测覆盖"未审批拒/审批后单账套放行/空值拒";companion 单测覆盖"下发值驱动白名单 + 硬闸不变"。
6. runbook 文档可被一个没碰过这项目的人照着走通(PM 读 runbook 判完整性)。

---

## T3 · setup.exe 代码签名(🔒 卡 Owner 采购证书)

**问题**:`PearnlyCompanion-Setup.exe`(124.5MB)无数字签名。Windows SmartScreen 对未签名安装包弹"未知发布者/可能有害",会计事务所大概率不敢装。

**Owner 必须先决定/采购**(施工窗口无法替代):
- 买一张 **OV 代码签名证书**(标准,SmartScreen 信誉需累积)或 **EV 代码签名证书**(贵,但即时通过 SmartScreen、需硬件 token/云 HSM)。PM 建议:若近期要铺多家客户,直接上 EV 免信誉爬坡;若先 1–2 家试点,OV 够用。
- 证书签发给 Pearnly 的公司主体。

**实现要点(拿到证书后)**:
- `packaging/installer.iss` 出包后,对 `companion.exe`、`pack_runner.exe`、`PearnlyCompanion-Setup.exe` 三个都用 `signtool sign /fd sha256 /tr <时间戳服务器> /td sha256` 签名(含 RFC3161 时间戳,证书过期后已签的仍有效)。
- 签名步骤固化进打包脚本/文档,别手签漏签。
- 顺手把 `installer.iss` 的 `ArchitecturesAllowed=x64` 改 `x64compatible`(backlog 项,避免新版 Inno 警告/未来 ARM)。

**验收(拿到证书后跑)**:
1. 右键 setup.exe → 属性 → 数字签名,显示 Pearnly 主体、时间戳有效。
2. 干净 Windows 机器双击安装 → **不弹** SmartScreen"未知发布者"(EV)或弹后"更多信息"显示已验证发布者(OV)。
3. 装完两个 exe 也都已签名。
4. 静默装→弹配对窗→卸载干净(回归 P4 真机链)。

> **当前状态:Owner 暂缓(2026-06-22)**。签名先不做——施工单冻结存档,将来要铺多家客户/事务所反馈装机被拦时再解冻。不影响 T1/T2/T4。

---

## T4 · 工程债收口(垫底 · 无客户影响)

来自 P4 收尾 backlog,纯重构、零行为变更:
- `PollWorker` 与 `step_poll_loop` 抽共享循环壳(消除两份轮询骨架)。
- `pack_contract.py` 共享 exit 码 + tasklist 探测(companion 与 pack_runner 各有一份常量,易漂移)。

**验收**:行为零变更(diff 纯结构);既有 companion 单测全绿、不增不减语义;`/simplify` 过一遍。**放在 T1/T2 上线、有真客户跑通后再做**,避免重构期撞真客户问题。

---

## PM 维护 · 状态追踪

- 2026-06-22:Owner 拍板"四件都做、按序发"。本单为派工总纲。
  - T3(代码签名)Owner 当日暂缓,冻结存档。
  - **同日修正(Owner 提醒"逆向看是否取消账号密码")**:PM 读 companion 真码 + `PITFALLS_AND_FLOW.md` 确认——`express_pw` 唯一活跃用途是夜间 PACK,而 PACK 默认 off、writer 已设 `CMPLAPP='Y'` + per-write reindex。原 T1"加密密码"误把前置问题跳过了。→ **插 T0 逆向 spike**(不 PACK 报表是否可见)置于 T1 前;T1 由"加密"改为"删字段优先 / 加密兜底",形态由 T0 裁决。
  - 活动队列:**T0 → T1 → T2 → T4**(T3 冻结)。
- 2026-06-22:**T0 spike 跑完 + PM 验收**(`13-pack-necessity-findings.md`·DATAT 零污染回基线)。**PACK 必需**(241 报表 PACK 前 10 张缺 RR581220-004 → PACK 后 11 张精确填回·唯一变量是 PACK)。PM 摆 A/B/C 三路,**Owner 拍 A(存·DPAPI 加密)** 且定**前瞻共用设计**:凭证语义=方法无关的「Express 登录」,直录喂 PACK 登录、未来 RPA 当登录口,一处输入一处加密双方法共用。→ **T1 已按此重写**(canonical 凭证 + `secret_store.load_express_login()` 收口 + 单输入框扩展性)。C「writer 端免登录复刻 PACK」单列为将来优化,不阻塞。
- 2026-06-22:**T1 施工单已出**(`15-...`)。新 `secret_store.py`(DPAPI)+ config 语义改「Express 登录」+ 存量明文启动即迁移 + pack_runner 32 位自带 ctypes DPAPI 解密 + 7 项真机验收。
- 2026-06-22:**T1 施工完成 + PM 代码层验收通过**。PM 读真码确认接线:`secret_store`(win32crypt·UI_FORBIDDEN·空密码不加密·migrate 幂等且空也升版·收口 `load_express_login`)+ `pack_runner.resolve_express_pw`(32 位 ctypes crypt32·同 0x1 flag·按 `pw_enc_version` 分流·解密失败返空不崩·接进 `login_and_open`)。`test_secret_store` 10 断言过·169 既有单测过(4 既有 OCR/RPA 真机依赖失败·stash 后同样失败=非 T1 引入)·全文件<500·ruff 过。**§5.1/5.5/5.6/5.7/5.3 真机/确定性已证**(配对落盘=密文+v1+user 明文 / 迁移幂等 / 日志无明文 / 本地配对窗单框掩码 / 32 位解 64 位 blob=原文)。
  - **★施工修正(PM 采纳·进 canon)**:凭证录入点 = **companion 本地配对窗 `gui_pairing`,非云端 web 向导**(密码属装 Express 的机器·上云=安全倒退)。原 ticket §3.6 假设错·已改。pearnly-app 零改动、无需 push。
  - **未收口的一项(PM 拍:要跑)**:frozen `pack_runner.exe` 端到端 PACK 烟测(重建 32 位 exe → DATAT 备份/PACK/还原一轮)。各环节已分证·但冻结 exe 是发客户的产物 + 凭证 + 写账路径·frozen 坑有前科(cp874/stdout None)→ 花一轮 DATAT 把"很可能"变"证毕"。**跑完即收 T1。**
- 2026-06-22:**T2 施工单已出**(`16-t2-account-set-approval.md`)。PM 读两边真码定位白名单 4 写死点:云 `account_set_allowed`/`ALLOWED_ACCOUNT_SETS`(C1)、companion `ALLOWED_DIR_TAIL`(C2)/`purchase_adapter.ALLOWED_ACCOUNT_SETS`(C3)、PACK `account_company`(C4·已 config 驱动)。机制:Owner 从 heartbeat 候选选一个审批 → `endpoint.config.approved_account_set` → 云端 + companion 白名单期望值都读它·**三重闸逻辑不动只换期望值来源**·未审批=仍只 DATAT(fail-safe)。三段:T2-A 云审批模型+逐端点+审批/撤回路由+下发 / T2-B companion 允许值换下发 / T2-C `14-onboarding-runbook.md`。**真正放开某客户账套仍 Owner 逐个拍·本单只建机制。**
- 2026-06-22:**T5 补登**(`17-t5-companion-pairing-ux.md`)。Owner 真机截图反馈——配对窗逼客户填账套目录/神秘行号/PACK 日期。**此项昨日讨论过但交接卡 backlog 漏记·PM 之前 T 清单遗漏·现补**。改:砍三处黑话(`account_probe` 已能探测账套→改"列真公司名给客户选"·自动推 dir/行号/account_company)+ PACK 日期默认今天客户不可见 + 窗口加最小化不强制置顶。改后客户只碰:配对码 + 登录账密 + 选账套。companion only·pearnly-app 零改。建议紧随 T1、与 T2 并行。
