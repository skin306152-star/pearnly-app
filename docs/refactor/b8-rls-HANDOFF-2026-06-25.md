# B8 多租户 RLS · 交接(2026-06-25 收尾)

> 接手先读:本文件 + `b8-rls-no-policy-orphans-INCIDENT.md`(事故全程)+ 记忆 `rls-b8-p3-prod-enabled.md`。
> 设计源:`b8-rls-production-design.md` / `b8-rls-wave2-closure-design.md`。实时数字跑 `scripts/refactor_progress.py`。

## 0. 一句话现状

ready 域 + wave2 对账 + bank_reconcile_* + wave3 3a 核心(ocr_history/clients)**已 prod 真隔离并验收**。
本窗口处理了一次 **P0 生产事故**(孤儿表 deny-all 把识别记录/LINE/推送读空),已全量止血 + 落代码自愈守卫。
**B8 未完结**:wave3 外围 + 3b/3c/3d + wave4 + P4,外加事故衍生的「71 张孤儿表按域 re-enroll」。

## 1. 本窗口已完成(prod live · CI 绿)

| commit | 内容 |
|---|---|
| `8ba73117` | 事故止血:prod 全量 DISABLE 72 张零-policy 孤儿表 + `core/rls.disable_orphan_rls`/`ensure_no_orphan_rls` startup 自愈守卫 + 事故文档 §6 + 守卫单测 |
| `6b83e9b6` | /simplify 收口:模块级 logger、守卫挪进 `run_startup` 的 ddl 锁块(结构保证 DDL 全完才扫)、松测试 |

**自愈守卫机制**:`run_startup` 的 `with startup_ddl_lock(): _boot_schema_ddl()` 之后跑 `ensure_no_orphan_rls()`
→ 扫 `relrowsecurity=true AND 0 policy` 全 DISABLE。真 enroll 的表此时已有 policy(被排除),只关残留孤儿。
幂等、每部署一次、与按域 enroll 完全兼容(enroll 后有 policy → 不在孤儿集)。

**prod 核验(role 上下文真数据)**:孤儿残留 0 · OCR 识别记录 app 角色可读 21 · `users` 根因表可读 1 · ERP 推送 2 · LINE 绑定 4 · 跨租户 fake=0 隔离仍在。

## 2. ★事故衍生的新债:71 张孤儿表按域 re-enroll(优先级最高的剩余项)

事故里为止血把 72 张「RLS-on 零-policy」全 DISABLE 了。其中 `users`/`tenants`/`roles`/`rd_cache`/审计日志
等本就是设计 §6「不开 RLS」→ DISABLE 即终态,**不用动**。但**数据隔离表**(`sales_documents`/`products`/
`exceptions`/`erp_*`/`notification_*` 等)是「本应有 policy 却缺失」→ 现在 disabled(单租户无暴露,但无隔离)。
**proper 终态 = 按域 enroll**(`apply_*_rls` 一调即从 disabled 恢复成隔离,无需先 enable)。

**每表用哪个模板** = `INCIDENT.md` §2 已按隔离列分好类(`tenant_or_user` / `tenant` / `tenant_ws` / `user` / 不开)。
按下面 wave 分批迁,**enroll 时连同把该表所有访问点的裸 `get_cursor` 换成 `get_cursor_rls` 穿 tenant+user**
(只 enroll 不迁访问点 = owner 绕过 = 假隔离)。

> LINE 窗口在事故里已给 `workspace_clients` 补了 `tenant_or_user` policy(它现有 policy、不在孤儿集)。
> **但代码里 `ensure_workspace_tables` 还没加 `apply_tenant_or_user_rls`** → 下次某环境重建会再成孤儿被守卫关掉。
> **wave3 3b 第一件事:把 workspace_clients 的 enroll 落进 `ensure_workspace_tables` + 集成测试。**

## 3. 剩余 wave(按序 · 沿用 wave2/3a 套路)

### wave3 3a 外围收口(enroll 后裸 get_cursor 仍 owner 绕过 · 安全但未隔离)
- `sales/seller_profile.get_buyer`(只穿 tenant 漏 user)、`workspace/seller_routing`+`list_stats`、
  routes(clients CSV 导出 / billing usage / auth_me 的 OCR 计数 / history PDF 计数)→ 穿上下文。
