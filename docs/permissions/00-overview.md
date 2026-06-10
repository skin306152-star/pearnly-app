# 权限管理整顿 · 00 概念与边界

> 把"三个硬编码身份 + 九个零散的门"整顿成对标市场最高标准的一套 RBAC+作用域体系。
> 动前先读这页 + `docs/permissions/02-roles-permissions.md`(★核心:权限点全集+角色矩阵)。
> **状态:图纸草案(2026-06-10)· 待 Zihao 拍板封板**。拍板点清单见本页末尾。

## 一句话

**权限 = 角色(能做什么动作)× 作用域(对哪些数据)× 模块开关(租户买没买/开没开),三者正交;后端唯一执行点 `require_perm()`,deny-by-default,权限变更进安全审计。**

## 对标依据(2026-06-10 调研 · 官方文档原文核实)

| 设计决策 | 谁这么做 |
|---|---|
| 预设角色 4~6 个,不做自定义角色(P1) | Xero(4 角色无自定义)/ Stripe(细预设+叠加并集替代自定义)/ QBO·Square 把自定义锁在最高付费档 |
| 角色骨架 Owner→Admin→全功能→受限→只读 | Xero / QBO / Canopy / Stripe 共同骨架 |
| 录入与审批分档(建草稿 ≠ 开正式票) | Xero Invoice Only 四子档(Draft only / Sales / Purchases / Approve and pay)· NIST RBAC2 职责分离 |
| 作用域独立于角色:事务所员工"只看被分配客户" | Canopy 预设角色 Staff (Assigned Contacts) / Karbon Client Owner 关系 / Square 按 location |
| Owner 唯一·不可被他人移除·本人发起双向确认转移 | Xero Subscriber / QBO Primary admin(接收方须先是 Admin)/ Stripe Super Admin / Square(24h 时限) |
| 安全事件审计(邀人/改角色/移除)独立于业务审计 | Stripe Security history(180 天 + API)· QBO Audit Log(2 年) |
| deny-by-default · 单一服务端执行点 · 授权必有测试 | OWASP Authorization Cheat Sheet 逐条 |
| RBAC 骨架上叠"成员↔套账分配"关系(ReBAC) | OWASP 明确建议多租户对象级场景 ABAC/ReBAC 优于纯 RBAC |

调研报告原文(含来源 URL 和未确认事项)见本窗口记录;关键结论已分摊进各图纸的"依据"标注。

## 现状(2026-06-10 摸底 · file:line 见 04)

- 身份层达标:JWT+jti 单设备+改密失效(`core/auth.py`);POS 双令牌(typ=pos/pos_store)独立体系。
- 租户隔离达标:应用层全查询 `WHERE tenant_id`;RLS 兜底未强制(prod BYPASSRLS)。
- 审计有基座:`operation_logs`(actor/IP/UA/JSONB details)。
- **缺口**:角色只有 owner/member 两档无差别;9 个 require_* 各查各的;`roles` 表建了没接逻辑(死表);`memberships` 与 `user_company_roles` 职责重叠;owner 判定靠 `invited_by IS NULL`(出身不是角色,管理权交不出去);无邀请流(手动建号发密码);权限变更无专门审计。

## 范围(P1 一口气建完)

1. **权限点 registry**(~55 个 `module.resource.action` 码,代码单一来源)+ **6 预设角色**(老板/管理员/会计/录入员/只读/收银员)。
2. **作用域**:全租户 vs 仅被分配套账(`member_scopes` 按 workspace_client)。
3. **统一执行点** `require_perm()`,9 门收敛(旧门变薄别名,逐路由迁移)。
4. **数据模型收敛**:激活 `roles` 表 · memberships 定为唯一成员真相 · 邀请表 · owner 显式化+转移流。
5. **安全事件审计**:`team.invite / role.change / member.remove / ownership.transfer` 进 operation_logs 一等事件。
6. **前端**:`GET /api/me/permissions` 协议替代硬编码 data-show-if-*;设置页「团队与权限」屏。
7. **机械闸**:每条路由必须声明权限或在显式公开白名单(CI 拦漏门)。

## 非目标(P2+,先记不做)

- 自定义角色(对标结论:高配版差异化,P1 预设角色切细即可)。
- 多角色叠加并集(Stripe 模式,P1 单角色+作用域够用)。
- POS 敏感动作经理输码放行(Square Require passcode 模式)、实体工牌。
- 超管分级(只读超管 vs 运维超管)。
- 字段级权限(五家头部产品无一做)。
- RLS 强制启用(独立运维事项,本次不绑)。

## 六类完整性

| 类 | 覆盖 |
|---|---|
| ① 操作面 | 设置·团队与权限页(成员列表/邀请/改角色/分配套账) |
| ② 老板配置后台 | 同上(owner/admin 专属)+ 角色说明卡(permission-role review·NIST RBAC3) |
| ③ 登录/接入·角色 | 邀请链接接受流(新建号或既有号入组)· POS 令牌体系不动 |
| ④ 四态+边界 | 空(还没邀人)/载入/错 + 降自己权限拦截/最后一个 owner 拦截/邀请过期 |
| ⑤ 角色权限 | 本体。管团队 = `team.member.*`(owner/admin) |
| ⑥ 模块联动 | 模块关 ⇒ 该模块整组权限点不可用;业态 onboarding 不变 |

## 拍板点(封板前 Zihao 决定)

| # | 问题 | 建议 |
|---|---|---|
| 1 | 角色集:6 个(老板/管理员/会计/录入员/只读/收银员)够不够?事务所和 SME 共用一套? | 共用;事务所差异走作用域不走角色 |
| 2 | 作用域单位 = 套账主体(workspace_client)。现有 `client_assignments`(买方 client_id)迁移还是并存? | 迁到 member_scopes,旧表退役 |
| 3 | memberships 与 user_company_roles 收敛方向 | memberships 为唯一真相,加列;user_company_roles 退役(计费引用改读 memberships) |
| 4 | 只读角色可不可以导出报表? | 可(Stripe View Only 可导出) |
| 5 | 邀请通道:邮件之外要不要 LINE 邀请链接? | 要(泰国市场,复用现有 LINE 改密链路) |
| 6 | 旧 member 员工的存量映射:全部映成「会计」还是「录入员」? | 会计(现状权限≈全业务,降档会破坏在用功能) |
