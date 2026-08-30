# F1-B3B2b-2 · Owner Express endpoint lifecycle CAS discovery

> 状态：`IMPLEMENTING` / `DISCOVERY_COMPLETE_FLAG_OFF`
>
> 本页是 B3B2b-2 的派单合同。它只冻结设计、边界、验证矩阵和落地文件，不表示代码已实现、
> 不表示生产可用，也不解锁 B3B3、B3C、B4、B5 或任何真机验收。

## 1. Discovery：场景、价值与成熟范式

### JTBD

个体老板已经在网页把 Express 小助手绑定到一个账套。换账套、临时停用、恢复使用或永久
撤销时，老板需要在网页完成一次可追踪的连接生命周期操作；员工只负责录单，不能改变连接
归属或凭据。Cowork 和 `/erp` 共享同一个组织连接，但每次请求仍必须落在当前 tenant、
当前 workspace 和当前 owner 身份上。

### RICE / Kano

这是 F1 的必需后端前置，不是额外的设置花活：

- Reach：每个使用共享 Express 的组织至少需要启用、停用和换账套能力。
- Impact：连接错绑会造成跨账套推送、重复入账或无法恢复，影响高。
- Confidence：现有 managed endpoint、workspace 指针、generation、审计和 RLS 底座已经存在，
  本批只补生命周期写入。
- Effort：中等；需要四路由、CAS、并发锁序、撤销墓碑和真 PostgreSQL 矩阵。
- Kano：启用/停用是 Must-have，rebind/revoke 是安全与运维必需；UI、Companion、推送和
  heartbeat 明确不属于本批。

### 组织资源范式与便利性

采用 Square/Loyverse 的组织资源模式：操作者用个人账号，ERP 连接属于 tenant/workspace，
危险动作单独授权并二次确认；采用成熟本地同步代理的“状态可见、离线不假成功”原则。
四个动作都要求客户端带 operation id 和 generation，服务端返回 `changed`，避免老板重复
点击造成第二次状态变化。revoke 是不可逆危险动作，必须带 `confirm=true`。本批无页面改动，
所以没有浏览器或真机门；后续 B4 才把这些错误和确认接到网页。

## 2. 冻结范围与非目标

本批只做 **owner 管理现有 Express managed endpoint 的生命周期 CAS**：

1. `POST /api/erp/endpoints/{endpoint_id}/shared/rebind`
2. `POST /api/erp/endpoints/{endpoint_id}/shared/enable`
3. `POST /api/erp/endpoints/{endpoint_id}/shared/disable`
4. `POST /api/erp/endpoints/{endpoint_id}/shared/revoke`

所有 tenant 的 `erp_shared_express_endpoint` 继续 OFF；flag-off 在业务身份解析前返回稳定
`404`。B3B3（live heartbeat/profile mismatch/旧 writer 隔离）、B3C（reservation/finalize、
drain、managed push log、Agent lease/ack、steward bridge）、B4 UI、B5 放量/真机、Companion、
LINE、MR.ERP、auto push、普通 push 和任何外部 ERP 网络调用均 locked。`erp_push_logs` 仍是
唯一推送状态源，本批不得新建生命周期之外的推送状态表。

旧实现为 `N/A`：现有 gen0 CRUD 和 `workspace_clients.erp_endpoint_id` 绑定逻辑不替代本批
managed lifecycle；旧 CRUD、旧 Companion token/reporting writer 继续按 `binding_generation=0`
隔离，不能写入或复活 managed endpoint。

## 3. 统一请求、身份与安全响应合同

### 请求头和 body

每个请求都必须有 `X-Workspace-Client-Id`。它就是 expected source workspace，不能从 endpoint
当前值、用户默认值或请求 body 猜测。body 必须包含：

```json
{
  "operation_id": "<UUID>",
  "expected_generation": 3,
  "reason": "optional short reason"
}
```

`expected_generation` 必须为整数且 `>=1`；`operation_id` 必须是规范 UUID。rebind 另外必须
包含 `target_workspace_client_id` 和同值显式确认字段
`confirm_target_workspace_client_id`，二者必须完全相等。revoke 另外必须包含 `confirm: true`。
reason 只用于审计，长度和控制字符按现有请求 schema 的安全限制拒绝。

