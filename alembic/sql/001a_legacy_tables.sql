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
--     ix_erp_push_logs_tenant_wo / uq_erp_endpoints_shared_express_workspace)
--     —— 一个对象只能有一个迁移当主人;
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
  "user_id" uuid,
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
  "workspace_client_id" bigint,
  "shared_scope" boolean DEFAULT false NOT NULL,
  "bound_account_set" text,
  "bound_profile_key" text,
  "live_account_set" text,
  "live_profile_key" text,
  "agent_last_seen_at" timestamp with time zone,
  "agent_version" text,
  "binding_generation" bigint DEFAULT 0 NOT NULL,
  CONSTRAINT "erp_endpoints_adapter_chk" CHECK ((adapter = ANY (ARRAY['webhook'::text, 'xero'::text, 'flowaccount'::text, 'mrerp'::text, 'mrerp_dms'::text, 'express'::text]))),
  CONSTRAINT "erp_endpoints_binding_generation_chk" CHECK ((binding_generation >= 0)),
  CONSTRAINT "erp_endpoints_bound_profile_pair_chk" CHECK (((bound_account_set IS NULL) = (bound_profile_key IS NULL))),
  CONSTRAINT "erp_endpoints_legacy_creator_chk" CHECK (((binding_generation > 0) OR (user_id IS NOT NULL))),
  CONSTRAINT "erp_endpoints_live_profile_pair_chk" CHECK (((live_account_set IS NULL) = (live_profile_key IS NULL))),
  CONSTRAINT "erp_endpoints_managed_scope_chk" CHECK (((binding_generation = 0) OR ((tenant_id IS NOT NULL) AND (workspace_client_id IS NOT NULL) AND (adapter = 'express'::text)))),
  CONSTRAINT "erp_endpoints_shared_generation_chk" CHECK ((NOT shared_scope OR binding_generation > 0)),
  CONSTRAINT "erp_endpoints_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_erp_endpoints_one_default_per_user ON public.erp_endpoints USING btree (user_id) WHERE (is_default = true);
CREATE INDEX IF NOT EXISTS idx_erp_endpoints_tenant_id ON public.erp_endpoints USING btree (tenant_id);
CREATE INDEX IF NOT EXISTS idx_erp_endpoints_user ON public.erp_endpoints USING btree (user_id, enabled, is_default DESC);
CREATE UNIQUE INDEX IF NOT EXISTS uq_erp_endpoints_user_express ON public.erp_endpoints USING btree (user_id) WHERE ((adapter = 'express'::text) AND (binding_generation = 0));

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
  "workspace_client_id" bigint,
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

DO $pearnly$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'erp_endpoints'::regclass
      AND conname = 'erp_endpoints_user_id_fkey'
  ) THEN
    ALTER TABLE erp_endpoints
      ADD CONSTRAINT erp_endpoints_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'erp_endpoints'::regclass
      AND conname = 'erp_endpoints_tenant_id_fkey'
  ) THEN
    ALTER TABLE erp_endpoints
      ADD CONSTRAINT erp_endpoints_tenant_id_fkey
      FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
  END IF;
END
$pearnly$;


-- F1-B3B2b promotion guard. The policy is installed by 0111 after
-- workspace_clients, memberships, and roles exist; this row guard is safe in
-- the legacy baseline and protects direct SQL during the later upgrade.
CREATE OR REPLACE FUNCTION public.erp_endpoint_has_legacy_activity(p_endpoint_id uuid)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog
AS $pearnly$
  SELECT EXISTS (
    SELECT 1
    FROM public.erp_endpoints endpoint
    WHERE endpoint.id = $1
      AND endpoint.binding_generation = 0
      AND endpoint.adapter = 'express'
      AND endpoint.user_id::text = pg_catalog.current_setting('app.current_user_id', true)
      AND (
        endpoint.tenant_id IS NULL
        OR endpoint.tenant_id::text = pg_catalog.current_setting('app.current_tenant_id', true)
      )
      AND EXISTS (
        SELECT 1
        FROM public.erp_push_logs push_log
        WHERE push_log.endpoint_id = endpoint.id
          AND (
            push_log.status IN ('pending', 'retrying')
            OR push_log.next_retry_at IS NOT NULL
            OR push_log.lease_owner IS NOT NULL
          )
      )
  );
$pearnly$;
REVOKE ALL ON FUNCTION public.erp_endpoint_has_legacy_activity(uuid) FROM PUBLIC;
DO $pearnly$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'pearnly_app') THEN
    EXECUTE 'GRANT EXECUTE ON FUNCTION public.erp_endpoint_has_legacy_activity(uuid) TO pearnly_app';
  END IF;
END
$pearnly$;

