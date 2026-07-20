# GC-D 收官 + Agent 边界调研 + 月结 Agent 目标框架 · 交接

> 日期:2026-07-20。上一份交接:`HANDOFF-2026-07-19-NIGHT-SM-CLOSEOUT.md`(GC-E 清单/方向队列仍有效)。
> 本文三件事:①今天上线了什么 ②Agent 边界调研的可用结论 ③月结 Agent 未来的整体框架流程(Zihao 点名)。

---

## 1. 今天上线(master `01ba1c51..e77f6649` · CI 全绿 · prod 已部署)

| 批 | 内容 | 关键认知 |
|---|---|---|
| P0-1 | 签批投影 `sod.signoff_projection`(actor/at/stale)接 order_detail + review_feed,前端从投影点亮 | 真根因≠「复核触发重跑」——复核端点零副作用;是「已复核」只存前端内存,一刷新就丢 |
| P0-0 | 合并回放下沉 `decisions.replay_records` + `terminal_of` 终态仲裁单源,8 消费方全迁移 | 交接单点名 5 处,侦察穷尽出 **8 处**(漏网最重=人审队列投影 `flagged_projection`) |
| D2 | 银行断链页换眼重读(逐页直读、4 路并发、严格变好才采纳、`OCR_BANK_CHAIN_REREAD=0` 急停) | 吞折行真凶=**Vision 管线行切割**,不是 economy 模型;prod 对质:银行主解析根本不进 engine_context,一直跑 3.5-flash |
| D3 | `OcrRequest.policy_task` 落 contracts,拆「策略档」与「handler 路由」两概念 | 银行窄读 `overrides_by_task.bank_statement` 此前白设 |
| D4/D5 | 缺料键人话化、逐笔对账空态文案诚实化 | — |
| D6 | brain quota 退避不计熔断 + 复用 run_leases 跨进程互斥 + 失败落事件 + recovery tick 自动收尾(封顶 3 次)+ partial index | prod EXPLAIN 双路 Index Only Scan 验过 |
| /simplify | 四路审查修 ~15 项(死代码、热路径重复回放、三份拷贝归一、pkg 派生态收敛) | — |
| GC-E-1 | 报表钱数列表头随数据右对齐(7 张表全改) | Zihao 报表页实测红框 |

**验证**:全量单测 9558 绿;真浏览器 e2e 五剧本(_jb/_m13key/_mc1b2/_gcd45/_gce1)33 例 + 截图;签批投影拿 prod 1537 条真事件回放验中。

**生产待办**:工单 `bd093ba9`(SM 2569-05)仍 `review`——UI 现在会亮出 7/19 的复核记录 + 「请再次复核」,Zihao 重签 → 点「签批冻结」即归档。

---

## 2. Agent 边界调研(2026-07-20 · 五路并行 + 争议 claim 回验)

### 2.1 一句话结论

> **Agent 负责认字,代码负责算账,会计负责签规则——三件事一件都不能互换。**

产品负责人原话「靠代码死规则永远跟不上现实噪音」。**在「读」这层完全正确,在「算」和「核」这层方向反了。**根因是把两类东西都叫「噪音」:

- **A 类·表征噪音**(同一件事有无穷多种长相):7-11 汇总表 / Big C 扫描件 / 自开发票版式全不同。**无界长尾,该上 LLM。**
- **B 类·业务规则**(有限、可枚举、可配置):「进项 6 个月内可抵」是税法一条成文规则;「这家客户 3 个销项渠道」是一条客户档案属性;「发票被改过/作废没」是一个状态机。**把 B 类当噪音交给 Agent 每月现场判断,是全场最一致的反面模式。**

### 2.2 支持「上模型」的硬证据(A 类)

| 来源 | 数字 |
|---|---|
| BLOCKIE(ACL 2025,同行评审) | 跨版面泛化读总金额:**LLM 97.06% F1 vs 专用版面模型 33.43%**;极端版面多样性 94.47% vs 78.79% |
| LLM-TKIE(Nature Sci Rep 2025) | 零/少样本不微调:CORD 80.9 / SROIE 83.9 F1;域外海关单据比 SOTA 多模态高 5–8 个点 |

**结论:per-vendor 正则模板(invoice2data 那套 YAML)是上一个时代的东西,这层该上强模型。**

### 2.3 反对「让 Agent 算/核」的硬证据(B 类)