- `erp/push_log_queries` + `mappings_store` 的 JOIN(只收 user_id,强转会丢富化)→ **归 wave4** 与 erp_push_logs 一起迁。
- 超管(`admin_users_query`/`auth_admin_risk`/membership migration/usage cleanup/`owner_users`)→ **显式 bypass**(登记系统级理由)。

### wave3 3b/3c/3d
- 3b:`workspace_clients`(见 §2)+ `exceptions`/`exception_whitelist`(tenant_or_user)。
- 3c:`notification_*`(tenant_or_user)+ `archive_settings`。
- 3d:billing —— **`charge.py` 钱路径禁 bypass**(decimal·铁律);`credits`/`cost` 超管聚合**必 bypass**。

### wave4
- `erp_*`(endpoints/push_logs/mappings/oauth)、`email_ingest_*`、`import_template_*`。push_logs 的 JOIN 富化是难点(见 3a)。

### P4 收口
- `tests/e2e/12-rls-isolation.spec.js` 断言 `passed>=2` → `passed===5`。
- **重写 `core/db.py:run_rls_isolation_tests` harness**:现在建临时 `tenant_isolation_test` policy + cleanup 会 DISABLE clients RLS(clients 已永久 enroll → cleanup 在 `if rls_was_off_before` 内不跑 → 安全,但残留无害冗余 policy)。改成测真 policy 不建临时。
- ready 域裸 get_cursor 清零后上 `force=True`(收尾,非启用前置)。

## 4. 不开 RLS(设计裁决 · 别去 enroll)
`line_voice_quota` / 订阅·付款·改密日志 / `users`·`tenants` 根表 / `roles` / `rd_cache`·`rd_daily_usage` /
`billing_balance_log` / `alembic_version` / 审计日志类。这些 DISABLE 即终态。

## 5. ★坑(prod 验证踩过 · 接手必看)
1. **Supabase `postgres` 非 BYPASSRLS** → ready/已 enroll 域**别上 `force=True`**(会把 owner 也纳入 policy,裸 get_cursor 的 DDL/未迁 row-op 被拦查空)。force=True 是「该域裸 get_cursor 清零」后的收尾。
2. **`GRANT pearnly_app TO postgres` 只能在 Supabase 后台 SQL Editor 跑一次**(pooler/直连都够不到)。没它设 `RLS_ROLE` 全 500。**别加进 `ensure_rls_app_role`**(startup 经 pooler 会崩)。
3. **金丝雀必须走真 store 函数**,不止验 policy 谓词——本次事故就是金丝雀只跑 `SELECT count(*) FROM ocr_history`(直查正常)漏了 `list_ocr_history` 的 `users` 子查询。迁角色前**扫该查询触及的全部表**(含 JOIN/子查询)在角色下可读。
4. **回滚(零数据风险)**:删 `/opt/mrpilot/.env` 的 `RLS_ROLE` 行 + `systemctl restart mrpilot`(owner 连接退回全绕过)/ 表级 `scripts/rls_rollback.sql`。备份 `/opt/mrpilot/.env.bak_rls_*`。
5. **共享工作树**:多窗口同一 checkout,`git add` 只显式列自己文件的 pathspec,绝不 `git add -A`/`.`。本窗两 commit 与另一窗口 express 改动线性交错无冲突即此纪律之效。
6. **守门**:集成测试 `docker compose up -d db` + `PEARNLY_INTEGRATION_DB=1 RLS_ROLE=pearnly_app PGSSLMODE=disable`。本 clone pre-push 需手动跑 + `PYTHONUTF8=1` 治 charmap。

## 6. 验证设施
- 单测:`tests/unit/test_disable_orphan_rls_contract.py`(守卫)、`test_ocr_history_clients_rls_contract.py`(wave3 契约)。
- 集成(docker pg):矩阵 8 + 传递式 5 + recon 端到端 3 + bank 真表 4 + clients/ocr_history 真表 3 + 模板 4。
- prod 金丝雀:见 §5.3 套路(SET LOCAL ROLE pearnly_app + 真 user_id/tenant_id + 真 store 路径)。
- 孤儿自检 SQL(owner)见 `INCIDENT.md` §3。
