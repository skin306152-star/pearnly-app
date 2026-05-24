# 🤝 HANDOFF · Pearnly 整顿 B-C 阶段长跑

> 单一权威源:`CLAUDE.md/REFACTOR_MASTER_PLAN.md`(进度看板 + B1 行)。本文件 = B-C 长跑接力专用速查。
> **最后更新**:2026-05-25(第十六会话收尾)

---

## 0. 一句话现状

整顿期 · 在做 **REFACTOR-B1**(拆 `app.py` 巨石 router → 独立 `*_routes.py`)。
第十六会话抽了 5 个 router + 搬了 1 个 helper · **app.py 9350 → 8589 行(-761)** · **6 个 commit 全绿但全留本地未 push**(Zihao 指示)。

---

## 1. 当前行数(2026-05-25 会话末)

| 文件 | 行数 | 验收目标 | 冲刺目标 |
|---|---|---|---|
| app.py | **8589** | < 500 | < 300 |
| db.py | 10620 | < 500 | < 300 |
| home.js | 33867 | < 200 | < 120 |
| home.css | 16131 | < 500 | < 250 |
| home.html | 6726 | < 1000 | < 500 |

> 本会话只动后端(app.py / route_helpers / 5 新 router 模块 + 5 contract test + 改 1 个 test)· **前端 home.* / db.py 一行没动**。

---

## 2. 本会话 6 个本地 commit(全绿 · ⚠️ 未 push · 在 master 本地领先 origin/master 6 个)

| commit | 内容 | app.py 行数变化 |
|---|---|---|
| `b95372d` | extract team_routes(7 路由 `/api/team/employees*`) | 9350→9113 |
| `0e17fa4` | extract erp_mappings_routes(12 路由 `/api/erp/mappings/*`) | 9113→8922 |
| `8358b72` | extract email_ingest_routes(6 路由 `/api/email-ingest/*`) | 8922→8781 |
| `870290c` | move `_plan_permissions` → route_helpers(解锁 rd/archive/history) | 8781→8748 |
| `8fa55f7` | extract rd_routes(4 路由 `/api/(v1/)rd/*`) | 8748→8683 |
| `7686259` | extract settings_routes(5 路由 archive+dup-check) | 8683→8589 |

**测试**:unit 530 → **552**(每 router 一个 contract test · +新 PlanPermissions test)· imports / i18n(0/0)/ black / ruff(F)每轮全绿。

---

## 3. ⚠️ 第一件事:决定这 6 个本地 commit 怎么办

- 本会话 Zihao 指示「本地 commit · 不 push · 不因 push 权限弹窗停下」。
- 这 6 个 commit **未经生产验证**(没 push → 没部署 → 没 curl /api/version)。
- 但每轮跑过 `scripts/check_imports.py`(= 真 import app · 验证新 import 结构能加载)· 路由搬家最大风险(启动期 import 失败)已覆盖。纯后端搬家 · 0 业务逻辑改 · 0 URL/权限/返回值改。
- **选项**:
  - A:`git push origin master` → webhook 自动部署 → curl /api/version 看 cache_bust 翻新 + 抽查 `/api/team/employees`、`/api/erp/mappings/clients` 等返 401(未带 token = 路由在)→ 看 CI 绿。
  - B:继续本地累积更多 B1 slice · 攒一批再一次 push。
  - ⚠️ push 到 master 会被 auto-mode 权限分类器拦(本会话实测)· 需 Zihao 显式授权或加 `Bash(git push:*)` 权限规则。

---

## 4. 已抽出的 router 全景(14 个 `*_routes.py`)

| 模块 | 路由数 | 来源会话 |
|---|---|---|
| report_routes / recon_routes / recon_jobs_routes / import_routes / vat_excel_routes | — | 早期 |
| billing_routes / admin_diagnostics_routes | — | 阶段 5 / 早期 |
| notification_routes(6)/ clients_routes(5)/ exceptions_routes(8) | 19 | 第十/十一/十二会话 |
| **team_routes(7)/ erp_mappings_routes(12)/ email_ingest_routes(6)/ rd_routes(4)/ settings_routes(5)** | **34** | **第十六会话(本次)** |

**route_helpers.py**(公共 helper · 14 个 router 复用):`_require_super_admin` / `_require_owner_or_super` / `_log_op` / `_get_client_ip` / `_check_password_strength` / `_WEAK_PASSWORDS` / **`_plan_permissions`(本会话新搬入)**。

---

## 5. 下窗口 B1 续拆候选(按边界清晰度排序)