身份准入顺序固定：先认证并执行 `require_erp_portal`，确认入口属于 `main`、`cowork` 或
`erp`（失败沿用 `authz.entrance_scope`）；再检查当前 tenant 的 feature flag；之后才允许解析
任何 endpoint/workspace 对象。flag-off 沿用现有合同返回 `404 erp.shared_endpoint_unavailable`，
不能在未认证请求阶段先查 flag。对已认证请求，再校验当前 tenant 的 active owner
membership/role、`erp.endpoint.manage`，以及 source workspace 与 header 精确一致。
super-admin、普通 admin、员工、跨 tenant owner、非 active membership、非 owner 或缺少权限
沿用 `authz.forbidden`。跨 tenant 或当前 actor 不可见的 endpoint/workspace 统一返回对象隐藏的
`404 erp.endpoint_not_found` 或 `404 workspace.not_found`，不返回 403。

安全成功响应只返回 endpoint_id、workspace_client_id、generation、enabled、shared_scope、
revoked/lifecycle、`changed`、operation_id；不返回 tenant、adapter、config、token、token
hash/tail/created_at、Profile 原文或内部 SQL/存在性细节。错误继续沿用 FastAPI 的 `detail` 字段
承载既有 error code，不新造错误 envelope：字段类型/必填错误由 Pydantic 返回 422；semantic
confirm 错误返回 400；stale、busy 或业务冲突返回 409；事务或审计失败返回 500 并回滚，不能
返回 `changed=true`。

## 4. 四个动作的状态与 CAS 规则

### Rebind

- source 必须是 header 的 workspace；source workspace 与 endpoint 当前 workspace 指针必须精确
  对齐，且 endpoint 为 Express、managed、未撤销、当前 tenant active。
- target 必须是同 tenant、active workspace；target 必须没有别的 managed Express endpoint，
  或已经指向同一个 endpoint。空 target 才允许写入；任何另一个 endpoint 都返回
  `erp.workspace_endpoint_conflict`。
- endpoint 必须 disabled 且 busy-free；不得在 enabled、pending、retrying、next_retry、任意
  lease（含过期 lease）或旧 writer 活跃时迁移。
- 保留 tenant、creator/user、config、token 和 Profile 字段；只把 endpoint workspace 从 source
  改到 target、把 source/target workspace 指针做精确 CAS、保持 `enabled=false`，并令
  `binding_generation = expected_generation + 1`。不搬历史、不复制或删除 `erp_push_logs`。
- source 与 target 相同且 endpoint 已满足同一状态时，按幂等规则返回 `changed=false`；不允许
  借 rebind 隐式 enable。

### Enable

- 仅允许 managed Express、当前 tenant active、未撤销、workspace active 且 endpoint 仍精确
  绑定该 workspace。
- 只接受 disabled → enabled；必须 busy-free，并在同一事务内 CAS generation。
- generation 相同且已经 enabled 时安全重放 `changed=false`、不新增 audit；请求 generation
  过旧或未来均 `409 erp.endpoint_stale_generation`。

### Disable

- 仅接受 enabled → disabled；必须 busy-free，并在同一事务内 CAS generation。
- generation 相同且已经 disabled 时安全重放 `changed=false`、不新增 audit；stale 一律 409。
- 这是停止新任务的状态切换，不是 B3C 的 drain/lease 终止；如果存在任何在途状态，返回
  `409 erp.endpoint_busy`，不静默撤回、不伪造完成。

### Revoke

- 必须 `confirm=true`、endpoint 已 disabled、busy-free、managed Express、当前 tenant active，
  且 generation 精确匹配；enabled、在途或 stale 均拒绝。
- 新增 `revoked_at timestamptz`、`revoked_by uuid` 终态墓碑；清空 source workspace 的
  `erp_endpoint_id`，令 endpoint `workspace_client_id=NULL, shared_scope=false, enabled=false`，
  generation 加一。
- 从 config 删除 `agent_token`、`agent_token_hash`、`agent_token_tail`、`agent_token_created_at`，
  其余 config/Profile、tenant/creator、membership、历史和 `erp_push_logs` 保留。
- revoked endpoint 永远不能 enable/rebind；只有完全相同的 operation_id 才能安全重放原结果。
  不能用新 operation_id 重新激活，也不能通过旧 gen0 CRUD 或 Companion writer 绕过墓碑。

## 5. 幂等、审计与锁序

