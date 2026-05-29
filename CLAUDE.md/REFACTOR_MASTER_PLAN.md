# 🏗️ Pearnly · 整顿期主计划(REFACTOR_MASTER_PLAN)

> ## 🟢 2026-05-23 改善计划收尾 · 整顿可恢复(Zihao 拍板)
>
> **触发**:OCR/对账改善告一段落(M4 银行对账闭环 · M1/M2/M3 暂缓等用户反馈 · 学习机制设计已出但不建)· Zihao 拍板回归整顿。
>
> **整改单一权威源(已收尾)**:[`docs/audits/2026-05-22-ocr-recon-audit.md`](../docs/audits/2026-05-22-ocr-recon-audit.md)(看顶部"改善计划收尾"段)。
>
> **整顿期状态**:**恢复** · A 阶段 7.5/10(A0/A1/A2.1/A5/A6/A7/A8/A9 完成)· **A 阶段只剩 A3 + A4 · 都卡 Zihao 决策(服务器/钱/账号)** · 另已立"8 条硬门槛"(见下方专段 + 铁律 #23)。
>
> **接力 agent 进窗口先做**:读本文档"当前进度看板" + 找 A5 · 干活。改善已收尾 · 不再以审计文档为主线。
>
> **历史**:2026-05-22 因付费用户投诉 OCR 不准曾暂停整顿、整改优先;2026-05-23 改善收尾恢复整顿。

---

> **起源**:2026-05-22 Zihao 拍板"封锁整顿 5-8 个月 · 路径 B 上 Vite · 不开发任何新功能 · 把项目工程标准化到 Google / Anthropic Claude code 级"
>
> **状态**:整顿模式**恢复**(2026-05-23 改善收尾后续整顿 · 见本文档顶部"改善计划收尾"段)· 2026-05-29 起 3 窗口并行 loop 加速(ADR-011)
>
> **目标**:6-8 个月后 Pearnly 跟主流 SaaS 看齐 · "Google 级标准 90%+"(每个文件 100-500 行 · 50-100 个模块文件 · 测试覆盖 70%+ · 性能 p95 < 1s · 真到位)
>
> **本文档是整顿期单一权威源**(整改期间二线)· 所有接力 agent 进窗口必读

---

## 🚨 接力 agent 必读(开窗口前 60 秒)

**整顿期(2026-05-22 起到约 2026-12)铁律**:

1. **0 新功能开发**(铁律 #18)· 你 grep `MODULE_ROADMAP.md` 想做新功能 → 立即停 · 跟 Zihao 确认
2. **必读 4 文档**(铁律 #19)· 顺序:
   - `CLAUDE.md/CLAUDE.md`(项目宪法 · 28 条铁律)
   - `CLAUDE.md/STATE_PEARNLY.md`(当前状态 · 看头部"整顿模式 ON" 段)
   - **本文档**(整顿主计划 · 看"当前进度看板" + "下一个 task")
   - 当前 task 的"完成判定"段
3. **commit message 必含 task ID**(铁律 #20)· 格式 `<type>(<scope>): <subject> · REFACTOR-<task-id>` · 比如 `refactor(frontend): 抽 settings.js · REFACTOR-C12`
4. **6 道守门必跑全绿才能 push**(原有铁律 · 整顿期强化 · 2026-05-29 统一为 6 道):
   - `npm run format:check`(prettier · 最易漏)
   - `python -m unittest discover -s tests/unit` → 全量 all OK
   - `python scripts/check_imports.py --quiet` → EXIT 0
   - `python scripts/check_i18n.py --strict` → 0 missing 0 extra
   - `node --check <changed.js>` → 各改动 JS 都过
   - `npm run build`(Vite · 改前端必跑)
   - (E2E `npx playwright test` 按需单独跑 · 非每 commit 强制)
5. **窗口收尾必更新**(原有铁律 · 整顿期强化):
   - `STATE_PEARNLY.md` 写本窗口完成的 task + commit hash
   - 本文档"进度看板" 段更新 task 状态(待 → 做中 → 已完成)
   - 本文档对应 task 末尾加"完成日期 + commit hash"
6. **触发红线必停**(铁律 #16 红线 + 整顿期新增):
   - 改架构 / 加新功能 / 删字段 / 关键路径大改 → 停下问 Zihao
   - 删超过 30 个文件 → 停下问
   - 升级核心框架版本(FastAPI / Python 大版本)→ 停下问
   - 改 git-deploy.sh / webhook → 停下问

---

## 🔒 整顿期 8 条硬门槛(2026-05-23 Zihao 拍板 · 不可商量)

> 这 8 条是整顿期的"硬标准" · 比一般规矩更硬 · 接力 agent 违反任意一条 = 偷渡新债 · Zihao 追责。
> CLAUDE.md 铁律 #23 是本段的浓缩版 · 本段是权威详版。

**A. 止血(不让旧债继续长大)**

1. **`app.py` 封死** · 不许新增 `@app.*` 路由 · 新路由必须建 `*_routes.py` + `app.include_router()`。(强化铁律 #17 / #21)
2. **`db.py` 封死** · 不许新增 `ensure_*` 函数 · 新 schema 只能走 Alembic 迁移(借 A2.2 / B3 激活)。(强化铁律 #21 #5)
3. **`home.js` 封死** · 不许新增业务模块 · 新前端业务逻辑只能进 `src/home/*`(Vite ES 模块)。
   - ⚠️ **本条更正铁律 #17 / #21 的旧措辞"放 static/xxx.js IIFE"**:自 A1 上了 Vite + ES modules,**新业务逻辑一律进 `src/home/*`**;只有"完全独立、不依赖主应用"的小组件(如 version-banner)才允许留 `static/*.js` IIFE。

**B. 测试(每动一处都留安全网)**

4. **每拆出一个模块,必须同时带一个守门测试**(契约 / 单元)· 没测试 = 不算拆完 · 不许 commit。
5. **每个核心业务路径至少一个 E2E 或 integration 测试** · 核心路径 = 登录 / 注册 / 上传识别 / 销项税核查 / 收入对账 / ERP 推送 / 充值。

**C. 度量(数字不许造假 / 不许误导)**

6. **coverage 不死磕 70%** · 先按 A8 建 baseline · 之后**每月只准升不准降**(棘轮机制)· 降了 = CI 红 / Zihao 追。比一刀切 70% 更实在、更难造数据。
7. **`/ready` 必须能真实失败**(B4 落地时执行)· DB / Gemini / SMTP / LINE 任一挂 → `/ready` 返非 200 · **永远返 ok 的健康检查等于没有**。
8. **`scripts/refactor_progress.py` 必须诚实** · 数对位置(`src/home/*` 不是 `static/home/*`)· 不写死任何指标(integration 不许写死 0)· 每类按目标封顶(防某类超额掩盖未动的类)。**✅ REFACTOR-A5 已修(commit 见进度看板)**。

---

## 🧭 路径选择(2026-05-22 Zihao 拍板)

| 路径 | 说明 | 选择 |
|---|---|---|
| L1 推倒重写 | 整个项目重写 | ❌ |
| L2 换技术栈 | FastAPI → Django / vanilla → React | ❌ |
| **L3 内部整顿 + 路径 B** | 保留 FastAPI + 上 Vite + ES modules · 内部结构标准化 | ✅ **选这个** |

**为啥**:
- 有 1 真实付费用户(mrerp@outlook.co.th)· L1/L2 业务停 2-3 月不可接受
- 28 条铁律 + 守门测试 + 文档已立 · 推倒等于重做
- L3 + Vite 能到 Google 级 90% · 时间 4-6 月可控

---

## 📊 完成定义("Google 级 90%" 具体度量)

> **全生命周期权威详版 = [`docs/ENGINEERING_STANDARD.md`](../docs/ENGINEERING_STANDARD.md)**(从源码/去AI味 → 产品 → 流程 → 审核 → 测试 → CI/CD → 可观测 → 验收 → 安全合规 → 文档 · 每条标了靠什么机制保证)。本段是浓缩度量版。

整顿期结束的硬指标(全部达标才算完成):

### 代码规模(7 项)

> **行数目标分两层**:先达成"验收目标",能自然继续拆且职责更清晰时再冲"冲刺目标"。不允许为了凑行数制造过度抽象、空壳文件或跳转地狱。
>
> ⚠️ **"行数"指源码,不是成品(2026-05-29 钉死)**:目标是把巨石**拆成多个小源文件**(每个 < 500 行 · 好维护),**不是**把某个文件的内容压短。大厂(Chrome 36 行外壳 / Claude 一行 bundle)你看到的小行数是 **Vite build + minify 后的成品**,真源码是几千个小文件。成品体积归 E7(minify)管,源码行数归拆分管 —— **两件事别混。** "home.js < 200 行" = 入口/bootstrap 源文件,业务全在 `src/home/*`。

| 文件 | 当前(2026-05-22) | 目标 | 备注 |
|---|---|---|---|
| `home.js` | 33,251 行 | 验收 < 200 行 / 冲刺 < 120 行(入口 + bootstrap) | 业务逻辑全拆到 `src/home/*` 50-100 个模块 |
| `app.py` | 9,212 行 | 验收 < 500 行 / 冲刺 < 300 行(init + middleware) | 业务路由全拆到 20-30 个 `*_routes.py` |
| `db.py` | **9,255 行** | 验收 < 500 行 / 冲刺 < 300 行(cursor + pool + 框架) | 业务 SQL 迁到 `services/<domain>/<feature>.py` · 实际比估的大 2 倍 |
| `home.css` | **16,124 行** | 验收 < 500 行 / 冲刺 < 250 行(变量 + reset) | component CSS 拆 20-30 个 · 实际比估的大 2 倍 |
| `home.html` | 6,568 行 | 验收 < 1,000 行 / 冲刺 < 500 行 | 组件化或服务端拼接 |
| 模块文件数 | ~10 | 50-100 个 `src/home/*.js` + 20-30 个 `*_routes.py` + 10+ `services/*.py` + 20-30 component CSS | "Google 级"标志 |
| 单文件平均 | 巨大 | 100-300 行 | 超 500 行 = 拆 |

### 质量(8 项)

| 指标 | 当前 | 目标 |
|---|---|---|
| Unit tests | 293 | 500+ |
| Integration tests | 0 | 20+ |
| E2E tests | 1(着陆页) | 10+(覆盖核心路径) |
| 测试覆盖率 | 未测 | ≥ 70% |
| 静默吞错(`catch (_) {}` 无注释) | 21 个 home.js | 0 |
| API p95 响应时间 | 未测 | < 1 秒 |
| 前端首屏 LCP | 未测 | < 2.5 秒 |
| 切换交互延迟 | 3-5 秒 | < 1 秒 |

### 工程化(10 项)

| 指标 | 当前 | 目标 |
|---|---|---|
| Build pipeline | 无(裸文件) | Vite + esbuild |
| TypeScript 化前端 | 0% | 80%+ |
| ES modules | 0%(2 个独立 IIFE) | 100% |
| DB schema 版本化 | `ensure_*` 模式 | Alembic 全覆盖 |
| CI lint | 无 | black + ruff + ESLint + Prettier |
| CI 安全扫描 | 无 | bandit + safety + npm audit |
| 依赖锁定 | 无 | `requirements.lock.txt` + `package-lock.json` |
| 错误日志聚合 | 单 `last_500_event` | 简单版集中存储 + 时间线 |
| 健康检查端点 | 无 | `/health` + `/ready` |
| API 限流 | 部分(反薅闸) | 全局 + 每 endpoint |

### 文档(5 项)

| 文档 | 当前 | 目标 |
|---|---|---|
| `docs/README.md` 索引 | ✅(2026-05-22 done) | ✅ |
| ADR(架构决策记录) | 无 | 10+ 重要决策留文 |
| RUNBOOK(运维手册) | 部分散在 CLAUDE.md | 完整(部署 / 回滚 / 紧急排查) |
| OpenAPI / Swagger | FastAPI 自带未完善 | schema 完善 + 公开 `/docs` |
| ONBOARDING.md(给真人) | 无 | 完整 |

---

## 🗺️ 9 阶段路线图(A-I · 任务 ID 唯一)

> 每个 task 命名:`REFACTOR-<阶段字母><数字>` · 比如 `REFACTOR-A1`、`REFACTOR-C12`
>
> commit message 必含 task ID · 比如:`refactor(frontend): 装 Vite + 配 esbuild · REFACTOR-A1`

### 阶段 A · 工具链升级(1 个月 · 必须先做 · 后续依赖)

| ID | 任务 | 估时 | 依赖 | 状态 |
|---|---|---|---|---|
| **A0** | 整顿主计划落档(本文档 + 铁律 #18-20 + STATE 标识 + 统计脚本) | 2-3h | — | ✅ 2026-05-22 · commit `613ea23` |
| A1 | Vite + ES modules 落地(装包 + 配 esbuild + CI 加 build step + 把已抽 dashboard.js/billing.js 改 ES modules) | 1-2 天 | A0 | ✅ 全 4 子完成 · `e11e81d` / `cfbb7d5` / `1c4c3bd` · prod 11835032 部署成功 · 等 Zihao 人工测 dashboard + 充值 |
| A2 | Alembic 落地(装包 + `env.py` + 001 试点迁移 + git-deploy.sh 钩子) | 2.5h | A0 | 🟡 A2.1 ✅ `4d5c8ba`(装 alembic 1.18 / SQLAlchemy 2 / env.py 从 env var 读 DATABASE_URL / 001_baseline 空迁移)· A2.2 git-deploy.sh 钩子并入 B3(真迁第一个 ensure_* 时再加)|
| A3 | 环境分级(prod / staging / dev 三套 · Docker 本地或 Vultr 第二台) | 1-2 天 | A0 | 🟡 2026-05-24 · commit `df727f6`(Zihao 拍板**本地 Docker · 不开第二台 Vultr**)· Dockerfile + .dockerignore + docker-compose(staging)+ docker-compose.dev(热重载)+ ADR-003 · **本机未装 Docker · build 验证待 Zihao 装 Docker Desktop 后跑**(验证清单在 ADR-003)· prod 部署链未动 |
| A4 | Secrets 管理(`.env` → Doppler 或 1Password Secrets · 给多人协作铺垫) | 2-3 天 | A3 | 🟡 2026-05-24 · commit `df727f6`(Zihao 拍板 **Doppler · 个人免费**)· ADR-004 + 迁移 4 步计划 · **第 1 步收拢已完成**:生产 39 条密钥导入 Doppler `prd`(剔除 2 条死代码 demo 密码)· 桌面明文已删 · **剩第 2-4 步**:装 CLI / 本地 `doppler run` 验证 / 生产改用(碰红线)/ 清理旧密钥(都待做) |
| A5 | CI 加 lint + format(black + ruff + ESLint + Prettier) | 半天 | A0 | ✅ 2026-05-23 · commit `5ae7bd0`(black/ruff 全量格式化 129 .py + 顺手修 2 真 bug · prettier/eslint 格 18 可维护文件 · 巨石按 C1/C2/C3 豁免 · ci.yml 加并行 lint job · CI 双 job 全绿)|
| A6 | CI 加安全扫描(bandit + safety + npm audit) | 半天 | A5 | ✅ 2026-05-23 · commit `ed8b5af`(bandit HIGH 拦门 · 顺手清 2 处 md5 HIGH · pip-audit 代 safety 免账号 · npm audit · 三件套 baseline 全 0 · CI 绿)|
| A7 | 依赖锁定(`requirements.lock.txt` pip-tools) | 1-2h | A0 | ✅ 2026-05-22 · commit `296c074`(pip-tools 7.5.3 · 299 行 lock · ci.yml 装 lock · dependabot.yml 注释 + CONTRIBUTING.md §依赖管理) |
| A8 | Code Coverage(pytest-cov + 上传 codecov · baseline) | 半天 | A5 | ✅ 2026-05-23 · commit `c818578`(coverage.py 跑 unittest · baseline 22.5% · fail_under=21 棘轮只升不降 · ci 加 coverage 步骤 · codecov 上传需账号 token 暂缓)|
| A9 | Dependabot / Renovate 配置(自动 PR 升级依赖 · 每周一开) | 1h | A0 | ✅ 2026-05-22 · commit `e57993a`(.github/dependabot.yml · pip + npm + github-actions 3 ecosystem · 周一 08:00 Asia/Bangkok 开 PR · patch/minor 分组)|

**A 阶段完成判定**:Vite 跑通 / Alembic 迁过 001 / staging 能 deploy / CI 加了 lint+安全扫描 / requirements.lock 已生成 / Dependabot 跑过一次

---

### 阶段 B · 后端整顿(1-1.5 个月 · 可跟 C 并行)

| ID | 任务 | 估时 | 依赖 | 状态 |
|---|---|---|---|---|
| B1 | `app.py` 拆完 9k → 验收 < 500 行 / 冲刺 < 300 行(20-30 个 router) | 4-6 周 | A1, A5 | 🟡 进行中 · **已抽 14 个 router**:notification(6)+ clients(5)+ exceptions(8)+ team(7)+ erp_mappings(12)+ email_ingest(6)+ rd(4)+ settings(5)+ **bank_recon(11 `faaa536`)+ admin_migration(7 `b33dd58`)+ admin_cost(10 `13eded7`)+ tenant(6 `fac5f62`)+ admin_logs(4 `574c92d`)+ erp_xero(8 `569b534`)** · 另把 `_plan_permissions`(`870290c`)+ `_tid`(`4755af7`)搬进 route_helpers · `_ensure_fresh_xero_token` 随 erp_xero · **app.py 10075→9546→8589→7263**(第十七会话 8589→7263 · 净 -1326)· 每组带 contract test(unit 530→552→**580**)· 守门 imports/i18n/unit/black/ruff 全绿 · LF 全程干净 · **第十八/十九会话续抽** categories/erp/admin_users + exception_checks/history 组(全 push)· **第二十会话续抽** pages(12)/me(3+UserInfo)/line_binding(4)· **app.py 7263→4459** · 共 **21 router + 30 个 *_routes.py** · unit →639 · 全 push+CI 绿+生产零丢路由。**B1 安全部分已到顶**:剩 22 @app 全安全敏感(login/OAuth/email-code/JWT+账号合并)或勿碰(OCR recognize 850 行/LINE webhook)或故意留(/api/version)· **app.py < 500 无法靠安全搬家达成** · 需 auth 专窗口(铁律 #16 登录关键路径 · Zihao 在场)· 详见 `HANDOFF_REFACTOR_BC.md` |
| B2 | `db.py` 拆完 9k → 验收 < 500 行 / 冲刺 < 300 行(业务 SQL 迁 `services/`) | 3-4 周 | A1 | 🟡 进行中 · **第二十二会话**:db.py 10663→**7136**(-3527)· 抽 9 个域 DAL 到 services:`email_ingest/store.py`(10 `435ece6`)· `erp/oauth_store.py`(12 `78e9667`)· `erp/mappings_store.py`(15+常量 `f62d0d9`)· `notification/store.py`(9 `9de1baa`)· `erp/push_store.py`(25+3常量 `7edb3c3`)· `recon/{vat_recon_tasks,gl_vat,bank_recon_v2}_store.py`(7+6+6 `a012482`)· `recon/bank_recon_v1_store.py`(17 `e26dafd`)· **范式**:cohesive 域整片搬 service 模块(`import db`+运行时 `db.get_cursor()` → patch 生效 + 防循环 import)· db.py 文件尾 `from services.X import a as a` 显式 re-export(pyflakes 不报 F401)→ 所有 `db.xxx()`/`from db import xxx` 调用点**零改动** · 私有 helper/常量不外露 · 校验常量随域搬 · 每域带契约测试(函数在 service / re-export 同一对象防漂移)· LF 全程干净 · 全 push + CI 5 连绿 + 生产路由 401 验证零丢。**剩余域**(下窗口续 · 由易到难):archive_settings / rd_usage / vat_recon 三表组(vat_report+recon_task+recon_row)/ membership+RLS+migration / clients+categories+buyer_to_client / tenant / 操作日志+员工 / **(高敏后置 · Zihao 在场)** credits+charge_ocr(钱)/ user+auth / ocr_history(OCR 热路径)|
| B3 | 所有 `ensure_*` 迁 Alembic(25 个 · schema 完全版本化) | 3-4 周 | A2 | ⚪ |
| B4 | 健康检查端点 `/health` + `/ready`(DB / Gemini / SMTP / LINE 各 check) | 半天 | — | ⚪ |
| B5 | API 全局限流(每 IP / 每用户 / 每 endpoint · 比现有 PLG 反薅闸更全) | 1-2 天 | — | ⚪ |
| B6 | 结构化日志(logger 改 JSON · 加 request_id / user_id / tenant_id 全链路 trace) | 2-3 天 | — | ⚪ |
| B7 | 错误日志聚合(自建简单版 · 写 `errors` 表 + admin 后台时间线 · 不上 Sentry) | 2-3 天 | B6 | ⚪ |
| B8 | 多租户 RLS 双保险(Supabase Row Level Security · DB 层强制) | 1-2 周 | B3 | ⚪ |
| B9 | DB 索引审计(EXPLAIN 慢查询 · 加缺索引 · 删没用的) | 2-3 天 | — | ⚪ |
| B10 | DB 连接池调优(psycopg2 pool size + lifecycle) | 半天 | — | ⚪ |

**B 阶段完成判定**:`app.py` / `db.py` 达到验收 < 500 行；若继续拆能让职责更清晰,冲刺 < 300 行 / 25 个 ensure_* 全迁 Alembic / 4 个新端点端 + RLS / 9 个新机制全上线

---

### 阶段 C · 前端整顿(2-3 个月 · 最大头 · 可跟 B 并行)

| ID | 任务 | 估时 | 依赖 | 状态 |
|---|---|---|---|---|
| C1 | `home.js` 拆完 33k → 验收 < 200 行 / 冲刺 < 120 行(50-100 个 ES module · 每个 100-300 行) | 6-8 周 | A1 | 🟡 进行中 · home.js 32466→**6191**(第三十八~四十二会话大批 · 详见 STATE + `BATCH_STRATEGY.md` §10/§13)· 抽 35 个 `src/home/*` 模块 + i18n 字典→`static/i18n-data.js` + 整删老 admin 布局(`fa08ecc` -4566)+ **计费迁移收尾**(全平台只剩 credits+admin · 老套餐前后端全清 · `101824d`/`1f7d8b8`/`93a67da`/`52aeeb6`)· **WB-C1(2026-05-29)E2E 闸恢复(`7524309` storageState 账号隔离 + 专用账号 pearnly_e2e_2)→ 顶层函数群 window 桥接解封**:抽 line-email-modal/change-password/session-heartbeat 3 IIFE + 团队管理 team.js(`7bef576`)+ switchAutomationTab→automation.js(`640ac7b` · 删死码 showResetPwdResult/loadAutomationPage)· home.js 6191→**5359**(40 个 `src/home/*`)· 6 门 + CI success + 生产 E2E 03-08 7/7 · state-decoupled 顶层函数群逐组续抽;**深耦合 `{_results,_drawerIdx}`/`{_selectedFiles}` 簇(history抽屉/OCR/camera/RD/export)等 C9** · 🔴高敏 4 块抽 3(plans-plg-line 已删)· ⚠️**R3 chrome-render 组抽出生产 ReferenceError@loadAll 已 revert `d3c4deb`**:被 loadAll/boot init 期调用的顶层函数群不可经 window 桥接抽(await 早于 defer bundle · 竞态)· 须等 C9 |
| C2 | `home.css` 拆完 7k → 验收 < 500 行 / 冲刺 < 250 行(20-30 个 component CSS) | 2-3 周 | A1 | ⚪ |
| C3 | `home.html` 拆 6.5k → 验收 < 1000 行 / 冲刺 < 500 行(`<template>` 或服务端拼接) | 2 周 | C1 | 🟡 开篇 · home.html 6428→**4411**(第四十三会话 `e938ae3` · 抽 head 内联 `<style>` 巨块 2016 行 → `static/home-37-html-inline.css` · 字节无损 · 6 门绿 + CI success + 生产 E2E 10/10)· 剩 body HTML(`<template>` 化 · 较难 · 串行做) |
| C4 | Design System / 组件库(按钮 / 输入框 / Modal / Toast / Card / Table 抽通用 component) | 3-4 周 | C1 | ⚪ |
| C5 | TypeScript 化前端(vanilla JS → TS · 80%+) | 4-6 周 · 跟 C1 并行 | A1 | ⚪ |
| C6 | i18n 拆 .json(home.js 4 个翻译块各 2324 keys → `i18n/<lang>.json` + 按模块再拆) | 1-2 周 | C1 | ⚪ |
| C7 | 可访问性 a11y(WCAG 2.1 AA · 屏幕阅读器 / 键盘导航 / 对比度) | 2-3 周 | C4 | ⚪ |
| C8 | 移动端真适配(iPhone / Pixel 真测 · 触控目标 / 字号 / 横滚动) | 1-2 周 | C2 | ⚪ |
| C9 | 前端状态管理(`src/home/*` 模块化后引入轻量集中 store · 替代 bare global 耦合 · 单一数据源 + 订阅式刷新) | 1-2 周 | C1 | ⚪ **🔴 强撞 Loop 1 · 必须等 home.js 拆到地板(`src/home/*` 稳定)再做**(2026-05-29 Zihao 补入) |

**C 阶段完成判定**:`home.js` / `home.css` / `home.html` 先达到验收目标；若继续拆能让职责更清晰,再冲刺更小目标 / Design System 至少 8 个通用 component / TS 化 80%+ / i18n 拆到 .json / a11y AA / 移动端 4 浏览器全测过

---

### 阶段 D · 测试覆盖(1-1.5 个月 · 跟 B/C 并行)

| ID | 任务 | 估时 | 依赖 | 状态 |
|---|---|---|---|---|
| D1 | 10 个核心 E2E(登录 / 注册 / 上传 OCR / 销项税核查 / 收入对账 / ERP 推送 / 充值 / 客户 CRUD / 异常处理 / 4 语切换) | 4-6 周 | A1 | 🟡 1/10(已有着陆页) |
| D2 | Integration tests(API + 真 DB + Mock 外部服务 Gemini / LINE / Gmail) | 2-3 周 | A1 | ✅ 21 个集成测试(8 域:billing/recon/erp/ocr/auth/clients/team/archive · env-gated · CI 默认 skip)· 窗口 C `d37f091` |
| D3 | 死灰复燃守门(Zihao 给清单 · 每条加 1 个守门测试 · 复活即 CI 红) | 1 周 + Zihao 清单 | — | ⚪ 等清单 |
| D4 | 测试覆盖率达 70%(pytest-cov 报告) | 持续 | D1, D2 | ⚪ |
| D5 | Visual regression(Playwright screenshot diff · 防 UI 改一处炸另一处) | 1-2 周 | D1 | ✅ 10 页视觉回归 baseline(独立 `playwright.visual.config.js` · 暂不上 CI · 见 `tests/visual/README.md`)· `d37f091` |

**D 阶段完成判定**:10 E2E 跑通 / 20+ integration test / 死灰复燃清单全堵 / 覆盖率 ≥ 70% / Visual regression 跑

---

### 阶段 E · 性能 + 监控(1 个月 · 接 D)

| ID | 任务 | 估时 | 依赖 | 状态 |
|---|---|---|---|---|
| E1 | 性能基线(每个 API 加响应时间日志 · 写 `perf_log` 表 · 30 天看 p50/p95/p99) | 1 周 | B6 | ⚪ |
| E2 | 前端首屏测速(Playwright + `performance.timing` · FCP/LCP/TTI baseline) | 半天 | D1 | ⚪ |
| E3 | 修最慢 3 个 API(p95 < 1s) | 2-3 周 | E1 | ⚪ |
| E4 | 修最慢 3 个前端模块(切换 < 1s) | 2-3 周 | E2 | ⚪ |
| E5 | 静态资源 CDN(Cloudflare DNS only → 打开 proxy · static/*.js/css 走 CDN) | 半天 | — | ⚪ |
| E6 | 图片 / PDF 预处理(OCR 上传压缩 · 减带宽 + 加快 Gemini) | 1 周 | — | ⚪ |
| E7 | 资源 minify(确认 Vite prod build 的 JS/CSS minify 生效 + 补 HTML minify · 减体积加快首屏) | 半天 | A1 | ⚪ **🔴 碰 `vite.config` · 影响 Loop 1 的 build 守门 · 必须等 Loop 1 完成再改**(2026-05-29 Zihao 补入 · 注:JS/CSS minify Vite prod build 多半已默认开 · 本任务主要是确认 + 补 HTML minify) |

**E 阶段完成判定**:API p95 < 1s / 前端 LCP < 2.5s / 切换交互 < 1s / CDN 启用 / 大文件预处理

---

### 阶段 F · 数据 + 存储(2-3 周)

| ID | 任务 | 估时 | 依赖 | 状态 |
|---|---|---|---|---|
| F1 | 文件存储 Supabase Storage(本地磁盘 → Supabase · 为未来多实例铺垫) | 1-2 周 | B1 | ⚪ |
| F2 | 备份策略(Supabase 自带 + 应用层关键文件 · 写 RUNBOOK) | 半天 | F1 | ⚪ |
| F3 | 数据导出(用户一键导出所有数据 · GDPR / PDPA 合规) | 1 周 | — | ⚪ |

**F 阶段完成判定**:文件全挪 Supabase Storage / 备份脚本 + RUNBOOK / 用户能导出

---

### 阶段 G · 文档 + 流程(1-2 周 · 随时做)

| ID | 任务 | 估时 | 依赖 | 状态 |
|---|---|---|---|---|
| G1 | ADR(10+ 重要决策留文 · 给未来 AI 看) | 1 周 | — | ✅ 11 个(ADR-001~011 · 含 ADR-010 防屎山 + ADR-011 3 窗口并行 · `3e7647c`)|
| G2 | RUNBOOK(部署 / 回滚 / 紧急排查 / 数据恢复 / 服务挂了怎么办) | 1 周 | — | ✅ `docs/RUNBOOK.md` · `5544d0e` |
| G3 | ONBOARDING.md(给真人协作者) | 半天 | — | ✅ `docs/ONBOARDING.md` · 窗口 C `18e2747` |
| G4 | OpenAPI / Swagger(完善 schema · 公开 `/docs`) | 半天 | B1 | ✅ `docs/openapi.md`(36 router 索引)· `18e2747` |
| G5 | PR / Issue 模板(`.github/PULL_REQUEST_TEMPLATE.md`) | 1h | — | ✅ PR 模板 + `ISSUE_TEMPLATE/question.md` · `18e2747` |
| G6 | CHANGELOG 自动生成(git-cliff 类 · 从 commit message 出) | 半天 | — | ✅ `docs/CHANGELOG.md` + git-cliff 配置(暂不上 CI)· `18e2747` |
| G7 | CODEOWNERS(GitHub 标记 · 防误改) | 1h | — | ✅ `.github/CODEOWNERS`(高敏路径自动 @ Zihao)· `18e2747` |

**G 阶段完成判定**:10+ ADR / RUNBOOK 完整 / ONBOARDING / Swagger 公开 / 模板齐 / CHANGELOG 自动

---

### 阶段 H · 合规 + 安全 review(1-2 周 · 靠后)

| ID | 任务 | 估时 | 依赖 | 状态 |
|---|---|---|---|---|
| H1 | 隐私政策 / 服务条款 review 4 语(GDPR + PDPA) | 1 周 | — | ⚪ |
| H2 | Cookie 政策(给用户 opt-out) | 半天 | — | ⚪ |
| H3 | 数据删除(用户注销时真删 · 不只 soft delete) | 2-3 天 | F3 | ⚪ |
| H4 | 安全审计 review(OWASP Top 10 · XSS / SQLi / CSRF / SSRF / auth bypass) | 1 周 | — | ⚪ |
| H5 | HTTPS / TLS 续期(certbot 自动 + 监控告警) | 半天 | — | ⚪ |
| H6 | API key 轮换流程(LINE / Gmail / Gemini · 防泄露) | 半天 | A4 | ⚪ |

**H 阶段完成判定**:法律文档 4 语全 / OWASP Top 10 过 / TLS 自动续期 + 告警 / key 轮换流程文档化

---

### 阶段 I · 抛光收官(1-2 周)

| ID | 任务 | 估时 | 依赖 | 状态 |
|---|---|---|---|---|
| I1 | 静默吞错全清(home.js 剩 21 个 + 后续新增 · 清完 0 silent block) | 1-2 周 | C1 | 🟡 30/52 done |
| I2 | 死代码清完(grep `@deprecated` / `老版本` / `备用` · `git rm` 真删) | 1 周 | C1, B1 | 🟡 部分 · CLEANUP-PLAN(2026-05-22 Zihao 截图发现 admin 残留)· 后端 4 老订阅路由 + admin SPA 三件套 + home.* 用户可见 3 处文案 全清 `3cb8675` + 本 commit · home.js 死代码(L22200+ admin SPA 独立前老逻辑 + 27 个 unused i18n key + PLAN_CONFIG 常量) 留 C1 拆时一并清 |
| I3 | 性能再 review(E 阶段后再扫一遍 · 找漏的) | 半天 | E | ⚪ |
| I4 | 文档完整 review(docs/ 全索引 + 现状标签) | 1 周 | G | ⚪ |
| I5 | 最后一次大体检(让别的 AI 跑 · 跟 2026-05-21 那次对比) | 1 周 | A-H 完成 | ⚪ |
| I6 | **去 AI 味全量审计**(新旧源码都过 · 消除 `docs/ENGINEERING_STANDARD.md` §1.1 列的 13 种 AI 痕迹:过度注释/emoji/防御冗余/泛化命名/调试残留/AI自述/重复/魔法值等)· 让代码像资深工程师写的 | 2-3 周 | C1, B1 | ⚪ (2026-05-29 Zihao 拍板新增 · 拆模块时顺手清 + 本 task 收尾审计) |

**I 阶段完成判定**:0 silent block / 0 死代码 / **0 AI 味(过 ENGINEERING_STANDARD §1.1)** / 体检报告显示"Google 级 90%+"达标

---

## 📋 当前进度看板(每窗口收尾必更新)

> 状态符号:⚪ 待启动 · 🟡 进行中 · ✅ 已完成 · ⏸️ 已跳过 · ❌ 取消

> **🟢 窗口 C 跑文档/测试**(2026-05-28 · REFACTOR-WC · 0 业务代码)· 15/15 任务全 ✅ · 4 commit (`016aa79` `18e2747` `d37f091` + 本) · **铁律 #27 防屎山闸 + #28 新功能 4 问写入项目宪法 · scripts/check_file_size.py + scripts/check_line_ratchet.py + CI lint-size(warning 模式)+ 19 守门测试 + 21 集成测试(8 域)+ 10 视觉 baseline + G3-G7 文档 5 项 + ADR-010/011** · 详见 [`docs/refactor/WINDOW_C_COMPLETE.md`](../docs/refactor/WINDOW_C_COMPLETE.md) · **⚠️ 等 Loop 1 完成跟 Zihao 说切 CI 行数硬门 fail 模式**。

| 阶段 | 完成度 | 当前 task | 备注 |
|---|---|---|---|
| **A 工具链** | 🟡 8/10 | A0 ✅ · A1 ✅ · A2.1 ✅ `4d5c8ba` · A5 ✅ `5ae7bd0` · A6 ✅ `ed8b5af` · A7 ✅ `296c074` · A8 ✅ `c818578` · A9 ✅ `e57993a` · A2.2 并入 B3 · **A3/A4 进行中 `df727f6`** | 2026-05-24 Zihao 拍板 **A3=本地 Docker · A4=Doppler** · A3 配置就绪(待 Zihao 装 Docker Desktop build 验证)· A4 生产 39 密钥已收拢进 Doppler `prd`(待验证+清理旧密钥)· 详见 ADR-003/004 |
| B 后端 | 🟡 **B2 ✅ db.py<500** · B1 卡高敏 | **B2 ✅ 完工**:db.py 10663→**332**(<500 达标 `57ec1dc`)· **B1**:app.py 10075→**1701**(剩高敏 OCR/LINE 待 E2E 闸) | **B2(2026-05-29 收官)**:db.py 819→332 = 把 286 个(36 域)re-export 垫片收进门面 `services/dal_reexports.py`(<500)· 一行 `import *` 桥回 · 纯结构 0 逻辑改 · 推翻「<500 不可达」结论 · CI 真绿。此前 18 域 DAL 抽到 services(第二十二/二十三会话起 · re-export 范式零改调用点)· services/*.py 125(R17 push_store · **R19 `780a36c` 拆 auto_push 539→406 <500 · Xero 自动推→auto_push_xero**)· *_routes 36→38(**R18 `51c0035` 拆 erp_routes 1206→460 <500 · 端点CRUD/推送日志各自成模块 + erp_routes_access 共享准入闸 · include_router 聚合 · app include 不变**)。db.py = 连接池/get_cursor/RLS only。B1:21 router + 剩高敏 OCR/LINE 需 Zihao 独立 E2E 账号/C9 |
| C 前端 | 🟡 C1 到地板 · C2 ✅ home.css 0 · C3 🟡 开篇 | 第四十三会话:home.html 6428→**4411**(抽 head 内联 `<style>` 巨块 → home-37 切片) | C1:home.js 32466→**6191**(35 个 `src/home/*` + i18n-data.js + 老 admin 布局整删 + 计费迁移)· **剩地板**(routeTo 中枢 / 顶层函数群 / 🔴高敏)需 Zihao 在场。C2:home.css 16673→**0** ✅(36 切片)。**C3:home.html 6428→4411(`e938ae3` · 抽内联 style 2016 行 → home-37-html-inline.css · 字节无损 · CI success · 生产 E2E 10/10)· 剩 body HTML 组件化(串行)**。详见 STATE 第四十三会话块 + `BATCH_STRATEGY.md` §10/§13 |
| D 测试 | 🟡 **4/5**(D1 部分 + D2 Wave 0 + **D2 集成 21 个 + D5 视觉 10 页** · WC `d37f091`)| D2/D5 收尾 → D3/D4 待做 | **窗口 C(2026-05-28)REFACTOR-WC-P3**:D2 +21 集成测试(8 域 · billing/recon/erp/ocr/auth/clients/team/archive · env-gated · CI 默认 skip)+ D5 10 页视觉回归 baseline(独立 playwright.visual.config.js · 暂不上 CI · 见 `tests/visual/README.md`)。**第三十五会话(2026-05-27)REFACTOR-D2 Wave 0**:17 个核心纯逻辑模块行为契约 unit 872→1095 + 修 3 真 bug(`85c35bb`)。早前 D1 第二十一会话 `d65b692` |
| E 性能 | ⚪ 0/6 | — | 依赖 B6 + D1 |
| F 数据 | ⚪ 0/3 | — | 依赖 B1 |
| G 文档 | 🟡 **7/7**(G1 + G2 + **G3/G4/G5/G6/G7 · WC `18e2747`**) | ✅ G 阶段全收齐 | G1:ADR 11 个(+ADR-010 防屎山机制 + ADR-011 3 窗口并行 · WC)· G2:RUNBOOK ✅(`5544d0e`)。**窗口 C 收齐 G3/G4/G5/G6/G7**(REFACTOR-WC-P2 `18e2747`):G3 `docs/ONBOARDING.md` + G4 `docs/openapi.md`(36 router 索引)+ G5 question 模板补齐 + G6 `docs/CHANGELOG.md`(git-cliff 配置存档 · 暂不上 CI)+ G7 `.github/CODEOWNERS`(高敏路径自动 @ Zihao) |
| H 合规 | ⚪ 0/6 | — | 靠后 |
| I 抛光 | 🟡 1.6/5(I1 ✅home.js silent=0 + 部分 I2) | — | **I1:home.js 无注释 silent 0(`b7d167b`)** · I2 死码续清(usage 计数器/demo 播种 `158b55c`/`b62aeca`)+ 老订阅残留全清 |
| **WC 防屎山(新)** | ✅ **完成** `016aa79` | 铁律 #27 #28 + 2 脚本 + CI warning + 19 守门测试 | **窗口 C(2026-05-28)REFACTOR-WC-P1**:防屎山 4 件套(铁律 #27 4 条 / 铁律 #28 新功能 4 问 / `scripts/check_file_size.py` 220 行 / `scripts/check_line_ratchet.py` 250 行 + `RATCHET-EXEMPT:` 透明豁免 / CI `lint-size` job warning 模式 `continue-on-error: true` / `tests/unit/test_anti_bigfile.py` 19/19 PASS)· 首跑抓 39 违规 + 5 历史豁免 · **等 Loop 1 完成切硬门 fail 模式** |

**累计 task 数**:60 主 task · 已完成约 5 个(A0/A1/A2.1/A7/A9)+ 进行中约 3 个(C1/D1/I1)· 待启动 52 个

**当前累积成果**(从 2026-05-21 EXECUTION_PLAN 开始):
- `app.py` 10,075 → **4,459 行**(减 5,616 · B1 拆 21 router + 服务模块 · 安全部分到顶)
- `db.py` 10,663 → **819 行**(减 9,844 · 续抽至 819 见进度看板 C 行 · **2026-05-28 一夜自主 loop 11 commits:7 域 + preferred_lang + 删死码×2(4 用量计数器+demo 播种)+ I1 home.js silent=0 + ADR-009**:`73bebb5`/`c769104`/`16eaf14`/`122ff3c`/`11b3f56`/`547f116`/`14370ed`/`885cfbc`/`158b55c`/`b62aeca`/`b7d167b`/`7dfb1d5` 3356→1731)· 第四十一会话 `4a10b88` membership/tenant 接线 4620→3371 · 此前 **B2 第二十二+二十三会话** · 抽 18 域 DAL → services:email_ingest/erp.oauth/erp.mappings/notification/erp.push/recon.{vat_recon_tasks,gl_vat,bank_recon_v2,bank_recon_v1}/archive/rd/cost/exceptions/clients/billing/recon.vat_recon〔三表组〕/audit/team · **+user_settings(dup_check/erp_push_mode/gemini_key)**)
- `home.js` 33,768 → **6,190 行**(C1 持续抽至 6,190 见进度看板 C 行 + STATE · 早期:抽 dashboard + billing IIFE→ES module · + i18n 字典 9,763 行→`static/i18n-data.js` · + 测试中心 493 行→`src/home/test-center.js`)
- `services/**/*.py` 40 → **66**(B2 新增 18 个 store + 各 __init__);`services/ocr/entrypoints.py`(171 行 · 第二十一会话 `1eadc16`):web/LINE/email 三处共用 OCR 入口 helper 从 app.py/email_ingest 抽出
- 守门测试:0 → **1516 unit**(第四十一会话 +384 services 数据层行为契约 `917f2f4` 1132→1516;此前 B2 +40 域契约 → 702;**第三十五会话 REFACTOR-D2 Wave 0 安全网 +~220** → 17 个核心纯逻辑模块行为契约 · 顺手挖修 3 个真 bug)+ 1 E2E + CI(lint + test 双 job)全绿

---

## 🔄 接力 protocol(每窗口必走)

### 开窗口(60 秒)

```
1. 读 CLAUDE.md/CLAUDE.md(项目宪法)— 重点看顶部 28 条铁律
2. 读 CLAUDE.md/STATE_PEARNLY.md 头部 — 确认"整顿模式 ON"
3. 读本文档"当前进度看板" — 找下一个 task
4. 读对应 task 的"完成判定"段
5. git branch --show-current → 确认 master(铁律 #14)
```

### 干活

```
1. TaskCreate 创建本窗口任务列表
2. 按 task 完成判定干
3. 字节级 CRLF 处理避免 BOM(吸取 Task 5.1+5.2 教训)
4. 每个修改 file 都 node --check / python -c "import" 自查
```

### 收尾(每个 commit 前)

```
1. 跑 6 道守门:
   npm run format:check
   python -m unittest discover -s tests/unit
   python scripts/check_imports.py --quiet
   python scripts/check_i18n.py --strict
   node --check <changed.js>  # 若改了 JS
   npm run build             # 改前端必跑
   # E2E npx playwright test 按需单独跑(非每 commit 强制)
2. 全绿才 commit
3. commit message:
   <type>(<scope>): <subject> · REFACTOR-<task-id>
   
   <body>
   
   守门 6 道全绿:format/unit/imports/i18n/node/build
   
   Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
4. git push origin master(C 档位 · 不问)
```

### 验证(每次 push 后)

```
1. 等 webhook 自动部署(~20s)
2. curl https://pearnly.com/api/version 看 cache_bust 翻新
3. PAT + GitHub Actions API poll CI 状态 · 等 completed success
4. 更新进度看板:
   - 本文档 task 状态(待 → 做中 → 已完成)
   - 本文档 task 末尾加"完成日期 + commit hash"
   - STATE_PEARNLY.md 写本窗口 commit + 简短总结
```

### 跑统计脚本(每窗口 1 次 · 防偷懒)

```
python scripts/refactor_progress.py
```

输出当前 `home.js` 行数 / `app.py` 行数 / 测试数 / 模块文件数 / Google 级达标进度 %。

---

## 🚦 窗口产能标尺

| 任务规模 | 一窗口能做 | 例子 |
|---|---|---|
| 小(< 30min) | 4-6 个 | 改 cache_bust / 加注释 / 调文案 / silent 注释 |
| 中(30-90min) | 2-3 个 | 抽 1 个 router / 1 个前端模块 / 1 个 E2E |
| 大(2-4h) | 1 个 + 收尾 | 装 Vite / 写 10 个测试 / 大重构 |
| 巨大(> 4h) | 拆多窗口 | 阶段 C 整个 home.js 拆 → 60+ 个小 task |

**实测数据**(2026-05-22 第三会话):5 个 commit · 5 道守门 · prod + CI 全绿 · 约 3-4 小时 · 上下文 75%

---

## 📈 月报模板(每月末出一次)

格式:`docs/refactor/monthly-YYYY-MM.md`

```markdown
# 整顿月报 · YYYY-MM

## 量化进度
- home.js: NNN → MMM 行(减 X 行)
- app.py: NNN → MMM 行
- 测试数: NNN → MMM
- 模块文件: NNN → MMM
- Google 级达标进度: NN% → MM%

## 完成的 task
- REFACTOR-XX · 标题 · commit hash
- ...

## 阻塞 / 风险
- ...

## 下月计划
- ...
```

---

## 🛡️ 防偷懒机制

| 机制 | 实施 | 接力 agent 偷懒 → 后果 |
|---|---|---|
| 每窗口必跑 `scripts/refactor_progress.py` | 输出固定格式 | 数字没动 = Zihao 一眼看穿 |
| 每窗口必更新进度看板 | 本文档 + STATE | 没更新 = 下窗口接不上 |
| commit message 必含 REFACTOR-XX | 铁律 #20 | grep 不到 = 偷做新功能 |
| CI 6 道守门 | 已落 | 跑红 = push 不上 |
| 每月末必出月报 | 模板 + cron 提醒(可选) | 没月报 = Zihao 主动问 |

---

## 🎯 完成定义快速 check(整顿期结束时跑)

```
# 代码规模 7 项
[ ] home.js 验收 < 200 行 / 冲刺 < 120 行
[ ] app.py 验收 < 500 行 / 冲刺 < 300 行
[x] db.py 验收 < 500 行 ✅ 332 行(2026-05-29 `57ec1dc` · re-export 收进 services/dal_reexports 门面)· 冲刺 < 300 行(可选 · 剩 RLS infra 250 受硬线#1 保护不动)
[ ] home.css 验收 < 500 行 / 冲刺 < 250 行
[ ] home.html 验收 < 1000 行 / 冲刺 < 500 行
[ ] 模块文件数 ≥ 100(50+ src/home/*.js + 20+ *_routes.py + 10+ services/ + 20+ component CSS)
[ ] 单文件平均 100-300 行 · 0 文件 > 500 行(除非有理由)

# 质量 8 项
[ ] Unit tests ≥ 500
[ ] Integration tests ≥ 20
[ ] E2E tests ≥ 10
[ ] 测试覆盖率 ≥ 70%
[ ] 静默吞错 = 0
[ ] API p95 < 1s
[ ] 前端 LCP < 2.5s
[ ] 切换交互 < 1s

# 工程化 10 项
[ ] Vite + ES modules 100%
[ ] TypeScript 化 ≥ 80%
[ ] Alembic 全覆盖
[ ] CI lint(black + ruff + ESLint + Prettier)
[ ] CI 安全扫描(bandit + safety + npm audit)
[ ] requirements.lock.txt + package-lock.json
[ ] 错误日志聚合
[ ] /health + /ready
[ ] API 限流全局
[ ] Dependabot / Renovate 运转

# 文档 5 项
[ ] docs/README 索引
[ ] ADR ≥ 10
[ ] RUNBOOK 完整
[ ] OpenAPI 公开
[ ] ONBOARDING.md

# 第三方体检
[ ] 让别的 AI 跑只读体检 · 报告显示 "Google 级 90%+"
```

全过 → 整顿期结束 · 解禁新功能。

---

## 📂 整顿期文档结构

```
项目根/
├── CLAUDE.md/
│   ├── CLAUDE.md              ← 项目宪法 · 28 条铁律(18-20 整顿期)
│   ├── STATE_PEARNLY.md       ← 当前状态 · 整顿模式 ON 标识
│   ├── REFACTOR_MASTER_PLAN.md ← 本文档 · 整顿单一权威源
│   ├── EXECUTION_PLAN.md      ← 历史 8 阶段 · 已合并入本文档
│   ├── TECH_DEBT.md           ← 技术债清单 · 长期持续
│   ├── BACKLOG.md             ← 任务清单
│   └── ...
├── docs/
│   ├── README.md              ← 40 文档索引
│   ├── refactor/              ← 整顿期月报 + ADR
│   │   ├── monthly-2026-05.md
│   │   ├── monthly-2026-06.md
│   │   ├── adr-001-vite.md
│   │   ├── adr-002-alembic.md
│   │   └── ...
│   ├── architecture/
│   ├── audits/
│   └── ...
├── scripts/
│   ├── refactor_progress.py   ← 整顿进度自动统计
│   ├── check_imports.py
│   ├── check_i18n.py
│   └── ...
└── ...
```

---

## ❗ 例外段 · 整顿期破例做的新功能(铁律 #18 例外条款)

整顿期『0 新功能』红线 · 但 Zihao 可拍板『破例做某新功能』(铁律 #18 例外条款)·
本段记录每条破例 · 入档原因 · 防接力 agent 看见就以为闸开了。

| 日期 | 破例 task | commit | 原因 |
|---|---|---|---|
| 2026-05-22 | **BUG-B** · 收入对账 3 个 anchor 余额(GL 期末 / Statement 期初 / GL 期初)手动录入兜底 | `5ccd989` | OCR 抽这 3 个『锚点』数字不准时整张对账报告废 · 影响付费用户对账准确率 · 业务等式破坏一连串错位 · Zihao 拍板紧急 BUG 修复一级 · 破例做。客户原始诉求图见 D:\Users\Skin\Desktop\BUG\BUG-B\(1.jpg + 2.jpg + 紫色 bracket)|

**破例的代价**(继续整顿期记账):
- 整顿期破例次数累计:1 次(2026-05-22)
- 跟整顿期验收目标(home.js < 200 行 / app.py < 500 行)冲突:本次 +57 行 home.js / +8 行 app.py / +113 行 home.html / +24 行 recon_routes.py · home.js / home.html 都长 · 跟阶段 C 拆解目标背道而驰
- 缓解措施:整顿期结束(2026-12 左右)纳入 home.js 拆出后的 brv2 模块独立文件 · 同步迁出
- 闸不再开:Zihao 必须明确说『再破例 X』· 接力 agent 看到 MODULE_ROADMAP / 用户报新功能 → 立即停 · 跟 Zihao 确认

---

## 🚀 下一个 task

**⛔ 下窗口先做 BUG 整改(Zihao 2026-05-25 拍板:BUG > 整改)· Zihao 会在下窗口发 BUG 问题 · 修完 BUG 再回 B2 续抽。**

---

### 🚀🚀 整顿恢复后走 `/batch` 加速(2026-05-27 Zihao 拍板 · 见 `docs/refactor/BATCH_STRATEGY.md`)

**前提**:ERP「开箱即用」收尾(P2-B 日志折叠 / P2-C 不裸透泰文 / P3 概念导航)修完后,整顿正式恢复,并改用 **`/batch` 并行 worktree agent** 加速拆巨石/补测试。

**接力窗口进来(Zihao 说「继续整顿,按 BATCH_STRATEGY 走」)**:
1. 读 `docs/refactor/BATCH_STRATEGY.md`(整套作战手册 · 5 波次 + 承包清单 + agent 黄金模板 + 操作手册)。
2. 看该文档 §10 进度账本找当前波次,从 **Wave 0(安全网:E2E + 集成测试)** 起跑——动巨石前必须先有测试网。
3. 核心范式:**拆分=并行(agent 只 copy-out 新文件,不删巨石)· 接线=串行(单独窗口删巨石)**。
4. **Wave 2(home.js)必须在 ERP P2-C 之后**(P2-C 也改 home.js)。
5. 高敏域(登录/计费/OCR热路径/auth/RLS)永不进 batch,Zihao 在场单独做。

> 本段是整顿"如何加速"的指针 · 详版权威在 `BATCH_STRATEGY.md`。

**当前(第二十三会话 · 2026-05-25)· B2 db.py→services 长跑续**(Zihao "继续 · 慢慢做 · 最安全方式"):
- db.py 7136→**4513**(本会话 -2623 · 累计自 10663 起 -6150)· 再抽 9 个 cohesive 域 DAL 到 services(全 push 4 批 + CI 绿 + 生产 401 验证零丢路由):
  - `services/recon/vat_recon_store.py`(`cf712df` · 19 函数 · P0-VAT 对账三表组 + 屏 B 内嵌 client helper · find_or_create 原 bare `create_client`→`db.create_client` · get_recon_row 的 module 级 import json 随域搬)
  - `services/audit/store.py`(`cc2c3f5` · 3 函数 · operation_logs 操作/审计日志)
  - `services/team/store.py`(`048a0e7` · 4 函数 · 员工管理 users role=member · add_employee 原 bare `find_user_by_username`→`db.find_user_by_username` · import bcrypt as _bcrypt 进 header)
  - 以下 6 域见下方原记录:
  - `services/archive/store.py`(`ca4f242` · 3 函数 · 智能归档设置)
  - `services/rd/store.py`(`9a29821` · 2 函数 · RD 校验日限)
  - `services/cost/store.py`(`6870222` · 6 函数 · ocr_cost_log 成本记账+只读聚合 · 不涉扣费)
  - `services/exceptions/store.py`(`9468ba6` · 13 函数 · 异常栏+白名单 · tenant 隔离矩阵)
  - `services/clients/store.py`(`1888f23` · 16 函数 · clients CRUD+供应商分类+买家→客户映射/解析 · tenant 隔离矩阵 · 字节级提取)
  - `services/billing/store.py`(`5531a3b` · 2 函数 · billing_balance_log calibration 兜底)
- 守门:每域契约测试(共 +12 unit:682→**694**)· 既有 tenant 隔离/分类器/dedup/buyer-resolver/salesvat 测试全绿(`mock.patch("db.get_cursor")`/`db.log_ocr_cost`/`db.get_latest_balance`/`db.try_resolve_buyer_to_client` 经 re-export 仍生效)· black(py311)/ruff/check_imports/check_i18n(0/0)/LF 无 BOM 全绿。services 新增 6 个 store(archive/rd/cost/exceptions/clients/billing)。

**(第二十二会话 · 2026-05-25)· B2 启动**:
- db.py 10663→**7136**(-3527)· 抽 9 个 cohesive 域 DAL 到 services(全 push + CI 绿 + 生产 401 验证零丢路由):
  - `services/email_ingest/store.py`(`435ece6` · 10 函数)
  - `services/erp/oauth_store.py`(`78e9667` · 12 函数 · _b64 私有)
  - `services/erp/mappings_store.py`(`f62d0d9` · 15 函数 + ERP_TYPES_VALID/PEARNLY_TAX_KINDS_VALID 常量随域搬)
  - `services/notification/store.py`(`9de1baa` · 9 函数)
  - `services/erp/push_store.py`(`7edb3c3` · 25 函数 + 3 公共常量 · 重试/分类器)
  - `services/recon/{vat_recon_tasks,gl_vat,bank_recon_v2}_store.py`(`a012482` · 7+6+6 函数 · 三对账任务表 · tenant 隔离矩阵)
  - `services/recon/bank_recon_v1_store.py`(`e26dafd` · 17 函数 + _find_candidates 私有 · session+匹配候选)
  - 配套 `09a3e73` 把已抽 store 统一改 `import db`+运行时 `db.get_cursor()`(patch 生效 + 防循环)
- **B2 范式(下窗口照搬)**:① 行号随每次删除下移 · **抽前必 re-grep 当前行号**(别用旧 def-list)· ② cohesive 整片搬 service 模块 · `import db`+`db.get_cursor()`(不用 `from db import get_cursor` by-value · 否则 tenant 隔离测试 patch 失效)· ③ db.py 文件尾 `from services.X import a as a`(`x as x` 形式避 F401)· ④ 私有 `_helper`/`_常量` 不外露(确认无外部 `db._x` 引用)· 校验常量只在本域用则随域搬 · ⑤ 字节级 LF splice(无 BOM)· 边界 assert · ⑥ 每域带契约测试 · 跑全量 unit(尤其覆盖该域的既有测试)· ⑦ 批量本地 commit · 攒几个再 push(减生产重启)。
- **剩余域**(BUG 整改后再续 · 由易到难):membership+migration(admin · migrate_to_membership_model/list_orphan_users/fix_orphan_users/backfill_tenant_ids/get_visible_client_ids_for_user/list_assignments_by_employees/set_employee_assignments/auto_assign_client_to_creator/get_user_tenant_id · **⚠️ get_cursor_rls/_is_rls_enabled/get_clients_rls_status/run_rls_isolation_tests 是 RLS 基础设施 · get_cursor_rls 与 get_cursor 并列是 cursor 框架 · 别搬别动**)/ tenant(get_tenant/create_tenant/list_all_tenants/update_tenant_*/get_tenant_monthly_usage/list_tenant_members/get_tenant_usage_summary/list_all_owner_users/create_owner_user/preview_owner_cascade/delete_owner_user_cascade)→ **(高敏后置 · 建议 Zihao 在场)** verify_user_password/reset_user_password / credits+charge_ocr(钱)/ user+auth(登录)/ ocr_history(OCR 热路径)。**已完成(18 域)**:email_ingest / erp.oauth / erp.mappings / notification / erp.push / recon 4 表(vat_recon_tasks/gl_vat/bank_recon_v2/bank_recon_v1)/ archive / rd / cost / exceptions / clients / billing / vat_recon 三表组 / **audit(操作日志)/ team(员工管理)(第二十三会话)**。
- **B2 范式不变**(见上一会话段)· 大块用字节级 PowerShell 提取(`$body = $lines[a..b] | %{ $_ -replace 'get_cursor\(','db.get_cursor(' }` + 拼 header)避免手抄 750 行出错。

---

**(历史)A3/A4**:第十会话(2026-05-24)· Zihao 拍板 **A3=本地 Docker / A4=Doppler** · 推进两项(commit `df727f6`):
- **A3** · Docker 三件套(Dockerfile + .dockerignore + docker-compose + docker-compose.dev)+ ADR-003 · 配置就绪 · prod 部署链未动 · **待 Zihao 装 Docker Desktop 跑 `docker compose build` 验证**(清单见 ADR-003)
- **A4** · Doppler 收拢完成 · 生产 **39 密钥导入 `prd`**(剔除 2 死代码 demo 密码)· 桌面明文已删 · ADR-004 列迁移 4 步进度

**下一个(A3/A4 收官 · 部分需 Zihao 手动)**:
- **A4 第 2 步**:Zihao 装 doppler CLI → 本地 `doppler run` 跑通(验证注入)
- **A3 验证**:Zihao 装 Docker Desktop → `docker compose build` + `up`(ADR-003 清单)
- **A4 第 3-4 步**:生产改从 Doppler 取(**碰红线 #16 · 走流程**)+ 清理旧密钥(删前备份)· 待本地验证后做
- **可并行**:不等 A3/A4 收官 · 直接开 **B 阶段**(后端拆 router · 依赖 A1/A5 已满足)或 **C 阶段**(前端拆 home.js → src/home/*)

**遗留小债**:demo 账号死代码(`db.py` `ensure_demo_account` · 老套餐模型 · 已登不上)· 归整顿 I2 · 待清理。

**A2.2** 等 B3 真迁第一条 ensure_* 时再做(已并入 B3)。

**A2.2 钩子并入 B3**(2026-05-22 决策):
- A2.1 装好 Alembic + 001 空 baseline 后 · 没真迁移之前 git-deploy.sh 加 `alembic upgrade head` 是 no-op
- 把 hook 加在"真要跑第一条迁移"时(= B3 第一个 ensure_* 迁 Alembic 时)· 降低风险 + 不空动 prod 部署链
- 同步 B3 入参:本任务 commit hash + 001_baseline 已就位 + env.py 读 DATABASE_URL 已配好

**REFACTOR-A1 4 子拆分(全 ✅)**
- A1.1 · 装 Vite + 配 esbuild · ✅ `e11e81d`(Vite 6.4.2 + 本地 build)
- A1.2 · CI 加 build step · ✅ `cfbb7d5`(ci.yml 加 vite build · 5 关守门)
- A1.3 · dashboard.js / billing.js 改 ES modules · ✅ `1c4c3bd`(git mv 到 src/home/ · Vite bundle · home.html 改 script · cache_bust ++ · release_notes v118.35.0.32 4 语)
- A1.4 · 验证 prod 全跑通 · ✅ 2026-05-22(/api/version 返 11835032 · /static/dist/main.js 15KB serve OK · 旧 /static/home/*.js 404 无害)

---

**本文档更新规则**:
- 每完成 1 个 task → 状态符号变 + 加完成日期 + commit hash(在对应 task 行)
- 每完成 1 个阶段 → 进度看板该阶段 ✅ + 出阶段报告
- 每月末 → 出月报到 `docs/refactor/monthly-YYYY-MM.md`
- 任何 task 估时偏差 > 50% → 在备注列说明原因
