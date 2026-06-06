# Pearnly 知识库 · P3 死规则引擎 · 第一批规则清单

生成日期：2026-06-03
作者：Opus 4.8（设计，非执行）
配套：《Pearnly_知识库RAG_本地沙盒到迁移_多窗口执行计划_2026-06-03.md》第 6 节 Phase 3 / 第 8 节
对象：泰国发票（ใบกำกับภาษี / tax invoice）OCR 后的确定性检查。**全部不走 LLM。**

---

## 0. 给做项目窗口的总则

- **死规则 = 计算器**：同样输入永远同样输出，不会编、毫秒级、零成本、可精确说出"命中第几条规则"。
- **本清单只列"答案唯一确定"的检查**。凡是"要读文字理解"的（合同条款、会计政策）归 RAG（P4），不在这里。
- **规则两类来源**：
  - **全局规则**（税号校验、VAT 算术、查重、必填项）→ 代码里硬编码，所有租户一致。
  - **客户规则**（供应商白名单、金额上限、必须人工复核的供应商/费用类别）→ 存 `client_rules` 表，按 `tenant_id + workspace_client_id` 取，可增删改。
- **输出契约**：引擎返回 `findings`（list）写进 `invoice_risk_checks.findings`（jsonb），每条形如：
  ```json
  {"rule_id":"R-VAT-01","severity":"high","message_key":"risk.vat_mismatch",
   "evidence":{"net":1000.0,"vat":80.0,"expected_vat":70.0},"client_rule_id":null}
  ```
  - `severity`：`high|medium|low`。整张票的 `risk_level` = 所有 findings 里的**最高**严重度（无 finding = `low`）。
  - 任一 `high` → `needs_human_review = true`。
- **误报/白名单**：复用主项目已有的 `exception_whitelist`，命中白名单的 finding 降级或抑制（迁移时接线）。
- **i18n**：所有 `message_key` 进 `i18n-data.js` 四语（th/en/zh/ja），引擎只产出 key + evidence，不产出成句文案。
- **测试要求**：**每条规则**至少 1 正样本（应命中）+ 1 反样本（不该命中）单测；关键规则（税号校验、VAT、查重）进 `eval/golden_set`。

---

## 1. 输入字段（引擎需要 OCR 结构化结果提供）

引擎从一张 OCR 解析后的发票拿到大致这些字段（名称对齐主项目 `ocr_history` 真实 schema，迁移前核对）：

```
seller_tax_id, seller_name, seller_address, seller_branch
buyer_tax_id,  buyer_name,  buyer_address
invoice_no, invoice_date, currency
line_items: [{desc, qty, unit_price, amount}]
net_amount (不含税), vat_amount, total_amount (含税)
doc_type (full_tax_invoice / abbreviated / receipt ...)
is_multipage, pages
当前上下文：tenant_id, workspace_client_id（来自宿主契约）
```

---

## 2. 第一批规则（22 条）

### A. 合法性 / 格式（全局）

#### R-TAXID-01 · 卖方税号校验
- **判定**：`seller_tax_id` 必须是 13 位数字，且**第 13 位 = MOD-11 校验位**。
  - 校验算法（泰国 13 位税号/身份证通用）：
    ```
    sum = Σ digit[i] × (13 - i + 1)   for i = 1..12   # 权重 13,12,...,2
    check = (11 - (sum mod 11)) mod 10
    合法 ⟺ digit[13] == check
    ```
  - ⚠️ 实现后**必须**用一组已知合法/非法税号做单测验证算法（别裸信本文档）。
- **命中（非法）severity**：`high`（税号错=票本身有问题，下游全错）
- **evidence**：`{seller_tax_id}`

#### R-TAXID-02 · 买方税号校验（B2B 时）
- **判定**：当 `buyer_tax_id` 存在（B2B 全额税票），同 R-TAXID-01 校验。个人消费者票可空，空则跳过。
- **severity**：`high`
- **evidence**：`{buyer_tax_id}`

#### R-TAXID-03 · 税号非占位/非全零
- **判定**：税号不得为 `0000000000000`、全同位、明显占位串（OCR 兜底误填）。
- **severity**：`medium`
- **evidence**：`{field, value}`

#### R-DATE-01 · 发票日期合法且非未来
- **判定**：`invoice_date` 能解析为合法日期，且 ≤ 今天（不允许未来发票）。注意泰历(พ.ศ.)与公历(ค.ศ.)差 543 年——**先归一化年份**再判。
- **severity**：`medium`（未来日期）/ `high`（无法解析）
- **evidence**：`{invoice_date, normalized}`

