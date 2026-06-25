# B8 多租户 RLS · P3 逐域启用就绪审计 + Rollout Runbook(2026-06-25)

> 上游:P0 设计 `b8-rls-production-design.md` · P1 基建 `core/rls.py`+`core/db.py:get_cursor_rls` · P2 矩阵 `tests/integration/test_rls_isolation_matrix.py`。
> 本文 = P3 前置审计(486 处 get_cursor 分域)+ 一处对设计心智模型的纠正 + prod 启用 runbook。回滚脚本 `scripts/rls_rollback.sql`。

---

## 0. 一句话结论

**✅ ready 域已于 2026-06-25 在 prod 真启用并验收**(`RLS_ROLE=pearnly_app` 已写入 `/opt/mrpilot/.env`)。POS/库存/产品/采购/销售/会计/税/导出/LINE-brain/expense/modules 这些域的查询现在经数据库 policy 强制只能看到本租户数据;裸 `get_cursor`(owner 连接)在 force=False 下仍绕过 → 老路径不破。recon / 老模块尚未 enrolled,要先把 ~110 处裸 `get_cursor` 迁到 `get_cursor_rls` 才能开 —— 后续 wave。

启用证据(prod 真数据):金丝雀 journal_vouchers 自己 19 行 / 假租户 0;8 域多表冒烟全 PASS;重启零 error;真登录 `/api/me/modules` 正确返回 tenant_modules。

---

## 1. 前置审计:486 处 `get_cursor(` / 137 文件 分域(四路并行审计实测)

| 域 | enrolled? | get_cursor_rls 就绪 | 需改裸 get_cursor | 结论 |
|---|---|---|---|---|
| ① POS/库存/产品 | ✅(apply_tenant_rls) | ✅ 路由全带上下文 | 0(service 层全是 DDL) | **ready** |
| ② 采购/销售/会计/税/导出 | ✅ | ✅ 路由全带上下文 | 1(会计 posting_failures 后台 worker·见 §4) | **ready**(1 处加固) |
| ③ 对账(recon)/recon_jobs | ❌ 未 enrolled | ❌ 0 处用 rls 游标 | ~48 + ~9 worker bypass | wave 2 |
| ③ 知识(rd/knowledge_bridge) | ❌ | 部分 | rd_cache/rd_daily_usage 是全局/计数器**不开 RLS**;knowledge_bridge 4 处需改 | wave 2 |
| ④ 老模块 clients/exceptions/notification/billing/credits/cost/ocr_history/archive | ❌ 未 enrolled | ❌ 0 处 | ~62(billing charge.py 钱路径最危险;credits/cost 超管聚合需 bypass) | wave 3 |
| ⑤ auth/tenant/membership/team/authz/users | — | — | 0(根表/超管/DDL/迁移·**不开租户 RLS**) | n/a |
| ⑤ LINE-brain(line_message_refs/chat_history/action_nonces) | ✅ | ✅ 全用 rls 游标 | 0 | **ready** |
| ⑤ line_bindings / line_voice_quota | — | — | 0(LINE 身份全局·设计裁决**不开 RLS**) | n/a |
| ⑤ erp/email_ingest/importer | ❌ 未 enrolled | ❌(应用层 WHERE 隔离) | ~30(未来 wave·非当前风险) | wave 4 |

> 裁决项(P0 §6 已定·无需 Owner 输入):`line_voice_quota`/订阅·付款·改密日志/`users`·`tenants` 根表 → 不开租户 RLS;`rd_cache`(政府登记缓存)/`rd_daily_usage`(按 user 计数器)→ 非租户表不开;`billing_balance_log`(Google 余额全局账本)→ 无租户列不开。

---

## 2. ★ 对设计心智模型的一处纠正(影响 rollout 风险评估)

P0 设计与交接写「457 处裸 `get_cursor` 碰到 enrolled 表会**查空 / 写入被拒** → 必须先全迁完才能开」。**这对裸 `get_cursor` 路径不成立**,关键在 Postgres RLS 与角色的交互:

