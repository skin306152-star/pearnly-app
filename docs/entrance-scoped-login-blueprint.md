# 入口级会话隔离（"各是各的"）执行蓝图

> 立案 2026-07-15 · 施工中 · Zihao 拍板。产品按域名/路径分入口（pearnly.com 营销无登录 /
> `/login` 会计站自由注册 / `/pos` 收银老板后台邀请制 / `/ai` Pearnly AI 邀请制 / `/cashier`
> 收银台设备）。此前登录零隔离：同一账号密码从任何门都通、拿同一 token，入口纯前端装饰壳，
> 还串壳（登 ai 却落会计/pos）。本蓝图把它做成商业级"各是各的"。跨窗施工先读此页 + 记忆
> `entrance-scoped-login-design`。

## 1. 定稿模型（四层各管各的）

| 层 | 事实源 | 现状 → 目标 |
|---|---|---|
| 身份 | 账号密码（一套） | 不变 |
| **入口授权** | **授权入口集** `{main,pos,ai}` | 新增（Phase1 推导 / Phase2 落表）|
| **入口会话** | **token 的 `entry` claim** | 新增（取代 per-browser localStorage 猜测）|
| 功能模块 | tenant_modules / pearnly_ai allowlist | 保留（后端已真隔离）|

- 授权来源：`main`=业态非 pos_only（自由注册即得）；`pos`=开通 pos 模块（Earn 发放）；`ai`=在
  `pearnly_ai_m1` 白名单（Earn 邀请）。同账号可多线。
- 登录是**入口级**：`entry ∈ 授权集？` 否 → **401 `auth.invalid_credentials`（与密码错同一个错、
  不泄漏、无指向文案；且不计失败锁定，避免用错门锁死真账号/撞门 DoS）**。超管任意门放行。
- 壳 + API 都认 `token.entry`。登录页选择（pre-auth 无 token）仍用持久提示 `pearnly_entry`（降级为
  纯提示、登出即清、自愈收敛到权威 entry）——这是"拿到 token 前无从读 token"的先天矛盾正解。
- **单会话保留**（Zihao 拍板）：切入口 = 重新登录，不要求两线同时在线 → active_jti 机制不动。

## 2. Zihao 拍板 / 关键决策

- Phase 1/2/3 全做（3 = 连 API 都串不了）。
- 未授权拒登 = **账号密码错误**（不写"去别处登录"指向文案）。
- pos/ai 邀请制；同账号可被 Earn 邀请进多条线；从哪个门登录就是那个门的功能。
- `/pos` 早年是收银台域名、现改老板后台 → 删掉"残留 pos_store_token 即劫持 /cashier"守卫
  （老板浏览器残留令牌被误劫持；收银设备的家是 `/cashier`）。没有真实设备还书签 `/pos`。
- **回退/放量**：`entrance_gate` flag 默认关=不拦（现状）；测稳后 `rollout=all`（人类门，Zihao 真机点头
  后开）；锁不对随时关回。不搞灰度金丝雀（Zihao 定调），但保留 kill-switch。

## 3. 三期施工

### Phase 1 · 植根会话（拒登 + 入口定功能 + 零串壳）—— 施工中
后端（已落地 + 单测绿）：
- `core/auth.py`：`create_access_token(entry='main')` 烙 `entry` claim（未知值收敛 main）；
  `get_current_user_from_request` 显式 `user["entry"]=payload.get("entry") or "main"`（user 从 DB 重建，
  不透传就整链读不到）；`entry_of_request()` 供路由把权威 entry 下发前端。
- `core/pos_api.py`：收银员合成主体带 `entry='pos'`。
- `core/feature_flags.py`：`entrance_gate_enabled_for()` 回退开关（默认关）。
- `services/auth/entrance.py`（新·单一事实源）：`authorized_entrances()`（Phase1 推导版）+
  `login_entrance_allowed()`（超管放行/闸关不拦/推导异常 fail-open）。
- `routes/login_routes.py`：`LoginRequest.entry` 可选字段 + 准入校验 + token 传 entry。
- `routes/modules_routes.py`：`GET /api/me/modules` 响应加 `entry`（前端壳权威来源）。

前端（已落地 + build + dist）：
- `src/home/module-nav.ts`：`apply(modules, business_type, entry)` 认服务器 entry，回落 localStorage，
  自愈回写提示；resolvePreset 的 pos 护栏对齐。
- `src/home/topbar-avatar.ts`：登出 `removeItem('pearnly_entry')`。
- 三登录页带各自 entry：`landing.js`='main'、`pos-login.html`='pos'（+删劫持守卫）、`ai-api.js`/`ai-gate.js`='ai'。
- `home.html` `?v` bump（cachebust）。

