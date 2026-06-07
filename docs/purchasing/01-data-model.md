# 商户采购 · 01 数据模型(字段级 · 从定稿 UI 反推)

> 前后端唯一源。建在套账隔离地基上(每表 `workspace_client_id`,fail-closed)。外键类型对齐现有:
> tenant_id=uuid · products.id=uuid · workspace_clients.id=bigint。

## 复用(不新建)
- `products` / `product_units`:进货品项匹配 SKU(匹配不上→建新商品)。
- `workspace_clients`:卖方/本公司主体 + `promptpay_id`。
- `inventory_*`:进货入库走 `inventory_transactions`(ref_type=purchase)。
- OCR 引擎(`services/ocr/*`):扩 schema 认进项票(见 03)。

## 新表

### suppliers(供应商主数据 · 套账隔离 · AI 拍票自动建为主)
| 列 | 类型 | 说明 |
|---|---|---|
| id | uuid PK | |
| tenant_id | uuid NOT NULL | |
| workspace_client_id | bigint NOT NULL | 套账隔离硬边界 |
| name | text NOT NULL | |
| tax_id | text NULL | 13 位(小供应商可空) |
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
| doc_date | date | |
| has_vat | boolean | 是否含可抵进项税 |
| subtotal / vat_amount / grand_total | numeric(14,2) | 钱 Decimal |
| currency | text DEFAULT 'THB' | |
| category_id | uuid FK→expense_categories NULL | 费用/科目 |
| payment_status | text | unpaid/partial/paid |
| paid_amount | numeric(14,2) | |
| due_date | date NULL | 账期 |
| source | text | photo/line/manual/upload(来源) |
| ocr_raw | jsonb NULL | OCR 原样(可追溯/复算) |
| image_url / pdf_url | text NULL | 票图 |
| dedupe_key | text NULL | = hash(supplier_tax+doc_no+grand_total)·防重复票 |
| status | text | draft/posted/void |
| created_by | uuid | |
| created_at/updated_at | timestamptz | |
| UNIQUE | (tenant_id, workspace_client_id, dedupe_key) WHERE dedupe_key NOT NULL | **防重复抵扣** |

### purchase_lines(明细)
| 列 | 类型 | 说明 |
|---|---|---|
| id | uuid PK | tenant_id | purchase_doc_id FK |
| product_id | uuid NULL | 匹配到的 SKU(匹配不上=NULL,可一键建商品) |
| description | text | OCR 抽的品名(未匹配时用) |
| qty / unit | numeric(14,3) / text | |
| unit_price / line_total | numeric(14,2) | |
| vat_applicable | boolean | |
| batch_no / expiry_date | text / date NULL | 进货带批次→入库用 |

### expense_categories(费用科目 · AI 归类用 · 预设泰国标准 + 可改)
| id uuid PK · tenant_id · workspace_client_id · name · is_active · sort | 预设:进货/交通/水电/办公/清洁/租金/广告/维修 |

### purchase_settings(采购设置 · 一套账一行)
| 默认进项 VAT 率 · 进货自动入库(bool)· 重复票拦截(bool)· 默认账期(天)· 付款需审批(bool) |

### intake_items(智能分流待归类 · AI 拿不准时落这,等用户一点)
| id uuid · tenant_id · workspace_client_id · source(photo/line)· raw(jsonb/文字)· image_url · ai_guess(jsonb:{type,confidence})· status(pending/resolved)· resolved_doc_id |

## 联动(seam 在模型层留好)
- **进货入库**:`purchase_docs.post()` + 进货入库开 → 按 `purchase_lines.product_id` 写 `inventory_transactions`(ref_type=purchase·ref_id=purchase_doc.id·带批次/成本)。匹配不上 SKU 的行先建商品。
- **进项 VAT→报税**:月度汇总 `SUM(vat_amount) WHERE doc_kind='purchase_invoice' AND has_vat AND posted`(按套账)→ 喂报税(销项税−进项税)。
- **付款→应付**:`payment_status/paid_amount/due_date` 派生应付 aging;付款记录将来对银行流水(seam 留)。
- **做账(Phase 2)**:`post()` 留 hook → 生成进项凭证(借 费用/库存+进项税,贷 应付/现金)。

## 迁移(Alembic · 续 0029 之后)
```
0030_suppliers
0031_purchase_docs_lines
0032_expense_categories + purchase_settings + intake_items(预设科目 seed)
```
> prod 经 ensure_* 双跑;每表 ≥1 测试;套账隔离 SQL 闸纳入(workspace_client_id 必带)。