| 来源 | 数字 | 含义 |
|---|---|---|
| Thinking Machines《Defeating Nondeterminism in LLM Inference》(2025-09) | temperature 0 + 设置全同,同 prompt 跑 1000 次 → **80 种结构性不同输出**;根因是 **batch 非不变性**(结果取决于同时和你拼 batch 的别人发了什么) | **只要 LLM 在计算路径上,「同输入同输出」逻辑上不可能。**没法向国税局解释「同一张票上月 7,000 这月 7,013」 |
| FinSheet-Bench(arXiv 2603.07316,2026-03) | 表格**查值 89.1–93.6%**;**复杂聚合(求和/排序/计数)19.6–33.3%**;最大表全模型均值 48.6% | 让模型把三渠道销项加起来 = 架在最脆的点上 |
| ExtractBench(arXiv 2602.12247) | 全模型字段级通过率 **4.6%**;**369 字段的 SEC schema:所有前沿模型 0.0%**(连合法 JSON 都产不出) | **schema 宽度是主导变量**——ภ.พ.30 那种几十字段别指望一次调用端到端产出,拆窄 schema 多次抽取 |
| 财富管理 agent 基准(arXiv 2512.02230) | 高自主度检查点 49.0%;**降自主度+加人审 → 69.4% 且成本低 10%**。命名错误模式:**税率分档算错/重复计数**、**拿不到源数据时编数而不报错** | 打折说明:只测了 GPT-4o(老模型),但错误**性质**是架构性的 |
| TheAgentCompany(CMU,NeurIPS 2025) | 175 个真实办公任务,最强模型完整完成 **30.3%**;论文原话:**"DS, Admin, and Finance tasks are the lowest, with many LLMs completing none"** | 财务任务描述几乎逐字对应 Pearnly:做表、跨人收信息、看员工扫描的图 |

**关键不对称(本次调研最重要的一句)**:
> 正面证据**全部**集中在「抽取/分类」;反面证据**全部**集中在「判断/综合/算术」。
> 「做个 AI 管家处理杂事」这句话,悄悄把这两类合并了。

### 2.4 业界怎么分层(敢公开写架构的都画在同一条线上)

- **Thomson Reuters**:*"Where determinism is required, like tax calculation itself, rule-based engines handle the math... keeps probabilistic reasoning out of the final calculation of tax liability."*
- **Avalara**:agentic 层明确放在 *"at the 'edges' of the workflow"*;确定性内核独占 filing / form generation / submission / immutable logs;ML **只**用于商品分类,不碰税率与税额。
- **Intuit** GenOS:*"strictly separates LLM-generated explanations from actual tax calculations."*
- **Ramp**(工程博客):*"We layer deterministic rules on top: dollar limits, vendor blocklists, category restrictions."*
- **Veryfi**:*"LLMs are non-deterministic and not good for financial numbers."*
- **puzzle.io**(2026 agentic close):*"anything touching revenue recognition still needs a trained accountant to review."*

**没有任何一家公开声称让 LLM 算最终税额。**不敢写架构的那批(Vic.ai / Rossum / AppZen / Bill.com / Basware…),不是更激进,而是**没人愿意把这个承诺写下来**——我们逐字查过 Rossum Aurora 的 "0 hallucinated values",无方法论、无置信区间、无独立审计,且全文没说总额是算的还是抄的;坊间传的 "discriminative decoder 结构上无法生成" 这个技术说法**官方博客里根本不存在**,只有「给高亮笔不给钢笔」的比喻。

### 2.5 厂商数字不可信(做商业判断时按独立数字下注)

| 来源 | 声称 STP | 性质 |
|---|---|---|
| Coupa Benchmark | **99.97%** | 自报 |
| Vic.ai / Hypatos | 90%+ / 85–92% | 自报 |
| Rossum | 43% / 58.8% / 71% / 85%(同官网准确率写成 91%/93%/98%) | 自报,自相矛盾 |
| **Ardent Partners(独立)** | **均值 ≈25%,best-in-class 35–49%** | 独立 |

法务账:**SEC AI-washing 首案**(Delphia $225k + Global Predictions $175k)——夸大 AI 能力本身可独立起诉;**Moffatt v. Air Canada**——不能把 Agent 输出甩锅给 Agent。**对外只承诺自己金标跑出来的数字。**

### 2.6 三个值得抄的范式

