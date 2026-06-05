# 02 · 数据模型

> 对齐主仓库约定:多租户键 `tenant_id`(**UUID** · 已实扫确认)+ RLS(`SET LOCAL app.current_tenant_id` /
> policy `tenant_id::text = current_setting('app.current_tenant_id', true)`);
> 钱一律 `NUMERIC(14,2)`(不用 float/REAL);时间一律 `TIMESTAMPTZ`(存 UTC)。
> **新表走 Alembic 迁移**(`alembic/versions/NNNN_*.py` · 见既有 0001-0005 · **禁新增 `ensure_*`**);
> 热路径索引微调可走 `scripts/sql/*.sql` 手动 psql(见 b9)。
> ⚠️ **FK 类型坑**:`client_id` 必须匹配 **`clients.id` 的实际类型**(既有 PRD 为 INTEGER/BIGSERIAL ·
> 不是 UUID)· 迁回前先 `\d clients` 核实,别照搬下文 UUID 草案。
> 可执行草案见 `migrations/0001_sales_core.sql`(草案用 UUID 占位 · 落 Alembic 时按真实类型改)。

## 决策无关的核心表(几乎所有方案分支都需要)

### products · 商品主数据(新建)

| 列 | 类型 | 说明 |
|---|---|---|
| id | UUID PK | |
| tenant_id | UUID NOT NULL | RLS 键 |
| code | TEXT | 商品代码(手输录入用)· (tenant_id, code) 唯一 |
| barcode | TEXT NULL | 条形码(扫码录入)· Phase 2 |
| qr_payload | TEXT NULL | 二维码内容 · Phase 2 |
| name_th / name_en / name_zh | TEXT | 三语名(i18n) |
| unit | TEXT | 单位(个/ชิ้น…) |
| unit_price | NUMERIC(14,2) | 单价 |
| vat_applicable | BOOLEAN | 是否计 7% VAT |
| image_url | TEXT | **菜单图卡点选用图 · 一等字段**(客户 Q2 选图库点选 · Phase 1 就要) |
| category_id | UUID NULL | 复用现有分类体系 |
| is_active | BOOLEAN | 软删 |
| created_at / updated_at | TIMESTAMPTZ | |

> 库存/收银相关列(stock_qty / cost 等)**不在此表**,取决于 Q1(真 POS 才需要),见 `docs/09`。
>
> **商品图来源:两种都做**——手动上传(`image_url` 存图)+ Excel 批量导入带图(`product_import` 解析图列/URL)。

### 客户级兼容配置(②③④ 全做兼容 · 无需问客户 · 见 `docs/09`)

挂在每个 **workspace_client / tenant**(复用现有客户体系,加字段):

| 配置 | 取值 | 作用 |
|---|---|---|
| `vat_registered` | bool | **注册 VAT → 可开税票(含 7%);未注册 → 只开普通收据**。两种都支持,按客户开关。 |
| `default_send_channel` | email / line / print | 发送默认渠道(三种都做,默认 email,客户可改) |
| `numbering` | 见上 document_number_sequences 配置 | 前缀/重置/起始号等,默认兜底 |

> 这些都是**带安全默认的配置**,客户不必提前选,建档时按需调。

### sales_documents · 销项单据(新建)

| 列 | 类型 | 说明 |
|---|---|---|
| id | UUID PK | |
| tenant_id | UUID NOT NULL | RLS 键 |
| doc_type | TEXT | tax_invoice(ใบกำกับภาษี)/ receipt(ใบเสร็จ)/ quotation(报价) |
| doc_number | TEXT | **连号**(由 document_number_sequences 分配,见下)· (tenant_id, doc_type, doc_number) 唯一 |
| client_id | UUID | 买方 → 复用 `clients` |
| issue_date | DATE | 开票日 |
| status | TEXT | draft / issued / void / credited |
| currency | TEXT | 默认 THB |
| subtotal | NUMERIC(14,2) | 税前合计 |
| discount_total | NUMERIC(14,2) | 折扣 |
| vat_rate | NUMERIC(5,2) | 7.00 / 0 |
| vat_amount | NUMERIC(14,2) | 销项税额 |
| wht_amount | NUMERIC(14,2) | 预扣税(若适用) |
| grand_total | NUMERIC(14,2) | 应收 |
| issued_at | TIMESTAMPTZ NULL | 正式开出时间(开出后不可改) |
| created_by / created_at / updated_at | | |

