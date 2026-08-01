-- 遗留表建表 DDL · 迁移 001a_legacy_tables 的载荷
--
-- 这 26 张表在 2026-08-01 之前全仓没有任何建表语句:迁移史里只有 ALTER,
-- services/ 里只有读写没有 CREATE,唯一的 DDL 抄本在 tests/integration 的测试桩里。
-- 空库因此建不出它们(真库测试一碰就炸),生产结构靠"谁的开发库还活着"传承。
--
-- 内容逐字来自 docs/db/prod-schema.sql(scripts/dump_prod_schema.py 的只读快照),
-- 只做两处机械变换,tests/unit/test_legacy_baseline_migration.py 逐条守着:
--   1. "id" bigint DEFAULT nextval('<表>_id_seq'::regclass) -> "id" bigserial
--      (快照不导 CREATE SEQUENCE;序列名全部符合 serial 默认命名,故等价还原)
--   2. CREATE INDEX -> CREATE INDEX IF NOT EXISTS(整份 DDL 幂等)
--
-- 三类东西按规则排除,不是漏抄:
--   - 与表内 CONSTRAINT 同名的索引 —— 唯一约束自带索引,再建一次会撞名;
--   - 已由后续迁移建的索引(uq_users_username_lower / idx_ocr_history_workspace /
--     ix_erp_push_logs_tenant_wo)—— 一个对象只能有一个迁移当主人;
--   - 外键 —— 快照把 FK 统一列在末尾且跨全部 175 张表,补 FK 的前提是所有表都进了
--     迁移史,不在本轮范围。