CREATE OR REPLACE FUNCTION public.guard_erp_endpoint_enrollment_columns()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $pearnly$
BEGIN
  IF OLD.binding_generation = 0 AND NEW.binding_generation = 1 THEN
    IF NEW.id IS DISTINCT FROM OLD.id
       OR NEW.user_id IS DISTINCT FROM OLD.user_id
       OR NEW.name IS DISTINCT FROM OLD.name
       OR NEW.adapter IS DISTINCT FROM OLD.adapter
       OR NEW.config IS DISTINCT FROM OLD.config
       OR NEW.is_default IS DISTINCT FROM OLD.is_default
       OR NEW.auto_push IS DISTINCT FROM OLD.auto_push
       OR NEW.enabled IS DISTINCT FROM OLD.enabled
       OR NEW.last_used_at IS DISTINCT FROM OLD.last_used_at
       OR NEW.last_status IS DISTINCT FROM OLD.last_status
       OR NEW.success_count IS DISTINCT FROM OLD.success_count
       OR NEW.failure_count IS DISTINCT FROM OLD.failure_count
       OR NEW.created_at IS DISTINCT FROM OLD.created_at
       OR NEW.bound_account_set IS DISTINCT FROM OLD.bound_account_set
       OR NEW.bound_profile_key IS DISTINCT FROM OLD.bound_profile_key
       OR NEW.live_account_set IS DISTINCT FROM OLD.live_account_set
       OR NEW.live_profile_key IS DISTINCT FROM OLD.live_profile_key
       OR NEW.agent_last_seen_at IS DISTINCT FROM OLD.agent_last_seen_at
       OR NEW.agent_version IS DISTINCT FROM OLD.agent_version
    THEN
      RAISE EXCEPTION 'ERP endpoint enrollment may only change binding columns';
    END IF;
  END IF;
  RETURN NEW;
END
$pearnly$;
REVOKE ALL ON FUNCTION public.guard_erp_endpoint_enrollment_columns() FROM PUBLIC;

DO $pearnly$
DECLARE
  v_enabled "char";
  v_tgtype SMALLINT;
  v_tgattr TEXT;
  v_has_when BOOLEAN;
  v_function OID;
BEGIN
    SELECT tgenabled, tgtype, tgattr::text, tgqual IS NOT NULL, tgfoid
    INTO v_enabled, v_tgtype, v_tgattr, v_has_when, v_function
    FROM pg_trigger
   WHERE tgrelid = 'erp_endpoints'::regclass
     AND tgname = 'erp_endpoints_enrollment_columns_guard'
     AND NOT tgisinternal;
  IF NOT FOUND THEN
    CREATE TRIGGER erp_endpoints_enrollment_columns_guard
    BEFORE UPDATE ON public.erp_endpoints
    FOR EACH ROW
    EXECUTE FUNCTION public.guard_erp_endpoint_enrollment_columns();
  ELSIF v_enabled IS DISTINCT FROM 'O'
     OR v_tgtype IS DISTINCT FROM 19
     OR v_tgattr IS DISTINCT FROM ''
     OR v_has_when
     OR v_function IS DISTINCT FROM 'public.guard_erp_endpoint_enrollment_columns()'::regprocedure
  THEN
    RAISE EXCEPTION
      'erp_endpoints_enrollment_columns_guard does not match the enrollment contract';
  END IF;
END
$pearnly$;

CREATE OR REPLACE FUNCTION public.purge_managed_erp_endpoints_for_users(p_user_ids uuid[])
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $pearnly$
DECLARE
  v_deleted bigint;
BEGIN
  IF p_user_ids IS NULL OR cardinality(p_user_ids) > 1000 THEN
    RAISE EXCEPTION 'managed endpoint cleanup requires at most 1000 user ids';
  END IF;
  DELETE FROM public.erp_endpoints
   WHERE user_id = ANY (p_user_ids) AND binding_generation > 0;
  GET DIAGNOSTICS v_deleted = ROW_COUNT;
  RETURN v_deleted;
END
$pearnly$;
REVOKE ALL ON FUNCTION public.purge_managed_erp_endpoints_for_users(uuid[]) FROM PUBLIC;