测试：`test_entrance_gate.py`（新）、`test_auth_session_hardening.py`（+entry claim）、
`test_entry_shell_routing.py`（改认服务器 entry）、`test_pos_login_page_static.py`（劫持已删反向钉）。

**验收**：单测全绿；headless 真浏览器跑五场景（firm/pos 壳 + 串壳根治 + 旧后端回落 + /pos 不劫持）。
**未 push**：登录主路径 push 需 Zihao 真机人类门；`entrance_gate` 开闸放量同为人类门。

### Phase 2 · 授权入口集单一事实源（落表）—— 待办
- 新建 `tenant_entrances` 表（alembic，禁 services `ensure_`）；`signup_core.py` 写 main；
  Earn 开 POS（`entitlements.grant`）写 pos、邀请 AI（`admin_pearnly_ai_routes`）写 ai；迁移存量。
- `authorized_entrances()` 从"推导"换成读表（只改 `services/auth/entrance.py` 一处）。
- `business_type` 退役出定壳判据，保留元数据用途（餐厅桌台/服务费/pos_only 一号一店/登出路由）。
- 新路由登记 `agent_registry.json`（lint-agent 硬门）+ 配 `test_*_contract.py`。

### Phase 3 · 严格隔离（连 API 都串不了）—— 待办
- `services/authz/deps.py:_check` 加入口闸：`token.entry` 不含 code 所属入口 → 拒（复用现有
  403/PosError 两种错误形态）。**按权限码判、不按 URL 判**（`tax_profile_routes` 是 AI 接口却寄生
  `/api/workspace` 路径）。中性横切码（module_of=None：team/billing/settings/audit/field/ownership）
  短路放行否则登录 bootstrap 全崩。AI 的 `tax.*` 码显式归 ai（module_of=None 靠不住）。
  `/admin/*`+`/earn`+超管豁免。收银员/设备 token 天然免疫。
- 前端 `core-boot.ts:routeTo` 补 entry 路由守卫（现零守卫，pos-entry 手敲 `#/vouchers` 照进会计页）。
- 封死影子活体 `PUT /api/pos/admin/modules`（+ `business-presets` 孤悬端点）。
- 入口级隔离测试（仓内零覆盖）：main-token 打 POS 端点被拒 / pos-token 打 main 端点被拒。

## 4. 勘察拍死的约束（7 路只读勘察结论）

1. `entry` 只能可选默认 main——必填会让 4 登录页 + 全 e2e/脚本请求体全线 422。
2. token 最小声明 JWT：加 claim 必**两端动手**（签发写 payload + 请求侧显式透传，user 从 DB 重建）。
3. 6 个孤儿签发点默认 main（主登录/注册/Google/LINE/LIFF/账号合并）——LINE 用户天然归会计站。
4. `'ai'` entry 值原本全仓不存在，ai-gate 从不写——本批新增。
5. Phase3 闸挂 `_check` 一处、按码判、中性码短路、AI 靠 flag+码非模块、超管/admin/earn 豁免。
6. 单会话 active_jti：同账号切门会互踢——Zihao 选保留（切门=重登），不做 per-entry 会话。

## 5. 雷区与中和

先天矛盾（pre-auth 无 token）→ 提示/权威分离；深链窜路由 → Phase3 补守卫；套账门认业态不认
entry → 判据叠加 entry；超管无稳定 entry → 豁免；孤儿签发 → 默认 main；影子活体 → 封死；
preboot 遮罩误伤 → 入口壳不新增 preboot、复用现有门时序；module-nav 每次覆盖 window._entry →
改壳来源一起改（已改）。

## 6. CI 闸负担

改的文件全在 lint-size 棘轮监控 → 净增写 `RATCHET-EXEMPT`；改前端源必 build + 提交 dist + bump
`home.html` `dist/main.js?v=`（cachebust 闸）；Phase2 新路由禁进 app.py（lint-debt）+ 登记
`agent_registry.json`（lint-agent 硬门）+ 配 contract 测试；建表走 alembic 禁 services `ensure_`。
e2e 凭据只在 env，CI 无凭据下 01/13/15/24/25 全 skip（改坏真登录 CI 绿也发现不了，只本地炸）。

## 7. 状态

- Phase 1 后端 + 前端已落地、单测绿、build 出 dist、headless 验收进行/通过。**未 push（等 Zihao 真机门）**。
- Phase 2 / Phase 3 待办。
- `entrance_gate` 默认关 → 即便部署也零行为变化，直到 Zihao 真机点头 `rollout=all` 放量。
