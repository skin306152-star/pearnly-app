# 交接 · 2026-06-25 · B8 多租户 RLS · P3 ready 域 prod 启用 + wave2 对账迁移(进行中)

> 给下一个窗口。本文 = 本窗口做了什么(✅)、还剩什么(⏳)、怎么接着做(🔧)。
> 权威细节:`docs/refactor/b8-rls-p3-rollout-readiness.md`(审计+runbook)、`docs/refactor/b8-rls-production-design.md`(P0 设计)、记忆 `[[rls-b8-p3-prod-enabled]]`。
> prod 当前:HEAD `f860b984` · 全 push · `/api/ready` 200 · RLS 对 ready 域 + 3 个对账任务表真隔离生效 · 老路径不受影响 · 随时可秒回滚。

---

## 〇、一句话

把 B8 RLS 从「设计完但默认全关」推到了「**ready 域 + 3 个对账任务表在 prod 真隔离生效**」。机制经 prod 真数据验证可行(还顺手抓修了一个本地证不出来的 Supabase 坑)。wave2 对账剩下的是**需要设计决策**的难活,不是机械迁移,已写清怎么接。

---

## 一、✅ 已完成(全部上线 + 验收)

### 1. P3 · ready 域 prod 真启用(本窗口最大成果)
- **commits**:`8e88464e`(审计+回滚脚本)/`ae4556ec`(会计 worker 修)/`ae41277c`(文档)。
- **动作**:prod 建 `pearnly_app` 角色(NOSUPERUSER NOBYPASSRLS NOLOGIN)→ Owner 后台 SQL Editor 跑 `GRANT pearnly_app TO postgres` → 金丝雀验证 → systemd `/opt/mrpilot/.env` 加 `RLS_ROLE=pearnly_app` + 重启。
- **真隔离生效的域**:POS / 库存 / 产品 / 采购 / 销售 / 会计 / 税 / 导出 / modules / LINE-brain(line_message_refs·chat_history·action_nonces)/ expense。
- **机制**:`get_cursor_rls` 事务里 `SET LOCAL ROLE pearnly_app`(非表 owner)→ ENABLE 的表 policy 强制隔离。裸 `get_cursor` 留 owner 连接 → force=False 时靠 owner 身份绕过 → 老路径不破。
- **验收证据**:本地集成矩阵 8/8 + 回滚脚本端到端(32 表→0)+ prod 金丝雀(journal_vouchers 自己 19/假租户 0/无上下文 0)+ 8 域多表隔离全 PASS + 真登录 `/api/me/modules` 正确返回 tenant_modules。

### 2. 会计 posting_failures worker 加固(ready 域唯一代码缺口)
- **commit**:`ae4556ec`。`claim_due` 跨租户认领 → `get_cursor_rls(bypass=True)`;`retry_one` 单行重过账 → `get_cursor_rls(tenant_id, workspace_client_id)`。契约测试 `test_posting_failures_rls_contract`。

### 3. wave2 · 3 个自包含对账任务表迁移 + enroll(真隔离生效)
| 表 | commit | store 模块 | 验证 |
|---|---|---|---|
| `vat_recon_tasks` | `cd6a3d7e` | `services/recon/vat_recon_tasks_store.py` | 本地真隔离 + prod 金丝雀 own 12/12 |
| `gl_vat_task` | `8722b8b5` | `services/recon/gl_vat_store.py` | 本地(含 delete-by-tenant)+ prod enroll |
| `bank_recon_v2_task` | `a1e68aae` | `services/recon/bank_recon_v2_store.py` | 本地(含 delete-by-tenant)+ prod enroll |
- 三表都是 `tenant_or_user` 模板(tenant 可空 + user 兜底)。
- **★ 抓修的 money 陷阱**:`delete_*` 原来只按 user_id,RLS 下 tenant 拥有的任务不可见会**静默删 0 行** → 给 delete/batch 加 `tenant_id` 参数(默认 None 向后兼容),路由传 `user.get("tenant_id")`。
- `/simplify` 收口(`f860b984`):拍平测试辅助多余的 `_both()` 内嵌层。

### 4. 交付物(durable)
- `scripts/rls_rollback.sql`:数据驱动回滚(遍历 `tenant_isolation` policy 表·NO FORCE + DISABLE·不硬编码防漂移)。
- `docs/refactor/b8-rls-p3-rollout-readiness.md`:审计 + runbook + 两处 prod 实测纠正 + wave 表。
- 记忆 `[[rls-b8-p3-prod-enabled]]`。

