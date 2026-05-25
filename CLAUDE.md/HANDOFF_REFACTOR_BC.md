# 🤝 HANDOFF · Pearnly 整顿 B-C 阶段长跑

> 单一权威源:`CLAUDE.md/REFACTOR_MASTER_PLAN.md`(进度看板 + B1 行)。本文件 = B-C 长跑接力专用速查。
> **最后更新**:2026-05-25(**第二十三会话** · B2 db.py→services 续抽 9 域:archive/rd/cost/exceptions/clients/billing/vat_recon〔P0-VAT 三表组〕/audit〔操作日志〕/team〔员工管理〕· db.py 7136→4513 · 4 批 push+CI 绿+生产 401 验证)
> **⛔ 下窗口先做 BUG 整改(Zihao 拍板 BUG > 整改 · 会发 BUG 问题)· 修完再回 B2 续抽。**

> **✅ 第二十一会话(全 push + CI 绿 + 生产验证 · 工作区干净)**:
> - **D1**(`d65b692`):补 4 个 router 契约测试(report/vat_excel/recon/admin_diagnostics)· +16 unit。
> - **C1**(`0377055`):测试中心 IIFE → `src/home/test-center.js`(skin only)· home.js 22703→**22210**。**安全 bump 策略**:只 bump main.js?v= 不动 home.js?v=(/api/version 不变 · 不弹横幅)· 生产 playwright 验证渲染 0 报错。
> - **OCR 重构收尾**(`1eadc16`):上一会话遗留的 OCR 入口 helper 抽到 `services/ocr/entrypoints.py`(8 函数 · 171 行)已提交上线 · 生产 OCR 路由返 422(非 500)。⚠️ 未跑真额度 E2E · 建议真账号传发票冒烟计费。
> - **清理**:scratch(probes/ _deploy_nginx/ _test_reports/ recon-i18n md)+ `.claude/settings.local.json` 入 .gitignore(后者 git rm --cached · 本地保留)· 工作区无尾巴。
> - **admin-cost 抽迁尝试并回退**(load-order 纠缠:billing IIFE 装饰 + DOMContentLoaded 直绑)· 教训:多数 home.js 块有装饰器/裸名/inline onclick 纠缠 · 抽前必查引用。
>
> **下窗口**:app.py 已干净(OCR WIP 上线)· 全体用户 home.js 块现可正经抽(bump home.js?v= + 4 语 release_notes + 浏览器验证 · 抽前查装饰器纠缠 · 碰付费 UI 建议 Zihao 在场)· 或走无需 app.py 的 C2 home.css(不弹横幅)/ B2 db.py / D 测试(E2E 1/10)。



---

## 0. 一句话现状

整顿期 · B1(拆 app.py)**易摘果实已全部摘完** · 本会话末**启动 C1**(拆 home.js)。全部已 push + CI 绿 + 生产验证。

