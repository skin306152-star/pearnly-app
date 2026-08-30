-- Pearnly · 生产库表结构快照(自动生成 · 只读参照 · 不是迁移)
--
-- 生成:python scripts/dump_prod_schema.py docs/db/prod-schema.sql
-- 事实源说明见该脚本文件头。这份文件不被任何运行期代码读取或执行;
-- 它的读者是①灾备重建 ②DDL 覆盖闸(tests/unit/test_schema_ddl_coverage.py)③ PR reviewer。
--
-- 不含:数据、权限/角色、RLS 策略、触发器、扩展。只有表/列/约束/索引。
-- 生成顺序按表名排序,便于 diff;因此 FOREIGN KEY 单独列在末尾而非表内联。


CREATE TABLE IF NOT EXISTS "account_mappings" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "role" text NOT NULL,
  "account_id" uuid NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "account_mappings_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX uq_acct_mapping_role ON public.account_mappings USING btree (tenant_id, workspace_client_id, role);

CREATE TABLE IF NOT EXISTS "accounting_posting_failures" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "operation" text DEFAULT 'enqueue'::text NOT NULL,
  "source_type" text NOT NULL,
  "source_id" text NOT NULL,
  "status" text DEFAULT 'pending'::text NOT NULL,
  "attempts" integer DEFAULT 0 NOT NULL,
  "last_error" text,
  "context" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "created_by" text,
  "next_retry_at" timestamp with time zone,
  "first_failed_at" timestamp with time zone DEFAULT now() NOT NULL,
  "last_failed_at" timestamp with time zone DEFAULT now() NOT NULL,
  "resolved_at" timestamp with time zone,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "accounting_posting_failures_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_acct_posting_failure_due ON public.accounting_posting_failures USING btree (tenant_id, next_retry_at, first_failed_at) WHERE (status = ANY (ARRAY['pending'::text, 'retrying'::text]));
CREATE UNIQUE INDEX uq_acct_posting_failure_open ON public.accounting_posting_failures USING btree (tenant_id, workspace_client_id, operation, source_type, source_id) WHERE (status = ANY (ARRAY['pending'::text, 'retrying'::text]));

CREATE TABLE IF NOT EXISTS "accounting_settings" (
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "auto_post" boolean DEFAULT false NOT NULL,
  "auto_post_threshold" numeric(5,2) DEFAULT 90 NOT NULL,
  "auto_post_rules" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "accounting_standard" text DEFAULT 'TFRS_NPAE'::text NOT NULL,
  "inventory_method" text DEFAULT 'periodic'::text NOT NULL,
  "base_currency" text DEFAULT 'THB'::text NOT NULL,
  "start_period" text,
  "closed_through" text,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "accounting_settings_pkey" PRIMARY KEY (tenant_id, workspace_client_id)
);

CREATE TABLE IF NOT EXISTS "acct_bank_accounts" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "bank_code" text NOT NULL,
  "account_label" text,
  "account_last4" text,
  "coa_account_id" uuid,
  "last_closing_balance" numeric(14,2),
  "last_closing_date" date,
  "is_active" boolean DEFAULT true NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "acct_bank_accounts_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX uq_bank_account ON public.acct_bank_accounts USING btree (tenant_id, workspace_client_id, bank_code, COALESCE(account_last4, ''::text));

CREATE TABLE IF NOT EXISTS "acct_bank_lines" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "bank_account_id" uuid NOT NULL,
  "line_date" date NOT NULL,
  "amount" numeric(14,2) NOT NULL,
  "direction" text NOT NULL,
  "description" text,
  "bank_ref" text,
  "import_batch_id" uuid,
  "source_file_sha256" text,
  "status" text DEFAULT 'unmatched'::text NOT NULL,
  "matched_voucher_id" uuid,
  "match_payload" jsonb,
  "matched_at" timestamp with time zone,
  "matched_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "acct_bank_lines_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_bank_lines_date ON public.acct_bank_lines USING btree (tenant_id, workspace_client_id, line_date);
CREATE INDEX ix_bank_lines_matched_voucher ON public.acct_bank_lines USING btree (tenant_id, workspace_client_id, matched_voucher_id);
CREATE INDEX ix_bank_lines_status ON public.acct_bank_lines USING btree (tenant_id, workspace_client_id, status);
CREATE UNIQUE INDEX uq_bank_line_dedup ON public.acct_bank_lines USING btree (bank_account_id, line_date, amount, COALESCE(description, ''::text), COALESCE(bank_ref, ''::text));

CREATE TABLE IF NOT EXISTS "acct_voucher_templates" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "name" text NOT NULL,
  "lines" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "use_count" integer DEFAULT 0 NOT NULL,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "acct_voucher_templates_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX uq_voucher_template_name ON public.acct_voucher_templates USING btree (tenant_id, workspace_client_id, name);