-- The enrollment policy depends on tables owned by later revisions. Keep the
-- archive replay-safe: 0111 installs it once those dependencies exist.
DO $pearnly$
BEGIN
  IF to_regclass('public.workspace_clients') IS NOT NULL
     AND to_regclass('public.memberships') IS NOT NULL
     AND to_regclass('public.roles') IS NOT NULL
  THEN
    EXECUTE 'ALTER TABLE erp_endpoints ENABLE ROW LEVEL SECURITY';
    EXECUTE 'DROP POLICY IF EXISTS erp_endpoints_shared_express_enroll ON erp_endpoints';
    EXECUTE $policy$
      CREATE POLICY erp_endpoints_shared_express_enroll ON erp_endpoints
      FOR UPDATE
      USING (
        binding_generation = 0 AND adapter = 'express'
        AND user_id::text = current_setting('app.current_user_id', true)
        AND (tenant_id IS NULL OR tenant_id::text = current_setting('app.current_tenant_id', true))
      )
      WITH CHECK (
        binding_generation = 1 AND adapter = 'express' AND shared_scope = TRUE
        AND user_id::text = current_setting('app.current_user_id', true)
        AND tenant_id::text = current_setting('app.current_tenant_id', true)
        AND workspace_client_id::text = current_setting('app.current_workspace_id', true)
        AND EXISTS (
          SELECT 1 FROM workspace_clients workspace
          WHERE workspace.id = erp_endpoints.workspace_client_id
            AND workspace.tenant_id::text = current_setting('app.current_tenant_id', true)
            AND workspace.is_active = TRUE
        )
        AND EXISTS (
          SELECT 1 FROM memberships membership
          JOIN roles role ON role.id = membership.role_id
          WHERE membership.user_id::text = current_setting('app.current_user_id', true)
            AND membership.tenant_id::text = current_setting('app.current_tenant_id', true)
            AND membership.status = 'active' AND role.name = 'owner'
        )
      )
    $policy$;
  END IF;
END
$pearnly$;

CREATE OR REPLACE FUNCTION public.prevent_managed_erp_endpoint_creator_change()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $pearnly$
BEGIN
  IF OLD.binding_generation > 0
     AND NEW.user_id IS DISTINCT FROM OLD.user_id
     AND pg_trigger_depth() = 1
  THEN
    RAISE EXCEPTION 'managed ERP endpoint creator is immutable';
  END IF;
  RETURN NEW;
END
$pearnly$;
REVOKE ALL ON FUNCTION public.prevent_managed_erp_endpoint_creator_change() FROM PUBLIC;

DO $pearnly$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger
    WHERE tgrelid = 'erp_endpoints'::regclass
      AND tgname = 'erp_endpoints_managed_creator_immutable'
      AND NOT tgisinternal
  ) THEN
    CREATE TRIGGER erp_endpoints_managed_creator_immutable
    BEFORE UPDATE OF user_id ON public.erp_endpoints
    FOR EACH ROW
    EXECUTE FUNCTION public.prevent_managed_erp_endpoint_creator_change();
  END IF;
END
$pearnly$;

CREATE OR REPLACE FUNCTION public.preserve_managed_erp_endpoints_on_user_delete()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $pearnly$
BEGIN
  EXECUTE format(
    'UPDATE %I.erp_endpoints SET user_id = NULL, updated_at = clock_timestamp() '
    'WHERE user_id = $1 AND binding_generation > 0',
    TG_TABLE_SCHEMA
  ) USING OLD.id;
  RETURN OLD;
END
$pearnly$;
REVOKE ALL ON FUNCTION public.preserve_managed_erp_endpoints_on_user_delete() FROM PUBLIC;

DO $pearnly$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger
    WHERE tgrelid = 'users'::regclass
      AND tgname = 'erp_endpoints_preserve_managed_creator_delete'
      AND NOT tgisinternal
  ) THEN
    CREATE TRIGGER erp_endpoints_preserve_managed_creator_delete
    BEFORE DELETE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION public.preserve_managed_erp_endpoints_on_user_delete();
  END IF;
END
$pearnly$;

-- B3B2b-2 lifecycle baseline archive.
-- B3B2b-2 lifecycle columns are additive in the legacy baseline.
ALTER TABLE erp_endpoints ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ;
ALTER TABLE erp_endpoints ADD COLUMN IF NOT EXISTS revoked_by UUID;

DO $pearnly$
BEGIN
  ALTER TABLE erp_endpoints DROP CONSTRAINT IF EXISTS erp_endpoints_managed_scope_chk;
  ALTER TABLE erp_endpoints ADD CONSTRAINT erp_endpoints_managed_scope_chk CHECK
    (binding_generation = 0 OR (tenant_id IS NOT NULL AND adapter = 'express'
      AND (workspace_client_id IS NOT NULL OR revoked_at IS NOT NULL)));
  ALTER TABLE erp_endpoints DROP CONSTRAINT IF EXISTS erp_endpoints_revoked_pair_chk;
  ALTER TABLE erp_endpoints ADD CONSTRAINT erp_endpoints_revoked_pair_chk CHECK
    ((revoked_at IS NULL) = (revoked_by IS NULL));
  ALTER TABLE erp_endpoints DROP CONSTRAINT IF EXISTS erp_endpoints_revoked_terminal_chk;
  ALTER TABLE erp_endpoints ADD CONSTRAINT erp_endpoints_revoked_terminal_chk CHECK
    (revoked_at IS NULL OR (binding_generation > 0 AND tenant_id IS NOT NULL
      AND adapter = 'express' AND enabled = FALSE AND shared_scope = FALSE
      AND workspace_client_id IS NULL));
