# 👋 Pearnly · 新人上手指南(ONBOARDING)

> **整顿 REFACTOR-G3 · 2026-05-27 初版**
> 给**新来的人类协作者**看的第一天上手地图。看完这一份,就能把项目跑起来、知道东西放哪、知道改完怎么上线、知道整顿期能碰什么不能碰什么。
> 本文是导航 + 速查。权威细节以 `CLAUDE.md/CLAUDE.md`(项目宪法)为准,本文跟它冲突时**以宪法为准**。

---

## 1. Pearnly 是什么

Pearnly = 给**泰国会计事务所 + SME 老板**用的 AP(应付账款)自动化 SaaS。

- 一句话定位:**「不让用户换 ERP · 让 Pearnly 适配所有 ERP」**
- 强项:多语言 OCR(泰 / 中 / 日)+ 全管道自动化(LINE / 邮件 / 文件夹)+ ERP 中立中间件 + 一页多发票拆分
- 目标用户:泰国会计师 / 个体会计师 / SME 老板。判断一个功能值不值得做,标尺是:**能不能帮会计师省 1 个手动步骤**
- 4 语并重产品:**中 / 英 / 泰 / 日**都是真实产品语言(泰国是首发市场,默认泰语)。任何用户可见文字漏一语 = bug
- 线上地址:https://pearnly.com · 当前真实付费用户 1 个(mrerp@outlook.co.th)

---

## 2. 技术栈

| 层 | 用什么 |
|---|---|
| 后端 | Python(CI 跑 3.11 · black target py310/py311)· **FastAPI**(uvicorn `app:app`) |
| 数据库 | Supabase PostgreSQL(AWS ap-southeast-1)· 访问层 `db.py` + `services/<domain>/*.py` |
| 前端 | 原生 HTML/CSS/JS 起家,整顿期上 **Vite + ES modules**(新业务逻辑进 `src/home/*`) |
| OCR / AI | Gemini(多语言发票识别) |
| 集成 | MR.ERP(无 API · 走 Playwright)· Xero / FlowAccount(有 API) |
| 通知管道 | LINE Bot · Gmail SMTP(hello@pearnly.com) |
| 测试 | `unittest`(tests/unit · contract test)· Playwright(tests/e2e · 打 prod 着陆页) |
| CI | GitHub Actions(`.github/workflows/ci.yml` · lint job + test job 双轨) |
| 部署 | GitHub webhook → 服务器 `git pull` + 重启(详见 §5) |

---

## 3. 本地怎么跑起来

> 本地开发的权威环境变量模板是 `.env.example`(分区注释清楚哪些必填)。

```bash
# 1. 装 Python 依赖(锁文件更稳 · 与 CI / prod 一致)
python -m pip install --upgrade pip
pip install -r requirements.lock.txt
pip install -r requirements-dev.txt        # 本机另需 lint / 测试工具(black/ruff/coverage 等)

# 2. 装前端依赖(Vite build + Playwright 用)
npm ci

# 3. 配环境变量:复制模板,填值(.env.local 已被 .gitignore · 不会误提交)
cp .env.example .env.local
#   最小必填(否则跑不起来):DATABASE_URL · JWT_SECRET · PORT(默认 7860)· LOG_LEVEL
#   要跑 OCR / ERP / 邮件还需对应分区的 key — 见 .env.example 注释

# 4. 起后端(FastAPI · uvicorn)
uvicorn app:app --reload --port 7860       # 默认端口 7860(PORT 环境变量可改)

# 5.(前端有改动时)Vite build → 产物 static/dist/main.js
npm run build
```

打开 `http://localhost:7860`。生产真实密钥**不在仓库里**,只在生产 systemd 环境变量 / Doppler `prd`。本地缺某些 key 时对应功能(OCR / 推送 / 邮件)会降级或报错,核心页面仍可起。

> ⚠️ 注意:这是一个真实在线、带付费用户的系统。**不要拿本地配置连生产数据库改数据。**

---

## 4. 目录结构导览

完整文件地图见 `CONTRIBUTING.md` §项目文件地图;下面是最常摸到的:

