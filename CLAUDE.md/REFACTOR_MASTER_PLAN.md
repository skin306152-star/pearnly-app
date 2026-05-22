# 🏗️ Pearnly · 整顿期主计划(REFACTOR_MASTER_PLAN)

> **起源**:2026-05-22 Zihao 拍板"封锁整顿 5-8 个月 · 路径 B 上 Vite · 不开发任何新功能 · 把项目工程标准化到 Google / Anthropic Claude code 级"
>
> **状态**:整顿模式 ON · 0 新功能 · 仅整顿
>
> **目标**:6-8 个月后 Pearnly 跟主流 SaaS 看齐 · "Google 级标准 90%+"(每个文件 100-500 行 · 50-100 个模块文件 · 测试覆盖 70%+ · 性能 p95 < 1s · 真到位)
>
> **本文档是整顿期单一权威源** · 所有接力 agent 进窗口必读

---

## 🚨 接力 agent 必读(开窗口前 60 秒)

**整顿期(2026-05-22 起到约 2026-12)铁律**:

1. **0 新功能开发**(铁律 #18)· 你 grep `MODULE_ROADMAP.md` 想做新功能 → 立即停 · 跟 Zihao 确认
2. **必读 4 文档**(铁律 #19)· 顺序:
   - `CLAUDE.md/CLAUDE.md`(项目宪法 · 20 条铁律)
   - `CLAUDE.md/STATE_PEARNLY.md`(当前状态 · 看头部"整顿模式 ON" 段)
   - **本文档**(整顿主计划 · 看"当前进度看板" + "下一个 task")
   - 当前 task 的"完成判定"段
3. **commit message 必含 task ID**(铁律 #20)· 格式 `<type>(<scope>): <subject> · REFACTOR-<task-id>` · 比如 `refactor(frontend): 抽 settings.js · REFACTOR-C12`
4. **5 道守门必跑全绿才能 push**(原有铁律 · 整顿期强化):
   - `python scripts/check_imports.py --quiet` → EXIT 0
   - `python scripts/check_i18n.py --strict` → 0 missing 0 extra
   - `python -m unittest discover -s tests/unit` → all OK
   - `npx playwright test` → all passed
   - `node --check <changed.js>` → 各改动 JS 都过
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

## 🧭 路径选择(2026-05-22 Zihao 拍板)

| 路径 | 说明 | 选择 |
|---|---|---|
| L1 推倒重写 | 整个项目重写 | ❌ |
| L2 换技术栈 | FastAPI → Django / vanilla → React | ❌ |
| **L3 内部整顿 + 路径 B** | 保留 FastAPI + 上 Vite + ES modules · 内部结构标准化 | ✅ **选这个** |

**为啥**:
- 有 1 真实付费用户(mrerp@outlook.co.th)· L1/L2 业务停 2-3 月不可接受
- 17 条铁律 + 守门测试 + 文档已立 · 推倒等于重做
- L3 + Vite 能到 Google 级 90% · 时间 4-6 月可控

---

## 📊 完成定义("Google 级 90%" 具体度量)

整顿期结束的硬指标(全部达标才算完成):

### 代码规模(7 项)

| 文件 | 当前(2026-05-22) | 目标 | 备注 |
|---|---|---|---|
| `home.js` | 33,251 行 | < 200 行(入口 + bootstrap) | 业务逻辑全拆到 `static/home/*` 50-100 个模块 |
| `app.py` | 9,212 行 | < 500 行(init + middleware) | 业务路由全拆到 20-30 个 `*_routes.py` |
| `db.py` | **9,255 行** | < 500 行(cursor + pool + 框架) | 业务 SQL 迁到 `services/<domain>/<feature>.py` · 实际比估的大 2 倍 |
| `home.css` | **16,124 行** | < 500 行(变量 + reset) | component CSS 拆 20-30 个 · 实际比估的大 2 倍 |
| `home.html` | 6,568 行 | < 1,000 行 | 组件化或服务端拼接 |
| 模块文件数 | ~10 | 50-100 个 `static/home/*.js` + 20-30 个 `*_routes.py` + 10+ `services/*.py` + 20-30 component CSS | "Google 级"标志 |
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
| A1 | Vite + ES modules 落地(装包 + 配 esbuild + CI 加 build step + 把已抽 dashboard.js/billing.js 改 ES modules) | 1-2 天 | A0 | ⚪ 待启动 |
| A2 | Alembic 落地(装包 + `env.py` + 001 试点迁移 + git-deploy.sh 钩子) | 2.5h | A0 | ⚪ 待启动 |
| A3 | 环境分级(prod / staging / dev 三套 · Docker 本地或 Vultr 第二台) | 1-2 天 | A0 | ⚪ |
| A4 | Secrets 管理(`.env` → Doppler 或 1Password Secrets · 给多人协作铺垫) | 2-3 天 | A3 | ⚪ |
| A5 | CI 加 lint + format(black + ruff + ESLint + Prettier) | 半天 | A0 | ⚪ |
| A6 | CI 加安全扫描(bandit + safety + npm audit) | 半天 | A5 | ⚪ |
| A7 | 依赖锁定(`requirements.lock.txt` pip-tools) | 1-2h | A0 | ⚪ |
| A8 | Code Coverage(pytest-cov + 上传 codecov · baseline) | 半天 | A5 | ⚪ |
| A9 | Dependabot / Renovate 配置(自动 PR 升级依赖 · 每周一开) | 1h | A0 | ⚪ |

**A 阶段完成判定**:Vite 跑通 / Alembic 迁过 001 / staging 能 deploy / CI 加了 lint+安全扫描 / requirements.lock 已生成 / Dependabot 跑过一次

---

### 阶段 B · 后端整顿(1-1.5 个月 · 可跟 C 并行)

| ID | 任务 | 估时 | 依赖 | 状态 |
|---|---|---|---|---|
| B1 | `app.py` 拆完 9k → < 500 行(20-30 个 router) | 4-6 周 | A1, A5 | ⚪ |
| B2 | `db.py` 拆完 4k → < 500 行(业务 SQL 迁 `services/`) | 3-4 周 | A1 | ⚪ |
| B3 | 所有 `ensure_*` 迁 Alembic(25 个 · schema 完全版本化) | 3-4 周 | A2 | ⚪ |
| B4 | 健康检查端点 `/health` + `/ready`(DB / Gemini / SMTP / LINE 各 check) | 半天 | — | ⚪ |
| B5 | API 全局限流(每 IP / 每用户 / 每 endpoint · 比现有 PLG 反薅闸更全) | 1-2 天 | — | ⚪ |
| B6 | 结构化日志(logger 改 JSON · 加 request_id / user_id / tenant_id 全链路 trace) | 2-3 天 | — | ⚪ |
| B7 | 错误日志聚合(自建简单版 · 写 `errors` 表 + admin 后台时间线 · 不上 Sentry) | 2-3 天 | B6 | ⚪ |
| B8 | 多租户 RLS 双保险(Supabase Row Level Security · DB 层强制) | 1-2 周 | B3 | ⚪ |
| B9 | DB 索引审计(EXPLAIN 慢查询 · 加缺索引 · 删没用的) | 2-3 天 | — | ⚪ |
| B10 | DB 连接池调优(psycopg2 pool size + lifecycle) | 半天 | — | ⚪ |

**B 阶段完成判定**:`app.py` < 500 行 / `db.py` < 500 行 / 25 个 ensure_* 全迁 Alembic / 4 个新端点端 + RLS / 9 个新机制全上线

---

### 阶段 C · 前端整顿(2-3 个月 · 最大头 · 可跟 B 并行)

| ID | 任务 | 估时 | 依赖 | 状态 |
|---|---|---|---|---|
| C1 | `home.js` 拆完 33k → < 200 行(50-100 个 ES module · 每个 100-300 行) | 6-8 周 | A1 | 🟡 部分(已抽 dashboard + billing) |
| C2 | `home.css` 拆完 7k → < 500 行(20-30 个 component CSS) | 2-3 周 | A1 | ⚪ |
| C3 | `home.html` 拆 6.5k → < 1000 行(`<template>` 或服务端拼接) | 2 周 | C1 | ⚪ |
| C4 | Design System / 组件库(按钮 / 输入框 / Modal / Toast / Card / Table 抽通用 component) | 3-4 周 | C1 | ⚪ |
| C5 | TypeScript 化前端(vanilla JS → TS · 80%+) | 4-6 周 · 跟 C1 并行 | A1 | ⚪ |
| C6 | i18n 拆 .json(home.js 4 个翻译块各 2324 keys → `i18n/<lang>.json` + 按模块再拆) | 1-2 周 | C1 | ⚪ |
| C7 | 可访问性 a11y(WCAG 2.1 AA · 屏幕阅读器 / 键盘导航 / 对比度) | 2-3 周 | C4 | ⚪ |
| C8 | 移动端真适配(iPhone / Pixel 真测 · 触控目标 / 字号 / 横滚动) | 1-2 周 | C2 | ⚪ |

**C 阶段完成判定**:`home.js` < 200 行 / `home.css` < 500 行 / `home.html` < 1000 行 / Design System 至少 8 个通用 component / TS 化 80%+ / i18n 拆到 .json / a11y AA / 移动端 4 浏览器全测过

---

### 阶段 D · 测试覆盖(1-1.5 个月 · 跟 B/C 并行)

| ID | 任务 | 估时 | 依赖 | 状态 |
|---|---|---|---|---|
| D1 | 10 个核心 E2E(登录 / 注册 / 上传 OCR / 销项税核查 / 收入对账 / ERP 推送 / 充值 / 客户 CRUD / 异常处理 / 4 语切换) | 4-6 周 | A1 | 🟡 1/10(已有着陆页) |
| D2 | Integration tests(API + 真 DB + Mock 外部服务 Gemini / LINE / Gmail) | 2-3 周 | A1 | ⚪ |
| D3 | 死灰复燃守门(Zihao 给清单 · 每条加 1 个守门测试 · 复活即 CI 红) | 1 周 + Zihao 清单 | — | ⚪ 等清单 |
| D4 | 测试覆盖率达 70%(pytest-cov 报告) | 持续 | D1, D2 | ⚪ |
| D5 | Visual regression(Playwright screenshot diff · 防 UI 改一处炸另一处) | 1-2 周 | D1 | ⚪ |

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
| G1 | ADR(10+ 重要决策留文 · 给未来 AI 看) | 1 周 | — | ⚪ |
| G2 | RUNBOOK(部署 / 回滚 / 紧急排查 / 数据恢复 / 服务挂了怎么办) | 1 周 | — | ⚪ |
| G3 | ONBOARDING.md(给真人协作者) | 半天 | — | ⚪ |
| G4 | OpenAPI / Swagger(完善 schema · 公开 `/docs`) | 半天 | B1 | ⚪ |
| G5 | PR / Issue 模板(`.github/PULL_REQUEST_TEMPLATE.md`) | 1h | — | ⚪ |
| G6 | CHANGELOG 自动生成(git-cliff 类 · 从 commit message 出) | 半天 | — | ⚪ |
| G7 | CODEOWNERS(GitHub 标记 · 防误改) | 1h | — | ⚪ |

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
| I2 | 死代码清完(grep `@deprecated` / `老版本` / `备用` · `git rm` 真删) | 1 周 | C1, B1 | ⚪ |
| I3 | 性能再 review(E 阶段后再扫一遍 · 找漏的) | 半天 | E | ⚪ |
| I4 | 文档完整 review(docs/ 全索引 + 现状标签) | 1 周 | G | ⚪ |
| I5 | 最后一次大体检(让别的 AI 跑 · 跟 2026-05-21 那次对比) | 1 周 | A-H 完成 | ⚪ |

**I 阶段完成判定**:0 silent block / 0 死代码 / 体检报告显示"Google 级 90%+"达标

---

## 📋 当前进度看板(每窗口收尾必更新)

> 状态符号:⚪ 待启动 · 🟡 进行中 · ✅ 已完成 · ⏸️ 已跳过 · ❌ 取消

| 阶段 | 完成度 | 当前 task | 备注 |
|---|---|---|---|
| **A 工具链** | 🟡 1/10 | A0 ✅(`613ea23`)· A1 待启动 | 主计划落档完成 · 下一步装 Vite |
| B 后端 | ⚪ 0/10 | — | 依赖 A1, A5 |
| C 前端 | 🟡 1/8(部分 C1) | — | 依赖 A1 · C1 已抽 dashboard + billing |
| D 测试 | 🟡 1/5(部分 D1) | — | 依赖 A1 |
| E 性能 | ⚪ 0/6 | — | 依赖 B6 + D1 |
| F 数据 | ⚪ 0/3 | — | 依赖 B1 |
| G 文档 | ⚪ 0/7 | — | 随时做 · 不阻塞 |
| H 合规 | ⚪ 0/6 | — | 靠后 |
| I 抛光 | 🟡 1/5(部分 I1) | — | 依赖 A-H · I1 已清 30/52 |

**累计 task 数**:60 主 task · 已完成约 4 个 + 进行中约 3 个 · 待启动 53 个

**当前累积成果**(从 2026-05-21 EXECUTION_PLAN 开始):
- `app.py` 10,060 → 9,211 行(减 849 · 阶段 5 后端拆 router)
- `home.js` 33,768 → 33,251 行(减 517 · 阶段 7 抽 dashboard + billing)
- 守门测试:0 → 293 unit + 1 E2E + 4 step CI 全绿

---

## 🔄 接力 protocol(每窗口必走)

### 开窗口(60 秒)

```
1. 读 CLAUDE.md/CLAUDE.md(项目宪法)— 重点看顶部 20 条铁律
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
1. 跑 5 道守门:
   python scripts/check_imports.py --quiet
   python scripts/check_i18n.py --strict
   python -m unittest discover -s tests/unit
   npx playwright test
   node --check <changed.js>  # 若改了 JS
2. 全绿才 commit
3. commit message:
   <type>(<scope>): <subject> · REFACTOR-<task-id>
   
   <body>
   
   守门 5 道全绿:imports/i18n/unit/playwright/node
   
   Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
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
| CI 5 道守门 | 已落 | 跑红 = push 不上 |
| 每月末必出月报 | 模板 + cron 提醒(可选) | 没月报 = Zihao 主动问 |

---

## 🎯 完成定义快速 check(整顿期结束时跑)

```
# 代码规模 7 项
[ ] home.js < 200 行
[ ] app.py < 500 行
[ ] db.py < 500 行
[ ] home.css < 500 行
[ ] home.html < 1000 行
[ ] 模块文件数 ≥ 100(50+ static/home/*.js + 20+ *_routes.py + 10+ services/ + 20+ component CSS)
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
│   ├── CLAUDE.md              ← 项目宪法 · 20 条铁律(18-20 整顿期)
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

## 🚀 下一个 task

**当前**:REFACTOR-A0 ✅ 完成(`613ea23` · 2026-05-22)

**下一个**:REFACTOR-A1 · Vite + ES modules 落地(1-2 天 · 2-4 个窗口)

**子拆分**(给下下个窗口看):
- A1.1 · 装 Vite + 配 esbuild · 半天 · 1 窗口
- A1.2 · CI 加 build step · 1h · 同 1 窗口
- A1.3 · 现有 dashboard.js / billing.js 改 ES modules · 半天 · 1 窗口
- A1.4 · 验证 prod 全跑通 · 半天 · 1 窗口

---

**本文档更新规则**:
- 每完成 1 个 task → 状态符号变 + 加完成日期 + commit hash(在对应 task 行)
- 每完成 1 个阶段 → 进度看板该阶段 ✅ + 出阶段报告
- 每月末 → 出月报到 `docs/refactor/monthly-YYYY-MM.md`
- 任何 task 估时偏差 > 50% → 在备注列说明原因
