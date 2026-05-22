# db.py · ensure_* 函数盘点

> **目的**：摸清 `db.py` 里所有 `ensure_*` 函数干啥 · 为 Task 6.2 设计 Alembic 迁移方案打底
> **状态**：Task 6.1 产出 · 阶段 6 起点 · EXECUTION_PLAN.md P2-03
> **创建**：2026-05-22

---

## 1 · 总览

- **25 个** `ensure_*` 函数(2 个带 `_` prefix 内部 helper)
- **24 个 DDL**(建表 / 加列 / 加索引 / 改约束) · **1 个数据初始化**(`ensure_tenant_credits`)
- **23 个启动时调用**(app.py `lifespan` L463-609 顺序执行) · **1 个按需调用** · **1 个已注释禁用**
- **全部幂等**(`IF NOT EXISTS` / `ON CONFLICT` / pg_catalog 探测) · 失败用 `logger.warning` 包起来 · 不阻塞启动
- 操作的表 **~28 张**(含扩展列 ALTER) · 覆盖用户认证 / 客户 / ERP / 对账 / 计费 / 多租户 6 大域

---

## 2 · 启动时调用顺序(app.py lifespan L463-609)

| # | 行 | 函数 | 类型 | 主要建表/操作 | 行 (db.py) | 幂等性 |
|---|---|---|---|---|---|---|
| 0 | 463 | ~~ensure_demo_account~~ | 数据 init | 注释掉 · Supabase 接管 · 不再调用 | 73 | n/a |
| 1 | 476 | ensure_ocr_cost_log_table | CREATE | `ocr_cost_log` 表 + 3 索引 | 3996 | ✅ IF NOT EXISTS |
| 2 | 482 | ensure_clients_table | CREATE+ALTER | `clients` 表 + 3 索引 · `ocr_history.client_id` 加列 + 索引 | 4188 | ✅ IF NOT EXISTS |
| 3 | 488 | ensure_supplier_categories_table | CREATE | `supplier_categories` 表 + 2 索引 | 4230 | ✅ IF NOT EXISTS |
| 4 | 494 | ensure_buyer_to_client_table | CREATE | `buyer_to_client_memory` 表 + tax 索引 | 4280 | ✅ IF NOT EXISTS |
| 5 | 500 | ensure_google_sub_column | ALTER | `users.google_sub` + `users.avatar_url` + google_sub 索引 | 246 | ✅ ADD COLUMN IF NOT EXISTS |
| 6 | 506 | ensure_line_uid_column | ALTER | `users.line_uid` + 索引 | 327 | ✅ ADD COLUMN IF NOT EXISTS |
| 7 | 512 | ensure_password_changed_at_column | ALTER | `users.password_changed_at` | 312 | ✅ ADD COLUMN IF NOT EXISTS |
| 8 | 518 | ensure_email_codes_table | CREATE | `email_codes` 表 + 2 索引 | 398 | ✅ IF NOT EXISTS |
| 9 | 524 | ensure_gl_vat_task_table | CREATE | `gl_vat_task` 表 + 2 索引 | 8259 | ✅ IF NOT EXISTS |
| 10 | 530 | ensure_membership_tables | CREATE+ALTER | `roles` + `memberships` + `client_assignments` + `tenants.tenant_type_v2` | 5756 | ✅ IF NOT EXISTS |
| 11 | 536 | ensure_billing_balance_table | CREATE | `billing_balance_log` 表 + 索引(老余额追踪 · v108) | 4815 | ✅ IF NOT EXISTS |
| 12 | 542 | ensure_exceptions_tables | CREATE | `exceptions` + `exception_whitelist` + 5+2 索引 | 4979 | ✅ IF NOT EXISTS |
| 13 | 548 | ensure_notification_tables | CREATE | `notification_rules` + `notification_logs` + 3+2 索引 | 5482 | ✅ IF NOT EXISTS |
| 14 | 554 | ensure_erp_retry_columns | ALTER | `erp_push_logs` retry_count / max_retries / next_retry_at + 索引 | 1621 | ✅ ADD COLUMN IF NOT EXISTS |
| 15 | 563 | ensure_erp_endpoints_adapter_constraint | CONSTRAINT | `erp_endpoints` adapter CHECK 白名单加 'mrerp' | 1510 | ⚠️ 半幂等(pg_catalog 探测 + drop+rebuild) |
| 16 | 567 | ensure_erp_push_logs_adapter_constraint | CONSTRAINT | `erp_push_logs` adapter CHECK 白名单加 'mrerp' | 1571 | ⚠️ 半幂等 |
| 17 | 573 | ensure_bank_recon_client_id_column | ALTER | `bank_reconcile_sessions.client_id` + 索引 | 2326 | ✅ ADD COLUMN IF NOT EXISTS |
| 18 | 579 | ensure_erp_mapping_tables | CREATE | `erp_client_mappings` + `erp_account_mappings` + `erp_tax_mappings` + `erp_product_mappings` + 11 索引 | 6601 | ✅ IF NOT EXISTS |
| 19 | 585 | ensure_erp_oauth_tables | CREATE | `erp_oauth_tokens` + `erp_oauth_states` + 3 索引 | 7072 | ✅ IF NOT EXISTS |
| 20 | 591 | ensure_vat_recon_tables | CREATE | `vat_report` + `reconciliation_task` + `reconciliation_row` + 10 索引(销项税对账三表) | 7399 | ✅ IF NOT EXISTS |
| 21 | 597 | ensure_vat_recon_tasks_table | CREATE | `vat_recon_tasks` 表 + 4 索引(Excel 公式对账) | 8024 | ✅ IF NOT EXISTS |
| 22 | 603 | ensure_bank_recon_v2_table | CREATE | `bank_recon_v2_task` 表 + 2 索引 | 8427 | ✅ IF NOT EXISTS |
| 23 | 609 | ensure_credits_tables | CREATE+ALTER+INSERT+UPDATE | 6 表 + `users.is_billing_exempt` + `users.active_tenant_id` + 数据回填 + 设豁免账号 | 8622 | ⚠️ 半幂等(末尾 UPDATE 每次重启重设) |