- `ENABLE ROW LEVEL SECURITY` 后,policy 对**除表 owner 外**的所有角色生效;`FORCE` 才把 owner 也纳入;带 `BYPASSRLS` 属性的角色**永远绕过**。
- `get_cursor_rls` 在事务里 `SET LOCAL ROLE pearnly_app`(NOBYPASSRLS·非表 owner)→ 对 enrolled 表 **policy 强制生效**(`FORCE` 与否都一样,因为 pearnly_app 本就不是 owner)。
- 裸 `get_cursor` **不切角色** → 留在 owner 连接 → **绕过 policy** → 老代码继续工作,只是没隔离。
  - ★ **prod 实测纠正**:Supabase 的连接角色是 `postgres`,但**它不是 BYPASSRLS**(`rolbypassrls=False`),它绕过是靠**表 owner 身份**(force=False 时 owner 豁免)。**推论:对 enrolled 表跑 `force=True` 会让裸 `get_cursor` 也被 policy 拦 → 在那些表上未迁完的裸 row-op 会查空。所以 ready 域当前保持 force=False**(owner 绕过兜底),force=True 留到该域裸 get_cursor 清零后再上。

**推论(修正 rollout 风险面)**:
1. 设 `RLS_ROLE` 是**全局**的:一旦设上,**所有** enrolled 表的 **所有 `get_cursor_rls` 路径**立即被强制隔离(不是按 `force=True` 逐表 gate)。
2. 真正的启用 gate = 「所有 enrolled 表的每个 `get_cursor_rls` 调用都带正确上下文」。**已实测 GREEN**:227 处 `get_cursor_rls` 无一缺上下文(空括号 0 处、`get_cursor_rls(commit=...)` 无 tenant 的 0 处·3 处疑似命中是 docstring),4 处 `bypass=True` 是合法超管/worker 通道。
3. 裸 `get_cursor` 的迁移(457 处)是为**给那些域也拿到隔离**,不是「防止设 env 时崩站」。所以可以**先给 ready 域开 env、其余域慢慢迁**,中间态安全。
4. **prod 隔离全靠 `RLS_ROLE` 切到 pearnly_app**(非 owner → ENABLE 即被 policy 拦)。**ready 域不能上 `force=True`**:owner(postgres·非 BYPASSRLS)一旦被 FORCE 纳入,裸 get_cursor 的 DDL/未迁 row-op 会被拦 → 风险倒挂。force=True 是「该域裸 get_cursor 清零」后的收尾动作,不是启用前置。

### ★ Supabase 专属前置:必须授角色成员资格(否则 SET ROLE 失败)
`SET LOCAL ROLE pearnly_app` 要求**连接角色是 pearnly_app 的成员**。Supabase 的 `postgres` 默认不是、且**不能经 pooler(6543/5432)授权**(`GRANT pearnly_app TO postgres` 经 pooler 会被掐断 SSL;直连 db 主机是 IPv6-only 从 prod 服务器够不到)。**唯一可行 = Supabase 后台 SQL Editor 跑一次** `GRANT pearnly_app TO postgres;`(后台连接权限够)。一次性·成员资格存 `pg_auth_members` 全局生效。**这步没做的话设 RLS_ROLE 会让每条 RLS 路径 500。** ⚠️ 别把这条加进 `ensure_rls_app_role`(startup 经 pooler 跑会崩)。

---

## 3. Prod 启用 Runbook(ready 域:POS/库存/产品/采购/销售/会计/税/导出/LINE-brain/expense/modules)

> Owner「没有真实用户」→ 影响面极小·出问题秒回滚。不必等低峰窗口。