END
$pearnly$;

DO $pearnly$
DECLARE v_unique boolean; v_keys smallint; v_definition text; v_predicate text; v_duplicate boolean;
BEGIN
  SELECT EXISTS (
      SELECT 1
        FROM operation_logs
       WHERE target_type = 'erp_endpoint'
         AND action IN ('erp.endpoint.rebind', 'erp.endpoint.enable', 'erp.endpoint.disable', 'erp.endpoint.revoke')
         AND details ? 'operation_id'
       GROUP BY tenant_id, (details ->> 'operation_id')
      HAVING count(*) > 1
  ) INTO v_duplicate;
  IF v_duplicate THEN
    RAISE EXCEPTION 'duplicate tenant operation_id prevents lifecycle index contract';
  END IF;
  SELECT index_meta.indisunique, index_meta.indnkeyatts, pg_get_indexdef(index_meta.indexrelid),
         pg_get_expr(index_meta.indpred, index_meta.indrelid)
    INTO v_unique, v_keys, v_definition, v_predicate
    FROM pg_catalog.pg_index index_meta
   WHERE index_meta.indexrelid = pg_catalog.to_regclass('uq_operation_logs_erp_endpoint_lifecycle_operation');
  IF NOT FOUND THEN
    CREATE UNIQUE INDEX uq_operation_logs_erp_endpoint_lifecycle_operation
      ON operation_logs (tenant_id, (details ->> 'operation_id'))
      WHERE target_type = 'erp_endpoint'
        AND action IN ('erp.endpoint.rebind', 'erp.endpoint.enable', 'erp.endpoint.disable', 'erp.endpoint.revoke')
        AND details ? 'operation_id';
  ELSIF v_unique IS DISTINCT FROM TRUE OR v_keys IS DISTINCT FROM 2
     OR position('tenant_id' IN lower(v_definition)) = 0
     OR position('details ->> ''operation_id''' IN lower(v_definition)) = 0
     OR v_predicate IS NULL OR position('target_type' IN lower(v_predicate)) = 0
     OR position('operation_id' IN lower(v_predicate)) = 0
     OR position('erp.endpoint.rebind' IN v_predicate) = 0
     OR position('erp.endpoint.enable' IN v_predicate) = 0
     OR position('erp.endpoint.disable' IN v_predicate) = 0
     OR position('erp.endpoint.revoke' IN v_predicate) = 0
  THEN
    RAISE EXCEPTION 'uq_operation_logs_erp_endpoint_lifecycle_operation does not match lifecycle contract';
  END IF;
END
$pearnly$;


CREATE OR REPLACE FUNCTION public.guard_erp_endpoint_lifecycle_columns()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $pearnly$
DECLARE
    v_action text := current_setting('app.erp_endpoint_lifecycle_action', true);
    v_expected text := current_setting('app.erp_endpoint_lifecycle_expected_generation', true);
    v_source text := current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true);
    v_target text := current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true);
    v_scrubbed jsonb;
