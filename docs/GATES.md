# 机械闸自查手册(每个窗口开工先读 · 左移=别等 push 才第一次见闸)

> 出身:push 即自动部署,CI 事后才红=太晚 → 全部质量检查做成 pre-push 本地硬拦(scripts/git-hooks/pre-push,只认退出码)。
> **本页的用法:① 开工第 0 步把"全套自查"跑一遍拿基线(知道哪些红是别窗口/存量的) ② 干活中途随时跑单道 ③ 收尾跑全套,绿了才 push。**
> 一键全套(等价 pre-push,不用真推):`sh scripts/git-hooks/pre-push`(在 Git Bash)或逐条跑下表命令。

## 装钩子(一句话 · 复制就跑)

```sh
git config core.hooksPath scripts/git-hooks
```

装没装上:`git config --get core.hooksPath` 有输出 = 装上了(没输出/退出码 1 = 没装,闸一道都不跑)。卸:`git config --unset core.hooksPath`。

三件事先知道,别装完才发现:

1. **它写进 `.git/config`,不是写进某个 worktree** —— 共享同一个 `.git` 的所有 worktree(`git worktree list` 列出来的每一个)从此每次 push 都走这道闸。逐 worktree 单独开关做不到,除非先开 `extensions.worktreeConfig` 再用 `git config --worktree`。
2. **路径是相对的,按「谁在 push」各自解析** —— githooks(5):钩子跑之前 git 会 `cd` 到该 worktree 的根。所以 A worktree push 跑的是 `A/scripts/git-hooks/pre-push`,B 跑 B 的。老分支跑老版本的闸;分支里没这个文件 = 那次 push 静悄悄没有闸。
3. **代价**:改动只含文档/纯文本约 40 秒;含 `.py`(要跑全量 unittest)或前端(要跑 eslint + vite build)实测约 3 分钟起。**「改了什么」按 merge-base 算**,所以分支自己没动 `.py` 就不跑那趟全量单测 —— 停摆分支不会再因为 master 往前跑而白跑 3 分钟(2026-07-31)。那趟单测有意保留:它是钩子里唯一盖「改一处崩别处」的闸,而 push 即上线、CI 是事后报警器;按 import 反查裁剪的路验过不通(1038 个测试模块里 213 个靠扫文件/起子进程验,没有 import 边)。`git push --dry-run` 也会触发本钩子(但不会真推),可拿来空跑验证。

## 27 道闸 · 查什么 · 怎么提前自查 · 豁免法