**步骤(2026-06-25 已全部执行 ✅)**:
1. ✅ **建角色**(一次性):prod 跑 `ensure_rls_app_role(cur)` → `pearnly_app`(NOSUPERUSER NOBYPASSRLS NOLOGIN)+ 授 public schema DML/SEQUENCE。幂等。
2. ✅ **授成员资格**(Supabase 后台 SQL Editor·见 §2 末):`GRANT pearnly_app TO postgres;`。**没这步 SET ROLE 会失败、设 env 必崩。**
3. ✅ **金丝雀**(开 env 前·只读+rollback):脚本验证 pooler 上 `SET LOCAL ROLE` + 真数据隔离(自己看全/假租户 0/无上下文 0)。这步证不过别开 env。
4. ✅ **设 env + 重启**(碰红线 #16):`/opt/mrpilot/.env` 加 `RLS_ROLE=pearnly_app`(先 `cp .env .env.bak_rls_*`)→ `systemctl restart mrpilot`。
5. ✅ **冒烟**:`/api/ready` 200·8 域多表隔离全 PASS·真登录 `/api/me/modules` 正确返回 enrolled 表数据。
6. **(收尾·暂不做)** ready 域裸 get_cursor 清零后再 `force=True`(见 §2.4·当前保持 force=False)。
5. **出事回滚**:① 删 `RLS_ROLE` env + 重启(秒级·全站恢复)② 必要时 `psql -f scripts/rls_rollback.sql`(NO FORCE + DISABLE)。

**会计域先决条件**:启用前先合 §4 的 posting_failures worker 加固(否则该表在 `force=True` + 非 BYPASSRLS owner 场景下 worker 认领会被过滤;prod BYPASSRLS owner 下虽不立即坏,但属正确性债,先清)。

---

## 4. ready 域唯一代码缺口:会计 posting_failures 后台 worker

`services/accounting/posting_failures.py` 的 `claim_due`(L118)/`retry_one`(L190)用裸 `get_cursor()` 读写 enrolled 表 `accounting_posting_failures`,是**跨租户重试队列**(`FOR UPDATE SKIP LOCKED`·无 HTTP 上下文)。

- prod(owner BYPASSRLS):裸 get_cursor 绕过 → 现状能跑,**不阻塞设 env**。
- 但若该表 `force=True` 且换到非 BYPASSRLS owner / 或将来收紧 owner → `claim_due` 被 policy 过滤成空 → 队列瘫痪。

**加固**:worker 跨租户认领改 `get_cursor_rls(bypass=True)`(显式声明跨租户),`retry_one` 真过账时按行 tenant 重建上下文。属正确性债·与 recon_jobs / notification 跨租户 hook 同类(那些在 wave 2/3 一并处理)。

---

## 5. 后续 wave(未 enrolled·需先迁裸 get_cursor 才能开)

### wave 2 进度(对账·进行中)
**✅ 已上线**(2026-06-25·3 个自包含 `tenant_or_user` task 表·迁 get_cursor_rls + enroll + 本地真隔离 + prod 验证):`vat_recon_tasks`(`cd6a3d7e`)、`gl_vat_task`(`8722b8b5`)、`bank_recon_v2_task`(`a1e68aae`)。
- 套路:store 签名本有 tenant/user → 换游标即可;按 user_id 删的函数补 `tenant_id` 参数(否则 RLS 下 tenant 任务删 0 行·money 陷阱);受影响 mock-cursor 测试辅助改为同 patch `get_cursor`+`get_cursor_rls`。

**⏳ 剩余 = 两类更难的活(非机械迁移·需设计)**:
1. **`vat_recon_store`(vat_report+reconciliation_task/row)+ `bank_recon_v1`/`bank_recon_match`** — 三个结构性障碍:
   - `reconciliation_row` **无 tenant_id 列**(仅 task_id)→ 现有 3 模板套不上,需给 `core/rls.py` 加「经 task_id 子查询取租户」的**传递式 policy 模板**,或有意识地让它保持裸 get_cursor(owner 绕过·靠路由 authz + 父 task 已 enroll 间接保护)。
   - `vat_report` **只有 tenant_id 没 user_id** → 只能纯 tenant 模板·孤立用户行(tenant 空)全员不可见(先确认 prod 无孤立 vat_report)。
   - **~10 个函数只收 id 不收租户上下文**(`get_recon_row(row_id)`/`update_recon_row_action`/`get_recon_task(task_id)`/`update_recon_task_status`…)→ 要给一长串签名 + 路由/对账引擎调用方穿上下文。
2. **`recon_jobs` worker**(claim/finish/fail/reclaim/gc 跨租户队列→`bypass=True`)+ **`knowledge_bridge`**(读 ocr_history/client_rules=wave3 表·纯游标迁移·隔离落 wave3)。
| wave | 域 | 工作量 | 要点 |
|---|---|---|---|
| 2 剩 | recon 跨表 + recon_jobs + knowledge_bridge | ~40 改 + 设计 | 见上·需传递式 policy + 上下文穿线 |
| 3 | 老模块 clients/exceptions/notification/billing/credits/cost/ocr_history/archive | ~62 | billing `charge.py` 钱路径最危险;credits/cost 超管聚合必须 `bypass=True`(否则报表归零);统一用 `tenant_or_user` 模板(遗留 NULL-tenant 行靠 user_id 兜底) |
| 4 | erp/email_ingest/importer | ~30 | 后台扫描(push_retry/email list_enabled/agent get_express_endpoint)走 bypass |

每 wave 同 cycle:审计 → 改 get_cursor_rls → 该域表 `apply_*` + enroll → 本地恢复库 force=True 跑穿透 → prod 设/已设 env 下该域自动生效 → 冒烟。

---

## 6. P4 收尾(prod 真启用后)
- `tests/e2e/12-rls-isolation.spec.js` 断言 `passed>=2` → `passed===5`(spec 顶部 E 段 TODO)。
- 设计文档 §7 rollout 状态更新到「ready 域已 prod 启用」。
- 回滚脚本已建(`scripts/rls_rollback.sql`)。
