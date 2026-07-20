# 交接 · 静默改数清单与月结产线待办(2026-07-20 夜)

换窗先读本页 + `HANDOFF-2026-07-20-AGENT-BOUNDARY-AND-FRAMEWORK.md`(边界与框架)。
本页只讲**没做完的**:每条给「为什么修 / 修哪里 / 怎么复现 / 建议怎么修 / 怎么根治」。

盘点方法:生产库全量事件流取证(SM 工单 `bd093ba9`,1527 事件 / 105 件)+ 代码审计约 47k 行
(`services/workorder`、`ocr`、`summary_import`、`purchase`、`recon`、`routes/workorder*`、
`static/ai`)+ 完整性检查专项 + 四路 /simplify 审查。
**未覆盖**:OCR 逐字准确率(要拿原件比对)、前端渲染与后端数据一致性(要真浏览器抓)、
跨期历史(SM 只跑过一期)。

---

## 0. 今天已上线(不用再看,只列结论)

| commit | 内容 | 性质 |
|---|---|---|
| `2fb5fae0` | 机器自动改动进签字页(SA-1 点灯) | 新增可见性 |
| `96f4160e` | 改判清不掉旧 `flag_reason` | 真 bug,生产有脏数据 |
| `b49d9af9` | 进销底稿逐行对齐 R1 合计 | 真 bug,交付物自相矛盾 |
| `d285672f` | 方向裁决通道认「人已裁过」 | 理论缺陷,生产零命中 |
| `27b7e6a5` | `history_routes` 512→415 拆分 | 解 CI 硬闸 |
| `38ce30cf` | 重出两处 stale dist | 不修则改动上线不生效 |
| `9abfe1fc` | /simplify 收口 · 方向判据归一 | 质量 |

**三条修复都做过回滚验证**(把修复改回去看测试是否转红)。其中一条第一次跑仍是绿的——
说明原测试压根没断言过该行为,补了预设脏值才真正守住。**这一步不做,守门是空的。**

---

## 1. A 类 · 会静默改申报数字,且用户完全看不见

> 共同病根:**算术自洽就当读对了,而那个"自洽"是系统自己造出来的。**
> 这一类比 IN-R 更靠近钱,建议优先。

### A-1 OCR 在票上"补"一行不存在的折扣 ★最高

- **为什么修**:勾稽差额被当成"漏抓的折扣"回填进发票对象,回填后
  `triggers._check_amount_math`(口径 `sub - disc + vat`)自动通过 → 该票**不再触发 L3、
  不再报 amount math fail**。差额本来可能是选错列或漏读一位,被包装成折扣后静默入账。
- **修哪里**:`services/ocr/sanity.py:213-236`(`invoice.discount = f"{d:.2f}"`);
  调用点 `services/ocr/page_runner.py:195-202`(L2 后)、`:407-409`(L3 后)、
  `services/ocr/direct_read.py:312-314`(直读路)。
- **怎么复现**:造一张 `subtotal + vat ≠ total_amount` 且差额恰等于某个"像折扣"的值的票,
  跑 `page_runner`;观察 `invoice.discount` 被写入、`_check_amount_math` 由红转绿。
  真件参照 SM 工单 `IMG_2647`(折扣淡票,人工 recalc 过)。
- **建议怎么修**:回填保留,但**强制** `needs_manual_review=True` 并把
  `discount_inferred` 提升成 `validation_warnings` 一等项(现在直读路只降 0.05 置信、
  Vision 路进 warnings 但文案泛化,**不说"我改了折扣"**)。
- **怎么根治**:分开「报告差额」与「消除差额」两件事。闸的职责是报告,不是把票改到闸能过。
  凡是为了让闸通过而回写票面字段的动作,一律要求人确认 —— 这是本类问题的统一原则。

### A-2 L3 失败后第二个模型重读金额,成功就整体顶掉、不留痕 ★最高

