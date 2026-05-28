# 🚀 Pearnly · Onboarding(新协作者 + 新 AI 窗口入门)

> 适用对象:① 新人类协作者(开发 / 测试 / 翻译 / 设计)② 新 AI 窗口(Claude / Codex / Copilot)③ 任何时隔 > 1 周回来的旧人 — 接力前 10 分钟读完本文,就能"接住"项目。
>
> 编写于:2026-05-28 · 窗口 C(REFACTOR-WC-P2 / G3)· 与 `CONTRIBUTING.md` 互补(本文是 quickstart · CONTRIBUTING 是详规)。

---

## 0. 30 秒电梯介绍

**Pearnly** = 泰国会计师 + SME 老板的 AP 自动化 SaaS · 4 语(zh / en / th / ja)。
- 🌐 Live:https://pearnly.com
- 🧠 大脑:`CLAUDE.md/CLAUDE.md`(项目宪法 · 28 条铁律)
- 📊 当前状态:`CLAUDE.md/STATE_PEARNLY.md`(每窗口收尾必更新)
- 🏗️ 整顿期:2026-05-22 起 · 5-8 个月 · **0 新功能** · 只做工程标准化(主计划 `CLAUDE.md/REFACTOR_MASTER_PLAN.md`)

---

## 1. 第一次开窗口 · 60 秒 checklist

```
[ ] git branch --show-current → master(铁律 #14)
[ ] cat CLAUDE.md/CLAUDE.md(全读完 · 28 铁律是项目宪法)
[ ] cat CLAUDE.md/STATE_PEARNLY.md 头部 50 行("整顿模式 ON" 段)
[ ] cat CLAUDE.md/REFACTOR_MASTER_PLAN.md(看"当前进度看板" + "下一个 task")
[ ] python scripts/refactor_progress.py(看综合进度 % · 数字没动 = 上窗口没干活)
```

读完 → 找当前要做的 task → 干 → 6 道门 → push → 更新 STATE。

---

## 2. 必读 4 文档(铁律 #19 接力 protocol)

| 顺序 | 文件 | 看什么 |
|---|---|---|
| 1 | `CLAUDE.md/CLAUDE.md` | 项目宪法 · 28 条铁律 · 至少看完铁律 #18-#28 |
| 2 | `CLAUDE.md/STATE_PEARNLY.md` 头部 | "下个窗口立即接手"段 + 当前 commit hash + 数字 |
| 3 | `CLAUDE.md/REFACTOR_MASTER_PLAN.md` | 整顿主计划 · 单一权威源 · 看"当前进度看板" |
| 4 | 当前 task 对应段 | 主计划里 task 行的"完成判定" |

**漏读后果**:
- 漏 #1 → 违反铁律 #17(新东西塞巨石)、#27(防屎山闸)、#28(新功能 4 问)
- 漏 #2 → 重复做上窗口已完成的工作
- 漏 #3 → 不知道下一个 task 是什么 · 自由发挥
- 漏 #4 → 做完判不出"是否合格"

---

## 3. 核心目录结构

```
D:\Users\Skin\Desktop\pearnly_project\
├── CLAUDE.md\                        ← 项目大脑(目录名带 .md 是历史命名)
│   ├── CLAUDE.md                     ← 项目宪法(28 铁律 · 必读)
│   ├── STATE_PEARNLY.md              ← 当前状态(每窗口收尾必更新)
│   ├── REFACTOR_MASTER_PLAN.md       ← 整顿主计划(60+ task · 9 阶段 A-I)
│   ├── BACKLOG.md / TECH_DEBT.md     ← 任务清单 / 技术债清单
│   ├── MODULE_*.md / NAV_IA_PRD.md   ← 模块 PRD(整顿期不做新模块)
│   ├── DESIGN_SYSTEM.md              ← UI 设计规范
│   └── CODEX_COLLAB_RULES.md         ← Codex 协作分流规则
├── app.py · auth_signup.py · db.py   ← 后端巨石(整顿期拆中 · 不许新增)
├── home.html · home.js · home.css    ← 前端巨石(整顿期拆中 · 不许新增)
├── login.html                        ← 登录着陆页
├── *_routes.py                       ← 整顿期 B 阶段拆出的 FastAPI router
├── services/                         ← 整顿期 B 阶段拆出的业务层
│   ├── auth/{user_lookup,password,account_merge}/
│   ├── billing/{charge,account_status,credits_schema,pricing}/
│   ├── erp/ · ocr/ · ocr_history/ · clients/ · ...
├── src/home/                         ← 整顿期 C 阶段拆出的 Vite ES 模块
├── tests/
│   ├── unit/                         ← 1600+ unittest(`python -m unittest discover -s tests/unit`)
│   ├── integration/                  ← API + 真 DB + Mock 外部
│   ├── e2e/                          ← Playwright 17 spec(真账号 · 兜底高敏)
│   └── visual/                       ← 视觉回归(Playwright screenshot baseline · 窗口 C 新加)
├── docs/
│   ├── ONBOARDING.md                 ← 本文件
│   ├── RUNBOOK.md                    ← 运维手册
│   ├── openapi.md                    ← API 索引(窗口 C 新加)
│   ├── refactor/                     ← ADR 决策文档
│   ├── audits/ · integrations/       ← 审计 / 集成专题
│   └── ...
├── scripts/
│   ├── check_imports.py              ← 静态 import 检查(6 道门 #3)
│   ├── check_i18n.py                 ← 4 语 i18n 完整性(6 道门 #4)
│   ├── check_file_size.py            ← 防屎山闸 #1(铁律 #27.1 · 窗口 C)
│   ├── check_line_ratchet.py         ← 防屎山闸 #2(铁律 #27.2 · 窗口 C)
│   └── refactor_progress.py          ← 整顿进度统计
├── .github/
│   ├── workflows/ci.yml              ← CI(lint + test + e2e + lint-size)
│   ├── PULL_REQUEST_TEMPLATE.md      ← PR 自检
│   ├── ISSUE_TEMPLATE/{bug,feature,question}.md
│   └── CODEOWNERS                    ← 敏感路径标记(窗口 C 新加)
├── playwright.config.js              ← E2E 主配置(testDir: ./tests/e2e)
├── package.json / vite.config.mjs    ← 前端构建
├── pyproject.toml / requirements*.txt ← Python 依赖 / black / ruff / coverage
└── alembic.ini · alembic/            ← 数据库迁移
```

