# B8 · 多租户 RLS 生产级加固 · 设计文档(REFACTOR-B8)

> 状态:设计阶段(2026-06-24)· 不碰生产 · 实现按本文档分阶段推进
> 关联:铁律 #26 硬线 #1(RLS 基础设施)· 工程标准「多租户必隔离+RLS」· `core/rls.py` / `core/db.py` 现有基建
> 目标 spec:`tests/e2e/12-rls-isolation.spec.js`(收尾收紧到 `passed===5`)

## 0. 一句话目标

把"租户/账套数据隔离"从**只有应用层 WHERE**(一道防线)升级为**应用层 WHERE + 数据库 RLS 强制**(双防线):就算某条代码路径漏写了 `WHERE tenant_id`,数据库层也绝不跨租户/跨账套泄漏。RLS 是**第二道防线,不替代应用层 WHERE**。

## 1. 现状审计(2026-06-24 实测)

### 1.1 已有基建
- `core/rls.py` · `apply_tenant_rls(cur, *tables)`:单一来源 policy `tenant_isolation`,USING + WITH CHECK,谓词 `tenant_id::text = current_setting('app.current_tenant_id', true) OR current_setting('app.bypass_rls', true)='on'`。已被 POS/库存表的 `ensure_*` 调用。
- `core/db.py` · `get_cursor_rls(tenant_id, bypass)`:`SET LOCAL app.current_tenant_id` / `app.bypass_rls`;`run_rls_isolation_tests`:临时对 `clients` 表跑 5 条穿透测试。`ENABLE_RLS` 默认 `0`。
- `core/workspace_context.py` · `scope_from_request` / `assert_workspace_in_tenant` / `resolve_active_workspace_id`:请求级 tenant + workspace + user 上下文,可复用做 RLS context 注入。

### 1.2 真实缺陷(spec 顶部 + core/rls.py 注释已记录)
**生产 DB 连接角色带 `BYPASSRLS`(SUPERUSER / cloud owner 默认)→ 所有 policy 被跳过**。这是 `12-rls-isolation.spec.js` 里 T1/T3/T5 失败的根因(全表返,看似隔离失效)。**不修 role,开多少 policy 都是摆设。**

### 1.3 最大生产风险(本次实测发现)
- `get_cursor()`(无上下文普通游标):**457 处 / 113 文件**(老模块为主)。
- `get_cursor_rls()`(带上下文):220 处 / 51 文件(POS/会计/销售/采购/库存/知识/LINE 新模块)。
- **风险**:对一张表 `ENABLE + FORCE RLS` 且业务角色 `NOBYPASSRLS` 后,任何**没先 SET 上下文**的查询(那 457 处里碰到该表的)`USING` 谓词为假 → **返空 / 写入被拒**。
- **推论**:RLS 必须**按域分批开**,每批开 RLS 前先确保该域所有读写都走带上下文的游标。一次性全开 = 整站数据消失。

## 2. 全表隔离矩阵(99 张存活表)