- **为什么修**:救援成功分支**唯独不设** `needs_manual_review`、**不往
  `validation_warnings` 追加任何内容**。四个金额字段被另一次模型调用整体替换,验收条件
  只有两条算术自洽。而 `layer_chain` 不进 `item_classified` 事件
  (`classify.py:473` 只取 pipeline 名)→ 工单侧 `status="ok"` → 直接进 R1 合计。
  **一张原本被闸抓住的错读票,被第二次读数洗白成绿票。**
- **修哪里**:`services/ocr/totals_rescue.py:83-96` + `services/ocr/page_runner.py:313-323`
  (对比 `:331`/`:339` 的失败分支都设了 `needs_manual_review = True`)。
- **怎么复现**:让 L3 主路返回不自洽三数触发 rescue,rescue 返回自洽值;
  观察 `needs_manual_review` 仍为 False、`validation_warnings` 为空、工单侧判 ok。
- **建议怎么修**:救援成功也设 `needs_manual_review=True`,并把 `layer_chain` 落进
  `item_classified` payload(现在整条模型降档/回落链对用户全程不可见)。
- **怎么根治**:**换过眼睛的读数必须留痕并留人**。凡"第二次读"替换"第一次读"的路径,
  差异必须进证据链;SA-1 的 `machine_actions` 投影就是为这类动作准备的落点(见 §5)。

### A-3 超 2000 行的汇总表静默截断,连报警一起截掉 ★高

- **为什么修**:`_MAX_ROWS = 2000` 截断后置 `truncated=True`,但
  `reconcile_gates.aggregate_sales` **全文不读这个字段**。更糟:**表底合计行也被截掉** →
  `_total_row_check` 的 `summaries` 为空 → `total_check = "absent"`,在 gates 里等同于
  "这表本来就没有合计行"。**唯一那道交叉校验闸被自己静默关掉。**
- **修哪里**:`services/summary_import/parse.py:20,118-123` 与 `pdf_table.py:88-90`
  产出 `truncated`;消费缺口在 `services/workorder/steps/reconcile_gates.py:257-310`。
  工单侧的路径确认走这里:`steps/summary_read.py:13` → `summary_import.parse.parse_table`。
- **怎么复现**:造一份 2001 行 + 表底合计行的销项汇总表(xlsx),走工单收料 → classify;
  观察 R2 销售额按前 2000 行算、`total_check` 为 `absent`、无任何提示。
- **建议怎么修**:`aggregate_sales` 读到 `truncated=True` 直接 `StepResult.stuck` 点名
  (与 `TOTAL_CHECK_MISMATCH` 同级),别让"截断"和"这表没合计行"共用一个表现。
- **怎么根治**:**降级信号必须有消费方**。仓库里同类还有 `degraded`(pdf_grid)、
  `layer_chain`、`escalations` —— 建议立一条机械闸:凡产出降级标记的函数,
  CI 检查是否存在读取方(参照 `check_new_debt` 的写法)。

### A-4 银行金额被按余额反推改写,并把报警从红翻成绿 ★高

- **为什么修**:与前后余额差 ≤30%(`_REPAIR_RATIO`)就把 OCR 读的金额改成反推值,
  同时把 `balance_ok` 由 False 翻 True(该行**退出所有待核对清单**)。改后的金额是
  `bank_sales_suggest` 销项倒推(÷1.07)的基数。同族:`:94-101` 方向按余额涨跌自动翻转,
  **方向决定这笔算不算销售收入**(`classify_row:295-296`)。
- **修哪里**:`services/recon/bank_stmt_balance.py:163,205-211`(金额)、`:94-101`(方向);
  GL 版同病在 `services/ocr/gl_balance_chain.py:73-77`、`:104-113`(后者连 warning 都没有)。
- **怎么复现**:造一段余额链,让某行印刷金额与"前后余额差"相差 20%;
  观察 `amount_autocorrected=True`、`balance_ok` 由 False 变 True。
