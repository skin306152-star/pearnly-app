# B8 多租户 RLS · wave2 收尾闭环 · 实施决策(2026-06-25)

> 上游:`b8-rls-production-design.md`(P0)、`b8-rls-p3-rollout-readiness.md`(P3 审计 + runbook)。
> 本文记录 wave2 收尾的**已落地决策**(非建议):传递式 policy、上下文穿线、bypass 登记册、wave3/4 分类、P4 收口。每条决策附「为什么」与「测试在哪」。

---

## 1. 两个 hard policy 设计点(已落地)

### hard point 1:`reconciliation_row` 无 tenant_id → 经 task_id 传递式隔离

`reconciliation_row` 只有 `task_id`(FK→`reconciliation_task`),无 `tenant_id`/`user_id`,3 个现有模板(tenant / tenant_ws / tenant_or_user)都套不上。

**决策**:给 `core/rls.py` 加第 4 个模板 `apply_tenant_via_parent_rls(table, parent, fk)` —— policy 谓词是对父表的 `EXISTS` 子查询:

```sql
USING (
  EXISTS (SELECT 1 FROM reconciliation_task _p
          WHERE _p.id = reconciliation_row.task_id
            AND (_p.tenant_id::text = current_setting('app.current_tenant_id', true)
                 OR (_p.tenant_id IS NULL
                     AND _p.user_id::text = current_setting('app.current_user_id', true))))
  OR current_setting('app.bypass_rls', true) = 'on')
```

- 父表 `reconciliation_task` 本就是 `tenant_or_user` 隔离,子查询复用同款谓词(经别名 `_p`)。
- `WITH CHECK` 同款:INSERT/UPDATE 子行时,其 `task_id` 必须指向**本租户可见**的 task → 不能往别租户的 task 塞行。
- `field_override` 写 `reconciliation_row.field_overrides` 同受此 policy 约束。
- **为什么不给 row 加 tenant_id 冗余列**:会引入父子 tenant 不一致的写入风险(冗余列要靠触发器同步),传递式 policy 让父表成为唯一真相源。

**测试**:集成矩阵 `test_rls_isolation_matrix.py` 新增 `rls_m_parent`(tenant_or_user)+ `rls_m_child`(经 parent_id 传递)一组穿透用例(跨租户读/写/改/删 + bypass)。

### hard point 2:只收主键的函数必须补租户上下文

`get_recon_row(row_id)` / `update_recon_row_action(row_id)` / `get_recon_task(task_id)` / `update_recon_task_status(task_id)` / `update_recon_task_completed(task_id)` / `list_recon_rows(task_id)` / `list_recon_rows_detailed(task_id)` / `update_recon_row_ai_analysis(row_id)` / `bulk_insert_recon_rows(rows)` / `get_vat_report(report_id)` / `record_field_override(row_id)` 此前只收主键,RLS 下只凭主键访问无上下文 = 危险。

**决策**:全部改签名带 `tenant_id` + `user_id`(或经 task 先取上下文),游标换 `get_cursor_rls`,**禁裸 get_cursor 兜底、禁 owner 绕过**。调用方(`routes/recon_routes*.py`、对账引擎)一并穿上下文。

**测试**:`tests/unit/test_recon_store_rls_contract.py`(mock 断言每个函数把 tenant+user 注入 `get_cursor_rls`、且不回退裸 `get_cursor`)+ 集成矩阵传递式穿透。

### `vat_report`:只有 tenant_id 没有 user_id

**决策**:给 `vat_report` **补 `user_id` 列**(`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`),用 `tenant_or_user` 模板。

- **为什么补列而非纯 tenant 模板**:纯 tenant policy 下 `tenant_id IS NULL` 的单用户(无 tenant)账号的 `vat_report` 行对所有人隐形 → 单用户账号读不到自己的报告。补 `user_id` 后单用户账号经 user 兜底可见,跟全栈 `tenant_or_user` 一致。
- `vat_report` 在 `create_recon_task` 之前由 `create_vat_report` 建,创建侧上下文里 user_id 可得 → 直接写入,无需回填(新行);存量行回填 `UPDATE vat_report v SET user_id=t.user_id FROM reconciliation_task t WHERE t.vat_report_id=v.id AND v.user_id IS NULL`。

---

## 2. bypass=True 登记册(每处必须有系统级理由)

| 文件 · 函数 | 为什么 bypass | 是否 worker/system |
|---|---|---|
| `recon_jobs/store.py` · `claim_next` | 后台 worker 跨租户认领队列(`FOR UPDATE SKIP LOCKED`),无 HTTP 单租户上下文 | worker |
| `recon_jobs/store.py` · `update_progress`/`finish`/`set_needs_review`/`set_needs_mapping`/`set_failed`/`fail` | worker 认领 job 后按 job_id 写生命周期,跑在 worker 进程无请求上下文 | worker |
| `recon_jobs/store.py` · `reclaim_stale`/`gc_old` | 后台回收过期租约 / 清理老记录,扫全表跨租户 | worker |
| `recon_jobs/store.py` · `ensure_table` | DDL(建表/索引/扩展),owner 连接 | DDL/system |