**第二十会话 · B1 收尾(app.py 4888 → 4459 · -429 · 已 push+验证)**:
- `d73f21f` **pages_routes.py**(12):静态页面 / /login /home /admin /admin/{rest} /reset /terms /privacy + /api/health /api/contact /api/v1/{health,contact}。**/api/version 故意留 app.py**(铁律 #6 锚点 + PEARNLY_FRONTEND_VERSION 全局)。
- `4ab85a5` **me_routes.py**(3 + UserInfo + ProfileUpdate + _build_user_info):/api/me · /api/v1/me · /api/me/profile。⚠️ 铁律 #15 敏感区 · verbatim · 契约测试快照 UserInfo 60 字段。
- `54ce2c1` **line_binding_routes.py**(4 + 3 model):/api/line/binding-code · /api/line/binding(GET+DELETE)· /api/me/lang。
- 生产验证:/api/me 401、/api/line/binding 401、/(根) 200、/api/version 200 —— 零丢路由。

**第二十会话 · C1 第一刀(home.js 32466 → 22703 · -9763 · 已 push+CI 绿+生产 playwright 验证)**:
- `ed6cfa8` I18N 4 语字典(占 home.js 30%)→ `static/i18n-data.js`(`window.I18N` · git-tracked static · webhook `git reset --hard` 后即服务)。home.html 在 home.js **前** sync 加 `<script src="/static/i18n-data.js?v=11835078">`;home.js L145 改 `const I18N = window.I18N;`。**不 bump cache_bust**(home.html no-cache · 新旧 home.js 都有 window.I18N 兜底 · 无破坏态 · 不弹版本横幅)。配套改 check_i18n.py + test_i18n_completeness + test_brv2_anchor_audit_static 读新文件。
- `3a11f81` i18n-data.js 加入 prettier + eslint 豁免(跟 home.js 同策略 · verbatim 数据带既有 40 个 dupe-key 债 · 不在抽家阶段动数据)。
- **生产 playwright 验证**:/home(预置 dummy token 抑制跳转)`window.I18N` 4 语齐 + `t('ocr-title')`→泰文『อัปโหลดและอ่าน』· 翻译端到端正常。

**下窗口(C1 续)**:home.js 现 **22703 行**(主应用代码 ~22500 + 顶部错误拦截 IIFE)。比 i18n 难——home.js 是 **sync 巨石** · 124 个 `window.X` 全局暴露 · 抽 ES module 受 **load-order 约束**(home.js sync 先跑 → Vite bundle defer 后跑;能抽的是"home.js 之后才需执行"或"靠 window 全局通信"的块)。建议:抽 **cohesive feature 函数群**(如某 page 的 render 集)→ `src/home/*` ES module(side-effect import 进 src/main.js · 用 window 全局)· 仿 dashboard.js/billing.js 范式 · 每块 **prettier+eslint 强制**(非 i18n 数据 · 不豁免)· 每块浏览器验证。**B1 已到顶**(剩 auth 安全敏感 / OCR·webhook 勿碰 / /api/version 故意留)。

---

## 1. 当前行数(2026-05-25 第二十一会话末)

| 文件 | 行数 | 验收目标 | 冲刺目标 |
|---|---|---|---|
| app.py | **4464** | < 500 | < 300 |
| db.py | **4513** | < 500 | < 300（B2 抽 18 域 DAL→services · 10663→4513 · -6150）|
| home.js | **22210** | < 200 | < 120 |
| static/i18n-data.js | 9772 | — | 4 语 i18n 数据(window.I18N · prettier/eslint 豁免) |
| src/home/test-center.js | 706 | — | 第二十一会话从 home.js 抽出(测试中心 · skin only · ES module) |
| services/ocr/entrypoints.py | 171 | — | 第二十一会话 OCR 入口 helper(B2 风格 · web/LINE/email 共用) |
| home.css | 16131 | < 500 | < 250 |
| home.html | 6536 | < 1000 | < 500 |

> 已有 **30** 个 `*_routes.py` · `src/home/` 3 模块(dashboard/billing/test-center)· `services/ocr/entrypoints.py` · home.js 32466→**22210**(C1:i18n -9763 + 测试中心 -493)。
> ⚠️ **C1 续拆"只 bump main.js?v="安全模式(第二十一会话验证)**:抽 home.js 可执行块本需 bump home.js?v= 逐出旧缓存,但 home.js?v= 驱动 /api/version → 弹横幅 → 要改 app.py release_notes。若该块抽出后"老 home.js 内联版 + 新 bundle 版"经 window 入口覆盖(后跑赢)且 load-time 副作用幂等(setInterval/subscribeI18n 等)→ 双跑无害 → **可只 bump main.js?v= 不动 home.js?v=**(交付新 bundle · 老缓存用户行为不变 · 新用户拿瘦身 home.js)。**前提**:该块经 `window.X` 入口被调用(非 home.js 内裸名调)· 且 load-time 无非幂等副作用(无重复事件直绑同一 DOM)· 且无其他代码装饰该 window.X(admin-cost 因 billing IIFE 装饰被否)。测试中心满足(且 skin only 零付费影响)。**对全体用户、有直绑事件/被装饰的块不适用 · 必须 bump home.js?v= + release_notes(改 app.py)**。
> ⚠️ **app.py < 500 无法靠"安全搬家"达成**:剩 ~3950 行是 login/OAuth/email-code(安全敏感 · 需专窗口)+ OCR recognize 核心(勿碰)+ LINE webhook(勿碰)+ /api/version(故意留)。
> ✅ **OCR helper 抽迁已完成**(`1eadc16` · `services/ocr/entrypoints.py`)· app.py/email_ingest 不再内联那批 OCR 入口逻辑 · 工作区已无遗留未提交改动。

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