- **建议怎么修**:**已部分完成** —— SA-1(`2fb5fae0`)已把 `amount_autocorrected` /
  `direction_autocorrected` 投影到交付包页。剩下的是:超过某阈值(建议 5%)的改写不该
  自动翻绿 `balance_ok`,应保留待核对并点名。
- **怎么根治**:把"改写"与"消警"解耦 —— 改写可以自动,消警必须人确认。同 A-1 原则。

### A-5 解析不出的金额一律静默当 0 进合计 ★中

- **为什么修**:`to_dec` 的 docstring 写"由上层判 unresolved",但上层
  `resolve_input_vat:113-118` 判的是 `if not money`(**整个 dict 缺**)。单字段是
  `"N/A"`、`"-"` 这种,**按 0 计入,不触发 unresolved**。
- **修哪里**:`services/workorder/steps/reconcile_gates.py:35-43`;同族无日志兜底 6 处:
  `services/purchase/totals.py:24-26`、`ocr_corrections.py:25-27`、
  `summary_import/mapping.py:96-100`、`judge.py:36-40`、`services/ocr/money.py:26-29`。
- **怎么复现**:构造 `money = {"subtotal": "100", "vat": "N/A", "total_amount": "107"}`
  喂 `resolve_input_vat`,观察 vat 计 0 且不进 unresolved。
- **建议怎么修**:`to_dec` 增一个"严格模式"重载给钱路径用,解析失败返回 None,
  由 `_effective` 判 unresolved。**不要改 `to_dec` 现有签名的默认行为**(6 处调用方,
  其中部分是非钱路径)。
- **怎么根治**:钱字段的解析失败与"值为 0"必须在类型上可区分。长远看 `money` 应该是
  带解析状态的值对象,而不是裸 dict。

### A-6 试算平衡闸被自己的兜底架空 ★中

- **为什么修**:`_effective` 在 `total_amount` 缺失时用 `净+税` 派生,而 R4 试算平衡的
  credit 侧用的就是这个派生值 → `trial_balance` **恒等自平,`offenders` 恒空**。
  含税额缺失的票永远不会让 R4 报不平。
- **修哪里**:`services/workorder/steps/reconcile_gates.py:46-53` 与 `:339-368`。
- **怎么复现**:造一张 `total_amount` 缺失、`subtotal + vat` 与真实含税额不符的票,
  跑 R4,观察 `balanced=True`。
- **建议怎么修**:派生标记 `grand_derived=True`,R4 对派生件跳过借贷校验但**点名列出**
  (现在是静默当作已校验)。
- **怎么根治**:**派生值不得参与校验自己的那道闸**。这是一条可以机械检查的通则。

---

## 2. B 类 · 决定料件去向,用户近乎看不见

| # | 问题 | 修哪里 | 怎么复现 | 建议修法 |
|---|---|---|---|---|
| B-1 | 认不出的表格文件**默认归销项汇总表**,数字进 R2,`flag_reason=None` 不进任何清单 | `steps/sort.py:191-199` 兜底 + `:142-143` 无日志 fail-open | 上传一个损坏的 xlsx,观察归堆为 `sales_summary/pending` | 兜底改归 `unknown` + 方向 flag,让人裁 |
| B-2 | VAT 字段读花 = 视作没有 VAT → 进 `non_tax`/`bank_statement` | `steps/sort.py:456-460`(`except InvalidOperation: return False`,无日志) | 让 `fields["vat"]` 为 `"7O.00"`(字母 O),观察判 non_tax | 解析失败与真的无 VAT 分开:前者 flag 待人工 |
| B-3 | `non_tax` 直接 `status=excluded`,**不占 flagged、不进人审队列** | `steps/classify.py:344-347`;守恒闸 `conservation.py:142-143` 放行 | SM 工单实测 14 件全自动排除、零人复核、payload 无 confidence | 至少对低置信度的 non_tax 判定保留一次人工过目 |
| B-4 | latin-1 兜底仍在:改名的 `.csv` / 损坏的 `.xlsx` 会被解成逐行垃圾 | `summary_import/parse.py:64-69`;`recon/bank_table_io.py:103`;`ocr/table_path.py:295-300` | 把 PDF 改名成 `.csv` 上传,观察解出 N 行 `status=ok` | 现修复只覆盖 `.pdf` 后缀分流,应改为**内容嗅探**而非后缀 |
| B-5 | 去重键会把不同的票判成重复(票号读不出是常态) | `services/purchase/totals.py:145-156`(`sha256(税号\|票号\|含税合计)`);命中后 `classify.py:329-334` 设 `flagged=False` 不进人审 | 造两张同供应商、同金额、票号均读不出的票 | 票号为空时**不参与去重**(现在是空串照拼指纹) |
| B-6 | **跨期票完全没有概念**:上上个月的进项票混进来,系统看不见 | `steps/compute.py:39-41` 一次减法不看日期;`resolve_input_vat:81-134` 零日期判据 | 给一张 `invoice_date` 在账期外的进项票,观察照常计入 | 先做「识别 + 点名」,再谈剔除;6 个月规则在 `services/tax/aggregate.py:29-30` 但那条线**从未被工单调用** |

