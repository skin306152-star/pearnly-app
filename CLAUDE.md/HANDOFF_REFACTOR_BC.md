# 🤝 HANDOFF · Pearnly 整顿 B-C 阶段长跑

> 单一权威源:`CLAUDE.md/REFACTOR_MASTER_PLAN.md`(进度看板 + B1 行)。本文件 = B-C 长跑接力专用速查。
> **最后更新**:2026-05-25(第十九会话 · B1 续 · 抽 categories + erp + admin_users 3 router)

---

## 0. 一句话现状

整顿期 · 在做 **REFACTOR-B1**(拆 `app.py` 巨石 router → 独立 `*_routes.py`)。
**第十九会话(本次)抽了 3 个 router**(categories / erp / admin_users)+ 把 `_record_500` 三件套搬到 route_helpers · **app.py 7275 → 5530 行(-1745)** · **✅ 已 push + CI 双 job 全绿 + 生产抽查零丢路由**(`af9a2f4`/`c81f609`/`eadc121`)· 另修了第十八会话遗留的 CI lint 红(`9ee3a6d` · black 7 文件 + 2 F401)· origin/master 与 HEAD 同步 0/0。
**下窗口**:回归 §5 拆 **history 组**(唯一剩的大组 · 纠缠最深 · 需先把 `_async_run_exception_checks` 整条链搬到共享模块 · 分两步)· 或拆 `assign_client` 单路由(干净但薄)。开工前 baseline:`git status` 干净 + `origin/master...HEAD` = 0 0。

---

## 1. 当前行数(2026-05-25 第十九会话末)

| 文件 | 行数 | 验收目标 | 冲刺目标 |
|---|---|---|---|
| app.py | **5530** | < 500 | < 300 |
| db.py | 10661 | < 500 | < 300 |
| home.js | 32466 | < 200 | < 120 |
| home.css | 16131 | < 500 | < 250 |
| home.html | 6533 | < 1000 | < 500 |
| route_helpers.py | 284 | — | — |

> 本会话只动后端(app.py / route_helpers / 3 新 router 模块 + 2 新 contract test + 改 4 个既有 test)· **前端 home.* / db.py 一行没动**(home.js/html 行数变化是别的窗口的)。
> 已有 **24** 个 `*_routes.py`。

---

## 2. 本会话(第十九)3 个本地 commit(全绿 · ⚠️ 未 push · 领先 origin/master 3 个 · 0 behind)

| commit | 内容 | app.py 行数变化 |
|---|---|---|
| `af9a2f4` | extract categories_routes(1 路由 `/api/categories` · 用 `_tid`) | 7275→7271 |
| `c81f609` | extract erp_routes(15 路由 endpoints/test-connection/customers/products/push/logs/retry/batch + `_check_push_access` + 6 model + 3 TTL 缓存)· `_record_500/_read_last_500/_last_500_event` 搬到 route_helpers(共享状态单一来源) | 7271→6164 |
| `eadc121` | extract admin_users_routes(15 路由 admin users/employees + 4 model + CascadeDeleteRequest) | 6164→5530 |

**测试**:unit 597 → **612**(+2 新 contract test:erp / admin_users · 各 7/5 例 · 改 4 个既有 test:offload + route_helpers + team + tenant + admin_logs 的单一来源断言跟到新消费者)· imports / i18n(0/0)/ black / ruff(F)每轮全绿。

