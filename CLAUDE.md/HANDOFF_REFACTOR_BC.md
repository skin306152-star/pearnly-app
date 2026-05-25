# 🤝 HANDOFF · Pearnly 整顿 B-C 阶段长跑

> 单一权威源:`CLAUDE.md/REFACTOR_MASTER_PLAN.md`(进度看板 + B1 行)。本文件 = B-C 长跑接力专用速查。
> **最后更新**:2026-05-25(第十八会话 · 修复插曲收尾 · 下窗口回归 B1)

---

## 0. 一句话现状

整顿期 · 在做 **REFACTOR-B1**(拆 `app.py` 巨石 router → 独立 `*_routes.py`)。
第十七会话抽了 6 个 router + 搬了 1 个 helper(`_tid`)· **app.py 8589 → 7263 行(-1326)** · **7 个 commit 全绿 · ✅ 已 push**(`faaa536..569b534` + docs `aa2e6e3`,origin/master 与 HEAD 同步)。
**第十八会话是修复插曲**(codex 报告驱动的 3 批生产回归修复 · 见 STATE 头部)· **未动 app.py 拆分进度** · 下窗口直接回 §5 续拆纠缠组。

---

## 1. 当前行数(2026-05-25 第十七会话末)

| 文件 | 行数 | 验收目标 | 冲刺目标 |
|---|---|---|---|
| app.py | **7263** | < 500 | < 300 |
| db.py | 10620 | < 500 | < 300 |
| home.js | 33867 | < 200 | < 120 |
| home.css | 16131 | < 500 | < 250 |
| home.html | 6726 | < 1000 | < 500 |

> 本会话只动后端(app.py / route_helpers / 6 新 router 模块 + 6 contract test + 改 1 个 test)· **前端 home.* / db.py 一行没动**。

---

## 2. 本会话 7 个本地 commit(全绿 · ⚠️ 未 push · 领先 origin/master 7 个)

