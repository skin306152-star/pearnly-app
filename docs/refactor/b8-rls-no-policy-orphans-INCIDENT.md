# B8 RLS · 「RLS 启用但零 policy」孤儿表事故清单(交 RLS 窗口处理)

> 2026-06-25 · LINE 窗口诊断。LINE 记账生产级全断,挖到底是 RLS rollout 的系统性漏洞,**不止 LINE**。
> 本文档是给 RLS 窗口的交接:根因 + 完整受影响表清单 + 每表建议模板 + 已做的应急处置。

## 1. 现象与根因

- **现象**:真机发「กาแฟ 60 / 今天在 7-11 买咖啡 60」→ Bot 不记账,回「我能帮你做什么」能力介绍。
- **链路**:LINE 文字记账主路径 `line_expense.handle_expense_text` 现在走最小权限角色 `pearnly_app`(`get_cursor_rls`)。它先查默认套账 `default_workspace_id` → 读 `workspace_clients`。
- **根因**:`workspace_clients` 表 **RLS 已 ENABLE 但 policy 数 = 0**。Postgres 规则:RLS 启用 + 零 policy = 对非 BYPASS 角色**默认全拒**。prod 已设 `RLS_ROLE=pearnly_app`(NOBYPASSRLS)→ 该角色看到 **0** 行套账(owner 看到 10 行)→ `default_workspace_id` 返 None → `if ws is None: return False` → webhook 兜底回 capability 文案 → **所有文字记账静默全断**。
- **为什么没异常日志**:出事时是干净的 `ws is None` 提前 return,没抛异常,所以 prod 日志查不到 traceback(误导排查方向)。网页 `/api/workspace/clients` 仍 200,是因为网页走 owner `get_cursor` 绕过 RLS。

## 2. 系统性:72 张表同病

prod 上 **72 张表 RLS 启用却零 policy**(`relrowsecurity=true AND 0 policies`)。任何走 `get_cursor_rls` 的路径一旦读/写到它们:SELECT 返空、INSERT 被拒(`new row violates row-level security policy`)。enrolled 域只在「读到未 enroll 的共享表」这种接缝处爆雷。

**不变量被破坏**:`RLS 启用 ⟺ 必须有 policy`。72 张违反。每张表要么补对的 policy(enroll),要么 `DISABLE ROW LEVEL SECURITY`(暂不 enroll 就别开 RLS)。

### 已确认正在造成真实损坏的(get_cursor_rls 路径实际触及)
| 表 | 影响 | 状态 |
|---|---|---|
| `workspace_clients` | LINE 记账(查默认套账)全断 | ✅ **已在 prod 应急补 `tenant_or_user` policy**(见 §4),LINE 已恢复 |
| `document_number_sequences` | LINE/记账过账时挂会计凭证(复式分录编号)被拒 → 费用记上了但**会计分录静默没入队**(`accounting enqueue failed`)。也影响 sales/pos 编号 | ❌ 待修 |

### 其余 70 张(按隔离列给出建议模板,RLS 窗口照 `core/rls.py` 现成函数补)

`tenant_or_user`(有 tenant_id+user_id):`api_keys` `archive_settings` `automation_rules` `buyer_to_client_memory` `credit_transactions` `email_ingest_accounts` `email_ingest_logs` `erp_endpoints` `erp_oauth_states` `erp_push_logs` `error_events` `exception_whitelist` `exceptions` `line_binding_codes` `line_bindings` `memberships` `notification_logs` `notification_rules` `ocr_cost_log` `rd_daily_usage` `supplier_categories` `user_company_roles` `user_settings`

`tenant`(仅 tenant_id):`email_ingest_seen_uids` `erp_account_mappings` `erp_client_mappings` `erp_oauth_tokens` `erp_product_mappings` `erp_tax_mappings` `excel_templates` `import_template_mappings` `invitations` `monthly_page_usage` `mrerp_credentials` `operation_logs` `ownership_transfers` `roles` `sales_document_lines` `sales_document_sends` `sales_settings` `supplier_client_mapping` `tenant_credits` `topup_requests` `users`

`tenant_ws`/`tenant_or_user`(有 tenant_id+workspace_client_id,按是否需账套强隔离选):`client_rules` `document_number_sequences` `etax_channel_settings` `etax_submissions` `invoice_risk_checks` `knowledge_answers` `knowledge_bases` `knowledge_chunks` `knowledge_documents` `knowledge_embeddings` `knowledge_ingest_jobs` `member_scopes` `products` `sales_documents` `seller_workspace_routes`

`user`(仅 user_id):`client_assignments` `password_reset_log` `payment_pending` `risk_log` `subscription_log`

**无隔离列**(需 via_parent 或干脆 DISABLE RLS · 多为系统/日志表):`alembic_version` `billing_balance_log` `email_codes` `ip_usage` `line_voice_quota` `login_failure_log` `rd_cache` `tenants`

> ⚠️ 钱/超管类(`tenant_credits` `credit_transactions` `billing_balance_log` `users` `tenants` `roles` `memberships`)按你们既定口径:聚合/超管路径必 bypass,charge.py 钱禁 bypass——补 policy 时别破坏这些设计。

## 3. 复现/验证脚本(prod · owner vs RLS 角色对比)

```python
# 列出所有「RLS on 零 policy」表
SELECT c.relname, count(p.polname) n
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
LEFT JOIN pg_policy p ON p.polrelid=c.oid
WHERE n.nspname='public' AND c.relkind='r' AND c.relrowsecurity
GROUP BY c.relname HAVING count(p.polname)=0;

# 单表可见性对比:owner 看到 N 行,get_cursor_rls(tenant) 看到 0 行 = 中招
```