BEGIN
    IF OLD.binding_generation = 0 THEN
        RETURN NEW;
    END IF;
    IF current_setting('app.erp_endpoint_lifecycle', true) <> 'on'
       OR current_setting('app.current_tenant_id', true) <> OLD.tenant_id::text
       OR current_setting('app.current_user_id', true) <> current_setting('app.erp_endpoint_lifecycle_actor_id', true)
       OR current_setting('app.erp_endpoint_lifecycle_endpoint_id', true) <> OLD.id::text
       OR current_setting('app.erp_endpoint_lifecycle_operation_id', true) !~
           '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
       OR v_expected !~ '^[1-9][0-9]*$'
       OR v_expected::bigint <> OLD.binding_generation
       OR v_source IS DISTINCT FROM COALESCE(OLD.workspace_client_id::text, '')
    THEN
        RAISE EXCEPTION 'erp.endpoint_lifecycle_gate_required';
    END IF;
    IF NEW.id IS DISTINCT FROM OLD.id
       OR NEW.user_id IS DISTINCT FROM OLD.user_id
       OR NEW.name IS DISTINCT FROM OLD.name
       OR NEW.adapter IS DISTINCT FROM OLD.adapter
       OR NEW.is_default IS DISTINCT FROM OLD.is_default
       OR NEW.auto_push IS DISTINCT FROM OLD.auto_push
       OR NEW.last_used_at IS DISTINCT FROM OLD.last_used_at
       OR NEW.last_status IS DISTINCT FROM OLD.last_status
       OR NEW.success_count IS DISTINCT FROM OLD.success_count
       OR NEW.failure_count IS DISTINCT FROM OLD.failure_count
       OR NEW.created_at IS DISTINCT FROM OLD.created_at
       OR NEW.bound_account_set IS DISTINCT FROM OLD.bound_account_set
       OR NEW.bound_profile_key IS DISTINCT FROM OLD.bound_profile_key
       OR NEW.live_account_set IS DISTINCT FROM OLD.live_account_set
       OR NEW.live_profile_key IS DISTINCT FROM OLD.live_profile_key
       OR NEW.agent_last_seen_at IS DISTINCT FROM OLD.agent_last_seen_at
       OR NEW.agent_version IS DISTINCT FROM OLD.agent_version
       OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
    THEN
        RAISE EXCEPTION 'erp endpoint lifecycle may only change lifecycle columns';
    END IF;
    IF NEW.binding_generation <> OLD.binding_generation + 1 THEN
        RAISE EXCEPTION 'erp.endpoint_stale_generation';
    END IF;
    IF v_action = 'rebind' THEN
        IF OLD.revoked_at IS NOT NULL OR OLD.enabled OR NOT OLD.shared_scope
           OR OLD.workspace_client_id IS NULL
           OR v_target IS NULL OR v_target = ''
           OR NEW.workspace_client_id::text IS DISTINCT FROM v_target
           OR NEW.enabled OR NOT NEW.shared_scope
           OR NEW.revoked_at IS NOT NULL OR NEW.revoked_by IS NOT NULL
           OR NEW.config IS DISTINCT FROM OLD.config
        THEN
            RAISE EXCEPTION 'erp.endpoint_invalid_rebind';
        END IF;
    ELSIF v_action = 'enable' THEN
        IF OLD.revoked_at IS NOT NULL OR OLD.enabled OR NOT OLD.shared_scope
           OR NEW.workspace_client_id IS DISTINCT FROM OLD.workspace_client_id
           OR NOT NEW.enabled OR NOT NEW.shared_scope
           OR NEW.revoked_at IS DISTINCT FROM OLD.revoked_at
           OR NEW.revoked_by IS DISTINCT FROM OLD.revoked_by
           OR NEW.config IS DISTINCT FROM OLD.config
           OR v_target IS DISTINCT FROM v_source
        THEN
            RAISE EXCEPTION 'erp.endpoint_invalid_enable';
        END IF;
    ELSIF v_action = 'disable' THEN
        IF OLD.revoked_at IS NOT NULL OR NOT OLD.enabled OR NOT OLD.shared_scope
           OR NEW.workspace_client_id IS DISTINCT FROM OLD.workspace_client_id
           OR NEW.enabled OR NOT NEW.shared_scope
           OR NEW.revoked_at IS DISTINCT FROM OLD.revoked_at
           OR NEW.revoked_by IS DISTINCT FROM OLD.revoked_by
           OR NEW.config IS DISTINCT FROM OLD.config
           OR v_target IS DISTINCT FROM v_source
        THEN
            RAISE EXCEPTION 'erp.endpoint_invalid_disable';
        END IF;
    ELSIF v_action = 'revoke' THEN
        IF OLD.revoked_at IS NOT NULL OR OLD.enabled OR NOT OLD.shared_scope
           OR NEW.workspace_client_id IS NOT NULL OR NEW.enabled OR NEW.shared_scope
           OR NEW.revoked_at IS NULL
           OR NEW.revoked_by::text IS DISTINCT FROM current_setting('app.erp_endpoint_lifecycle_actor_id', true)
           OR v_target IS DISTINCT FROM ''
        THEN
            RAISE EXCEPTION 'erp.endpoint_invalid_revoke';
        END IF;
        v_scrubbed := OLD.config - ARRAY[
            'agent_token', 'agent_token_hash', 'agent_token_tail', 'agent_token_created_at'
        ]::text[];
        IF NEW.config IS DISTINCT FROM v_scrubbed THEN
            RAISE EXCEPTION 'erp.endpoint_revoke_token_scrub_required';
        END IF;
    ELSE
        RAISE EXCEPTION 'erp.endpoint_lifecycle_action_required';
    END IF;
    RETURN NEW;
END
$pearnly$
;

REVOKE ALL ON FUNCTION public.guard_erp_endpoint_lifecycle_columns() FROM PUBLIC;

DO $pearnly$
DECLARE
    v_enabled "char";
    v_tgtype smallint;
    v_tgattr text;
    v_has_when boolean;
    v_function oid;