| commit | 内容 | app.py 行数变化 |
|---|---|---|
| `faaa536` | extract bank_recon_routes(11 路由 `/api/bank-recon/*`) | 8589→8321 |
| `b33dd58` | extract admin_migration_routes(7 路由 `/api/admin/{migration,rls}/*`) | 8321→8246 |
| `13eded7` | extract admin_cost_routes(10 路由 `/api/admin/{cost,credits,monitoring}/*`) | 8246→7997 |
| `fac5f62` | extract tenant_routes(6 路由 `/api/admin/tenants/*` + `/api/me/tenant-usage` + 3 model) | 7997→7865 |
| `574c92d` | extract admin_logs_routes(4 路由 操作/审计日志) | 7865→7674 |
| `4755af7` | move `_tid` → route_helpers(解锁 categories/connectors/xero) | 7674→7666 |
| `569b534` | extract erp_xero_routes(8 路由 connectors/status + xero/* + `_ensure_fresh_xero_token`) | 7666→7263 |

**测试**:unit 552 → **580**(每 router 一个 contract test · +_tid single-source test · 改 1 个 route_helpers contract)· imports / i18n(0/0)/ black / ruff(F)每轮全绿。

---

## 3. ✅ B1 已 push + 已生产验证(第十八会话修复插曲一并部署)

- 第十七会话 7 个 commit(`faaa536..569b534`)+ docs `aa2e6e3` **已 push origin/master**(随第十八会话修复部署一并上线 · `origin/master` 与 HEAD 同步 `0/0`)。
- 其上又叠了第十八会话 3 批修复 commit(`672f748`/`0daebf6`/`eb87429`/`15241bd`/`575767f`)· 全已 push + 部署(版本 11835078)。
- **下窗口第一件事不再是 push** · 而是回 §5 续拆 B1 纠缠组(history / erp-push / admin-users)· 开工前 baseline:`git status` 干净 + `git rev-list --left-right --count origin/master...HEAD` 应为 `0 0`。
- B1 搬出的路由生产验证:`/api/version` 200 · 抽搬出路由确认 401/422(非 404)= 零丢路由(第十六会话已验范式 · 第十七组同范式)。

---

## 4. 已抽出的 router 全景(20 个 `*_routes.py`)

| 模块 | 路由数 | 来源会话 |
|---|---|---|
| report / recon / recon_jobs / import / vat_excel / billing / admin_diagnostics | — | 早期 / 阶段 5 |
| notification(6)/ clients(5)/ exceptions(8) | 19 | 第十/十一/十二会话 |
| team(7)/ erp_mappings(12)/ email_ingest(6)/ rd(4)/ settings(5) | 34 | 第十六会话 |
| **bank_recon(11)/ admin_migration(7)/ admin_cost(10)/ tenant(6)/ admin_logs(4)/ erp_xero(8)** | **46** | **第十七会话(本次)** |

**route_helpers.py**(公共 helper · 跨 router 复用):`_require_super_admin` / `_require_owner_or_super` / `_log_op` / `_get_client_ip` / `_check_password_strength` / `_WEAK_PASSWORDS` / `_plan_permissions` / **`_tid`(本会话新搬入)**。

---

## 5. 下窗口 B1 续拆候选(全部较纠缠 · 先评估共享 helper)

> ⚠️ 本会话把所有「边界清晰 · 自包含」的组都拆完了。剩下的组都有共享 helper 纠缠 · 不能直接 splice · 必须先把共享 helper 搬到 route_helpers(像本会话的 `_tid`)· 再拆路由。

1. **history(7 路由 `/api/history*` + `/api/v1/history*` + `/api/history/{id}/assign_client`)**:
   - 卡点:`_async_run_exception_checks`(app.py ~L3154 · 170 行)被 history PUT 路由**和** upload/OCR 路由(L2223/2780/6553/6683 等 · 留 app.py)共用。它依赖 `_notify_exception_high` / `_notify_large_invoice` / `EXC_RULE_*` 常量 / `_parse_money` / `_is_valid_thai_tax_id`。
   - `_check_history_access`(用 `_plan_permissions` · 现已在 route_helpers · 干净)只被 history 用 · 可随组走。
   - assign_client 用 `_tid`(已在 route_helpers)+ `db.learn_buyer_to_client` · 自包含 · 可随 history 走。
   - **建议**:要么把 `_async_run_exception_checks` 整条依赖链(含 `_notify_*` + EXC_RULE 常量)搬到一个 `services/exceptions/` 或 route_helpers · 要么 history 这组**先跳过**(纠缠最深)。
2. **`/api/erp/*` endpoints/test-connection/customers/products/push/logs**(~15 路由 · L3781-4836 + retry/batch 在 L4862+):
   - 卡点:`_check_push_access`(app.py ~L3733)被这一大片共用 · 先搬 route_helpers。
   - ⚠️ **铁律 #10**:test-connection / customers / products / push 是 async 路由调 sync Playwright(MRERPAdapter)· 必须保留 `await asyncio.to_thread` + AsyncLoopOffloadTests(`test_erp_test_connection_route_dispatch.py`)。搬家别破坏 offload。
   - app.py 还有 Xero 自动推送后台函数(用 `_ensure_fresh_xero_token` · 已 import from erp_xero_routes)在这片附近 · 别误搬。
3. **`/api/admin/users` + `/api/admin/employees` 大组**(~14 路由 · L6618-7374):
   - 卡点:用 `_user_by_id`?(其实多是 db 方法)+ models(AdminCreateUserRequest/AdminVerifyPasswordRequest/AdminDeleteUserRequest/AdminResetPasswordRequest · L6722+)+ `AdminUpdateTenantQuota/Status`(已在 tenant_routes · import)+ EmployeeToggleRequest(已在 team_routes · import)+ `_require_super_admin`/`_log_op`/`_get_client_ip`(route_helpers)。
   - **孤立 users.csv**:`/api/admin/users.csv`(本会话特意留 app.py · 待这组拆时一并搬)· contract test 锁了它仍在 app.py · 搬时更新 `test_admin_logs_routes_contract.test_users_csv_stays_in_app`。
   - 量大 · 建议拆成 admin_users_routes + admin_employees_routes 两个。
4. **categories(1 路由 `/api/categories`)**:只用 `_tid`(已在 route_helpers)+ db · 现在完全自包含 · 可随便找个 misc 模块塞 · 但单路由偏薄。

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
- 本会话**停止原因**:7 个干净 slice 后 · 剩余组(history/erp-push/admin-users)都纠缠较深(需先搬 `_async_run_exception_checks`/`_check_push_access`/多 helper)· 按「安全第一 · 纠缠太深跳过 · 上下文不足不硬开下一组」主动收尾 · **非测试失败 · 非阻碍 · 非红线**。

---

## 8. 检查记录(诚实)

- **black / ruff(F)/ check_imports / check_i18n(0/0)/ unit 580**:每个 commit 全绿 · 会话末跑了一次完整 consolidated gate(全 *_routes.py + route_helpers + app.py · 全绿)。
- **playwright / node --check**:本会话 0 改 JS / 0 改 UI(纯后端 router 搬家)· 不适用 · 未跑。
- **生产 / CI**:本会话**未 push · 未部署** · 无生产/CI 验证(下窗口 push 后补)。
- **git**:领先 origin/master 7 个 commit · 0 behind · 工作区只有这 7 个 commit 的内容 + 既有未跟踪 probes/ 等(非本会话产生)。