---

## 3. C 类 · 真 bug(已修的不列)

| # | 问题 | 修哪里 | 建议修法 |
|---|---|---|---|
| C-1 | **签核之后还能落裁决**:SM 实测 `review_signoff` 在 11:10:58,58 条 `assign_kind` 在 11:11:23(**之后 25 秒**) | 裁决端点 `routes/workorder_routes.py:251-276` 不检查签批态 | 签批后裁决应触发 `signoff` 转 stale(投影已支持),或直接拒绝 |
| C-2 | **批量「全部按建议处理」的置信度是查表查出来的**,与这张票的读数质量无关 | 前端 `static/ai/ai-review-verdict.js:51-64`;后端 `services/workorder/verdict.py:121-138` 的 `_MAP` 按 flag_reason 前缀返固定值 | confidence 应反映该票自身的 OCR 置信度与金额自洽性 |
| C-3 | **收件箱批量路径缺 `isDecided` 守卫**,会把已裁的票连同重发,覆盖手工改判 | `static/ai/ai-review-inbox-flagged.js:98-105`(对比 `ai-review-bulk.js:27` 有守卫) | 补守卫;分组头计数也要用后端 `undecided_count` 而非组内件数 |
| C-4 | 落 `run_finished` 事件失败被吞 → run 已结束但状态位停在 running,前端一直转圈 | `services/workorder/runner.py:335-337` | 落库失败应重试或落一条降级事件,别静默 |

---

## 4. D 类 · 该有的判断根本没写(IN-R 一族)

> 全流水线**唯一 fail-closed 的完整性闸**是守恒闸(`conservation.py` + `package.py:52-57`)。
> 它保证「收到的每一件都有明确终态」,**不保证「该收的都收到了」**。

| # | 缺什么 | 证据 |
|---|---|---|
| **D-1** | **IN-R:客户档案没有「本期应到哪些来源」** —— 系统只知道"手上有没有",不知道"该来什么" | `workspace_clients` + `client_tax_profiles` 全部列已查,零个相关字段 |
| D-2 | 出包不检查销项来源权威性 | `sales_source` 全仓只用于渲染和脚注,**无一处 if/raise** |
| D-3 | 人工填销项**不要求填出处** | `routes/workorder_schemas.py:33` 默认空串;`sales_entry.py:83-85` 只查长度 |
| D-4 | 银行倒推与手打的数**在库里不可区分** | 都落 `source="manual_entry"`;前端「采用建议值」只预填不标记 |
| D-5 | 逐票对账算了不拦人 | `sales_aggregate.py:133-142` 算出 `gap_net`/`coverage`/三态;`reconcile.py:210-211` try/except 注释写死"绝不阻断 package" |
| D-6 | **多来源销项前端没接**(后端完整) | `sales_entry.py:49-58,86,95,103-104` 支持分槽相加,全 `static/`+`src/` grep `source_label` 零命中 → 冰厂三渠道加不起来 |
| D-7 | 缺号检查与工单**零连接** | `services/vat/vat_report_checks.py:179-228` 做得很全,唯一调用方是独立上传端点 `routes/vat_report_checks_routes.py:20-44` |
| D-8 | **「缺票备忘」里没有一张缺的票** | `package.py:431,473-479`,N = `flagged_count` = 收到但有毛病的票 |
| D-9 | 上期留抵**硬置 0** | `pp30_form.py:58`;`vat_credit_carry` 字段存了,全仓消费方只有 store/route/前端渲染 |
| D-10 | 偏离告警只比一个数、无阈值 | `compute.py:94-121` 只比 `tax_due`,只记 delta |
| D-11 | 证据索引 `tax_due` 无原件 | `evidence.py:325-331` `items` 恒空 |