**不可变约束**:`status='issued'` 后业务层禁止 UPDATE 金额/明细;更正只能开红冲单(见 03)。
是否 MVP 就强制取决于 Q3。

### sales_document_lines · 行项目(新建)

| 列 | 类型 | 说明 |
|---|---|---|
| id | UUID PK | |
| tenant_id | UUID NOT NULL | RLS 键 |
| document_id | UUID FK → sales_documents | |
| line_no | INT | 行序 |
| product_id | UUID NULL | 引用 products;现填时可为空 |
| description | TEXT | 行描述(冗余存,开票后留痕) |
| qty | NUMERIC(14,3) | 数量 |
| unit_price | NUMERIC(14,2) | 成交单价(冗余,防主数据改价回溯) |
| discount | NUMERIC(14,2) | 行折扣 |
| vat_applicable | BOOLEAN | |
| line_total | NUMERIC(14,2) | |

### document_number_sequences · 连号分配器(新建 · 合规关键 · 可配置+默认兜底)

**法律(泰国税法 §86/4):** 税票必须有**连续编号 + 不跳号/不重号**(用册的话加册号 เล่มที่)。
**格式(前缀/重置周期/位数)法律不管,公司自定** → 故做成**可配置 + 安全默认**,客户不必提前选(见 `docs/09`)。

| 列 | 类型 | 说明 |
|---|---|---|
| tenant_id | UUID | |
| doc_type | TEXT | tax_invoice / receipt / credit_note / debit_note |
| prefix | TEXT | 前缀(默认按 doc_type · 客户可改,如 INV) |
| reset_cadence | TEXT | `none`(一直累加·**默认·最安全**)/ `yearly` / `monthly` |
| period | TEXT | 重置桶:none→固定值;yearly→`2026`;monthly→`2026-06` |
| pad_width | INT | 补零位数(默认 5 → 00001) |
| book_no | TEXT NULL | 册号(用册才填) |
| next_number | BIGINT | 下一个号(可设起始值 · 接客户旧账本) |
| PK | (tenant_id, doc_type, prefix, period) | |

- **默认格式**:`<prefix>-<YYYY 或 none>-<NNNNN>`,默认 `reset_cadence=none`(一直累加,**永不跳号、永远合规**)。
- **可配**:前缀 / 重置周期 / 位数 / 册号 / **起始号(seed `next_number`,接旧纸质账本)**——客户有习惯才改,否则用默认。
- **法律红线(连续不跳)由取号逻辑保证**,与外观格式无关:**事务内 `SELECT ... FOR UPDATE` 取号再 +1**。
- 草稿(draft)**不占号**,只有正式 issue 才取号——避免作废草稿留号洞。

## 后续表(客户已答锁定 · 2026-06-05 · 见 docs/09)

| 表 | Phase | 说明 |
|---|---|---|
| credit_debit_notes | **Phase 1**(客户选最高合规) | 红冲单 ใบลดหนี้ / 补开 ใบเพิ่มหนี้,引用原单 · 自身也连号 |
| product_imports | **Phase 1**(Q4 = Excel 导入) | 导入批次 + 行校验结果 |
| inventory_*(stock_levels / stock_movements) | **Phase 2**(Q4 要库存 คลังสินค้า) | 库存量 + 出入库流水 · 开票/POS 扣减 |
| etax_submissions | **Phase 3**(Q3 "可行才做") | RD e-Tax Invoice & e-Receipt 上报记录 + 状态 + 电子证书 |
| pos_*(pos_sessions / cash_drawer) | **下一个独立项目 POS** | 收银开班/交班、现金抽屉 · 不在本模块 |

> products 预留库存衔接:Phase 1 不建 inventory 表,但 products 设计不阻碍 Phase 2 接 `stock_levels`(按 product_id+仓库)。

## RLS(每张新表都要)

```sql
ALTER TABLE <t> ENABLE ROW LEVEL SECURITY;
CREATE POLICY <t>_tenant_isolation ON <t>
  USING (tenant_id::text = current_setting('app.current_tenant_id', true));
```
配套索引:每张表至少 `(tenant_id, ...)` 前缀索引,热查询另补(对齐 b9 索引审计风格)。
