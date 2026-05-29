# 🔀 3 窗口并行 Loop 派工(PARALLEL_LOOP_DISPATCH)

> **怎么用**:开 3 个新 Claude Code 窗口(确认 Opus 4.8)→ 每个窗口粘对应的「Loop 指令」整段 → Shift+Tab 切 auto-accept → 各自跑。
> **上级权威**:`docs/refactor/adr-011-parallel-loop-strategy.md`(分工 + 文件 ownership + 协调机制)· `CLAUDE.md/CLAUDE.md` 铁律 #26(自主 loop 高敏例外)。
> **跟 `AUTONOMOUS_LOOP.md` 的区别**:那份是**单窗口**跑全部(B/C 全含高敏,会自我串行);本份是**3 窗口并行**,按文件 ownership 切 A/B/C 互不撞车,速度 ≈ 2.5x。
> 最后更新:2026-05-29(Opus 4.8 1M · 守门 6 道 · 全自主含高敏 + E2E 闸 + 自动回滚)

---

## 0. 三窗口文件 ownership(防 merge 冲突 · ADR-011 §4.1)

| 窗口 | 只碰 | 绝不碰 | 当前任务 |
|---|---|---|---|
| **A 后端** | `app.py` `db.py` `*_routes.py` `services/**/*.py` | `home.*` `src/home/**` `tests/visual/` | B2 db.py 819→<500 + B1 app.py 3286→<500 |
| **B 前端** | `home.js` `home.html` `home.css` `src/home/**` `src/main.js` `vite.config.*` | `*.py` `services/` | C1 home.js 6190→<200 + C3 home.html 4410→<1000 |
| **C 文档测试** | `docs/**` `CLAUDE.md/*.md` `.github/` `scripts/*.py` `tests/integration/*` `tests/visual/*` `README.md` `CONTRIBUTING.md` | 所有业务代码(.py 业务 / .js / .html / .css / vite.config / package.json) | 文档冲突长尾扫荡 → D3/D4 测试 → 覆盖率棘轮 |

**唯一可能冲突边界**:`tests/unit/test_*_contract.py`(A 抽 service 时加契约测试)· 靠文件名唯一 + `git pull --rebase` 解。

**为啥不能全塞一个窗口/一步**:① 文件冲突(同一巨石俩窗口同时改 = merge 地狱)· ② 依赖顺序(minify[E7] / 状态管理[C9] / TS化[C5] 都碰 `src/home/*` 或 `vite.config`,必须等 A/B 把巨石拆到地板再做,先做 = 返工)。

---

## 窗口 A · 后端(粘这整段)

```
/loop 自主整顿 · 窗口A后端 · 无人值守全自主 · 你是Opus 4.8(1M context)别等我:

【铁律·只碰这些文件】app.py / db.py / *_routes.py / services/**/*.py。绝不碰 home.* / src/home/** / tests/visual/(那是窗口B/C的)。

【4.8能力榨干】每轮把整个目标巨石(db.py或app.py全文)+ 所有调用点 + 对应测试一次性读进上下文整体推理——你有1M context,别切片漏调用点。修同类问题按铁律#1"修一类不修一处":grep全项目同类pattern一次性全改。

【范围·B2+B1】
- B2: db.py 819→<500。剩余域由易到难:tenant / membership+migration(⚠️get_cursor_rls/_is_rls_enabled/get_clients_rls_status/run_rls_isolation_tests是RLS基础设施·别搬别动) / verify_user_password+reset / credits+charge_ocr(钱) / user+auth(登录) / ocr_history(OCR热路径)。范式见主计划第二十二会话段:cohesive整片搬service · `import db`+运行时`db.get_cursor()`(不用by-value否则tenant隔离patch失效) · db.py尾`from services.X import a as a`。
- B1: app.py 3286→<500。剩余@app路由抽独立*_routes.py + app.include_router()。

【全自主含高敏·安全网保留】Zihao已确认"没有高敏·全部跑完"。但保留安全网:① 高敏块(钱/登录/auth/RLS/OCR)只做纯结构性挪代码·0逻辑改 ② 推送后用环境变量测试账号跑真账号E2E(登录+受影响流程·只动测试账号台账绝不碰mrerp真余额) ③ CI红或E2E红→立刻git revert HEAD+单独push再重做·绝不留红在master。

【每轮】
1. 读 CLAUDE.md/CLAUDE.md(28铁律)+ STATE_PEARNLY.md头部 + REFACTOR_MASTER_PLAN.md进度看板 + docs/refactor/BATCH_STRATEGY.md。git branch--show-current确认master(铁律#14)。
2. 抽前必re-grep真实行号。copy-out新文件→接线→删巨石。
3. 跑6道守门全绿:npm run format:check / 全量python -m unittest discover -s tests/unit / python scripts/check_imports.py --quiet / python scripts/check_i18n.py --strict / node --check <改的.js> / npm run build(改前端才需·后端可跳)。每域带契约测试。
4. commit(message含·REFACTOR-WA-B2或WA-B1 + Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>) → git pull --rebase origin master → git push origin master(C档位不问)。
5. gh run watch盯CI真绿;高敏块还跑真账号E2E。红了revert+重做到真绿。
6. 更新STATE_PEARNLY.md头部"窗口A当前task"+主计划进度看板+BATCH_STRATEGY §10。
一直循环别停下问我。
```