BEGIN
    SELECT trigger_meta.tgenabled, trigger_meta.tgtype, trigger_meta.tgattr::text,
           trigger_meta.tgqual IS NOT NULL, trigger_meta.tgfoid
      INTO v_enabled, v_tgtype, v_tgattr, v_has_when, v_function
      FROM pg_catalog.pg_trigger trigger_meta
     WHERE trigger_meta.tgrelid = 'erp_endpoints'::regclass
       AND trigger_meta.tgname = 'erp_endpoints_lifecycle_columns_guard'
       AND NOT trigger_meta.tgisinternal;
    IF NOT FOUND THEN
        CREATE TRIGGER erp_endpoints_lifecycle_columns_guard
        BEFORE UPDATE OF tenant_id, workspace_client_id, binding_generation, enabled,
            shared_scope, revoked_at, revoked_by, updated_at ON public.erp_endpoints
        FOR EACH ROW
        EXECUTE FUNCTION public.guard_erp_endpoint_lifecycle_columns();
    ELSIF v_enabled IS DISTINCT FROM 'O' OR v_tgtype IS DISTINCT FROM 19
       OR v_tgattr IS DISTINCT FROM (
           SELECT string_agg(attribute.attnum::text, ' ' ORDER BY array_position(
               ARRAY['tenant_id', 'workspace_client_id', 'binding_generation', 'enabled',
                     'shared_scope', 'revoked_at', 'revoked_by', 'updated_at'], attribute.attname
           ))
           FROM pg_catalog.pg_attribute attribute
           WHERE attribute.attrelid = 'erp_endpoints'::regclass
             AND attribute.attname = ANY (ARRAY[
                 'tenant_id', 'workspace_client_id', 'binding_generation', 'enabled',
                 'shared_scope', 'revoked_at', 'revoked_by', 'updated_at'
             ])
             AND attribute.attnum > 0 AND NOT attribute.attisdropped
       ) OR v_has_when
       OR v_function IS DISTINCT FROM 'public.guard_erp_endpoint_lifecycle_columns()'::regprocedure
    THEN
        RAISE EXCEPTION 'erp_endpoints_lifecycle_columns_guard does not match lifecycle contract';
    END IF;
END
$pearnly$
;


DO $pearnly$
BEGIN
  IF to_regclass('public.workspace_clients') IS NOT NULL
     AND to_regclass('public.memberships') IS NOT NULL
     AND to_regclass('public.roles') IS NOT NULL
  THEN
    EXECUTE $archive$

CREATE OR REPLACE FUNCTION public.erp_managed_endpoint_has_activity(p_endpoint_id uuid)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog
AS $helper$
    SELECT EXISTS (
        SELECT 1
        FROM public.erp_endpoints endpoint
        WHERE endpoint.id = $1
          AND endpoint.binding_generation > 0
          AND endpoint.adapter = 'express'
          AND endpoint.revoked_at IS NULL
          AND endpoint.tenant_id::text = pg_catalog.current_setting('app.current_tenant_id', true)
          AND endpoint.workspace_client_id IS NOT NULL
          AND EXISTS (
              SELECT 1
              FROM public.workspace_clients workspace
              WHERE workspace.id = endpoint.workspace_client_id
                AND workspace.tenant_id = endpoint.tenant_id
                AND workspace.is_active = TRUE
          )
          AND EXISTS (
              SELECT 1
              FROM public.users actor
              JOIN public.memberships membership ON membership.user_id = actor.id
              JOIN public.roles role ON role.id = membership.role_id
              WHERE actor.id::text = pg_catalog.current_setting('app.current_user_id', true)
                AND actor.tenant_id = endpoint.tenant_id
                AND actor.is_active = TRUE
                AND membership.tenant_id = endpoint.tenant_id
                AND membership.status = 'active'
                AND role.name = 'owner'
          )
          AND EXISTS (
              SELECT 1
              FROM public.erp_push_logs push_log
              WHERE push_log.endpoint_id = endpoint.id
                AND (
                    push_log.status IN ('pending', 'retrying')
                    OR push_log.next_retry_at IS NOT NULL
                    OR push_log.lease_owner IS NOT NULL
                    OR push_log.lease_expires_at IS NOT NULL
                )
          )
    )
$helper$

    $archive$;
  END IF;
END
$pearnly$;

REVOKE ALL ON FUNCTION public.erp_managed_endpoint_has_activity(uuid) FROM PUBLIC;
DO $pearnly$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'pearnly_app') THEN
    EXECUTE 'GRANT EXECUTE ON FUNCTION public.erp_managed_endpoint_has_activity(uuid) TO pearnly_app';
  END IF;
END
$pearnly$;