### 5. ★ 两个 prod-only 坑(金丝雀抓到·本地永远证不出来·下次必记)
1. **Supabase `postgres` 非 BYPASSRLS**(`rolbypassrls=False`)· 它绕过靠**表 owner 身份** → **ready 域 + 已迁表都保持 `force=False`**(force=True 会把 owner 也纳入 policy → 裸 get_cursor 被拦·风险倒挂)。
2. **`SET LOCAL ROLE` 要求连接角色是目标角色成员**·Supabase `postgres` **不能经 pooler 授成员**(GRANT 经 6543/5432 被掐 SSL·直连 db 主机 IPv6-only 够不到)→ **唯一可行 = Owner 后台 SQL Editor 跑 `GRANT pearnly_app TO postgres`**(已跑·一次性·存 pg_auth_members 全局)。**没这步设 env 全站 500。** ⚠️ 别加进 `ensure_rls_app_role`(startup 经 pooler 会崩)。

---

## 二、⏳ 待完成

### wave2 剩余(对账·两类难活·需设计不是机械迁移)
**A. `vat_recon_store`(vat_report + reconciliation_task/row)+ `bank_recon_v1_store`/`bank_recon_match`** — 三个结构性障碍:
- `reconciliation_row` **无 tenant_id 列**(仅 task_id)→ 现有 3 个模板套不上。
- `vat_report` **只有 tenant_id 没 user_id** → 只能纯 tenant 模板·孤立用户行(tenant 空)会全员不可见。
- **~10 个函数只收 id 不收租户上下文**(`get_recon_row(row_id)`/`update_recon_row_action(row_id)`/`get_recon_task(task_id)`/`update_recon_task_status`/`get_vat_report(report_id)`…)。
- `bank_recon_v1` 同样 JOIN `ocr_history`(wave3 表)。

**B. `recon_jobs` worker**(`services/recon_jobs/store.py`):`claim_next`/`finish`/`fail`/`reclaim_stale`/`gc_old` 是跨租户队列 → `get_cursor_rls(bypass=True)`;`enqueue`/状态查询带上下文。**注**:recon_jobs 表当前未 enroll,所以这是 prep——除非也 enroll recon_jobs 否则只是统一游标。

**C. `knowledge_bridge`**(`services/exceptions/knowledge_bridge.py` 4 处):读 `ocr_history`/`client_rules`(wave3 表)→ 纯游标迁移·隔离落 wave3。

### wave3(老模块·~62 处·更敏感)
clients / exceptions / notification / billing / credits / cost / ocr_history / archive。**billing `charge.py` 钱路径最危险**;credits/cost 超管聚合必须 `bypass=True`(否则报表归零)。统一 `tenant_or_user` 模板。ocr_history enroll 后 wave2 的 knowledge_bridge/recon 跨表 JOIN 才真隔离。

### wave4(erp/email/import·~30 处)
后台扫描(push_retry / email list_enabled / agent get_express_endpoint)走 bypass。

### P4 收尾
`tests/e2e/12-rls-isolation.spec.js` 断言从 `passed>=2` 收紧到 `passed===5`(prod 已启用·应能过 5)。

---

## 三、🔧 怎么完成

### A. 已验证稳定的「自包含 task 表」套路(前 3 个就这么干的·照抄)
适用:store 函数签名里**本就有 tenant_id/user_id** 的表。
1. **store 文件**:`from core.rls import apply_tenant_or_user_rls`(或 `apply_tenant_rls`,看表有无 user_id 列);ensure_* 建表后加一行 `apply_tenant_or_user_rls(cur, "<表>")`。
2. **每个读写函数**:`db.get_cursor(...)` → `db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, workspace_client_id=workspace_client_id, commit=...)`(传函数签名里现成的上下文·None 自动跳过)。
3. **按 user_id 删的函数**:加 `tenant_id=None` 参数,路由调用方传 `user.get("tenant_id")`——否则 RLS 下 tenant 任务删 0 行(money 陷阱)。
4. **测试**:受影响的 mock-cursor 辅助(`patch_cursor`/`_patch`/`_patch_cursor` 等)改成**同时 patch `get_cursor` 和 `get_cursor_rls`**(指向同一假游标);加契约测试锁定 `get_cursor_rls` 注入了 tenant+user(参 `test_vat_recon_tasks_rls_contract.py`)。
5. **守门**:black + ruff + `python -m unittest discover -s tests/unit`(全量)+ check_file_size + check_line_ratchet(多行 kwargs 会涨行·加 `RATCHET-EXEMPT: <file> +N · ... · 删除 deadline = wave2 完`)。
6. **本地真隔离验证**(docker db):见下「本地验证脚手架」。
7. **提交 + push**(webhook 自动部署重启 → ensure 跑 → 表自动 enroll)→ **prod 金丝雀**(见下)。

