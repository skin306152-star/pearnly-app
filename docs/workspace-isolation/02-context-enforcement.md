# 套账隔离 · 02 请求上下文与强制机制

> 怎么把"当前套账"做成像 tenant 一样的请求级上下文,并用机械闸防回归。
> 核心反模式(必须杀死):**"前端可选传的 query 参数,后端缺了就静默看全部"**——识别记录串数据就是这么来的。

## 三层强制(全部都要,缺一层都漏)

```
① 请求上下文解析   resolve_workspace(request) → 校验归属 → 注入 handler
② DAL 约束        每个运营 store 函数签名强制要 workspace_client_id;每句 SQL 带它
③ CI 机械闸        扫运营表查询,缺 workspace_client_id 过滤 → fail
```

## ① 请求上下文:resolve_workspace

现有锚点:`tenant_id` 走 `core.route_helpers._tid(user)`;POS 已有 `require_workspace`(commit 85da4aa)。**推广/统一**成全站运营接口的依赖。

**来源(优先级)**:
1. 请求头 `X-Workspace-Client-Id`(SPA 顶栏切换器设置当前套账)。
2. (可选)用户的"上次选中套账"——存 `users.last_workspace_client_id` 或会话,前端启动回填到头。
3. 单套账用户(零售/餐厅):若租户恰好 1 个套账,缺省自动取它(免切换器)。

**校验(每请求,fail closed)**:
```
ws = header / session
若运营接口且 ws 缺失或非数字 → 400 workspace.required(不静默看全部)
SELECT 1 FROM workspace_clients
  WHERE id = ws AND tenant_id = <本租户> AND is_active = TRUE
  [AND id = ANY(<该用户被授权的套账>)]      ← 员工分配,见权限
若无 → 403 workspace.forbidden
通过 → 注入 request.state.workspace_client_id
```

**例外白名单**(非运营接口,不要套账):登录/注册、`/api/me/*`、计费/额度、套账管理本身(列/建/改套账)、健康检查、模块开关。维护一份"运营接口清单"由闸校验(见 ③)。

## ② DAL 约束:函数签名 + SQL

**约定(大厂做法:让正确成为默认,错误难写出)**:

- 每个运营 store 读写函数签名**必须**显式收 `workspace_client_id`(不给默认值 None;不可省)。对照反例:`list_ocr_history(... tenant_id=None, client_id=None)` 里套账缺席——目标是让"漏传"在调用处就编译/测试期暴露。
- 每句运营 SQL 的 WHERE 同时含 `tenant_id = %s AND workspace_client_id = %s`。
- INSERT 必写 `workspace_client_id`,取自上下文,不取自请求体(防伪造;与 cashier_id 取自 token 同范式)。
- 子表(派生表)读取必挂头表(见 01"派生表原则")。

**统一入口建议**:加一个轻量 `WorkspaceScope` 上下文对象 `{tenant_id, workspace_client_id, user_id}`,路由解析一次,贯穿传到 store。减少逐参数漏传。

## ③ CI 机械闸:隔离测试

推广现有 `test_pos_inventory_sql_isolation` 范式(见 [[pos-pob4-b5-b6-shipped]] 硬化段)。三道:

1. **静态扫描** `test_workspace_sql_isolation.py`:遍历运营表名单,对每个 store 模块的 SQL 字符串断言——出现该表的 SELECT/UPDATE/DELETE 必同时出现 `workspace_client_id`(白名单豁免管理类查询)。仿 `check_*` 机械闸,进 pre-push + CI fail。
2. **跨套账 E2E** `_e2e_ws_isolation.py`:真账号,一个租户建两个套账 A/B,各播数据,断言"在 A 上下文调每个运营列表接口,返回零 B 的行"。逐模块一条。仿 `docs/pos/_e2e_isolation.py`。
3. **运营接口清单守恒** `test_operational_endpoints_require_workspace.py`:枚举运营路由,断言都挂了 `resolve_workspace` 依赖;新增运营路由忘挂 → fail。防"新接口又开个不隔离的口子"。

**切闸节奏**:闸先以 warning 落地(地基 PO),每模块改完把该模块纳入 fail 名单,全改完整体翻 fail(见 04)。避免一上来红掉未改模块、堵住别的提交(参照 [[ratchet-flip-not-low-risk]])。

## 权限叠加(套账授权 × role)

两层独立(对齐业态套餐原则):
- **套账授权**:用户能进哪些套账。owner=全部;员工=被分配的子集(现有 `get_visible_client_ids_for_user` 是"买方"维度,**需新增套账维度的分配**,或复用其表结构按 workspace_client 存)。
- **role**:进了套账内再按角色裁(收银员只收银,等)。
- `resolve_workspace` 的校验里带上"该用户被授权套账"过滤(上方 ① 的可选 AND 子句)。

## 前端套账切换器(与买方切换器分层)

- 顶栏**第一层**:套账切换器(换公司)→ 切换即:设 `X-Workspace-Client-Id`、持久化选中、**重拉当前页所有数据**(整界面换上下文,不只筛一个列表)。
- 顶栏**第二层**(套账内):买方/供应商筛选器(原 `client_id` 切换器,保留语义)。
- 单套账用户:第一层自动隐藏/锁定。
- 启动:无选中套账时,默认套账(单个)或弹"选择套账"(多个)——不进运营页就让套账悬空。

## 不依赖 RLS(再强调)

prod 角色 BYPASSRLS,Postgres RLS 形同虚设(见 [[pos-rls-bypass-app-layer-isolation]])。本项目隔离 100% 靠应用层 WHERE + 上述三道闸。RLS 可留作"再加一层"但**绝不作为唯一/主要防线**。