| 闸 | 触发条件 | 查什么 | 提前自查命令 | 豁免/注意 |
|---|---|---|---|---|
| ruff | 改 .py | F821 未定义名/F822 漏 import(502 元凶) | `ruff check <你的.py>` | 无豁免,修 |
| black | 改 .py | Python 格式 | `black --check <你的.py>`(直接 `black <file>` 修) | 无 |
| import 冒烟 | 改 .py | 启动即崩(语法错/漏 import) | `python -c "import app"` | 无 |
| check_imports | 改 .py | import 结构 | `python scripts/check_imports.py --quiet` | 无 |
| check_tracked_imports | 改 .py | import 的本地模块必须 git 已跟踪(工作树有但 HEAD 没有=漏 add → clean clone/prod 崩) | `python scripts/check_tracked_imports.py --quiet` | 无;补 2026-06-11 部署崩盲区(check_imports 在工作树跑看不见未跟踪) |
| check_i18n | 改 .py | 4 语翻译完整 | `python scripts/check_i18n.py --strict --quiet` | 加键必四语齐 |
| 全量 unittest | 改 .py | 改一处崩别处 | `python -m unittest discover -s tests/unit -p "test_*.py"` | 无;**新文件≥1测试**是另一条家规 |
| check_new_debt | 改 .py | 禁新增 ensure_*/app.py 巨石路由 | `python scripts/check_new_debt.py` | 真要新 ensure:commit 写 `NEW-DEBT-EXEMPT: <理由>` |
| prettier | 改前端 | 格式(按**提交内容**校验,非工作区) | `npx prettier --check <file>`(home.html/home.js 在 .prettierignore,**禁 prettier --write 它们**) | CRLF 巨石文件别碰格式化 |
| eslint | 改前端 | 前端真 bug | `npm run lint` | 无 |
| check_ai_smell | 改前端 | 注释 emoji/console.log 残留 | `python scripts/check_ai_smell.py <files>` | 无,去 AI 味是家规 |
| check_ai_i18n_refs | 改 /ai 前端 | `at()`/`t()`/`data-at` 引的键必须在某份 `static/ai/ai-i18n*.js` 里有定义(落空 = 标识符原样印上屏) | `python scripts/check_ai_i18n_refs.py` | **check_i18n 看不见这片**(它只管 static/i18n-data.js);只查"引用得到定义",不查四语齐(各分片语种策略不同);拼接键 `at('pre_' + x)` 不查,由调用方测试兜;反证 `tests/unit/test_ai_i18n_refs_gate.py` |
| check_home_i18n_refs | 改 /home 前端 | `t()`/`_t()`/`kbT()`/`data-i18n` 引的键必须在 `static/i18n-data.js` 的 window.I18N 里有定义(落空 = 要么把 key 原样印上屏,要么整个元素跳过、模板里写死的中文永不翻译) | `python scripts/check_home_i18n_refs.py` | **check_i18n 只对拍四语之间齐不齐,从不问键有没有人引、引对没有**;只查"引用得到定义",不查四语齐;拼接键 `t('pre-' + x)` 与常量键表 `t(TBL[x])` 不查(闸顶注写明);存量落空记 `scripts/home_i18n_refs_baseline.txt`,只许降不许升,修好跑 `--update-baseline`;反证 `tests/unit/test_home_i18n_refs_gate.py` |
| tsc | 改 .ts | 类型错 | `npm run typecheck` | **已进 CI lint job(2026-07-30 · 硬闸)**;eslint 的 flat config 不收 src/**/*.ts,tsc 是 TS 源唯一的机械闸,别指望 eslint 兜 |
| build+dist 一致 | 改前端 | 改源没重打包=prod 跑旧 bundle | `npm run build` 后 `git add static/dist` + bump `?v=` | main.js/map 的 drift 不算 |
| check_asset_bundling | 改前端 | 源页明文引资源(view-source 退化)· 覆盖 home/login/admin/console/pos | `python scripts/check_asset_bundling.py` | 新资产进打包清单(pos/console 新 JS 逻辑必进 bundle·仅 *-i18n 数据/pos-sw 可独立) |
| ui_design_lint 棘轮 | 改前端 | 裸 hex/emoji 图标/自曝文案等,命中数**只许降** | `node scripts/ui_design_lint.mjs --gate` | **注释里的 hex 也计数**;存量降了跑 `--update-baseline` 收紧;写色一律 var() |
| check_file_size | 任何改动 | 任何监控文件 >500 行 | `python scripts/check_file_size.py --quiet` | 先拆,无豁免 |
| check_line_ratchet | 任何改动 | 监控文件行数净增 | `python scripts/check_line_ratchet.py --base "$(git merge-base origin/master HEAD)" --head HEAD --quiet` | 合理增长:commit 写 `RATCHET-EXEMPT: <file> +<N> · <理由>`;**新文件一律先豁免**;**base 必须是 merge-base,不能写 origin/master** —— `git diff A..B` 是两棵树的差,master 往前跑一笔就算到你头上(2026-07-31 实测:停摆分支自己只改 1 个 .md,却被红 19 个它没碰过的监控文件;13 条分支两点红 12、三点红 4),反证 `tests/unit/test_prepush_diff_range.py` |
| check_ui_consistency | 任何改动 | D1 禁新抽屉(用 .modal)/D2 按钮禁黑底(用 var(--btn-blue)) | `python scripts/check_ui_consistency.py --quiet` | 只导航栏可黑 |
| check_theme_responsive 棘轮 | 任何改动 | 暗夜不翻面的写死色(3位hex/white·black/不透明rgb·补 6 位 hex 闸的漏)+ 入口页 viewport 必须在,命中**只许降** | `python scripts/check_theme_responsive.py --gate --quiet` | 半透明 rgba(阴影/遮罩)豁免;颜色一律 var(--token);存量降了跑 `--update-baseline` 收紧;**手机端"合理"机械保证不了,真机验收见 docs/ui/THEME_RESPONSIVE_VERIFY.md** |
| check_test_git_writes | 任何改动(钩子里排第一道) | 测试里起 `git` 的子命令必须只读;写操作(init/add/commit/config…)或看不出是什么的转发(`["git", *args]`)= 拦 | `python scripts/check_test_git_writes.py --list` | 造真 commit 唯一合法入口 `tests/unit/_git_sandbox.py`(它是唯一豁免文件,改个名放同样的代码照样红);**位置是死的,必须排在「全量 unittest」之前** —— 2026-07-31 P0 就是钩子注入的 GIT_DIR/GIT_INDEX_FILE 盖过 `cwd=`,unittest 里的 `git add -A`/`commit` 打进宿主仓(4838 files / -794172,差一步 push 上线);`GIT_DIR` 类环境变量与 `.git` 路径字面量判不了好坏,进 `--list` 当 NOTE 摆着不判红,宁可漏不误报;反证 `tests/unit/test_git_write_isolation.py` |
| check_destructive_db_tests | 任何改动(跟在 git 写操作闸后面) | 测试里 `execute(…)` 出现 `DROP TABLE` / `DROP SCHEMA` / `TRUNCATE` 的模块,必须引用 `require_disposable_db()`;目标库里没有哨兵表 `_pearnly_disposable_test_db` 就在 setUpClass 红掉,一张表都不会掉 | `python scripts/check_destructive_db_tests.py --list` | tests/integration 那 28 个模块 DROP 的是 **DATABASE_URL 指到的那个库**,没有临时 schema 也没有回滚;而 `users`/`tenants`/`ocr_history`/`clients` 从来没进过版本控制(`ensure_*` 只做 ALTER,alembic 从空库第一条碰 ocr_history 的迁移就挂),掉了只能从 prod 拉 schema-only dump 灌回 —— 2026-07-11、2026-07-31 各中一次。判据只认 AST 上 execute/executemany 第一实参里的 DDL(f-string 与模块常量跟进一层),**只在 `assertIn` 里出现 DDL 文本的 19 个 migration 守门文件不收**;DELETE/ALTER 刻意不收(收了会把闸淹掉)。跑法见 `tests/integration/README.md`;反证 `tests/unit/test_destructive_db_test_gate.py` |
| check_e2e_stub_contracts | 任何改动 | E2E 桩(`page.route`)回包的顶层键不得少于真后端该端点的**无条件**投影;登记为 not_null 的键不许写成 `null`/`undefined` | `python scripts/check_e2e_stub_contracts.py --list` | 登记表在脚本顶部 CONTRACTS(现收 steward 的 status/sessions 三口);后端加键 → `tests/unit/test_e2e_stub_contract_gate.py` 的防漂测试先红,改表再补各 spec 的桩。**tasks/{id}、messages 故意没登记**(投影带条件分支,登记进去会误报)。非 2xx 的故障注入桩不判;分支里先做了别的事才 fulfill 的桩跟不到,`--list` 里点数,宁可漏不误报 |
| check_authz_coverage | 任何改动 | 每路由必声明权限或上公开白名单(第 8 道) | `PEARNLY_SKIP_HEAVY_INIT=1 python scripts/check_authz_coverage.py --quiet` | 公开路由进 PUBLIC_ROUTES 带注释;自定义门函数要登记进闸的 helper 清单(`_auth` 误判先例) |
| pg-smoke(真库冒烟) | 改 SQL / schema / RLS 策略 | mock 单测钉不住的那层:方言、`numeric(12,6)` 精度、`pg_advisory_xact_lock` 真串行、RLS 真隔离。CI 独立 job(带 postgres:16 service),**skip 也判红**(连不上库 = 这道闸没跑) | 本机 docker `pearnly-db` 起着,`PEARNLY_PG_SMOKE_URL=postgresql://pearnly:pearnly_local_dev@127.0.0.1:5432/pearnly python -m unittest discover -s tests/unit -p "test_*_pg_smoke.py"` | 新 smoke 文件按 `test_*_pg_smoke.py` 命名即自动进闸,无需登记;测试只认 `PEARNLY_PG_SMOKE_URL`,**绝不回落 DATABASE_URL**(防误连生产);tests/integration 那批仍未进 CI —— 2026-07-31 实测结论是先别搬:28 个模块会拆掉目标库、且互相不隔离(同一个库连跑两遍红从 28 涨到 32),细节见 check_destructive_db_tests 那行 |
| 视觉照搬闸 + 基准过期检测 | 任何改动(CI test job 无条件跑)· pre-push 改 POS/库存/采购照搬页或 tests/visual/design/ 时触发 | ① 关键令牌 == 设计快照;② 基准里出现「生产该页 DOM 没有 **且** 生产样式表也没有」的 class = 基准过期(尺子自己旧了) | `node tests/visual/test_design_fidelity.spec.js`(`--list` 看逐页清单) | 红了二选一:生产真删了 → **改基准**(pur-settings 那面 chip 墙就是这么修的);设计稿装饰件/外壳区 → 逐条登记 `tests/visual/design/_freshness-allow.json` **并写理由**(理由太短会被单测拦)。失效登记同样报红;闸每次跑先自检(塞毒 class 必须只逮住它),逮不着直接红;反证 `tests/unit/test_design_freshness_frontend.py` |

## 多窗口并行的三条铁纪律(闸之外最常见的"被拦"原因)

1. **只 add 自己的 pathspec** —— `git add -A` 会把别窗口 WIP 卷进你的 commit。
2. **push 被拦先看红的是谁的文件** —— 闸扫整棵推送链,别窗口 commit 的红会卡住你;别替它修它的 baseline/token 决策,等它收口(worktree 单推自己 commit 是兜底术,见 memory)。
3. **PowerShell 5.1 读 UTF-8 文件必用 Edit 工具**,`Get-Content -Raw` 无编码参数会把中泰文读坏(console.html 乱码先例)。

## 紧急绕过(仅人工,明知故犯)

`git push --no-verify` —— **AI 窗口永远不许用**(家规:禁 --no-verify)。
