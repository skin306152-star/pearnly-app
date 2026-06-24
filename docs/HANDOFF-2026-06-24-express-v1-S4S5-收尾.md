# 交接 · 2026-06-24 「Express 全自动 v1 收口(S5 / defer① / S4)+ 全语料真机验证」窗口收尾

> 给下一个窗口/接手人。只写**事实**与**待办**。承接 `HANDOFF-2026-06-23-绑主体面板-收尾.md`(那份的 ④ 绑主体面板已上线)。
> 收尾时 prod = pearnly-app master `d8c7cd8f`(本窗口最后一笔自有 commit `fb245dc9`,其后是别窗口 LINE 工作)· companion **1.1.11**(prod latest.json)· 网站正常。

---

## 〇、本窗口一句话
把 Express 全自动 **v1 的 S5 / defer① / S4 三件全部做完上线**,并用一整套语料(51 张测试发票)在真机 DATAT 上跑了**端到端验证**——核心账务管道(方向/金额/去重/科目/主档建档)**稳**,但测试**如实暴露了一批"防呆闸"缺口**(币种/日期/押金/折让),已列 backlog。

---

## 一、本窗口【已完成并上线】

### S5 — 科目保守版收口(来源诚实化 + 落默认标「待核」)
- prod commit `62626323`(feat)+ `29e22bb8`(test E2E)。CI 6/6 绿。真站 E2E **5 PASS**。
- **问题**:`enqueue.py` 此前用 `"category_map" if pf.category else "config_default"` **猜**科目来源——票有品类但没命中映射、回落账套默认时仍谎报 `category_map`(违铁律 #3/#12 状态诚实)。
- **修**:`common.resolve_account_sourced()` 返 `(code, source)`(`category_map`=品类映射命中 / `config_default`=落账套默认);`resolve_account` 变薄封装(AR/AP/VAT 固定项不关心来源)。mapper/sales_mapper 把**变动科目**(采购/收入)真来源 + `account_review`(=落默认即待核)写进载荷;enqueue 读载荷不再猜。详情卡落默认显柔和琥珀「默认·待核」提示(`expd-acct-review` 4 语,`.exp-je-note` CSS)。**零入账行为改动**。

### defer① — 绑主体 `bind_fix` 后端派生 + 拆 `push_exception_classify.py`
- prod commit `8c79d556`。CI 6/6 绿。真站 E2E **8 PASS**(绑主体卡由后端字段驱动渲染)。prod API 实测返 `bind_fix:{can_bind:true}`。
- **前置拆分**:`services/erp/push_log_queries.py` 已 492/500 加不下 → 抽异常分类/派生纯函数到新模块 `services/erp/push_exception_classify.py`(`classify_push_exception` + `derive_account_fix` + slots + 新 `derive_bind_fix`),原文件 re-import 保 facade(`store.X is q.X` 由 `test_push_log_queries_contract` 钉死),文件回落 **436 行**。`push_store` 也 re-export `derive_bind_fix`。
- **新派生**:`derive_bind_fix(error_msg)` → `direction_unknown` 且非 `direction_not_enabled` 返 `{can_bind:True}` 否则 None。`list_push_exceptions` 对 `direction_unknown` 异常派生 `bind_fix`。前端 `erp-exceptions.ts` `isBind` 改读 `it.bind_fix.can_bind`,删掉 `!/direction_not_enabled/` 正则(单一口径)。**零行为改动**。

### S4 — 自建客户 ARMAS(销项·票上买方)疑似重复转人工守卫
- **companion 大半早建好**(探代码发现):`ensure_customer`(建 ARMAS)、`find_customer_code`、`verify_customer_row` 都在,`write_sale` 也早接了 `ensure_customer`。**唯一缺口** = 采购有的「疑似重复转人工」守卫,销项没接 → 名近税号不同的买方会**静默建重复客户**。
- **companion 修**(commit `a27cc82`):`master_create.suspected_customer_dup()`(镜像 `suspected_supplier_dup`)+ `dbf_sales.ERR_CUSTOMER_DUP="CUSTOMER_DUP_SUSPECTED"` + `write_sale` 加 `elif suspected_customer_dup → 转人工不建`(建前无写盘)。
- **云端人话化**(commit `33582a24`·CI 6/6 绿·prod E2E 4 PASS):`erp-log-card._AGENT_REASON_I18N` 加 `CUSTOMER_DUP_SUSPECTED → erp-reason-customer-dup`(4 语,镜像 supplier-dup),不裸露英文码。
- **★真机暴露并修了一个真 dedup bug**(commit `41418cc`):第一次真机测 S4b 仍**静默建了重复客户**。根因实测确认:`_norm_match` 用 `isalnum()` 过滤会**删掉泰文声调符 `็`**,两个名(`เอ็มเพ็กซ์` vs `เอ็มเพกซ์`)归一后**完全相同**(相似度 1.0),但 `_find_suspected_dup` 有 `cand == target → continue`(当"完全同名=真匹配")把这种「同名不同税号」的最该警惕情况漏过去了;`_find_code` 又按逐字名+税号匹配不上 → 既不复用也不拦 → 建重复。**修**:`if not cand or cand == target` → `if not cand`(归一同名落到相似度判定 1.0≥0.9 返回疑似重复)。**供应商侧同享此守卫**。加 `test_suspected_dup_normalized_identical_diff_tax`(旧码漏、修后拦)。
- **/simplify 微优**(commit `dd4f670`·**未单独发版·搭下次功能版**):`cand == target` 时直接返回,省 `SequenceMatcher`,行为不变。
- **发版**:version.py 1.1.9 → **1.1.10**(`644ae85`)→ **1.1.11**(`cdeafca`,含 dedup 修复),两次跑 `release.ps1` 推到 prod(latest.json=1.1.11,setup.exe 75.8MB)。`dd4f670` 已 commit 未发(零行为改动)。
- **真机重测 PASS**:S4a(`INV6812-041`)→ 自动建客户 `เอ็มเพ็กซ์` + 过账成功(`IV681222-001`);S4b(`INV6812-042`)→ **正确转人工**「疑似与已有客户重复…」+ `[CUSTOMER_DUP_SUSPECTED]`,**不建重复户**。

### 测试发票语料 — 加 S4 两张(commit `66d41ffb` + `fb245dc9` black)
- `scripts/_gen_test_invoices.py` 加 `CUS.newC/dupC` + 场景 `S4a/S4b`(group5_push)。生成器输出 **51 PDF** 到 `~/Desktop/test_invoices`(语料**不进仓**,只生成器进仓)。README 自动含 S4 大白话。
- **坑**:生成器此前是**未跟踪文件**(从没过 lint),纳入仓后补了 black + 去未用 `import field`(`fb245dc9`)。

### DATAT 清理(第一次 · 失败测试的重复残留)
- 第一次真机测 S4b 误建的重复客户 + 单已**全删干净并验证**:6 表 16 条(ARMAS/ARBAL 各 2 客户、ARTRN/ISVAT/GLJNL/GLJNLIT 共 12 行)→ accserver 读回确认残留 0、行数回基线。备份在 `桌面\DATAT_backup_20260624-134032`(重测通过后可删)。

---

## 二、全语料真机测试 — 详细排查结果(Owner 上传 51 张减 S4a/S4b = 49 张,我查 prod 数据核实)

**测试账号**:`18685123459@163.com`(user_id `0ac26816-d529-40b2-a5f2-eee9d5d3331f`)· workspace `บริษัท มานะชัยบริการ จำกัด`(税号 `0735527000289`)。
**结果总览**:今天 push_logs **46 条 = 41 success + 5 manual**;ocr_history 今天 50 条。

### ✅ 核实正确的(核心管道稳)
- **去重无双记账(最要命的,已查 DATAT 实证)**:重复票 `RR581215-004`(场景 01 与 23 同号)、`BT6812-001`(34-01 与 34-dup)在 DATAT 采购表 APTRN(源单号存 **REFNUM** 字段,非 YOUREF)**各只有 1 条** → 第 2 次推送被去重(日志显 success 但实际没重复写)。**确认无双记账。**
- **5 张正确转人工**:`IV6812-0130`(12 方向判不出 `direction_unknown`)、`IV6812-0180`(28 行金额不符 `amounts_not_consistent`)、`IV6812-0190`(31 零额 `amounts_not_consistent`)、(空单号)(29 残缺票 `amounts_not_consistent`)、`INV6812-042`(S4b `CUSTOMER_DUP_SUSPECTED`)。
- **自动建供应商**:09 `NT6812-007` → 建 APMAS `เ001`;33 `RR6812-0500` 等同理。
- **供应商归一**:R3a `TWG6812-01` / R3b `TWG6812-02`(同公司不同写法)→ 都落同一供应商 `บ023`。
- **加油票防呆**:15 `BCP6812-5521` → 推 `total=751.87`(真油费总额,**没把升数/积分当钱**)。
- 正常票(采购/销项/多行/含税反算/佛历/泰数字/折扣/大小额)全部正确入账。

### ❌ 有问题的(测试如实暴露的"防呆闸"缺口 → 已列 backlog)
这几张"陷阱票"**该标记/转人工却当普通票推成功**(查 request_body 实证):
| 票 | 场景 | 实际推送 | 应该 |
|---|---|---|---|
| `INV-US-0091` | 26 美元票 | `total=1284` **当泰铢记**(无币种检查) | 标币种不符(**最严重·金额性质错**) |
| `DEP6812-01` | 27 押金收据 | `total=21400` 当普通采购 | 特殊处理/转人工 |
| `CN6812-0005` | 30 折让/退货单 | `total=3959` 当**正向**采购 | 走冲销(负向) |
| `IV6906-0001` | 24 未来日期 | `total=5350` 照推 | 标可疑复核 |
| `IV6512-9999` | 25 倒签可疑 | 照推 | 标可疑 |
| `IV6812-0160` | 19 税号非法 | 照推(买方=自家故方向不受影响) | 标税号无效(轻) |

**性质判定**:不是"坏了"——Express 推送 preflight 目前只查 `feature/account_set/direction/direction_enabled/mapping(金额/日期/借贷)/chart(科目白名单)/confidence`,**没做币种、日期合理性、押金、折让单**这类防呆。这些在 doc28 §8「对抗设想」就列为 v1 之后项。测试核心管道(方向/金额/去重/科目/建档)全稳。

### 未单独核实(够不上结论但记一笔)
- 16 POS(`0012345`)、17 多页(`RR6812-0301`)、21 手写(`0456`)未出现在 push success 也未在 manual → 应是识别了但未推(非自动推或识别为不可推);22 菜单、34-non 非发票**未进 push_logs**(正确没推,= Owner 看到的"被拦在 Pearnly")。这几张的识别准确度没逐张核(Owner 可在「识别记录」页看)。

---

## 三、Backlog（待办 / 待定 / 不做）

### A. 待做 — Express 推送防呆闸(本次测试暴露,Owner 拍优先级)
1. **币种检查(最优先)**:非泰铢票(USD 等)→ 标币种不符 / 转人工,不当泰铢直接入账(现 `INV-US-0091` 会错记)。
2. **折让/退货单(贷项 CN)**:识别为冲销,走负向,不当正向采购(现 `CN6812-0005` 错记)。
3. **押金/定金收据**:不当普通费用直推,转人工。
4. **日期合理性**:未来日期 / 异常倒签 → 标可疑复核。
5. (轻)税号非法(非 13 位)→ 标无效。
> 这些都属 doc28 §8 deferred,做法多为「转人工」即可(不必自动入账)。建议在 `preflight_express` 加对应体检项。

### B. 待定 — 存档,看要不要启动
- **S7 自建套账(建账套)**:事务所新客户建**整套新账**(目录 + ISINFO + GLACC 科目种子 + SCCOMP + ISRUN + 会计期)。**全系统风险最高的写**。规矩(doc29 §3.6):**先做逆向勘探 spike**——真 Express 上手动建一个账套抓出动了哪些表/字段/种子/成功判据,**证明能 100% 正确复刻才建**;不行就改走 Express 界面引导。需 Owner 真机配合抓数据。**本窗口未起,Owner 拍板暂缓存档。**

### C. 不做 / 低优先(明确不动或待触发)
- **defer② acctfix→通用 panel 句柄改名**:绑主体卡复用了 `data-erpexc-acctfix`/`data-acctfix-*`/`erp-exc-acctfix` 这套(机制通用·行为正确),名字带 acctfix 语义靠注释防误解。**第三个消费者出现再做**(现 2 个:科目卡 + 绑主体卡)。/simplify 4 个 agent 也确认这是有意 deferral,别re-flag。
- **prod `pearnly_e2e_3` 残留**:早期 bind e2e 留的 1 个 express 端点 + direction_unknown 日志(**无害**,是复验绑主体卡的 fixture)。可清可留。

### D. v2(doc28/29 已记 · 现在不做)
- 科目**全自动新建**(现保守版:落已有/人确认)· 预扣税 WHT · 存货 vs 非存货 · 已过账改错的冲销-重过账 · 全托管档位细调。

### E. DATAT 清理(本轮全语料测试数据 · 待 Owner 定)
- 本轮 41 张 success 在 DATAT 留了一批测试数据(采购→APTRN/APMAS 等,销项→ARTRN/ARMAS 等)+ S4a 重测残留(`เ002 เอ็มเพ็กซ์` + `IV681222-001`)。
- **清理两条路**(见下「资源」proven 流程):① 按全部测试单号 REFNUM 逐表删(用本窗口验证过的拷出→本地手术→拷回流程,扩大单号集);② 从干净基线备份 robocopy `/MIR` 还原(需 Owner 确认哪个是"干净基线",避免误删)。**Owner 未拍,本窗口未清(等下次或 Owner 决定)。**

---

## 四、关键事实 / 坑 / 资源(给接手人)

### 版本与 commit
- **pearnly-app(我的)**:`62626323` S5 / `29e22bb8` S5-test / `8c79d556` defer① / `33582a24` S4-humanize / `66d41ffb` 语料S4 / `fb245dc9` 语料black。其后 master 是别窗口 LINE 工作(`d8c7cd8f` 等)。
- **companion(`D:\pearnly-companion`·无 remote)**:`a27cc82` S4守卫 / `644ae85` v1.1.10 / `41418cc` dedup修 / `cdeafca` v1.1.11 / `dd4f670` simplify微优(**未发版**)。prod latest.json = **1.1.11**。

### DATAT 写盘清理 · 本窗口验证过的安全流程(accserver 易掉线 + 我的进程无 P: 映射认证)
1. **关键发现**:原生 Windows 进程(Python/PowerShell)**访问不了** `\\accserver`(无 SMB 认证会话,P: 是 Owner 交互登录的映射);但 **bash(MSYS)能读能写** `//accserver/ACCOUNT/70EXP/test`。所以 DBF 操作走:**bash 拷出 → 本地 Python+dbf 手术 → bash 拷回**。
2. 账套目录:`\\accserver\ACCOUNT\70EXP\test`(= Express 里的 `P:\70EXP\TEST` = DATAT)。
3. 销项写 6 表:`ISRUN, ARTRN, ISVAT, GLJNL, GLJNLIT, ARBAL`;采购写 `ISRUN, APTRN, ISVAT, GLJNL, GLJNLIT, APBAL`;主档 `ARMAS/APMAS`。每表只有 `.DBF + .CDX`(无 .FPT memo)。
4. **链接字段**:ARTRN/ISVAT 按 `DOCNUM`;GLJNL/GLJNLIT 按 `VOUCHER`;ARMAS/ARBAL 按 `CUSCOD`;**源发票号在 APTRN/ARTRN 的 `REFNUM` 字段**(不是 YOUREF,YOUREF 多为空)。
5. 流程:① bash 整套备份到 `桌面\DATAT_backup_<ts>`(兜底)② bash 拷受影响表到本地 work 目录 ③ 本地 `dbf.Table(...,codepage=cp874)` 删行 + `pack()` + `reindex()` ④ 本地读回核对行数 ⑤ **Owner 关 Express + 退小助手**(否则文件锁→拷回失败/损坏)⑥ bash 逐表拷回 + 核对大小 ⑦ accserver 读回验证残留 0。
6. **坑**:`pack()+reindex()` 大表(GLJNLIT 2 万行)可能超 2 分钟前台超时 → 后台跑或分步;dbf 库 `__version__` 不存在(import 成功别被 AttributeError 骗)。

### prod 监控(查任意账号推送结果)
- SSH `root@66.42.49.213` → `cd /opt/mrpilot && set -a && . /opt/mrpilot/.env && set +a && PYTHONPATH=/opt/mrpilot venv/bin/python` → `psycopg2` 连 `DATABASE_URL`,查 `erp_push_logs`(invoice_no/status/error_msg/request_body)+ `ocr_history`(direction/workspace_client_id)。注意 `invoice_no` 可能 NULL(format 前判)。
- 状态语义:success=推成功(含去重 skip)· manual=转人工(`EXPRESS_MANUAL:<reason>` / `[CODE]`)· failed=失败 · pending=排队待 Agent。

### 工具/路径
- companion 构建:py64 `C:\Users\skin3\AppData\Local\Programs\Python\Python311`、py32 `D:\py311-x86`、ISCC `...\Inno Setup 6\ISCC.exe`,PyInstaller 6.21。`packaging\release.ps1` 一键(读 version.py → 64位companion.exe + 32位pack_runner.exe + Inno + scp prod + latest.json)。
- companion 测试:`PYTHONUTF8=1 python -m pytest tests/`(系统 py64 有 dbf+pytest;全量 266 passed + 4 pre-existing OCR 环境性失败 `test_e2e_headless`/`test_field_engine`,非功能缺口)。
- gh CLI(本机):`C:\Users\skin3\AppData\Local\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe`。

### 共享树纪律(踩过)
- pearnly-app 是多窗口共享树。本窗口 push 期间别窗口的 `erp-express-wizard.ts`(509 行超 size 闸)一度让 master CI 红,他们自己压回 ≤500 修复。build 前若有别窗口未提交的 `src/home/*.ts`,会被烤进 `dist/main.js`(虽 main.js 被一致性闸排除,但会推上线别人半成品)→ 我用 `git stash push -- <他们的文件>` → rebuild 干净 → 提交我的 → `git stash pop` 还原。只 `git add` 自己的文件。

---

## 五、当前各闸/状态快照
- pearnly-app:我的 6 个 commit CI 全 6/6 绿(unit/lint-ui/lint-debt/lint/lint-routes/lint-size)。`push_log_queries.py` 436 行(<500)、`push_exception_classify.py` 93 行、`erp-exceptions.ts` 496 / `erp-exc-actions.ts` 307。i18n 4 语平衡(+`expd-acct-review`+`erp-reason-customer-dup`)。
- companion:全量 266 passed(4 OCR 环境性 pre-existing)· ruff 绿 · prod 1.1.11 · `dd4f670` 待随下次功能版发。
- DATAT:第一次失败测试残留已清;本轮全语料测试数据 + S4a 重测残留(`เ002`+`IV681222-001`)**未清**(待 Owner 定,见 backlog E)。
- 备份:`桌面\DATAT_backup_20260624-134032`(第一次清理前的 6 表原始,重测已通过,可删)。
</content>