**顺序敏感性**:
- `ensure_membership_tables` 依赖 `tenants` 表存在(预设 · 不由 ensure_* 建)
- `ensure_credits_tables` 依赖 `tenants` + `users` 表存在
- `ensure_clients_table` 给 `ocr_history` 加 `client_id` 列 · 依赖 ocr_history 表存在
- 改顺序前必须检查 FK 依赖

---

## 3 · 按需调用(非 lifespan)

| 函数 | 调用点 | 操作 | 行 (db.py) |
|---|---|---|---|
| **ensure_tenant_credits**(tenant_id) | auth_signup.py:952 · 1100 · 1233(email / google / line 注册) | `INSERT INTO tenant_credits (tenant_id) VALUES (?) ON CONFLICT DO NOTHING` · 给新公司初始化 0 余额 | 8746 |
| _ensure_one_account(...) | 内部 helper · 给 `ensure_demo_account` 用 · 已废弃 | INSERT 测试用户 | 115 |

---

## 4 · 幂等性分类

### 4.1 · 完全幂等(20 个 · 标准 PG `IF NOT EXISTS`)
- 模式 A:`CREATE TABLE IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS`
- 模式 B:`ALTER TABLE ADD COLUMN IF NOT EXISTS`(PG 9.6+ 支持)
- 风险:**零** · 重启 1000 次效果跟跑 1 次一样

### 4.2 · 半幂等(2 个 · constraint 探测)
- `ensure_erp_endpoints_adapter_constraint` / `ensure_erp_push_logs_adapter_constraint`
- 模式:读 `pg_catalog.pg_constraint` 找现存 adapter CHECK → 若已含 `'mrerp'` 跳过 → 否则 `DROP CONSTRAINT IF EXISTS` + `ADD CONSTRAINT`
- 风险:**低** · 检测逻辑稳;但 Alembic 不擅长动态 constraint 改造 · 建议保留 ensure 方式