> 用户触发的 `enqueue` / `get` **不 bypass**,走 `get_cursor_rls(tenant_id,user_id)`。worker 处理的 job 行其 tenant/user 在 enqueue 时已写入行,worker/handler 从行取套账,绝不"看全租户当自己的"。

---

## 3. wave3 老模块迁移计划(分批 · 钱路径单列)

范围(~62 处):clients / exceptions / notification / billing / credits / cost / ocr_history / archive。

| 批次 | 表/模块 | 模板 | 要点 |
|---|---|---|---|
| 3a | `ocr_history` + `clients` | tenant_or_user | 闭合 wave2 的 bank_recon / knowledge_bridge / recon_resolve JOIN 隔离;迁移面最广先做 |
| 3b | `exceptions` / `notification` | tenant_or_user | exceptions 已有应用层 scope;notification 跨租户推送 hook 走 bypass |
| 3c | `archive` | tenant_or_user | 读多写少 |
| 3d ★钱 | `billing`/`charge.py` / `credits` / `cost` | tenant_or_user | **charge.py 钱路径**:扣费/充值必带 tenant+user,**禁 bypass**;credits/cost **超管聚合报表**必 bypass(否则归零),但须证明聚合不串单租户视图(聚合只在超管路由,普通用户路径带上下文) |

每批同 cycle:审计 → 改 get_cursor_rls → `apply_*` + enroll → 本地恢复库 force=True 穿透 → prod 设 env 自动生效 → 冒烟。

## 4. wave4 集成模块(bypass vs RLS 分类)

范围(~30 处):erp / email_ingest / importer。

| 必须 bypass(系统级后台) | 必须 RLS(用户触发/含租户数据) |
|---|---|
| `push_retry` 后台扫描重推队列 | 用户触发的 ERP 推送(`/api/erp/push` 带 tenant+user) |
| `email_ingest` `list_enabled` 后台轮询收件 | 推送状态查询(用户看自己的 erp_push_logs) |
| `agent get_express_endpoint`(本地 agent 拉配置,无用户会话) | endpoint 配置的增删改(用户在设置页操作,带上下文) |

判据:**有 HTTP 用户会话 = 带上下文走 RLS;后台 worker/定时/本地 agent 拉取 = bypass + 登记理由**。

---

## 5. P4 收口

- `tests/e2e/12-rls-isolation.spec.js`:`passed>=2` → `passed===5`(全部 5 个隔离断言必须过)。
- ready 域**裸 get_cursor 清零**后,逐表 `force=True`(当前 force=False 靠 owner 兜底是中间态,非终态)。force=True 前置 = 该域无任何裸 row-op/DDL 依赖 owner 绕过。

---

## 5b. 实施进度(2026-06-25)

| Phase | 范围 | 状态 | commit |
|---|---|---|---|
| 1 | recon_jobs(enroll+worker bypass)+ knowledge_bridge(穿上下文) | ✅ | `9f7765c2` |
| 2 | 两个 hard point:传递式 policy + reconciliation 三表穿上下文 + vat_report 补 user_id | ✅ 真库验证 | `967e9fba` |
| 3a | recon_resolve(ocr_history/clients 读穿上下文) | ✅ | `933e1681` |
| 3b | bank_recon(v1_store/match/scoring/routes 穿 tenant+user) | ✅ | `f1714ca1` |

**验证**:真 postgres 16/16 集成(矩阵 8 + 传递式 5 + 真 recon 表端到端 3)+ 全量单测 4877 passed。
wave2 的 row-operation 裸 get_cursor 已全部迁 `get_cursor_rls`;recon 域残留裸 get_cursor 仅 DDL/ensure(owner)。

**bank_reconcile_\* 表 enroll(明确的小 follow-on)**:这三张表是 **user 维度(无 tenant_id)**,本轮已把
所有 row-op 穿 user 上下文(应用层 `user_id` WHERE 仍是当前隔离 · 无跨用户泄漏)。要给它们 DB 级
policy,需:① `core/rls.py` 加 user-only 模板 `apply_user_rls`(`user_id = current_user`);② 在
`ensure_bank_recon_client_id_column`(已 startup 跑)enroll `bank_reconcile_sessions`/`transactions`;
③ `bank_reconcile_candidates`(经 tx_id→transactions)用 user-via-parent。穿线groundwork已就位,
enroll 仅是补 apply_* 调用 + 真库穿透。**ocr_history JOIN 隔离随 wave3 ocr_history enroll 自动闭合**。

## 6. 不开 RLS(设计已裁决 · 本轮明确不碰)

| 表/域 | 为什么不开 |
|---|---|
| `line_voice_quota` | LINE 身份全局,非租户资源 |
| 订阅 / 付款 / 改密日志 | 根级审计,超管视角 |
| `users` / `tenants` 根表 | RLS 的"身份来源",自己不能再被自己过滤 |
| `rd_cache` | 政府登记缓存,全局共享非租户 |
| `rd_daily_usage` | 按 user 的计数器,非租户隔离对象 |
| `billing_balance_log` | Google 余额全局账本,无租户列 |