`operation_id` 必须写入 `operation_logs.details`，并新增 tenant+operation_id（tenant 内全局唯一）的 ERP
endpoint 生命周期 partial unique expression index。审计白名单扩展为 endpoint、action、
operation_id、expected/actual generation、workspace before/after、enabled/shared/revoked before/
after、target、reason（reason 需脱敏/限长）；禁止写 token、密文或完整 config。完全相同请求
安全重放原响应；同 operation_id 但 endpoint/action/source/target/generation/tenant/actor 任一
不同返回 `409 erp.operation_id_conflict`。该冲突/重放判定在 endpoint 可见性与当前 endpoint
状态查询之前；因此已认证的同 tenant owner 不会因旧 endpoint 不存在而得到不同结果，也不会泄露
旧 endpoint 细节。跨 tenant 或未授权请求仍按不可见返回 404。审计 insert 失败，整个状态、指针、config 和墓碑写入
必须回滚。

所有四路由必须采用同一锁序，避免交叉死锁：

1. endpoint advisory lock（按 endpoint UUID 稳定 hash）；
2. active owner membership/role 行及 user authority；
3. endpoint `FOR UPDATE`；
4. source/target workspace 按数值 id 升序 `FOR UPDATE`（同一 workspace 只锁一次）；
5. fixed-search-path managed busy helper，覆盖 endpoint 全 actor 的 pending/retrying/next_retry/
   任意 lease，包括已过期 lease；
6. generation、状态、tenant、adapter、revoked、source/target 指针的 CAS 检查；
7. endpoint 与 workspace pointer 更新；
8. required operation audit；
9. commit。

任何检查失败都在 commit 前返回并回滚；不得先写指针再补审计，也不得用应用内锁替代数据库锁。

## 6. 数据库与 RLS 设计门

- 迁移必须 additive、可重放、transactional，并在启动 ensure 与 Alembic archive 双跑；约束允许
  revoked tombstone，同时保证 `revoked_at/revoked_by` 成对、revoked 必须 disabled/unshared/
  workspace NULL，非 revoked 不能带墓碑。
- managed busy helper 使用 fixed `search_path=pg_catalog` 和显式 `public.*` 对象；撤销 PUBLIC
  execute，仅当 `pearnly_app` 存在时条件 grant，并在 helper 内自验 tenant、owner、adapter、
  generation 和 endpoint 身份。
- 禁止 RLS bypass、tenant-only policy 和“大函数”万能写入口。生命周期 policy 必须是 exact
  GUC policy：tenant、actor、endpoint、action、source、target、expected generation 全部绑定；
  GUC 只是 transaction-local routing gate，不是认证边界。
- managed sensitive-column transition trigger 必须拒绝绕过路由/actor/operation 的 token/config、
  workspace、generation、enabled/shared/revoked 非法跃迁；只允许四动作定义的精确变更。
- 现有 `erp_endpoints` 共享 Express partial unique 继续生效；不删除、不自动合并冲突；
  `erp_push_logs` 所有权和 actor `user_id` 语义不变。

## 7. 落地四问与精确文件清单

1. **领域**：`erp`，子域为 shared Express endpoint lifecycle。
2. **新增/修改源码**：
   - `routes/erp_shared_express_lifecycle_routes.py`：四个 POST handler、请求 schema、flag/入口/
     权限准入和安全响应。
   - `services/erp/shared_express_lifecycle.py`：事务编排、幂等判定、CAS、统一锁序、状态结果。
   - `services/erp/shared_express_lifecycle_schema.py`：列/约束、索引、trigger、policy、busy
     helper、conditional ACL 与 startup ensure；与已有 enrollment/managed schema 保持单一职责。
   - `services/audit/store.py`：只扩现有 operation log 的白名单/字段序列化能力；不另建 audit 表。
   - `routes/erp_routes.py`：include lifecycle router；`docs/agent/agent_registry.json` 登记
     新 route 为 `C`；`app.py` 不新增第二棵 ERP router。
3. **迁移与 schema archive**：
   - `alembic/versions/0112_erp_shared_express_lifecycle.py`：`revoked_at/revoked_by`、
     operation-id partial unique、约束/trigger/policy/helper 的 archive。
   - `alembic/sql/001a_legacy_tables.sql`：同步增量 DDL，保持可重复执行且不修改 gen0 语义。
   - `docs/db/prod-schema.sql`：生产 schema archive 同步，包含列、索引、约束、trigger、policy、
     helper ACL/search_path 的可读定义。
   - `services/startup.py`：调用 lifecycle ensure，并在 readiness 中 fail-closed 校验 catalog。
   - 兼容核查但不改旧语义：`services/erp/shared_express_enrollment_schema.py`、
     `services/erp/shared_express_managed_schema.py`、`services/workspace/endpoint_binding.py`；
     它们只保留 B3B2b-1 的 enrollment/managed 读和 gen0 绑定隔离，不能被生命周期写入复用成
     第二套锁或第二套状态。