```
pearnly_project/
├── CLAUDE.md/                  # 项目"大脑"目录(优先级最高)
│   ├── CLAUDE.md               #   ← 项目宪法 · 必读 · 25+ 条铁律
│   ├── STATE_PEARNLY.md        #   ← 当前状态 · 每个工作窗口结尾更新
│   ├── REFACTOR_MASTER_PLAN.md #   ← 整顿期主计划 · 单一权威源(9 阶段 A-I)
│   ├── TECH_DEBT.md / BACKLOG.md / MODULE_*.md  # 技术债 / 任务 / 模块路线
├── CONTRIBUTING.md             # 协作守则(人 + AI 都看)· 4 不许 + 提交前必跑
├── AGENTS.md                   # 给 AI 协作 agent 的约定
├── ONBOARDING.md               # 本文件
│
├── app.py                      # FastAPI 主入口(整顿期渐进瘦身 · 封死不许加新路由)
├── db.py                       # DB 访问层(封死 · 复杂业务搬 services/)
├── auth.py · auth_signup.py    # 鉴权 / 注册
├── *_routes.py                 # 已拆出的独立路由(billing/recon/erp/admin_*/me 等 30+ 个)
├── services/<domain>/*.py      # 业务 service 层(erp/recon/clients/billing/ocr/... DAL + 逻辑)
├── src/                        # ★ 新前端业务逻辑(Vite ES modules · main.js + home/*)
├── static/                     # 前端静态资源
│   ├── home.html · home.js · home.css   # 主 SPA(巨石 · 整顿期渐进拆分中)
│   ├── version-banner.js       #   独立 IIFE 小组件示范
│   ├── admin/                  #   admin SPA(独立 layout · 不引 home.js)
│   └── dist/main.js            #   Vite 构建产物
├── tests/{unit,e2e,integration}/   # 测试
├── scripts/                    # check_imports.py · check_i18n.py · refactor_progress.py
├── alembic/ · alembic.ini      # DB 迁移(整顿期激活中)
├── Dockerfile · docker-compose*.yml    # 本地容器(整顿 A3 · 配置就绪)
└── .github/workflows/ci.yml    # CI(lint + test 双 job)
```

**当前的 4 个"巨石"文件**(整顿期重点拆解对象,改起来要小心牵连):`home.js`(~3 万行)· `home.css` · `home.html` · `app.py` / `db.py`。**新功能严禁继续往里塞**(见 §6)。

---

## 5. 部署流程概览(指向 RUNBOOK)

Pearnly 用 **git webhook 自动部署 · 每次 push 即上线 · 没有 staging**:

```
git push origin master  →  GitHub webhook  →  服务器 git pull + cp static/ + 重启 mrpilot  →  ~15s 后 prod 生效
```

- 服务器:`root@45.76.53.194`(Vultr Tokyo · Ubuntu 24.04 · `/opt/mrpilot/`)· 进程 systemd unit `mrpilot`
- 本地 remote 名 `origin`,分支名 `master`(历史原因)
- 验证上线:`curl https://pearnly.com/api/version` 看 `cache_bust` 翻新
- **回滚用 `git revert`(新增反向 commit)· 绝不 `--force` / `reset --hard` 到 master**

> 📖 **部署 / 回滚 / CI 查看 / 健康检查 / 紧急排查(磁盘满血泪根因)完整操作手册 → [`docs/RUNBOOK.md`](docs/RUNBOOK.md)。出事先翻那里。**

---

## 6. 整顿期在做什么(指向 REFACTOR_MASTER_PLAN)

项目目前处于 **封锁整顿期(2026-05-22 起 · 约 5-8 个月)· 0 新功能开发**。目标:把工程标准化到 "Google / Anthropic 级 90%+"(每文件 100-500 行 · 50-100 个模块 · 测试覆盖 ≥ 70% · API p95 < 1s)。

整顿分 9 个阶段(A 工具链 → I 抛光),每个任务有唯一 ID(如 `REFACTOR-B1`)。

- ✅ **只做** `REFACTOR_MASTER_PLAN.md` 里的任务
- ❌ **禁止** 任何 `MODULE_ROADMAP.md` 新功能 / P0-VAT 主线 / Phase 6 进项管理 MVP
- ✅ 唯一例外:影响付费用户 / 数据安全 / 服务中断的紧急 BUG 修复

> 📖 **整顿主计划(单一权威源 · 进度看板 + 下一个 task)→ [`CLAUDE.md/REFACTOR_MASTER_PLAN.md`](CLAUDE.md/REFACTOR_MASTER_PLAN.md)。**