**第十九会话踩的坑(下窗口注意)**:
- **erp 的 `_record_500`**:被 app.py 全局异常处理器 + erp 路由 + admin_diagnostics 三方共享(含 mutable `_last_500_event` 状态)→ 必须搬 route_helpers 做单一来源 · 不能各持副本(否则诊断读不到 erp 写的 500)。
- **erp 自动推送 cluster**(`_auto_push_history`/`_auto_push_xero_for_history`/`_trigger_auto_push_all`):被留守 app.py 的 OCR 路由调用 · 是非路由的后台 helper · 物理夹在 erp 路由中间 → **两段 splice 绕开它** · `import erp_push as _erp` 保留给它。
- **erp 3 个 TTL 缓存**(test/customers/products):随路由搬走后 · app.py 启动 flush 裸名失效 → 加 `erp_routes.flush_test_connection_caches()` 封装 · app.py 调它。
- **offload 测试**(`test_erp_test_connection_route_dispatch.py`):patch 目标 `app.X` → `erp_routes.X`(`_check_push_access` ×17 + `get_current_user_from_request` ×17)· 但 `app._erp.*` / `app.db.*` patch **不用改**(共享模块单例)。
- **删 app.py import 前查 contract 断言**:admin 组搬走后 app.py 不再用 `_require_super_admin`/`_log_op`/`EmployeeToggleRequest`/`AdminUpdateTenant*` → ruff F401 · 但 route_helpers/team/tenant 三个 contract test 有 `assertIs(app.X, ...)` → 删 import 前把断言**跟到新消费者** `admin_users_routes`。

---

## 3. ✅ 本会话已 push + CI 全绿 + 生产验证(下窗口无需补 push)

- 本会话 5 个 commit 全已 push(`e3a42bc..9ee3a6d`):3 router(`af9a2f4`/`c81f609`/`eadc121`)+ docs(`8ef6779`)+ 格式修复(`9ee3a6d`)· `origin/master` 与 HEAD 同步 `0/0`。
- **CI 双 job 全绿**(run 26390… 之后的格式 push run):✓ lint(black+ruff+prettier+eslint · 58s)✓ test(import+i18n+unit+vite+e2e · 2m49s)。
- **生产验证**:`/api/version` 200(版本 11835078 不变 · 纯后端重构无 cache_bust)· 抽查 `/api/categories`、`/api/erp/{endpoints,logs}`、`/api/admin/{users,employees,users.csv}` 全返 401(非 404/500)= 零丢路由。
- **CI lint 红已清**:第十八会话 recon/salesvat 修复漏跑 black → CI lint 自那时一直红 · 本会话 `9ee3a6d` black 格式化 7 文件 + ruff --fix 2 个 F401 修复(纯格式化)· 下窗口 baseline CI 应是绿的。

---

## 4. 已抽出的 router 全景(20 个 `*_routes.py`)

| 模块 | 路由数 | 来源会话 |
|---|---|---|
| report / recon / recon_jobs / import / vat_excel / billing / admin_diagnostics | — | 早期 / 阶段 5 |
| notification(6)/ clients(5)/ exceptions(8) | 19 | 第十/十一/十二会话 |
| team(7)/ erp_mappings(12)/ email_ingest(6)/ rd(4)/ settings(5) | 34 | 第十六会话 |
| bank_recon(11)/ admin_migration(7)/ admin_cost(10)/ tenant(6)/ admin_logs(4)/ erp_xero(8) | 46 | 第十七会话 |
| **categories(1)/ erp(15)/ admin_users(15)** | **31** | **第十九会话(本次)** |

**route_helpers.py**(公共 helper · 跨 router 复用):`_require_super_admin` / `_require_owner_or_super` / `_log_op` / `_get_client_ip` / `_check_password_strength` / `_WEAK_PASSWORDS` / `_plan_permissions` / `_tid` / **`_record_500` / `_read_last_500` / `_last_500_event`(第十九会话搬入 · 共享 500 现场状态单例)**。

---

## 5. 下窗口 B1 续拆候选(categories / erp / admin_users 本会话已拆 · 见 §2)

> ⚠️ 边界清晰的组基本拆完。**剩下主要就 history 一个大组 · 它是全项目纠缠最深的**(共享 `_async_run_exception_checks`)· 拆它前必须先做一次「共享 helper 链迁移」子工程。建议给它**整个新窗口的预算**(像第十九会话拆 erp 那样,先迁移再拆路由),不要在上下文不足时硬开。

