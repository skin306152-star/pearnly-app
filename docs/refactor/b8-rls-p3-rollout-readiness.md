# B8 多租户 RLS · P3 逐域启用就绪审计 + Rollout Runbook(2026-06-25)

> 上游:P0 设计 `b8-rls-production-design.md` · P1 基建 `core/rls.py`+`core/db.py:get_cursor_rls` · P2 矩阵 `tests/integration/test_rls_isolation_matrix.py`。
> 本文 = P3 前置审计(486 处 get_cursor 分域)+ 一处对设计心智模型的纠正 + prod 启用 runbook。回滚脚本 `scripts/rls_rollback.sql`。

---

## 0. 一句话结论

**已 enrolled 的「新模块」域(POS/库存/产品/采购/会计/税/导出/LINE-brain/expense/modules)现在就 RLS-ready**:这些表的 `ensure_*` 已调 `apply_tenant_rls`,且其所有 `get_cursor_rls` 调用(227 处 / 51 文件)**无一处缺租户上下文**。Owner 设 `RLS_ROLE=pearnly_app` + 建角色即可真启用隔离,**裸 `get_cursor` 路径不会被打断**(见 §2 语义)。recon / 老模块(clients/exceptions/notification/billing 等)**尚未 enrolled**,要先把 ~110 处裸 `get_cursor` 迁到 `get_cursor_rls` 才能开 —— 那是后续 wave。

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

- `ENABLE ROW LEVEL SECURITY` 后,policy 对**除表 owner 外**的所有角色生效;`FORCE` 才把 owner 也纳入;带 `BYPASSRLS` 属性的角色**永远绕过**(prod owner 即此,根因 #19)。
- `get_cursor_rls` 在事务里 `SET LOCAL ROLE pearnly_app`(NOBYPASSRLS·非表 owner)→ 对 enrolled 表 **policy 强制生效**(`FORCE` 与否都一样,因为 pearnly_app 本就不是 owner)。
- 裸 `get_cursor` **不切角色** → 留在 owner 连接(prod owner 带 BYPASSRLS)→ **始终绕过 policy** → 老代码继续工作,只是没隔离。

**推论(修正 rollout 风险面)**:
1. 设 `RLS_ROLE` 是**全局**的:一旦设上,**所有** enrolled 表的 **所有 `get_cursor_rls` 路径**立即被强制隔离(不是按 `force=True` 逐表 gate)。
2. 真正的启用 gate = 「所有 enrolled 表的每个 `get_cursor_rls` 调用都带正确上下文」。**已实测 GREEN**:227 处 `get_cursor_rls` 无一缺上下文(空括号 0 处、`get_cursor_rls(commit=...)` 无 tenant 的 0 处·3 处疑似命中是 docstring),4 处 `bypass=True` 是合法超管/worker 通道。
3. 裸 `get_cursor` 的迁移(457 处)是为**给那些域也拿到隔离**,不是「防止设 env 时崩站」。所以可以**先给 ready 域开 env、其余域慢慢迁**,中间态安全。
4. `force=True` 在 prod(owner 带 BYPASSRLS)对 owner 路径其实是 cosmetic(BYPASSRLS 压过 FORCE);它在「owner 不带 BYPASSRLS」的环境(如本地集成矩阵以 owner 角色直连)才有意义。**prod 的隔离全靠 `RLS_ROLE` 切角色,不靠 force。** 仍建议对 ready 域表跑一遍 `force=True`(幂等·防未来 owner 去掉 BYPASSRLS 时退化·零代价)。

---

## 3. Prod 启用 Runbook(ready 域:POS/库存/产品/采购/销售/会计/税/导出/LINE-brain/expense/modules)

> Owner「没有真实用户」→ 影响面极小·出问题秒回滚。不必等低峰窗口。

**步骤(碰红线 #16 systemd env·需 Owner 点)**:
1. **建角色**(一次性·owner 连接):prod 跑 `ensure_rls_app_role(cur)`(`core/rls.py`)或等效 SQL —— 建 `pearnly_app`(NOSUPERUSER NOBYPASSRLS NOLOGIN)+ 授 public schema DML/SEQUENCE。幂等。
2. **设 env + 重启**:systemd `RLS_ROLE=pearnly_app` → `systemctl restart mrpilot`。此刻 ready 域的 `get_cursor_rls` 路径开始真隔离。
3. **冒烟**(立即):
   - `/api/ready` db ok;
   - 登录测试号 → POS 收银开单 / 采购票列表 / 会计凭证列表 各拉一次(确认看得到自己租户数据·非空);
   - `tests/e2e/12-rls-isolation.spec.js`(prod 跑·此时应从 `passed>=2` 升到 `passed===5`)。
4. **(可选·防退化)** 对 ready 域表跑 `apply_*(force=True)`(或直接 SQL `ALTER TABLE <t> FORCE ROW LEVEL SECURITY`)。幂等·prod 行为不变。
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

| wave | 域 | 工作量 | 要点 |
|---|---|---|---|
| 2 | recon + recon_jobs + knowledge_bridge | ~48 改 + ~9 worker bypass + 4 | 大量 store 函数仅按主键 id 查、无应用层租户 WHERE → 最依赖上下文,优先 |
| 3 | 老模块 clients/exceptions/notification/billing/credits/cost/ocr_history/archive | ~62 | billing `charge.py` 钱路径最危险;credits/cost 超管聚合必须 `bypass=True`(否则报表归零);统一用 `tenant_or_user` 模板(遗留 NULL-tenant 行靠 user_id 兜底) |
| 4 | erp/email_ingest/importer | ~30 | 后台扫描(push_retry/email list_enabled/agent get_express_endpoint)走 bypass |

每 wave 同 cycle:审计 → 改 get_cursor_rls → 该域表 `apply_*` + enroll → 本地恢复库 force=True 跑穿透 → prod 设/已设 env 下该域自动生效 → 冒烟。

---

## 6. P4 收尾(prod 真启用后)
- `tests/e2e/12-rls-isolation.spec.js` 断言 `passed>=2` → `passed===5`(spec 顶部 E 段 TODO)。
- 设计文档 §7 rollout 状态更新到「ready 域已 prod 启用」。
- 回滚脚本已建(`scripts/rls_rollback.sql`)。