### 4.3 · 半幂等(1 个 · UPDATE 每次重设)
- `ensure_credits_tables` 末尾:
  ```sql
  UPDATE users SET is_billing_exempt = TRUE
  WHERE email IN ('skin306152@gmail.com','mrerp@outlook.co.th')
  ```
- 风险:**零**(数据安全) · 但每次重启浪费 1 SQL · Alembic 迁移时这应该作 one-shot data migration · 不进 schema 版本

### 4.4 · 数据初始化(2 个)
- `ensure_credits_tables` 末尾的 `INSERT ... ON CONFLICT DO NOTHING`(回填 user_company_roles + tenant_credits)
- `ensure_tenant_credits`(注册时)
- 风险:**零**(ON CONFLICT 保护) · Alembic 迁移时这两个应该作 data migration · 跟 DDL 分开

---

## 5 · 表清单(目标 schema 全图 · 按域分组)

### 5.1 · 用户 / 认证(2 表 + 5 扩展列)
- **email_codes** 表(注册邮箱验证码)
- **users 扩展列**:`google_sub`(Google OAuth)· `avatar_url` · `line_uid`(LINE Login)· `password_changed_at`(改密失效 JWT)· `is_billing_exempt`(豁免)· `active_tenant_id`(切公司)

### 5.2 · 客户管理(3 表 + 1 扩展列)
- **clients** 主表 · **supplier_categories** 学习表 · **buyer_to_client_memory** 学习表
- **ocr_history.client_id** 扩展列

### 5.3 · 多租户改造(3 表 + 1 扩展列)
- **roles** · **memberships** · **client_assignments**
- **tenants.tenant_type_v2** 扩展列

### 5.4 · ERP(6 表 + 3 列 + 2 constraints)
- 适配器:`erp_endpoints` adapter CHECK + `erp_push_logs` adapter CHECK + 3 retry 列
- Mapping(4 表):**erp_client_mappings** · **erp_account_mappings** · **erp_tax_mappings** · **erp_product_mappings**
- OAuth(2 表):**erp_oauth_tokens** · **erp_oauth_states**

### 5.5 · 异常 + 通知(4 表)
- 异常:**exceptions** · **exception_whitelist**
- 通知:**notification_rules** · **notification_logs**

### 5.6 · 对账(8 表 + 1 列)
- **vat_report** + **reconciliation_task** + **reconciliation_row**(销项税对账三表)
- **vat_recon_tasks**(Excel 公式对账)
- **gl_vat_task**(GL vs 销项税)
- **bank_recon_v2_task** + `bank_reconcile_sessions.client_id`

### 5.7 · 计费 + 监控(6 表 + 2 列)
- 老:**billing_balance_log** · **ocr_cost_log**
- 按量付费(v118.35.0.6):**user_company_roles** · **tenant_credits** · **credit_transactions** · **monthly_page_usage** · **topup_requests**
- **users.is_billing_exempt** · **users.active_tenant_id** 扩展列

---

## 6 · Alembic 迁移优先级建议(为 Task 6.2 打底)

### P0 · 第一批迁移(高复杂度 · 体量大 · 改动频繁)
1. **ensure_credits_tables**(6 表 + 2 列 + 2 数据迁移 + 1 UPDATE)
   - 拆 Alembic:`001_credits_schema.py`(纯 DDL)+ `002_credits_data_backfill.py`(2 个 ON CONFLICT INSERT)+ runtime fixture 设豁免账号(不进迁移 · 改 lifespan 直接 UPDATE)
2. **ensure_membership_tables**(3 表 + 1 列 · 多租户改造核心)
   - 拆 Alembic:`003_membership_schema.py`
3. **ensure_vat_recon_tables**(3 表 + 10 索引 · 对账核心)
   - 拆 Alembic:`004_vat_recon_schema.py`