1. **history(7 路由 `/api/history*` + `/api/v1/history*`)· 纠缠最深 · 需先迁移 exception-check 链**:
   - **卡点**:`_async_run_exception_checks`(app.py ~L3153 · 170 行)被 history PUT 路由(~L3594)**和** 4 处留守 app.py 的 OCR/LINE upload 路由(L2222/2779/5208/5338)共用。它依赖 `_notify_exception_high` / `_notify_large_invoice` / `EXC_RULE_*` 5 个常量 / 可能还有 `_parse_money` / `_is_valid_thai_tax_id`(L3167/3180 区)。
   - `_check_history_access`(用 `_plan_permissions` · 已在 route_helpers · 干净)只被 history 用 · 可随组走。
   - **推荐做法(分两步 · 仿第十九会话 erp 的 `_record_500` 迁移)**:
     - 步骤 A:先把 `_async_run_exception_checks` 整条依赖链(含 `_notify_*` + `EXC_RULE_*` 常量 + `_parse_money`/`_is_valid_thai_tax_id` 如被共用)搬到 `services/exceptions/` 或 route_helpers · app.py 的 4 处 OCR 调用点 + history PUT 都 import 同一份(单一来源 · 保留共享行为)· 单独 commit + 守门全绿。
     - 步骤 B:再抽 history 7 路由到 `history_routes.py`(届时 `_async_run_exception_checks` 已可 import · `_check_history_access` 随组走)。
   - 若步骤 A 评估下来牵出太多(`_notify_*` 又依赖别的)· 按「纠缠太深跳过」处理 · 别硬拆。
2. **assign_client(单路由 `/api/history/{history_id}/assign_client` · app.py ~L5430)**:用 `_tid`(route_helpers)+ `db.learn_buyer_to_client` · **完全自包含**(`test_tenant_routes_contract.test_assign_client_stays_in_app` 锁它在 app.py)· 干净但单路由偏薄 · 可单独抽 `history_routes.py` 起头(然后 history 主组随后并入)· 搬时更新该 contract 断言。
3. **其它**:app.py 5530 行里除上面两组 · 剩下多是 auth/login/oauth/line-webhook/ocr-recognize/version/static 等**核心耦合区**(OCR recognize 调 `_async_run_exception_checks` + `_trigger_auto_push_all` + 计费 · 牵一发动全身)· B1 阶段不建议碰 · 留后续阶段或 home.js 前端拆(C 档)。

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
- **第十九会话(本次)停止原因**:3 个干净 slice(categories/erp/admin_users)后 · 唯一剩的大组 history 纠缠最深(需先做 `_async_run_exception_checks` 整条链迁移子工程 · 见 §5)· 本窗口已做大量分析 + 3 次提取(含 erp 共享状态迁移 + admin 5 个 contract 更新)· 上下文消耗可观 · 按「上下文不足不硬开下一大组 · 不留半拆 app.py」主动收尾 · **非测试失败 · 非阻碍 · 非红线**。

---

## 8. 检查记录(诚实 · 第十九会话)

- **black / ruff(F)/ check_imports / check_i18n(0/0)/ unit 612**:每个 commit 全绿 · 会话末完整 gate 全绿(unit 597→612)。
- **offload 守门**:`test_erp_test_connection_route_dispatch.py` 33 passed(erp 路由搬家后 patch 目标改 erp_routes · async tripwire/to_thread 未破坏)。
- **playwright / node --check**:本会话 0 改 JS / 0 改 UI(纯后端 router 搬家)· 不适用 · 未跑。
- **生产 / CI**:✅ 已 push + 部署 · **CI 双 job 全绿**(lint 58s + test 2m49s)· `/api/version` 200 · 搬出路由抽查全 401(零丢路由)。
- **CI lint 红已清**:`9ee3a6d` black 7 文件 + ruff --fix 2 个 F401(第十八会话 recon/salesvat 漏跑 black 的遗留)· 修后全仓 `black --check .` 干净(206 files)。
- **git**:`origin/master` 与 HEAD 同步 `0/0` · 工作区只剩既有未跟踪 probes/ 等 + 别的窗口的 `.claude/settings.local.json`、`CLAUDE.md/CLAUDE.md`(非本会话 · 别误提交)。
- **app.py**:7275 → 5530(-1745)· CRLF=0(每次 splice 后校验)。
