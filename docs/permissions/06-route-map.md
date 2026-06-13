# 权限管理整顿 · 06 全量路由对照表(批2 产物 · 批5 收口更新 2026-06-10)

> 生成源:`scripts/authz_route_inventory.py`(随 `check_authz_coverage` 闸常新)。
> 表为快照;真相 = 源码守门 + 第 8 道闸。

## 收敛结果速览(批5 后)

| 守门形态 | 路由数 |
|---|---|
| require_perm | 109 |
| 登录态(resolver 吸收 · P2 待映射) | 104 |
| 文件内 helper 守门 | 68 |
| 公开白名单 | 54(含 fastapi /docs 4 条) |
| 平台层 _require_super_admin(保留) | 52 |
| require_perm(经 auth_member/auth_owner) | 47 |
| POS require_tenant(收银员可调) | 1 |

## 九门收敛状态(批5 收口后 · 旧门别名全删)

| 旧门 | 状态 |
|---|---|
| `_require_super_admin` | 保留(平台层短路,52 路由不动) |
| `_require_owner_or_super` | **批5 已删**(批2 清零 23 调用点 · 本体随批5 从 route_helpers 移除 · 契约测试锁不许复活) |
| `_require_tenant` | **批5 已删**(route_helpers 本体移除;uploads_routes 文件内同名 helper 为局部租户解析,非旧门) |
| `require_account_owner` | **批5 已删**(modules 写接口直走 require_perm_pos_tid "settings.modules.manage") |
| `require_owner`(POS) | **批5 已删**(批2 清零 13 调用点 · 本体随批5 从 pos_api 移除) |
| `pos_auth` | 保留为令牌解析层(require_perm_pos 内部走它) |
| `require_workspace` | 保留 + 套账解析点叠 `check_request_scope`(assigned 未分配 → 404) |
| `assert_module_enabled` | 仍在(双保险);require_perm 第 3 步按码→模块自动判 |
| `auth_member/auth_owner`(purchase/accounting) | 改带码签名,invited_by 判定退役,46+ 调用点逐路由带码 |

批5 同时收口:旧团队管理 7 接口(`/api/team/employees*` · routes/team_routes.py)整体处决,
员工管理全走 /console 新体系(`/api/team/members*`);billing 读侧 owner 判定从
`invited_by IS NULL` 切 membership(`authz.deps.is_owner_role`)。

## 行为偏差清单(矩阵为准 · 与切换前 diff 的全部已知项)