---

## 4. 6 道门(每个 commit push 前必跑)

```bash
# 1. 格式
black --check .
ruff check .

# 2. 单测全量(1600+ 测试 · ≤ 60s)
python -m unittest discover -s tests/unit -p "test_*.py"

# 3. 静态 import
python scripts/check_imports.py --quiet

# 4. 4 语 i18n(0 missing 0 extra)
python scripts/check_i18n.py --strict --quiet

# 5. Vite build
npm run build

# 6. 改了 JS 才跑
node --check <changed.js>
```

全绿才 push。任意一个红:**不许 push** → 修了再来。

---

## 5. Commit / Push 规范(铁律 #14 / #16 / #20 / #27)

**Commit message 格式**(整顿期 commit 必含 task ID):
```
<type>(<scope>): <subject> · REFACTOR-<task-id>

<body 说改了什么 · 为啥 · 怎么验证>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**type 取值**:`feat` / `fix` / `refactor` / `test` / `chore` / `docs` / `hotfix`(整顿期允许的紧急 BUG 修复 · 不带 REFACTOR-id)

**Push**:
- 必先 `git branch --show-current` → 在 master(铁律 #14)
- `git push origin master`(显式 master · 不是当前 branch)
- 不许 `--force` / `--no-verify`(红线 · 必问 Zihao)
- Push 后:`gh run watch <id> --exit-status --repo skin306152-star/pearnly-app` 独立查 CI 真绿(不只信本地)
- 红即 `git revert HEAD` + 单独 push,**绝不留红**

---

## 6. 整顿期硬约束(铁律 #18 / #23 / #27)

**8 条硬门槛**(REFACTOR_MASTER_PLAN.md 顶部"🔒 8 条硬门槛"):
1. `app.py` 封死(新路由必须 `*_routes.py`)
2. `db.py` 封死(新 schema 必须 Alembic)
3. `home.js` 封死(新前端必须 `src/home/*`)
4. 每拆一个模块必带 ≥ 1 测试
5. 每个核心业务路径 ≥ 1 E2E / integration
6. coverage 棘轮(月度只升不降)
7. `/ready` 必须能真实失败
8. `refactor_progress.py` 不许造假

**铁律 #27 防屎山 4 条**(2026-05-28 新):
1. 监控代码文件 ≤ 500 行(`scripts/check_file_size.py`)
2. 监控文件行数 commit 净增长 ≤ 0(`scripts/check_line_ratchet.py`)
3. 新功能必带独立文件 + ≥ 1 测试
4. 替换旧实现必须同 PR 删旧代码(不许两套并存)

**铁律 #28 新功能 4 问**(写代码前):
1. 这是什么领域?(billing / auth / OCR / ...)
2. 新建什么文件?(确切路径)
3. 测试在哪?(确切路径 + 用例名)
4. 删什么旧文件?(N/A 或 git rm 列表)

---

## 7. 高敏区(铁律 #26)

**🔴 不许无人值守动**(必须 Zihao 在场):
- `auth.py` / `auth_signup.py` / `*auth*_routes.py`
- `billing_routes.py` / `services/billing/charge.py` / `db.py` 钱写入
- `line_binding_routes.py` / `line_client.py`
- `app.py` 的 OCR `/recognize` 路由
- `home.js` 的 plans-plg-line / password-change / line-email-modal / session-heartbeat 块
- RLS 基础设施(`get_cursor_rls` 等)— **永远勿动**

**🟢 安全区**:文案 / i18n / CSS / 普通业务 / 测试 / 文档 / 依赖绿 PR — 无人值守可全自动。

例外:自主 BC 拆搬删 Loop 可碰高敏(`docs/refactor/AUTONOMOUS_LOOP.md`)· 用 4 条安全替身(纯结构 / 真账号 E2E / 失败自动回滚 / 永不真付)。

---

## 8. 真账号 E2E(本地跑)

环境变量(已在 HKCU `setx`):
```powershell
# 本会话桥接(claude-code 子进程不继承 setx · 每次跑必桥接)
$env:PEARNLY_E2E_USER = [Environment]::GetEnvironmentVariable('PEARNLY_E2E_USER','User')
$env:PEARNLY_E2E_PASS = [Environment]::GetEnvironmentVariable('PEARNLY_E2E_PASS','User')
# 跑 spec 11 / 12 还需要 ADMIN_USER / ADMIN_PASS
```

**硬线**:绝不 commit / 打印 / 写文件 / 推到日志。E2E 跑完:`rm tests/e2e/.auth/state.json`(含 token)。

---

## 9. CI 状态查询(铁律 #22)

```powershell
# 列最近 5 个 master CI run
& "C:\Program Files\GitHub CLI\gh.exe" run list --repo skin306152-star/pearnly-app --branch master --limit 5

# 等某 run 完成(独立查 · 不只信本地)
& "C:\Program Files\GitHub CLI\gh.exe" run watch <RUN_ID> --exit-status --repo skin306152-star/pearnly-app

# 查失败 step 日志
& "C:\Program Files\GitHub CLI\gh.exe" run view <RUN_ID> --repo skin306152-star/pearnly-app --log-failed
```

---

## 10. 接力收尾必更新

每个窗口收尾必须:
1. **更新 `CLAUDE.md/STATE_PEARNLY.md` 头部**:本窗口完成的 task + commit hash + 数字变化
2. **更新 `CLAUDE.md/REFACTOR_MASTER_PLAN.md` 进度看板**:对应 task 待 → 做中 → 已完成
3. **跑 `python scripts/refactor_progress.py`**:确认综合进度 % 真涨了(没涨 = 没干活)
4. 写一句话给下个窗口:"下一步建议做 X · 在哪里 · 注意什么"

---

## 11. 常见 FAQ

**Q: 我能加新功能吗?**
A: 整顿期(2026-05-22 起约 5-8 个月)**0 新功能**(铁律 #18)。例外:紧急 BUG 修复(影响付费用户)用 `hotfix:` 前缀。

**Q: 我能改 home.js / app.py / db.py 加新代码吗?**
A: 不行(铁律 #17 / #21 / #23 / #27)。新路由 → `*_routes.py`。新业务 → `services/<域>/`。新前端 → `src/home/<feature>/`。

**Q: 我改了 docs/ 还要跑全套 6 道门吗?**
A: 改纯 docs/ 可只跑 black + ruff + check_imports(快)· 但 push 前还是 5 关都跑一次稳妥。CI 会跑完整套,所以本地省了 CI 也会抓。

**Q: 真账号 E2E 凭据怎么拿?**
A: 跟 Zihao 要(普通非超管邮箱+密码)· 只设 env 不打印不入 git · 跑完删 `.auth/state.json`。

**Q: PR / commit 没带 `REFACTOR-<task-id>` 算违规吗?**
A: 整顿期是的(铁律 #20)· 月末 Zihao grep 抓不到 task ID 的 commit 单独看。

**Q: 我能直接 push 到 master 吗?**
A: 可以(铁律 #16 · C 档位全自动授权)· 但触发"红线"任一条必须停下问 Zihao(force push / reset hard / 30+ 文件改动 / 删表 / 关键路径大改)。

**Q: 我跑测试一直 fail 怎么办?**
A: 先看是不是环境问题(Python 3.10 vs 3.11 · npm ci · pip install -r requirements-dev.txt)。再看是不是数据库问题(`docker compose up` · 或 stub fixture)。最后看是不是真 bug(grep 同类 / 重现 / 守门 + 修)。

---

## 12. 紧急联系 / 关键资源

| 项 | 值 |
|---|---|
| 域名 | https://pearnly.com |
| Repo | https://github.com/skin306152-star/pearnly-app(私库) |
| 服务器 | root@45.76.53.194(Vultr Tokyo · 免密 SSH) |
| 数据库 | Supabase PostgreSQL · AWS ap-southeast-1 |
| 邮件 | hello@pearnly.com(Gmail SMTP) |
| LINE Bot | @059oupmg(Channel ID 2010022630) |
| 部署 | git push origin master → webhook 自动部署 · ~15s 后 `/api/version` 可验 |
| 1 真实付费用户 | mrerp@outlook.co.th(MR.ERP · 维护时绝不动其余额) |

---

## 13. 5 道核心信条(背下来 = 不会出错)

1. **Zihao 是产品经理 · 不是工程师** → 说大白话
2. **默认沉默** → 除非影响产品/用户/未来,否则别主动喷
3. **部署完核心场景必测** → 项数不限 · 每项 ≤30 秒能验完 · 不要科普
4. **能自动跑的不要让 Zihao 手动** → scp/ssh/验证/清理全自己来
5. **关键词触发收尾** → 自动更新文档 → 报"可以关窗口了"

---

**下一步**:回到主计划找下个 task,开干 → 6 道门 → push → 更新 STATE。