CREATE TABLE IF NOT EXISTS "api_keys" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "key_prefix" text NOT NULL,
  "key_hash" text NOT NULL,
  "name" text NOT NULL,
  "is_active" boolean DEFAULT true,
  "last_used_at" timestamp with time zone,
  "usage_count" bigint DEFAULT 0,
  "created_at" timestamp with time zone DEFAULT now(),
  "expires_at" timestamp with time zone,
  "tenant_id" uuid,
  CONSTRAINT "api_keys_pkey" PRIMARY KEY (id),
  CONSTRAINT "api_keys_key_hash_key" UNIQUE (key_hash)
);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON public.api_keys USING btree (key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant_id ON public.api_keys USING btree (tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON public.api_keys USING btree (user_id);

CREATE TABLE IF NOT EXISTS "automation_rules" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "name" text NOT NULL,
  "rule_type" text NOT NULL,
  "config" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "is_active" boolean DEFAULT true,
  "last_run_at" timestamp with time zone,
  "last_run_status" text,
  "created_at" timestamp with time zone DEFAULT now(),
  "updated_at" timestamp with time zone DEFAULT now(),
  "tenant_id" uuid,
  CONSTRAINT "automation_rules_pkey" PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_automation_rules_tenant_id ON public.automation_rules USING btree (tenant_id);
CREATE INDEX IF NOT EXISTS idx_automation_rules_user_id ON public.automation_rules USING btree (user_id);

CREATE TABLE IF NOT EXISTS "bank_reconcile_candidates" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tx_id" uuid NOT NULL,
  "history_id" uuid NOT NULL,
  "score" numeric(5,2) NOT NULL,
  "reason" text,
  "is_auto_picked" boolean DEFAULT false NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "tenant_id" uuid,
  CONSTRAINT "bank_reconcile_candidates_pkey" PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_bank_recon_cand_tx ON public.bank_reconcile_candidates USING btree (tx_id, score DESC);
CREATE INDEX IF NOT EXISTS idx_bank_reconcile_candidates_tenant_id ON public.bank_reconcile_candidates USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "bank_reconcile_sessions" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "bank_code" text NOT NULL,
  "account_last4" text,
  "statement_month" date,
  "period_start" date,
  "period_end" date,
  "opening_balance" numeric(18,2),
  "closing_balance" numeric(18,2),
  "total_inflow" numeric(18,2) DEFAULT 0,
  "total_outflow" numeric(18,2) DEFAULT 0,
  "parse_status" text DEFAULT 'pending'::text NOT NULL,
  "parse_error" text,
  "match_status" text DEFAULT 'pending'::text NOT NULL,
  "tx_count" integer DEFAULT 0 NOT NULL,
  "matched_count" integer DEFAULT 0 NOT NULL,
  "unmatched_count" integer DEFAULT 0 NOT NULL,
  "source_filename" text,
  "source_pages" integer,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "tenant_id" uuid,
  "client_id" integer,
  "workspace_client_id" bigint,
  CONSTRAINT "bank_reconcile_sessions_pkey" PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_bank_recon_sessions_client ON public.bank_reconcile_sessions USING btree (client_id);
CREATE INDEX IF NOT EXISTS idx_bank_recon_sessions_user ON public.bank_reconcile_sessions USING btree (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bank_reconcile_sessions_tenant_id ON public.bank_reconcile_sessions USING btree (tenant_id);
CREATE INDEX IF NOT EXISTS ix_bank_reconcile_sessions_ws ON public.bank_reconcile_sessions USING btree (tenant_id, workspace_client_id);

CREATE TABLE IF NOT EXISTS "bank_reconcile_transactions" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "session_id" uuid NOT NULL,
  "user_id" uuid NOT NULL,
  "row_no" integer,
  "tx_date" date,
  "value_date" date,
  "direction" text NOT NULL,
  "amount" numeric(18,2) NOT NULL,
  "balance_after" numeric(18,2),
  "description" text,
  "counterparty" text,
  "ref_no" text,
  "channel" text,
  "match_status" text DEFAULT 'unmatched'::text NOT NULL,
  "matched_history_id" uuid,
  "match_score" numeric(5,2),
  "match_reason" text,
  "match_reviewed_by" uuid,
  "match_reviewed_at" timestamp with time zone,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "tenant_id" uuid,
  CONSTRAINT "bank_reconcile_transactions_pkey" PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_bank_recon_tx_match_lookup ON public.bank_reconcile_transactions USING btree (user_id, amount, tx_date) WHERE (match_status = 'unmatched'::text);
CREATE INDEX IF NOT EXISTS idx_bank_recon_tx_match_status ON public.bank_reconcile_transactions USING btree (session_id, match_status);
CREATE INDEX IF NOT EXISTS idx_bank_recon_tx_session ON public.bank_reconcile_transactions USING btree (session_id, row_no);
CREATE INDEX IF NOT EXISTS idx_bank_recon_tx_user_date ON public.bank_reconcile_transactions USING btree (user_id, tx_date DESC);
CREATE INDEX IF NOT EXISTS idx_bank_reconcile_transactions_tenant_id ON public.bank_reconcile_transactions USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "email_ingest_accounts" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "email_address" text NOT NULL,
  "imap_host" text NOT NULL,
  "imap_port" integer DEFAULT 993 NOT NULL,
  "imap_use_ssl" boolean DEFAULT true NOT NULL,
  "password_enc" bytea NOT NULL,
  "folder" text DEFAULT 'INBOX'::text NOT NULL,
  "filter_subject" text,
  "filter_sender" text,
  "mark_as_read" boolean DEFAULT true NOT NULL,
  "enabled" boolean DEFAULT true NOT NULL,
  "last_check_at" timestamp with time zone,
  "last_error" text,
  "success_count" integer DEFAULT 0 NOT NULL,
  "failure_count" integer DEFAULT 0 NOT NULL,
  "last_fetched_at" timestamp with time zone,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "interval_min" integer DEFAULT 15 NOT NULL,
  "tenant_id" uuid,
  CONSTRAINT "email_ingest_interval_check" CHECK ((interval_min = ANY (ARRAY[5, 15, 60]))),
  CONSTRAINT "email_ingest_accounts_pkey" PRIMARY KEY (id),
  CONSTRAINT "email_ingest_accounts_user_id_key" UNIQUE (user_id)
);
CREATE INDEX IF NOT EXISTS idx_email_ingest_accounts_enabled ON public.email_ingest_accounts USING btree (enabled) WHERE (enabled = true);
CREATE INDEX IF NOT EXISTS idx_email_ingest_accounts_tenant_id ON public.email_ingest_accounts USING btree (tenant_id);
CREATE INDEX IF NOT EXISTS idx_email_ingest_accounts_user ON public.email_ingest_accounts USING btree (user_id);

CREATE TABLE IF NOT EXISTS "email_ingest_logs" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "account_id" uuid NOT NULL,
  "user_id" uuid NOT NULL,
  "status" text NOT NULL,
  "emails_scanned" integer DEFAULT 0 NOT NULL,
  "attachments_found" integer DEFAULT 0 NOT NULL,
  "ocr_succeeded" integer DEFAULT 0 NOT NULL,
  "ocr_failed" integer DEFAULT 0 NOT NULL,
  "elapsed_ms" integer,
  "error_message" text,
  "error_details" jsonb,
  "trigger" text DEFAULT 'auto'::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "tenant_id" uuid,
  CONSTRAINT "email_ingest_logs_pkey" PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_email_ingest_logs_account_time ON public.email_ingest_logs USING btree (account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_ingest_logs_tenant_id ON public.email_ingest_logs USING btree (tenant_id);
CREATE INDEX IF NOT EXISTS idx_email_ingest_logs_user_time ON public.email_ingest_logs USING btree (user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS "email_ingest_seen_uids" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "account_id" uuid NOT NULL,
  "uid" text NOT NULL,
  "history_id" uuid,
  "subject" text,
  "sender" text,
  "fetched_at" timestamp with time zone DEFAULT now() NOT NULL,
  "tenant_id" uuid,
  CONSTRAINT "email_ingest_seen_uids_pkey" PRIMARY KEY (id),
  CONSTRAINT "email_ingest_seen_uids_account_id_uid_key" UNIQUE (account_id, uid)
);
CREATE INDEX IF NOT EXISTS idx_email_ingest_seen_account ON public.email_ingest_seen_uids USING btree (account_id, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_ingest_seen_uids_tenant_id ON public.email_ingest_seen_uids USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "erp_endpoints" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "name" text NOT NULL,
  "adapter" text NOT NULL,
  "config" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "is_default" boolean DEFAULT false NOT NULL,
  "auto_push" boolean DEFAULT false NOT NULL,
  "enabled" boolean DEFAULT true NOT NULL,
  "last_used_at" timestamp with time zone,
  "last_status" text,
  "success_count" integer DEFAULT 0 NOT NULL,
  "failure_count" integer DEFAULT 0 NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "tenant_id" uuid,
  CONSTRAINT "erp_endpoints_adapter_chk" CHECK ((adapter = ANY (ARRAY['webhook'::text, 'xero'::text, 'flowaccount'::text, 'mrerp'::text, 'mrerp_dms'::text, 'express'::text]))),
  CONSTRAINT "erp_endpoints_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_erp_endpoints_one_default_per_user ON public.erp_endpoints USING btree (user_id) WHERE (is_default = true);
CREATE INDEX IF NOT EXISTS idx_erp_endpoints_tenant_id ON public.erp_endpoints USING btree (tenant_id);
CREATE INDEX IF NOT EXISTS idx_erp_endpoints_user ON public.erp_endpoints USING btree (user_id, enabled, is_default DESC);
CREATE UNIQUE INDEX IF NOT EXISTS uq_erp_endpoints_user_express ON public.erp_endpoints USING btree (user_id) WHERE (adapter = 'express'::text);

CREATE TABLE IF NOT EXISTS "erp_oauth_states" (
  "state" text NOT NULL,
  "tenant_id" uuid NOT NULL,
  "user_id" uuid NOT NULL,
  "erp_type" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "erp_oauth_states_pkey" PRIMARY KEY (state)
);
CREATE INDEX IF NOT EXISTS idx_oauth_states_created ON public.erp_oauth_states USING btree (created_at);

CREATE TABLE IF NOT EXISTS "erp_oauth_tokens" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "erp_type" text NOT NULL,
  "organisation_id" text NOT NULL,
  "organisation_name" text,
  "access_token" text NOT NULL,
  "refresh_token" text NOT NULL,
  "expires_at" timestamp with time zone NOT NULL,
  "scope" text,
  "is_default" boolean DEFAULT false NOT NULL,
  "token_version" integer DEFAULT 1 NOT NULL,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "auto_push" boolean DEFAULT false NOT NULL,
  CONSTRAINT "erp_oauth_tokens_pkey" PRIMARY KEY (id),
  CONSTRAINT "erp_oauth_tokens_tenant_id_erp_type_organisation_id_key" UNIQUE (tenant_id, erp_type, organisation_id)
);
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_default ON public.erp_oauth_tokens USING btree (is_default) WHERE (is_default = true);
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_tenant ON public.erp_oauth_tokens USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "erp_push_logs" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "endpoint_id" uuid,
  "history_id" uuid,
  "invoice_no" text,
  "seller_name" text,
  "total_amount" numeric(18,2),
  "status" text NOT NULL,
  "http_status" integer,
  "request_body" jsonb,
  "response_body" text,
  "error_msg" text,
  "attempt" integer DEFAULT 1 NOT NULL,
  "elapsed_ms" integer,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "trigger" text DEFAULT 'manual'::text NOT NULL,
  "tenant_id" uuid,
  "retry_count" integer DEFAULT 0 NOT NULL,
  "max_retries" integer DEFAULT 3 NOT NULL,
  "next_retry_at" timestamp with time zone,
  "lease_owner" text,
  "lease_expires_at" timestamp with time zone,
  "work_order_id" uuid,
  CONSTRAINT "erp_push_logs_status_chk" CHECK ((status = ANY (ARRAY['success'::text, 'failed'::text, 'skipped_dup'::text, 'pending'::text, 'retrying'::text, 'manual'::text]))),
  CONSTRAINT "erp_push_logs_pkey" PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_erp_logs_pending_lease ON public.erp_push_logs USING btree (endpoint_id, status) WHERE (status = 'pending'::text);
CREATE INDEX IF NOT EXISTS idx_erp_logs_retry_due ON public.erp_push_logs USING btree (next_retry_at) WHERE ((next_retry_at IS NOT NULL) AND (status = 'failed'::text));
CREATE INDEX IF NOT EXISTS idx_erp_push_logs_dedup ON public.erp_push_logs USING btree (history_id, endpoint_id);
CREATE INDEX IF NOT EXISTS idx_erp_push_logs_tenant_id ON public.erp_push_logs USING btree (tenant_id);
CREATE INDEX IF NOT EXISTS idx_erp_push_logs_user_created ON public.erp_push_logs USING btree (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_push_logs_endpoint ON public.erp_push_logs USING btree (endpoint_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_push_logs_history ON public.erp_push_logs USING btree (history_id);
CREATE INDEX IF NOT EXISTS idx_push_logs_user ON public.erp_push_logs USING btree (user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS "excel_templates" (
  "id" bigserial NOT NULL,
  "owner_id" uuid,
  "name" text NOT NULL,
  "description" text,
  "config_json" jsonb NOT NULL,
  "is_default" boolean DEFAULT false NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "tenant_id" uuid,
  CONSTRAINT "excel_templates_pkey" PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_excel_templates_tenant_id ON public.excel_templates USING btree (tenant_id);
CREATE INDEX IF NOT EXISTS idx_tpl_owner ON public.excel_templates USING btree (owner_id);

CREATE TABLE IF NOT EXISTS "expense_draft" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "source" text DEFAULT 'line_text'::text NOT NULL,
  "status" text DEFAULT 'draft'::text NOT NULL,
  "line_user_id" text,
  "raw_text" text,
  "document_type" text DEFAULT ''::text NOT NULL,
  "amount" numeric(14,2),
  "qty" numeric(14,3),
  "unit_price" numeric(14,2),
  "currency" text DEFAULT 'THB'::text NOT NULL,
  "expense_type" text DEFAULT ''::text NOT NULL,
  "category" text DEFAULT ''::text NOT NULL,
  "subcategory" text DEFAULT ''::text NOT NULL,
  "vendor_name" text DEFAULT ''::text NOT NULL,
  "vendor_tax_id" text DEFAULT ''::text NOT NULL,
  "invoice_number" text DEFAULT ''::text NOT NULL,
  "doc_date" date,
  "vat_mode" text DEFAULT 'included'::text NOT NULL,
  "vat_amount" numeric(14,2),
  "wht_amount" numeric(14,2),
  "note" text DEFAULT ''::text NOT NULL,
  "confidence" numeric(5,2) DEFAULT 0 NOT NULL,
  "created_by" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "category_id" uuid,
  "subcategory_id" uuid,
  CONSTRAINT "expense_draft_pkey" PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS ix_expense_draft_invoice_no ON public.expense_draft USING btree (tenant_id, workspace_client_id, invoice_number);
CREATE INDEX IF NOT EXISTS ix_expense_draft_ws_status ON public.expense_draft USING btree (tenant_id, workspace_client_id, status);

CREATE TABLE IF NOT EXISTS "ip_usage" (
  "ip_address" text NOT NULL,
  "usage_date" date DEFAULT CURRENT_DATE NOT NULL,
  "count" integer DEFAULT 0 NOT NULL,
  CONSTRAINT "ip_usage_pkey" PRIMARY KEY (ip_address, usage_date)
);
CREATE INDEX IF NOT EXISTS idx_ip_date ON public.ip_usage USING btree (usage_date DESC);

CREATE TABLE IF NOT EXISTS "line_binding_codes" (
  "code" text NOT NULL,
  "user_id" uuid NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "expires_at" timestamp with time zone NOT NULL,
  "used_at" timestamp with time zone,
  "tenant_id" uuid,
  CONSTRAINT "line_binding_codes_pkey" PRIMARY KEY (code)
);
CREATE INDEX IF NOT EXISTS idx_line_binding_codes_expires ON public.line_binding_codes USING btree (expires_at);
CREATE INDEX IF NOT EXISTS idx_line_binding_codes_tenant_id ON public.line_binding_codes USING btree (tenant_id);
CREATE INDEX IF NOT EXISTS idx_line_binding_codes_user ON public.line_binding_codes USING btree (user_id, used_at);

CREATE TABLE IF NOT EXISTS "line_bindings" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "line_user_id" text NOT NULL,
  "line_display_name" text,
  "line_picture_url" text,
  "bound_at" timestamp with time zone DEFAULT now() NOT NULL,
  "last_active_at" timestamp with time zone DEFAULT now() NOT NULL,
  "tenant_id" uuid,
  "current_workspace_client_id" bigint,
  "monthly_report_opt_out" boolean DEFAULT false NOT NULL,
  CONSTRAINT "line_bindings_pkey" PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_line_bindings_tenant_id ON public.line_bindings USING btree (tenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_line_bindings_line_user_id ON public.line_bindings USING btree (line_user_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_line_bindings_user_id ON public.line_bindings USING btree (user_id);

CREATE TABLE IF NOT EXISTS "mrerp_credentials" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "encrypted_username" text NOT NULL,
  "encrypted_password" text NOT NULL,
  "comidyear" integer DEFAULT 6 NOT NULL,
  "seldb" integer DEFAULT 1 NOT NULL,
  "company_label" text,
  "last_test_at" timestamp with time zone,
  "last_test_ok" boolean,
  "last_test_error" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "auto_push" boolean DEFAULT false NOT NULL,
  CONSTRAINT "mrerp_credentials_pkey" PRIMARY KEY (id),
  CONSTRAINT "mrerp_credentials_tenant_unique" UNIQUE (tenant_id)
);
CREATE INDEX IF NOT EXISTS idx_mrerp_credentials_tenant ON public.mrerp_credentials USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "ocr_history" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "filename" text NOT NULL,
  "page_count" integer DEFAULT 1 NOT NULL,
  "file_size_kb" integer,
  "pages" jsonb NOT NULL,
  "confidence" text,
  "elapsed_ms" integer,
  "invoice_no" text,
  "invoice_date" date,
  "seller_name" text,
  "total_amount" numeric(14,2),
  "fields_edited_at" timestamp with time zone,
  "edit_count" integer DEFAULT 0 NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "file_hash" text,
  "last_pushed_at" timestamp with time zone,
  "last_push_status" text,
  "archive_name" text,
  "category_tag" text,
  "archived_at" timestamp with time zone,
  "storage_path" text,
  "source_pdf_id" uuid,
  "source_page_indices" jsonb,
  "source_index" integer,
  "source_total" integer,
  "source" text DEFAULT 'manual'::text NOT NULL,
  "source_ref" text,
  "tenant_id" uuid,
  "client_id" bigint,
  "pdf_storage_path" text,
  "pdf_size_bytes" integer,
  "smart_assigned_flag" boolean DEFAULT false,
  "field_overrides" jsonb,
  "workspace_client_id" bigint,
  "ai_raw" jsonb,
  "seller_name_official" text,
  "seller_name_verified" boolean DEFAULT false NOT NULL,
  "staged" boolean DEFAULT false NOT NULL,
  "posting_kind" text,
  CONSTRAINT "ocr_history_pkey" PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_ocr_history_archive ON public.ocr_history USING btree (user_id, archived_at DESC) WHERE (archive_name IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_ocr_history_client ON public.ocr_history USING btree (client_id) WHERE (client_id IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_ocr_history_hash ON public.ocr_history USING btree (user_id, file_hash, created_at DESC) WHERE (file_hash IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_ocr_history_invoice_no ON public.ocr_history USING btree (user_id, invoice_no) WHERE (invoice_no IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_ocr_history_pdf_storage ON public.ocr_history USING btree (pdf_storage_path) WHERE (pdf_storage_path IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_ocr_history_pushed ON public.ocr_history USING btree (user_id, last_push_status);
CREATE INDEX IF NOT EXISTS idx_ocr_history_seller ON public.ocr_history USING btree (user_id, seller_name) WHERE (seller_name IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_ocr_history_source ON public.ocr_history USING btree (user_id, source);
CREATE INDEX IF NOT EXISTS idx_ocr_history_source_pdf ON public.ocr_history USING btree (user_id, source_pdf_id) WHERE (source_pdf_id IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_ocr_history_storage ON public.ocr_history USING btree (user_id) WHERE (storage_path IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_ocr_history_tenant_id ON public.ocr_history USING btree (tenant_id);
CREATE INDEX IF NOT EXISTS idx_ocr_history_user_created ON public.ocr_history USING btree (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ocr_history_user_invno ON public.ocr_history USING btree (user_id, lower(invoice_no)) WHERE ((invoice_no IS NOT NULL) AND (invoice_no <> ''::text));
CREATE INDEX IF NOT EXISTS idx_ocr_history_user_signature ON public.ocr_history USING btree (user_id, invoice_date, total_amount) WHERE ((invoice_date IS NOT NULL) AND (total_amount IS NOT NULL));

CREATE TABLE IF NOT EXISTS "operation_logs" (
  "id" bigserial NOT NULL,
  "tenant_id" uuid,
  "actor_user_id" uuid,
  "actor_username" character varying(100),
  "actor_is_super" boolean DEFAULT false,
  "action" character varying(50) NOT NULL,
  "target_type" character varying(30),
  "target_id" character varying(100),
  "target_name" character varying(200),
  "details" jsonb,
  "ip" character varying(50),
  "ua" character varying(300),
  "created_at" timestamp with time zone DEFAULT now(),
  CONSTRAINT "operation_logs_pkey" PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_opl_action ON public.operation_logs USING btree (action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_opl_actor ON public.operation_logs USING btree (actor_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_opl_tenant ON public.operation_logs USING btree (tenant_id, created_at DESC);

CREATE TABLE IF NOT EXISTS "rd_cache" (
  "tax_id" text NOT NULL,
  "branch_no" integer DEFAULT 0 NOT NULL,
  "service" text NOT NULL,
  "payload" jsonb NOT NULL,
  "is_success" boolean DEFAULT true NOT NULL,
  "error_msg" text,
  "cached_at" timestamp with time zone DEFAULT now() NOT NULL,
  "expires_at" timestamp with time zone DEFAULT (now() + '7 days'::interval) NOT NULL,
  CONSTRAINT "rd_cache_pkey" PRIMARY KEY (tax_id, branch_no, service)
);
CREATE INDEX IF NOT EXISTS idx_rd_cache_expires ON public.rd_cache USING btree (expires_at);

CREATE TABLE IF NOT EXISTS "rd_daily_usage" (
  "user_id" uuid NOT NULL,
  "day" date NOT NULL,
  "count" integer DEFAULT 0 NOT NULL,
  "tenant_id" uuid,
  CONSTRAINT "rd_daily_usage_pkey" PRIMARY KEY (user_id, day)
);
CREATE INDEX IF NOT EXISTS idx_rd_daily_usage_day ON public.rd_daily_usage USING btree (day);
CREATE INDEX IF NOT EXISTS idx_rd_daily_usage_tenant_id ON public.rd_daily_usage USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "supplier_client_mapping" (
  "id" bigserial NOT NULL,
  "tenant_id" uuid NOT NULL,
  "supplier_name" text DEFAULT ''::text NOT NULL,
  "supplier_tax_id" text,
  "client_id" bigint NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "supplier_client_mapping_pkey" PRIMARY KEY (id),
  CONSTRAINT "supplier_client_mapping_tenant_id_supplier_name_key" UNIQUE (tenant_id, supplier_name)
);
CREATE INDEX IF NOT EXISTS idx_scm_tenant_tax ON public.supplier_client_mapping USING btree (tenant_id, supplier_tax_id) WHERE (supplier_tax_id IS NOT NULL);

CREATE TABLE IF NOT EXISTS "tenants" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "name" text NOT NULL,
  "display_name" text,
  "owner_user_id" uuid,
  "parent_tenant_id" uuid,
  "tenant_type" text DEFAULT 'shared_api'::text NOT NULL,
  "monthly_quota" integer DEFAULT 0,
  "used_this_month" integer DEFAULT 0 NOT NULL,
  "quota_reset_at" date DEFAULT CURRENT_DATE NOT NULL,
  "quota_alert_sent" boolean DEFAULT false NOT NULL,
  "gemini_api_key_encrypted" text,
  "status" text DEFAULT 'active'::text NOT NULL,
  "subscription_started_at" timestamp with time zone,
  "subscription_expires_at" timestamp with time zone,
  "last_active_at" timestamp with time zone,
  "member_count" integer DEFAULT 0 NOT NULL,
  "notes" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "tenant_type_v2" text DEFAULT 'firm'::text,
  CONSTRAINT "tenants_pkey" PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS idx_tenants_owner ON public.tenants USING btree (owner_user_id);
CREATE INDEX IF NOT EXISTS idx_tenants_parent ON public.tenants USING btree (parent_tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON public.tenants USING btree (status);

CREATE TABLE IF NOT EXISTS "user_settings" (
  "user_id" uuid NOT NULL,
  "erp_endpoint" text,
  "erp_auth_token" text,
  "erp_vendor" text,
  "email_inbox" text,
  "email_credentials" jsonb,
  "notification_line_id" text,
  "notification_email" text,
  "settings_json" jsonb DEFAULT '{}'::jsonb,
  "updated_at" timestamp with time zone DEFAULT now(),
  "tenant_id" uuid,
  CONSTRAINT "user_settings_pkey" PRIMARY KEY (user_id)
);
CREATE INDEX IF NOT EXISTS idx_user_settings_tenant_id ON public.user_settings USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "users" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "username" text NOT NULL,
  "password_hash" text NOT NULL,
  "email" text,
  "plan" text DEFAULT 'free'::text NOT NULL,
  "monthly_quota" integer DEFAULT 0,
  "used_this_month" integer DEFAULT 0 NOT NULL,
  "quota_reset_at" date DEFAULT CURRENT_DATE NOT NULL,
  "user_api_key_encrypted" text,
  "can_use_custom_template" boolean DEFAULT false NOT NULL,
  "can_view_history" boolean DEFAULT false NOT NULL,
  "can_use_typhoon" boolean DEFAULT false NOT NULL,
  "is_active" boolean DEFAULT true NOT NULL,
  "expires_at" timestamp with time zone,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "last_login_at" timestamp with time zone,
  "notes" text,
  "can_edit_fields" boolean DEFAULT false,
  "can_verify_tax" boolean DEFAULT false,
  "can_use_gemini" boolean DEFAULT false,
  "can_push_erp" boolean DEFAULT false,
  "can_use_automation" boolean DEFAULT false,
  "can_manage_api_keys" boolean DEFAULT false,
  "typhoon_quota_monthly" integer DEFAULT 0,
  "typhoon_used_this_month" integer DEFAULT 0,
  "history_retention_days" integer DEFAULT 0,
  "custom_template_limit" integer DEFAULT 0,
  "custom_gemini_api_key" text,
  "last_usage_month" date,
  "dup_check_enabled" boolean DEFAULT true,
  "gemini_api_key" text,
  "trial_uploads_count" integer DEFAULT 0,
  "subscription_expires_at" timestamp with time zone,
  "typhoon_last_reset_month" text,
  "preferred_lang" text DEFAULT 'zh'::text,
  "tenant_id" uuid,
  "role" text DEFAULT 'owner'::text,
  "is_super_admin" boolean DEFAULT false NOT NULL,
  "invited_by" uuid,
  "company_name" character varying(200),
  "email_normalized" text,
  "signup_ip" text,
  "signup_ip_subnet" text,
  "signup_fingerprint" text,
  "signup_user_agent" text,
  "line_user_id" text,
  "signup_source" text,
  "full_name" text,
  "user_role" text,
  "monthly_volume" text,
  "phone" text,
  "newsletter_opt_in" boolean DEFAULT true,
  "trial_expires_at" timestamp with time zone,
  "plan_expires_at" timestamp with time zone,
  "signup_country" text,
  "line_id" text,
  "line_verified_at" timestamp with time zone,
  "risk_score" integer DEFAULT 0,
  "is_banned" boolean DEFAULT false,
  "ban_reason" text,
  "last_seen_at" timestamp with time zone,
  "upgraded_at" timestamp with time zone,
  "parent_user_id" uuid,
  "country" character varying(8),
  "google_sub" text,
  "avatar_url" text,
  "line_uid" text,
  "password_changed_at" timestamp with time zone DEFAULT now(),
  "active_jti" text,
  "is_billing_exempt" boolean DEFAULT false NOT NULL,
  "must_change_password" boolean DEFAULT false NOT NULL,
  "active_tenant_id" uuid,
  "vb_last_seen_version" character varying(64),
  "erp_push_mode" text DEFAULT 'smart'::text,
  CONSTRAINT "users_preferred_lang_check" CHECK ((preferred_lang = ANY (ARRAY['zh'::text, 'en'::text, 'th'::text, 'ja'::text]))),
  CONSTRAINT "users_pkey" PRIMARY KEY (id),
  CONSTRAINT "users_username_key" UNIQUE (username)
);
CREATE INDEX IF NOT EXISTS idx_users_email_norm ON public.users USING btree (email_normalized);
CREATE INDEX IF NOT EXISTS idx_users_fingerprint ON public.users USING btree (signup_fingerprint, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_google_sub ON public.users USING btree (google_sub) WHERE (google_sub IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_users_line_uid ON public.users USING btree (line_uid) WHERE (line_uid IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_users_line_user_id ON public.users USING btree (line_user_id);
CREATE INDEX IF NOT EXISTS idx_users_plan ON public.users USING btree (plan);
CREATE INDEX IF NOT EXISTS idx_users_signup_ip ON public.users USING btree (signup_ip, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_signup_source ON public.users USING btree (signup_source, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_signup_subnet ON public.users USING btree (signup_ip_subnet, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON public.users USING btree (tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON public.users USING btree (username);