**新功能去哪里(铁律 #17 / #21 / #23 · 4 不许)**:
- 新后端路由 → 独立 `xxx_routes.py` + `app.include_router()`(不进 `app.py`)
- 新前端业务逻辑 → `src/home/*`(Vite ES module · 不进 `home.js`)
- 新 CSS → 独立 `.css` 或 scoped 组件(不进 `home.css`)
- 新业务 SQL → `services/<domain>/<feature>.py`(不进 `db.py` 尾部)· 新 schema 走 Alembic(不加 `ensure_*`)

---

## 7. 必读的铁律摘要(指向 CLAUDE.md)

`CLAUDE.md/CLAUDE.md` 是项目宪法(25+ 条铁律)。第一天至少把下面这些记住:

| 主题 | 一句话 | 铁律 |
|---|---|---|
| **4 语 i18n** | 任何用户可见文字必须 zh/en/th/ja 全 · 漏一个=bug · 提交前跑 `check_i18n.py` | i18n 史上最严 |
| **修一类不修一处** | 改 bug 前先 grep 同类 pattern · 一次性全修 · 不留尾巴 | #1 |
| **巨石封死** | 新路由/前端逻辑/CSS/业务SQL 都不许进 app.py/home.js/home.css/db.py | #17 #21 #23 |
| **0 新功能** | 整顿期只做 REFACTOR 任务 · 想做新功能先停下确认 | #18 |
| **commit 带 task ID** | 整顿期 commit message 必含 `REFACTOR-<task-id>` | #20 |
| **开工先 check master** | 每窗口先 `git branch --show-current` · 不在 master 就切回去 | #14 |
| **push 红线** | `--force` / `reset --hard` / 删 branch / DROP / 改登录计费OCR大改 → 先问 | #16 |
| **删后端字段** | 同步改 Pydantic `response_model` · 删字段先 Optional 一版再真删 | #15 |
| **报 500 先查磁盘** | 上传/对账 500 + `Unexpected token '<'` → 第一反应 `df -h /` | #24 |
| **不靠 sync mock 蒙** | async 路由要真 async 测试;改 bug 自己端到端测到 PASS | #10 #13 #25 |
| **图标 / 沟通** | 只用 SVG line 图标(禁 emoji 当图标)· 对 Zihao 默认沉默、大白话 | UI / 沟通 |

> 📖 完整 25+ 条 → [`CLAUDE.md/CLAUDE.md`](CLAUDE.md/CLAUDE.md)。每次开工前应完整读一遍。

---

## 8. 提交前必跑的 6 道守门

push 前本机全绿才提交(CI 也跑同样的检查,不绿合不进):

```bash
npm run format:check                               # 1) prettier 格式 → 全绿
python -m unittest discover -s tests/unit -p "test_*.py"   # 2) 全量单元 / contract 测试 → all OK
python scripts/check_imports.py --quiet            # 3) 静态 import 检查 → EXIT 0
python scripts/check_i18n.py --strict              # 4) i18n 4 语完整性 → 0 missing 0 extra
node --check <changed.js>                          # 5) 改了 JS 时 · 各改动文件都过
npm run build                                      # 6) Vite 构建通过(改了前端时)
npx playwright test                                # (按需 E2E)改了 login.html / 顶栏 / 4 语切换 / 核心路径时必跑
```

commit message 格式(整顿期):

```
<type>(<scope>): <subject> · REFACTOR-<task-id>

<body 说改了什么 · 为啥 · 怎么验证>

守门 6 道全绿:format / unit / imports / i18n / node / build
```

---

## 9. 第一天该做什么(建议顺序)

1. **读三份核心文档**:`CLAUDE.md/CLAUDE.md`(宪法)→ `CLAUDE.md/STATE_PEARNLY.md`(当前状态)→ `CLAUDE.md/REFACTOR_MASTER_PLAN.md`(整顿主计划 · 看"当前进度看板")。
2. **把项目在本地跑起来**(§3),打开 `http://localhost:7860` 确认能看到登录 / 主页面。
3. **跑一遍 6 道守门**(§8),确认本机环境干净、测试全绿 —— 这是你后续每次提交的基线。
4. **跑一次整顿进度脚本**熟悉度量口径:`python scripts/refactor_progress.py`(输出各巨石行数 / 测试数 / 模块数 / 达标进度 %)。
5. **翻一遍 `docs/README.md`**(40+ 文档索引)+ `CONTRIBUTING.md`,知道遇到具体问题去哪查。
6. **找一个 `REFACTOR_MASTER_PLAN.md` 进度看板里"进行中"或下一个待启动的小任务**(中等粒度,如抽一个 router / 补一个模块测试)上手 —— **不要**第一天就动登录 / 计费 / OCR 热路径等高敏区(那些要在 Zihao 在场时单独做)。
7. **提交前对照 §8 六道守门 + §7 铁律摘要**,commit message 带上 `REFACTOR-<task-id>`。

---

*配套文档:`CLAUDE.md/CLAUDE.md`(宪法)· `CLAUDE.md/REFACTOR_MASTER_PLAN.md`(整顿主计划)· `CONTRIBUTING.md`(协作守则)· `docs/RUNBOOK.md`(运维手册)· `docs/README.md`(文档索引)。*