**IN-R 的根治形态**(2026-07-20 与 Zihao 对齐):
登记表存的必须是**来源清单**(名称 + 类型),**永远不存"本期应等于多少"**。
一旦存了期望值,所有闸都会不自觉地朝它对齐 —— 那才是真把产品做成对账工具。
存来源清单只回答一个问题:**该来的来齐了没有。**

---

## 5. /simplify 提出但本次未做的补深(高度角排序)

| # | 内容 | 为什么值得做 | 代价 |
|---|---|---|---|
| S-1 | `store.update_item` 改**哨兵值**(`_UNSET`),四列同时获得置空能力 | 现在 `clear_flag_reason` 只给一列开逃生口,是在有缺陷的通用机制上叠列专用特例;`taxid_realign._reset_items` 与 `reset_quota_deferred_items` 仍在直写 SQL 绕开,下次要清 `kind` 只能再加一个布尔 | **全仓仅 6 个调用点**(classify ×4 / sort ×1 / statement_regroup ×1),现在是最便宜的时刻 |
| S-2 | 钱路径统一走 `decisions.kind_of`,拆掉 `counted_items` 数据通道 | `counted_items` 只覆盖了进项方向的一个消费方,**销项侧三处留着同样的病**:`reconcile.py:200`、`sales_aggregate.py:179`、`reconcile.py:56` —— 被裁成 `sales_doc` 的 unknown 件不进逐票销项佐证,覆盖率数字会偏低 | 改 4 处各一行;`decision_recs` 各处已在手。**要碰钱路径,需配完整测试** |
| S-3 | `machine_actions` 渲染改 `type → 渲染器`表(带 default) | 现在 `ai-mact-render.js:26-59` 是 `if/else`,**第三类动作会被渲染成一条空白银行行**;接 A-2/A-3 的痕迹时当天就会出事 | ~20 行,现在只有 2 个 producer,是最便宜的时刻 |
| S-4 | `app.py` 路由注册表**数据化** | 现在 70 余行扁平 `include_router` 占满行数预算,导致本次 `history_assign_routes` 只能用 `include_router` 回挂 —— **注册中心不再权威**,从 app.py 读不全路由表。这是过闸产物,不该扩散到第三个模块 | 一次性搬 70 行,app.py 立刻 499→~430,此后新路由零行成本。风险=路由匹配顺序,保序即可 |
| S-5 | 测试替身 `update_item` 收进 `tests/unit/_workorder_fakes.py` | DAL 语义有 **9 份手抄副本**,本次只跟上了 1 份 —— 这次的 bug 正是被这种替身遮住的,修完遮罩仍在 8 处 | 中等 |
| S-6 | i18n `mact_kind_*` 收成共享 kind→key 映射 | 同一批后端 kind 的四语文案现在有 4 套并行副本,且已产生分叉(`intake_excluded_sales` 叫"销售件"、新词条叫"销项汇总表")。范式见 `ai-desk-render.js:166 GROUP_LABEL_KEYS` | 小 |
| S-7 | e2e stub 引导复用 `_uidebt0714_verify.spec.js` 的参数化 `routeApi`/`bootWith` | 交付包页桩契约现有三份副本 | 小 |

