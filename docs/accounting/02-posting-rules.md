# 自动做账 · 02 自动记账规则目录(★引擎核心 · 业务→借贷模板)

> 这是发动机。每种业务动作 = 一条规则模板,引擎按 `source_type + 上下文` 选模板 → 经 `account_mappings` 把**角色**解析成真科目 → 生成平衡凭证。
> 实现:`services/accounting/rules.py`(模板目录·纯函数·零副作用)+ `posting.py`(取业务→套模板→解析科目→断言平→落库)。基于 TFRS for NPAEs。**钱 Decimal·单次取整对齐业务单(不重算,反解业务单已算好的 subtotal/vat/wht)。**

## 角色(account_mappings 的 role · 规则只认这些)
`inventory 库存` · `cogs 销售成本` · `input_vat 进项税` · `output_vat 销项税` · `ap 应付` · `ar 应收` · `bank 银行` · `cash 现金` · `sales_revenue 销售收入` · `wht_payable 预扣税应缴` · `expense:<category> 费用(按科目)`

## 规则模板(逐条 · 借=贷)

### R1 进货·进项票(赊账) — source=purchase, doc_kind=purchase_invoice, unpaid
```
借 inventory        subtotal(可入库部分)
借 input_vat        vat_amount
贷 ap               grand_total
```
> 现结(paid):贷 `bank/cash` 代替 `ap`。未配 SKU 的进货行 → 借 `expense:<category>` 而非 inventory。

### R2 费用(含服务·WHT) — source=expense / purchase doc_kind=expense
```
借 expense:<category>   subtotal
借 input_vat            vat_amount        (有票才有)
贷 bank/cash 或 ap      net_payable        (= grand_total − wht)
贷 wht_payable          wht_amount         (服务·item_type=service 才有)
```
> 无 VAT 票:无 input_vat 行。无 WHT:无 wht_payable 行。**WHT 来自业务单已算好的 wht_amount,不重算。**

### R3 采购订单(PO·在途) — doc_kind=purchase_order
> **不生成凭证**(未到货/未开票·仅承诺)。收货转进项票(R1)时才记。

### R4 销售开票 — source=sale, sales_document issued
```
借 ar               grand_total
贷 sales_revenue     subtotal
贷 output_vat        vat_amount
```
> 现结:借 `bank/cash` 代 `ar`。客户预扣我方 WHT:借 `wht_prepaid`(我方预付税·资产)代部分 ar。

### R5 POS 当日营业额(汇总) — source=pos, 按终端按日汇总
```
借 bank/cash         日收款合计
贷 sales_revenue      net(不含税)
贷 output_vat         vat
```
> **永续盘存**额外结转成本:`借 cogs / 贷 inventory`(按当日售出 SKU 成本);定期盘存 → 月末统一结。

### R6 收款(应收回款) — source=payment, AR settle
```
借 bank/cash   收到额
贷 ar           收到额
```
### R7 付款(应付付清) — source=payment, AP settle
```
借 ap          付出额
贷 bank/cash    付出额
```

### R8 红冲/退货(CN) — source=purchase/sale credit_note
> 按原凭证**反向**(借贷对调·金额取负或调换),引用原 voucher。逐笔审常涉(方向易错→低 confidence 进待审)。

### R9 月末 VAT 结转 — source=vat_closing(月末触发/手动)
```
借 output_vat       本月销项税合计
贷 input_vat         本月进项税合计
贷 vat_payable       差额(销>进=应交)   或 借 vat_receivable(进>销=留抵)
```
> 喂报税 PP30。

## 数据源分级(C1 · 超越方案核心 · 第一方数据是结构优势)
| source_tier | 来源 | 置信策略 |
|---|---|---|
| `first_party` | POS 卖货 / 销项开票 / 采购在 Pearnly 内发生(结构化·零 OCR 零猜测) | **confidence=100 直通**(仍受 auto_post 开关辖制) |
| `ocr` | 票据识别得来的进项单(LINE/拍照/上传) | 置信分流:门槛上自动、门槛下待审 |
| `bank` | 银行流水(屏6 对账) | **只做建议匹配·人确认才记账**·绝不自动落凭证 |
| `manual` | 手工凭证 | 人录·借贷平断言 |
> 判定:purchase_docs 看 `source`/`created_via`(OCR 入口=ocr·手录=first_party);sales_documents/pos_sales 全部 first_party。自动化率的大头建在自家地基(第一方交易)上,OCR 只覆盖外部来票那一截。

