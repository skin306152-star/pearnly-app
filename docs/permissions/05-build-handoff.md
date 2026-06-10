# 权限管理整顿 · 05 施工文案

> 高敏改造(动鉴权主路径)。原则:每步上线后全站行为与前一步逐字等价,真账号 E2E 对照;deny-by-default 只在最后一步合闸。

## 施工顺序(5 批 · 每批独立可上线)

### 批 1 · 地基(纯增量,零行为变化)
- `services/authz/`(registry / resolver / deps)+ 单测:矩阵全量断言(6 角色 × 56 码逐格)、未知码启动自检、deny-by-default。
- ensure_authz_roles / memberships / tables(01 的迁移)+ 存量回填(owner/accountant 映射)。
- 双写:建号/改角色同时写 users.role 与 memberships。
- 验收:全站现有 E2E 全绿(行为零变化);新单测绿。

### 批 2 · 9 门收敛(等价替换)
- 旧门变薄别名 → 逐路由换 `require_perm(码)`(施工时出全量路由对照表,一路由一行,review 逐条勾)。
- owner 判定从 invited_by 切到 membership(require_account_owner 语义点)。
- 验收:权限矩阵 E2E(owner/member 两存量角色逐路由 200/403 与切换前 diff = 空);POS 双令牌回归(118 单测 + 真机 E2E)。

### 批 3 · 团队与权限后端
- 邀请(email/LINE)+ 接受流 + 改角色/配作用域接口 + 所有权转移 + 安全事件落 operation_logs。
- scope 执行(deps 第 5 步)对带 workspace 维度的路由生效;scope_mode='all' 存量成员无感。
- 验收:邀请全流程真账号 E2E(注册新号入组 / 既有号拒绝 / 过期 / 撤回);最后一个 owner 拦截;转移流双向确认。

### 批 4 · 前端 3 屏 + can() 协议
- /api/me/permissions + can() helper;团队与权限 tab / 作用域配置 / 安全日志;邀请接受公开页。
- data-show-if-* 逐个改读 can()(团队/money/admin 三个先行)。
- 验收:5 角色 × 逐屏真浏览器可见性矩阵(04 表);视觉闸(照预览稿)。

### 批 5 · 收口
- 删旧门别名、user_company_roles 读取点改造 + drop、client_assignments 只读冻结(下版本 drop)、users.role 标记 deprecated(读侧兼容保留)。
- **机械闸合闸**(见下)。
- /simplify 全链。

## 机械闸(新增第 8 道)

`scripts/check_authz_coverage.py`(pre-push + CI fail):
- 遍历 FastAPI app.routes,每条路由必须满足其一:① dependencies 含 require_perm/require_any ② 在 `PUBLIC_ROUTES` 显式白名单(登录/注册/邀请接受/webhook/静态)③ 平台层(_require_super_admin)。
- 白名单加条目必须带注释说明为何公开;闸输出缺门路由清单。
- 依据:OWASP "A single missed check can compromise resource security"——漏门靠机器拦,不靠自觉。

## 测试矩阵(底线)

| 层 | 内容 |
|---|---|
| 单测 | registry×roles 逐格断言 · resolver 短路顺序 · deny-by-default(未知码=拒)· scope 404 语义 |
| 集成 | 9 门对照(切换前后 diff=空)· 邀请生命周期 · 转移流 · 最后 owner 拦截 · 自锁拦截 |
| 真库 E2E | 5 角色真账号逐路由 200/403/404 · assigned 成员跨套账 404 · POS 令牌不越权(pos 码集外全 403) |
| 真浏览器 | 04 可见性矩阵逐屏 isVisible · 邀请接受页四态 |
| 机械闸 | check_authz_coverage · registry/JSONB 一致性自检 |

## 风险与红线

- **铁律范围**:登录主路径(core/auth.py 的 token 签发/校验)本次只加不改;LINE 主路径一字不动;POS 离线链路一字不动。
- 改密/单设备/jti 逻辑不碰(身份层已达标)。
- 批 2 是最高危的一批:必须独立 commit + 全量对照 E2E,push 前 Zihao 知会(push 即上线)。
- 存量员工映射「会计」(拍板点#6)若 Zihao 改判「录入员」:开票/审批立即对他们 403,需提前通知用户——映射档位是产品决策不是技术决策。
- 回滚:批 1-2 双写期间任何异常,旧门别名仍在,revert 单 commit 即回旧世界。

## 工程标准对齐

- 新文件全 <500 行(authz 三件套预估 120/150/180);每新文件 ≥1 测试;schema 走 ensure 迁移;SQL 全参数化 + tenant 隔离;Conventional Commits;i18n 4 语齐(角色名/错误码/邀请文案);UI 四态;无 AI 味。