### P1 · 第二批迁移(中复杂度)
4. **ensure_erp_mapping_tables**(4 表 + 11 索引)
5. **ensure_erp_oauth_tables**(2 表 + 3 索引)
6. **ensure_exceptions_tables**(2 表 + 7 索引)
7. **ensure_notification_tables**(2 表 + 5 索引)
8. **ensure_clients_table**(1 表 + 3 索引 + ocr_history 扩列)
9. **ensure_gl_vat_task_table** / **ensure_bank_recon_v2_table** / **ensure_vat_recon_tasks_table**(3 个对账小表)

### P2 · 第三批迁移(低复杂度 · 单列 / 简单表)
10. `ensure_google_sub_column` / `ensure_line_uid_column` / `ensure_password_changed_at_column` 合并 → `005_users_oauth_columns.py`
11. `ensure_bank_recon_client_id_column` / `ensure_erp_retry_columns` 单独迁
12. `ensure_email_codes_table` / `ensure_ocr_cost_log_table` / `ensure_supplier_categories_table` / `ensure_buyer_to_client_table` / `ensure_billing_balance_table`

### P3 · 保留 ensure 模式 · 不进 Alembic
- **ensure_erp_endpoints_adapter_constraint** / **ensure_erp_push_logs_adapter_constraint**:运行时 pg_catalog 探测 · 跨"adapter 注册表"动态扩白名单 · Alembic 静态迁移不擅长这种;未来扩 adapter 时改这两个函数 + erp_push ADAPTER_REGISTRY 即可
- **ensure_tenant_credits**(注册时 · 不是启动迁移 · 留 db.py 当 lib helper)

---

## 7 · 已知风险 + 切换 Alembic 必须先解的

1. **顺序敏感性**:ensure_credits_tables 依赖 ensure_membership_tables 先跑(因为 user_company_roles 跟 memberships 有重叠角色定义)。Alembic 用 revision 链 + `down_revision` 锚定顺序即可。
2. **跨表 ALTER 跨函数**(`ensure_clients_table` 给 `ocr_history` 加 `client_id` 列):Alembic 迁移时 ocr_history 表必须先在 schema 里(老表 · 不由 ensure_* 建 · 假设 prod 已存在);新环境 bootstrap 需要先建 ocr_history 再跑 client_id 迁移。
3. **dual-write 期**:Alembic 接管后 · 老 ensure_* 函数必须保留一段时间(灰度 · 验证 Alembic 写的 schema 跟老 ensure 一致)· 否则新部署到没跑 Alembic 的环境会缺表。
4. **数据迁移混在 DDL 里**:ensure_credits_tables 末尾 UPDATE / INSERT 写死了豁免邮箱 + 回填角色 · 这些应该:(a) 一次性 data migration 进 Alembic;(b) 启动 fixture 跑(开 PEARNLY_INIT_FIXTURES env);(c) 手动 SQL 跑一次。
5. **Constraint 动态扩白名单**:adapter constraint 函数是"动态 schema" · 不应该被 Alembic 锁死成 enum / static CHECK。保留 ensure 方式 · 但在迁移文档里写明"扩 adapter 走 ensure 不走 Alembic"。

---

## 8 · Task 6.2 接力提示

下个任务(Task 6.2 · 迁移体系设计 · 2h)用本盘点作输入:
- **决策点 1**:Alembic vs 自研 migrations 表(本项目用 Alembic 是行业标准 · 但要评估 Supabase 是否兼容)
- **决策点 2**:第一批试点选哪个 ensure_*(推荐 `ensure_vat_recon_tasks_table` · 因为是新表 · 没历史数据 · 风险最低)
- **决策点 3**:回滚策略(`down_revision` + `downgrade()` 函数 · Alembic 默认支持但需要每个迁移写 `downgrade`)
- **决策点 4**:dual-write 灰度期多长(建议至少 1 周 · 验证 Alembic schema = ensure_* 现状)
- **决策点 5**:Supabase 限制(部分 DDL 受 Supabase RLS / extensions 限制 · 需在 Task 6.2 实测)

---

*最后更新:2026-05-22 · 阶段 6 Task 6.1 产出 · 阶段 5 完成后第一个文档级任务*
