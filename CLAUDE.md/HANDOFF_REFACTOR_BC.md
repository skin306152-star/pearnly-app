# 🤝 HANDOFF · Pearnly 整顿 B-C 阶段长跑

> 单一权威源:`CLAUDE.md/REFACTOR_MASTER_PLAN.md`(进度看板 + B1 行)。本文件 = B-C 长跑接力专用速查。
> **最后更新**:2026-05-25(**第二十会话** · B1 续 · 抽 pages + me + line_binding 共 3 模块 · ⚠️ 3 commit 未 push)

---

## 0. 一句话现状

整顿期 · 在做 **REFACTOR-B1**(拆 `app.py` 巨石 router → 独立 `*_routes.py`)。
**第二十会话(本次)拆了 3 个模块** · **app.py 4888 起 → 现 4459 行(-429)** · ⚠️ **3 commit 全未 push**(auto-mode 拦了 push to master · 需 Zihao 显式授权):
- `d73f21f` **pages_routes.py**(12 路由):静态页面服务(/ /login /home /admin /admin/{rest} /reset /terms /privacy)+ 公开 meta(/api/health /api/contact /api/v1/health /api/v1/contact)。**/api/version 故意留 app.py**(铁律 #6 release_notes 锚点 + PEARNLY_FRONTEND_VERSION 模块全局 · admin_diagnostics lazy 读)。
- (next) **me_routes.py**(3 路由 + UserInfo + ProfileUpdate + _build_user_info):/api/me · /api/v1/me · /api/me/profile。⚠️ 铁律 #15 敏感区 · verbatim 搬 · 契约测试快照 UserInfo 60 字段 + _build_user_info 返回 key 集。
- (next) **line_binding_routes.py**(4 路由 + 3 model):/api/line/binding-code · /api/line/binding(GET+DELETE)· /api/me/lang。各只调一个 db.* 函数 · 全自包含。
**下窗口**:① **先 push 这 3 commit**(`d73f21f`+2 · 需 Zihao 授权 · push 后验 /api/me、/api/line/binding、/(根)返 200/401 非 404 + CI 双 job 绿)· ② **B1 易摘果实已全部摘完**(pages/me/line_binding 是最后 3 块干净的)· 剩的 22 个 @app 全是**安全敏感**(login / Google+LINE OAuth / send+verify_email_code / line_complete_email 含 JWT 颁发 + 账号合并)或 **勿碰**(OCR recognize 850 行 / LINE webhook)或**故意留**(/api/version)· **B1 常规长跑到此为止** · 转 ③ auth 专窗口(需 Zihao 在场 · 铁律 #16 登录关键路径)或 ④ C 前端拆 home.js(收益最大)。

---

## 1. 当前行数(2026-05-25 第二十会话末)

| 文件 | 行数 | 验收目标 | 冲刺目标 |
|---|---|---|---|
| app.py | **4459** | < 500 | < 300 |
| db.py | 10663 | < 500 | < 300 |
| home.js | 32466 | < 200 | < 120 |
| home.css | 16131 | < 500 | < 250 |
| home.html | 6533 | < 1000 | < 500 |
| route_helpers.py | 284 | — | — |
| pages_routes.py | 168 | — | 静态页面+公开 meta 12 路由(本会话新建) |
| me_routes.py | 293 | — | /api/me 家族 3 路由 + UserInfo(本会话新建) |
| line_binding_routes.py | 111 | — | LINE 绑定 + 偏好语言 4 路由(本会话新建) |

> 本会话只动后端 · **前端 home.* / db.py 一行没动** · 已有 **28** 个 `*_routes.py`。
> ⚠️ **app.py < 500 的目标无法靠"安全搬家"达成**:剩余 ~3950 行是 login/OAuth/email-code(安全敏感 · 需专窗口)+ OCR recognize 核心(勿碰)+ LINE webhook(勿碰)+ /api/version(故意留)。要继续压 app.py 必须开 auth 专窗口 + OCR 专项重构 · 不是常规长跑能安全推进的。

---

## 2. 本会话(第二十)3 个本地 commit(全绿 · ⚠️ 未 push · 领先 origin/master 3 个 · 0 behind)

| commit | 内容 | app.py 行数变化 |
|---|---|---|
| `d73f21f` | extract pages_routes(12 路由:静态页面 / /login /home /admin /admin/{rest} /reset /terms /privacy + 公开 meta /api/health /api/contact /api/v1/health /api/v1/contact)· /api/version **故意留 app.py** | 4888→4777 |
| (2nd) | extract me_routes(3 路由 /api/me + /api/v1/me + /api/me/profile · 随路由搬 UserInfo + ProfileUpdate + _build_user_info)· ⚠️ 铁律 #15 敏感区 | 4777→4541 |
| (3rd) | extract line_binding_routes(4 路由 /api/line/binding-code + /api/line/binding GET+DELETE + /api/me/lang · 随路由搬 3 model) | 4541→4459 |

**测试**:unit 622 → **634**(+3 新 contract test:pages(4 例)/ me(5 例)/ line_binding(3 例))· imports / i18n(0/0)/ black / ruff(F · 仅 5 个 OCR 区既有 F841)每轮全绿。playwright / node:0 改 JS/UI · 不适用。

**第二十会话踩的坑 / 关键决策(下窗口注意)**:
- **/api/version 不搬**:它读 `PEARNLY_FRONTEND_VERSION` 模块全局(admin_diagnostics_routes lazy `import app` 读)· 且是铁律 #6「每次部署写 4 语 release_notes」的固定编辑锚点。搬走会破坏部署流程 → 留 app.py。pages_routes 契约测试专门断言 /api/version **不在** pages_routes 但仍挂 app。
- **铁律 #15 敏感区(UserInfo/_build_user_info)安全搬法**:① 搬前用脚本核对 app.UserInfo 与 me_routes.UserInfo 的 60 字段 name/type/default 完全一致(IDENTICAL)· ② 契约测试快照 UserInfo 全字段集 + _build_user_info 返回 key 集 · 任何字段漂移当场 fail。`_build_user_info` 唯一 code 消费者是 get_me(其余引用全是注释)· `_calc_trial_days_left`(死代码)/`_ensure_user_profile_columns`(启动 schema)物理夹在 UserInfo 与 _build_user_info 之间但**不搬**。
- **多段 splice**:me 组是 4 段(UserInfo 1250 / _build_user_info 1405 / get_me+profile 1948 / v1_me 3033)· 单次 ReadAllLines + 4 处边界 assert + 拼 5 段。pages 是 4 段(health/contact 分散 + 页面被 /api/version 夹断)。每段都 `chk` 字面量断言 · 0 写坏。
- **black 会把单行 import 拆成多行**:`from pages_routes import (\n    router as pages_router,\n)` —— 下窗口加新 import 时照这个多行格式。
- **push 被 auto-mode 拦**:`git push origin master` 被 auto classifier 拒(默认分支 push 绕过 review · "最高权限"不算具体授权)→ 需 Zihao 显式批准 push。

---

## 3. push 状态:前半已 push+验证 · ⚠️ 后半 3 commit 未 push(下窗口第一件事)

- **前半 5 commit 已 push**(`e3a42bc..9ee3a6d`):categories/erp/admin_users 3 router + docs + 格式修复 · CI 双 job 全绿 · 生产抽查零丢路由(`/api/categories`、`/api/erp/*`、`/api/admin/*` 全 401)· `/api/version` 200(11835078 不变)。
- **⚠️ 后半 3 commit 未 push**(history 组):`b264790`(exception_checks)/`c5af58e`(history_routes 10 路由)/`1835bce`(assign_client 并入 · 11 路由)· **领先 origin/master 3 个 · 0 behind**。
- 下窗口第一件事:`git push origin master`(**会被 auto-mode 拦** · 需 Zihao 授权)· push 后验:`/api/version` 200 + 抽 `/api/history`、`/api/history/{id}/assign_client` 返 401/422(非 404)· CI 看 `gh run list --branch master` 双 job 绿。
- 本窗口后半**未跑生产/CI 验证**(没 push)· 全部本地守门全绿(unit 622)。
- **CI lint 红已清**(`9ee3a6d` · 第十八会话遗留)· 前半 push 时 CI 已验全绿 · 后半纯后端搬家不影响 lint。

---

## 4. 已抽出的 router 全景(25 个 `*_routes.py` + exception_checks.py 服务模块)

| 模块 | 路由数 | 来源会话 |
|---|---|---|
| report / recon / recon_jobs / import / vat_excel / billing / admin_diagnostics | — | 早期 / 阶段 5 |
| notification(6)/ clients(5)/ exceptions(8) | 19 | 第十/十一/十二会话 |
| team(7)/ erp_mappings(12)/ email_ingest(6)/ rd(4)/ settings(5) | 34 | 第十六会话 |
| bank_recon(11)/ admin_migration(7)/ admin_cost(10)/ tenant(6)/ admin_logs(4)/ erp_xero(8) | 46 | 第十七会话 |
| categories(1)/ erp(15)/ admin_users(15) | 31 | 第十九会话前半 |
| **history(11 · 含 assign_client)** + **exception_checks.py(异常检测+LINE 提醒链 · 非 router)** | **11** | **第十九会话后半(本次)** |

**route_helpers.py**(公共 helper · 跨 router 复用):`_require_super_admin` / `_require_owner_or_super` / `_log_op` / `_get_client_ip` / `_check_password_strength` / `_WEAK_PASSWORDS` / `_plan_permissions` / `_tid` / **`_record_500` / `_read_last_500` / `_last_500_event`(第十九会话搬入 · 共享 500 现场状态单例)**。

---

## 5. 下窗口 B1 续拆候选(categories/erp/admin_users + exception_checks/history 本会话已拆 · 见 §2)

> ✅ **history 组已完成**(本会话两步法:exception_checks.py 迁移 → history_routes.py 11 路由)· 纠缠最深的组已啃下。**剩下 app.py 4888 行里的 37 个 @app 路由全是核心耦合区 / 安全敏感区**,B1 阶段都不建议轻拆。逐类评估:

1. **静态 / 页面路由(最干净候选 · ~10 路由)**:`/`、`/login`、`/home`、`/admin`、`/admin/{rest}`、`/reset`、`/terms`、`/privacy`(HTMLResponse 服务)+ `/api/health`、`/api/contact`、`/api/version`。多为读文件/返静态 · 低风险。卡点:`/api/version` 读 `PEARNLY_FRONTEND_VERSION` 模块全局 + release_notes(模块级状态 · 搬走要带状态或留 app)· `/admin` 系列读前端构建。**若下窗口要继续 B1 · 这组最安全 · 但收益小(行数少)**。可抽 `pages_routes.py`。
2. **auth / OAuth 组(安全敏感 · ~9 路由)**:`/api/login`、`/api/auth/google/{start,callback}`、`/api/auth/line/{start,callback}`、`/api/auth/{send,verify}_email_code`。纯搬可行但涉 JWT/session/active_jti/OAuth 重定向/邮箱验证码 · 共享 `create_access_token`/`verify_password`(auth 模块)+ 可能 OAuth 配置全局。**风险中高 · 搬前务必逐路由核对 session/jti/redirect 不变 · 建议 Zihao 在场或专窗口**。
3. **me / line 组(中等耦合)**:`/api/me`、`/api/me/profile`、`/api/me/lang`、`/api/me/needs_email`、`/api/me/line_complete_email`、`/api/line/binding*`、`/api/v1/me`。部分简单(profile/lang)· 但 line_complete_email/needs_email 涉 LINE 绑定流程。
4. **🚫 OCR 核心 + LINE webhook(深耦合 · 勿碰)**:`/api/ocr/recognize`(L2069-2920 · **~850 行巨石**)、`/api/ocr/export*`、`/api/line/webhook`(L4295+)。调 `_async_run_exception_checks`(已在 exception_checks · import)+ `_trigger_auto_push_all`(自动推送 cluster · 在 app.py)+ 计费 + dedup + OCR pipeline · **牵一发动全身 · B1 不拆** · 留专项重构或 C 档前端。

> **建议**:B1 的"易摘果实"已摘完(app.py 10075→4888 · -51%)。下窗口要么做①静态页面(安全但收益小)· 要么转 **C 档前端拆 home.js**(32466 行 · 收益大)· 要么 ②auth 组(需谨慎专窗口)。不建议在常规长跑里碰 ④OCR 核心。

---

## 6. 本会话验证过的安全范式(下窗口照抄)

**抽 router 步骤**:
1. grep 目标路由组 + 它用的 helper / model / 是否被组外引用(确认自包含 · 重点查 helper 是否被留 app.py 的路由共用 → 是就先搬 route_helpers)。
2. 新建 `xxx_routes.py`:`from __future__ import annotations` · `router = APIRouter()` · `from auth import get_current_user_from_request` · `from route_helpers import ...` · 组专属 helper/model 整体搬入。
3. 路由体**逐字复制** · 只把 `@app.` → `@router.`。**大组(>200 行)用字节级 PowerShell 提取**:`$lines = ReadAllLines; $block = $lines[a..b] | %{ $_ -replace '^@app\.','@router.' }; 拼 header + block 写出`(本会话 erp_xero 411 行就这么干 · 避免手抄出错)。先 `python -c "import ast; ast.parse(...)"` + `import xxx_routes` 自测编译。
4. app.py 加 `from xxx_routes import router as xxx_router`(+ 共享 helper/model import 回来)+ `app.include_router(xxx_router)`。
5. **删 app.py 旧块**:字节级 splice 保 LF —
   ```powershell
   $lines = [System.IO.File]::ReadAllLines("app.py")
   # 边界 assert(top/end/tail 各校验一行字面量 · 0-indexed = grep行号-1)
   $out = $head + $marker + $tail
   $enc = New-Object System.Text.UTF8Encoding($false)
   [System.IO.File]::WriteAllText((Resolve-Path "app.py"), ($out -join "`n") + "`n", $enc)
   ```
   删完 grep 确认 `@app.*("/api/xxx` 残留=0 · helper def 残留=0。
6. 写 `tests/unit/test_xxx_routes_contract.py`:路由 path+method 集合 == 期望 · `app.app.routes` 含路由 · helper 单一来源 `assertIs(xxx._helper, route_helpers._helper)` · model 字段契约。
7. 守门:`black <files>` → `ruff check <files>`(删块后常有孤儿 import F401 · 删掉)→ `check_imports --quiet` → `check_i18n --strict` → `unittest discover -s tests/unit`。
8. commit(**用 `-F _commitmsg.txt` 文件传 message** · 写完 `rm`)· message 带 `· REFACTOR-B1`。

**本会话踩的坑(下窗口注意)**:
- **共享 helper 反咬**:搬走某组后 · 它用的 helper 可能在 app.py 变成 unused → ruff F401。本会话 `_require_owner_or_super` 最后消费者随 xero 搬走 · app.py 去掉 import · 但 `test_route_helpers_contract` 有 `assertIs(app._require_owner_or_super, ...)` 断言挂了 → 把断言**跟到新消费者**(erp_xero_routes)。删 helper import 前先 grep 该 helper 是否还有 app.py 消费者 + 是否有 contract test 断言 app.X。
- **model 被组外复用**:tenant 的 `AdminUpdateTenantQuota/Status` 被 admin user 路由(留 app.py)复用 → model 留 tenant_routes · app.py import 回去。搬 model 前 grep 它在 app.py 剩余引用。
- **路由被夹断**:tenant 组被 history 的 assign_client 夹在中间 → 两段 splice(读一次数组 · 拼 segA+marker1+segB+marker2+segC)· 注意 0-indexed = grep行号-1(本会话有一次 assert literal 写错索引 · assert 当场拦下 · 没写坏文件)。
- **CSV BOM**:`"﻿"` 与字面 BOM `"﻿"` 是同一 Python 字符串 · 不影响行为 · 不用纠结。

---

## 7. 红线 / 停止条件(本会话遵守的)

- 不 push(本会话自主长跑指示)· 不 force-push · 不动 db.py schema · 不动前端 home.*(留 Zihao 在场)· 不动 git-deploy/webhook。
- 触发停止:上下文 ~80% / 不可抗阻碍 / 测试失败短时不可修 / 需改架构·部署·DB·付费·生产密钥 / 单轮 diff >30 文件 / 无法判断是否改变业务行为 / 连续 8-10 commit 且上下文不足以安全开下一组。
- 第十七会话停止原因:见 git 历史。
- **第十九会话(本次)停止原因**:前半 3 router(categories/erp/admin_users)+ 后半 history 组完成(exception_checks 迁移 → history_routes 11 路由)· 共 6 模块 · app.py 10075→4888(-51%)。**最深纠缠的 history 组已啃下**;剩余 37 个 @app 路由全是核心耦合区(OCR recognize 850 行巨石 / LINE webhook)或安全敏感区(auth/OAuth · 见 §5)· 上下文消耗可观 · 按「易摘果实已摘完 · 不在预算偏紧时硬开核心耦合/安全敏感区 · 不留半拆 app.py」主动收尾 · **非测试失败 · 非阻碍 · 非红线**。

---

## 8. 检查记录(诚实 · 第十九会话)

- **black / ruff(F)/ check_imports / check_i18n(0/0)/ unit 622**:每个 commit 全绿 · 会话末完整 gate 全绿(unit 597→622)。
- **offload 守门**:`test_erp_test_connection_route_dispatch.py` 33 passed(erp 搬家后 patch 目标改 erp_routes · async tripwire 未破坏)。
- **history 步骤 A/B 守门**:exception_checks 单一来源测试 + history 11 路由契约测试全绿 · history PUT 重跑规则链(_async_run_exception_checks)单一来源跟到 exception_checks。
- **playwright / node --check**:本会话 0 改 JS / 0 改 UI(纯后端搬家)· 不适用 · 未跑。
- **生产 / CI**:前半已 push + 部署 + CI 双 job 全绿 + 零丢路由验证;**后半 history 3 commit 未 push · 无生产/CI 验证**(下窗口 push 后补)。
- **git**:领先 origin/master **3** 个 commit(`b264790`/`c5af58e`/`1835bce`)· 0 behind · 工作区只剩既有未跟踪 probes/ 等 + 别的窗口的 `.claude/settings.local.json`、`CLAUDE.md/CLAUDE.md`(非本会话 · 别误提交)。
- **app.py**:7275 → 4888(本窗口 -2387 · 含前半 -1745 + 后半 history -642)· CRLF=0(每次 splice 后校验)。
