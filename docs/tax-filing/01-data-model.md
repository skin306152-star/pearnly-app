# 自动报税 · 01 数据模型(字段级)

> 每表 `workspace_client_id` NOT NULL · fail-closed 隔离 · 钱 Decimal。报税**吃做账/进项的产出**,不复制业务,引用 + 汇总。

## 复用(不新建)
- 做账 `journal_vouchers/lines`(销项税/进项税科目 → PP30 汇总源)。
- 进项 `purchase_docs/lines`(item_type=service + wht_amount + 供应商 → PND 明细源)+ 已生成的扣缴凭证(`purchase_attachments` kind=wht_cert)。
- 销项 `sales_documents`(销项税源)。
- reportlab 泰文(税表/扣缴凭证 PDF)。

## 新表

### tax_filings(税表头 · 一期一种一行)
| 列 | 类型 | 说明 |
|---|---|---|
| id | uuid PK · tenant_id · workspace_client_id | |
| period | text | `YYYY-MM`(申报所属期) |
| kind | text | `pp30` / `pnd53` / `pnd3`(年度 pnd50 留 Phase4) |
| status | text | `prepared`(自动备好)/`reviewed`(已复核)/`filed`(已报)/`void` |
| net_amount | numeric(14,2) | 应交(PP30 可负=留抵) |
| breakdown | jsonb | 算出来的明细(output_vat/input_vat/留抵 或 各笔 WHT 汇总) |
| anomalies | jsonb | 报前异常(超期进项/缺税号…·见 02) |
| due_date | date | 截止(按 settings 提交方式算) |
| filed_method | text NULL | `etax` / `manual_export` |
| receipt_no | text NULL | e-Tax 回执号 |
| filed_at / filed_by | timestamptz / uuid NULL | |
| created_at/updated_at | timestamptz | |
| UNIQUE | (tenant_id, workspace_client_id, period, kind) | 一期一种唯一 |

### filing_lines(PND 逐笔代扣明细 · PP30 用 breakdown 即可)
| 列 | 类型 | 说明 |
|---|---|---|
| id | uuid PK · tenant_id · filing_id FK | |
| payee_name / payee_tax_id | text | 收款人(供应商/个人) |
| payee_type | text | `juristic`(公司→PND53)/`individual`(个人→PND3) |
| income_type | text | 服务/租金/咨询…(税率依据) |
| base_amount / wht_rate / wht_amount | numeric | 付款额/率/代扣额 |
| source_purchase_id | uuid NULL | 追溯到进项付款 |
| cert_url | text NULL | 扣缴凭证 PDF(关联进项已生成的) |
| cert_status | text | generated / missing_tax_id(缺税号) |

### 报税设置(并入 accounting_settings 或 tax_settings · 一套账一行)
| vat_registered(bool) · branch_type/branch_no · efiling_connected(bool·RD e-filing 接入态) · efiling_credential_ref(凭据引用·不存明文) · remind_days_before(默认3) · file_zero(bool·0也报·默认true) |

## 连号 / 唯一性
税表无连号(按期按种唯一);扣缴凭证号复用进项已生成的。e-Tax 回执号存 receipt_no。

## 套账隔离机械闸
`test_tax_sql_isolation`:tax_filings/filing_lines 每句 SQL 带 workspace_client_id;税号按主体;A 拿不到 B。
