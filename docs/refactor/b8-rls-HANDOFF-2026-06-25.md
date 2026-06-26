# B8 多租户 RLS · 交接(2026-06-25 起 · 末次更新 2026-06-26)

> 接手先读:本文件 + `b8-rls-no-policy-orphans-INCIDENT.md`(事故全程)+ 记忆 `rls-b8-p3-prod-enabled.md`。
> 设计源:`b8-rls-production-design.md` / `b8-rls-wave2-closure-design.md`。实时数字跑 `scripts/refactor_progress.py`。
>
> **⚡ 2026-06-26 续:wave3 3b/3c/3d + 3a 外围收口已全部 prod live + CI 绿 + 金丝雀验过。最新进度见文末 §7「2026-06-26 收尾」——接手从那读起,§1~§3 是 06-25 基线快照(部分已被 §7 推进,以 §7 为准)。**

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

## 7. 2026-06-26 收尾(wave3 3b/3c/3d + 3a 外围 · prod live + CI 绿)

> 本节是当前权威进度。§1~§3 是 06-25 的基线快照,凡与本节冲突以本节为准。

### 7.1 本窗口已完成(全 prod live · CI 全 6 闸绿 · 金丝雀验过)

| commit | wave | 内容 | 金丝雀 |
|---|---|---|---|
| `fd847e54` | 3b | workspace/exceptions 域 enroll + DAL 穿上下文 | 真租户自见 / 假 0 |
| `c0ef628b` | 3c | notification + archive(`archive_settings`)enroll;`update_ocr_history_pages` 迁 get_cursor_rls | 同上 |
| `cfe232b8` | 3d | billing 钱表(`tenant_credits`/`credit_transactions`/`monthly_page_usage`/`topup_requests`)+ `ocr_cost_log` enroll;`charge.py` 3 游标穿 tenant**禁 bypass**;`account_status`/`cost.store` 迁 | 真租户 balance 99万(未被 RLS 清零)/ 假 0 |
| `5e3917f8` | 3a 外围 | enroll 后裸 get_cursor 穿上下文:`auth_me`(OCR 计数)/`clients`(CSV 导出)/`billing_credits`(5 游标)/`erp/mappings_store`;超管路径(`admin_users_query`/`auth_admin_risk`/`auth_admin`/membership migration/`usage.store`/`owner_users`)→**显式 bypass=True** 带系统级理由注释 | auth_me ocr=21 / billing breakdown 21·credit_tx 57 / 假租户全 0 |
| `0c930f4c` | /simplify 收口 | 抽 `tests/unit/_cursor_patch.py`(`patch_both` + `CursorPatchProxy`「双挂 get_cursor/get_cursor_rls」)· 6 个 contract 测试复用 · 纯测试基建净 −63 行 | 测试 only |

**3c CI 历史坑(已向前盖绿)**:`c0ef628b` 当时 `archive/store.py +27` 漏 `RATCHET-EXEMPT` + 新 `ensure_archive_settings_table` 触 lint-debt,两道 **per-commit** 闸(push 用 `HEAD~1..HEAD`)红;豁免必须写进**同一 commit**,事后无法补(master 禁强推)。**3d/3a 外围干净 → head 已绿**,prod 不受影响。教训已并入 §5。

### 7.2 钱路径纪律(本窗口落实 · 接手别破)

- `services/billing/charge.py`:`charge_ocr` 读/写、`deduct_thb` 全走 `get_cursor_rls(tenant_id=..., commit=True)`,**绝不 bypass**(decimal·铁律·钱必经 RLS 二道闸)。
- `services/billing/credits_schema.py` / `cost/store.py`:enroll + 业务读写穿上下文;**超管聚合**(账单总览跨租户)才 `bypass=True`,且每处带「为什么是系统级」注释。
- 判据:**普通业务读自己租户 → 穿 tenant/user;跨租户聚合/迁移/后台任务 → 显式 bypass + 注释**。裸 get_cursor 仍是 owner 连接(force=False 不拦),老路径不破——所以 enroll 安全,迁移可逐函数推进。

### 7.3 「patch both」测试范式(`tests/unit/_cursor_patch.py`)

store 模块迁移期会同时存在 已迁(get_cursor_rls)/未迁(get_cursor)函数。测试用 `patch_both(value=cur)` 或 `patch_both(factory=...)` 把**两个游标都挂到同一 fake**,`CursorPatchProxy` 从「实际被调的那个」取 `call_args`(断言 `commit` kwarg)。坑:抽出 helper 后 membership/tenant 测试单跑会 `circular import`(**预存**,非本次引入——committed 版单跑也崩,只在成组跑时过),修法=文件顶 `from core import db  # noqa: F401` 先破环。

### 7.4 仍未完成(交给下一窗口 · 按序)

