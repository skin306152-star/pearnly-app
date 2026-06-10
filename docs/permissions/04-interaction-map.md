# 权限管理整顿 · 04 互通地图 + 屏稿

> UI 一律照 `docs/ui/DESIGN_LANGUAGE.md`(收拢版·Emerald 基座)。HTML 预览稿出在 `桌面/Pearnly_权限_UI预览/`,Zihao 拍板后施工照搬挂视觉闸。

## 屏清单(3 屏 + 1 公开页)

### 屏 1 · 设置 → 团队与权限(主操作面 · owner/admin)

替换现「团队管理」入口,进设置页 tab(与业务/模块 tab 并列)。

- **顶部行动卡**:北极星「团队 N 人 · 待接受邀请 M 份」+ 主按钮「邀请成员」。
- **成员列表**(收拢单列):头像/姓名/用户名 · 角色徽章 · 作用域(全部 / N 个套账) · 状态(在用/停用) · 行内展开 = 改角色 + 配作用域 + 启停 + 移除。
  - owner 行:皇冠标,无操作菜单(只有 owner 本人行内见「转移所有权」)。
  - 自己的行:操作禁用(防自锁)。
- **待接受邀请区**(有才显):目标/角色/剩余有效期/撤回。
- **邀请弹窗**(.modal):通道(邮件 | LINE)→ 目标 → 角色卡单选(角色说明卡:一句话+权限分组摘要,permission-role review)→ 作用域(默认全部;选「仅指定套账」展开套账多选)→ 发送。
- **角色变更弹窗**:同角色卡;若降档导致正在用的能力消失(如会计→只读),列明会失去什么再确认。

### 屏 2 · 配作用域(屏 1 行内展开,不独立路由)

- scope_mode 开关:全部套账 | 仅指定套账。
- 套账主体多选列表(workspace_clients·按名称搜),勾选即所见范围。
- 事务所文案:「该员工只能看到和处理勾选客户的账」。

### 屏 3 · 安全日志(设置 tab · owner/admin · audit.log.view)

- operation_logs 过滤视图:预置筛选「团队与权限」(team.* / role.* / scope.* / ownership.*)。
- 行:时间 · 操作者 · 人话描述(「把 Somchai 从录入员改为会计」)· 展开看 details。
- 依据:Stripe Security history 形态(事件类型过滤 + 全员可见范围限 admin)。

### 公开页 · 邀请接受(/invite/{token})

- 渲染:「{租户名} 邀请你以 {角色名} 加入 Pearnly」+ 角色一句话。
- 无账号:注册表单(用户名/密码/语言)→ 入组 → 进 home。
- 有账号:登录 → 入组(已属别的租户 = 人话拒绝)。
- 过期/已用/已撤:对应空态文案 + 「联系邀请人重新发送」。

## 四态 + 边界

| 场景 | 行为 |
|---|---|
| 空 | 团队只有自己:行动卡引导「邀请第一位成员」 |
| 载入/错 | 骨架 + 信封错误人话(全站标准) |
| 删/降最后一个 owner | 422 拦截(理论上 UI 已挡,后端兜底) |
| 改自己角色 / 移除自己 | 422 `cannot_modify_self` |
| 邀请已存在的用户名/邮箱(本租户) | 422 人话提示 |
| 邀请 token 过期/重放 | 接受页空态;token 单次有效 |
| assigned 成员访问未分配套账 | 404(防枚举);套账切换器只列已分配 |
| 模块关闭但成员有该模块权限 | 导航不显(module-nav 现逻辑)+ 后端 403 module_disabled |
| 降档进行时(他正在开票途中被降权) | 下一个请求 403,前端信封提示「权限已变更」+ 刷新 |

## 模块联动

- 权限码→模块映射在 registry 静态推导(`sales.* → sales` 模块),`assert_module_enabled` 退役。
- 业态 onboarding / tenant_modules 七开关 / data-show-if-* 的模块部分:行为不变,只换数据源(can() 协议)。
- 做账/报税(待施工模块)按 02 的占位码直接 require_perm,不再二次开门。

## 角色×屏幕可见性(前端验收基准)

| 屏/能力 | owner | admin | accountant | clerk | viewer |
|---|---|---|---|---|---|
| 设置·团队与权限 | ✔ | ✔ | ─ | ─ | ─ |
| 设置·业务/模块 | ✔ | ✔ | ─ | ─ | ─ |
| 订阅&充值(data-show-if-money) | ✔ | 只读 | ─ | ─ | ─ |
| 销项工作台:开出按钮 | ✔ | ✔ | ✔ | ─(只有存草稿) | ─(纯看) |
| 进项:录入/上传 | ✔ | ✔ | ✔ | ✔ | ─ |
| 报表/导出 | ✔ | ✔ | ✔ | ─ | ✔ |
| 安全日志 | ✔ | ✔ | ─ | ─ | ─ |

E2E 验收 = 每角色一个真账号,逐屏断言可见性 + 后端 403/404(不止 grep 类名,真浏览器 isVisible)。

## 现状代码触点(施工导航)

| 触点 | 文件 |
|---|---|
| 菜单显隐 applyRoleVisibility | src/home/topbar-avatar.ts:34 |
| 模块导航 | src/home/module-nav.ts |
| 团队管理现页(7 接口) | routes/team_routes.py · services/team/store.py |
| owner 判定(invited_by) | core/pos_api.py:163 |
| 审计写入 | services/audit/store.py |
| 死表 schema | services/membership/schema.py:42(roles)·:50(memberships)·:66(client_assignments) |