-- Workspace-dependent lifecycle RLS is installed by revision 0112 after its
-- dependency tables exist; this baseline policy keeps legacy replay valid.
DROP POLICY IF EXISTS erp_endpoints_managed_lifecycle_update ON erp_endpoints;
CREATE POLICY erp_endpoints_managed_lifecycle_update ON erp_endpoints FOR UPDATE
USING (current_setting('app.erp_endpoint_lifecycle', true) = 'on'
  AND current_setting('app.erp_endpoint_lifecycle_tenant_id', true) = current_setting('app.current_tenant_id', true)
  AND current_setting('app.erp_endpoint_lifecycle_actor_id', true) = current_setting('app.current_user_id', true)
  AND id::text = current_setting('app.erp_endpoint_lifecycle_endpoint_id', true)
  AND binding_generation > 0 AND adapter = 'express' AND revoked_at IS NULL)
WITH CHECK (current_setting('app.erp_endpoint_lifecycle', true) = 'on'
  AND current_setting('app.erp_endpoint_lifecycle_tenant_id', true) = current_setting('app.current_tenant_id', true)
  AND current_setting('app.erp_endpoint_lifecycle_actor_id', true) = current_setting('app.current_user_id', true)
  AND id::text = current_setting('app.erp_endpoint_lifecycle_endpoint_id', true)
  AND binding_generation > 0 AND adapter = 'express');