1. **★ 71 张孤儿表按域 re-enroll**(事故止血时全 DISABLE,proper 隔离待补)——优先级最高。模板分类见 `INCIDENT.md` §2。
2. **wave4**:~~`erp_*_mappings`(client/account/tax/product)~~ ✅ 已 enroll(见 §7.7,`3f337517`)。剩 `erp_endpoints`/`erp_push_logs`/`erp_oauth_*`、`email_ingest_*`、`import_template_*`。**`erp_push_logs` 的 JOIN 富化是难点**——`push_log_queries` + `mappings_store` 的 JOIN 只收 user_id,强转会丢富化,刻意留到此处与 push_logs 一起迁(见 §3 wave4)。注:`erp_endpoints`/`erp_push_logs` prod 上无 CREATE 钩子(legacy·只 `push_schema.py` 的 ALTER ensure_*),INSERT 走 `user_id`(无 tenant_id)→ 多半 `apply_user_rls`;`erp_oauth_*`/`mrerp_credentials`/`erp_connectors` 当前代码树无 CREATE 也无访问点(纯 prod 孤儿,需先决定是否重建 creator)。
3. **P4 收口**:`tests/e2e/12-rls-isolation.spec.js` 断言 `passed===5`(现 `>=2`);重写 `core/db.py:run_rls_isolation_tests` harness(别建临时 policy);ready/已 enroll 域裸 get_cursor 清零后才上 `force=True`(收尾,非启用前置)。
4. **预存测试脆性**(非本窗口引入,记录备查):`test_billing_contract.py:100` 模块级 `_ensure_stub_bcrypt()` 往 `sys.modules` 装假 bcrypt(`hashpw` 返明文),仅当 bcrypt 未先导入时生效。全量套件 bcrypt 先被导入 → stub no-op → **4970 全绿**;但 `billing→tenant` 两文件单独成对跑会让 `test_create_owner_user...` 因密码未 hash 失败。**真闸是全量套件(绿)**,接手别被子集误导。彻底修=把 stub 改成 fixture 级 setUp/tearDown 或用真 bcrypt。

### 7.5 验证记录(本窗口)

- 全量单测 **4970 passed, 3 skipped**(`PYTHONUTF8=1 python -m pytest -q tests/unit`)。
- CI 全 6 闸绿(run `28232941566`):lint-size / import+i18n+unit+vite+e2e / lint-ui / lint-routes / lint(black+ruff+prettier+eslint)/ lint-debt。
- 三道 per-commit 闸本地复跑:ratchet PASS(净增 ≤0)、new_debt PASS、file_size PASS。
- prod 金丝瓜见 7.1 表;套路同 §5.3(`SET LOCAL ROLE pearnly_app` + 真 user_id/tenant_id + 走真 store 函数,不止验 policy 谓词)。

### 7.6 共享树事故(本窗口踩 · 接手引以为戒)

1. **另一窗口 `git commit -a`/`git add .` 把我保存未提交的 `history_routes.py`/`push_store.py` 编辑卷进它的 `63c13b97`**(push_store bypass 后被 `822778c0` 还原——裸=owner bypass 安全)。**教训:共享树里改完立即提交自己文件,别留在工作树过夜。**
2. **误 `git stash pop` 把另一窗口 `stash@{0}`(feat/express-fe-p3b)弹出**致 6 文件 UU 冲突。安全恢复=`git checkout --ours -- <files>`(取 pop 前工作树即 HEAD)+ `git reset -- <files>`(退回未暂存),**stash@{0} 完整保留在列表供其窗口正常 pop**。`git stash` 是仓库级共享栈,多窗口下危险——**别 stash,要么提交要么留工作树**。

## 7.7 2026-06-26 wave4 第一棒 · erp 4 张映射表 enroll(prod live · CI 绿 · 金丝雀 PASS)

| commit | 内容 | 金丝雀 |
|---|---|---|
| `3f337517` | `erp_client/account/tax/product_mappings` enroll `apply_tenant_rls`(纯 tenant·落 `ensure_erp_mapping_tables`·force=False)+ 11 个裸 get_cursor 访问点穿 `get_cursor_rls(tenant_id=...)` | 真租户 040f012b… 经真 DAL `list_erp_account_mappings` 自见 5 行 / 假租户 0;4 表 rls=on npol=1 |

- **模板判据**:4 张表 `tenant_id NOT NULL` + `created_by`(**无 `user_id` 列**)→ 必须 `apply_tenant_rls`(纯 tenant);用 `tenant_or_user` 会因谓词引用不存在的 `user_id` 列在建 policy 时报错。对上 `INCIDENT.md` §2 把这 4 张归 `tenant` 类。
- **访问点**:client list/upsert 早已穿(wave3 期);本棒补 account/tax/product 全 CRUD + client delete + product batch find,共 11 处。直接 SQL 只在 `mappings_store.py`/`product_mappings_store.py` 两文件(其余 sales_mapper/mapper/mrerp_* 走 store 函数,无需动)。
- **验证**:集成 `tests/integration/test_erp_mappings_rls_real_tables.py`(docker pg·FORCE RLS)5 例(account/tax/product 真 DAL 跨租户隔离 + WITH CHECK 拦跨租户写 + client 直 SQL 隔离);全量 4970 单测绿;CI run `28234248951`(含本 commit 的树)6 闸全绿。
- **坑**:contract/coverage 测试用 `_cursor_patch.patch_both` 双挂 get_cursor/get_cursor_rls → 迁移不破 mock(56 单测无改动即过)。ratchet:`mappings_store.py +11`(enroll 块)已 `RATCHET-EXEMPT`;新测试在 `tests/` 前缀豁免。