LINE 端到端自检(workspace_clients 补后):`handle_expense_text('กาแฟ 60')` → `consumed=True` + `state='posted'` 数据卡(已在 Skin 测试号 `U26139c19...` 跑通,测试单已删)。

## 4. 已做的应急处置(LINE 窗口)

- **仅 prod DB**,**未改代码、未 commit**:`apply_tenant_or_user_rls(cur, 'workspace_clients')`(force=False)。
  - 验证:RLS 角色 workspace_clients 0→10 行,`default_workspace_id` 返 1,LINE 记账恢复。
  - 持久性:重启/部署不会丢(policy 在 DB),也不会复发(无代码 enable 它)。但**未落 code**——RLS 窗口请把它纳入正式 enroll(加进对应 `ensure_*` + 集成测试),与其余 71 张一起系统化处理。
- 没碰别的表、没碰别的窗口的文件。

## 5. 建议
1. 立刻补 `document_number_sequences`(否则 LINE 记的账没有会计分录,数据不完整)。
2. 系统化扫 72 张:enroll(补 policy)或 disable RLS,消灭「RLS on 零 policy」半态;加一个守门:CI/startup 断言「无 RLS-on-零-policy 表」防回归。
3. 复盘:rollout 时 `RLS_ROLE` 一上,所有被 get_cursor_rls 触及的共享维表都必须先 enroll,否则接缝即断。

---

## 6. 系统化处置(RLS 窗口 · 2026-06-25 · 本窗执行)

LINE 窗口诊断准确。本窗在 wave3 enroll ocr_history/clients 后**独立撞到同一根因**(真机「识别记录」0 条·实有 6):role 上下文下 `list_ocr_history` 的 `user_id IN (SELECT id FROM users WHERE tenant_id=%s)` 子查询读孤儿表 `users`(RLS on 零 policy)→ 返空 → 0 行。证据:role 上下文 `SELECT count(*) FROM ocr_history`=6(policy 正常)但 `FROM users`=0(孤儿 deny)。**坏在被 JOIN 的孤儿,不在 ocr_history 自身**。

### 选定方案:全量 DISABLE 孤儿(非逐张 enroll)
按判据 `relrowsecurity=true AND 0 policy` 在 prod 逐表 `DISABLE ROW LEVEL SECURITY`,共 **72 张**(含 LINE 窗口未及的 71 张 + `users`)。
- **为何 disable 不 enroll**:孤儿表 0 policy = **无任何隔离逻辑** = deny-all(坏)。disable 把「坏的全拒」恢复成「可用」,**不丢任何有效隔离**。**有 policy 的 61 张真隔离表(`ocr_history`/`clients`/`bank_reconcile_*`/`recon`/`workspace_clients`[LINE 窗已补]/POS/采购/会计/journal/inventory/suppliers/sales? 见下)全部未动**。单租户 prod 下被 disable 的表无跨租户暴露。
- **与 enroll 不冲突**:proper 隔离仍是 B8 后续目标。某张表将来按域 enroll(`apply_*` = `ENABLE`+`CREATE POLICY` 原子)即从 disabled 恢复成隔离,无需先 enable。即:**disable 现在止血,enroll 以后按域慢慢补**(单租户不急)。

### 处置后 prod 核验(role 上下文 · 真数据)
| 业务 | 结果 |
|---|---|
| OCR 识别记录(用户 6 票) | 6 ✅(原 0) |
| ERP 推送日志 | 2 ✅ |
| LINE 绑定 | 4 ✅ |
| `document_number_sequences` 可读 | 21 ✅(原写被拒·LINE 会计分录恢复) |
| `ocr_history` 跨租户(fake 租户) | 0 ✅(隔离仍在) |
| 复查残留孤儿 | 0 ✅ |

> 注:`sales_documents`/`products`/`exceptions`/`erp_*` 等在孤儿列(本就 0 policy)→ 已 disable。它们是「应有 policy 却缺失」的表,proper 隔离待后续按域 enroll;`users`/`tenants`/`roles`/`rd_cache`/`line_voice_quota`/审计日志 本就是设计 §6「不开 RLS」→ disable 即终态。

### 防复发:自愈守卫(代码 · 已落)
`core/rls.py` 加 `disable_orphan_rls(cur)`:扫 `relrowsecurity=true AND 0 policy` 全 disable + 记日志。注册为 **startup 最后一步**(所有 `ensure_*`/`apply_*` 建完 policy 之后)→ 真 enroll 的表此时已有 policy(不被误关),残留孤儿被关。幂等自愈,杜绝「带外开 RLS 没建 policy → deny-all」再次发生。**与按域 enroll 完全兼容**(enroll 后有 policy → 守卫不动它)。

### 教训(本窗)
1. **金丝雀必须走真 store 函数**:wave3 金丝雀只跑 `SELECT count(*) FROM ocr_history`(直查·policy 正常),没跑 `list_ocr_history` 的 `users` 子查询 → 漏掉孤儿 users。**以后 enroll 金丝雀必调真 app 函数,不止验 policy 谓词**。
2. **迁角色前扫全 JOIN/子查询触及表**:任何 owner→`get_cursor_rls` 的迁移,前置必须确认该查询触及的**所有**表(含 JOIN/子查询)在角色下可读(无孤儿)。