-- 0112 installs the exact workspace-aware policies once these later tables exist.
-- Dollar-quoted dynamic SQL keeps this legacy payload replay-safe.
DO $pearnly$
BEGIN
  IF to_regclass('public.workspace_clients') IS NOT NULL
     AND to_regclass('public.memberships') IS NOT NULL
     AND to_regclass('public.roles') IS NOT NULL
  THEN
    EXECUTE $policy$
      DROP POLICY IF EXISTS erp_endpoints_managed_lifecycle_select ON erp_endpoints;
      CREATE POLICY erp_endpoints_managed_lifecycle_select ON erp_endpoints FOR SELECT
      USING (
        current_setting('app.erp_endpoint_lifecycle', true) = 'on'
        AND current_setting('app.erp_endpoint_lifecycle_tenant_id', true) = current_setting('app.current_tenant_id', true)
        AND current_setting('app.erp_endpoint_lifecycle_actor_id', true) = current_setting('app.current_user_id', true)
        AND current_setting('app.erp_endpoint_lifecycle_action', true) IN ('rebind','enable','disable','revoke')
        AND id::text = current_setting('app.erp_endpoint_lifecycle_endpoint_id', true)
        AND current_setting('app.erp_endpoint_lifecycle_expected_generation', true) ~ '^[1-9][0-9]*$'
        AND tenant_id::text = current_setting('app.current_tenant_id', true)
        AND EXISTS (SELECT 1 FROM users lifecycle_actor
          JOIN memberships lifecycle_membership ON lifecycle_membership.user_id = lifecycle_actor.id
          JOIN roles lifecycle_role ON lifecycle_role.id = lifecycle_membership.role_id
          WHERE lifecycle_actor.id::text = current_setting('app.current_user_id', true)
            AND lifecycle_actor.tenant_id = erp_endpoints.tenant_id AND lifecycle_actor.is_active
            AND lifecycle_membership.tenant_id = erp_endpoints.tenant_id
            AND lifecycle_membership.status = 'active' AND lifecycle_role.name = 'owner')
        AND (
          (binding_generation::text = current_setting('app.erp_endpoint_lifecycle_expected_generation', true)
           AND binding_generation > 0 AND adapter = 'express' AND revoked_at IS NULL
           AND current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true) = COALESCE(workspace_client_id::text, '')
           AND EXISTS (SELECT 1 FROM workspace_clients source_workspace
             WHERE source_workspace.id = erp_endpoints.workspace_client_id
               AND source_workspace.tenant_id = erp_endpoints.tenant_id AND source_workspace.is_active))
          OR
          (binding_generation::text = (current_setting('app.erp_endpoint_lifecycle_expected_generation', true)::bigint + 1)::text
           AND binding_generation > 0 AND adapter = 'express'
           AND ((current_setting('app.erp_endpoint_lifecycle_action', true) IN ('enable','disable')
                 AND current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) = current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true)
                 AND workspace_client_id::text = current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true)
                 AND enabled = (current_setting('app.erp_endpoint_lifecycle_action', true) = 'enable')
                 AND shared_scope = TRUE AND revoked_at IS NULL AND revoked_by IS NULL
                 AND EXISTS (SELECT 1 FROM workspace_clients source_workspace
                   WHERE source_workspace.id = erp_endpoints.workspace_client_id
                     AND source_workspace.tenant_id = erp_endpoints.tenant_id AND source_workspace.is_active))
             OR (current_setting('app.erp_endpoint_lifecycle_action', true) = 'rebind'
                 AND current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) <> ''
                 AND workspace_client_id::text = current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true)
                 AND enabled = FALSE AND shared_scope = TRUE AND revoked_at IS NULL AND revoked_by IS NULL
                 AND EXISTS (SELECT 1 FROM workspace_clients target_workspace
                   WHERE target_workspace.id = erp_endpoints.workspace_client_id
                     AND target_workspace.tenant_id = erp_endpoints.tenant_id AND target_workspace.is_active))
             OR (current_setting('app.erp_endpoint_lifecycle_action', true) = 'revoke'
                 AND current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) = ''
                 AND workspace_client_id IS NULL AND enabled = FALSE AND shared_scope = FALSE
                 AND revoked_at IS NOT NULL
                 AND revoked_by::text = current_setting('app.erp_endpoint_lifecycle_actor_id', true))))
        )
      );
      DROP POLICY IF EXISTS erp_endpoints_managed_lifecycle_update ON erp_endpoints;
      CREATE POLICY erp_endpoints_managed_lifecycle_update ON erp_endpoints FOR UPDATE
      USING (
        current_setting('app.erp_endpoint_lifecycle', true) = 'on'
        AND current_setting('app.erp_endpoint_lifecycle_tenant_id', true) = current_setting('app.current_tenant_id', true)
        AND current_setting('app.erp_endpoint_lifecycle_actor_id', true) = current_setting('app.current_user_id', true)
        AND current_setting('app.erp_endpoint_lifecycle_action', true) IN ('rebind','enable','disable','revoke')
        AND id::text = current_setting('app.erp_endpoint_lifecycle_endpoint_id', true)
        AND current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true) = COALESCE(workspace_client_id::text, '')
        AND current_setting('app.erp_endpoint_lifecycle_expected_generation', true) ~ '^[1-9][0-9]*$'
        AND binding_generation >= current_setting('app.erp_endpoint_lifecycle_expected_generation', true)::bigint
        AND binding_generation > 0 AND adapter = 'express' AND revoked_at IS NULL
        AND tenant_id::text = current_setting('app.current_tenant_id', true)
        AND EXISTS (SELECT 1 FROM workspace_clients source_workspace
          WHERE source_workspace.id = erp_endpoints.workspace_client_id
            AND source_workspace.tenant_id = erp_endpoints.tenant_id AND source_workspace.is_active)
        AND EXISTS (SELECT 1 FROM users lifecycle_actor
          JOIN memberships lifecycle_membership ON lifecycle_membership.user_id = lifecycle_actor.id
          JOIN roles lifecycle_role ON lifecycle_role.id = lifecycle_membership.role_id
          WHERE lifecycle_actor.id::text = current_setting('app.current_user_id', true)
            AND lifecycle_actor.tenant_id = erp_endpoints.tenant_id AND lifecycle_actor.is_active
            AND lifecycle_membership.tenant_id = erp_endpoints.tenant_id
            AND lifecycle_membership.status = 'active' AND lifecycle_role.name = 'owner')
      )
      WITH CHECK (current_setting('app.erp_endpoint_lifecycle', true) = 'on'
        AND current_setting('app.erp_endpoint_lifecycle_tenant_id', true) = current_setting('app.current_tenant_id', true)
        AND current_setting('app.erp_endpoint_lifecycle_actor_id', true) = current_setting('app.current_user_id', true)
        AND id::text = current_setting('app.erp_endpoint_lifecycle_endpoint_id', true)
        AND binding_generation::text = (current_setting('app.erp_endpoint_lifecycle_expected_generation', true)::bigint + 1)::text
        AND binding_generation > 0 AND adapter = 'express' AND tenant_id::text = current_setting('app.current_tenant_id', true)
        AND ((current_setting('app.erp_endpoint_lifecycle_action', true) = 'rebind' AND current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) <> '' AND workspace_client_id::text = current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) AND enabled = FALSE AND shared_scope = TRUE AND revoked_at IS NULL AND revoked_by IS NULL)
          OR (current_setting('app.erp_endpoint_lifecycle_action', true) = 'enable' AND current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) = current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true) AND workspace_client_id::text = current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true) AND enabled = TRUE AND shared_scope = TRUE AND revoked_at IS NULL AND revoked_by IS NULL)
          OR (current_setting('app.erp_endpoint_lifecycle_action', true) = 'disable' AND current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) = current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true) AND workspace_client_id::text = current_setting('app.erp_endpoint_lifecycle_source_workspace_id', true) AND enabled = FALSE AND shared_scope = TRUE AND revoked_at IS NULL AND revoked_by IS NULL)
          OR (current_setting('app.erp_endpoint_lifecycle_action', true) = 'revoke' AND current_setting('app.erp_endpoint_lifecycle_target_workspace_id', true) = '' AND workspace_client_id IS NULL AND enabled = FALSE AND shared_scope = FALSE AND revoked_at IS NOT NULL AND revoked_by::text = current_setting('app.erp_endpoint_lifecycle_actor_id', true))))
    $policy$;
  END IF;
END
$pearnly$;
