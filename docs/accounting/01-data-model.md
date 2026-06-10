# 自动做账 · 01 数据模型(字段级 · 从定稿 UI 反推)

> 前后端唯一源。每表 `workspace_client_id` NOT NULL · fail-closed 套账隔离。钱 numeric(14,2) Decimal。
> 外键:tenant_id=uuid · workspace_clients.id=bigint。复用:进项/销项/POS 单据作 `source`(不复制数据,引用)。

## 复用(不新建)
- 业务源:`purchase_docs`(进项)/ `sales_documents`(销项)/ `pos_sales`(POS)/ 付款记录 —— 凭证用 `source_type+source_id` **引用**它们,不复制。
- `services/sales/totals.py`(VAT/WHT 已实现)· reportlab 泰文(账本/报表 PDF)· 套账隔离上下文 `core/workspace_context`。

## 新表

### chart_of_accounts(科目表 · 套账隔离 · 泰标预置)
| 列 | 类型 | 说明 |
|---|---|---|
| id | uuid PK | |
| tenant_id / workspace_client_id | uuid / bigint | 隔离 |
| code | text | 科目编号(1010/2010…) |
| name_zh / name_th | text | 中/泰文名(UI 双显) |
| acct_type | text | asset/liability/equity/revenue/expense |
| parent_id | uuid NULL | 两级(细分科目) |
| is_preset | boolean | 预置(不可删·可停) |
| is_active / sort | boolean / int | |
| UNIQUE | (tenant_id, workspace_client_id, code) | |

### account_mappings(科目映射 · 角色→科目 · 规则引擎引用)
| 列 | 类型 | 说明 |
|---|---|---|
| id | uuid PK · tenant_id · workspace_client_id | |
| role | text | 逻辑角色:`inventory`/`input_vat`/`output_vat`/`ap`/`ar`/`bank`/`cash`/`sales_revenue`/`wht_payable`/`cogs`/`expense_default`… |
| account_id | uuid FK→chart_of_accounts | 该角色对应的真科目 |
| UNIQUE | (tenant_id, workspace_client_id, role) | |
> 规则引擎只认**角色**,过账时经此表解析成真科目 → 用户改映射不动规则代码。预置默认映射随科目表 seed。

### journal_vouchers(凭证头)
| 列 | 类型 | 说明 |
|---|---|---|
| id | uuid PK · tenant_id · workspace_client_id | |
| voucher_no | text | 连号(按主体按期·见连号) |
| voucher_date | date | |
| period | text | `YYYY-MM`(归属会计期) |
| source_type | text | `purchase`/`sale`/`pos`/`payment`/`expense`/`manual`/`adjustment`/`vat_closing` |
| source_id | uuid NULL | 引用业务单(不复制) |
| source_ref | text | 显示用("采购进项单 #..") |
| description | text | 摘要 |
| human_note | text NULL | 人话翻译(UI 展示) |
| rule_key | text | 套了哪条规则(见 02·可追溯) |
| confidence | numeric(5,2) | 引擎把握(<设置门槛→待审) |
| source_tier | text | 数据源分级(C1):`first_party`(POS/销项/采购在系统内发生)/`ocr`(票据识别)/`bank`(流水建议)/`manual` |
| method | text | 安全带①(C3):`auto`(引擎自动过账)/`suggested`(引擎建议·人确认)/`manual`(人工/手工凭证)·列表可筛 |
| status | text | `auto_posted`/`pending_review`/`posted`/`void` |
| total_debit / total_credit | numeric(14,2) | **入库前断言相等** |
| created_by | text | `system` 或 user uuid |
| reviewed_by | uuid NULL | 审核人 |
| created_at/updated_at | timestamptz | |
| UNIQUE | (tenant_id, workspace_client_id, source_type, source_id) **WHERE source_id NOT NULL AND status != 'void'** | **防重复生成凭证**;partial 排除 void = 撤销重做(undo+重判)后允许同 source 重新生成 |

### journal_lines(凭证明细 = 借贷分录)
| 列 | 类型 | 说明 |
|---|---|---|
| id | uuid PK · tenant_id | |
| voucher_id | uuid FK | |
| account_id | uuid FK→chart_of_accounts | |
| dr_cr | text | `debit`/`credit` |
| amount | numeric(14,2) | >0 · Decimal |
| memo | text NULL | |
| sort | int | |
> 约束:每凭证 `SUM(debit)=SUM(credit)`(应用层断言 + 入账校验,不平拒绝)。

### accounting_settings(做账设置 · 一套账一行)
| auto_post(bool·**默认 false=建议模式**) · auto_post_threshold(numeric·默认90) · auto_post_rules(jsonb·安全带③粒度 opt-in:rule_key→bool 覆盖全局 auto_post,如 `{"R1":true}`=只进货自动) · accounting_standard(默认 'TFRS_NPAE') · inventory_method('perpetual'/'periodic') · base_currency('THB') · start_period('YYYY-MM') |
> **安全带③(C3)**:新租户默认 `auto_post=false`(建议模式·引擎生成的凭证全部 `pending_review`+`method=suggested`,人确认才过账),跑稳才按规则粒度逐条开自动。绝不学 QBO 静默批改。

### review_learned(审例外记忆 · 越用越省)
| id · tenant_id · workspace_client_id · scope_key(如 `supplier:<id>` / `desc_hash:<h>`)· decision(jsonb:{item_type/account_role/wht_rate…})· created_by · created_at |
> 逐笔审解决一笔 → 落一条;引擎下次同 scope 命中 → 直接套、自动过账(不再进待审)。

## 连号(凭证号 · 按主体按期 · 合规)
凭证号按 `(tenant, workspace_client, period)` 各自连号(`document_number_sequences` 复用·扩 doc_type='voucher'·`FOR UPDATE` 防跳号)。多主体各跑各的号。

## 套账隔离机械闸
`test_accounting_sql_isolation`:科目/凭证/明细/映射每句 SQL 必带 workspace_client_id;A 套账拿不到 B。纳入 CI。
