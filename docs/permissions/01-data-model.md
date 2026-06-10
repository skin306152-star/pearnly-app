# 权限管理整顿 · 01 数据模型

> 原则:能复用不新建;schema 走迁移不走 ad-hoc;每张表 tenant 隔离;存量零破坏(老租户行为不变)。

## 表总览(收敛后)

| 表 | 状态 | 职责 |
|---|---|---|
| `roles` | **激活**(现为死表) | 角色定义:系统预设 6 行,`permissions` JSONB = 权限码数组或 `{"all": true}` |
| `memberships` | **唯一成员真相**(加列) | user↔tenant↔role + 作用域模式 + 状态 |
| `member_scopes` | 新建 | 成员↔套账主体分配(ReBAC 关系表) |
| `invitations` | 新建 | 邀请链接生命周期 |
| `operation_logs` | 复用 | 安全事件 = 一等 action 类型(不新建表) |
| `users.role` | **降级为缓存/兼容** | 真相迁到 memberships;过渡期双写 |
| `user_company_roles` | **退役**(拍板点#3) | 数据迁入 memberships;计费读取点改造 |
| `client_assignments` | **退役**(拍板点#2) | 语义由 member_scopes 接管(单位从买方 client 换成套账 workspace_client) |

## 逐表定义

### roles(激活既有表 · `services/membership/schema.py:42`)

系统预设行 `tenant_id IS NULL`(全局共享,licence 上不归任何租户),P2 自定义角色时插租户行,表结构今天就留好位:

```sql
-- 既有列:id uuid PK, name text, permissions jsonb
ALTER TABLE roles ADD COLUMN IF NOT EXISTS tenant_id uuid NULL;      -- NULL=系统预设
ALTER TABLE roles ADD COLUMN IF NOT EXISTS key text;                  -- 'owner'|'admin'|'accountant'|'clerk'|'viewer'|'cashier'
ALTER TABLE roles ADD COLUMN IF NOT EXISTS is_system boolean DEFAULT false;
CREATE UNIQUE INDEX IF NOT EXISTS uq_roles_system_key ON roles(key) WHERE tenant_id IS NULL;
```

种子 6 行(key + permissions):`owner → {"all": true}`;其余 = 权限码数组(全集见 02)。
**permissions JSONB 不是真相的全部**:权限码合法集合在代码 registry(`services/authz/registry.py`)单一来源;JSONB 里出现 registry 没有的码 = 启动自检报错(防漂移)。

### memberships(加列 · 现 `UNIQUE(user_id)` 保持)

```sql
ALTER TABLE memberships ADD COLUMN IF NOT EXISTS scope_mode text NOT NULL DEFAULT 'all';
  -- 'all' = 全租户 | 'assigned' = 仅 member_scopes 列出的套账(Canopy Staff (Assigned Contacts) 模式)
ALTER TABLE memberships ADD COLUMN IF NOT EXISTS granted_by uuid NULL;     -- 谁给的这个角色(审计联动)
ALTER TABLE memberships ADD COLUMN IF NOT EXISTS granted_at timestamptz;
```

约束(应用层断言 + 单测,不靠 DB trigger):
- 每租户**至少 1 个 active 的 owner membership**(删/降最后一个 owner = 422 拦截)。
- owner 角色只能经「所有权转移流」变更,不能在改角色接口里直接授/撤(行业一致做法)。

### member_scopes(新建)

```sql
CREATE TABLE IF NOT EXISTS member_scopes (
  id bigserial PRIMARY KEY,
  tenant_id uuid NOT NULL,
  membership_id uuid NOT NULL REFERENCES memberships(id) ON DELETE CASCADE,
  workspace_client_id uuid NOT NULL,          -- 套账主体 = 数据硬边界(workspace-isolation 已收官的那个)
  assigned_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (membership_id, workspace_client_id)
);
CREATE INDEX IF NOT EXISTS ix_member_scopes_ws ON member_scopes(tenant_id, workspace_client_id);
```

语义:`scope_mode='assigned'` 的成员,所有带 workspace 维度的读写都被限制在本表列出的套账内(执行方式见 03)。`scope_mode='all'` 的成员不查本表。
**client_assignments 迁移**:旧表按买方 client_id 分配,语义对不上套账边界,不做自动数据迁移(事务所老板在新 UI 重新按套账分配,成本=一次点选);旧表只读保留一个版本周期后 drop。

### invitations(新建)

```sql
CREATE TABLE IF NOT EXISTS invitations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  email text NULL,                 -- 邮件邀请
  line_target text NULL,          -- LINE 邀请(拍板点#5)·二选一非空
  role_key text NOT NULL,          -- 不允许 'owner'(owner 只走转移流)
  scope_mode text NOT NULL DEFAULT 'all',
  token_hash text NOT NULL,        -- 链接 token 只存哈希(同改密链路做法)
  invited_by uuid NOT NULL,
  expires_at timestamptz NOT NULL, -- 默认 7 天
  accepted_at timestamptz NULL,
  accepted_user_id uuid NULL,
  revoked_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_invitations_tenant ON invitations(tenant_id, created_at DESC);
```

状态派生不另存:pending(未过期未接受未撤)/ accepted / expired / revoked。
接受流:点链接 → 没账号则注册(用户名+密码,role 不可选)→ 建 membership(role_key/scope_mode 照邀请)→ 标 accepted。已有账号且已属别的租户 = 明确拒绝(现 1 人 1 租户约束不动,提示用新邮箱注册)。

### 所有权显式化 + 转移

owner 真相 = `memberships.role = owner 角色`,**替代 `invited_by IS NULL` 判定**(`core/pos_api.py:174` 等)。存量回填:每租户把 `invited_by IS NULL` 的用户回填成 owner membership。

转移流(QBO+Square 杂交,最严做法):
1. 仅现任 owner 本人可发起;**接收方必须已是本租户 admin**(QBO 约束)。
2. 发起 → 生成确认 token(24h 时限,Square)→ 接收方登录确认。
3. 完成 = 同事务内:旧 owner membership 降为 admin + 新 owner 升 owner + 写 `ownership.transfer` 安全事件。**不可撤销**。
4. 拍板点外的简化:不做 Square 式换绑个人身份信息(我们账号本来就不挂 SSN 类数据)。

### 安全事件(复用 operation_logs · `services/audit/store.py`)

不新建表;新增 action 一等类型,details JSONB 记 before/after:

| action | details 关键字段 |
|---|---|
| `team.invite` | role_key, channel(email/line), invitation_id |
| `team.invite_revoke` | invitation_id |
| `team.member_join` | invitation_id, role_key |
| `role.change` | target_user_id, role_from, role_to |
| `scope.change` | target_user_id, scope_mode, ws_added[], ws_removed[] |
| `member.remove` / `member.toggle` | target_user_id(既有 employee.* 改挂新码,旧码读侧兼容) |
| `ownership.transfer` | from_user_id, to_user_id |

依据:Stripe Security history 把邀请/角色变更做成一等事件类型。保留期跟 operation_logs 现策略(不单独清理)。

## 存量映射(零破坏)

| 现状 | 映射 |
|---|---|
| users.role='owner' / invited_by IS NULL | memberships → owner |
| users.role='member'(受邀员工) | memberships → **accountant**(拍板点#6:现状权限≈全业务,映会计不降档) |
| is_super_admin | 不动(平台层,在 RBAC 之上短路,见 03) |
| POS cashier(typ=pos 令牌) | 不进 memberships;registry 里有 cashier 角色定义供 POS 门引用(见 02) |
| client_assignments 既有分配 | 不自动迁(语义换单位);老板新 UI 重配,期间员工 scope_mode='all' 保持现状可见性 |

## 迁移清单(ensure_* 启动自愈式,同 numbering_workspace_key 套路)

1. `ensure_authz_roles`:roles 加列 + 种子 6 系统角色(幂等 upsert by key)。
2. `ensure_authz_memberships`:memberships 加列 + 存量回填(owner/accountant 映射)+ 双写开关。
3. `ensure_authz_tables`:member_scopes + invitations 建表。
4. 退役(最后一刀,独立 commit):user_company_roles 读取点改造完 → drop;client_assignments 保留只读一个版本周期 → drop。
