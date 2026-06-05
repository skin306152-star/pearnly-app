-- 0001_sales_core.sql · 销项模块核心 schema(草案)
--
-- 状态:草案。决策无关的核心表先建模;Phase-gated 表(红冲/e-Tax/库存/导入)
--       待客户拍板(docs/09)后另起迁移文件。
-- ⚠️ 迁回方式:主项目 schema 走 **Alembic**(alembic/versions/NNNN_sales_core.py · 见既有 0001-0005)。
--    本 .sql 仅为可读草案;落地时转写成 Alembic op.execute(...) 或 op.create_table(...),不新增 ensure_*。
--    热路径索引微调可单独走 scripts/sql/*.sql 手动 psql(见 b9)。
-- 约定:tenant_id UUID + RLS;钱 NUMERIC(14,2);时间 TIMESTAMPTZ(UTC);幂等 IF NOT EXISTS。
--
-- ⚠️ FK 类型坑:下文 client_id 用 UUID 仅占位。clients.id 既有为 INTEGER/BIGSERIAL ·
--    迁回前 `\d clients` 核实真实类型,client_id 必须与之一致(否则 FK 建不上)。
-- ⚠️ 其余迁回前 review:UUID 默认值方案、FK 级联策略、与现有 clients/categories 的外键。

-- ── products · 商品主数据 ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    code            TEXT,
    barcode         TEXT,            -- Phase 2(扫码)
    qr_payload      TEXT,            -- Phase 2(扫码)
    name_th         TEXT NOT NULL,
    name_en         TEXT,
    name_zh         TEXT,
    unit            TEXT,
    unit_price      NUMERIC(14,2) NOT NULL DEFAULT 0,
    vat_applicable  BOOLEAN NOT NULL DEFAULT TRUE,
    image_url       TEXT,            -- TBD:取决于 Q2(图库点选才必需)
    category_id     UUID,            -- 复用现有分类体系(迁回补 FK)
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_products_tenant_code
    ON products (tenant_id, code) WHERE code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_tenant ON products (tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products (tenant_id, barcode) WHERE barcode IS NOT NULL;

-- ── document_number_sequences · 连号分配器(合规关键)──────────────────
-- 泰国税票连号不跳:取号必须事务内 SELECT ... FOR UPDATE 再 +1。
-- 草稿不占号,只有正式 issue 时取号。
CREATE TABLE IF NOT EXISTS document_number_sequences (
    tenant_id    UUID NOT NULL,
    doc_type     TEXT NOT NULL,      -- tax_invoice / receipt / credit_note / debit_note
    prefix       TEXT NOT NULL,      -- 如 INV2026
    period       TEXT NOT NULL,      -- 期间桶:2026-06 或 2026(规则待客户确认)
    next_number  BIGINT NOT NULL DEFAULT 1,
    PRIMARY KEY (tenant_id, doc_type, prefix, period)
);

-- ── sales_documents · 销项单据 ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    doc_type        TEXT NOT NULL,           -- tax_invoice / receipt / quotation
    doc_number      TEXT,                    -- issue 时才分配(草稿为 NULL)
    client_id       UUID,                    -- 买方 → clients(迁回补 FK)
    issue_date      DATE,
    status          TEXT NOT NULL DEFAULT 'draft',  -- draft/issued/void/credited
    currency        TEXT NOT NULL DEFAULT 'THB',
    subtotal        NUMERIC(14,2) NOT NULL DEFAULT 0,
    discount_total  NUMERIC(14,2) NOT NULL DEFAULT 0,
    vat_rate        NUMERIC(5,2)  NOT NULL DEFAULT 7.00,
    vat_amount      NUMERIC(14,2) NOT NULL DEFAULT 0,
    wht_amount      NUMERIC(14,2) NOT NULL DEFAULT 0,
    grand_total     NUMERIC(14,2) NOT NULL DEFAULT 0,
    issued_at       TIMESTAMPTZ,             -- 开出时间;开出后金额/明细禁改(业务层)
    created_by      UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_sales_doc_number
    ON sales_documents (tenant_id, doc_type, doc_number) WHERE doc_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sales_docs_tenant_status
    ON sales_documents (tenant_id, status, issue_date DESC);
CREATE INDEX IF NOT EXISTS idx_sales_docs_client ON sales_documents (tenant_id, client_id);

-- ── sales_document_lines · 行项目 ──────────────────────────────────
CREATE TABLE IF NOT EXISTS sales_document_lines (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    document_id     UUID NOT NULL REFERENCES sales_documents(id) ON DELETE CASCADE,
    line_no         INT NOT NULL,
    product_id      UUID,                    -- 可空(现填行项目)
    description     TEXT NOT NULL,           -- 冗余存,开票后留痕
    qty             NUMERIC(14,3) NOT NULL DEFAULT 1,
    unit_price      NUMERIC(14,2) NOT NULL DEFAULT 0,  -- 冗余,防主数据改价回溯
    discount        NUMERIC(14,2) NOT NULL DEFAULT 0,
    vat_applicable  BOOLEAN NOT NULL DEFAULT TRUE,
    line_total      NUMERIC(14,2) NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sales_lines_doc ON sales_document_lines (document_id, line_no);
CREATE INDEX IF NOT EXISTS idx_sales_lines_tenant ON sales_document_lines (tenant_id);

-- ── RLS(每张表)──────────────────────────────────────────────────
-- policy 与主仓库一致:tenant_id::text = current_setting('app.current_tenant_id', true)
DO $$
DECLARE t TEXT;
BEGIN
  FOREACH t IN ARRAY ARRAY['products','document_number_sequences','sales_documents','sales_document_lines']
  LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY;', t);
    EXECUTE format(
      'CREATE POLICY %I ON %I USING (tenant_id::text = current_setting(''app.current_tenant_id'', true));',
      t || '_tenant_isolation', t
    );
  END LOOP;
EXCEPTION WHEN duplicate_object THEN
  -- policy 已存在 · 幂等忽略
  NULL;
END $$;