#### R-DATE-02 · 发票日期落在允许会计期间内（客户规则·可配）
- **判定**：若该客户配置了 `accounting_period`（如"只收本月/上月票"），`invoice_date` 不在区间内则命中。未配置则跳过。
- **来源**：`client_rules(rule_type='accounting_period')`
- **severity**：`medium`
- **evidence**：`{invoice_date, period_start, period_end}`

#### R-BRANCH-01 · 分店号格式
- **判定**：`seller_branch` 应为 5 位数字（总店 = `00000`）或泰文"สำนักงานใหญ่"(总店)标识。格式不符则命中。
- **severity**：`low`
- **evidence**：`{seller_branch}`

---

### B. 算术一致性（全局）

> 金额比较一律用容差（如 `abs(a-b) <= 0.01` 元），避免浮点/四舍五入误报。

#### R-VAT-01 · VAT = 不含税额 × 7%
- **判定**：`abs(vat_amount - round(net_amount × 0.07, 2)) <= tol`。
  - ⚠️ 例外：zero-rated(0%)/exempt 发票 VAT=0 合法——**先看 doc_type/标记**，免税票跳过本规则。
- **severity**：`high`
- **evidence**：`{net_amount, vat_amount, expected_vat}`

#### R-VAT-02 · 含税总额 = 不含税 + VAT
- **判定**：`abs(total_amount - (net_amount + vat_amount)) <= tol`。
- **severity**：`high`
- **evidence**：`{net_amount, vat_amount, total_amount}`

#### R-SUM-01 · 行项目合计 = 不含税额
- **判定**：`abs(Σ line_items.amount - net_amount) <= tol`。
- **severity**：`medium`
- **evidence**：`{lines_sum, net_amount}`

#### R-LINE-01 · 单行 数量×单价 = 金额
- **判定**：每行 `abs(qty × unit_price - amount) <= tol`。
- **severity**：`low`
- **evidence**：`{line_index, qty, unit_price, amount}`

#### R-MULTIPAGE-01 · 多页发票聚合一致
- **判定**：`is_multipage` 时，各页聚合后的 net/vat/total 与发票级汇总一致（容差）。
- **severity**：`medium`
- **evidence**：`{pages, page_sums, doc_total}`

#### R-WHT-01 · 预扣税率符合费用类别（客户规则·可配·边界）
- **判定**：若客户为某费用类别配了 WHT 率（服务费常见 3%、租金 5%、运输 1% 等），且票上声明了 WHT，则校验率是否匹配。无配置/无 WHT 字段则跳过。
- **来源**：`client_rules(rule_type='wht_rate')`
- **severity**：`medium`
- **evidence**：`{category, declared_rate, expected_rate}`
- **备注**：率表因客户/税务口径而异，**必须可配**，不硬编码。

---

### C. 查重（全局，需查库）

#### R-DUP-01 · 精确重复
- **判定**：库中已存在同 `(seller_tax_id, invoice_no)` 的历史票（同租户内）→ 重复推送/重复录入风险。
- **severity**：`high`
- **evidence**：`{existing_history_id, seller_tax_id, invoice_no}`

#### R-DUP-02 · 疑似重复
- **判定**：无精确命中，但存在 `(seller_tax_id, total_amount, invoice_date)` 三者全同的历史票 → 疑似（可能换了发票号的重开票）。
- **severity**：`medium`
- **evidence**：`{candidate_history_ids}`

---

### D. 完整性 / 法定必填项（全局，依泰国税法 86/4）

> 仅对"全额税票 full_tax_invoice"严格要求；简易票/收据放宽。

#### R-FIELD-01 · 含"ใบกำกับภาษี"字样
- **判定**：`doc_type=full_tax_invoice` 时，原文应含税票字样。缺失 → 可能不是合规税票。
- **severity**：`medium`
- **evidence**：`{doc_type}`

#### R-FIELD-02 · 卖方信息齐全
- **判定**：`seller_name` + `seller_address` + `seller_tax_id` 三者皆非空。
- **severity**：`medium`
- **evidence**：`{missing: [...]}`

#### R-FIELD-03 · 买方信息齐全（B2B）
- **判定**：B2B 全额税票应有 `buyer_name`（及税号，见 R-TAXID-02）。
- **severity**：`medium`
- **evidence**：`{missing: [...]}`