---

## 窗口 B · 前端(粘这整段)

```
/loop 自主整顿 · 窗口B前端 · 无人值守全自主 · 你是Opus 4.8(1M context)别等我:

【铁律·只碰这些文件】home.js / home.html / home.css / src/home/**/*.{js,css} / src/main.js / vite.config.*。绝不碰任何.py / services/(那是窗口A的)。

【4.8能力榨干】每轮把整个home.js(或home.html)全文 + routeTo调用链 + 对应E2E/契约测试一次性读进上下文整体推理——你有1M context,这正是home.js地板(routeTo中枢+顶层函数群)最需要的:看全所有调用点再动,别漏桥接。同类问题grep全项目一次性批改(铁律#1)。

【范围·C1+C3】
- C1: home.js 6190→<200。剩地板:routeTo中枢 / 顶层函数群 / 高敏4块(plans-plg-line / password-change / line-email-modal / session-heartbeat)→ src/home/*.js。范式见已上线src/home/test-center.js:共享全局(t/subscribeI18n/showToast/showConfirm/apiGet)直接bare调用·勿重定义勿import·home.js已暴露成全局;搬完src/main.js加import;顶部按需补/* global */。顶层函数群需window桥接(routeTo中枢)·细心。
- C3: home.html 4410→<1000。body section组件化/运行期模板拆分。

【全自主含高敏·安全网保留】Zihao已确认"没有高敏·全部跑完"。但保留安全网:① 高敏4块只做纯结构性挪代码·0逻辑改 ② 推送后跑生产E2E(spec 03-08 home tabs)+视觉回归(tests/visual) ③ CI红或E2E红→立刻git revert HEAD+单独push再重做·绝不留红。

【删home.*大块铁律】必须node split('\n')/join('\n')保CRLF + 删前cp备份 + 删后字节校验(行数对+无\r的行=0)。禁用sed/python盲写。

【每轮】
1. 读 CLAUDE.md/CLAUDE.md(28铁律)+ STATE_PEARNLY.md头部 + REFACTOR_MASTER_PLAN.md进度看板 + BATCH_STRATEGY.md §10/§13。git branch--show-current确认master。
2. 抽前必re-grep真实行号。copy-out→接线(src/main.js import)→自底向上按行号删+字节校验。
3. 跑6道守门全绿:npm run format:check / 全量unittest / check_imports / check_i18n / node --check <改的.js> / npm run build。带渲染/契约测试(module入口函数能渲染·0报错)。
4. commit(message含·REFACTOR-WB-C1或WB-C3 + Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>) → git pull --rebase origin master → git push origin master。
5. gh run watch盯CI真绿 + 生产E2E。红了revert+重做。
6. 更新STATE头部"窗口B当前task"+主计划进度看板+BATCH_STRATEGY §10/§13。
一直循环别停下问我。
```

---

## 窗口 C · 文档 + 测试(粘这整段)