## confidence(进待审还是自动过账)
| 情形 | confidence | 去向 |
|---|---|---|
| 第一方交易(source_tier=first_party)+ 映射命中 | 100 | **auto_posted**(auto_post 开时) |
| 模板清晰 + 科目映射命中 + 业务单完整 | 高(≥门槛) | **auto_posted** |
| 商品/服务判不准(影响 WHT) | 低 | pending_review(逐笔审·见 UI 屏2) |
| 红冲方向 / 科目模糊 / 多分录歧义 | 低 | pending_review |
| `review_learned` 命中(审过的同类) | 拉高 → 自动过 | auto_posted |
> 门槛取 `accounting_settings.auto_post_threshold`。**绝不静默乱过**——拿不准一律待审(状态诚实·铁律#3)。

## 错账安全带三件套(C3 · 信任护城河 · 调研翻车案例反推)
> 用户暴怒从来不是分类错,是"错得安静"(QBO 静默批改/Puzzle 改不回来)。宣传口径定死:不吹自动化率,吹「错了立刻看见、立刻撤销、下次不再犯」。
1. **Method 标注**:每笔凭证 `method` ∈ auto(自动过账)/suggested(建议·人确认)/manual(人工),主屏列表可按此筛(JAX Method 列)——自动改的账永远看得见。
2. **一键撤销重做**:`POST /vouchers/{id}/unpost` 对 auto_posted/posted 凭证整笔撤销(置 void)+ 立即重判(重新 enqueue 跑引擎·吃最新映射/记忆),绝不"改不回来"。防重复唯一索引为 partial(排除 void)以放行重生成。期已结(period_closed)不可撤。
3. **粒度 opt-in**:自动过账受 `auto_post`(全局·**新租户默认 false=建议模式**)+ `auto_post_rules`(按 rule_key 粒度覆盖)双辖制。建议模式下引擎照样算、照样给借贷和置信,只是落 `pending_review`+`method=suggested` 等人点头;跑两周稳了按规则逐条开自动。
> 加已有的人话翻译(human_note 解释每笔为什么这样记)= 可解释,四件齐 = 2026 金标交互水平。

## 引擎流程(posting.py)
```
业务 post/issue/settle ──hook──► enqueue(source_type, source_id)
  → 取业务单(只读·按套账)
  → 选模板 R# (source_type + doc_kind + item_type + payment + has_vat)
  → 解析角色→科目(account_mappings·缺映射=待审+提示配)
  → 反解业务单金额建 journal_lines(不重算)
  → 断言 SUM(借)=SUM(贷)·不平=拒绝+告警(绝不落不平凭证)
  → 定 source_tier(first_party/ocr/bank)→ 算 confidence(first_party=100)
  → confidence≥门槛 且 auto_post 辖制放行(全局或 rule_key 粒度) → auto_posted + method=auto
    否则 → pending_review + method=suggested(建议模式/低置信都走这)
  → 落 journal_voucher + lines(partial UNIQUE source 防重复·排除 void)
```

## seam:业务模块挂 hook(零返工)
- 进项 `purchase_docs.post()` → 已留 hook(见 docs/purchasing/01)→ 接 enqueue('purchase', id)。
- 销项 issue_document → 加 hook。POS 日结 → 加 hook。付款 → 加 hook。
- **幂等**:UNIQUE(source_type,source_id) + enqueue 去重;重跑不重复生成。

## 测试(每模板 ≥1)
R1-R9 各造业务 → 断言生成的借贷科目/金额/平衡正确 · WHT/VAT 反解一致 · 红冲反向 · 缺映射进待审 · review_learned 命中自动过 · 套账隔离 · 防重复(同 source 二次 enqueue 不增凭证)。
