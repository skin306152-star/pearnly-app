# 知识库规则引擎 · 统一接管异常检测 · 迁移方案

状态:草案待 Zihao 审 · 不碰代码 · 2026-06-04
分支:`feat/knowledge-backend` · 全程 flag 后面 · 可回滚 · 真发票验证

---

## 0. 目标与铁律

**目标**:`services/knowledge/rules_engine.py` 成为**唯一**规则来源;旧 `services/exceptions/exception_checks.py` 里内联的规则逻辑退休。一套引擎,不再两套打架(铁律 #12 单一来源)。

**保持不变**(只换"出题的引擎",不换"考场"):异常存储 `store.py`、白名单 `exceptions_whitelist.py`、放行/忽略、抽屉 UI、KPI、LINE 提醒。

**保留旧的两样**(它们本来就不是规则):
- `confidence_low`(OCR 没看清的信号,非发票对错)→ 留旧路径。
- 高额/高风险 **LINE 提醒**(通知行为,非规则)→ 保留,改成由新 findings 触发。

**验收闸(Zihao 拍板)**:每接好一条规则,配**一张"模拟该规则触发条件"的测试**——构造一张"应命中"的发票断言规则触发 + 一张"干净"的断言不触发。绿 = 这条规则"完成"。

---

## 1. 旧 → 新 逐条对照

| 旧异常检查 | 新引擎规则 | 覆盖? | 注意 |
|---|---|---|---|
| `math_mismatch`(VAT/金额算术) | R-VAT-01/02 · R-SUM-01 · R-LINE-01 | ✅ 更细 | **核对容差**(旧的 tolerance vs 新的),别一换就多报 |
| `tax_id_format_invalid`(税号) | R-TAXID-01/02/03 | ✅ 更严(带 MOD-11 校验位) | 可能对"历史曾通过"的票多报 → 见 §6 决策 |
| `amount_missing`(缺字段) | R-FIELD-01~05(完整性) | ✅ | — |
| `duplicate`(重复票) | R-DUP-01/02 | ⚠️ 逻辑就绪·**缺接线** | 需接真 ocr_history 查重 lookup,见 §2.1 |
| `confidence_low`(置信度低) | 无 | ❌ 不归规则 | **保留旧路径** |
| 大额/高风险 LINE 提醒 | 无 | ❌ 非规则 | **保留**,由新 findings 触发 |
| (新增)供应商必审/白名单 | R-SUP-01/02 | 🆕 | 客户规矩,纯新增价值 |
| (新增)合同金额上限 | R-LIMIT-01 | 🆕 | 客户规矩 |
| (新增)会计期间 / 预扣税 / 分支 / 归属 | R-DATE-02 · R-WHT-01 · R-BRANCH-01 · R-WS-01 · R-CAT-01 | 🆕 | 客户规矩 |

---

## 2. 缺口补齐清单(切换前必做)

### 2.1 接查重 lookup
`R-DUP-01/02` 通过 `RuleContext.find_exact_duplicate` / `find_suspected_duplicates` 取数,沙盒是空的。
- 补:在 `services/knowledge/risk_check.py`(或 host_provider)提供 ocr_history 支持的实现:
  - `find_exact_duplicate(seller_tax_id, invoice_no, tenant_id)` → 已存在的 history_id 或空
  - `find_suspected_duplicates(seller_tax_id, total_amount, invoice_date, tenant_id)` → 候选 id 列表
- **必须 tenant 隔离**(只在本租户内查重)。

### 2.2 保留 confidence_low + LINE 提醒
`exception_checks.py` 改造为:flag 开时 → ① 调新引擎产 findings → ② 映射成异常行;③ **照旧**补 `confidence_low`;④ **照旧**跑 LINE 提醒(改成读新 findings 的 severity)。

### 2.3 白名单名称映射(别让用户白学)
旧"忽略此类"按旧规则名存(如 `math_mismatch`),新规则叫 `R-VAT-01`。建映射表,查白名单时用它,旧学习继续生效:
```
math_mismatch        ↔ {R-VAT-01, R-VAT-02, R-SUM-01, R-LINE-01}
tax_id_format_invalid↔ {R-TAXID-01, R-TAXID-02, R-TAXID-03}
duplicate            ↔ {R-DUP-01, R-DUP-02}
amount_missing       ↔ {R-FIELD-01..05}
```
(粒度见 §6 决策。)

### 2.4 Finding → 异常行 字段映射
新 `Finding(rule_id, severity, message_key, evidence)` → 旧异常行(rule/severity/detail 列)。一处转换函数,集中维护。

---

## 3. 接入位置(改最少、风险最低)

旧 `exception_checks` 被 4 处调用:`ocr/recognize/persist.py`、`recognize/cache.py`、`line_image_ocr.py`、`history_routes.py`。
- **不动这 4 个调用点**。只换 `exception_checks` 内部"产规则"那段:`KNOWLEDGE_RULES` flag 开 → 调 `rules_engine.run_rules`;关 → 旧逻辑(回滚路径)。
- `rules_engine` 输入:从 OCR history payload 构造 `Invoice` + `RuleContext`(注入该客户的 `client_rules` + 查重 lookup)。

---

## 4. 实施阶段(激进版 · Zihao 2026-06-04 拍板:无用户无数据,跳过影子/比对/白名单迁移)

> 因当前**无真实用户、无生产数据**,省去影子并行、真发票 parity、旧白名单迁移这三套"保命"步骤。验证靠 §5 的"每条规则模拟触发测试"+ 集成测试。仍保留 flag 作干净开关/回滚。

| 阶段 | 做什么 |
|---|---|
| **P0** | 本方案 · 已审 |
| **P1 脚手架** | 在 `exception_checks` 建接入层:OCR payload → `Invoice` + `RuleContext`(注入 client_rules + 查重 lookup);`Finding` → 异常行映射;接真 ocr_history 查重 lookup;`KNOWLEDGE_RULES` flag |
| **P2 逐条接规则** | 一组一组把规则接上(算术 → 税号 → 完整性 → 查重 → 客户规矩),**每条配一张模拟触发测试**(§5),绿了再下一条 |
| **P3 切换 + 删旧** | flag 开 → 新驱动异常;**删掉旧规则逻辑**;保留 `confidence_low` + LINE 提醒(照旧) | 回滚 = flag 关 |
| **P4 客户规矩 UI** | 配供应商名单/上限/账期 + 抽屉显示新规则 |

旧白名单**不迁移**(无数据);新白名单直接用新 rule_id。

---

## 5. 测试策略(Zihao 拍板:每条规则一张模拟触发测试)

1. **单元(每条规则一对)**:`test_rules_engine` 已覆盖 28 条逻辑。补:① 缺的客户规矩规则 ② 依赖 lookup 的 R-DUP(用假 lookup 注入"有重复/无重复"两种)。每条:**应触发的样本断言命中** + **干净样本断言不命中**。
2. **集成**:喂一条构造的 OCR history → 跑改造后的 `exception_checks` → 断言:生成的异常行 rule/severity 对、白名单映射生效、confidence_low/LINE 仍在。
3. **Parity(P2 关键)**:一组脱敏真发票,新旧引擎输出逐票 diff;旧报的新必须也报;新多报的逐条确认是"改进"还是"误报"。
4. **闸**:某条规则的模拟触发测试绿 = 这条"完成"才往下做。

---

## 6. 待 Zihao 拍板的 3 个点

1. **白名单粒度**:用户对旧 `math_mismatch` 点过"忽略此类",换新后是**忽略整组**(R-VAT/R-SUM/R-LINE 全不报)还是**细分到具体规则**?(建议:先整组,贴合旧行为,不惊扰用户。)
2. **税号变严**:新 R-TAXID 带校验位,会对一些"以前能过"的票多报。**接受更准但更吵吗?**(建议:接受,但把"校验位不过"设为"中"不设"高",先观察。)
3. **confidence_low 要不要也统一进新引擎**(做一条读 OCR payload 置信度的规则),还是保持旧路径独立?(建议:保持旧路径,它本质不是发票规则,混进去反而不清晰。)

---

## 6b. 决议(Zihao 2026-06-04 · 激进版,取代上方待定项)

无用户、无数据 → 跳过影子/比对/白名单迁移。
1. 白名单:不迁移,直接用新 rule_id。
2. 税号:接受更严(带校验位),不为旧票让步。
3. confidence_low:**不**塞进新引擎,保持旧路径。

**架构定**:统一路径下,引擎产出的 `Finding` **写进现有异常存储**(`db.insert_exception` · 经 `db.is_exception_whitelisted(..., new_rule_id)` 查白名单),由现有异常 UI 直接显示;**不**用 `invoice_risk_checks` 表(standalone 那条路在统一后闲置,后续可删)。`confidence_low` + LINE 提醒在 `exception_checks` 内照旧保留。查重 lookup 接真 ocr_history。

---

## 7. 不在本方案内(后续)

- RAG 带出处问答(读合同/政策)— 知识库 P4,另起。
- 客户规矩的复杂条件编排 UI — V1 先单条。
- 5 张知识库表在真 Supabase 建表 — 切换前用 Alembic 应用(含 `CREATE EXTENSION vector`,可能需 Supabase 后台开权限)。