### B. wave2 难活的设计决策(动手前先定)
1. **`reconciliation_row`(无 tenant 列)** 二选一:
   - **方案①(推荐·更深)**:给 `core/rls.py` 加**传递式 policy 模板** `apply_via_parent_rls(cur, table, parent_table, fk_col, parent_key)`,谓词 = `EXISTS (SELECT 1 FROM <parent> p WHERE p.id = <table>.<fk> AND <parent 已是 tenant_or_user 可见>)` 或直接 `<fk> IN (SELECT id FROM <parent>)`(parent 已 enroll → 子查询自动被 parent 的 policy 过滤)。给它写单测(仿 `test_core_rls.py`)。
   - **方案②(保守)**:`reconciliation_row` **不 enroll**,其 id-only 函数保持裸 `get_cursor`(owner 绕过)——靠路由 authz + 父 `reconciliation_task` 已 enroll 间接保护。代价:该表无第二道防线。
2. **`vat_report`(无 user_id)**:先查 prod 有无孤立 vat_report(`SELECT count(*) FROM vat_report WHERE tenant_id IS NULL`)。无 → 安全用 `apply_tenant_rls`;有 → 要么回填 tenant,要么也走方案①经父任务。
3. **id-only 函数穿上下文**:`get_recon_task(task_id)` 等加 `tenant_id`/`user_id` 参数(默认 None),改所有调用方(routes/recon 引擎)传上下文。**这是 wave2 剩余的主要工作量**·逐函数 grep 调用点。

### C. 本地验证脚手架(每个域照用)
```bash
# docker db 起:docker compose start db
export DATABASE_URL="postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly"
export RLS_ROLE=pearnly_app PGSSLMODE=disable PYTHONUTF8=1
# 脚本:ensure_rls_app_role + GRANT pearnly_app TO current_user(本地 owner 可)+ ensure_<表>
#       + 2 租户各 create + 断言 list/get/delete 跨租户拿不到、删不掉对方、删得掉自己 tenant 的。
# 模板见本窗口对话里 vat_recon_tasks/gl_vat/bank_recon_v2 的本地验证片段。
# 集成矩阵(三模板回归):
PEARNLY_INTEGRATION_DB=1 RLS_ROLE=pearnly_app PGSSLMODE=disable \
  python -m unittest tests.integration.test_rls_isolation_matrix -v   # 期望 8/8
```

### D. prod 金丝雀(每个域 enroll 后·只读+rollback·不改数据)
脚本(scp 到 prod 跑 `cd /opt/mrpilot && venv/bin/python /tmp/x.py`):从 `.env` 取 DATABASE_URL → 找该表一个有数据的 tenant → 事务里 `SET LOCAL ROLE pearnly_app` + `SET LOCAL app.current_tenant_id` → 比 own/fake/none 三种计数(own==全量·fake==0·none==0)→ ROLLBACK。模板见本窗口 `/tmp/rls_vat_canary.py`。

---

## 四、坑 / 资源(接手必读)
- **共享工作树**:push 前 `git pull --rebase` 会因别窗口未跟踪文件报 unstaged(无害)·**只 `git add` 自己文件 + 显式 pathspec commit**(`git commit -- <files>`)·绝不 `add -A`/裸 commit。提交后 `git diff-tree --no-commit-id --name-only -r HEAD` 核实只含自己的。
- **改监控文件涨行**:多行 get_cursor_rls kwargs 必涨 → commit 带 `RATCHET-EXEMPT`。
- **循环导入**:直接首个 import recon store 会触发 `core.db ↔ dal_reexports` 循环(预存·非新引入)——测试文件先 `import core.db` 再 import store 即可。
- **prod 访问**:`ssh root@66.42.49.213` → `/opt/mrpilot` venv·DATABASE_URL 在 `.env`(pooler 6543)·查库用 `venv/bin/python`。
- **部署**:push master → webhook pull+cp+restart(~25s)→ ensure_* 跑 → 新表 enroll。验 `curl https://pearnly.com/api/version`(200)+ 扫 `journalctl -u mrpilot --since "90 sec ago"` 无 error。
- **回滚**:① 删 `.env` 的 `RLS_ROLE` 行 + `systemctl restart mrpilot`(秒级·全站退回绕过)② `psql -f scripts/rls_rollback.sql`。备份 `/opt/mrpilot/.env.bak_rls_*`。
- **CI**:`gh run list --repo skin306152-star/pearnly-app --branch master`(gh 路径见 PARALLEL_LOOP_DISPATCH §操作提醒)。
- **测试账号**:env `PEARNLY_E2E_USER/PASS`(已配)·登录端点字段是 `username` 不是 email。

---

## 五、状态总览
- HEAD `f860b984` · 无未 push · prod `/api/ready` 200。
- 真隔离生效:ready 域(11 组)+ `vat_recon_tasks`/`gl_vat_task`/`bank_recon_v2_task`。
- 守门:全量单测 4768 OK · ratchet PASS · CI 绿。
- 未完成:wave2 剩余(见 §二·需设计)/ wave3 / wave4 / P4。