```
/loop 自主整顿 · 窗口C文档测试 · 0业务代码 · 无人值守 · 你是Opus 4.8(1M context)别等我:

【铁律·只碰这些文件】docs/**/*.md / CLAUDE.md/*.md / .github/ / scripts/*.py / tests/integration/* / tests/visual/* / README.md / CONTRIBUTING.md。绝不碰任何业务代码(.py业务/.js/.html/.css/vite.config/package.json)。越界=立刻停下开PR等Zihao。

【4.8能力榨干】文档一致性扫荡用1M context把所有相关文档一次性读进来对照·"修一类不修一处"(铁律#1)grep全项目同类不一致一次性全改。

【第一轮先做·文档冲突长尾扫荡】主控窗口已修两份必读宪法(CLAUDE.md/CLAUDE.md + REFACTOR_MASTER_PLAN.md · commit 6f98d33)。你扫剩余二级文档的同类不一致全改齐:
- "5道守门"→"6道守门"(format:check+全量unit+imports+i18n+node--check+build·E2E按需):RUNBOOK.md / ONBOARDING.md / docs/ONBOARDING.md / BATCH_STRATEGY.md / adr-008 / TASK_MODES.md / BATCH_AGENT_DISPATCH_TEMPLATE.md / .github/PULL_REQUEST_TEMPLATE.md
- 署名"Opus 4.7"→"4.8":只改前瞻性模板(BATCH_STRATEGY/ONBOARDING/dispatch等commit模板);⚠️史实签名不改(docs/audits/*日期签名 / WINDOW_C_COMPLETE完成签名 / STATE过往会话日志 / erp-out-of-box起草署名)。
- 铁律计数 17/20→28:docs/README.md(17→28)等。
- 校验:改完grep确认无残留前瞻性"5道守门"/前瞻性"Opus 4.7"/"17条铁律"/"20条铁律"。

【之后·D3/D4测试 + 覆盖率】
- D3/D4:补E2E(tests/e2e/*.spec.js)+集成测试(tests/integration·env-gated)覆盖核心路径(登录/注册/上传识别/销项税/收入对账/ERP推送/充值)。
- A8覆盖率棘轮:跑baseline·每月只升不降。
- 纯新增文件·绝不改业务代码。

【每轮】
1. 读 CLAUDE.md/CLAUDE.md(28铁律)+ STATE头部 + REFACTOR_MASTER_PLAN.md进度看板。git branch确认master。
2. 干活·字节级LF无BOM。
3. 跑6道守门全绿(改测试跑全量unittest+playwright;纯docs可跳build)。
4. commit(message含·REFACTOR-WC-* + Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>) → git pull --rebase origin master → git push origin master。
5. gh run watch盯CI真绿。红了revert+重做。
6. 更新STATE头部"窗口C当前task"+主计划进度看板。
一直循环别停下问我。
```

---

## 操作提醒

- **测试账号凭据**:窗口 A 跑真账号 E2E 用环境变量 `PEARNLY_E2E_USER/_PASS`(HKCU setx)· **绝不进 git**。开窗口前确认已配。
- **三窗口同时 push**:CI `concurrency` 会取消旧 run(feature 不是 bug)· 每个窗口 push 前 `git pull --rebase`、push 后独立 `gh run watch` 查自己那条真绿。
- **🔴 共享 git index 铁律 · commit 必带 pathspec**(2026-05-29 窗口 C 踩坑):三窗口共用同一工作目录 = 共用同一个 `.git/index`。`git add <我的文件>` 后 `git commit`(不带路径)会把**另一个窗口在这两步之间 `git add` 的文件一起卷进我的 commit**(窗口 C 的 `docs(state)` commit 曾误卷入窗口 B 的 home.js/chrome-render.js · 已在 master 无法回退)。**铁律:每次 commit 必须显式带 pathspec** —— `git commit -- <精确文件列表>`(`--` 后只提交这些路径 · 无视 index 里别人 stage 的东西)· 或 `git commit <files>`。**绝不 `git commit` 裸提交 / `git commit -a`。** 提交后用 `git diff-tree --no-commit-id --name-only -r HEAD` 核实只含自己的文件;若已卷入别人的且已 push → **不 force-push 不 revert**(会毁对方工作)· 只在 STATE 记录 + 口头知会对方窗口。
- **gh CLI 路径**(2026-05-29 更新):`%LOCALAPPDATA%\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe`(旧 `C:\Program Files\GitHub CLI\gh.exe` 已失效)。
- **STATE 头部**会出现"窗口 A/B/C 当前 task"三行,一眼看到三条线。
- **本地跑**(非云端):窗口留着才跑,持续耗 Opus 额度。

## 等 Loop 1(A+B)拆完才能做的后续(别提前做 · 会撞车 / 返工)

| 后续 task | 为啥要等 | 触发 |
|---|---|---|
| 防屎山 CI 切 fail 模式 | 行数没降下来会卡 push | `refactor_progress.py` 规模 ≥ 80% + Zihao 拍板(铁律 #27) |
| C5 TypeScript 化 | 碰所有 .js | home.js 拆到地板后 |
| C9 状态管理 | 碰 src/home/* 业务 JS | src/home/* 模块稳定后 |
| E7 资源 minify | 碰 vite.config 影响 build 守门 | Loop 1 完成后 |

---

*配套:ADR-011(3 窗口策略)· 铁律 #26(自主 loop)· 铁律 #27(防屎山 fail 模式切换)· AUTONOMOUS_LOOP.md(单窗口版)· 整顿搞完即归档。*
