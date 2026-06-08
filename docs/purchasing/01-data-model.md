# 商户采购 · 01 数据模型(字段级 · 封板 · 从定稿 UI + Paypers 对标反推)

> 前后端唯一源。建在套账隔离地基上(每表 `workspace_client_id`,fail-closed)。外键类型对齐现有:
> tenant_id=uuid · products.id=uuid · workspace_clients.id=bigint。
> **本版已并入 Paypers 对标补缺(7 项)**:WHT 预扣税 · 替代收据 · 报销审批人 · 两级费用科目 · 商品/服务区分 · 多币种 · 供应商地址/总分公司。详见 [[pearnly-2.0-positioning-closed-loop]] 与 `用户需求/` 截图。

## 复用(不新建)
- `products` / `product_units`:进货品项匹配 SKU(匹配不上→建新商品)。
- `workspace_clients`:卖方/本公司主体 + `promptpay_id`。
- `inventory_*`:进货入库走 `inventory_transactions`(ref_type=purchase)。
- OCR 引擎(`services/ocr/*`):**判方向 + 抽全卖方**(见 03 PO-3;不是新增票种)。
- **WHT 计算 + 泰文合规 PDF**:复用销项 `services/sales/totals.py`(价内外/WHT 已实现)+ reportlab 泰文字体(`services/sales/*` 合规 PDF)。替代收据/扣缴凭证走同一套,不从零造。
- **审批工作流**:复用 `services/sales/approval.py`(销项 §F 已落)。

## 新表

### suppliers(供应商主数据 · 套账隔离 · AI 拍票自动建为主)
| 列 | 类型 | 说明 |
|---|---|---|
| id | uuid PK | |
| tenant_id | uuid NOT NULL | |
| workspace_client_id | bigint NOT NULL | 套账隔离硬边界 |
| name | text NOT NULL | |
| tax_id | text NULL | 13 位(小供应商可空) |
| **branch_type** | text DEFAULT 'none' | `head_office`/`branch`/`none`(总公司/分公司/无分支·合规票用) |
| **branch_no** | text NULL | 分公司编号(branch_type=branch 时) |
| **address** | text NULL | 供应商地址(替代收据/合规用) |
| phone / note | text NULL | |
| is_active | boolean | 停用=隐藏不删 |
| created_at/updated_at | timestamptz | |
| UNIQUE | (tenant_id, workspace_client_id, tax_id) WHERE tax_id NOT NULL | 防重 |

### purchase_docs(进项单据头:进项票 / 采购单 / 费用)
| 列 | 类型 | 说明 |
|---|---|---|
| id | uuid PK | |
| tenant_id / workspace_client_id | uuid / bigint | 隔离 |
| doc_kind | text | `purchase_invoice`(进项票·有VAT抵) / `purchase_order`(采购单·在途·无VAT) / `expense`(费用) |
| supplier_id | uuid FK→suppliers NULL | 费用可空 |
| doc_no | text NULL | 供应商票号 |
| doc_date | date | 开票/收据日期 |
| has_vat | boolean | 是否含可抵进项税 |
| currency | text DEFAULT 'THB' | **多币种**(THB/USD/…·非 THB 存原币 + 记账汇率) |
| fx_rate | numeric(14,6) DEFAULT 1 | 折 THB 汇率(currency≠THB 时) |
| subtotal | numeric(14,2) | 税前小计 |
| discount_total | numeric(14,2) DEFAULT 0 | 折扣合计 |
| vat_amount | numeric(14,2) | 进项税(可抵) |
| **wht_amount** | numeric(14,2) DEFAULT 0 | **预扣税合计(代供应商扣缴)** |
| **rounding** | numeric(14,2) DEFAULT 0 | 凑整 |
| grand_total | numeric(14,2) | 含税合计(subtotal−discount+vat±rounding) |
| **net_payable** | numeric(14,2) | **实付供应商 = grand_total − wht_amount** |
| category_id | uuid FK→expense_categories NULL | 单据级默认科目(行可覆盖) |
| **requester** | text NULL | 报销申请人姓名(Paypers ผู้ขออนุญาตเบิกจ่าย) |
| **requester_user_id** | uuid NULL | 关联用户(选填) |
| **approval_status** | text DEFAULT 'none' | none/pending/approved/rejected(复用销项 approval) |
| payment_status | text DEFAULT 'unpaid' | unpaid/partial/paid |
| paid_amount | numeric(14,2) DEFAULT 0 | |
| due_date | date NULL | 账期(按 purchase_settings 默认 + 可改) |
| source | text | photo/line/manual/upload |
| ocr_raw | jsonb NULL | OCR 原样(可追溯/复算) |
| dedupe_key | text NULL | = hash(supplier_tax+doc_no+grand_total)·防重复票 |
| status | text DEFAULT 'draft' | draft/posted/void |
| created_by | uuid | |
| created_at/updated_at | timestamptz | |
| UNIQUE | (tenant_id, workspace_client_id, dedupe_key) WHERE dedupe_key NOT NULL | **防重复抵扣** |

> **钱字段全 Decimal**。WHT/VAT/凑整单次取整对齐(同 POS 餐厅服务费教训:逐步取整防 ±1 分漂移)。