完整逐表矩阵见 [附录 A](#附录-a全表隔离矩阵)。分类汇总:

| 分类 | 张数 | 隔离手段 |
|---|---|---|
| **tenant**(含 `tenant_id`) | 84 | RLS policy 判 `tenant_id` |
| **workspace**(`workspace_clients` 根表) | 1 | RLS policy 判 `id = workspace_client_id` |
| **parent-derived**(无租户列·靠父表) | 8 | RLS policy 用子查询 JOIN 父表,或不开 RLS 靠父表网关 |
| **admin-only**(平台级·无租户) | 3 | 不开租户 RLS·靠垂直权限(超管 403 闸) |
| **global**(查找/配置) | 2 | 不开 RLS |
| **可疑·需裁决** | 1 | `line_voice_quota`(见 §6) |

> 另:`users` / `tenants` / `ocr_history` 三张根表是 Supabase 托管、本仓库无 `CREATE TABLE`,RLS 要覆盖须走 Supabase 侧 migration,单列处理(见 §6 裁决项)。

## 3. 设计

### 3.1 DB role 分离(你的第 3 点)
建三类角色,**业务连接必须 NOBYPASSRLS**:

```sql
-- 业务角色:最小权限·受 RLS 约束·只 DML
CREATE ROLE pearnly_app NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOINHERIT LOGIN;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pearnly_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT,INSERT,UPDATE,DELETE ON TABLES TO pearnly_app;

-- migration/admin 角色:可 DDL·可 bypass(跑 ensure_*/alembic/超管维护)
-- 复用现有 owner 连接即可,不新建 LOGIN 角色(减少凭据面)。
```

**关键:`ALTER TABLE <t> FORCE ROW LEVEL SECURITY`** —— 否则 table owner 连接仍绕过 RLS。

**连接落地(Supabase pooler 约束)**:不改连接串的 role(pooler 连接共享),而是在 `get_cursor_rls` 进入事务时 `SET LOCAL ROLE pearnly_app`(事务级·`putconn` 随事务结束自动恢复·不泄漏给下个借用者)。migration / 超管路径走 `bypass=True` 不切 role 或切回 owner。

### 3.2 RLS context 三维(你的第 4 点)
现有 `get_cursor_rls` 只设 `app.current_tenant_id`。扩展为三维:

```
SET LOCAL app.current_tenant_id      = <tenant_id>
SET LOCAL app.current_workspace_id   = <workspace_client_id>   -- 账套级·可空
SET LOCAL app.current_user_id        = <user_id>               -- 孤立用户兜底(tenant_id 可空的存量行)
SET LOCAL app.bypass_rls             = 'on'                      -- 仅 migration/超管
```

**注入策略(降低 457 处改造成本)**:引入请求级 `ContextVar`(中间件从 `scope_from_request` 填),`get_cursor_rls()` 默认从 ContextVar 读三维,不必每个调用点手传。老 `get_cursor()` 在目标域改造时替换为 `get_cursor_rls()`(或让 `get_cursor` 也注入只读上下文)。

### 3.3 policy 模板(按分类)
`core/rls.py` 从单 policy 扩成几种模板(仍单一来源):

- **tenant 表**:`tenant_id::text = current_setting('app.current_tenant_id', true)` `OR bypass`
- **tenant+workspace 表**(账套强隔离·如 POS 明细):额外 `AND (current_setting('app.current_workspace_id', true) IS NULL OR workspace_client_id::text = current_setting(...))`
- **tenant 可空 + user 兜底表**:`(tenant_id IS NULL AND user_id::text = current_setting('app.current_user_id', true)) OR tenant_id::text = current_setting('app.current_tenant_id', true)` `OR bypass` —— **解决 §1.3 NULL tenant_id 存量行**
- **parent-derived 表**:policy 用 `EXISTS (SELECT 1 FROM 父表 p WHERE p.id = 本表.父键 AND p.tenant_id::text = current_setting(...))`,或不开 RLS、靠父表网关 + 应用层
- **admin-only / global**:不开租户 RLS

### 3.4 应用层 WHERE 保留(你的第 2 点)
**不删任何现有 `WHERE tenant_id` / `WHERE workspace_client_id`**。RLS 是兜底,应用层仍是主隔离 + 性能(走索引)。审计中若发现某查询**没有**应用层过滤,先补应用层,再靠 RLS 兜底。

## 4. 测试矩阵(你的第 5 点)

每张开 RLS 的表,对 `SELECT / INSERT / UPDATE / DELETE` 各跑 5 场景:

| 场景 | 期望 |
|---|---|
| 跨租户(A 上下文读 B 数据) | 空 / 拒 |
| 跨账套(同租户·账套 A 读账套 B) | 空 / 拒(workspace 强隔离表) |
| 无上下文(没 SET) | 空 / 拒 |
| fake tenant(伪造 UUID) | 空 / 拒 |
| admin bypass | 全见(超管/migration 通道) |

落地:扩 `run_rls_isolation_tests` 从「clients 单表 5 条」→「每域代表表 × 4 CRUD × 5 场景」,本地 Docker / 恢复库上对**全部** 84+ tenant 表跑;`12-rls-isolation.spec.js` 是生产冒烟(收尾 `passed===5`)。

## 5. 部署阶梯 + 回滚(你的第 6 点)

```
本地 Docker(空库/恢复库)  →  staging(IdeaPad 或本地)  →  prod
        ↑ 全表 CRUD×5 测试绿        ↑ 真数据快照验证          ↑ 分批·每批冒烟·盯 CI
```

**一键回滚脚本** `scripts/rls_rollback.sql`(prod 必备):
```sql
-- 对所有已开 RLS 的表:关 FORCE + 关 RLS(policy 留着不碍事·BYPASS 角色立即恢复旧行为)
ALTER TABLE <t> NO FORCE ROW LEVEL SECURITY;
ALTER TABLE <t> DISABLE ROW LEVEL SECURITY;
-- + 业务连接切回 owner 角色(改 env / 重启)
```
回滚是**幂等、零数据风险**(只关开关,不动数据);任何一批上 prod 后冒烟异常 → 立即跑回滚 + 排查。

## 6. 裁决项(需先定·我给推荐)

| # | 表/问题 | 推荐 | 需你/产品确认 |
|---|---|---|---|
| 1 | `line_voice_quota` 无任何租户列 | 补 `tenant_id`;或确认 `line_user_id` 全局唯一、配额全局可接受 | 是 |
| 2 | `products` 只有 tenant_id 无 workspace_client_id(下游全带) | 确认「商品主数据 tenant 级共享」是有意设计 | 是 |
| 3 | `pos_sale_lines/pos_payments/pos_session_lines/reconciliation_row` 无 workspace·靠父表 JOIN | parent-derived policy(EXISTS 父表)或父表网关 | 我定 |
| 4 | 一批表 `tenant_id` 可空(孤立用户存量行) | §3.3「tenant 可空 + user 兜底」policy 模板 | 我定 |
| 5 | `subscription_log/payment_pending/password_reset_log` 只有 user_id | 归 admin/计费域·绑 user·不开租户 RLS | 是(产品) |
| 6 | `users/tenants/ocr_history` Supabase 托管根表 | 单列 Supabase 侧 migration·本批不动 | 是 |

## 7. 分阶段 rollout(实现顺序)

- **P0 设计**(本文档)✅
- **P1 role + context 基建**:建 `pearnly_app` 角色、`get_cursor_rls` 接 ContextVar 三维、中间件注入、policy 模板扩展 —— **本地 Docker 验证**,不碰 prod。
- **P2 测试矩阵**:扩 `run_rls_isolation_tests` 全 CRUD×5 + 本地/恢复库对全表跑绿。
- **P3 按域分批开 RLS**(先确保该域查询走上下文游标):① POS/库存(已大量用 rls 游标·风险低)→ ② 采购/销售/会计 → ③ 对账/知识 → ④ 老模块(clients/exceptions/notification/billing·457 处重灾)。每批:本地绿 → staging → prod 冒烟 → 盯 CI。
- **P4 收尾**:prod 全绿后 `12-rls-isolation.spec.js` 收紧 `passed===5`;回滚脚本归档;文档更新。

---

## 附录 A·全表隔离矩阵

(99 张存活表逐表 tenant_id/workspace_client_id/user_id/父键/分类/定义位置 —— 见本仓库 git 历史 commit 附带的扫描结果;裁决项见 §6。下批实现时把完整表格补全到此处。)
