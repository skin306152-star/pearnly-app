# 权限管理整顿 · 03 执行点与接口契约

> OWASP 三铁律落地:deny-by-default · 单一服务端执行点 · 每请求校验。前端显隐只是 UX,不是安全。

## 统一执行点 `require_perm()`

新包 `services/authz/`:

```
services/authz/registry.py   # 权限码全集(02 的代码化·tuple 常量+按模块分组)
services/authz/resolver.py   # user → 生效权限集(role permissions ∪ all 短路)·单请求内缓存
services/authz/deps.py       # require_perm(code) / require_any(codes) FastAPI dependency
```

判定顺序(全部在 deps 单点,任何路由不得自己写 if role):

```
1. is_super_admin            → 放行(平台层短路)
2. POS 令牌(typ=pos/pos_store)→ 只认 cashier 角色码集(pos.sale.operate 等),其余一律 403
3. 模块联动:code 所属模块在 tenant_modules 关闭 → 403 module_disabled
4. membership.role.permissions 含 code(或 {"all":true})→ 过,否则 403 forbidden
5. 资源带 workspace 维度且 scope_mode='assigned' → member_scopes 校验,未分配 → 404
```

- 错误码进信封体系:`403 forbidden` / `403 module_disabled` / `404 not_found`(scope 防枚举)。i18n 4 语人话文案,不露权限码。
- 授权失败记结构化日志(OWASP "Implement Appropriate Logging"):code、user、tenant、path,一致格式可聚合。
- registry 与 roles 表 JSONB 启动自检互卡(JSONB 出现未知码 = 启动报错)。

## 9 门收敛映射(旧门 → 新码)

旧门**先变薄别名**(内部转调 require_perm),路由逐批换新码,全换完删别名。迁移期行为逐字等价(同一批 E2E 对照跑)。

| 旧门(位置) | 新形态 |
|---|---|
| `_require_super_admin`(core/route_helpers.py:58) | 保留(平台层,短路逻辑并入 deps) |
| `_require_owner_or_super`(route_helpers.py:221) | `require_perm("team.member.view")` 等按路由实际语义逐条标注(施工时列全量对照表) |
| `_require_tenant`(route_helpers.py:209) | 被 resolver 吸收(无 tenant = 401,人人都查) |
| `require_account_owner`(core/pos_api.py:163·invited_by IS NULL) | `require_perm("settings.modules.manage")`;**owner 判定改 membership,删 invited_by 语义** |
| `require_owner`(pos_api.py:148) | `require_perm("pos.admin.manage")` |
| `pos_auth`(pos_api.py:96) | 保留为令牌解析层,角色判定走 deps 第 2 步 |
| `require_workspace`(pos_api.py:181) | 保留(套账归属校验)+ 叠加第 5 步 scope 校验 |
| `assert_module_enabled`(pos_api.py:191) | 被 deps 第 3 步吸收(码→模块映射自动推导,路由不再手动传模块名) |
| `auth_member`(routes/purchase_common.py) | `require_perm("purchase.doc.create")` 系 |

## 接口契约(新增/变更)

### 前端权限协议

```
GET /api/me/permissions
→ { ok, data: { role_key, scope_mode,
                permissions: ["sales.doc.view", ...],   # 生效全集(超管返 ["*"])
                workspace_ids: [...] | null } }          # assigned 时返分配清单
```

前端 core-boot 拉一次进内存,显隐统一走 `can(code)` helper;逐步替换 data-show-if-*(topbar-avatar.ts / module-nav.ts)。**变更角色后服务端即时生效**(每请求查库),前端下次拉取刷新——接受短暂显示滞后,后端兜底。

### 团队与权限(替换/扩展现 /api/team/*)

```
GET    /api/team/members                       # 成员列表(角色/作用域/状态/最近活跃)
PUT    /api/team/members/{uid}/role            # 改角色(不可设 owner·不可改自己·见边界)
PUT    /api/team/members/{uid}/scope           # scope_mode + workspace_ids 全量替换
PATCH  /api/team/members/{uid}/active          # 启停(沿用)
DELETE /api/team/members/{uid}                 # 移除(沿用·级联清理)
POST   /api/team/invitations                   # {channel: email|line, target, role_key, scope_mode, workspace_ids}
GET    /api/team/invitations                   # pending 列表
DELETE /api/team/invitations/{id}              # 撤回
GET    /api/team/roles                         # 角色说明卡数据(key/名称/权限分组·permission-role review)
POST   /api/ownership/transfer                 # 发起(target 必须是 admin·签 24h token)
POST   /api/ownership/transfer/accept          # 接收方确认(同事务换角色+安全事件)
```

公开接受页(无登录态):

```
GET  /api/invitations/{token}/preview          # 租户名/角色名/过期态(供接受页渲染)
POST /api/invitations/{token}/accept           # 新号注册 or 既有号登录后入组
```

### 守门标注

- /api/team/* 与 /api/ownership/*:`require_perm("team.member.*")`;移除/改角色目标是 owner = 422 拦截;改自己角色 = 422(防自锁,Stripe 同款防呆)。
- 邀请的 role_key 禁 owner;invitation token 只存哈希、单次使用、7 天过期。

## 兼容与过渡

- `users.role` 双写保留 ≥1 个版本周期(JWT claim、老前端、报表读它);新逻辑只读 memberships。
- JWT 不加权限集 claim(权限变更要即时生效,token 7 天太长);只保留现有 role claim 兼容。
- POS 双令牌、收银 PIN、店铺码、离线 PWA:**一字不动**。
- LINE 主路径(铁律):不碰;LINE 邀请只复用现有改密链路的发消息通道。