#### R-FIELD-04 · 发票号 / 日期齐全
- **判定**：`invoice_no` 与 `invoice_date` 皆非空。
- **severity**：`high`（缺这俩无法入账/查重）
- **evidence**：`{missing: [...]}`

#### R-FIELD-05 · 金额结构齐全
- **判定**：`net_amount`、`vat_amount`、`total_amount` 至少能确定其二（第三个可推）。
- **severity**：`medium`
- **evidence**：`{present: [...]}`

---

### E. 名单 / 归属（客户规则）

#### R-SUP-01 · 供应商白名单
- **判定**：客户启用了白名单时，`seller_tax_id` 不在 `client_rules(rule_type='supplier_allowlist')` → 提示"非常用/未授权供应商"。未启用则跳过。
- **severity**：`medium`
- **evidence**：`{seller_tax_id, seller_name}`

#### R-SUP-02 · 供应商强制人工复核
- **判定**：`seller_tax_id` 命中 `client_rules(rule_type='supplier_force_review')` → 直接置 `needs_human_review`。
- **severity**：`high`
- **evidence**：`{seller_tax_id, reason}`

#### R-WS-01 · 票据归属账套一致性
- **判定**：当前 `workspace_client_id` 正在为某主体做账，发票的买方税号应与该主体税号一致（进项票）。对不上 → 可能传错账套。
  - ⚠️ 依赖：能从 workspace_client 拿到其税号（宿主契约提供）。
- **severity**：`high`
- **evidence**：`{buyer_tax_id, workspace_client_tax_id}`
- **备注**：这条直接防"把 A 公司的票录进 B 公司账"——事务所多客户场景的高频事故。

---

### F. 业务边界（客户规则，部分依赖提取值）

#### R-LIMIT-01 · 金额超合同/PO 上限
- **判定**：客户为某供应商/合同配了金额上限（`client_rules(rule_type='amount_limit')`），`total_amount` 超限则命中。
  - 上限**已是结构化数字** → 纯死规则比大小。
  - 上限**还埋在合同 PDF 文字里** → 由 RAG(P4) 先提取成数字写进 `client_rules`，本规则再比大小。**职责分清：提取靠 RAG，比较靠死规则。**
- **severity**：`high`
- **evidence**：`{total_amount, limit, source_rule_id}`

#### R-CAT-01 · 费用类别禁止自动推 ERP
- **判定**：发票归类命中 `client_rules(rule_type='no_auto_push_category')` → 标记"禁止自动推送，需人工"。
- **severity**：`medium`（但应阻断 ERP 自动推送 guard）
- **evidence**：`{category}`
- **备注**：与原方案 8.2"ERP 推送前检查"联动；此规则产出建议，**不写 `erp_push_logs`**。

---

## 3. 引擎结构建议（`services/knowledge/rules_engine.py`）

- 每条规则一个纯函数：`def r_vat_01(invoice, ctx) -> Finding | None`，无副作用、可单测。
- 规则注册成列表，引擎遍历跑、收集非空 Finding。
- 全局规则与客户规则分两组加载；客户规则从 `client_rules` 按 `tenant_id+workspace_client_id` 取。
- 引擎主函数：`def run_rules(invoice, ctx) -> RuleResult{risk_level, findings, needs_human_review}`。
- **<500 行**：规则多了就按 A–F 分子模块（`rules/validity.py`、`rules/arithmetic.py`...），引擎只做编排。
- 文件全部去 AI 味、注释讲 why、英文标识符、署名 Opus 4.8。

---

## 4. 不在第一批（留后续）

- 进项/销项方向判定与 VAT 申报勾稽（要更多税务上下文）。
- 跨期/预付/分期票的复杂入账规则。
- 汇率与外币票换算校验（先假设 THB）。
- 凭历史习惯"猜科目/mapping"——属学习/RAG（P4/Phase4），非死规则。
- 任何需要读合同条款理解的判断——属 RAG（P4）。

---

## 5. 验收（本 Phase done gate 对应项）

1. 22 条规则各有正/反样本单测，全绿。
2. 用 `fixtures/` 构造的问题发票跑一遍，命中预期规则集，**0 次调用 LLM**（可断言）。
3. 每条 finding 都能精确回指 `rule_id` 与 evidence（可审计）。
4. 客户规则增删改 API + 前端 `knowledge-rules.js` 能改 `supplier_allowlist`/`amount_limit` 等并即时生效。
5. 跨租户测试：A 租户的 `client_rules` 绝不作用于 B 租户。