存量角色映射:owner→owner(全码);受邀 member→accountant(拍板点#6)。

**收紧(原先是漏门,按矩阵关上):**
- POS 后台(收银员管理/店铺码/收款设置/桌台区域管理):原 require_owner 只挡收银员 · 受邀员工可进 → 现 pos.admin.manage(owner/admin)。会计/录入 403。
- 销项设置 PUT /api/sales/settings、开票方资料 PUT /api/sales/sellers/*:原任意成员 → 现 sales.settings.manage(owner/admin)。
- 模块开关(原 require_account_owner):语义不变之外,管理员(admin 角色)新获权(矩阵 ✔)。

**放宽(原先过严,按矩阵打开):**
- 进项审付款/作废/凭据(原 auth_owner=invited_by 空):会计角色现可 purchase.doc.approve(矩阵 ✔ · 拍板点#6 会计=审批级)。
- 做账写侧(原 auth_owner):会计现可 acct.entry.review/approve/coa.manage。
- ERP 映射/Xero 配置(原仅 owner):admin 现可(settings.org.edit)。
- 销项单据审批(原 _require_owner_or_super):会计现可 sales.doc.approve。

**P2 待映射面(保持登录态守门 · registry 本期未设码):**
OCR 识别/上传、history、ERP push/endpoints、对账 v0 杂项、clients/categories、DMS、email-ingest、exceptions、notification、billing 读侧、settings_routes(采集偏好)。新角色(clerk/viewer)对这些面暂与会计同权;批5/P2 收紧。

## 逐路由明细

| 方法 | 路径 | 守门 | 权限码 | 文件 |
|---|---|---|---|---|
| GET | `/api/accounting/books` | helper_gated | — | routes/accounting_books_routes.py |
| POST | `/api/accounting/close-period` | auth_member | `acct.entry.approve` | routes/accounting_books_routes.py |
| GET | `/api/accounting/export-package` | auth_member | `acct.ledger.export` | routes/accounting_books_routes.py |
| GET | `/api/accounting/financials` | helper_gated | — | routes/accounting_books_routes.py |
| GET | `/api/accounting/tax-reports` | helper_gated | — | routes/accounting_books_routes.py |
| GET | `/api/accounting/accounts` | auth_member | `acct.coa.manage` `acct.entry.view` | routes/accounting_routes.py |
| POST | `/api/accounting/accounts` | auth_member | `acct.coa.manage` `acct.entry.view` | routes/accounting_routes.py |
| PATCH | `/api/accounting/accounts/{account_id}` | auth_member | `acct.coa.manage` | routes/accounting_routes.py |
| GET | `/api/accounting/learned` | auth_member | `acct.entry.view` | routes/accounting_routes.py |
| DELETE | `/api/accounting/learned/{learned_id}` | auth_member | `acct.coa.manage` | routes/accounting_routes.py |
| GET | `/api/accounting/mappings` | auth_member | `acct.coa.manage` `acct.entry.view` | routes/accounting_routes.py |
| PUT | `/api/accounting/mappings` | auth_member | `acct.coa.manage` `acct.entry.view` | routes/accounting_routes.py |
| GET | `/api/accounting/review` | auth_member | `acct.entry.review` | routes/accounting_routes.py |
| GET | `/api/accounting/settings` | auth_member | `acct.entry.view` `acct.settings.manage` | routes/accounting_routes.py |
| PUT | `/api/accounting/settings` | auth_member | `acct.entry.view` `acct.settings.manage` | routes/accounting_routes.py |
| GET | `/api/accounting/vouchers` | auth_member | `acct.entry.view` | routes/accounting_routes.py |
| POST | `/api/accounting/vouchers/manual` | auth_member | `acct.entry.review` | routes/accounting_routes.py |
| GET | `/api/accounting/vouchers/{voucher_id}` | auth_member | `acct.entry.review` `acct.entry.view` | routes/accounting_routes.py |
| PATCH | `/api/accounting/vouchers/{voucher_id}` | auth_member | `acct.entry.review` `acct.entry.view` | routes/accounting_routes.py |
| POST | `/api/accounting/vouchers/{voucher_id}/review` | auth_member | `acct.entry.review` | routes/accounting_routes.py |
| POST | `/api/accounting/vouchers/{voucher_id}/unpost` | auth_member | `acct.entry.approve` | routes/accounting_routes.py |
| POST | `/api/accounting/vouchers/{voucher_id}/void` | auth_member | `acct.entry.approve` | routes/accounting_routes.py |
| GET | `/api/admin/cost/by_user` | super_admin | — | routes/admin_cost_routes.py |
| GET | `/api/admin/cost/daily_trend` | super_admin | — | routes/admin_cost_routes.py |
| GET | `/api/admin/cost/debug` | super_admin | — | routes/admin_cost_routes.py |
| GET | `/api/admin/cost/export` | super_admin | — | routes/admin_cost_routes.py |
| GET | `/api/admin/cost/overview` | super_admin | — | routes/admin_cost_routes.py |
| GET | `/api/admin/credits/daily_trend` | super_admin | — | routes/admin_cost_routes.py |
| GET | `/api/admin/credits/export` | super_admin | — | routes/admin_cost_routes.py |
| GET | `/api/admin/credits/overview` | super_admin | — | routes/admin_cost_routes.py |
| GET | `/api/admin/credits/tenants` | super_admin | — | routes/admin_cost_routes.py |
| GET | `/api/admin/monitoring/overview` | super_admin | — | routes/admin_cost_routes.py |
| GET | `/api/admin/diagnostics/errors` | super_admin | — | routes/admin_diagnostics_routes.py |
| GET | `/api/admin/diagnostics/runtime` | super_admin | — | routes/admin_diagnostics_routes.py |
| POST | `/internal/deploy` | public | — | routes/admin_diagnostics_routes.py |
| GET | `/internal/deploy/log` | public | — | routes/admin_diagnostics_routes.py |
| GET | `/internal/deploy/manual` | public | — | routes/admin_diagnostics_routes.py |
| GET | `/internal/deploy/status` | public | — | routes/admin_diagnostics_routes.py |
| GET | `/internal/install-playwright` | public | — | routes/admin_diagnostics_routes.py |
| POST | `/internal/install-playwright` | public | — | routes/admin_diagnostics_routes.py |
| GET | `/api/admin/logs` | super_admin | — | routes/admin_logs_routes.py |
| GET | `/api/admin/logs.csv` | super_admin | — | routes/admin_logs_routes.py |
| GET | `/api/me/access_log` | login_only | — | routes/admin_logs_routes.py |
| GET | `/api/me/access_log.csv` | login_only | — | routes/admin_logs_routes.py |
| POST | `/api/admin/migration/backfill_tenant_ids` | super_admin | — | routes/admin_migration_routes.py |
| POST | `/api/admin/migration/dry_run` | super_admin | — | routes/admin_migration_routes.py |
| POST | `/api/admin/migration/execute` | super_admin | — | routes/admin_migration_routes.py |
| POST | `/api/admin/migration/fix_orphans` | super_admin | — | routes/admin_migration_routes.py |
| GET | `/api/admin/migration/orphan_list` | super_admin | — | routes/admin_migration_routes.py |
| POST | `/api/admin/rls/run_tests` | super_admin | — | routes/admin_migration_routes.py |
| GET | `/api/admin/rls/status` | super_admin | — | routes/admin_migration_routes.py |
| DELETE | `/api/admin/employees/{employee_id}` | super_admin | — | routes/admin_users_mutation_routes.py |
| PATCH | `/api/admin/employees/{employee_id}/active` | super_admin | — | routes/admin_users_mutation_routes.py |
| POST | `/api/admin/employees/{employee_id}/reset-password` | super_admin | — | routes/admin_users_mutation_routes.py |
| POST | `/api/admin/users` | super_admin | — | routes/admin_users_mutation_routes.py |
| POST | `/api/admin/users/{user_id}/cascade-delete` | super_admin | — | routes/admin_users_mutation_routes.py |
| POST | `/api/admin/users/{user_id}/delete` | super_admin | — | routes/admin_users_mutation_routes.py |
| PATCH | `/api/admin/users/{user_id}/quota` | super_admin | — | routes/admin_users_mutation_routes.py |
| POST | `/api/admin/users/{user_id}/reset-password` | super_admin | — | routes/admin_users_mutation_routes.py |
| PATCH | `/api/admin/users/{user_id}/status` | super_admin | — | routes/admin_users_mutation_routes.py |
| GET | `/api/admin/employees` | super_admin | — | routes/admin_users_query_routes.py |
| GET | `/api/admin/users` | super_admin | — | routes/admin_users_query_routes.py |
| GET | `/api/admin/users.csv` | super_admin | — | routes/admin_users_query_routes.py |
| GET | `/api/admin/users/{user_id}` | super_admin | — | routes/admin_users_query_routes.py |
| GET | `/api/admin/users/{user_id}/cascade-preview` | super_admin | — | routes/admin_users_query_routes.py |
| GET | `/api/admin/users/{user_id}/logs` | super_admin | — | routes/admin_users_query_routes.py |
| POST | `/api/admin/risk/batch-ban` | super_admin | — | routes/auth_admin_risk_routes.py |
| GET | `/api/admin/risk/suspicious` | super_admin | — | routes/auth_admin_risk_routes.py |
| POST | `/api/admin/users/{user_id}/ban` | super_admin | — | routes/auth_admin_risk_routes.py |
| POST | `/api/admin/users/{user_id}/unban` | super_admin | — | routes/auth_admin_risk_routes.py |
| POST | `/api/admin/cleanup_demo` | super_admin | — | routes/auth_admin_routes.py |
| GET | `/api/admin/password_resets` | super_admin | — | routes/auth_admin_routes.py |
| GET | `/api/admin/signup_sources` | super_admin | — | routes/auth_admin_routes.py |
| GET | `/api/admin/users/funnel` | super_admin | — | routes/auth_admin_routes.py |
| POST | `/api/auth/send_email_code` | public | — | routes/auth_email_code_routes.py |
| POST | `/api/auth/verify_email_code` | public | — | routes/auth_email_code_routes.py |
| POST | `/api/me/link_line` | helper_gated | — | routes/auth_me_routes.py |
| POST | `/api/me/link_line_dev` | helper_gated | — | routes/auth_me_routes.py |
| GET | `/api/me/plan` | helper_gated | — | routes/auth_me_routes.py |
| POST | `/api/auth/forgot_password` | public | — | routes/auth_password_routes.py |
| POST | `/api/auth/reset_password` | public | — | routes/auth_password_routes.py |
| POST | `/api/me/change_password` | login_only | — | routes/auth_password_routes.py |
| POST | `/api/bank-recon/_dev/clear` | require_perm | `recon.create` | routes/bank_recon_routes.py |
| POST | `/api/bank-recon/_dev/seed` | require_perm | `recon.create` | routes/bank_recon_routes.py |
| GET | `/api/bank-recon/sessions` | require_perm | `recon.view` | routes/bank_recon_routes.py |
| DELETE | `/api/bank-recon/sessions/{session_id}` | require_perm | `recon.create` `recon.view` | routes/bank_recon_routes.py |
| GET | `/api/bank-recon/sessions/{session_id}` | require_perm | `recon.create` `recon.view` | routes/bank_recon_routes.py |
| PATCH | `/api/bank-recon/sessions/{session_id}/client` | require_perm | `recon.create` | routes/bank_recon_routes.py |
| POST | `/api/bank-recon/sessions/{session_id}/match` | require_perm | `recon.create` | routes/bank_recon_routes.py |
| GET | `/api/bank-recon/stats` | require_perm | `recon.view` | routes/bank_recon_routes.py |
| GET | `/api/bank-recon/tx/{tx_id}/candidates` | require_perm | `recon.view` | routes/bank_recon_routes.py |
| POST | `/api/bank-recon/tx/{tx_id}/override` | require_perm | `recon.create` | routes/bank_recon_routes.py |
| POST | `/api/bank-recon/upload` | require_perm | `recon.create` | routes/bank_recon_routes.py |
| GET | `/api/credits/usage-history` | login_only | — | routes/billing_credits_routes.py |
| GET | `/api/credits/usage-report` | login_only | — | routes/billing_credits_routes.py |
| GET | `/api/me/credits` | login_only | — | routes/billing_credits_routes.py |
| GET | `/api/my-companies` | login_only | — | routes/billing_credits_routes.py |
| POST | `/api/switch-company` | login_only | — | routes/billing_credits_routes.py |
| POST | `/api/admin/credits/topup/approve/{request_id}` | super_admin | — | routes/billing_topup_routes.py |
| POST | `/api/admin/credits/topup/reject/{request_id}` | super_admin | — | routes/billing_topup_routes.py |
| GET | `/api/admin/credits/topup/requests` | super_admin | — | routes/billing_topup_routes.py |
| GET | `/api/credits/topup/history` | login_only | — | routes/billing_topup_routes.py |
| POST | `/api/credits/topup/request` | login_only | — | routes/billing_topup_routes.py |
| POST | `/api/credits/topup/upload-slip/{request_id}` | login_only | — | routes/billing_topup_routes.py |
| GET | `/api/categories` | login_only | — | routes/categories_routes.py |
| GET | `/api/clients` | login_only | — | routes/clients_routes.py |
| POST | `/api/clients` | login_only | — | routes/clients_routes.py |
| POST | `/api/clients/batch-delete` | login_only | — | routes/clients_routes.py |
| DELETE | `/api/clients/{client_id}` | login_only | — | routes/clients_routes.py |
| PATCH | `/api/clients/{client_id}` | login_only | — | routes/clients_routes.py |
| GET | `/api/clients/{client_id}/export` | login_only | — | routes/clients_routes.py |
| POST | `/api/invitations/{token}/accept` | public | — | routes/console_invite_routes.py |
| GET | `/api/invitations/{token}/preview` | public | — | routes/console_invite_routes.py |
| POST | `/api/ownership/transfer` | require_perm | `ownership.transfer` | routes/console_invite_routes.py |
| POST | `/api/ownership/transfer/accept` | login_only | — | routes/console_invite_routes.py |
| GET | `/api/team/invitations` | require_perm | `team.member.invite` `team.member.view` | routes/console_invite_routes.py |
| POST | `/api/team/invitations` | require_perm | `team.member.invite` `team.member.view` | routes/console_invite_routes.py |
| DELETE | `/api/team/invitations/{invitation_id}` | require_perm | `team.member.invite` | routes/console_invite_routes.py |
| GET | `/api/me/permissions` | login_only | — | routes/console_team_routes.py |
| GET | `/api/team/members` | require_perm | `team.member.view` | routes/console_team_routes.py |
| DELETE | `/api/team/members/{uid}` | require_perm | `team.member.remove` | routes/console_team_routes.py |
| PATCH | `/api/team/members/{uid}/active` | require_perm | `team.member.toggle` | routes/console_team_routes.py |
| PUT | `/api/team/members/{uid}/role` | require_perm | `team.member.edit_role` | routes/console_team_routes.py |
| PUT | `/api/team/members/{uid}/scope` | require_perm | `team.member.scope` | routes/console_team_routes.py |
| GET | `/api/team/roles` | require_perm | `team.member.view` | routes/console_team_routes.py |
| GET | `/api/team/security-events` | require_perm | `audit.log.view` | routes/console_team_routes.py |
| GET | `/api/team/roles/custom` | require_perm | `team.member.view` | routes/console_roles_routes.py |
| POST | `/api/team/roles` | require_perm | `team.member.edit_role` | routes/console_roles_routes.py |
| PATCH | `/api/team/roles/{role_id}` | require_perm | `team.member.edit_role` | routes/console_roles_routes.py |
| DELETE | `/api/team/roles/{role_id}` | require_perm | `team.member.edit_role` | routes/console_roles_routes.py |
| PUT | `/api/team/members/{uid}/role-assign` | require_perm | `team.member.edit_role` | routes/console_roles_routes.py |
| POST | `/api/dms/id-card/recognize` | login_only | — | routes/dms_routes.py |
| GET | `/api/dms/geo` | login_only | — | routes/dms_routes.py |
| POST | `/api/dms/id-card/push` | login_only | — | routes/dms_routes.py |
| DELETE | `/api/email-ingest/account` | login_only | — | routes/email_ingest_routes.py |
| GET | `/api/email-ingest/account` | login_only | — | routes/email_ingest_routes.py |
| PUT | `/api/email-ingest/account` | login_only | — | routes/email_ingest_routes.py |
| GET | `/api/email-ingest/logs` | login_only | — | routes/email_ingest_routes.py |
| POST | `/api/email-ingest/test` | login_only | — | routes/email_ingest_routes.py |
| POST | `/api/email-ingest/trigger` | login_only | — | routes/email_ingest_routes.py |
| GET | `/api/erp/endpoints` | login_only | — | routes/erp_endpoints_routes.py |
| POST | `/api/erp/endpoints` | login_only | — | routes/erp_endpoints_routes.py |
| DELETE | `/api/erp/endpoints/{endpoint_id}` | login_only | — | routes/erp_endpoints_routes.py |
| PATCH | `/api/erp/endpoints/{endpoint_id}` | login_only | — | routes/erp_endpoints_routes.py |
| PATCH | `/api/erp/endpoints/{endpoint_id}/seed` | login_only | — | routes/erp_endpoints_routes.py |
| GET | `/api/erp/endpoints/{endpoint_id}/customers` | login_only | — | routes/erp_listing_routes.py |
| GET | `/api/erp/endpoints/{endpoint_id}/products` | login_only | — | routes/erp_listing_routes.py |
| POST | `/api/erp/endpoints/{endpoint_id}/test-connection` | login_only | — | routes/erp_listing_routes.py |
| POST | `/api/erp/test-connection` | login_only | — | routes/erp_listing_routes.py |
| POST | `/api/erp/wizard/products` | login_only | — | routes/erp_listing_routes.py |
| GET | `/api/erp/mappings/accounts` | login_only | `settings.org.edit` | routes/erp_mappings_routes.py |
| POST | `/api/erp/mappings/accounts` | require_perm | `settings.org.edit` | routes/erp_mappings_routes.py |
| DELETE | `/api/erp/mappings/accounts/{mapping_id}` | require_perm | `settings.org.edit` | routes/erp_mappings_routes.py |
| GET | `/api/erp/mappings/clients` | login_only | `settings.org.edit` | routes/erp_mappings_routes.py |
| POST | `/api/erp/mappings/clients` | require_perm | `settings.org.edit` | routes/erp_mappings_routes.py |
| DELETE | `/api/erp/mappings/clients/{mapping_id}` | require_perm | `settings.org.edit` | routes/erp_mappings_routes.py |
| GET | `/api/erp/mappings/products` | login_only | — | routes/erp_mappings_routes.py |
| POST | `/api/erp/mappings/products` | login_only | — | routes/erp_mappings_routes.py |
| DELETE | `/api/erp/mappings/products/{mapping_id}` | login_only | — | routes/erp_mappings_routes.py |
| GET | `/api/erp/mappings/taxes` | login_only | `settings.org.edit` | routes/erp_mappings_routes.py |
| POST | `/api/erp/mappings/taxes` | require_perm | `settings.org.edit` | routes/erp_mappings_routes.py |
| DELETE | `/api/erp/mappings/taxes/{mapping_id}` | require_perm | `settings.org.edit` | routes/erp_mappings_routes.py |
| GET | `/api/erp/exceptions` | login_only | — | routes/erp_push_log_routes.py |
| GET | `/api/erp/history/{history_id}/push_status` | login_only | — | routes/erp_push_log_routes.py |
| GET | `/api/erp/logs` | login_only | — | routes/erp_push_log_routes.py |
| POST | `/api/erp/logs/batch-delete` | login_only | — | routes/erp_push_log_routes.py |
| POST | `/api/erp/logs/batch-retry` | login_only | — | routes/erp_push_log_routes.py |
| GET | `/api/erp/logs/{log_id}` | login_only | — | routes/erp_push_log_routes.py |
| GET | `/api/erp/logs/{log_id}/debug-xlsx` | login_only | — | routes/erp_push_log_routes.py |
| POST | `/api/erp/logs/{log_id}/retry` | login_only | — | routes/erp_push_log_routes.py |
| POST | `/api/erp/push` | login_only | — | routes/erp_push_log_routes.py |
| GET | `/api/erp/stats/today` | login_only | — | routes/erp_push_log_routes.py |
| GET | `/api/erp/connectors/status` | login_only | — | routes/erp_xero_routes.py |
| GET | `/api/erp/xero/auth/callback` | public | — | routes/erp_xero_routes.py |
| GET | `/api/erp/xero/auth/start` | require_perm | `settings.org.edit` | routes/erp_xero_routes.py |
| POST | `/api/erp/xero/auto-push` | require_perm | `settings.org.edit` | routes/erp_xero_routes.py |
| POST | `/api/erp/xero/disconnect` | require_perm | `settings.org.edit` | routes/erp_xero_routes.py |
| POST | `/api/erp/xero/push/{history_id}` | login_only | — | routes/erp_xero_routes.py |
| POST | `/api/erp/xero/select_org` | require_perm | `settings.org.edit` | routes/erp_xero_routes.py |
| GET | `/api/erp/xero/status` | login_only | — | routes/erp_xero_routes.py |
| GET | `/api/exception-whitelist` | login_only | — | routes/exceptions_routes.py |
| DELETE | `/api/exception-whitelist/{wl_id}` | login_only | — | routes/exceptions_routes.py |
| POST | `/api/exceptions/batch` | login_only | — | routes/exceptions_routes.py |
| GET | `/api/exceptions/list` | login_only | — | routes/exceptions_routes.py |
| GET | `/api/exceptions/stats` | login_only | — | routes/exceptions_routes.py |
| GET | `/api/exceptions/{exception_id}` | login_only | — | routes/exceptions_routes.py |
| POST | `/api/exceptions/{exception_id}/ignore` | login_only | — | routes/exceptions_routes.py |
| POST | `/api/exceptions/{exception_id}/resolve` | login_only | — | routes/exceptions_routes.py |
| GET | `/api/history` | login_only | — | routes/history_routes.py |
| POST | `/api/history/batch-delete` | login_only | — | routes/history_routes.py |
| POST | `/api/history/{history_id}/assign_client` | login_only | — | routes/history_routes.py |
| DELETE | `/api/history/{record_id}` | login_only | — | routes/history_routes.py |
| GET | `/api/history/{record_id}` | login_only | — | routes/history_routes.py |
| PUT | `/api/history/{record_id}` | login_only | — | routes/history_routes.py |
| GET | `/api/history/{record_id}/pdf` | login_only | — | routes/history_routes.py |
| GET | `/api/v1/history` | public | — | routes/history_routes.py |
| DELETE | `/api/v1/history/{record_id}` | public | — | routes/history_routes.py |
| GET | `/api/v1/history/{record_id}` | public | — | routes/history_routes.py |
| PUT | `/api/v1/history/{record_id}` | public | — | routes/history_routes.py |
| GET | `/api/recon/import/mappings` | login_only | — | routes/import_routes.py |
| DELETE | `/api/recon/import/mappings/{mapping_id}` | login_only | — | routes/import_routes.py |
| POST | `/api/recon/import/save-mapping` | login_only | — | routes/import_routes.py |
| GET | `/api/inventory/report` | require_perm | `inv.report.view` | routes/inventory_report_routes.py |
| POST | `/api/inventory/adjust` | helper_gated | — | routes/inventory_routes.py |
| POST | `/api/inventory/count` | helper_gated | — | routes/inventory_routes.py |
| POST | `/api/inventory/in` | helper_gated | — | routes/inventory_routes.py |
| GET | `/api/inventory/near-expiry` | helper_gated | — | routes/inventory_routes.py |
| GET | `/api/inventory/stock` | helper_gated | — | routes/inventory_routes.py |
| GET | `/api/inventory/warehouses` | helper_gated | — | routes/inventory_routes.py |
| POST | `/api/me/line_complete_email` | login_only | — | routes/line_account_merge_routes.py |
| GET | `/api/me/needs_email` | login_only | — | routes/line_account_merge_routes.py |
| DELETE | `/api/line/binding` | login_only | — | routes/line_binding_routes.py |
| GET | `/api/line/binding` | login_only | — | routes/line_binding_routes.py |
| POST | `/api/line/binding-code` | login_only | — | routes/line_binding_routes.py |
| POST | `/api/me/lang` | login_only | — | routes/line_binding_routes.py |
| POST | `/api/line/webhook` | public | — | routes/line_webhook_routes.py |
| POST | `/api/login` | public | — | routes/login_routes.py |
| GET | `/api/me` | login_only | — | routes/me_routes.py |
| PUT | `/api/me/profile` | login_only | — | routes/me_routes.py |
| GET | `/api/v1/me` | public | — | routes/me_routes.py |
| GET | `/api/v1/ocr/quota` | public | — | routes/meta_aliases_routes.py |
| POST | `/api/v1/ocr/recognize` | public | — | routes/meta_aliases_routes.py |
| GET | `/api/version` | public | — | routes/meta_aliases_routes.py |
| GET | `/api/me/modules` | pos_require_tenant | — | routes/modules_routes.py |
| PUT | `/api/me/modules/{module_key}` | require_perm | `settings.modules.manage` | routes/modules_routes.py |
| PUT | `/api/me/onboarding` | require_perm | `settings.modules.manage` | routes/modules_routes.py |
| GET | `/api/notifications/logs` | login_only | — | routes/notification_routes.py |
| GET | `/api/notifications/rules` | login_only | — | routes/notification_routes.py |
| POST | `/api/notifications/rules` | login_only | — | routes/notification_routes.py |
| DELETE | `/api/notifications/rules/{rule_id}` | login_only | — | routes/notification_routes.py |
| PATCH | `/api/notifications/rules/{rule_id}` | login_only | — | routes/notification_routes.py |
| POST | `/api/notifications/rules/{rule_id}/test` | login_only | — | routes/notification_routes.py |
| GET | `/api/auth/google/callback` | public | — | routes/oauth_routes.py |
| GET | `/api/auth/google/start` | public | — | routes/oauth_routes.py |
| GET | `/api/auth/line/callback` | public | — | routes/oauth_routes.py |
| GET | `/api/auth/line/start` | public | — | routes/oauth_routes.py |
| POST | `/api/ocr/export` | login_only | — | routes/ocr_export_routes.py |
| POST | `/api/ocr/export-by-history-ids` | login_only | — | routes/ocr_export_routes.py |
| GET | `/api/ocr/quota` | login_only | — | routes/ocr_export_routes.py |
| POST | `/api/v1/ocr/export` | public | — | routes/ocr_export_routes.py |
| POST | `/api/ocr/recognize` | login_only | — | routes/ocr_recognize_routes.py |
| GET | `/` | public | — | routes/pages_routes.py |
| GET | `/admin` | public | — | routes/pages_routes.py |
| GET | `/admin/{rest:path}` | public | — | routes/pages_routes.py |
| GET | `/api/contact` | public | — | routes/pages_routes.py |
| GET | `/api/health` | public | — | routes/pages_routes.py |
| GET | `/api/ready` | public | — | routes/pages_routes.py |
| GET | `/api/v1/contact` | public | — | routes/pages_routes.py |
| GET | `/api/v1/health` | public | — | routes/pages_routes.py |
| GET | `/console` | public | — | routes/pages_routes.py |
| GET | `/console/{rest:path}` | public | — | routes/pages_routes.py |
| GET | `/home` | public | — | routes/pages_routes.py |
| GET | `/invite/{token}` | public | — | routes/pages_routes.py |
| GET | `/login` | public | — | routes/pages_routes.py |
| GET | `/pos` | public | — | routes/pages_routes.py |
| GET | `/pos/{rest:path}` | public | — | routes/pages_routes.py |
| GET | `/privacy` | public | — | routes/pages_routes.py |
| GET | `/reset` | public | — | routes/pages_routes.py |
| GET | `/terms` | public | — | routes/pages_routes.py |
| GET | `/api/pos/admin/cashiers` | require_perm | `pos.admin.manage` | routes/pos_auth_routes.py |
| POST | `/api/pos/admin/cashiers` | require_perm | `pos.admin.manage` | routes/pos_auth_routes.py |
| DELETE | `/api/pos/admin/cashiers/{cashier_id}` | require_perm | `pos.admin.manage` | routes/pos_auth_routes.py |
| PUT | `/api/pos/admin/cashiers/{cashier_id}` | require_perm | `pos.admin.manage` | routes/pos_auth_routes.py |
| PUT | `/api/pos/admin/onboarding` | require_perm | `settings.modules.manage` | routes/pos_auth_routes.py |
| GET | `/api/pos/admin/store-code` | require_perm | `pos.admin.manage` | routes/pos_auth_routes.py |
| POST | `/api/pos/admin/store-code/reset` | require_perm | `pos.admin.manage` | routes/pos_auth_routes.py |
| POST | `/api/pos/auth/pin` | public | — | routes/pos_auth_routes.py |
| POST | `/api/pos/bind` | public | — | routes/pos_auth_routes.py |
| GET | `/api/pos/cashiers` | public | — | routes/pos_auth_routes.py |
| GET | `/api/pos/admin/business-presets` | require_perm | `settings.modules.manage` | routes/pos_modules_routes.py |
| GET | `/api/pos/admin/modules` | require_perm | `settings.modules.manage` | routes/pos_modules_routes.py |
| PUT | `/api/pos/admin/modules` | require_perm | `settings.modules.manage` | routes/pos_modules_routes.py |
| GET | `/api/pos/admin/onboarding-state` | require_perm | `settings.modules.manage` | routes/pos_modules_routes.py |
| GET | `/api/pos/admin/payment-settings` | helper_gated | — | routes/pos_payment_routes.py |
| PUT | `/api/pos/admin/payment-settings` | helper_gated | — | routes/pos_payment_routes.py |
| GET | `/api/pos/admin/report` | require_perm | `pos.report.view` | routes/pos_report_routes.py |
| GET | `/api/pos/admin/restaurant/areas` | helper_gated | — | routes/pos_restaurant_admin_routes.py |
| POST | `/api/pos/admin/restaurant/areas` | helper_gated | — | routes/pos_restaurant_admin_routes.py |
| DELETE | `/api/pos/admin/restaurant/areas/{area_id}` | helper_gated | — | routes/pos_restaurant_admin_routes.py |
| PATCH | `/api/pos/admin/restaurant/areas/{area_id}` | helper_gated | — | routes/pos_restaurant_admin_routes.py |
| GET | `/api/pos/admin/restaurant/tables` | helper_gated | — | routes/pos_restaurant_admin_routes.py |
| POST | `/api/pos/admin/restaurant/tables` | helper_gated | — | routes/pos_restaurant_admin_routes.py |
| DELETE | `/api/pos/admin/restaurant/tables/{table_id}` | helper_gated | — | routes/pos_restaurant_admin_routes.py |
| PATCH | `/api/pos/admin/restaurant/tables/{table_id}` | helper_gated | — | routes/pos_restaurant_admin_routes.py |
| GET | `/api/pos/restaurant/kitchen` | helper_gated | — | routes/pos_restaurant_routes.py |
| POST | `/api/pos/restaurant/kot/items/{line_id}/status` | helper_gated | — | routes/pos_restaurant_routes.py |
| POST | `/api/pos/restaurant/kot/{kot_id}/status` | helper_gated | — | routes/pos_restaurant_routes.py |
| GET | `/api/pos/restaurant/sessions/{session_id}` | helper_gated | — | routes/pos_restaurant_routes.py |
| GET | `/api/pos/restaurant/sessions/{session_id}/bill` | helper_gated | — | routes/pos_restaurant_routes.py |
| POST | `/api/pos/restaurant/sessions/{session_id}/cancel` | helper_gated | — | routes/pos_restaurant_routes.py |
| POST | `/api/pos/restaurant/sessions/{session_id}/checkout` | helper_gated | — | routes/pos_restaurant_routes.py |
| POST | `/api/pos/restaurant/sessions/{session_id}/lines` | helper_gated | — | routes/pos_restaurant_routes.py |
| DELETE | `/api/pos/restaurant/sessions/{session_id}/lines/{line_id}` | helper_gated | — | routes/pos_restaurant_routes.py |
| PATCH | `/api/pos/restaurant/sessions/{session_id}/lines/{line_id}` | helper_gated | — | routes/pos_restaurant_routes.py |
| POST | `/api/pos/restaurant/sessions/{session_id}/request-bill` | helper_gated | — | routes/pos_restaurant_routes.py |
| POST | `/api/pos/restaurant/sessions/{session_id}/send-kitchen` | helper_gated | — | routes/pos_restaurant_routes.py |
| GET | `/api/pos/restaurant/tables` | helper_gated | — | routes/pos_restaurant_routes.py |
| POST | `/api/pos/restaurant/tables/{table_id}/open` | helper_gated | — | routes/pos_restaurant_routes.py |
| GET | `/api/pos/bootstrap` | helper_gated | — | routes/pos_sales_routes.py |
| GET | `/api/pos/products` | helper_gated | — | routes/pos_sales_routes.py |
| GET | `/api/pos/products/by-barcode` | helper_gated | — | routes/pos_sales_routes.py |
| GET | `/api/pos/promptpay-qr` | helper_gated | — | routes/pos_sales_routes.py |
| POST | `/api/pos/sales` | helper_gated | — | routes/pos_sales_routes.py |
| GET | `/api/pos/sales/by-receipt` | helper_gated | — | routes/pos_sales_routes.py |
| POST | `/api/pos/sales/sync` | helper_gated | — | routes/pos_sales_routes.py |
| GET | `/api/pos/sales/{sale_id}` | helper_gated | — | routes/pos_sales_routes.py |
| POST | `/api/pos/sales/{sale_id}/full-tax-invoice` | helper_gated | — | routes/pos_sales_routes.py |
| GET | `/api/pos/sales/{sale_id}/promptpay-qr` | helper_gated | — | routes/pos_sales_routes.py |
| GET | `/api/pos/sales/{sale_id}/receipt-pdf` | helper_gated | — | routes/pos_sales_routes.py |
| POST | `/api/pos/sales/{sale_id}/refund` | helper_gated | — | routes/pos_sales_routes.py |
| POST | `/api/pos/sales/{sale_id}/void` | helper_gated | — | routes/pos_sales_routes.py |
| POST | `/api/pos/shifts/open` | helper_gated | — | routes/pos_sales_routes.py |
| POST | `/api/pos/shifts/{shift_id}/close` | helper_gated | — | routes/pos_sales_routes.py |
| GET | `/api/sales/products` | require_perm | `sales.product.manage` `sales.product.view` | routes/products_routes.py |
| POST | `/api/sales/products` | require_perm | `sales.product.manage` `sales.product.view` | routes/products_routes.py |
| POST | `/api/sales/products/import` | require_perm | `sales.product.manage` | routes/products_routes.py |
| GET | `/api/sales/products/lookup` | require_perm | `sales.product.view` | routes/products_routes.py |
| DELETE | `/api/sales/products/{product_id}` | require_perm | `sales.product.manage` `sales.product.view` | routes/products_routes.py |
| GET | `/api/sales/products/{product_id}` | require_perm | `sales.product.manage` `sales.product.view` | routes/products_routes.py |
| PATCH | `/api/sales/products/{product_id}` | require_perm | `sales.product.manage` `sales.product.view` | routes/products_routes.py |
| GET | `/api/sales/products/{product_id}/units` | require_perm | `sales.product.manage` `sales.product.view` | routes/products_routes.py |
| POST | `/api/sales/products/{product_id}/units` | require_perm | `sales.product.manage` `sales.product.view` | routes/products_routes.py |
| DELETE | `/api/sales/products/{product_id}/units/{unit_id}` | require_perm | `sales.product.manage` | routes/products_routes.py |
| PATCH | `/api/sales/products/{product_id}/units/{unit_id}` | require_perm | `sales.product.manage` | routes/products_routes.py |
| GET | `/api/purchase/categories` | auth_member | `purchase.doc.view` `purchase.supplier.manage` | routes/purchase_config_routes.py |
| POST | `/api/purchase/categories` | auth_member | `purchase.doc.view` `purchase.supplier.manage` | routes/purchase_config_routes.py |
| DELETE | `/api/purchase/categories/{category_id}` | auth_member | `purchase.supplier.manage` | routes/purchase_config_routes.py |
| PATCH | `/api/purchase/categories/{category_id}` | auth_member | `purchase.supplier.manage` | routes/purchase_config_routes.py |
| GET | `/api/purchase/settings` | auth_member | `purchase.doc.view` `purchase.settings.manage` | routes/purchase_config_routes.py |
| PUT | `/api/purchase/settings` | auth_member | `purchase.doc.view` `purchase.settings.manage` | routes/purchase_config_routes.py |
| GET | `/api/purchase/suppliers` | auth_member | `purchase.doc.view` `purchase.supplier.manage` | routes/purchase_config_routes.py |
| POST | `/api/purchase/suppliers` | auth_member | `purchase.doc.view` `purchase.supplier.manage` | routes/purchase_config_routes.py |
| DELETE | `/api/purchase/suppliers/{supplier_id}` | auth_member | `purchase.supplier.manage` | routes/purchase_config_routes.py |
| PATCH | `/api/purchase/suppliers/{supplier_id}` | auth_member | `purchase.supplier.manage` | routes/purchase_config_routes.py |
| POST | `/api/purchase/expense` | auth_member | `purchase.doc.create` | routes/purchase_intake_routes.py |
| GET | `/api/purchase/inbox` | auth_member | `intake.classify` | routes/purchase_intake_routes.py |
| POST | `/api/purchase/inbox/{item_id}/resolve` | auth_member | `intake.classify` | routes/purchase_intake_routes.py |
| POST | `/api/purchase/intake` | auth_member | `intake.upload` | routes/purchase_intake_routes.py |
| DELETE | `/api/purchase/attachments/{attachment_id}` | auth_member | `purchase.doc.edit` | routes/purchase_routes.py |
| GET | `/api/purchase/docs` | auth_member | `purchase.doc.create` `purchase.doc.view` | routes/purchase_routes.py |
| POST | `/api/purchase/docs` | auth_member | `purchase.doc.create` `purchase.doc.view` | routes/purchase_routes.py |
| DELETE | `/api/purchase/docs/{doc_id}` | auth_member | `purchase.doc.delete` `purchase.doc.edit` `purchase.doc.view` | routes/purchase_routes.py |
| GET | `/api/purchase/docs/{doc_id}` | auth_member | `purchase.doc.delete` `purchase.doc.edit` `purchase.doc.view` | routes/purchase_routes.py |
| PUT | `/api/purchase/docs/{doc_id}` | auth_member | `purchase.doc.delete` `purchase.doc.edit` `purchase.doc.view` | routes/purchase_routes.py |
| POST | `/api/purchase/docs/{doc_id}/attachments` | auth_member | `purchase.doc.edit` | routes/purchase_routes.py |
| GET | `/api/purchase/docs/{doc_id}/bill-image` | auth_member | `purchase.doc.view` | routes/purchase_routes.py |
| GET | `/api/purchase/docs/{doc_id}/document.pdf` | auth_member | `purchase.doc.view` | routes/purchase_routes.py |
| POST | `/api/purchase/docs/{doc_id}/pay` | auth_member | `purchase.doc.approve` | routes/purchase_routes.py |
| POST | `/api/purchase/docs/{doc_id}/post` | auth_member | `purchase.doc.approve` | routes/purchase_routes.py |
| POST | `/api/purchase/docs/{doc_id}/substitute-receipt` | helper_gated | — | routes/purchase_routes.py |
| POST | `/api/purchase/docs/{doc_id}/void` | auth_member | `purchase.doc.approve` | routes/purchase_routes.py |
| POST | `/api/purchase/docs/{doc_id}/wht-cert` | helper_gated | — | routes/purchase_routes.py |
| POST | `/api/purchase/lines/{line_id}/match-product` | auth_member | `purchase.doc.edit` | routes/purchase_routes.py |
| GET | `/api/purchase/summary` | auth_member | `purchase.doc.view` | routes/purchase_routes.py |
| POST | `/api/rd/lookup` | login_only | — | routes/rd_routes.py |
| POST | `/api/rd/verify` | login_only | — | routes/rd_routes.py |
| POST | `/api/v1/rd/lookup` | public | — | routes/rd_routes.py |
| POST | `/api/v1/rd/verify` | public | — | routes/rd_routes.py |
| POST | `/api/recon/bank-v2/confirm-rows/{job_id}` | require_perm | `recon.approve` | routes/recon_jobs_routes.py |
| POST | `/api/recon/bank-v2/submit` | require_perm | `recon.create` | routes/recon_jobs_routes.py |
| POST | `/api/recon/gl-vat/submit` | require_perm | `recon.create` | routes/recon_jobs_routes.py |
| GET | `/api/recon/jobs/{job_id}` | require_perm | `recon.view` | routes/recon_jobs_routes.py |
| POST | `/api/vat_excel/submit` | require_perm | `recon.create` | routes/recon_jobs_routes.py |
| GET | `/api/recon/export/{task_id}` | require_perm | `recon.export` | routes/recon_routes.py |
| GET | `/api/recon/progress/{pid}` | require_perm | `recon.view` | routes/recon_routes.py |
| GET | `/api/recon/result/{task_id}` | require_perm | `recon.view` | routes/recon_routes.py |
| POST | `/api/recon/row/{row_id}/action` | require_perm | `recon.create` | routes/recon_routes.py |
| POST | `/api/recon/row/{row_id}/analyze` | require_perm | `recon.create` | routes/recon_routes.py |
| PATCH | `/api/recon/row/{row_id}/field` | require_perm | `recon.create` | routes/recon_routes.py |
| POST | `/api/recon/run/{task_id}` | require_perm | `recon.create` | routes/recon_routes.py |
| POST | `/api/recon/task` | require_perm | `recon.create` | routes/recon_routes.py |
| GET | `/api/recon/tasks` | require_perm | `recon.view` | routes/recon_routes.py |
| GET | `/api/recon/bank-v2/tasks` | require_perm | `recon.view` | routes/recon_routes_bankv2.py |
| POST | `/api/recon/bank-v2/tasks/batch_delete` | require_perm | `recon.create` | routes/recon_routes_bankv2.py |
| DELETE | `/api/recon/bank-v2/{task_id}` | require_perm | `recon.create` `recon.view` | routes/recon_routes_bankv2.py |
| GET | `/api/recon/bank-v2/{task_id}` | require_perm | `recon.create` `recon.view` | routes/recon_routes_bankv2.py |
| GET | `/api/recon/bank-v2/{task_id}/export` | require_perm | `recon.export` | routes/recon_routes_bankv2.py |
| POST | `/api/recon/bank-v2/run` | require_perm | `recon.create` | routes/recon_routes_bankv2_run.py |
| POST | `/api/recon/gl-vat/run` | require_perm | `recon.create` | routes/recon_routes_glvat.py |
| GET | `/api/recon/gl-vat/tasks` | require_perm | `recon.view` | routes/recon_routes_glvat.py |
| POST | `/api/recon/gl-vat/tasks/batch_delete` | require_perm | `recon.create` | routes/recon_routes_glvat.py |
| DELETE | `/api/recon/gl-vat/{task_id}` | require_perm | `recon.create` `recon.view` | routes/recon_routes_glvat.py |
| GET | `/api/recon/gl-vat/{task_id}` | require_perm | `recon.create` `recon.view` | routes/recon_routes_glvat.py |
| GET | `/api/recon/gl-vat/{task_id}/export` | require_perm | `recon.export` | routes/recon_routes_glvat.py |
| POST | `/api/recon/batch_process` | require_perm | `recon.create` | routes/recon_routes_v1_batch.py |
| DELETE | `/api/recon/task/{task_id}` | public | — | routes/recon_routes_v1_batch.py |
| POST | `/api/recon/tasks/batch_delete` | require_perm | `recon.create` | routes/recon_routes_v1_batch.py |
| GET | `/api/reports/clients/{client_id}/export` | helper_gated | — | routes/report_routes.py |
| POST | `/api/reports/export` | helper_gated | — | routes/report_routes.py |
| POST | `/api/reports/history/batch_export` | helper_gated | — | routes/report_routes.py |
| GET | `/api/reports/templates` | helper_gated | — | routes/report_routes.py |
| GET | `/api/sales/documents` | require_perm | `sales.doc.create` `sales.doc.view` | routes/sales_routes.py |
| POST | `/api/sales/documents` | require_perm | `sales.doc.create` `sales.doc.view` | routes/sales_routes.py |
| DELETE | `/api/sales/documents/{doc_id}` | require_perm | `sales.doc.delete` `sales.doc.edit` `sales.doc.view` | routes/sales_routes.py |
| GET | `/api/sales/documents/{doc_id}` | require_perm | `sales.doc.delete` `sales.doc.edit` `sales.doc.view` | routes/sales_routes.py |
| PATCH | `/api/sales/documents/{doc_id}` | require_perm | `sales.doc.delete` `sales.doc.edit` `sales.doc.view` | routes/sales_routes.py |
| POST | `/api/sales/documents/{doc_id}/approve` | require_perm | `sales.doc.approve` | routes/sales_routes.py |
| POST | `/api/sales/documents/{doc_id}/convert` | require_perm | `sales.doc.create` | routes/sales_routes.py |
| POST | `/api/sales/documents/{doc_id}/credit-note` | require_perm | `sales.doc.approve` | routes/sales_routes.py |
| POST | `/api/sales/documents/{doc_id}/debit-note` | require_perm | `sales.doc.approve` | routes/sales_routes.py |
| POST | `/api/sales/documents/{doc_id}/issue` | require_perm | `sales.doc.approve` | routes/sales_routes.py |
| GET | `/api/sales/documents/{doc_id}/pdf` | require_perm | `sales.doc.view` | routes/sales_routes.py |
| GET | `/api/sales/documents/{doc_id}/promptpay-qr` | require_perm | `sales.doc.view` | routes/sales_routes.py |
| POST | `/api/sales/documents/{doc_id}/reject` | require_perm | `sales.doc.approve` | routes/sales_routes.py |
| POST | `/api/sales/documents/{doc_id}/submit` | require_perm | `sales.doc.create` | routes/sales_routes.py |
| POST | `/api/sales/documents/{doc_id}/void` | require_perm | `sales.doc.approve` | routes/sales_routes.py |
| GET | `/api/sales/sellers` | require_perm | `sales.doc.view` | routes/sales_seller_routes.py |
| GET | `/api/sales/sellers/{workspace_client_id}` | require_perm | `sales.doc.view` `sales.settings.manage` | routes/sales_seller_routes.py |
| PUT | `/api/sales/sellers/{workspace_client_id}` | require_perm | `sales.doc.view` `sales.settings.manage` | routes/sales_seller_routes.py |
| GET | `/api/sales/documents/shared/{token}/pdf` | public | — | routes/sales_send_routes.py |
| POST | `/api/sales/documents/{doc_id}/send` | require_perm | `sales.doc.approve` | routes/sales_send_routes.py |
| GET | `/api/sales/settings` | require_perm | `sales.doc.view` `sales.settings.manage` | routes/sales_settings_routes.py |
| PUT | `/api/sales/settings` | require_perm | `sales.doc.view` `sales.settings.manage` | routes/sales_settings_routes.py |
| POST | `/api/archive/rename-preview` | login_only | — | routes/settings_routes.py |
| GET | `/api/archive/settings` | login_only | — | routes/settings_routes.py |
| PUT | `/api/archive/settings` | login_only | — | routes/settings_routes.py |
| GET | `/api/settings/dup-check` | login_only | — | routes/settings_routes.py |
| PUT | `/api/settings/dup-check` | login_only | — | routes/settings_routes.py |
| GET | `/api/settings/erp-push-mode` | login_only | — | routes/settings_routes.py |
| PUT | `/api/settings/erp-push-mode` | login_only | — | routes/settings_routes.py |
| GET | `/api/admin/tenants` | super_admin | — | routes/tenant_routes.py |
| POST | `/api/admin/tenants` | super_admin | — | routes/tenant_routes.py |
| PATCH | `/api/admin/tenants/{tenant_id}/quota` | super_admin | — | routes/tenant_routes.py |
| PATCH | `/api/admin/tenants/{tenant_id}/status` | super_admin | — | routes/tenant_routes.py |
| GET | `/api/admin/tenants/{tenant_id}/summary` | super_admin | — | routes/tenant_routes.py |
| GET | `/api/me/tenant-usage` | login_only | — | routes/tenant_routes.py |
| POST | `/api/uploads/image` | helper_gated | — | routes/uploads_routes.py |
| GET | `/api/uploads/image/{tenant_id}/{name}` | helper_gated | — | routes/uploads_routes.py |
| POST | `/api/vat_excel/build` | helper_gated | — | routes/vat_excel_routes.py |
| GET | `/api/vat_excel/check` | login_only | — | routes/vat_excel_routes.py |
| GET | `/api/vat_excel/tasks/{task_id}/download` | helper_gated | — | routes/vat_excel_routes.py |
| POST | `/api/vat_excel/tasks/{task_id}/regenerate` | helper_gated | — | routes/vat_excel_routes.py |
| GET | `/api/vat_excel/tasks` | helper_gated | — | routes/vat_excel_tasks_routes.py |
| DELETE | `/api/vat_excel/tasks/clear_old` | helper_gated | — | routes/vat_excel_tasks_routes.py |
| DELETE | `/api/vat_excel/tasks/{task_id}` | helper_gated | — | routes/vat_excel_tasks_routes.py |
| GET | `/api/vat_excel/tasks/{task_id}` | helper_gated | — | routes/vat_excel_tasks_routes.py |
| GET | `/api/workspace/clients` | login_only | `settings.workspace.manage` | routes/workspace_routes.py |
| POST | `/api/workspace/clients` | require_perm | `settings.workspace.manage` | routes/workspace_routes.py |
| DELETE | `/api/workspace/clients/{workspace_client_id}` | require_perm | `settings.workspace.manage` | routes/workspace_routes.py |
| PATCH | `/api/workspace/clients/{workspace_client_id}` | require_perm | `settings.workspace.manage` | routes/workspace_routes.py |
| PUT | `/api/workspace/clients/{workspace_client_id}/endpoint` | require_perm | `settings.workspace.manage` | routes/workspace_routes.py |