**两条明确不采纳**(附理由,别再提):
- `store.update_item` 去掉 `flag_reason is None` 守卫 → 会生成
  `SET flag_reason=%s, flag_reason=NULL` 的非法 SQL,守卫不是冗余。
- `machine_actions.projection` 加懒加载 → 实测 0.40ms/次,而同请求 `list_events` 已无条件
  拉 261KB payload(含这批行)、反序列化就 1.6ms;加懒加载还会重新制造 review 态看不见的
  问题。效率角结论:占单核 0.008%,**不优化**。

---

## 6. 生产状态与卡在人这边的事

- **SM 工单 `bd093ba9`(客户 106 / 2569-05)= `review`,不该签。**
  销项 ฿60,073.60 的证据链是空的(`无原件(人工申报)`),数字来自银行流水倒推 +
  **597 行个人转账一次性全部认定为销售收入**(同一微秒、零 non_sales、零 pending)。
  佐证闸自曝 `coverage=12.5% / gap_net=750,764.48 / covered_state=amber`,只标黄没拦。
  **缺的是 POS Z 报表 / 月度销售汇总** —— 拿到它销项才第一次有真凭证,那才是这条产线的首跑。
- **机器与人的分工是互斥不是复核**:LLM 判 `sales` 的 125 行**一条都没进人工裁决集**
  (指纹交集为 0),人兜的是机器 `cannot_judge` 的 355 行 + 机器没看过的 242 行。
- **冰厂(Sincere Ice)2569-06** 仍缺:纸质进项、银行流水、金标;待问客户:7-11 与 Big C
  有没有另开发票(防重复计算)、`IV69/06-011` 改单状态。

---

## 7. 多窗口协作(今天踩了 5 次)

共享工作树 = 共享 `.git/index`,任何 `git add` 都是全局写。今天的事故:index 卷走对方文件、
`reset --mixed` 改写了已提交 commit 的 hash、残留锁、两处 stale dist、别窗文件未过 black。

**根治**:一窗口一 worktree(`git worktree add ../pearnly-xxx -b w/xxx`)。范式在本仓已验证
(GC-D 那批派子代理就是隔离 worktree + wip 分支 + 主窗 ff-merge)。
**dist 约定**:各分支只提交源码,由 push 的人在 master 上 build 一次、提交、再 push。

**立即可用的绕法**(今天验证):
```bash
export GIT_INDEX_FILE=/tmp/my_index
git read-tree HEAD
git add <我的文件>
git commit -F msg.txt
```
完全不碰 `.git/index`,不用等锁、不用删锁、不可能卷走别人的文件。

**两条今天新踩的**:
- `git commit -- <paths>` 对 **untracked 新文件不生效**(报 `no changes added to commit`)。
  正确是 `git add <我的路径>` → 立刻 `git commit -- <我的路径>`。
- push 前必须 `npx eslint .` + `npm run format:check` **全仓**,只 lint 自己改的目录会把
  CI 弄红(本窗口犯过一次:e2e spec 用了 `document` 但 global 只声明了 `window`)。

---

## 8. 建议的下一批顺序

1. **A-1 + A-2**(折扣回填 / totals_rescue 洗白)—— 同一类病,一起修,改 OCR 主路径**先报方案**
2. **A-3**(截断)—— 独立、低风险、有明确闸
3. **S-3**(渲染 default 分支)—— 接 A-2/A-3 痕迹前必须先做,否则当天出事
4. **IN-R**(D-1 ~ D-3 + D-6)—— 闸开始真报警之后,"该来没来"才有意义
5. **S-1 哨兵 / S-2 kind_of 收口 / S-4 注册表** —— 择期,各自独立

**管家 Agent 不提前**(2026-07-20 定案):这批问题没有一条是它能解决的
(全在"代码算账"那半边),而且闸被 A-1/A-2/A-6 架空的情况下,Agent 连报警扳机都收不到。
先修闸,Agent 才有活干。