### purchase_lines(明细)
| 列 | 类型 | 说明 |
|---|---|---|
| id | uuid PK | |
| tenant_id | uuid | 冗余隔离 |
| purchase_doc_id | uuid FK | |
| **item_type** | text DEFAULT 'goods' | `goods`(商品) / `service`(服务·触发 WHT 默认) |
| product_id | uuid NULL | 匹配到的 SKU(NULL=未配·可一键建商品) |
| description | text | OCR 抽的品名(未匹配时用) |
| qty | numeric(14,3) | |
| unit | text NULL | |
| unit_price | numeric(14,2) | |
| discount | numeric(14,2) DEFAULT 0 | 行折扣 |
| line_total | numeric(14,2) | 行小计 |
| vat_rate | numeric(5,2) DEFAULT 7 | 行 VAT 率(0=ไม่มี vat) |
| vat_applicable | boolean | |
| **wht_rate** | numeric(5,2) DEFAULT 0 | 行预扣率(服务默认按类型·0=不扣) |
| category_id | uuid FK→expense_categories NULL | **行级科目(大类)** |
| **subcategory_id** | uuid FK→expense_categories NULL | **行级子科目(两级)** |
| batch_no / expiry_date | text / date NULL | 进货带批次→入库用 |

### expense_categories(费用科目 · 两级 · AI 归类用 · 预设泰国标准 + 可改)
| 列 | 类型 | 说明 |
|---|---|---|
| id | uuid PK | |
| tenant_id / workspace_client_id | uuid / bigint | 隔离 |
| **parent_id** | uuid FK→expense_categories NULL | **NULL=大类,非空=子类(两级)** |
| name | text | |
| is_active / sort | boolean / int | |

> 预设(大类›子类):进货 · 交通(打车/油费)· 水电(水费/电费)· 办公(文具/设备)· 清洁 · 租金 · 广告 · 维修 · 服务外包。AI 归类映射到子类。

### purchase_attachments(单据附件 · 票图 + 凭据)
| 列 | 类型 | 说明 |
|---|---|---|
| id | uuid PK | tenant_id · purchase_doc_id FK |
| kind | text | `bill`(票图)/`substitute_receipt`(替代收据·系统生成)/`payment_proof`(付款凭证)/`wht_cert`(扣缴凭证·系统生成) |
| url | text | 文件地址 |
| generated | boolean DEFAULT false | true=系统生成的 PDF(替代收据/扣缴凭证) |
| created_at | timestamptz | |

> **替代收据 / 扣缴凭证**:`generated=true` 的 PDF,由 reportlab(复用销项泰文模板)生成,挂这张表。无正规发票的费用 → 生成 `substitute_receipt` 使其合规可抵。

### purchase_settings(采购设置 · 一套账一行)
| 字段 | 说明 |
|---|---|
| default_vat_rate | 默认进项 VAT 率(7) |
| auto_stock_in | 进货自动入库(bool) |
| dedupe_block | 重复票拦截(bool) |
| default_due_days | 默认账期天数(0=现结) |
| pay_needs_approval | 付款需审批(bool) |
| **default_wht_service_rate** | 服务默认预扣率(3%·可改) |
| **base_currency** | 记账本位币(THB) |

### intake_items(智能分流待归类 · AI 拿不准时落这,等用户一点)
| id uuid · tenant_id · workspace_client_id · source(photo/line)· raw(jsonb/文字)· image_url · ai_guess(jsonb:{kind,confidence})· status(pending/resolved)· resolved_doc_id |

## 联动(seam 在模型层留好)
- **进货入库**:`post()` + 进货入库开 → 按 `purchase_lines.product_id` 写 `inventory_transactions`(ref_type=purchase·ref_id=doc.id·带批次/成本)。未配 SKU 的行先建商品。
- **进项 VAT→报税**:月度汇总 `SUM(vat_amount) WHERE doc_kind='purchase_invoice' AND has_vat AND posted`(按套账)→ 喂报税(销项税−进项税)。
- **WHT→报税**:`SUM(wht_amount)` 按月汇总 → PND 53/3 扣缴申报(Phase 3 接;本期记 + 出扣缴凭证)。
- **付款→应付**:`payment_status/paid_amount/due_date` 派生应付 aging;付款记录将来对银行流水(seam 留)。
- **做账(Phase 2)**:`post()` 留 hook → 生成进项凭证(借 费用/库存+进项税,贷 应付/现金;WHT 贷 应交税费-代扣)喂做账引擎。

## 迁移(Alembic · ⚠️ 0030 已被 `product_units_workspace_client_id` 占 · 续 0031)
```
0031_suppliers
0032_purchase_docs + purchase_lines           (含 WHT/rounding/net_payable/currency/fx/item_type/两级科目)
0033_expense_categories(两级) + purchase_settings + intake_items + purchase_attachments(预设科目 seed)
```
> prod 经 ensure_* 双跑;新 ensure 标 `NEW-DEBT-EXEMPT`;每表 ≥1 测试;套账隔离 SQL 闸纳入(workspace_client_id 必带·见 05)。