1. **history(7 路由 `/api/history*`)**:依赖 `_async_run_exception_checks` / `_check_history_access`(用 `_plan_permissions` · 现已在 route_helpers · entangle 解了一半)· 评估这两个 helper 是否也搬 route_helpers 或随 history 走。含 `/api/history/{id}/assign_client`(clients test 锁了它仍在 app.py · 搬时要更新该断言)。
2. **`/api/bank-recon/*`**(~10 路由 · 含 _dev/seed、_dev/clear · 部分逻辑较重 · 看 `_check_*` 依赖)。
3. **`/api/erp/*`**(endpoints / test-connection / customers / products / push / logs)· ⚠️ **铁律 #10**:async 路由调 sync Playwright adapter · 搬完必须保留 async tripwire 守门测试(AsyncLoopOffloadTests)· 别破坏 `await asyncio.to_thread`。
4. **`/api/admin/*` 大组**(cost / credits / monitoring / tenants / users / logs)· 多用 `_require_super_admin`(已在 route_helpers)· 量大 · 可拆成 admin_users_routes / admin_cost_routes 等多个。
5. **`/api/erp/xero/*` + connectors/status**(OAuth · 有状态 · 谨慎)。

---

## 6. 本会话验证过的安全范式(下窗口照抄)

**抽 router 步骤**:
1. grep 目标路由组 + 它用的 helper / model / 是否被组外引用(确认自包含)。
2. 新建 `xxx_routes.py`:`from __future__ import annotations` · `router = APIRouter()` · `from auth import get_current_user_from_request` · `from route_helpers import ...` · 组专属 helper/model 整体搬入(组外用的留 app.py 或搬 route_helpers)。
3. 路由体**逐字复制** · 只把 `@app.` → `@router.`。懒 import(asyncio / 第三方)保持原样。
4. app.py 加 `from xxx_routes import router as xxx_router` + `app.include_router(xxx_router)`。
5. **删 app.py 旧块**:用字节级 splice 保 LF —
   ```powershell
   $lines = [System.IO.File]::ReadAllLines("app.py")   # 丢 EOL
   # 边界 assert(top 是 # ==== / def / @app · end 是 return 行)
   $out = $head + $marker + $tail
   $enc = New-Object System.Text.UTF8Encoding($false)
   [System.IO.File]::WriteAllText((Resolve-Path "app.py"), ($out -join "`n") + "`n", $enc)
   ```
   删完 grep 确认 `@app.*("/api/xxx` 残留=0 · model/helper 残留=0(marker 注释里的同名词不算)。
6. 写 `tests/unit/test_xxx_routes_contract.py`:路由 path+method 集合 == 期望 · `app.app.routes` 含路由(防漏挂)· helper 单一来源 `assertIs(xxx._helper, route_helpers._helper)` · model 字段契约。
7. 守门:`python -m black <files>`(会 wrap 长 import 行 · 正常)→ `python -m ruff check <files>`(删块后常有孤儿 import F401 · 删掉)→ `python scripts/check_imports.py --quiet` → `python scripts/check_i18n.py --strict` → `python -m unittest discover -s tests/unit`。
8. commit(**用 `-F _commitmsg.txt` 文件传 message**:这会话发现 here-string `@'...'@` 偶发触发沙箱 Remove-Item 误判 · 用文件最稳)· message 带 `· REFACTOR-B1`。

**坑**:
- 改 app.py 别用大块 Edit 匹配(易 mismatch)· 用上面字节级 splice。
- black 会把超 100 字符的新 import 行 wrap 成多行 · 之后再 Edit 那行要按 wrap 后的样子匹配。
- 删块后跑 ruff 抓孤儿 import(本会话 `_check_password_strength` 就这样被抓出)。
- 删 helper 后若有 contract test 断言 `app._helper is route_helpers._helper` · 消费者搬走了就把断言跟到新模块(本会话 _check_password_strength 这么处理的)。

---

## 7. 红线 / 停止条件(本会话遵守的)

- 不 push(本会话指示)· 不 force-push · 不动 db.py schema · 不动前端 home.*(留 Zihao 在场)· 不动 git-deploy/webhook。
- 触发停止:上下文 ~80% / 不可抗阻碍 / 测试失败短时不可修 / 需改架构·部署·DB·付费·生产密钥 / 单轮 diff >30 文件 / 无法判断是否改变业务行为。
- 本会话**停止原因 = 主动收尾保预算**:已做 6 个干净 slice · 留足上下文写本交接文档 · 非阻碍非失败。

---

## 8. 未跑的检查(诚实记录)

- **playwright / node --check**:本会话 0 改 JS / 0 改 UI(纯后端 router 搬家)· 不适用 · 未跑。
- **生产 /api/version + CI**:未 push · 故未验证(见 §3)。
- **CI lint job**:本地已跑 black --check + ruff(F)全绿 · 等价覆盖 · CI 未实际跑(未 push)。