CREATE TABLE IF NOT EXISTS "agent_turn_logs" (
  "id" bigint DEFAULT nextval('agent_turn_logs_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid,
  "user_id" text,
  "line_user_id" text,
  "trace_id" text,
  "lang" text,
  "user_text" text DEFAULT ''::text NOT NULL,
  "result_kind" text NOT NULL,
  "tool_trace" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "elapsed_ms" integer,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "degraded" text,
  "intent" text,
  CONSTRAINT "agent_turn_logs_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_agent_turn_logs_created ON public.agent_turn_logs USING btree (created_at);
CREATE INDEX ix_agent_turn_logs_tenant ON public.agent_turn_logs USING btree (tenant_id, created_at DESC);

CREATE TABLE IF NOT EXISTS "ai_contract_files" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "contract_id" uuid NOT NULL,
  "tenant_id" uuid NOT NULL,
  "file_ref" text NOT NULL,
  "original_name" text,
  "sha256" text,
  "status" text DEFAULT 'staged'::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "ai_contract_files_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_ai_contract_files_contract ON public.ai_contract_files USING btree (tenant_id, contract_id);

CREATE TABLE IF NOT EXISTS "ai_goal_contracts" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint,
  "period" text,
  "intent" text,
  "deliverables" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "status" text DEFAULT 'draft'::text NOT NULL,
  "utterance_raw" text,
  "brain_suggestion" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "work_order_id" uuid,
  "created_by" text,
  "confirmed_by" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "ai_goal_contracts_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_ai_goal_contracts_client ON public.ai_goal_contracts USING btree (tenant_id, workspace_client_id, created_at DESC);
CREATE INDEX ix_ai_goal_contracts_tenant ON public.ai_goal_contracts USING btree (tenant_id, created_at DESC);

CREATE TABLE IF NOT EXISTS "ai_usage" (
  "id" bigint DEFAULT nextval('ai_usage_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid,
  "user_id" text,
  "task" text NOT NULL,
  "provider" text,
  "model" text,
  "status" text NOT NULL,
  "error_kind" text,
  "latency_ms" integer,
  "input_tokens" integer,
  "output_tokens" integer,
  "cost_thb" numeric(12,6) DEFAULT 0 NOT NULL,
  "trace_id" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "ai_usage_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_ai_usage_task ON public.ai_usage USING btree (task, created_at DESC);
CREATE INDEX idx_ai_usage_tenant ON public.ai_usage USING btree (tenant_id, created_at DESC);

CREATE TABLE IF NOT EXISTS "alembic_version" (
  "version_num" character varying(32) NOT NULL,
  CONSTRAINT "alembic_version_pkc" PRIMARY KEY (version_num)
);
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);

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
CREATE UNIQUE INDEX api_keys_key_hash_key ON public.api_keys USING btree (key_hash);
CREATE INDEX idx_api_keys_hash ON public.api_keys USING btree (key_hash);
CREATE INDEX idx_api_keys_tenant_id ON public.api_keys USING btree (tenant_id);
CREATE INDEX idx_api_keys_user_id ON public.api_keys USING btree (user_id);

CREATE TABLE IF NOT EXISTS "archive_settings" (
  "user_id" uuid NOT NULL,
  "name_template" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "folder_strategy" text DEFAULT 'by_month_seller'::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "tenant_id" uuid,
  CONSTRAINT "archive_folder_strategy_chk" CHECK ((folder_strategy = ANY (ARRAY['none'::text, 'by_month'::text, 'by_seller'::text, 'by_month_seller'::text]))),
  CONSTRAINT "archive_settings_pkey" PRIMARY KEY (user_id)
);
CREATE INDEX idx_archive_settings_tenant_id ON public.archive_settings USING btree (tenant_id);

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
CREATE INDEX idx_automation_rules_tenant_id ON public.automation_rules USING btree (tenant_id);
CREATE INDEX idx_automation_rules_user_id ON public.automation_rules USING btree (user_id);

CREATE TABLE IF NOT EXISTS "bank_recon_v2_task" (
  "id" integer DEFAULT nextval('bank_recon_v2_task_id_seq'::regclass) NOT NULL,
  "user_id" uuid NOT NULL,
  "tenant_id" uuid,
  "bank_code" text,
  "gl_account" text,
  "stmt_files" text,
  "gl_files" text,
  "stmt_row_count" integer DEFAULT 0,
  "gl_row_count" integer DEFAULT 0,
  "matched_count" integer DEFAULT 0,
  "unmatched_gl" integer DEFAULT 0,
  "unmatched_stmt" integer DEFAULT 0,
  "stmt_opening" numeric(18,2) DEFAULT 0,
  "stmt_closing" numeric(18,2) DEFAULT 0,
  "gl_opening" numeric(18,2) DEFAULT 0,
  "gl_closing" numeric(18,2) DEFAULT 0,
  "formula_diff" numeric(18,2) DEFAULT 0,
  "detail_json" jsonb,
  "summary_json" jsonb,
  "status" text DEFAULT 'done'::text,
  "created_at" timestamp with time zone DEFAULT now(),
  "workspace_client_id" bigint,
  CONSTRAINT "bank_recon_v2_task_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_bank_recon_v2_tenant ON public.bank_recon_v2_task USING btree (tenant_id, created_at DESC) WHERE (tenant_id IS NOT NULL);
CREATE INDEX idx_bank_recon_v2_user ON public.bank_recon_v2_task USING btree (user_id, created_at DESC);
CREATE INDEX ix_bank_recon_v2_task_ws ON public.bank_recon_v2_task USING btree (tenant_id, workspace_client_id);

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
CREATE INDEX idx_bank_recon_cand_tx ON public.bank_reconcile_candidates USING btree (tx_id, score DESC);
CREATE INDEX idx_bank_reconcile_candidates_tenant_id ON public.bank_reconcile_candidates USING btree (tenant_id);

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
CREATE INDEX idx_bank_recon_sessions_client ON public.bank_reconcile_sessions USING btree (client_id);
CREATE INDEX idx_bank_recon_sessions_user ON public.bank_reconcile_sessions USING btree (user_id, created_at DESC);
CREATE INDEX idx_bank_reconcile_sessions_tenant_id ON public.bank_reconcile_sessions USING btree (tenant_id);
CREATE INDEX ix_bank_reconcile_sessions_ws ON public.bank_reconcile_sessions USING btree (tenant_id, workspace_client_id);

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
CREATE INDEX idx_bank_recon_tx_match_lookup ON public.bank_reconcile_transactions USING btree (user_id, amount, tx_date) WHERE (match_status = 'unmatched'::text);
CREATE INDEX idx_bank_recon_tx_match_status ON public.bank_reconcile_transactions USING btree (session_id, match_status);
CREATE INDEX idx_bank_recon_tx_session ON public.bank_reconcile_transactions USING btree (session_id, row_no);
CREATE INDEX idx_bank_recon_tx_user_date ON public.bank_reconcile_transactions USING btree (user_id, tx_date DESC);
CREATE INDEX idx_bank_reconcile_transactions_tenant_id ON public.bank_reconcile_transactions USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "billing_balance_log" (
  "id" bigint DEFAULT nextval('billing_balance_log_id_seq'::regclass) NOT NULL,
  "real_balance_thb" numeric(12,4) NOT NULL,
  "notes" text,
  "estimated_used_since_last" numeric(12,4) DEFAULT 0,
  "real_used_since_last" numeric(12,4) DEFAULT 0,
  "calibration_factor" numeric(6,4) DEFAULT 1.0,
  "updated_by_user_id" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "billing_balance_log_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_billing_log_created ON public.billing_balance_log USING btree (created_at DESC);

CREATE TABLE IF NOT EXISTS "brain_shadow_log" (
  "id" bigint DEFAULT nextval('brain_shadow_log_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "work_order_id" uuid NOT NULL,
  "item_id" uuid NOT NULL,
  "suggestion" text,
  "confidence" numeric(4,3),
  "reason_zh" text,
  "cited_event_ids" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "valid" boolean DEFAULT false NOT NULL,
  "invalid_reason" text,
  "model" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "brain_shadow_log_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_brain_shadow_log_wo ON public.brain_shadow_log USING btree (tenant_id, work_order_id, created_at DESC);

CREATE TABLE IF NOT EXISTS "buyer_to_client_memory" (
  "id" bigint DEFAULT nextval('buyer_to_client_memory_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid,
  "user_id" uuid NOT NULL,
  "buyer_name" text NOT NULL,
  "buyer_tax" text,
  "client_id" integer NOT NULL,
  "use_count" integer DEFAULT 1 NOT NULL,
  "last_used_at" timestamp with time zone DEFAULT now() NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "buyer_to_client_memory_pkey" PRIMARY KEY (id)
);
CREATE INDEX buyer_to_client_tax_idx ON public.buyer_to_client_memory USING btree (buyer_tax) WHERE ((buyer_tax IS NOT NULL) AND (length(buyer_tax) >= 10));
CREATE UNIQUE INDEX buyer_to_client_unique_scope ON public.buyer_to_client_memory USING btree (COALESCE((tenant_id)::text, (user_id)::text), lower(buyer_name), COALESCE(buyer_tax, ''::text));

CREATE TABLE IF NOT EXISTS "chart_of_accounts" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "code" text NOT NULL,
  "name_zh" text NOT NULL,
  "name_th" text,
  "acct_type" text NOT NULL,
  "parent_id" uuid,
  "is_preset" boolean DEFAULT false NOT NULL,
  "is_active" boolean DEFAULT true NOT NULL,
  "sort" integer DEFAULT 0 NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "chart_of_accounts_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX uq_coa_code ON public.chart_of_accounts USING btree (tenant_id, workspace_client_id, code);

CREATE TABLE IF NOT EXISTS "client_assignments" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "client_id" bigint NOT NULL,
  "assigned_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "client_assignments_pkey" PRIMARY KEY (id),
  CONSTRAINT "client_assignments_user_id_client_id_key" UNIQUE (user_id, client_id)
);
CREATE UNIQUE INDEX client_assignments_user_id_client_id_key ON public.client_assignments USING btree (user_id, client_id);
CREATE INDEX idx_client_assign_client ON public.client_assignments USING btree (client_id);
CREATE INDEX idx_client_assign_user ON public.client_assignments USING btree (user_id);

CREATE TABLE IF NOT EXISTS "client_name_aliases" (
  "id" bigint DEFAULT nextval('client_name_aliases_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "alias_raw" text NOT NULL,
  "alias_norm" text NOT NULL,
  "alias_kind" text DEFAULT 'misc'::text NOT NULL,
  "match_mode" text DEFAULT 'exact'::text NOT NULL,
  "source" text DEFAULT 'onboarding'::text NOT NULL,
  "confidence" numeric(4,3),
  "is_active" boolean DEFAULT true NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "client_name_aliases_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_client_alias_ws ON public.client_name_aliases USING btree (tenant_id, workspace_client_id);
CREATE UNIQUE INDEX uq_client_alias_norm ON public.client_name_aliases USING btree (tenant_id, alias_norm) WHERE is_active;

CREATE TABLE IF NOT EXISTS "client_payroll_rows" (
  "id" bigint DEFAULT nextval('client_payroll_rows_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "period" text NOT NULL,
  "seq" integer NOT NULL,
  "employee_id" text NOT NULL,
  "title" text DEFAULT ''::text NOT NULL,
  "first_name" text DEFAULT ''::text NOT NULL,
  "last_name" text DEFAULT ''::text NOT NULL,
  "income_code" text DEFAULT '40(1)'::text NOT NULL,
  "paid_date" date,
  "paid_amount" numeric(15,2) DEFAULT 0 NOT NULL,
  "wht_amount" numeric(15,2) DEFAULT 0 NOT NULL,
  "condition" text DEFAULT '1'::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "client_payroll_rows_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_payroll_rows_period ON public.client_payroll_rows USING btree (tenant_id, workspace_client_id, period);

CREATE TABLE IF NOT EXISTS "client_payroll_templates" (
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "column_map" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "income_code" text DEFAULT '40(1)'::text NOT NULL,
  "fixed_values" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "header_hash" text DEFAULT ''::text NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "client_payroll_templates_pkey" PRIMARY KEY (tenant_id, workspace_client_id)
);

CREATE TABLE IF NOT EXISTS "client_period_obligations" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "work_order_id" uuid,
  "period" text NOT NULL,
  "obligation_code" text NOT NULL,
  "status" text DEFAULT 'tentative'::text NOT NULL,
  "trigger_source" text DEFAULT ''::text NOT NULL,
  "due_paper" date,
  "due_efiling" date,
  "assignee" text,
  "filed_at" timestamp with time zone,
  "receipt_ref" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "client_period_obligations_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_period_obligation_due ON public.client_period_obligations USING btree (tenant_id, due_efiling);
CREATE UNIQUE INDEX uq_period_obligation ON public.client_period_obligations USING btree (tenant_id, workspace_client_id, period, obligation_code);

CREATE TABLE IF NOT EXISTS "client_rules" (
  "id" bigint DEFAULT nextval('client_rules_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint,
  "rule_type" text NOT NULL,
  "subject_type" text NOT NULL,
  "subject_key" text,
  "rule_body" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "severity" text,
  "is_active" boolean DEFAULT true NOT NULL,
  "effective_from" date,
  "effective_to" date,
  "origin" text DEFAULT 'manual'::text NOT NULL,
  "confidence" numeric,
  "source_document_id" bigint,
  "source_correction_id" bigint,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_by" uuid,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "hit_count" integer DEFAULT 0 NOT NULL,
  "accepted_count" integer DEFAULT 0 NOT NULL,
  "dismissed_count" integer DEFAULT 0 NOT NULL,
  CONSTRAINT "client_rules_origin_check" CHECK ((origin = ANY (ARRAY['manual'::text, 'learned'::text, 'imported'::text, 'extracted'::text]))),
  CONSTRAINT "client_rules_rule_type_check" CHECK ((rule_type = ANY (ARRAY['supplier_allowlist'::text, 'supplier_force_review'::text, 'amount_limit'::text, 'no_auto_push_category'::text, 'wht_rate'::text, 'accounting_period'::text, 'feature_toggle'::text]))),
  CONSTRAINT "client_rules_severity_check" CHECK (((severity IS NULL) OR (severity = ANY (ARRAY['high'::text, 'medium'::text, 'low'::text])))),
  CONSTRAINT "client_rules_subject_type_check" CHECK ((subject_type = ANY (ARRAY['supplier'::text, 'category'::text, 'contract'::text, 'global'::text]))),
  CONSTRAINT "client_rules_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_client_rules_load ON public.client_rules USING btree (tenant_id, workspace_client_id, rule_type) WHERE is_active;
CREATE INDEX idx_client_rules_subject ON public.client_rules USING btree (tenant_id, workspace_client_id, subject_type, subject_key) WHERE is_active;
CREATE UNIQUE INDEX uq_client_rules_active ON public.client_rules USING btree (tenant_id, COALESCE(workspace_client_id, ('-1'::integer)::bigint), rule_type, subject_type, COALESCE(subject_key, ''::text)) WHERE is_active;

CREATE TABLE IF NOT EXISTS "client_tax_profiles" (
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "sbt_status" text DEFAULT 'none'::text NOT NULL,
  "sbt_business_type" text DEFAULT ''::text NOT NULL,
  "has_employees" text DEFAULT 'unknown'::text NOT NULL,
  "pays_individuals" text DEFAULT 'unknown'::text NOT NULL,
  "pays_juristic" text DEFAULT 'unknown'::text NOT NULL,
  "pays_foreign" text DEFAULT 'unknown'::text NOT NULL,
  "pays_interest_dividend" text DEFAULT 'unknown'::text NOT NULL,
  "has_multi_branch" boolean DEFAULT false NOT NULL,
  "branch_count" smallint DEFAULT 1 NOT NULL,
  "filing_disposition" text DEFAULT 'active'::text NOT NULL,
  "efiling_enrolled" text DEFAULT 'unknown'::text NOT NULL,
  "tax_agent_authorized" boolean DEFAULT false NOT NULL,
  "tax_agent_ref" text DEFAULT ''::text NOT NULL,
  "vat_credit_carry" numeric(14,2) DEFAULT 0 NOT NULL,
  "source" text DEFAULT 'onboarding'::text NOT NULL,
  "confidence" numeric(4,3),
  "profile_version" integer DEFAULT 1 NOT NULL,
  "updated_by" text DEFAULT 'system'::text NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "client_tax_profiles_pkey" PRIMARY KEY (tenant_id, workspace_client_id)
);

CREATE TABLE IF NOT EXISTS "clients" (
  "id" bigint DEFAULT nextval('clients_id_seq'::regclass) NOT NULL,
  "user_id" uuid NOT NULL,
  "tenant_id" uuid,
  "name" text NOT NULL,
  "short_name" text,
  "tax_id" text,
  "address" text,
  "contact_person" text,
  "contact_phone" text,
  "contact_email" text,
  "notes" text,
  "color" text DEFAULT '#3b82f6'::text,
  "is_active" boolean DEFAULT true NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "party_type" text,
  "branch" text,
  "promptpay_id" text,
  CONSTRAINT "clients_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_clients_tax_id ON public.clients USING btree (tax_id) WHERE (tax_id IS NOT NULL);
CREATE INDEX idx_clients_tenant ON public.clients USING btree (tenant_id, is_active);
CREATE INDEX idx_clients_user ON public.clients USING btree (user_id, is_active);

CREATE TABLE IF NOT EXISTS "coa_erp_bridge" (
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "erp_type" text NOT NULL,
  "coa_code" text NOT NULL,
  "erp_code" text NOT NULL,
  "erp_name" text DEFAULT ''::text NOT NULL,
  "match_source" text DEFAULT 'manual'::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "coa_erp_bridge_pkey" PRIMARY KEY (tenant_id, workspace_client_id, erp_type, coa_code)
);

CREATE TABLE IF NOT EXISTS "credit_transactions" (
  "id" integer DEFAULT nextval('credit_transactions_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "user_id" uuid,
  "type" text NOT NULL,
  "amount_thb" numeric(12,2) NOT NULL,
  "pages" integer DEFAULT 0,
  "balance_after" numeric(12,2) NOT NULL,
  "description" text,
  "created_at" timestamp with time zone DEFAULT now(),
  CONSTRAINT "credit_transactions_type_check" CHECK ((type = ANY (ARRAY['topup'::text, 'usage'::text, 'adjustment'::text, 'subscription'::text, 'pos_buyout'::text]))),
  CONSTRAINT "credit_transactions_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_ctx_tenant ON public.credit_transactions USING btree (tenant_id, created_at DESC);
CREATE INDEX idx_ctx_user ON public.credit_transactions USING btree (user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS "dms_line_sessions" (
  "tenant_id" uuid NOT NULL,
  "line_user_id" text NOT NULL,
  "state" text,
  "payload" jsonb DEFAULT '{}'::jsonb,
  "expires_at" timestamp with time zone NOT NULL,
  CONSTRAINT "dms_line_sessions_pkey" PRIMARY KEY (tenant_id, line_user_id)
);

CREATE TABLE IF NOT EXISTS "dms_masters_cache" (
  "endpoint_id" text NOT NULL,
  "masters" jsonb NOT NULL,
  "refreshed_at" timestamp with time zone NOT NULL,
  CONSTRAINT "dms_masters_cache_pkey" PRIMARY KEY (endpoint_id)
);

CREATE TABLE IF NOT EXISTS "dms_operator_profiles" (
  "user_id" uuid NOT NULL,
  "tenant_id" uuid NOT NULL,
  "display_name" text NOT NULL,
  "dms_role" text NOT NULL,
  "status" text DEFAULT 'active'::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now(),
  CONSTRAINT "dms_operator_profiles_dms_role_check" CHECK ((dms_role = ANY (ARRAY['sales'::text, 'admin'::text]))),
  CONSTRAINT "dms_operator_profiles_pkey" PRIMARY KEY (user_id)
);
CREATE INDEX ix_dms_operator_profiles_tenant ON public.dms_operator_profiles USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "document_number_sequences" (
  "tenant_id" uuid NOT NULL,
  "doc_type" text NOT NULL,
  "prefix" text NOT NULL,
  "period" text NOT NULL,
  "next_number" bigint DEFAULT 1 NOT NULL,
  "workspace_client_id" bigint
);
CREATE INDEX ix_document_number_sequences_ws ON public.document_number_sequences USING btree (tenant_id, workspace_client_id);
CREATE UNIQUE INDEX uq_dns_ws ON public.document_number_sequences USING btree (tenant_id, workspace_client_id, doc_type, prefix, period);

CREATE TABLE IF NOT EXISTS "email_codes" (
  "id" bigint DEFAULT nextval('email_codes_id_seq'::regclass) NOT NULL,
  "email" text NOT NULL,
  "code" text NOT NULL,
  "purpose" text DEFAULT 'signup'::text NOT NULL,
  "expires_at" timestamp with time zone NOT NULL,
  "sent_at" timestamp with time zone DEFAULT now() NOT NULL,
  "used" boolean DEFAULT false NOT NULL,
  "used_at" timestamp with time zone,
  "sender_ip" text,
  CONSTRAINT "email_codes_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_email_codes_email ON public.email_codes USING btree (email, purpose, used);
CREATE INDEX idx_email_codes_expires ON public.email_codes USING btree (expires_at);

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
CREATE UNIQUE INDEX email_ingest_accounts_user_id_key ON public.email_ingest_accounts USING btree (user_id);
CREATE INDEX idx_email_ingest_accounts_enabled ON public.email_ingest_accounts USING btree (enabled) WHERE (enabled = true);
CREATE INDEX idx_email_ingest_accounts_tenant_id ON public.email_ingest_accounts USING btree (tenant_id);
CREATE INDEX idx_email_ingest_accounts_user ON public.email_ingest_accounts USING btree (user_id);

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
CREATE INDEX idx_email_ingest_logs_account_time ON public.email_ingest_logs USING btree (account_id, created_at DESC);
CREATE INDEX idx_email_ingest_logs_tenant_id ON public.email_ingest_logs USING btree (tenant_id);
CREATE INDEX idx_email_ingest_logs_user_time ON public.email_ingest_logs USING btree (user_id, created_at DESC);

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
CREATE UNIQUE INDEX email_ingest_seen_uids_account_id_uid_key ON public.email_ingest_seen_uids USING btree (account_id, uid);
CREATE INDEX idx_email_ingest_seen_account ON public.email_ingest_seen_uids USING btree (account_id, fetched_at DESC);
CREATE INDEX idx_email_ingest_seen_uids_tenant_id ON public.email_ingest_seen_uids USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "erp_account_mappings" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "erp_type" text NOT NULL,
  "pearnly_category" character varying(64) NOT NULL,
  "erp_code" character varying(128) NOT NULL,
  "erp_name" text,
  "notes" text,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "erp_account_mappings_pkey" PRIMARY KEY (id),
  CONSTRAINT "erp_account_mappings_tenant_id_erp_type_pearnly_category_key" UNIQUE (tenant_id, erp_type, pearnly_category)
);
CREATE UNIQUE INDEX erp_account_mappings_tenant_id_erp_type_pearnly_category_key ON public.erp_account_mappings USING btree (tenant_id, erp_type, pearnly_category);
CREATE INDEX idx_erp_acc_map_erp ON public.erp_account_mappings USING btree (erp_type);
CREATE INDEX idx_erp_acc_map_tenant ON public.erp_account_mappings USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "erp_client_mappings" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "client_id" bigint NOT NULL,
  "erp_type" text NOT NULL,
  "erp_code" character varying(128) NOT NULL,
  "notes" text,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "erp_client_mappings_pkey" PRIMARY KEY (id),
  CONSTRAINT "erp_client_mappings_tenant_id_client_id_erp_type_key" UNIQUE (tenant_id, client_id, erp_type)
);
CREATE UNIQUE INDEX erp_client_mappings_tenant_id_client_id_erp_type_key ON public.erp_client_mappings USING btree (tenant_id, client_id, erp_type);
CREATE INDEX idx_erp_cli_map_client ON public.erp_client_mappings USING btree (client_id);
CREATE INDEX idx_erp_cli_map_erp ON public.erp_client_mappings USING btree (erp_type);
CREATE INDEX idx_erp_cli_map_tenant ON public.erp_client_mappings USING btree (tenant_id);

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
  CONSTRAINT "erp_endpoints_live_profile_pair_chk" CHECK (((live_account_set IS NULL) = (live_profile_key IS NULL))),
  CONSTRAINT "erp_endpoints_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX idx_erp_endpoints_one_default_per_user ON public.erp_endpoints USING btree (user_id) WHERE (is_default = true);
CREATE INDEX idx_erp_endpoints_tenant_id ON public.erp_endpoints USING btree (tenant_id);
CREATE INDEX idx_erp_endpoints_user ON public.erp_endpoints USING btree (user_id, enabled, is_default DESC);
CREATE UNIQUE INDEX uq_erp_endpoints_user_express ON public.erp_endpoints USING btree (user_id) WHERE (adapter = 'express'::text);
CREATE UNIQUE INDEX uq_erp_endpoints_shared_express_workspace ON public.erp_endpoints USING btree (tenant_id, workspace_client_id, adapter) WHERE ((enabled = true) AND (shared_scope = true) AND (adapter = 'express'::text) AND (tenant_id IS NOT NULL) AND (workspace_client_id IS NOT NULL));

CREATE TABLE IF NOT EXISTS "erp_oauth_states" (
  "state" text NOT NULL,
  "tenant_id" uuid NOT NULL,
  "user_id" uuid NOT NULL,
  "erp_type" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "erp_oauth_states_pkey" PRIMARY KEY (state)
);
CREATE INDEX idx_oauth_states_created ON public.erp_oauth_states USING btree (created_at);

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
CREATE UNIQUE INDEX erp_oauth_tokens_tenant_id_erp_type_organisation_id_key ON public.erp_oauth_tokens USING btree (tenant_id, erp_type, organisation_id);
CREATE INDEX idx_oauth_tokens_default ON public.erp_oauth_tokens USING btree (is_default) WHERE (is_default = true);
CREATE INDEX idx_oauth_tokens_tenant ON public.erp_oauth_tokens USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "erp_product_mappings" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "erp_type" text NOT NULL,
  "item_name" text NOT NULL,
  "item_name_norm" character varying(256) NOT NULL,
  "erp_code" character varying(128) NOT NULL,
  "erp_name" text,
  "notes" text,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "erp_product_mappings_pkey" PRIMARY KEY (id),
  CONSTRAINT "erp_product_mappings_tenant_id_erp_type_item_name_norm_key" UNIQUE (tenant_id, erp_type, item_name_norm)
);
CREATE UNIQUE INDEX erp_product_mappings_tenant_id_erp_type_item_name_norm_key ON public.erp_product_mappings USING btree (tenant_id, erp_type, item_name_norm);
CREATE INDEX idx_erp_prod_map_erp ON public.erp_product_mappings USING btree (erp_type);
CREATE INDEX idx_erp_prod_map_norm ON public.erp_product_mappings USING btree (tenant_id, erp_type, item_name_norm);
CREATE INDEX idx_erp_prod_map_tenant ON public.erp_product_mappings USING btree (tenant_id);

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
CREATE INDEX idx_erp_logs_pending_lease ON public.erp_push_logs USING btree (endpoint_id, status) WHERE (status = 'pending'::text);
CREATE INDEX idx_erp_logs_retry_due ON public.erp_push_logs USING btree (next_retry_at) WHERE ((next_retry_at IS NOT NULL) AND (status = 'failed'::text));
CREATE INDEX idx_erp_push_logs_dedup ON public.erp_push_logs USING btree (history_id, endpoint_id);
CREATE INDEX idx_erp_push_logs_tenant_id ON public.erp_push_logs USING btree (tenant_id);
CREATE INDEX idx_erp_push_logs_user_created ON public.erp_push_logs USING btree (user_id, created_at DESC);
CREATE INDEX idx_push_logs_endpoint ON public.erp_push_logs USING btree (endpoint_id, created_at DESC);
CREATE INDEX idx_push_logs_history ON public.erp_push_logs USING btree (history_id);
CREATE INDEX idx_push_logs_user ON public.erp_push_logs USING btree (user_id, created_at DESC);
CREATE INDEX ix_erp_push_logs_tenant_wo ON public.erp_push_logs USING btree (tenant_id, work_order_id) WHERE (work_order_id IS NOT NULL);

CREATE TABLE IF NOT EXISTS "erp_tax_mappings" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "erp_type" text NOT NULL,
  "pearnly_tax_kind" character varying(32) NOT NULL,
  "erp_code" character varying(64) NOT NULL,
  "notes" text,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "erp_tax_mappings_pkey" PRIMARY KEY (id),
  CONSTRAINT "erp_tax_mappings_tenant_id_erp_type_pearnly_tax_kind_key" UNIQUE (tenant_id, erp_type, pearnly_tax_kind)
);
CREATE UNIQUE INDEX erp_tax_mappings_tenant_id_erp_type_pearnly_tax_kind_key ON public.erp_tax_mappings USING btree (tenant_id, erp_type, pearnly_tax_kind);
CREATE INDEX idx_erp_tax_map_erp ON public.erp_tax_mappings USING btree (erp_type);
CREATE INDEX idx_erp_tax_map_tenant ON public.erp_tax_mappings USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "error_events" (
  "id" bigint DEFAULT nextval('error_events_id_seq'::regclass) NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "level" text DEFAULT 'ERROR'::text NOT NULL,
  "logger" text,
  "message" text,
  "request_id" text,
  "user_id" text,
  "tenant_id" text,
  "path" text,
  "method" text,
  "status_code" integer,
  "exc_type" text,
  "traceback" text,
  CONSTRAINT "error_events_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_error_events_created ON public.error_events USING btree (created_at DESC);

CREATE TABLE IF NOT EXISTS "etax_channel_settings" (
  "tenant_id" uuid NOT NULL,
  "client_id" bigint,
  "channel" text DEFAULT 'noop'::text NOT NULL,
  "credentials_ref" text,
  "config" jsonb,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "workspace_client_id" bigint
);
CREATE INDEX ix_etax_channel_settings_ws ON public.etax_channel_settings USING btree (tenant_id, workspace_client_id);
CREATE UNIQUE INDEX uq_etax_channel_tenant_client ON public.etax_channel_settings USING btree (tenant_id, COALESCE(client_id, ('-1'::integer)::bigint));

CREATE TABLE IF NOT EXISTS "etax_submissions" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "document_id" uuid NOT NULL,
  "channel" text NOT NULL,
  "rd_ref" text,
  "status" text DEFAULT 'pending'::text NOT NULL,
  "receipt_url" text,
  "payload" jsonb,
  "error" text,
  "submitted_at" timestamp with time zone,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "workspace_client_id" bigint,
  CONSTRAINT "etax_submissions_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_etax_submissions_doc ON public.etax_submissions USING btree (tenant_id, document_id);
CREATE INDEX ix_etax_submissions_ws ON public.etax_submissions USING btree (tenant_id, workspace_client_id);

CREATE TABLE IF NOT EXISTS "excel_templates" (
  "id" bigint DEFAULT nextval('excel_templates_id_seq'::regclass) NOT NULL,
  "owner_id" uuid,
  "name" text NOT NULL,
  "description" text,
  "config_json" jsonb NOT NULL,
  "is_default" boolean DEFAULT false NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "tenant_id" uuid,
  CONSTRAINT "excel_templates_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_excel_templates_tenant_id ON public.excel_templates USING btree (tenant_id);
CREATE INDEX idx_tpl_owner ON public.excel_templates USING btree (owner_id);

CREATE TABLE IF NOT EXISTS "exception_whitelist" (
  "id" bigint DEFAULT nextval('exception_whitelist_id_seq'::regclass) NOT NULL,
  "user_id" uuid NOT NULL,
  "tenant_id" uuid,
  "seller_name" text NOT NULL,
  "rule_code" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "exception_whitelist_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_exc_wl_tenant ON public.exception_whitelist USING btree (tenant_id) WHERE (tenant_id IS NOT NULL);
CREATE UNIQUE INDEX idx_exc_wl_unique ON public.exception_whitelist USING btree (COALESCE((tenant_id)::text, (user_id)::text), lower(seller_name), rule_code);
CREATE INDEX idx_exc_wl_user ON public.exception_whitelist USING btree (user_id);

CREATE TABLE IF NOT EXISTS "exceptions" (
  "id" bigint DEFAULT nextval('exceptions_id_seq'::regclass) NOT NULL,
  "user_id" uuid NOT NULL,
  "tenant_id" uuid,
  "history_id" uuid NOT NULL,
  "rule_code" text NOT NULL,
  "severity" text DEFAULT 'medium'::text NOT NULL,
  "seller_name" text,
  "invoice_no" text,
  "total_amount" numeric(18,2),
  "detail_json" jsonb,
  "status" text DEFAULT 'pending'::text NOT NULL,
  "resolved_by" uuid,
  "resolved_at" timestamp with time zone,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "exceptions_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_exc_created ON public.exceptions USING btree (created_at DESC);
CREATE INDEX idx_exc_history ON public.exceptions USING btree (history_id);
CREATE INDEX idx_exc_rule ON public.exceptions USING btree (rule_code);
CREATE INDEX idx_exc_tenant_status ON public.exceptions USING btree (tenant_id, status) WHERE (tenant_id IS NOT NULL);
CREATE UNIQUE INDEX idx_exc_unique_pending ON public.exceptions USING btree (history_id, rule_code) WHERE (status = 'pending'::text);
CREATE INDEX idx_exc_user_status ON public.exceptions USING btree (user_id, status);

CREATE TABLE IF NOT EXISTS "expense_categories" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "parent_id" uuid,
  "name" text NOT NULL,
  "is_active" boolean DEFAULT true NOT NULL,
  "sort" integer DEFAULT 0 NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "expense_categories_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_expense_categories_ws ON public.expense_categories USING btree (tenant_id, workspace_client_id);

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
CREATE INDEX ix_expense_draft_invoice_no ON public.expense_draft USING btree (tenant_id, workspace_client_id, invoice_number);
CREATE INDEX ix_expense_draft_ws_status ON public.expense_draft USING btree (tenant_id, workspace_client_id, status);

CREATE TABLE IF NOT EXISTS "expense_learned" (
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "keyword" text NOT NULL,
  "category_id" uuid,
  "subcategory_id" uuid,
  "category_name" text DEFAULT ''::text NOT NULL,
  "subcategory_name" text DEFAULT ''::text NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "source" text DEFAULT ''::text NOT NULL,
  CONSTRAINT "expense_learned_pkey" PRIMARY KEY (tenant_id, workspace_client_id, keyword)
);

CREATE TABLE IF NOT EXISTS "export_archived_docs" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "doc_id" uuid NOT NULL,
  "drive_folder_id" text,
  "drive_url" text,
  "sheet_synced" boolean DEFAULT false NOT NULL,
  "archived_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "export_archived_docs_pkey" PRIMARY KEY (id),
  CONSTRAINT "export_archived_docs_tenant_id_workspace_client_id_doc_id_key" UNIQUE (tenant_id, workspace_client_id, doc_id)
);
CREATE UNIQUE INDEX export_archived_docs_tenant_id_workspace_client_id_doc_id_key ON public.export_archived_docs USING btree (tenant_id, workspace_client_id, doc_id);
CREATE INDEX ix_export_archived_ws ON public.export_archived_docs USING btree (tenant_id, workspace_client_id);

CREATE TABLE IF NOT EXISTS "export_google_credentials" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "google_email" text,
  "access_token" text NOT NULL,
  "refresh_token" text NOT NULL,
  "expires_at" timestamp with time zone,
  "scope" text,
  "token_version" integer DEFAULT 1 NOT NULL,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "export_google_credentials_pkey" PRIMARY KEY (id),
  CONSTRAINT "export_google_credentials_tenant_id_workspace_client_id_key" UNIQUE (tenant_id, workspace_client_id)
);
CREATE UNIQUE INDEX export_google_credentials_tenant_id_workspace_client_id_key ON public.export_google_credentials USING btree (tenant_id, workspace_client_id);
CREATE INDEX ix_export_creds_ws ON public.export_google_credentials USING btree (tenant_id, workspace_client_id);

CREATE TABLE IF NOT EXISTS "export_oauth_states" (
  "state" text NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "user_id" uuid NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "return_to" text DEFAULT 'purchase-export'::text NOT NULL,
  CONSTRAINT "export_oauth_states_pkey" PRIMARY KEY (state)
);
CREATE INDEX ix_export_states_created ON public.export_oauth_states USING btree (created_at);

CREATE TABLE IF NOT EXISTS "filing_lines" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "filing_id" uuid NOT NULL,
  "payee_name" text,
  "payee_tax_id" text,
  "payee_type" text DEFAULT 'juristic'::text NOT NULL,
  "income_type" text DEFAULT 'service'::text NOT NULL,
  "base_amount" numeric(14,2) DEFAULT 0 NOT NULL,
  "wht_rate" numeric(5,2),
  "wht_amount" numeric(14,2) DEFAULT 0 NOT NULL,
  "source_purchase_id" uuid,
  "cert_url" text,
  "cert_status" text DEFAULT 'generated'::text NOT NULL,
  "sort" integer DEFAULT 0 NOT NULL,
  CONSTRAINT "filing_lines_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_filing_lines_filing ON public.filing_lines USING btree (tenant_id, filing_id);

CREATE TABLE IF NOT EXISTS "gl_vat_task" (
  "id" bigint DEFAULT nextval('gl_vat_task_id_seq'::regclass) NOT NULL,
  "user_id" uuid NOT NULL,
  "tenant_id" uuid,
  "gl_filename" text,
  "vat_filename" text,
  "gl_row_count" integer DEFAULT 0,
  "vat_row_count" integer DEFAULT 0,
  "matched_count" integer DEFAULT 0,
  "unmatched_count" integer DEFAULT 0,
  "diff_count" integer DEFAULT 0,
  "detail_json" jsonb,
  "summary_json" jsonb,
  "status" text DEFAULT 'done'::text,
  "error" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "workspace_client_id" bigint,
  CONSTRAINT "gl_vat_task_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_gl_vat_task_tenant ON public.gl_vat_task USING btree (tenant_id, created_at DESC);
CREATE INDEX idx_gl_vat_task_user ON public.gl_vat_task USING btree (user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS "import_template_mappings" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "document_type" text NOT NULL,
  "header_signature" text NOT NULL,
  "template_name" text,
  "sheet_hint" text,
  "mapping_json" jsonb NOT NULL,
  "sample_headers" jsonb,
  "source" text,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "import_template_mappings_pkey" PRIMARY KEY (id),
  CONSTRAINT "import_template_mappings_tenant_id_document_type_header_sig_key" UNIQUE (tenant_id, document_type, header_signature)
);
CREATE INDEX idx_import_tmpl_tenant_type ON public.import_template_mappings USING btree (tenant_id, document_type);
CREATE UNIQUE INDEX import_template_mappings_tenant_id_document_type_header_sig_key ON public.import_template_mappings USING btree (tenant_id, document_type, header_signature);

CREATE TABLE IF NOT EXISTS "inventory_batches" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "product_id" uuid NOT NULL,
  "batch_no" text NOT NULL,
  "expiry_date" date,
  "received_at" date DEFAULT CURRENT_DATE NOT NULL,
  "unit_cost" numeric(14,2),
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "workspace_client_id" bigint,
  CONSTRAINT "inventory_batches_pkey" PRIMARY KEY (id),
  CONSTRAINT "inventory_batches_tenant_id_product_id_batch_no_key" UNIQUE (tenant_id, product_id, batch_no)
);
CREATE UNIQUE INDEX inventory_batches_tenant_id_product_id_batch_no_key ON public.inventory_batches USING btree (tenant_id, product_id, batch_no);
CREATE INDEX ix_batches_fefo ON public.inventory_batches USING btree (tenant_id, product_id, expiry_date);
CREATE INDEX ix_batches_ws ON public.inventory_batches USING btree (tenant_id, workspace_client_id, product_id);
CREATE INDEX ix_inventory_batches_ws ON public.inventory_batches USING btree (tenant_id, workspace_client_id);

CREATE TABLE IF NOT EXISTS "inventory_stock" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "product_id" uuid NOT NULL,
  "warehouse_id" bigint NOT NULL,
  "batch_id" uuid,
  "qty_on_hand" numeric(14,3) DEFAULT 0 NOT NULL,
  "qty_reserved" numeric(14,3) DEFAULT 0 NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "inventory_stock_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_stock_ws_product ON public.inventory_stock USING btree (tenant_id, workspace_client_id, product_id);
CREATE UNIQUE INDEX uq_stock_batched ON public.inventory_stock USING btree (tenant_id, product_id, warehouse_id, batch_id) WHERE (batch_id IS NOT NULL);
CREATE UNIQUE INDEX uq_stock_nobatch ON public.inventory_stock USING btree (tenant_id, product_id, warehouse_id) WHERE (batch_id IS NULL);

CREATE TABLE IF NOT EXISTS "inventory_transactions" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "product_id" uuid NOT NULL,
  "warehouse_id" bigint NOT NULL,
  "batch_id" uuid,
  "txn_type" text NOT NULL,
  "qty_delta" numeric(14,3) NOT NULL,
  "unit_cost" numeric(14,2),
  "ref_type" text,
  "ref_id" uuid,
  "client_uuid" uuid,
  "reason" text,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "inventory_transactions_pkey" PRIMARY KEY (id),
  CONSTRAINT "inventory_transactions_client_uuid_key" UNIQUE (client_uuid)
);
CREATE UNIQUE INDEX inventory_transactions_client_uuid_key ON public.inventory_transactions USING btree (client_uuid);
CREATE INDEX ix_txn_product ON public.inventory_transactions USING btree (tenant_id, workspace_client_id, product_id, created_at);

CREATE TABLE IF NOT EXISTS "invitations" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "email" text,
  "line_target" text,
  "role_key" text NOT NULL,
  "scope_mode" text DEFAULT 'all'::text NOT NULL,
  "workspace_ids" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "token_hash" text NOT NULL,
  "invited_by" uuid NOT NULL,
  "expires_at" timestamp with time zone NOT NULL,
  "accepted_at" timestamp with time zone,
  "accepted_user_id" uuid,
  "revoked_at" timestamp with time zone,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "invitations_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_invitations_tenant ON public.invitations USING btree (tenant_id, created_at DESC);
CREATE UNIQUE INDEX uq_invitations_token_hash ON public.invitations USING btree (token_hash);

CREATE TABLE IF NOT EXISTS "invoice_risk_checks" (
  "id" bigint DEFAULT nextval('invoice_risk_checks_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint,
  "history_id" uuid NOT NULL,
  "risk_level" text NOT NULL,
  "needs_human_review" boolean DEFAULT false NOT NULL,
  "findings" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "status" text NOT NULL,
  "human_status" text DEFAULT 'unreviewed'::text NOT NULL,
  "error_code" text,
  "created_by" uuid,
  "checked_at" timestamp with time zone DEFAULT now() NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "invoice_risk_checks_risk_level_check" CHECK ((risk_level = ANY (ARRAY['high'::text, 'medium'::text, 'low'::text]))),
  CONSTRAINT "invoice_risk_checks_status_check" CHECK ((status = ANY (ARRAY['pending'::text, 'success'::text, 'failed'::text, 'skipped'::text]))),
  CONSTRAINT "invoice_risk_checks_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_invoice_risk_checks_history ON public.invoice_risk_checks USING btree (tenant_id, history_id, id);

CREATE TABLE IF NOT EXISTS "ip_usage" (
  "ip_address" text NOT NULL,
  "usage_date" date DEFAULT CURRENT_DATE NOT NULL,
  "count" integer DEFAULT 0 NOT NULL,
  CONSTRAINT "ip_usage_pkey" PRIMARY KEY (ip_address, usage_date)
);
CREATE INDEX idx_ip_date ON public.ip_usage USING btree (usage_date DESC);

CREATE TABLE IF NOT EXISTS "journal_lines" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "voucher_id" uuid NOT NULL,
  "account_id" uuid NOT NULL,
  "dr_cr" text NOT NULL,
  "amount" numeric(14,2) NOT NULL,
  "memo" text,
  "sort" integer DEFAULT 0 NOT NULL,
  CONSTRAINT "journal_lines_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_journal_lines_voucher ON public.journal_lines USING btree (tenant_id, voucher_id);

CREATE TABLE IF NOT EXISTS "journal_vouchers" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "voucher_no" text,
  "voucher_date" date NOT NULL,
  "period" text NOT NULL,
  "source_type" text NOT NULL,
  "source_id" uuid,
  "source_ref" text,
  "description" text,
  "human_note" text,
  "rule_key" text,
  "confidence" numeric(5,2) DEFAULT 0 NOT NULL,
  "source_tier" text DEFAULT 'manual'::text NOT NULL,
  "method" text DEFAULT 'suggested'::text NOT NULL,
  "status" text DEFAULT 'pending_review'::text NOT NULL,
  "review_reason" text,
  "total_debit" numeric(14,2) DEFAULT 0 NOT NULL,
  "total_credit" numeric(14,2) DEFAULT 0 NOT NULL,
  "created_by" text,
  "reviewed_by" uuid,
  "reviewed_at" timestamp with time zone,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "journal_vouchers_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_jv_ws_period ON public.journal_vouchers USING btree (tenant_id, workspace_client_id, period);
CREATE UNIQUE INDEX uq_jv_source ON public.journal_vouchers USING btree (tenant_id, workspace_client_id, source_type, source_id) WHERE ((source_id IS NOT NULL) AND (status <> 'void'::text));

CREATE TABLE IF NOT EXISTS "knowledge_answers" (
  "id" bigint DEFAULT nextval('knowledge_answers_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint,
  "question" text NOT NULL,
  "answer" text NOT NULL,
  "citations" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "model" text,
  "no_answer" boolean DEFAULT false NOT NULL,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "knowledge_answers_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_knowledge_answers_tenant ON public.knowledge_answers USING btree (tenant_id, workspace_client_id, id);

CREATE TABLE IF NOT EXISTS "knowledge_bases" (
  "id" bigint DEFAULT nextval('knowledge_bases_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint,
  "scope" text NOT NULL,
  "name" text NOT NULL,
  "status" text DEFAULT 'active'::text NOT NULL,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "knowledge_bases_scope_check" CHECK ((scope = ANY (ARRAY['firm'::text, 'workspace_client'::text]))),
  CONSTRAINT "knowledge_bases_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_knowledge_bases_tenant_scope_name ON public.knowledge_bases USING btree (tenant_id, scope, name, workspace_client_id);

CREATE TABLE IF NOT EXISTS "knowledge_chunks" (
  "id" bigint DEFAULT nextval('knowledge_chunks_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint,
  "document_id" bigint NOT NULL,
  "chunk_index" integer NOT NULL,
  "text" text NOT NULL,
  "char_count" integer NOT NULL,
  "metadata" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "knowledge_chunks_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_knowledge_chunks_tenant_document ON public.knowledge_chunks USING btree (tenant_id, document_id, chunk_index);

CREATE TABLE IF NOT EXISTS "knowledge_documents" (
  "id" bigint DEFAULT nextval('knowledge_documents_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint,
  "knowledge_base_id" bigint NOT NULL,
  "source_type" text NOT NULL,
  "filename" text NOT NULL,
  "mime_type" text,
  "storage_path" text,
  "checksum" text NOT NULL,
  "status" text NOT NULL,
  "uploaded_by" uuid,
  "error_code" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "knowledge_documents_status_check" CHECK ((status = ANY (ARRAY['uploaded'::text, 'extracting'::text, 'chunking'::text, 'embedding'::text, 'ready'::text, 'failed'::text, 'deleted'::text]))),
  CONSTRAINT "knowledge_documents_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_knowledge_documents_tenant_base ON public.knowledge_documents USING btree (tenant_id, knowledge_base_id, status);

CREATE TABLE IF NOT EXISTS "knowledge_embeddings" (
  "id" bigint DEFAULT nextval('knowledge_embeddings_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint,
  "chunk_id" bigint NOT NULL,
  "embedding" vector(768) NOT NULL,
  "model" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "knowledge_embeddings_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_knowledge_embeddings_tenant ON public.knowledge_embeddings USING btree (tenant_id, workspace_client_id);
CREATE INDEX idx_knowledge_embeddings_vec ON public.knowledge_embeddings USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS "knowledge_ingest_jobs" (
  "id" bigint DEFAULT nextval('knowledge_ingest_jobs_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint,
  "document_id" bigint NOT NULL,
  "status" text NOT NULL,
  "progress" integer DEFAULT 0 NOT NULL,
  "error_code" text,
  "retry_count" integer DEFAULT 0 NOT NULL,
  "max_retries" integer DEFAULT 3 NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "finished_at" timestamp with time zone,
  CONSTRAINT "knowledge_ingest_jobs_status_check" CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'success'::text, 'failed'::text, 'retrying'::text]))),
  CONSTRAINT "knowledge_ingest_jobs_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_knowledge_ingest_jobs_document ON public.knowledge_ingest_jobs USING btree (document_id);
CREATE INDEX idx_knowledge_ingest_jobs_tenant_status ON public.knowledge_ingest_jobs USING btree (tenant_id, status);

CREATE TABLE IF NOT EXISTS "line_action_nonces" (
  "token" text NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "user_id" text DEFAULT ''::text NOT NULL,
  "action_ref" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "expires_at" timestamp with time zone NOT NULL,
  "consumed_at" timestamp with time zone,
  CONSTRAINT "line_action_nonces_pkey" PRIMARY KEY (token)
);
CREATE INDEX ix_line_action_nonces_expires ON public.line_action_nonces USING btree (expires_at);

CREATE TABLE IF NOT EXISTS "line_agent_anchors" (
  "tenant_id" uuid NOT NULL,
  "line_user_id" text NOT NULL,
  "anchors" jsonb NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "expires_at" timestamp with time zone NOT NULL,
  CONSTRAINT "line_agent_anchors_pkey" PRIMARY KEY (tenant_id, line_user_id)
);

CREATE TABLE IF NOT EXISTS "line_agent_profiles" (
  "tenant_id" uuid NOT NULL,
  "line_user_id" text NOT NULL,
  "profile" jsonb NOT NULL,
  "refreshed_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "line_agent_profiles_pkey" PRIMARY KEY (tenant_id, line_user_id)
);

CREATE TABLE IF NOT EXISTS "line_binding_codes" (
  "code" text NOT NULL,
  "user_id" uuid NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "expires_at" timestamp with time zone NOT NULL,
  "used_at" timestamp with time zone,
  "tenant_id" uuid,
  CONSTRAINT "line_binding_codes_pkey" PRIMARY KEY (code)
);
CREATE INDEX idx_line_binding_codes_expires ON public.line_binding_codes USING btree (expires_at);
CREATE INDEX idx_line_binding_codes_tenant_id ON public.line_binding_codes USING btree (tenant_id);
CREATE INDEX idx_line_binding_codes_user ON public.line_binding_codes USING btree (user_id, used_at);

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
CREATE INDEX idx_line_bindings_tenant_id ON public.line_bindings USING btree (tenant_id);
CREATE UNIQUE INDEX uq_line_bindings_line_user_id ON public.line_bindings USING btree (line_user_id);
CREATE UNIQUE INDEX uq_line_bindings_user_id ON public.line_bindings USING btree (user_id);

CREATE TABLE IF NOT EXISTS "line_chat_history" (
  "id" bigint DEFAULT nextval('line_chat_history_id_seq'::regclass) NOT NULL,
  "line_user_id" text NOT NULL,
  "tenant_id" uuid NOT NULL,
  "role" text NOT NULL,
  "content" text DEFAULT ''::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "line_chat_history_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_line_chat_history_user ON public.line_chat_history USING btree (line_user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS "line_client_bind_codes" (
  "code" text NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "expires_at" timestamp with time zone NOT NULL,
  CONSTRAINT "line_client_bind_codes_pkey" PRIMARY KEY (code)
);

CREATE TABLE IF NOT EXISTS "line_client_contacts" (
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "line_user_id" text NOT NULL,
  "preferred_lang" text DEFAULT 'th'::text NOT NULL,
  "display_name" text,
  "bound_at" timestamp with time zone DEFAULT now() NOT NULL,
  "last_active_at" timestamp with time zone,
  CONSTRAINT "line_client_contacts_pkey" PRIMARY KEY (tenant_id, workspace_client_id)
);
CREATE INDEX ix_line_client_contacts_luid ON public.line_client_contacts USING btree (line_user_id);

CREATE TABLE IF NOT EXISTS "line_client_questions" (
  "id" bigint DEFAULT nextval('line_client_questions_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "work_order_id" uuid NOT NULL,
  "item_id" uuid NOT NULL,
  "period" text NOT NULL,
  "question_type" text NOT NULL,
  "question_payload" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "status" text DEFAULT 'staged'::text NOT NULL,
  "batch_id" uuid,
  "answer_raw" text,
  "resolution" jsonb,
  "created_by" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "sent_at" timestamp with time zone,
  "answered_at" timestamp with time zone,
  "closed_at" timestamp with time zone,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "batch_seq" smallint,
  CONSTRAINT "line_client_questions_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_lcq_client_active ON public.line_client_questions USING btree (tenant_id, workspace_client_id, status);
CREATE INDEX ix_lcq_pending_chase ON public.line_client_questions USING btree (status, sent_at) WHERE (status = 'pending'::text);
CREATE UNIQUE INDEX uq_lcq_active_item ON public.line_client_questions USING btree (tenant_id, work_order_id, item_id) WHERE (status = ANY (ARRAY['staged'::text, 'pending'::text, 'manual_review'::text]));

CREATE TABLE IF NOT EXISTS "line_dms_binding_codes" (
  "code" text NOT NULL,
  "tenant_id" uuid,
  "user_id" uuid,
  "expires_at" timestamp with time zone,
  "used_at" timestamp with time zone,
  CONSTRAINT "line_dms_binding_codes_pkey" PRIMARY KEY (code)
);

CREATE TABLE IF NOT EXISTS "line_dms_bindings" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "line_user_id" text,
  "tenant_id" uuid NOT NULL,
  "user_id" uuid NOT NULL,
  "display_name" text,
  "bound_at" timestamp with time zone DEFAULT now(),
  "last_active_at" timestamp with time zone,
  CONSTRAINT "line_dms_bindings_pkey" PRIMARY KEY (id),
  CONSTRAINT "line_dms_bindings_line_user_id_key" UNIQUE (line_user_id)
);
CREATE UNIQUE INDEX line_dms_bindings_line_user_id_key ON public.line_dms_bindings USING btree (line_user_id);

CREATE TABLE IF NOT EXISTS "line_funnel_events" (
  "line_user_id" text NOT NULL,
  "event" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "line_funnel_events_pkey" PRIMARY KEY (line_user_id, event)
);

CREATE TABLE IF NOT EXISTS "line_message_refs" (
  "line_message_id" text NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "line_user_id" text DEFAULT ''::text NOT NULL,
  "ref_type" text DEFAULT 'purchase_doc'::text NOT NULL,
  "ref_id" text NOT NULL,
  "state" text DEFAULT ''::text NOT NULL,
  "summary" text DEFAULT ''::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "expires_at" timestamp with time zone NOT NULL,
  CONSTRAINT "line_message_refs_pkey" PRIMARY KEY (line_message_id)
);
CREATE INDEX ix_line_message_refs_expires ON public.line_message_refs USING btree (expires_at);

CREATE TABLE IF NOT EXISTS "line_ocr_jobs" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid,
  "user_id" text DEFAULT ''::text NOT NULL,
  "line_user_id" text NOT NULL,
  "message_id" text NOT NULL,
  "lang" text DEFAULT 'th'::text NOT NULL,
  "filename" text,
  "quote_token" text,
  "payload" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "status" text DEFAULT 'queued'::text NOT NULL,
  "attempts" integer DEFAULT 0 NOT NULL,
  "max_attempts" integer DEFAULT 3 NOT NULL,
  "last_error" text,
  "next_retry_at" timestamp with time zone,
  "started_at" timestamp with time zone,
  "finished_at" timestamp with time zone,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "line_ocr_jobs_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_line_ocr_jobs_due ON public.line_ocr_jobs USING btree (status, next_retry_at, created_at);
CREATE INDEX ix_line_ocr_jobs_tenant ON public.line_ocr_jobs USING btree (tenant_id, status, created_at);
CREATE UNIQUE INDEX uq_line_ocr_job_message ON public.line_ocr_jobs USING btree (line_user_id, message_id);

CREATE TABLE IF NOT EXISTS "line_pending_actions" (
  "tenant_id" uuid NOT NULL,
  "line_user_id" text NOT NULL,
  "action" jsonb NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "expires_at" timestamp with time zone NOT NULL,
  CONSTRAINT "line_pending_actions_pkey" PRIMARY KEY (tenant_id, line_user_id)
);

CREATE TABLE IF NOT EXISTS "line_pending_entry" (
  "line_user_id" text NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "draft" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "missing" text DEFAULT ''::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "line_pending_entry_pkey" PRIMARY KEY (line_user_id)
);

CREATE TABLE IF NOT EXISTS "line_pending_intents" (
  "tenant_id" uuid NOT NULL,
  "line_user_id" text NOT NULL,
  "workspace_client_id" bigint,
  "intent" jsonb NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "expires_at" timestamp with time zone NOT NULL,
  CONSTRAINT "line_pending_intents_pkey" PRIMARY KEY (tenant_id, line_user_id)
);

CREATE TABLE IF NOT EXISTS "line_voice_quota" (
  "line_user_id" text NOT NULL,
  "day" date NOT NULL,
  "n" integer DEFAULT 0 NOT NULL,
  CONSTRAINT "line_voice_quota_pkey" PRIMARY KEY (line_user_id, day)
);

CREATE TABLE IF NOT EXISTS "line_webhook_events" (
  "event_id" text NOT NULL,
  "received_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "line_webhook_events_pkey" PRIMARY KEY (event_id)
);

CREATE TABLE IF NOT EXISTS "login_failure_log" (
  "id" bigint DEFAULT nextval('login_failure_log_id_seq'::regclass) NOT NULL,
  "email_or_username" text NOT NULL,
  "ip" text,
  "fingerprint" text,
  "user_agent" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "login_failure_log_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_login_fail_ip ON public.login_failure_log USING btree (ip, created_at DESC);
CREATE INDEX idx_login_fail_user ON public.login_failure_log USING btree (email_or_username, created_at DESC);

CREATE TABLE IF NOT EXISTS "member_scopes" (
  "id" bigint DEFAULT nextval('member_scopes_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "membership_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "assigned_by" uuid NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "member_scopes_pkey" PRIMARY KEY (id),
  CONSTRAINT "member_scopes_membership_id_workspace_client_id_key" UNIQUE (membership_id, workspace_client_id)
);
CREATE INDEX ix_member_scopes_ws ON public.member_scopes USING btree (tenant_id, workspace_client_id);
CREATE UNIQUE INDEX member_scopes_membership_id_workspace_client_id_key ON public.member_scopes USING btree (membership_id, workspace_client_id);

CREATE TABLE IF NOT EXISTS "memberships" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "tenant_id" uuid NOT NULL,
  "role_id" uuid NOT NULL,
  "status" text DEFAULT 'active'::text NOT NULL,
  "joined_at" timestamp with time zone DEFAULT now() NOT NULL,
  "scope_mode" text DEFAULT 'all'::text NOT NULL,
  "granted_by" uuid,
  "granted_at" timestamp with time zone,
  CONSTRAINT "memberships_pkey" PRIMARY KEY (id),
  CONSTRAINT "memberships_user_id_key" UNIQUE (user_id)
);
CREATE INDEX idx_memberships_status ON public.memberships USING btree (status) WHERE (status = 'active'::text);
CREATE INDEX idx_memberships_tenant ON public.memberships USING btree (tenant_id);
CREATE UNIQUE INDEX memberships_user_id_key ON public.memberships USING btree (user_id);

CREATE TABLE IF NOT EXISTS "monthly_page_usage" (
  "tenant_id" uuid NOT NULL,
  "year_month" text NOT NULL,
  "pages_used" integer DEFAULT 0 NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now(),
  CONSTRAINT "monthly_page_usage_pkey" PRIMARY KEY (tenant_id, year_month)
);

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
CREATE INDEX idx_mrerp_credentials_tenant ON public.mrerp_credentials USING btree (tenant_id);
CREATE UNIQUE INDEX mrerp_credentials_tenant_unique ON public.mrerp_credentials USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "notification_logs" (
  "id" bigint DEFAULT nextval('notification_logs_id_seq'::regclass) NOT NULL,
  "user_id" uuid NOT NULL,
  "tenant_id" uuid,
  "rule_id" bigint,
  "template_code" text NOT NULL,
  "event_type" text,
  "event_ref" text,
  "line_user_id" text,
  "status" text NOT NULL,
  "error" text,
  "sent_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "notification_logs_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_notif_logs_rule ON public.notification_logs USING btree (rule_id, sent_at DESC) WHERE (rule_id IS NOT NULL);
CREATE INDEX idx_notif_logs_user ON public.notification_logs USING btree (user_id, sent_at DESC);

CREATE TABLE IF NOT EXISTS "notification_rules" (
  "id" bigint DEFAULT nextval('notification_rules_id_seq'::regclass) NOT NULL,
  "user_id" uuid NOT NULL,
  "tenant_id" uuid,
  "name" text NOT NULL,
  "template_code" text NOT NULL,
  "params" jsonb DEFAULT '{}'::jsonb,
  "enabled" boolean DEFAULT true,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "notification_rules_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_notif_rules_active ON public.notification_rules USING btree (template_code) WHERE (enabled = true);
CREATE INDEX idx_notif_rules_tenant ON public.notification_rules USING btree (tenant_id) WHERE (tenant_id IS NOT NULL);
CREATE INDEX idx_notif_rules_user ON public.notification_rules USING btree (user_id);

CREATE TABLE IF NOT EXISTS "ocr_correction_examples" (
  "id" bigint DEFAULT nextval('ocr_correction_examples_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid,
  "user_id" uuid NOT NULL,
  "seller_tax" text,
  "seller_name" text,
  "field_name" text NOT NULL,
  "ai_value" text,
  "corrected_value" text NOT NULL,
  "use_count" integer DEFAULT 1 NOT NULL,
  "source_history_id" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "ocr_correction_examples_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_corr_ex_lookup ON public.ocr_correction_examples USING btree (COALESCE((tenant_id)::text, (user_id)::text), seller_tax);
CREATE UNIQUE INDEX idx_corr_ex_unique ON public.ocr_correction_examples USING btree (COALESCE((tenant_id)::text, (user_id)::text), COALESCE(seller_tax, ''::text), field_name, COALESCE(ai_value, ''::text));

CREATE TABLE IF NOT EXISTS "ocr_cost_log" (
  "id" bigint DEFAULT nextval('ocr_cost_log_id_seq'::regclass) NOT NULL,
  "user_id" uuid NOT NULL,
  "tenant_id" uuid,
  "history_id" text,
  "engine" text DEFAULT 'gemini'::text NOT NULL,
  "pages" integer DEFAULT 1 NOT NULL,
  "input_tokens" integer DEFAULT 0,
  "output_tokens" integer DEFAULT 0,
  "cost_thb" numeric(10,4) DEFAULT 0 NOT NULL,
  "elapsed_ms" integer DEFAULT 0,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "model" text DEFAULT ''::text NOT NULL,
  "mode" text DEFAULT ''::text NOT NULL,
  "l3_fired" boolean DEFAULT false NOT NULL,
  "status" text DEFAULT 'ok'::text NOT NULL,
  CONSTRAINT "ocr_cost_log_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_cost_log_created ON public.ocr_cost_log USING btree (created_at DESC);
CREATE INDEX idx_cost_log_tenant ON public.ocr_cost_log USING btree (tenant_id, created_at DESC);
CREATE INDEX idx_cost_log_user ON public.ocr_cost_log USING btree (user_id, created_at DESC);

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
CREATE INDEX idx_ocr_history_archive ON public.ocr_history USING btree (user_id, archived_at DESC) WHERE (archive_name IS NOT NULL);
CREATE INDEX idx_ocr_history_client ON public.ocr_history USING btree (client_id) WHERE (client_id IS NOT NULL);
CREATE INDEX idx_ocr_history_hash ON public.ocr_history USING btree (user_id, file_hash, created_at DESC) WHERE (file_hash IS NOT NULL);
CREATE INDEX idx_ocr_history_invoice_no ON public.ocr_history USING btree (user_id, invoice_no) WHERE (invoice_no IS NOT NULL);
CREATE INDEX idx_ocr_history_pdf_storage ON public.ocr_history USING btree (pdf_storage_path) WHERE (pdf_storage_path IS NOT NULL);
CREATE INDEX idx_ocr_history_pushed ON public.ocr_history USING btree (user_id, last_push_status);
CREATE INDEX idx_ocr_history_seller ON public.ocr_history USING btree (user_id, seller_name) WHERE (seller_name IS NOT NULL);
CREATE INDEX idx_ocr_history_source ON public.ocr_history USING btree (user_id, source);
CREATE INDEX idx_ocr_history_source_pdf ON public.ocr_history USING btree (user_id, source_pdf_id) WHERE (source_pdf_id IS NOT NULL);
CREATE INDEX idx_ocr_history_storage ON public.ocr_history USING btree (user_id) WHERE (storage_path IS NOT NULL);
CREATE INDEX idx_ocr_history_tenant_id ON public.ocr_history USING btree (tenant_id);
CREATE INDEX idx_ocr_history_user_created ON public.ocr_history USING btree (user_id, created_at DESC);
CREATE INDEX idx_ocr_history_user_invno ON public.ocr_history USING btree (user_id, lower(invoice_no)) WHERE ((invoice_no IS NOT NULL) AND (invoice_no <> ''::text));
CREATE INDEX idx_ocr_history_user_signature ON public.ocr_history USING btree (user_id, invoice_date, total_amount) WHERE ((invoice_date IS NOT NULL) AND (total_amount IS NOT NULL));
CREATE INDEX idx_ocr_history_workspace ON public.ocr_history USING btree (workspace_client_id) WHERE (workspace_client_id IS NOT NULL);

CREATE TABLE IF NOT EXISTS "operation_logs" (
  "id" bigint DEFAULT nextval('operation_logs_id_seq'::regclass) NOT NULL,
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
CREATE INDEX idx_opl_action ON public.operation_logs USING btree (action, created_at DESC);
CREATE INDEX idx_opl_actor ON public.operation_logs USING btree (actor_user_id, created_at DESC);
CREATE INDEX idx_opl_tenant ON public.operation_logs USING btree (tenant_id, created_at DESC);

CREATE TABLE IF NOT EXISTS "ownership_transfers" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "from_user_id" uuid NOT NULL,
  "to_user_id" uuid NOT NULL,
  "token_hash" text NOT NULL,
  "expires_at" timestamp with time zone NOT NULL,
  "completed_at" timestamp with time zone,
  "cancelled_at" timestamp with time zone,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "ownership_transfers_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX uq_ownership_transfers_token ON public.ownership_transfers USING btree (token_hash);

CREATE TABLE IF NOT EXISTS "password_reset_log" (
  "id" bigint DEFAULT nextval('password_reset_log_id_seq'::regclass) NOT NULL,
  "token" text NOT NULL,
  "user_id" uuid NOT NULL,
  "email" text NOT NULL,
  "expires_at" timestamp with time zone NOT NULL,
  "used" boolean DEFAULT false,
  "used_at" timestamp with time zone,
  "requester_ip" text,
  "requester_fingerprint" text,
  "delivery_method" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "password_reset_log_pkey" PRIMARY KEY (id),
  CONSTRAINT "password_reset_log_token_key" UNIQUE (token)
);
CREATE INDEX idx_pwreset_email ON public.password_reset_log USING btree (email, created_at DESC);
CREATE INDEX idx_pwreset_token ON public.password_reset_log USING btree (token);
CREATE UNIQUE INDEX password_reset_log_token_key ON public.password_reset_log USING btree (token);

CREATE TABLE IF NOT EXISTS "payment_pending" (
  "id" bigint DEFAULT nextval('payment_pending_id_seq'::regclass) NOT NULL,
  "user_id" uuid NOT NULL,
  "target_plan" text NOT NULL,
  "amount_thb" numeric(10,2) NOT NULL,
  "screenshot_path" text,
  "payer_name" text,
  "payer_note" text,
  "status" text DEFAULT 'pending'::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "reviewed_at" timestamp with time zone,
  "reviewed_by" uuid,
  "review_note" text,
  CONSTRAINT "payment_pending_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_pay_pending_status ON public.payment_pending USING btree (status, created_at DESC);

CREATE TABLE IF NOT EXISTS "platform_setting_allowlist" (
  "setting_key" text NOT NULL,
  "user_id" uuid NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "platform_setting_allowlist_pkey" PRIMARY KEY (setting_key, user_id)
);
CREATE INDEX idx_psa_key ON public.platform_setting_allowlist USING btree (setting_key);

CREATE TABLE IF NOT EXISTS "platform_settings" (
  "key" text NOT NULL,
  "value" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "enabled" boolean DEFAULT false NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_by" uuid,
  CONSTRAINT "platform_settings_pkey" PRIMARY KEY (key)
);

CREATE TABLE IF NOT EXISTS "pos_areas" (
  "id" bigint DEFAULT nextval('pos_areas_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "name" text NOT NULL,
  "sort" integer DEFAULT 0 NOT NULL,
  "is_active" boolean DEFAULT true NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "pos_areas_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_pos_areas_ws ON public.pos_areas USING btree (tenant_id, workspace_client_id);

CREATE TABLE IF NOT EXISTS "pos_cashiers" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "user_id" uuid,
  "display_name" text NOT NULL,
  "pin_hash" text NOT NULL,
  "color" text,
  "is_active" boolean DEFAULT true NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "caps" jsonb DEFAULT '{}'::jsonb NOT NULL,
  CONSTRAINT "pos_cashiers_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_pos_cashiers_ws ON public.pos_cashiers USING btree (tenant_id, workspace_client_id);

CREATE TABLE IF NOT EXISTS "pos_entitlements" (
  "id" bigint DEFAULT nextval('pos_entitlements_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "grant_code" text NOT NULL,
  "amount_paid_thb" numeric(12,2) DEFAULT 0 NOT NULL,
  "purchased_at" timestamp with time zone DEFAULT now() NOT NULL,
  "store_limit" integer DEFAULT 1 NOT NULL,
  "cashier_limit" integer DEFAULT 3 NOT NULL,
  "status" text DEFAULT 'active'::text NOT NULL,
  "granted_by" uuid,
  "transferred_from" uuid,
  "transferred_to" uuid,
  "transferred_at" timestamp with time zone,
  "transferred_by" uuid,
  "revoked_at" timestamp with time zone,
  "revoked_by" uuid,
  "note" text,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "pos_entitlements_status_check" CHECK ((status = ANY (ARRAY['active'::text, 'revoked'::text, 'transferred'::text]))),
  CONSTRAINT "pos_entitlements_pkey" PRIMARY KEY (id),
  CONSTRAINT "pos_entitlements_tenant_id_key" UNIQUE (tenant_id)
);
CREATE UNIQUE INDEX pos_entitlements_tenant_id_key ON public.pos_entitlements USING btree (tenant_id);
CREATE UNIQUE INDEX uq_pos_entitlement_code ON public.pos_entitlements USING btree (grant_code);

CREATE TABLE IF NOT EXISTS "pos_kot" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "session_id" uuid NOT NULL,
  "ticket_no" integer NOT NULL,
  "sent_at" timestamp with time zone DEFAULT now() NOT NULL,
  "started_at" timestamp with time zone,
  "done_at" timestamp with time zone,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "pos_kot_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_pos_kot_ws_session ON public.pos_kot USING btree (tenant_id, workspace_client_id, session_id);

CREATE TABLE IF NOT EXISTS "pos_payment_settings" (
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "promptpay_enabled" boolean DEFAULT true NOT NULL,
  "card_enabled" boolean DEFAULT true NOT NULL,
  "service_charge_rate" numeric(6,2) DEFAULT 0 NOT NULL,
  "price_includes_vat" boolean DEFAULT true NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "bank_transfer_enabled" boolean DEFAULT false NOT NULL,
  "bank_name" text,
  "bank_account_no" text,
  "bank_account_name" text,
  CONSTRAINT "pos_payment_settings_pkey" PRIMARY KEY (tenant_id, workspace_client_id)
);

CREATE TABLE IF NOT EXISTS "pos_payments" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "sale_id" uuid NOT NULL,
  "method" text NOT NULL,
  "amount" numeric(14,2) NOT NULL,
  "ref" text,
  CONSTRAINT "pos_payments_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_pos_payments_sale ON public.pos_payments USING btree (sale_id);

CREATE TABLE IF NOT EXISTS "pos_sale_lines" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "sale_id" uuid NOT NULL,
  "product_id" uuid NOT NULL,
  "sell_unit" text,
  "unit_factor" numeric(14,3) DEFAULT 1 NOT NULL,
  "qty" numeric(14,3) NOT NULL,
  "qty_base" numeric(14,3) NOT NULL,
  "unit_price" numeric(14,2) NOT NULL,
  "line_discount" numeric(14,2) DEFAULT 0 NOT NULL,
  "vat_applicable" boolean DEFAULT true NOT NULL,
  "batch_id" uuid,
  "refund_of_line_id" uuid,
  "line_total" numeric(14,2) NOT NULL,
  "cost_total" numeric(14,2),
  CONSTRAINT "pos_sale_lines_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_pos_sale_lines_refund ON public.pos_sale_lines USING btree (refund_of_line_id);
CREATE INDEX ix_pos_sale_lines_sale ON public.pos_sale_lines USING btree (sale_id);

CREATE TABLE IF NOT EXISTS "pos_sales" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "client_uuid" uuid,
  "shift_id" uuid,
  "terminal_id" bigint,
  "cashier_id" uuid,
  "receipt_no" text,
  "doc_kind" text DEFAULT 'receipt'::text NOT NULL,
  "sale_type" text DEFAULT 'sale'::text NOT NULL,
  "refund_of_sale_id" uuid,
  "member_client_id" bigint,
  "subtotal" numeric(14,2) DEFAULT 0 NOT NULL,
  "discount_total" numeric(14,2) DEFAULT 0 NOT NULL,
  "vat_amount" numeric(14,2) DEFAULT 0 NOT NULL,
  "grand_total" numeric(14,2) DEFAULT 0 NOT NULL,
  "price_includes_vat" boolean DEFAULT false NOT NULL,
  "paid_total" numeric(14,2) DEFAULT 0 NOT NULL,
  "change_amount" numeric(14,2) DEFAULT 0 NOT NULL,
  "full_invoice_id" uuid,
  "status" text DEFAULT 'completed'::text NOT NULL,
  "sold_at" timestamp with time zone DEFAULT now() NOT NULL,
  "synced_at" timestamp with time zone,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "service_charge" numeric(14,2) DEFAULT 0 NOT NULL,
  CONSTRAINT "pos_sales_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_pos_sales_receipt ON public.pos_sales USING btree (tenant_id, receipt_no);
CREATE INDEX ix_pos_sales_shift ON public.pos_sales USING btree (tenant_id, workspace_client_id, shift_id);
CREATE INDEX ix_pos_sales_sold_at ON public.pos_sales USING btree (tenant_id, workspace_client_id, sold_at);
CREATE UNIQUE INDEX uq_pos_sales_client_uuid_scope ON public.pos_sales USING btree (tenant_id, workspace_client_id, client_uuid);

CREATE TABLE IF NOT EXISTS "pos_session_lines" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "session_id" uuid NOT NULL,
  "kot_id" uuid,
  "product_id" uuid NOT NULL,
  "sell_unit" text,
  "unit_factor" numeric(14,3) DEFAULT 1 NOT NULL,
  "qty" numeric(14,3) NOT NULL,
  "unit_price" numeric(14,2) NOT NULL,
  "line_discount" numeric(14,2) DEFAULT 0 NOT NULL,
  "vat_applicable" boolean DEFAULT true NOT NULL,
  "note" text,
  "kitchen_status" text DEFAULT 'pending'::text NOT NULL,
  "settled_sale_id" uuid,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "pos_session_lines_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_pos_session_lines_kot ON public.pos_session_lines USING btree (tenant_id, kot_id);
CREATE INDEX ix_pos_session_lines_session ON public.pos_session_lines USING btree (tenant_id, session_id);

CREATE TABLE IF NOT EXISTS "pos_sheets_settings" (
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "spreadsheet_id" text,
  "tab_name" text DEFAULT 'POS'::text NOT NULL,
  "enabled" boolean DEFAULT false NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "header_lang" text DEFAULT 'th'::text NOT NULL,
  CONSTRAINT "pos_sheets_settings_pkey" PRIMARY KEY (tenant_id, workspace_client_id)
);

CREATE TABLE IF NOT EXISTS "pos_shifts" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "terminal_id" bigint NOT NULL,
  "cashier_id" uuid NOT NULL,
  "opened_at" timestamp with time zone DEFAULT now() NOT NULL,
  "closed_at" timestamp with time zone,
  "opening_float" numeric(14,2) DEFAULT 0 NOT NULL,
  "expected_cash" numeric(14,2),
  "counted_cash" numeric(14,2),
  "cash_diff" numeric(14,2),
  "status" text DEFAULT 'open'::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "shift_seq" integer,
  CONSTRAINT "pos_shifts_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_pos_shifts_cashier ON public.pos_shifts USING btree (tenant_id, cashier_id, status);
CREATE UNIQUE INDEX uq_pos_shift_open ON public.pos_shifts USING btree (tenant_id, terminal_id) WHERE (status = 'open'::text);
CREATE UNIQUE INDEX uq_pos_shift_seq ON public.pos_shifts USING btree (tenant_id, workspace_client_id, shift_seq);

CREATE TABLE IF NOT EXISTS "pos_store_codes" (
  "id" bigint DEFAULT nextval('pos_store_codes_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "code" text NOT NULL,
  "token_version" integer DEFAULT 1 NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "pos_store_codes_pkey" PRIMARY KEY (id),
  CONSTRAINT "pos_store_codes_tenant_id_workspace_client_id_key" UNIQUE (tenant_id, workspace_client_id)
);
CREATE UNIQUE INDEX pos_store_codes_tenant_id_workspace_client_id_key ON public.pos_store_codes USING btree (tenant_id, workspace_client_id);
CREATE UNIQUE INDEX uq_pos_store_code ON public.pos_store_codes USING btree (code);

CREATE TABLE IF NOT EXISTS "pos_table_sessions" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "table_id" bigint NOT NULL,
  "service_type" text DEFAULT 'dine_in'::text NOT NULL,
  "party_size" integer DEFAULT 1 NOT NULL,
  "status" text DEFAULT 'open'::text NOT NULL,
  "opened_at" timestamp with time zone DEFAULT now() NOT NULL,
  "closed_at" timestamp with time zone,
  "cashier_id" uuid,
  "note" text,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "pos_table_sessions_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_pos_sessions_ws_status ON public.pos_table_sessions USING btree (tenant_id, workspace_client_id, status);
CREATE UNIQUE INDEX uq_table_open ON public.pos_table_sessions USING btree (tenant_id, table_id) WHERE (status <> 'closed'::text);

CREATE TABLE IF NOT EXISTS "pos_tables" (
  "id" bigint DEFAULT nextval('pos_tables_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "area_id" bigint,
  "name" text NOT NULL,
  "seats" integer DEFAULT 4 NOT NULL,
  "sort" integer DEFAULT 0 NOT NULL,
  "is_active" boolean DEFAULT true NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "pos_tables_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX uq_pos_tables_name ON public.pos_tables USING btree (tenant_id, workspace_client_id, name);

CREATE TABLE IF NOT EXISTS "pos_terminals" (
  "id" bigint DEFAULT nextval('pos_terminals_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "name" text DEFAULT 'แคชเชียร์ 1'::text NOT NULL,
  "is_active" boolean DEFAULT true NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "pos_terminals_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_pos_terminals_ws ON public.pos_terminals USING btree (tenant_id, workspace_client_id);

CREATE TABLE IF NOT EXISTS "product_units" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "product_id" uuid NOT NULL,
  "unit_name" text NOT NULL,
  "factor_to_base" numeric(14,3) NOT NULL,
  "barcode" text,
  "price" numeric(14,2),
  "is_default_sell" boolean DEFAULT false NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "workspace_client_id" bigint,
  CONSTRAINT "product_units_pkey" PRIMARY KEY (id),
  CONSTRAINT "product_units_tenant_id_product_id_unit_name_key" UNIQUE (tenant_id, product_id, unit_name)
);
CREATE INDEX ix_product_units_product ON public.product_units USING btree (tenant_id, product_id);
CREATE INDEX ix_product_units_ws ON public.product_units USING btree (tenant_id, workspace_client_id);
CREATE UNIQUE INDEX product_units_tenant_id_product_id_unit_name_key ON public.product_units USING btree (tenant_id, product_id, unit_name);

CREATE TABLE IF NOT EXISTS "products" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "code" text,
  "barcode" text,
  "qr_payload" text,
  "name_th" text NOT NULL,
  "name_en" text,
  "name_zh" text,
  "unit" text,
  "unit_price" numeric(14,2) DEFAULT 0 NOT NULL,
  "vat_applicable" boolean DEFAULT true NOT NULL,
  "image_url" text,
  "category_id" bigint,
  "is_active" boolean DEFAULT true NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "base_unit" text DEFAULT 'ชิ้น'::text NOT NULL,
  "track_batch" boolean DEFAULT false NOT NULL,
  "track_expiry" boolean DEFAULT false NOT NULL,
  "is_weighed" boolean DEFAULT false NOT NULL,
  "min_stock" numeric(14,3),
  "default_cost" numeric(14,2),
  "workspace_client_id" bigint,
  CONSTRAINT "products_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_products_barcode ON public.products USING btree (tenant_id, barcode) WHERE (barcode IS NOT NULL);
CREATE INDEX idx_products_tenant ON public.products USING btree (tenant_id, is_active);
CREATE INDEX ix_products_ws ON public.products USING btree (tenant_id, workspace_client_id);
CREATE UNIQUE INDEX uq_products_tenant_code ON public.products USING btree (tenant_id, code) WHERE (code IS NOT NULL);

CREATE TABLE IF NOT EXISTS "purchase_attachments" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "purchase_doc_id" uuid NOT NULL,
  "kind" text NOT NULL,
  "url" text,
  "generated" boolean DEFAULT false NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "purchase_attachments_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_purchase_attachments_doc ON public.purchase_attachments USING btree (tenant_id, purchase_doc_id);

CREATE TABLE IF NOT EXISTS "purchase_docs" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "doc_kind" text NOT NULL,
  "supplier_id" uuid,
  "doc_no" text,
  "doc_date" date,
  "has_vat" boolean DEFAULT false NOT NULL,
  "currency" text DEFAULT 'THB'::text NOT NULL,
  "fx_rate" numeric(14,6) DEFAULT 1 NOT NULL,
  "subtotal" numeric(14,2) DEFAULT 0 NOT NULL,
  "discount_total" numeric(14,2) DEFAULT 0 NOT NULL,
  "vat_amount" numeric(14,2) DEFAULT 0 NOT NULL,
  "wht_amount" numeric(14,2) DEFAULT 0 NOT NULL,
  "rounding" numeric(14,2) DEFAULT 0 NOT NULL,
  "grand_total" numeric(14,2) DEFAULT 0 NOT NULL,
  "net_payable" numeric(14,2) DEFAULT 0 NOT NULL,
  "category_id" uuid,
  "requester" text,
  "requester_user_id" uuid,
  "approval_status" text DEFAULT 'none'::text NOT NULL,
  "payment_status" text DEFAULT 'unpaid'::text NOT NULL,
  "paid_amount" numeric(14,2) DEFAULT 0 NOT NULL,
  "due_date" date,
  "source" text,
  "ocr_raw" jsonb,
  "dedupe_key" text,
  "status" text DEFAULT 'draft'::text NOT NULL,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "amount_override" boolean DEFAULT false NOT NULL,
  "payment_method" text,
  "image_sha256" text,
  CONSTRAINT "purchase_docs_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_purchase_docs_image_sha ON public.purchase_docs USING btree (tenant_id, workspace_client_id, image_sha256) WHERE (image_sha256 IS NOT NULL);
CREATE INDEX ix_purchase_docs_ws ON public.purchase_docs USING btree (tenant_id, workspace_client_id);
CREATE UNIQUE INDEX uq_purchase_docs_dedupe ON public.purchase_docs USING btree (tenant_id, workspace_client_id, dedupe_key) WHERE (dedupe_key IS NOT NULL);

CREATE TABLE IF NOT EXISTS "purchase_lines" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "purchase_doc_id" uuid NOT NULL,
  "line_no" integer DEFAULT 1 NOT NULL,
  "item_type" text DEFAULT 'goods'::text NOT NULL,
  "product_id" uuid,
  "description" text,
  "qty" numeric(14,3) DEFAULT 0 NOT NULL,
  "unit" text,
  "unit_price" numeric(14,2) DEFAULT 0 NOT NULL,
  "discount" numeric(14,2) DEFAULT 0 NOT NULL,
  "line_total" numeric(14,2) DEFAULT 0 NOT NULL,
  "vat_rate" numeric(5,2) DEFAULT 7 NOT NULL,
  "vat_applicable" boolean DEFAULT true NOT NULL,
  "wht_rate" numeric(5,2) DEFAULT 0 NOT NULL,
  "category_id" uuid,
  "subcategory_id" uuid,
  "batch_no" text,
  "expiry_date" date,
  CONSTRAINT "purchase_lines_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_purchase_lines_doc ON public.purchase_lines USING btree (tenant_id, purchase_doc_id);

CREATE TABLE IF NOT EXISTS "purchase_settings" (
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "default_vat_rate" numeric(5,2) DEFAULT 7 NOT NULL,
  "auto_stock_in" boolean DEFAULT false NOT NULL,
  "dedupe_block" boolean DEFAULT true NOT NULL,
  "default_due_days" integer DEFAULT 0 NOT NULL,
  "pay_needs_approval" boolean DEFAULT false NOT NULL,
  "default_wht_service_rate" numeric(5,2) DEFAULT 3 NOT NULL,
  "base_currency" text DEFAULT 'THB'::text NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "auto_book" boolean DEFAULT true NOT NULL,
  CONSTRAINT "purchase_settings_pkey" PRIMARY KEY (tenant_id, workspace_client_id)
);

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
CREATE INDEX idx_rd_cache_expires ON public.rd_cache USING btree (expires_at);

CREATE TABLE IF NOT EXISTS "rd_daily_usage" (
  "user_id" uuid NOT NULL,
  "day" date NOT NULL,
  "count" integer DEFAULT 0 NOT NULL,
  "tenant_id" uuid,
  CONSTRAINT "rd_daily_usage_pkey" PRIMARY KEY (user_id, day)
);
CREATE INDEX idx_rd_daily_usage_day ON public.rd_daily_usage USING btree (day);
CREATE INDEX idx_rd_daily_usage_tenant_id ON public.rd_daily_usage USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "recon_jobs" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "job_type" text NOT NULL,
  "user_id" uuid NOT NULL,
  "tenant_id" uuid,
  "status" text DEFAULT 'queued'::text NOT NULL,
  "progress" jsonb,
  "params" jsonb,
  "input_ref" jsonb,
  "result_table" text,
  "result_id" text,
  "error_code" text,
  "attempts" integer DEFAULT 0 NOT NULL,
  "max_attempts" integer DEFAULT 1 NOT NULL,
  "worker_id" text,
  "lease_until" timestamp with time zone,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "started_at" timestamp with time zone,
  "finished_at" timestamp with time zone,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "workspace_client_id" bigint,
  CONSTRAINT "recon_jobs_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_recon_jobs_status_created ON public.recon_jobs USING btree (status, created_at);
CREATE INDEX idx_recon_jobs_tenant_created ON public.recon_jobs USING btree (tenant_id, created_at DESC) WHERE (tenant_id IS NOT NULL);
CREATE INDEX idx_recon_jobs_user_created ON public.recon_jobs USING btree (user_id, created_at DESC);
CREATE INDEX ix_recon_jobs_ws ON public.recon_jobs USING btree (tenant_id, workspace_client_id);

CREATE TABLE IF NOT EXISTS "reconciliation_row" (
  "id" bigint DEFAULT nextval('reconciliation_row_id_seq'::regclass) NOT NULL,
  "task_id" bigint NOT NULL,
  "invoice_id" uuid,
  "report_row_no" integer,
  "pair_confidence" real,
  "status" text DEFAULT 'pending'::text NOT NULL,
  "diff_fields" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "diff_categories" text,
  "ai_analysis" text,
  "accountant_action" text DEFAULT 'pending'::text NOT NULL,
  "notes" text,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "field_overrides" jsonb,
  CONSTRAINT "reconciliation_row_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_recon_row_invoice ON public.reconciliation_row USING btree (invoice_id) WHERE (invoice_id IS NOT NULL);
CREATE INDEX idx_recon_row_task ON public.reconciliation_row USING btree (task_id);
CREATE INDEX idx_recon_row_task_status ON public.reconciliation_row USING btree (task_id, status);

CREATE TABLE IF NOT EXISTS "reconciliation_task" (
  "id" bigint DEFAULT nextval('reconciliation_task_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid,
  "user_id" uuid NOT NULL,
  "client_id" bigint,
  "period_year" integer NOT NULL,
  "period_month" integer NOT NULL,
  "vat_report_id" bigint,
  "invoice_count_archived" integer DEFAULT 0 NOT NULL,
  "invoice_count_supplement" integer DEFAULT 0 NOT NULL,
  "report_row_count" integer DEFAULT 0 NOT NULL,
  "status" text DEFAULT 'created'::text NOT NULL,
  "matched_count" integer DEFAULT 0 NOT NULL,
  "mismatched_count" integer DEFAULT 0 NOT NULL,
  "invoice_orphan_count" integer DEFAULT 0 NOT NULL,
  "report_orphan_count" integer DEFAULT 0 NOT NULL,
  "confidence_score" real,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "completed_at" timestamp with time zone,
  CONSTRAINT "reconciliation_task_period_month_check" CHECK (((period_month >= 1) AND (period_month <= 12))),
  CONSTRAINT "reconciliation_task_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_recon_task_client_period ON public.reconciliation_task USING btree (client_id, period_year, period_month);
CREATE INDEX idx_recon_task_status ON public.reconciliation_task USING btree (status);
CREATE INDEX idx_recon_task_tenant ON public.reconciliation_task USING btree (tenant_id) WHERE (tenant_id IS NOT NULL);
CREATE UNIQUE INDEX idx_recon_task_unique_period ON public.reconciliation_task USING btree (client_id, period_year, period_month) WHERE (status <> 'failed'::text);
CREATE INDEX idx_recon_task_user ON public.reconciliation_task USING btree (user_id);

CREATE TABLE IF NOT EXISTS "review_learned" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "scope_key" text NOT NULL,
  "decision" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "review_learned_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX uq_review_learned_scope ON public.review_learned USING btree (tenant_id, workspace_client_id, scope_key);

CREATE TABLE IF NOT EXISTS "risk_log" (
  "id" bigint DEFAULT nextval('risk_log_id_seq'::regclass) NOT NULL,
  "user_id" uuid,
  "event_type" text NOT NULL,
  "ip" text,
  "fingerprint" text,
  "detail" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "risk_log_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_risk_log_event ON public.risk_log USING btree (event_type, created_at DESC);

CREATE TABLE IF NOT EXISTS "roles" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "name" text NOT NULL,
  "permissions" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "is_system" boolean DEFAULT false NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "tenant_id" uuid,
  "key" text,
  "display_name" text,
  "is_active" boolean DEFAULT true NOT NULL,
  "version" integer DEFAULT 0 NOT NULL,
  "created_by" uuid,
  CONSTRAINT "roles_pkey" PRIMARY KEY (id),
  CONSTRAINT "roles_name_key" UNIQUE (name)
);
CREATE UNIQUE INDEX roles_name_key ON public.roles USING btree (name);
CREATE UNIQUE INDEX uq_roles_system_key ON public.roles USING btree (key) WHERE (tenant_id IS NULL);
CREATE UNIQUE INDEX uq_roles_tenant_key ON public.roles USING btree (tenant_id, key) WHERE (tenant_id IS NOT NULL);

CREATE TABLE IF NOT EXISTS "sales_document_lines" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "document_id" uuid NOT NULL,
  "line_no" integer NOT NULL,
  "product_id" uuid,
  "description" text NOT NULL,
  "qty" numeric(14,3) DEFAULT 1 NOT NULL,
  "unit_price" numeric(14,2) DEFAULT 0 NOT NULL,
  "discount" numeric(14,2) DEFAULT 0 NOT NULL,
  "vat_applicable" boolean DEFAULT true NOT NULL,
  "line_total" numeric(14,2) DEFAULT 0 NOT NULL,
  "discount_pct" numeric(5,2),
  CONSTRAINT "sales_document_lines_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_sales_lines_doc ON public.sales_document_lines USING btree (document_id, line_no);
CREATE INDEX idx_sales_lines_tenant ON public.sales_document_lines USING btree (tenant_id);

CREATE TABLE IF NOT EXISTS "sales_document_sends" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "document_id" uuid NOT NULL,
  "channel" text NOT NULL,
  "identity" text NOT NULL,
  "recipient" text,
  "status" text DEFAULT 'sent'::text NOT NULL,
  "error" text,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "sales_document_sends_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_sales_sends_doc ON public.sales_document_sends USING btree (tenant_id, document_id, created_at DESC);

CREATE TABLE IF NOT EXISTS "sales_documents" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "doc_type" text NOT NULL,
  "doc_number" text,
  "client_id" bigint,
  "issue_date" date,
  "status" text DEFAULT 'draft'::text NOT NULL,
  "currency" text DEFAULT 'THB'::text NOT NULL,
  "subtotal" numeric(14,2) DEFAULT 0 NOT NULL,
  "discount_total" numeric(14,2) DEFAULT 0 NOT NULL,
  "vat_rate" numeric(5,2) DEFAULT 7.00 NOT NULL,
  "vat_amount" numeric(14,2) DEFAULT 0 NOT NULL,
  "wht_amount" numeric(14,2) DEFAULT 0 NOT NULL,
  "grand_total" numeric(14,2) DEFAULT 0 NOT NULL,
  "issued_at" timestamp with time zone,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "references_document_id" uuid,
  "reference_reason" text,
  "seller_workspace_client_id" bigint,
  "buyer_type" text,
  "buyer_name" text,
  "buyer_address" text,
  "buyer_tax_id" text,
  "buyer_branch_type" text,
  "buyer_branch_no" text,
  "parties_snapshot" jsonb,
  "payment_status" text DEFAULT 'unpaid'::text NOT NULL,
  "paid_amount" numeric(14,2) DEFAULT 0 NOT NULL,
  "payment_method" text,
  "payment_date" date,
  "header_discount_amount" numeric(14,2) DEFAULT 0 NOT NULL,
  "header_discount_pct" numeric(5,2),
  "due_date" date,
  "payment_terms" text,
  "price_includes_vat" boolean DEFAULT false NOT NULL,
  "approved_by" text,
  "approved_at" timestamp with time zone,
  "rejected_reason" text,
  "pdf_sha256" text,
  "pdf_url" text,
  "wht_rate" numeric(6,2),
  "share_token" text,
  "copies_layout" text DEFAULT 'separate'::text NOT NULL,
  "paper_size" text DEFAULT 'A4'::text NOT NULL,
  "doc_language" text DEFAULT 'th_en'::text NOT NULL,
  "workspace_client_id" bigint,
  CONSTRAINT "sales_documents_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_sales_docs_client ON public.sales_documents USING btree (tenant_id, client_id);
CREATE INDEX idx_sales_docs_references ON public.sales_documents USING btree (tenant_id, references_document_id) WHERE (references_document_id IS NOT NULL);
CREATE INDEX idx_sales_docs_seller ON public.sales_documents USING btree (tenant_id, seller_workspace_client_id) WHERE (seller_workspace_client_id IS NOT NULL);
CREATE INDEX idx_sales_docs_tenant_status ON public.sales_documents USING btree (tenant_id, status, issue_date DESC);
CREATE INDEX ix_sales_documents_ws ON public.sales_documents USING btree (tenant_id, workspace_client_id);
CREATE UNIQUE INDEX uq_sales_doc_number ON public.sales_documents USING btree (tenant_id, doc_type, doc_number) WHERE (doc_number IS NOT NULL);
CREATE UNIQUE INDEX uq_sales_doc_share_token ON public.sales_documents USING btree (share_token) WHERE (share_token IS NOT NULL);

CREATE TABLE IF NOT EXISTS "sales_settings" (
  "tenant_id" uuid NOT NULL,
  "number_prefix" text,
  "number_reset" text DEFAULT 'yearly'::text NOT NULL,
  "number_start" bigint DEFAULT 1 NOT NULL,
  "approval_mode" text DEFAULT 'none'::text NOT NULL,
  "price_includes_vat_default" boolean DEFAULT false NOT NULL,
  "default_wht_rate" numeric(6,2) DEFAULT 0 NOT NULL,
  "default_template_id" text DEFAULT 'classic'::text NOT NULL,
  "default_doc_lang" text DEFAULT 'th'::text NOT NULL,
  "default_paper" text DEFAULT 'A4'::text NOT NULL,
  "default_copies_layout" text DEFAULT 'separate'::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "sales_settings_pkey" PRIMARY KEY (tenant_id)
);

CREATE TABLE IF NOT EXISTS "seller_workspace_routes" (
  "id" bigint DEFAULT nextval('seller_workspace_routes_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid,
  "user_id" uuid NOT NULL,
  "seller_tax" text,
  "seller_name" text,
  "workspace_client_id" bigint NOT NULL,
  "use_count" integer DEFAULT 1 NOT NULL,
  "last_used_at" timestamp with time zone DEFAULT now() NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "seller_workspace_routes_pkey" PRIMARY KEY (id)
);
CREATE INDEX seller_route_tax_idx ON public.seller_workspace_routes USING btree (seller_tax) WHERE ((seller_tax IS NOT NULL) AND (length(seller_tax) >= 10));
CREATE UNIQUE INDEX seller_route_unique_scope ON public.seller_workspace_routes USING btree (COALESCE((tenant_id)::text, (user_id)::text), COALESCE(seller_tax, ''::text), lower(COALESCE(seller_name, ''::text)));

CREATE TABLE IF NOT EXISTS "shadow_money_log" (
  "id" bigint DEFAULT nextval('shadow_money_log_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "history_id" text NOT NULL,
  "b_total" numeric,
  "s_total" numeric,
  "total_match" boolean,
  "b_vat" numeric,
  "s_vat" numeric,
  "vat_match" boolean,
  "b_discount" numeric,
  "s_discount" numeric,
  "discount_match" boolean,
  "b_subtotal" numeric,
  "s_subtotal" numeric,
  "subtotal_match" boolean,
  "match_all" boolean,
  "b_confidence" text,
  "status" text DEFAULT 'ok'::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "shadow_money_log_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_shadow_money_created ON public.shadow_money_log USING btree (created_at);

CREATE TABLE IF NOT EXISTS "steward_attachments" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "session_id" uuid NOT NULL,
  "message_id" uuid,
  "user_id" text NOT NULL,
  "original_name" text DEFAULT ''::text NOT NULL,
  "file_ref" text DEFAULT ''::text NOT NULL,
  "size_bytes" bigint DEFAULT 0 NOT NULL,
  "sha256" text DEFAULT ''::text NOT NULL,
  "mime" text DEFAULT ''::text NOT NULL,
  "kind" text DEFAULT 'unknown'::text NOT NULL,
  "kind_source" text DEFAULT 'unknown'::text NOT NULL,
  "kind_reason" text DEFAULT ''::text NOT NULL,
  "detect" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "status" text DEFAULT 'ready'::text NOT NULL,
  "promoted_to" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "expires_at" timestamp with time zone DEFAULT (now() + '30 days'::interval) NOT NULL,
  CONSTRAINT "steward_attachments_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_steward_attachments_expiry ON public.steward_attachments USING btree (expires_at);
CREATE INDEX ix_steward_attachments_session ON public.steward_attachments USING btree (tenant_id, session_id, created_at);

CREATE TABLE IF NOT EXISTS "steward_cost_entries" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "session_id" uuid NOT NULL,
  "task_id" uuid,
  "cost_thb" numeric(12,6) DEFAULT 0 NOT NULL,
  "settled" boolean DEFAULT false NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "steward_cost_entries_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_steward_cost_entries_session ON public.steward_cost_entries USING btree (tenant_id, session_id);
CREATE INDEX ix_steward_cost_entries_tenant_day ON public.steward_cost_entries USING btree (tenant_id, created_at);

CREATE TABLE IF NOT EXISTS "steward_messages" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "session_id" uuid NOT NULL,
  "role" text NOT NULL,
  "text" text DEFAULT ''::text NOT NULL,
  "tool_trace" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "task_id" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "steward_messages_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_steward_messages_session ON public.steward_messages USING btree (tenant_id, session_id, created_at);

CREATE TABLE IF NOT EXISTS "steward_sessions" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "user_id" text NOT NULL,
  "title" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "last_active_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "steward_sessions_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_steward_sessions_tenant ON public.steward_sessions USING btree (tenant_id, last_active_at DESC);

CREATE TABLE IF NOT EXISTS "steward_tasks" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "session_id" uuid,
  "title" text DEFAULT ''::text NOT NULL,
  "status" text DEFAULT 'running'::text NOT NULL,
  "steps" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "artifacts" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "payload" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "timeout_s" integer DEFAULT 300 NOT NULL,
  "worker_id" text,
  "lease_until" timestamp with time zone,
  "error_code" text,
  "error_message" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "finished_at" timestamp with time zone,
  CONSTRAINT "steward_tasks_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_steward_tasks_active ON public.steward_tasks USING btree (created_at) WHERE (status = 'running'::text);
CREATE INDEX ix_steward_tasks_session ON public.steward_tasks USING btree (tenant_id, session_id, created_at DESC);

CREATE TABLE IF NOT EXISTS "subscription_log" (
  "id" bigint DEFAULT nextval('subscription_log_id_seq'::regclass) NOT NULL,
  "user_id" uuid NOT NULL,
  "from_plan" text,
  "to_plan" text NOT NULL,
  "changed_at" timestamp with time zone DEFAULT now() NOT NULL,
  "changed_by" uuid,
  "reason" text,
  "amount_thb" numeric(10,2),
  "note" text,
  CONSTRAINT "subscription_log_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_sub_log_user ON public.subscription_log USING btree (user_id, changed_at DESC);

CREATE TABLE IF NOT EXISTS "supplier_categories" (
  "id" bigint DEFAULT nextval('supplier_categories_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid,
  "user_id" uuid NOT NULL,
  "seller_name" text NOT NULL,
  "category" text NOT NULL,
  "use_count" integer DEFAULT 1 NOT NULL,
  "last_used_at" timestamp with time zone DEFAULT now() NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "supplier_categories_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_supcat_tenant ON public.supplier_categories USING btree (tenant_id) WHERE (tenant_id IS NOT NULL);
CREATE UNIQUE INDEX idx_supcat_unique ON public.supplier_categories USING btree (COALESCE((tenant_id)::text, (user_id)::text), lower(seller_name));
CREATE INDEX idx_supcat_user ON public.supplier_categories USING btree (user_id);

CREATE TABLE IF NOT EXISTS "supplier_client_mapping" (
  "id" bigint DEFAULT nextval('supplier_client_mapping_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "supplier_name" text DEFAULT ''::text NOT NULL,
  "supplier_tax_id" text,
  "client_id" bigint NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "supplier_client_mapping_pkey" PRIMARY KEY (id),
  CONSTRAINT "supplier_client_mapping_tenant_id_supplier_name_key" UNIQUE (tenant_id, supplier_name)
);
CREATE INDEX idx_scm_tenant_tax ON public.supplier_client_mapping USING btree (tenant_id, supplier_tax_id) WHERE (supplier_tax_id IS NOT NULL);
CREATE UNIQUE INDEX supplier_client_mapping_tenant_id_supplier_name_key ON public.supplier_client_mapping USING btree (tenant_id, supplier_name);

CREATE TABLE IF NOT EXISTS "supplier_posting_profiles" (
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "seller_tax_id" text NOT NULL,
  "default_payment" text DEFAULT ''::text NOT NULL,
  "default_item_type" text DEFAULT ''::text NOT NULL,
  "default_category_id" uuid,
  "default_erp_account" text,
  "source" text DEFAULT ''::text NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "supplier_posting_profiles_pkey" PRIMARY KEY (tenant_id, workspace_client_id, seller_tax_id)
);
CREATE INDEX ix_supplier_posting_profiles_ws ON public.supplier_posting_profiles USING btree (tenant_id, workspace_client_id);

CREATE TABLE IF NOT EXISTS "suppliers" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "name" text NOT NULL,
  "tax_id" text,
  "branch_type" text DEFAULT 'none'::text NOT NULL,
  "branch_no" text,
  "address" text,
  "phone" text,
  "note" text,
  "is_active" boolean DEFAULT true NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "suppliers_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_suppliers_ws ON public.suppliers USING btree (tenant_id, workspace_client_id);
CREATE UNIQUE INDEX uq_suppliers_taxid ON public.suppliers USING btree (tenant_id, workspace_client_id, tax_id) WHERE (tax_id IS NOT NULL);

CREATE TABLE IF NOT EXISTS "tax_filings" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "period" text NOT NULL,
  "kind" text NOT NULL,
  "status" text DEFAULT 'prepared'::text NOT NULL,
  "net_amount" numeric(14,2) DEFAULT 0 NOT NULL,
  "breakdown" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "anomalies" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "due_date" date,
  "filed_method" text,
  "receipt_no" text,
  "filed_at" timestamp with time zone,
  "filed_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "tax_filings_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX uq_tax_filings_period_kind ON public.tax_filings USING btree (tenant_id, workspace_client_id, period, kind);

CREATE TABLE IF NOT EXISTS "tax_obligation_defs" (
  "obligation_code" text NOT NULL,
  "display_names" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "trigger_kind" text NOT NULL,
  "due_paper_day" smallint,
  "due_efiling_day" smallint,
  "sso_epayment_extra_workdays" smallint DEFAULT 0 NOT NULL,
  "evidence_level" text DEFAULT ''::text NOT NULL,
  "note" text DEFAULT ''::text NOT NULL,
  "effective_from" date DEFAULT '2024-02-01'::date NOT NULL,
  "effective_to" date,
  "version" integer DEFAULT 1 NOT NULL,
  CONSTRAINT "tax_obligation_defs_pkey" PRIMARY KEY (obligation_code)
);

CREATE TABLE IF NOT EXISTS "tax_settings" (
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "vat_registered" boolean DEFAULT true NOT NULL,
  "branch_type" text DEFAULT 'main'::text NOT NULL,
  "branch_no" text,
  "efiling_connected" boolean DEFAULT false NOT NULL,
  "efiling_credential_ref" text,
  "remind_days_before" integer DEFAULT 3 NOT NULL,
  "file_zero" boolean DEFAULT true NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "tax_settings_pkey" PRIMARY KEY (tenant_id, workspace_client_id)
);

CREATE TABLE IF NOT EXISTS "tenant_credits" (
  "tenant_id" uuid NOT NULL,
  "balance_thb" numeric(12,2) DEFAULT 0 NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now(),
  "low_balance_notified_at" timestamp with time zone,
  CONSTRAINT "tenant_credits_pkey" PRIMARY KEY (tenant_id)
);

CREATE TABLE IF NOT EXISTS "tenant_modules" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "module_key" text NOT NULL,
  "enabled" boolean DEFAULT false NOT NULL,
  "config" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "tenant_modules_pkey" PRIMARY KEY (id),
  CONSTRAINT "tenant_modules_tenant_id_module_key_key" UNIQUE (tenant_id, module_key)
);
CREATE INDEX ix_tenant_modules_tenant ON public.tenant_modules USING btree (tenant_id);
CREATE UNIQUE INDEX tenant_modules_tenant_id_module_key_key ON public.tenant_modules USING btree (tenant_id, module_key);

CREATE TABLE IF NOT EXISTS "tenant_subscriptions" (
  "tenant_id" uuid NOT NULL,
  "plan_code" text NOT NULL,
  "status" text DEFAULT 'active'::text NOT NULL,
  "cycle_start" timestamp with time zone DEFAULT now() NOT NULL,
  "cycle_end" timestamp with time zone NOT NULL,
  "quota" integer NOT NULL,
  "over_rate" numeric(12,2) NOT NULL,
  "monthly_fee" numeric(12,2) NOT NULL,
  "pages_used_this_cycle" integer DEFAULT 0 NOT NULL,
  "auto_renew" boolean DEFAULT true NOT NULL,
  "created_at" timestamp with time zone DEFAULT now(),
  "updated_at" timestamp with time zone DEFAULT now(),
  CONSTRAINT "tenant_subscriptions_plan_code_check" CHECK ((plan_code = ANY (ARRAY['S'::text, 'M'::text, 'L'::text]))),
  CONSTRAINT "tenant_subscriptions_status_check" CHECK ((status = ANY (ARRAY['active'::text, 'cancelled'::text]))),
  CONSTRAINT "tenant_subscriptions_pkey" PRIMARY KEY (tenant_id)
);

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
CREATE INDEX idx_tenants_owner ON public.tenants USING btree (owner_user_id);
CREATE INDEX idx_tenants_parent ON public.tenants USING btree (parent_tenant_id);
CREATE INDEX idx_tenants_status ON public.tenants USING btree (status);

CREATE TABLE IF NOT EXISTS "topup_requests" (
  "id" integer DEFAULT nextval('topup_requests_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "requested_by" uuid NOT NULL,
  "amount_thb" numeric(12,2) NOT NULL,
  "slip_path" text,
  "payer_name" text,
  "note" text,
  "status" text DEFAULT 'pending'::text NOT NULL,
  "reviewed_by" uuid,
  "reviewed_at" timestamp with time zone,
  "review_note" text,
  "created_at" timestamp with time zone DEFAULT now(),
  CONSTRAINT "topup_requests_status_check" CHECK ((status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text]))),
  CONSTRAINT "topup_requests_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS "user_company_roles" (
  "id" integer DEFAULT nextval('user_company_roles_id_seq'::regclass) NOT NULL,
  "user_id" uuid NOT NULL,
  "tenant_id" uuid NOT NULL,
  "role" text NOT NULL,
  "is_active" boolean DEFAULT true,
  "joined_at" timestamp with time zone DEFAULT now(),
  CONSTRAINT "user_company_roles_role_check" CHECK ((role = ANY (ARRAY['admin'::text, 'member'::text]))),
  CONSTRAINT "user_company_roles_pkey" PRIMARY KEY (id),
  CONSTRAINT "user_company_roles_user_id_tenant_id_key" UNIQUE (user_id, tenant_id)
);
CREATE INDEX idx_ucr_tenant ON public.user_company_roles USING btree (tenant_id);
CREATE INDEX idx_ucr_user ON public.user_company_roles USING btree (user_id);
CREATE UNIQUE INDEX user_company_roles_user_id_tenant_id_key ON public.user_company_roles USING btree (user_id, tenant_id);

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
CREATE INDEX idx_user_settings_tenant_id ON public.user_settings USING btree (tenant_id);

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
CREATE INDEX idx_users_email_norm ON public.users USING btree (email_normalized);
CREATE INDEX idx_users_fingerprint ON public.users USING btree (signup_fingerprint, created_at DESC);
CREATE INDEX idx_users_google_sub ON public.users USING btree (google_sub) WHERE (google_sub IS NOT NULL);
CREATE INDEX idx_users_line_uid ON public.users USING btree (line_uid) WHERE (line_uid IS NOT NULL);
CREATE INDEX idx_users_line_user_id ON public.users USING btree (line_user_id);
CREATE INDEX idx_users_plan ON public.users USING btree (plan);
CREATE INDEX idx_users_signup_ip ON public.users USING btree (signup_ip, created_at DESC);
CREATE INDEX idx_users_signup_source ON public.users USING btree (signup_source, created_at DESC);
CREATE INDEX idx_users_signup_subnet ON public.users USING btree (signup_ip_subnet, created_at DESC);
CREATE INDEX idx_users_tenant_id ON public.users USING btree (tenant_id);
CREATE INDEX idx_users_username ON public.users USING btree (username);
CREATE UNIQUE INDEX uq_users_username_lower ON public.users USING btree (lower(username));
CREATE UNIQUE INDEX users_username_key ON public.users USING btree (username);

CREATE TABLE IF NOT EXISTS "vat_recon_tasks" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid,
  "user_id" uuid NOT NULL,
  "client_name" text,
  "period" text,
  "invoice_count" integer DEFAULT 0 NOT NULL,
  "report_count" integer DEFAULT 0 NOT NULL,
  "matched" integer DEFAULT 0 NOT NULL,
  "mismatched" integer DEFAULT 0 NOT NULL,
  "mismatch_amount" numeric(18,2) DEFAULT 0 NOT NULL,
  "status" text DEFAULT 'done'::text NOT NULL,
  "elapsed_seconds" numeric(8,2),
  "excel_path" text,
  "raw_data_json" jsonb,
  "lang" text DEFAULT 'th'::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "workspace_client_id" bigint,
  CONSTRAINT "vat_recon_tasks_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_vrt_tenant_created ON public.vat_recon_tasks USING btree (tenant_id, created_at DESC) WHERE (tenant_id IS NOT NULL);
CREATE INDEX idx_vrt_tenant_period ON public.vat_recon_tasks USING btree (tenant_id, period) WHERE (tenant_id IS NOT NULL);
CREATE INDEX idx_vrt_tenant_status ON public.vat_recon_tasks USING btree (tenant_id, status) WHERE (tenant_id IS NOT NULL);
CREATE INDEX idx_vrt_user ON public.vat_recon_tasks USING btree (user_id);
CREATE INDEX ix_vat_recon_tasks_ws ON public.vat_recon_tasks USING btree (tenant_id, workspace_client_id);

CREATE TABLE IF NOT EXISTS "vat_report" (
  "id" bigint DEFAULT nextval('vat_report_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid,
  "client_id" bigint,
  "period_year" integer NOT NULL,
  "period_month" integer NOT NULL,
  "issuer_tax_id" text,
  "issuer_name" text,
  "issuer_branch" text DEFAULT '00000'::text,
  "source_file_ids" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "parsed_rows" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "total_amount_pre_vat" numeric(18,2),
  "total_vat" numeric(18,2),
  "total_amount" numeric(18,2),
  "parser_version" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "user_id" uuid,
  CONSTRAINT "vat_report_period_month_check" CHECK (((period_month >= 1) AND (period_month <= 12))),
  CONSTRAINT "vat_report_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_vat_report_client_period ON public.vat_report USING btree (client_id, period_year, period_month);
CREATE INDEX idx_vat_report_tax_id ON public.vat_report USING btree (issuer_tax_id) WHERE (issuer_tax_id IS NOT NULL);
CREATE INDEX idx_vat_report_tenant ON public.vat_report USING btree (tenant_id) WHERE (tenant_id IS NOT NULL);
CREATE INDEX idx_vat_report_user ON public.vat_report USING btree (user_id) WHERE (user_id IS NOT NULL);

CREATE TABLE IF NOT EXISTS "warehouses" (
  "id" bigint DEFAULT nextval('warehouses_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "name" text DEFAULT 'ร้าน'::text NOT NULL,
  "is_default" boolean DEFAULT false NOT NULL,
  "is_active" boolean DEFAULT true NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT "warehouses_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_warehouses_ws ON public.warehouses USING btree (tenant_id, workspace_client_id);

CREATE TABLE IF NOT EXISTS "work_order_deliverables" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "work_order_id" uuid NOT NULL,
  "kind" text NOT NULL,
  "artifact_path" text,
  "numbers" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "version" integer DEFAULT 1 NOT NULL,
  CONSTRAINT "work_order_deliverables_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX uq_wo_deliverables_kind_version ON public.work_order_deliverables USING btree (tenant_id, work_order_id, kind, version);

CREATE TABLE IF NOT EXISTS "work_order_events" (
  "id" bigint DEFAULT nextval('work_order_events_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid NOT NULL,
  "work_order_id" uuid NOT NULL,
  "step" text NOT NULL,
  "event_type" text NOT NULL,
  "payload" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "actor" text DEFAULT 'system'::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "dedupe_key" text,
  CONSTRAINT "work_order_events_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_wo_events_brain_terminal ON public.work_order_events USING btree (event_type, tenant_id, work_order_id, id) WHERE (event_type = ANY (ARRAY['bank_sales_brain_failed'::text, 'bank_sales_brain_finished'::text]));
CREATE INDEX ix_wo_events_wo ON public.work_order_events USING btree (tenant_id, work_order_id, id);
CREATE UNIQUE INDEX uq_wo_events_dedupe ON public.work_order_events USING btree (tenant_id, work_order_id, step, event_type, dedupe_key) WHERE (dedupe_key IS NOT NULL);

CREATE TABLE IF NOT EXISTS "work_order_items" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "work_order_id" uuid NOT NULL,
  "source" text NOT NULL,
  "kind" text DEFAULT 'unknown'::text NOT NULL,
  "file_ref" text,
  "ocr_history_id" uuid,
  "status" text DEFAULT 'pending'::text NOT NULL,
  "flag_reason" text,
  "dedupe_key" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "original_name" text,
  CONSTRAINT "work_order_items_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_wo_items_wo ON public.work_order_items USING btree (tenant_id, work_order_id);
CREATE UNIQUE INDEX uq_wo_items_dedupe ON public.work_order_items USING btree (tenant_id, work_order_id, dedupe_key) WHERE (dedupe_key IS NOT NULL);

CREATE TABLE IF NOT EXISTS "work_orders" (
  "id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "tenant_id" uuid NOT NULL,
  "workspace_client_id" bigint NOT NULL,
  "period" text NOT NULL,
  "intent" text DEFAULT 'monthly_vat'::text NOT NULL,
  "status" text DEFAULT 'collecting'::text NOT NULL,
  "current_step" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "run_lease_owner" text,
  "run_lease_expires_at" timestamp with time zone,
  CONSTRAINT "work_orders_pkey" PRIMARY KEY (id)
);
CREATE INDEX ix_wo_dead_run_scan ON public.work_orders USING btree (run_lease_expires_at) WHERE ((status = 'running'::text) AND (run_lease_expires_at IS NOT NULL));
CREATE UNIQUE INDEX uq_work_orders_scope ON public.work_orders USING btree (tenant_id, workspace_client_id, period, intent);

CREATE TABLE IF NOT EXISTS "workspace_clients" (
  "id" bigint DEFAULT nextval('workspace_clients_id_seq'::regclass) NOT NULL,
  "tenant_id" uuid,
  "user_id" uuid NOT NULL,
  "name" text NOT NULL,
  "tax_id" text,
  "erp_endpoint_id" text,
  "is_active" boolean DEFAULT true NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "address" text,
  "branch" text DEFAULT 'สำนักงานใหญ่'::text,
  "phone" text,
  "vat_registered" boolean DEFAULT true NOT NULL,
  "promptpay_id" text,
  "template_id" text,
  "brand_color" text,
  "logo_url" text,
  "seal_url" text,
  "signature_url" text,
  "footer_text" text,
  "email" text,
  "subject_type" text DEFAULT 'company'::text NOT NULL,
  "fiscal_year_start_month" smallint DEFAULT 1 NOT NULL,
  "doc_prefix" text,
  CONSTRAINT "workspace_clients_pkey" PRIMARY KEY (id)
);
CREATE INDEX idx_workspace_clients_tenant ON public.workspace_clients USING btree (tenant_id, is_active);
CREATE INDEX idx_workspace_clients_user ON public.workspace_clients USING btree (user_id, is_active);
CREATE UNIQUE INDEX uq_workspace_clients_personal_tenant ON public.workspace_clients USING btree (tenant_id) WHERE ((subject_type = 'personal'::text) AND is_active AND (tenant_id IS NOT NULL));
CREATE UNIQUE INDEX uq_workspace_clients_personal_user ON public.workspace_clients USING btree (user_id) WHERE ((subject_type = 'personal'::text) AND is_active AND (tenant_id IS NULL));
CREATE UNIQUE INDEX uq_workspace_clients_tax_active ON public.workspace_clients USING btree (tenant_id, tax_id) WHERE (is_active AND (tax_id IS NOT NULL));

-- 外键(建表全部完成后再加,避免顺序依赖)
ALTER TABLE "acct_bank_lines" ADD CONSTRAINT "acct_bank_lines_bank_account_id_fkey" FOREIGN KEY (bank_account_id) REFERENCES acct_bank_accounts(id) ON DELETE CASCADE;
ALTER TABLE "ai_contract_files" ADD CONSTRAINT "ai_contract_files_contract_id_fkey" FOREIGN KEY (contract_id) REFERENCES ai_goal_contracts(id) ON DELETE CASCADE;
ALTER TABLE "api_keys" ADD CONSTRAINT "api_keys_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "archive_settings" ADD CONSTRAINT "archive_settings_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "automation_rules" ADD CONSTRAINT "automation_rules_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "bank_reconcile_candidates" ADD CONSTRAINT "bank_reconcile_candidates_history_id_fkey" FOREIGN KEY (history_id) REFERENCES ocr_history(id) ON DELETE CASCADE;
ALTER TABLE "bank_reconcile_candidates" ADD CONSTRAINT "bank_reconcile_candidates_tx_id_fkey" FOREIGN KEY (tx_id) REFERENCES bank_reconcile_transactions(id) ON DELETE CASCADE;
ALTER TABLE "bank_reconcile_sessions" ADD CONSTRAINT "bank_reconcile_sessions_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "bank_reconcile_transactions" ADD CONSTRAINT "bank_reconcile_transactions_matched_history_id_fkey" FOREIGN KEY (matched_history_id) REFERENCES ocr_history(id) ON DELETE SET NULL;
ALTER TABLE "bank_reconcile_transactions" ADD CONSTRAINT "bank_reconcile_transactions_session_id_fkey" FOREIGN KEY (session_id) REFERENCES bank_reconcile_sessions(id) ON DELETE CASCADE;
ALTER TABLE "client_assignments" ADD CONSTRAINT "client_assignments_assigned_by_fkey" FOREIGN KEY (assigned_by) REFERENCES users(id);
ALTER TABLE "client_assignments" ADD CONSTRAINT "client_assignments_client_id_fkey" FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE;
ALTER TABLE "client_assignments" ADD CONSTRAINT "client_assignments_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "client_period_obligations" ADD CONSTRAINT "client_period_obligations_work_order_id_fkey" FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE SET NULL;
ALTER TABLE "credit_transactions" ADD CONSTRAINT "credit_transactions_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE "credit_transactions" ADD CONSTRAINT "credit_transactions_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE "email_ingest_accounts" ADD CONSTRAINT "email_ingest_accounts_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "email_ingest_logs" ADD CONSTRAINT "email_ingest_logs_account_id_fkey" FOREIGN KEY (account_id) REFERENCES email_ingest_accounts(id) ON DELETE CASCADE;
ALTER TABLE "email_ingest_logs" ADD CONSTRAINT "email_ingest_logs_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "email_ingest_seen_uids" ADD CONSTRAINT "email_ingest_seen_uids_account_id_fkey" FOREIGN KEY (account_id) REFERENCES email_ingest_accounts(id) ON DELETE CASCADE;
ALTER TABLE "email_ingest_seen_uids" ADD CONSTRAINT "email_ingest_seen_uids_history_id_fkey" FOREIGN KEY (history_id) REFERENCES ocr_history(id) ON DELETE SET NULL;
ALTER TABLE "erp_account_mappings" ADD CONSTRAINT "erp_account_mappings_created_by_fkey" FOREIGN KEY (created_by) REFERENCES users(id);
ALTER TABLE "erp_account_mappings" ADD CONSTRAINT "erp_account_mappings_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE "erp_client_mappings" ADD CONSTRAINT "erp_client_mappings_client_id_fkey" FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE;
ALTER TABLE "erp_client_mappings" ADD CONSTRAINT "erp_client_mappings_created_by_fkey" FOREIGN KEY (created_by) REFERENCES users(id);
ALTER TABLE "erp_client_mappings" ADD CONSTRAINT "erp_client_mappings_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE "erp_endpoints" ADD CONSTRAINT "erp_endpoints_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "erp_oauth_tokens" ADD CONSTRAINT "erp_oauth_tokens_created_by_fkey" FOREIGN KEY (created_by) REFERENCES users(id);
ALTER TABLE "erp_oauth_tokens" ADD CONSTRAINT "erp_oauth_tokens_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE "erp_product_mappings" ADD CONSTRAINT "erp_product_mappings_created_by_fkey" FOREIGN KEY (created_by) REFERENCES users(id);
ALTER TABLE "erp_product_mappings" ADD CONSTRAINT "erp_product_mappings_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE "erp_push_logs" ADD CONSTRAINT "erp_push_logs_endpoint_id_fkey" FOREIGN KEY (endpoint_id) REFERENCES erp_endpoints(id) ON DELETE SET NULL;
ALTER TABLE "erp_push_logs" ADD CONSTRAINT "erp_push_logs_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "erp_tax_mappings" ADD CONSTRAINT "erp_tax_mappings_created_by_fkey" FOREIGN KEY (created_by) REFERENCES users(id);
ALTER TABLE "erp_tax_mappings" ADD CONSTRAINT "erp_tax_mappings_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE "etax_submissions" ADD CONSTRAINT "etax_submissions_document_id_fkey" FOREIGN KEY (document_id) REFERENCES sales_documents(id) ON DELETE CASCADE;
ALTER TABLE "excel_templates" ADD CONSTRAINT "excel_templates_owner_id_fkey" FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "expense_categories" ADD CONSTRAINT "expense_categories_parent_id_fkey" FOREIGN KEY (parent_id) REFERENCES expense_categories(id) ON DELETE CASCADE;
ALTER TABLE "filing_lines" ADD CONSTRAINT "filing_lines_filing_id_fkey" FOREIGN KEY (filing_id) REFERENCES tax_filings(id) ON DELETE CASCADE;
ALTER TABLE "inventory_batches" ADD CONSTRAINT "inventory_batches_product_id_fkey" FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
ALTER TABLE "inventory_stock" ADD CONSTRAINT "inventory_stock_batch_id_fkey" FOREIGN KEY (batch_id) REFERENCES inventory_batches(id) ON DELETE CASCADE;
ALTER TABLE "inventory_stock" ADD CONSTRAINT "inventory_stock_product_id_fkey" FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
ALTER TABLE "inventory_stock" ADD CONSTRAINT "inventory_stock_warehouse_id_fkey" FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE;
ALTER TABLE "inventory_transactions" ADD CONSTRAINT "inventory_transactions_batch_id_fkey" FOREIGN KEY (batch_id) REFERENCES inventory_batches(id) ON DELETE SET NULL;
ALTER TABLE "inventory_transactions" ADD CONSTRAINT "inventory_transactions_product_id_fkey" FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
ALTER TABLE "inventory_transactions" ADD CONSTRAINT "inventory_transactions_warehouse_id_fkey" FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE;
ALTER TABLE "journal_lines" ADD CONSTRAINT "journal_lines_voucher_id_fkey" FOREIGN KEY (voucher_id) REFERENCES journal_vouchers(id) ON DELETE CASCADE;
ALTER TABLE "knowledge_chunks" ADD CONSTRAINT "knowledge_chunks_document_id_fkey" FOREIGN KEY (document_id) REFERENCES knowledge_documents(id);
ALTER TABLE "knowledge_documents" ADD CONSTRAINT "knowledge_documents_knowledge_base_id_fkey" FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id);
ALTER TABLE "knowledge_embeddings" ADD CONSTRAINT "knowledge_embeddings_chunk_id_fkey" FOREIGN KEY (chunk_id) REFERENCES knowledge_chunks(id);
ALTER TABLE "knowledge_ingest_jobs" ADD CONSTRAINT "knowledge_ingest_jobs_document_id_fkey" FOREIGN KEY (document_id) REFERENCES knowledge_documents(id);
ALTER TABLE "line_binding_codes" ADD CONSTRAINT "line_binding_codes_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "line_bindings" ADD CONSTRAINT "line_bindings_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "member_scopes" ADD CONSTRAINT "member_scopes_membership_id_fkey" FOREIGN KEY (membership_id) REFERENCES memberships(id) ON DELETE CASCADE;
ALTER TABLE "memberships" ADD CONSTRAINT "memberships_role_id_fkey" FOREIGN KEY (role_id) REFERENCES roles(id);
ALTER TABLE "memberships" ADD CONSTRAINT "memberships_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE "memberships" ADD CONSTRAINT "memberships_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "monthly_page_usage" ADD CONSTRAINT "monthly_page_usage_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE "mrerp_credentials" ADD CONSTRAINT "mrerp_credentials_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE "ocr_history" ADD CONSTRAINT "ocr_history_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "operation_logs" ADD CONSTRAINT "operation_logs_actor_user_id_fkey" FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE "operation_logs" ADD CONSTRAINT "operation_logs_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE "pos_cashiers" ADD CONSTRAINT "pos_cashiers_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE "pos_kot" ADD CONSTRAINT "pos_kot_session_id_fkey" FOREIGN KEY (session_id) REFERENCES pos_table_sessions(id) ON DELETE CASCADE;
ALTER TABLE "pos_payments" ADD CONSTRAINT "pos_payments_sale_id_fkey" FOREIGN KEY (sale_id) REFERENCES pos_sales(id) ON DELETE CASCADE;
ALTER TABLE "pos_sale_lines" ADD CONSTRAINT "pos_sale_lines_product_id_fkey" FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT;
ALTER TABLE "pos_sale_lines" ADD CONSTRAINT "pos_sale_lines_refund_of_line_id_fkey" FOREIGN KEY (refund_of_line_id) REFERENCES pos_sale_lines(id) ON DELETE SET NULL;
ALTER TABLE "pos_sale_lines" ADD CONSTRAINT "pos_sale_lines_sale_id_fkey" FOREIGN KEY (sale_id) REFERENCES pos_sales(id) ON DELETE CASCADE;
ALTER TABLE "pos_sales" ADD CONSTRAINT "pos_sales_cashier_id_fkey" FOREIGN KEY (cashier_id) REFERENCES pos_cashiers(id) ON DELETE SET NULL;
ALTER TABLE "pos_sales" ADD CONSTRAINT "pos_sales_refund_of_sale_id_fkey" FOREIGN KEY (refund_of_sale_id) REFERENCES pos_sales(id) ON DELETE SET NULL;
ALTER TABLE "pos_sales" ADD CONSTRAINT "pos_sales_shift_id_fkey" FOREIGN KEY (shift_id) REFERENCES pos_shifts(id) ON DELETE SET NULL;
ALTER TABLE "pos_sales" ADD CONSTRAINT "pos_sales_terminal_id_fkey" FOREIGN KEY (terminal_id) REFERENCES pos_terminals(id) ON DELETE SET NULL;
ALTER TABLE "pos_session_lines" ADD CONSTRAINT "pos_session_lines_kot_id_fkey" FOREIGN KEY (kot_id) REFERENCES pos_kot(id) ON DELETE SET NULL;
ALTER TABLE "pos_session_lines" ADD CONSTRAINT "pos_session_lines_product_id_fkey" FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT;
ALTER TABLE "pos_session_lines" ADD CONSTRAINT "pos_session_lines_session_id_fkey" FOREIGN KEY (session_id) REFERENCES pos_table_sessions(id) ON DELETE CASCADE;
ALTER TABLE "pos_session_lines" ADD CONSTRAINT "pos_session_lines_settled_sale_id_fkey" FOREIGN KEY (settled_sale_id) REFERENCES pos_sales(id) ON DELETE SET NULL;
ALTER TABLE "pos_shifts" ADD CONSTRAINT "pos_shifts_cashier_id_fkey" FOREIGN KEY (cashier_id) REFERENCES pos_cashiers(id) ON DELETE CASCADE;
ALTER TABLE "pos_shifts" ADD CONSTRAINT "pos_shifts_terminal_id_fkey" FOREIGN KEY (terminal_id) REFERENCES pos_terminals(id) ON DELETE CASCADE;
ALTER TABLE "pos_table_sessions" ADD CONSTRAINT "pos_table_sessions_cashier_id_fkey" FOREIGN KEY (cashier_id) REFERENCES pos_cashiers(id) ON DELETE SET NULL;
ALTER TABLE "pos_table_sessions" ADD CONSTRAINT "pos_table_sessions_table_id_fkey" FOREIGN KEY (table_id) REFERENCES pos_tables(id) ON DELETE RESTRICT;
ALTER TABLE "pos_tables" ADD CONSTRAINT "pos_tables_area_id_fkey" FOREIGN KEY (area_id) REFERENCES pos_areas(id) ON DELETE SET NULL;
ALTER TABLE "product_units" ADD CONSTRAINT "product_units_product_id_fkey" FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
ALTER TABLE "purchase_attachments" ADD CONSTRAINT "purchase_attachments_purchase_doc_id_fkey" FOREIGN KEY (purchase_doc_id) REFERENCES purchase_docs(id) ON DELETE CASCADE;
ALTER TABLE "purchase_lines" ADD CONSTRAINT "purchase_lines_purchase_doc_id_fkey" FOREIGN KEY (purchase_doc_id) REFERENCES purchase_docs(id) ON DELETE CASCADE;
ALTER TABLE "rd_daily_usage" ADD CONSTRAINT "rd_daily_usage_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "reconciliation_row" ADD CONSTRAINT "reconciliation_row_invoice_id_fkey" FOREIGN KEY (invoice_id) REFERENCES ocr_history(id) ON DELETE SET NULL;
ALTER TABLE "reconciliation_row" ADD CONSTRAINT "reconciliation_row_task_id_fkey" FOREIGN KEY (task_id) REFERENCES reconciliation_task(id) ON DELETE CASCADE;
ALTER TABLE "reconciliation_task" ADD CONSTRAINT "reconciliation_task_client_id_fkey" FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL;
ALTER TABLE "reconciliation_task" ADD CONSTRAINT "reconciliation_task_vat_report_id_fkey" FOREIGN KEY (vat_report_id) REFERENCES vat_report(id) ON DELETE SET NULL;
ALTER TABLE "sales_document_lines" ADD CONSTRAINT "sales_document_lines_document_id_fkey" FOREIGN KEY (document_id) REFERENCES sales_documents(id) ON DELETE CASCADE;
ALTER TABLE "sales_document_sends" ADD CONSTRAINT "sales_document_sends_document_id_fkey" FOREIGN KEY (document_id) REFERENCES sales_documents(id) ON DELETE CASCADE;
ALTER TABLE "sales_documents" ADD CONSTRAINT "sales_documents_references_document_id_fkey" FOREIGN KEY (references_document_id) REFERENCES sales_documents(id);
ALTER TABLE "sales_documents" ADD CONSTRAINT "sales_documents_seller_workspace_client_id_fkey" FOREIGN KEY (seller_workspace_client_id) REFERENCES workspace_clients(id);
ALTER TABLE "steward_attachments" ADD CONSTRAINT "steward_attachments_session_id_fkey" FOREIGN KEY (session_id) REFERENCES steward_sessions(id) ON DELETE CASCADE;
ALTER TABLE "steward_messages" ADD CONSTRAINT "steward_messages_session_id_fkey" FOREIGN KEY (session_id) REFERENCES steward_sessions(id) ON DELETE CASCADE;
ALTER TABLE "steward_tasks" ADD CONSTRAINT "steward_tasks_session_id_fkey" FOREIGN KEY (session_id) REFERENCES steward_sessions(id) ON DELETE CASCADE;
ALTER TABLE "tenant_credits" ADD CONSTRAINT "tenant_credits_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE "tenant_subscriptions" ADD CONSTRAINT "tenant_subscriptions_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE "topup_requests" ADD CONSTRAINT "topup_requests_requested_by_fkey" FOREIGN KEY (requested_by) REFERENCES users(id);
ALTER TABLE "topup_requests" ADD CONSTRAINT "topup_requests_reviewed_by_fkey" FOREIGN KEY (reviewed_by) REFERENCES users(id);
ALTER TABLE "topup_requests" ADD CONSTRAINT "topup_requests_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE "user_company_roles" ADD CONSTRAINT "user_company_roles_tenant_id_fkey" FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE "user_company_roles" ADD CONSTRAINT "user_company_roles_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "user_settings" ADD CONSTRAINT "user_settings_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE "users" ADD CONSTRAINT "users_active_tenant_id_fkey" FOREIGN KEY (active_tenant_id) REFERENCES tenants(id) ON DELETE SET NULL;
ALTER TABLE "vat_report" ADD CONSTRAINT "vat_report_client_id_fkey" FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL;
ALTER TABLE "work_order_deliverables" ADD CONSTRAINT "work_order_deliverables_work_order_id_fkey" FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE RESTRICT;
ALTER TABLE "work_order_events" ADD CONSTRAINT "work_order_events_work_order_id_fkey" FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE RESTRICT;
ALTER TABLE "work_order_items" ADD CONSTRAINT "work_order_items_work_order_id_fkey" FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE RESTRICT;