**① Google ADK 三区架构 · 人审规则不审单据**
(https://github.com/google/adk-samples/tree/main/python/agents/invoice-processing)
Zone 1 = 显式版本化规则库(README 称 *"constitution — the single source of truth"*);Zone 2 = 校验层拆两半(**确定性**做 "totals match, GST is 10%" 算术校验 + **LLM** 做规则发现);Zone 3 = 学习回路,硬性规定 ***"every correction rule requires SME review and approval"***。
**价值:人审次数随规则数增长,不随单据数增长。**

**② Compiled AI · LLM 编译一次,之后确定性重放**(arXiv 2604.05150,2026-04)
*"LLMs generate executable code artifacts during a compilation phase, after which workflows execute deterministically without further model invocation."*
实测:DocILE(5,680 张发票)**KILE 80.0 与实时调 LLM 持平,LIR 80.4 全场最高**;约 17 笔即成本打平,1000 笔 **token 降 57 倍**;生成代码先过 prompt-injection(96.7%)+ 静态安全(87.5%)闸再无人值守跑。
商业验证:Flatfile Blueprint(18 亿行训练,>90% 映射动作预测命中)。
**价值:「同输入同输出」只有把 LLM 挪出运行时才可能真正满足。**

**③ 预期输入登记表 + 机械完整性闸**
按客户配置「本月应到 N 个来源」→ 每月自动核对 → 缺一个卡住不出包。校验手段抄审计学四条成熟做法:**序号连续/缺号检查、从独立源单据反向追踪(tracing)、与上期/预算的分析性偏离告警、期末截止性测试**。
行业验证:BlackLine/FloQast/Trintech 把「缺失」做成一等公民状态;Content Snare/TaxDome/Financial Cents 在记账事务所场景里这是**标准功能不是新设计**;电商多渠道合并(A2X/Synder/Webgility/PEAK/FlowAccount)**全部是每渠道显式配置的连接器,零个"AI 每月看看有哪些渠道"**。
准则依据(直接管 7-11 场景):ASC 606/IFRS 15 寄售收入确认的**前提条件**就是收到受托方结算报表——PwC Viewpoint:*"only when... they have received reliable and timely reports from the consignee."*

### 2.7 两个明确不要抄

**① 绝不让 LLM 参与任何算术**(含看似无害的求和/换算/分摊)。金额只能**逐字提取**,所有加减乘除用 decimal 在代码里做,行项之和 vs 总额必须有确定性交叉校验。反面样本:TaxHacker(LLM 做分类+拆行项+币种换算,文档没说换算谁算的)。

**② 绝不按厂商自报数字做产品决策或对外承诺**(见 2.5)。

### 2.8 一个必须知道的坑(纠正记忆的失败模式)

ProMem(arXiv 2601.04463)点破:*"if the model makes a mistake ... this error will stay in the memory and hurt future performance"*。
**做「学一次固化」时,记忆条目必须配版本、生效期、一键回滚**,否则错的纠正也会被永久固化。

### 2.9 调研发现的两个真空(负面情报)

1. **没有开源版 Rossum**——没有任何可信开源项目在做「预训练抽取器 + 按发送方持久化纠正记忆」的完整工作流(搜到的 InvoiceShelf/SolidInvoice 全是**开票**工具,名字撞车)。
2. **没有 LLM 原生的 beancount 导入器占主导**——最接近的 `smart_importer`(304★)用的是 **scikit-learn SVC**,从用户自己历史账本现场训练。**这个场景活下来的是经典 ML,不是大模型。**

---

## 3. 月结 Agent 目标框架(Zihao 点名 · 未来实现后的整体流程)

### 3.1 三层宪法(所有设计决策的裁决依据)

```
┌─ 第 3 层 · 会计签规则 ────────────────────────────┐
│  审「以后这类都这么办」的规则,不审每张单据          │
│  签批冻结 → 不可变 manifest → 审计链               │
├─ 第 2 层 · 代码算账(确定性)─────────────────────┤
│  税额 decimal 计算 / 守恒闸 / 勾稽闸 / 跨期抵扣规则  │
│  完整性闸 / 申报表生成 / 事件流回放                 │
│  ★ 同输入必同输出,可复核可追溯                     │
├─ 第 1 层 · Agent 认字(概率)──────────────────────┤
│  读单据 / 分类 / 提议规则 / 卡点自愈 / 发现异常问人  │
│  ★ 永不进入计算路径,永不决定「哪些料算数」          │
└──────────────────────────────────────────────────┘
```

### 3.2 一轮月结的完整流程(★=未建,余为已上线)

```
① 开单           税历自动开单(到期日驱动)/ 深链带账期
                 └ 现状:已上线(obligation_engine 生成当期义务清单)

② 收料           多入口:上传 / 文件夹拖入 / zip / LINE / 邮件 / PDF / Excel
   ★ 完整性登记   客户档案读「本月应到 N 个来源」→ 到齐核对 → 缺谁点名催
                 └ 冰厂例:7-11 汇总 + Big C 对账 + 自开发票 三源缺一不可

③ 分拣+识别     Agent 认字:OCR → 分类(进项/销项/银行/非税)→ 抽字段
   ★ 一次编译     新格式第一次:模型生成解析器 → 人确认 → 固化
                 之后每月零 LLM 调用跑同一段代码(Compiled AI 范式)
                 └ 现状:OCR/分类已上线;编译固化未建

④ 对账+裁决     确定性:余额链 / 跨页交接 / 勾稽 / 方向判定
   ↳ 卡点自愈    Agent:断链换眼重读 ✅(D2)/ 看图裁方向票 ★ / 算术自证补正 ★
   ↳ ★ 主动问人  Agent 发现异常 → 生成一个具体问题给会计
                 └ 冰厂例:「7-11 汇总 385 万,但 50 张发票里没有 7-11,要相加吗?」
   ↳ 人裁决      W3 审核队列(批量键盘流)
   ↳ ★ 升格规则  裁决 → 提议成规则 → 会计批准 → 以后同类自动
                 └ 人审次数随规则数增长,不随单据数增长

⑤ 算税           纯确定性:decimal 求和 / 跨期抵扣(6 个月规则)/ 守恒闸
                 └ ★ Agent 在这一步完全不出现

⑥ 出包           ภ.พ.30 草稿 + 进销底稿 + 银行底稿 + 缺票备忘 + 证据索引
   ↳ 守恒闸      每件必须有明确终态,待裁决>0 → stuck 逐件点名 ✅
   ↳ ★ 完整性闸  预期来源未到齐 → 不许出包(审计学四条:缺号/反查/偏离/截止)

⑦ 人审签批      复核通过 → 签批冻结 → 不可变 manifest ✅(P0-1 修完)
                 SoD 四权分立(制单/复核/授权分离)✅

⑧ ★ 推 ERP      把凭证/分录推进客户 ERP(账本在 ERP,我们不做账本)
                 └ 复用主站已打通的推送线(MR.ERP adapter + erp_push_logs 状态源)
                 └ 工单→ERP 桥目前是空插座,方向级待立单

⑨ 归档           冻结包 + 完整证据链 + 审计留痕 ✅
```

### 3.3 关于 ERP 与账本的定位(Zihao 2026-07-20 明确)

> **我们不做账本。账本始终在 ERP。推送这条路老站已经打通。**

据此定位收敛:

| 我们产出的 | 是什么 | 不是什么 |
|---|---|---|
| 影子底稿(复式分录) | ①税务佐证(证明申报数字自洽)②**推 ERP 的载荷** | ❌ 不是账本,不是总账,一行不写 `journal_vouchers` |
| ภ.พ.30 / ภ.ง.ด. 申报件 | 报税出口(最终交付物) | — |
| 报表页(试算平衡/资产负债/损益) | 影子层的**自查视图** | ❌ 不是客户的正式财报(那是 ERP 出的) |

**推送线现状**:主站独立线已打通(MR.ERP · Playwright/xlsx · `erp_push_logs` 是状态唯一源)。工单线目前只出 xlsx 人工导入,**工单→ERP 桥是空插座**。接线时复用老站 adapter,不新造推送机制。

**GC-E(账簿二期)的定位随之明确**:目标不是「把账做出来」,而是「**让影子分录准确到能直接推进 ERP**」——所以 GC-E 那几条(存货口径错、往来虚挂、分录叙述矛盾、科目桥)是**推送前置质量问题**,不是做账本。

### 3.4 Agent 的四个动作集(笼子)

允许 Agent 做的,只有这四样,且全部走事件流留痕(actor=agent):

1. **认字**:读单据、分类、抽字段(第 1 层)
2. **自愈**:升档/换眼重读、看图裁票、算术自证补正(卡点四动作)
3. **提议**:提议一条规则、提议一个数值修正 → **必须人批准才生效**
4. **问人**:发现异常 → 生成一个具体问题(不是"有问题",是"7-11 要不要相加")

三条笼子铁律(7/19 已拍板,本次调研加固):
- 钱数永由确定性代码算(2.7①)
- 动作全走事件流留痕,可回放可追责
- 每单 token 封顶(照 ฿150 先例)

---

## 4. 下一批施工建议(按价值排序)

| # | 批 | 内容 | 为什么现在做 |
|---|---|---|---|
| **1** | **IN-R 预期输入登记表** | 客户档案存「本月应到 N 个来源」+ 每月到齐核对 + 缺料点名 + 出包完整性闸 | 冰厂三渠道销项**今天实锤**;调研证明这是行业标准功能不是新设计;不大 |
| 2 | AG-1 Agent 问人 | 异常 → 生成具体问题 → 进审核队列 | 最大空白;今天「7-11 不在发票里」是人肉发现的 |
| 3 | GC-E 账簿二期 | 存货口径 / 往来虚挂 / 分录叙述 / 科目桥 | 推 ERP 的前置质量(定位见 3.3) |
| 4 | ERP-B 工单→ERP 桥 | 接老站推送线 | 方向已明确(3.3),等 GC-E 质量达标 |
| 5 | AG-2 规则升格 | 裁决 → 提议规则 → 人批准 → 固化 | ADK 范式;人审次数脱离单据量 |
| 6 | CP-1 一次编译 | 新格式模型生成解析器 → 固化 → 零 LLM 重放 | Compiled AI 范式;等格式样本攒够 |

**GC-D 剩余记债**:D2 真多页断链 PDF 真跑未验(冰厂/SM 2569-06 自然覆盖);GC-D-7 真人旅程(分组确认→采纳→签批)与实测合并做;run_leases scope 参数化 + signoff_projection 挪 evidence(顺手时);`.mx-table`/`.sdw-table` 两套表格 CSS 并存(合并超范围,记债)。

---

## 5. 冰厂(Sincere Ice · 0105546015062)实测备料状态

**已到手(2026-06,`C:\Users\skin3\Downloads\`)**:

| 文件 | 内容 | 数字 |
|---|---|---|
| Invoice Jun Part1/2/3.pdf | 50 张自开 B2B 销项发票(IV69/06-001~050,51 页) | — |
| Details Invoice of Jun 2026 Update.pdf | 上述 50 张的汇总表 | 285,695 + VAT 19,999.30 |
| ยอดขาย 7-11 มิ.ย.pdf | 7-11 日销汇总(30 天) | **3,605,337.20 + VAT 252,373.60** |
| Big C ซอยประชุม / พลับพลาไชย Jun.pdf | 两家分店对账 · **42 页扫描件无文本层** | 待 OCR |
| ลูกค้าส่งแก้ไข IV69.06-011.pdf | 客户送回要改的发票 | 需问:原件作废没?改了什么? |
| บันทึกเงินเดือนพนักงาน 6.2569.pdf | **记账凭证 PV690630-001**(工资分录) | 非税料,可作分拣对抗样本 |

**★ 关键发现**:逐字查过——**50 张发票明细里完全没有 7-11 和 Big C**。三块是**独立且必须相加**的销项来源,7-11 一家占九成。这与 SM(单一 POS 零售)结构完全不同,是本次实测最值钱的考点,也是 IN-R 批的直接触发。

**仍缺**:①纸质进项(拍照,规则:RR69**06**xx 全拍 + 早月但盖 ถือเป็นภาษีซื้อ **6**/2569 章的也拍)②银行流水 ③**金标**(6 月已申报 ภ.พ.30 + 进销项报告;Express 直读可兜底)

**待 Zihao 问客户/事务所**:①7-11 与 Big C 的销售有没有另外开发票(防重复计算)②IV69/06-011 改单状态

---

## 6. 收尾状态

- master `e77f6649`,CI 全绿(run 29718390215),prod 已部署同 commit。
- /simplify:GC-D 全批四路审查已做(~15 项);GC-E-1 为纯机械「修一类」,自审无可收口(两套表格 CSS 合并记债)。
- 5 个 wip 分支已合入并删(远端+本地);施工 worktree 已清;共享树 DMS 窗未碰;未 push=0。
- 换窗入口:本文 + `CLAUDE.md/STATE_PEARNLY.md` 状态卡 + 记忆 `[[gcd-0720-full-queue-shipped]]` `[[agent-boundary-read-vs-calc]]`。