4. **测试与旧实现**：
   - `tests/unit/test_erp_shared_express_lifecycle_contract.py`：路由注册、请求字段、flag/入口/
     owner 权限、safe response、error code、旧 CRUD/gen0 隔离。
   - `tests/unit/test_erp_shared_express_lifecycle_pg_smoke.py`：真实 PostgreSQL schema、CAS、
     idempotency、revoke tombstone、audit rollback、ACL/search_path/trigger/policy。
   - `tests/integration/test_erp_shared_express_lifecycle_rls_real_tables.py`：真实表/真实 RLS
     tenant 与 actor 隔离，禁止伪造 GUC 越权。
   - `tests/unit/test_erp_shared_enrollment_pg_smoke.py`、
     `tests/unit/test_erp_shared_managed_pg_smoke.py`：只在既有合同需要时补回归，不改变 enrollment
     与 managed read 的行为。
   - 旧实现：`N/A`；`services/erp/push_store.py`、`services/erp/express_push/agent_store.py`、
     `services/erp/express_push/agent_reporting.py` 等 legacy writer 继续严格 `generation=0`，
     本批不得改成 managed writer。

## 8. 真 PostgreSQL 并发与失败矩阵

每个 case 要有唯一 operation id、tenant/workspace/endpoint/actor 别名、expected generation、
结果行和 audit readback；不得用 mock 代替事务/锁/RLS 证据。

| 场景 | 预期 |
|---|---|
| 两个 owner 对同 endpoint 同时 disable/enable | 一次 CAS changed=true，另一请求按实际 generation 409 或同请求安全重放；无双 audit、无死锁 |
| 两 endpoint 同时指向同 target | 只有一个成功，另一个 `workspace_endpoint_conflict` 409；source/target 指针不半更新 |
| A↔B rebind 20–50 轮并发 | 统一 advisory→owner→endpoint→workspace 升序锁序，无死锁；每轮 generation 单调、指针精确 |
| rebind 与 legacy writer/旧 retry race | managed promotion/lifecycle 永不接收 gen0 writer；busy 或旧代隔离，不能丢队列/写假 history |
| 各 busy 态：pending、retrying、next_retry、lease 未过期/已过期、多个 actor | 四动作都安全 409；无状态、指针、audit 半写 |
| enable/disable/rebind stale、未来 generation | 全部 409，不改变 enabled、workspace 或 generation |
| rebind source 空/错、target inactive/跨 tenant/已有其他 endpoint | 不可见/跨 tenant 对象统一 404；可见冲突 409，不泄露跨租户数据 |
| audit insert 失败、trigger 拒绝、unique 冲突 | 事务全回滚，不能留下墓碑、指针或 enabled 假状态 |
| RLS 伪造 tenant/actor/workspace/action/expected generation GUC | policy/trigger 拒绝；真实 owner 之外不可读写 |
| revoke token/config/terminal | token 四键清除；其余 config/Profile、历史、membership、logs 保留；墓碑成对且不可 enable/rebind |
| 同 operation_id 完全相同请求重放 | 返回原结果、无新 audit、无 generation 二次递增 |
| 同 operation_id 改 endpoint/action/source/target/generation/tenant/actor | `erp.operation_id_conflict` 409、无写入 |

自动化最小门：所有 contract + 真 PG + RLS cases 全 PASS、0 skip；并运行 black/ruff、
`git diff --check`、数据库 destructive-test gate 和完整 pre-push。任何 flag 仍 OFF，不能写
`READY_FOR_DEVICE`。生产 readback 只验证 migration/catalog/ACL/flags 及现有端点未被推广，不执行
四路由、不执行 revoke、不制造业务数据。

## 9. 派单完成条件与后续门

代理交付必须包含：改动文件清单、错误码表、真实 PG 并发结果、schema/ACL/search_path/trigger
回读、所有 tenant flag OFF 的证据和未解决问题；不得把 HTTP 200、CAS 入队或 audit 行单独称为
ERP 成功。B3B2b-2 完成后仍保持 `CODE_CANDIDATE_FLAG_OFF_NOT_USABLE_UNTIL_B3B3_AND_B3C`。

只有 B3B3 建立 bound/live heartbeat、Profile mismatch 反证及 legacy live isolation，B3C 建立
reservation/finalize、managed push log、Agent lease/ack 和 steward bridge，B4 做网页 UI，B5
完成测试 tenant/Express report/owner+employee 真机回归后，才可讨论 F1 的 `READY_FOR_DEVICE`。
