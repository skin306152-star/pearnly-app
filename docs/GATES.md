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

## 31 道闸 · 查什么 · 怎么提前自查 · 豁免法

| 闸 | 触发条件 | 查什么 | 提前自查命令 | 豁免/注意 |
|---|---|---|---|---|
| ruff | 改 .py | F821 未定义名/F822 漏 import(502 元凶) | `ruff check <你的.py>` | 无豁免,修 |
| black | 改 .py | Python 格式 | `black --check <你的.py>`(直接 `black <file>` 修) | 无 |
| import 冒烟 | 改 .py | 启动即崩(语法错/漏 import) | `python -c "import app"` | 无 |
| check_imports | 改 .py | import 结构 | `python scripts/check_imports.py --quiet` | 无 |
| check_tracked_imports | 改 .py | import 的本地模块必须 git 已跟踪(工作树有但 HEAD 没有=漏 add → clean clone/prod 崩) | `python scripts/check_tracked_imports.py --quiet` | 无;补 2026-06-11 部署崩盲区(check_imports 在工作树跑看不见未跟踪) |
| check_i18n | 改 .py | 4 语翻译完整(**横向**比:有 zh 没 th) | `python scripts/check_i18n.py --strict --quiet` | 加键必四语齐;**四语一起缺它看不见**(没有参照物)→ 那一半归下一行 |
| check_i18n_refs | 改 .py | **纵向**查:`t()` / `POS.t()` / `data-i18n` 用到的键必须在 `static/i18n-data.js` / `static/pos/pos-i18n.js` 里存在(落空 = 屏上印裸键名) | `python scripts/check_i18n_refs.py` | 2026-07-31 建;`sx-p-bc-dup-unit` / `posui.bscan.fails_n` 四语一起缺、check_i18n 同时报 0 missing,就是这么上屏的;拼接键 `t('pre_' + x)` 不查(判据故意做窄,误报一次闸就废);反证 `tests/unit/test_i18n_refs_gate.py` |
| 全量 unittest | 改 .py | 改一处崩别处 | `PYTHONUTF8=1 python -m unittest discover -s tests/unit -p "test_*.py"` | 无;**新文件≥1测试**是另一条家规;**必须 `PYTHONUTF8=1`**(只设 `PYTHONIOENCODING` 会让 `test_file_crypto` 假红,什么都不设会让 `test_agent_capability_audit` 假红 · 见 `tests/unit/test_pre_push_hook_env.py`) |
| E2E 台账闸(跑在全量 unittest 里) | 改扫码这一片的源码,或新写扫码验收脚本 | ① 新写的扫码 E2E 必须在 `tests/e2e/e2e_ledger.json` 里登记「只有它能保什么」② 改了 `covers` 里的源码却没重跑那个 E2E → 本机红(判据=产物截图 mtime;CI 上 mtime 全是检出时间,故 CI 自动跳过②) | `python -m unittest tests.unit.test_e2e_ledger_gate` | 真反证长在 `scripts/_*.cjs` 里而它们不在任何跑单上,这道闸补的就是那个洞;②的唯一过法是在台账 `stale_ack` 写一条带 `until` 的欠条(说清为什么、最长 14 天、过期照红) |
| 验收脚本两道(跑在全量 unittest 里) | 改 `scripts/_*.cjs` | ① 点击必须唯一定位(`.first()/.nth()` + `.click()` 关掉了 Playwright 严格模式 → 打偏也不抛)② 期望值必须现场从页面真词典取,脚本一个字都不注入 | `python -m unittest tests.unit.test_verify_script_selector_gate tests.unit.test_verify_script_i18n_injection_gate` | ① 真要按位置点:同行/上一行写 `// SELECTOR-INDEX-OK: <点的是哪一个>`(理由不许空)② 整份搬真词典进合成页放行(要 require 真词典源);「断言必须只有走目标路径才会变」机械化不了,见 `.claude/skills/verification` 验收脚本规范第 1 条 |
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
| check_file_size | 任何改动 | 任何监控文件 >500 行(监控面 = 根 `*.py` / `routes` `core` `services` 下的 `.py` / `src/home/**` / **`static/pos/**`(2026-07-31 收)/ `static/scan/**/*.js`(同期)/ `static/ai/**/*.js`(2026-08-01 收)**) | `python scripts/check_file_size.py --quiet` | 先拆,无豁免;**三片 plain-script SPA 此前整片在闸外** —— /pos 与 /ai 都不走 vite 打包,`src/home/**` 照不到,闸报 PASS 是没看见不是判合格(/pos 收进来抓到 4 个、/ai 抓到 7 个,`pos.html` 1429、`ai-review.js` 770 行居首),存量按下一行的基线记账 |
| check_file_size 存量基线 | 任何改动 | 基线里的文件行数只许降不许升(涨一行就红);基线**外**的文件越线即红,没有宽限 | `python scripts/check_file_size.py --quiet`(同一道命令、两层判据) | 基线在 `scripts/file_size_baseline.json`(共 11 条:`static/ai` 7 + `static/pos` 4,POS 那四条带 deadline 写在文件 `_notes` 里,三个 .js 2026-09-30、`pos.html` 2026-12-31,到期直接删条目让它红);拆下来后跑 `--update-baseline` 收紧,闸自己会提示哪条能收(`--quiet` 下也打,因为钩子只用 quiet);**词典 `ai-i18n-*.js` 与 `pos-i18n.js` 不在监控面**(纯键值表,拿行数量没意义;装配层 `ai-i18n.js` 带 `at()`,是代码,照常监控 —— 判据卡在中划线上);往基线里加条目要连 `tests/unit/test_file_size_gate.py` 那条「只许缩」的断言一起改,免不成默默的;反证 `tests/unit/test_file_size_gate.py` |
| check_line_ratchet | 任何改动 | 监控文件行数净增 | `python scripts/check_line_ratchet.py --base "$(git merge-base origin/master HEAD)" --head HEAD --quiet` | 合理增长:commit 写 `RATCHET-EXEMPT: <file> +<N> · <理由>`;**新文件一律先豁免**;**base 必须是 merge-base,不能写 origin/master** —— `git diff A..B` 是两棵树的差,master 往前跑一笔就算到你头上(2026-07-31 实测:停摆分支自己只改 1 个 .md,却被红 19 个它没碰过的监控文件;13 条分支两点红 12、三点红 4),反证 `tests/unit/test_prepush_diff_range.py` |
| check_ui_consistency | 任何改动 | D1 禁新抽屉(用 .modal)/D2 按钮禁黑底(用 var(--btn-blue)) | `python scripts/check_ui_consistency.py --quiet` | 只导航栏可黑 |
| check_theme_responsive 棘轮 | 任何改动 | 暗夜不翻面的写死色(3位hex/white·black/不透明rgb·补 6 位 hex 闸的漏)+ 入口页 viewport 必须在,命中**只许降** | `python scripts/check_theme_responsive.py --gate --quiet` | 半透明 rgba(阴影/遮罩)豁免;颜色一律 var(--token);存量降了跑 `--update-baseline` 收紧;**手机端"合理"机械保证不了,真机验收见 docs/ui/THEME_RESPONSIVE_VERIFY.md** |
| check_test_git_writes | 任何改动(钩子里排第一道) | 测试里起 `git` 的子命令必须只读;写操作(init/add/commit/config…)或看不出是什么的转发(`["git", *args]`)= 拦 | `python scripts/check_test_git_writes.py --list` | 造真 commit 唯一合法入口 `tests/unit/_git_sandbox.py`(它是唯一豁免文件,改个名放同样的代码照样红);**位置是死的,必须排在「全量 unittest」之前** —— 2026-07-31 P0 就是钩子注入的 GIT_DIR/GIT_INDEX_FILE 盖过 `cwd=`,unittest 里的 `git add -A`/`commit` 打进宿主仓(4838 files / -794172,差一步 push 上线);`GIT_DIR` 类环境变量与 `.git` 路径字面量判不了好坏,进 `--list` 当 NOTE 摆着不判红,宁可漏不误报;反证 `tests/unit/test_git_write_isolation.py` |
| check_destructive_db_tests | 任何改动(跟在 git 写操作闸后面) | 测试里 `execute(…)` 出现 `DROP TABLE` / `DROP SCHEMA` / `TRUNCATE` 的模块,必须引用 `require_disposable_db()`;目标库里没有哨兵表 `_pearnly_disposable_test_db` 就在 setUpClass 红掉,一张表都不会掉 | `python scripts/check_destructive_db_tests.py --list` | tests/integration 那 28 个模块 DROP 的是 **DATABASE_URL 指到的那个库**,没有临时 schema 也没有回滚;而库掉了没有"跑一遍迁移建回来"这条路:2026-08-01 起 `users`/`tenants`/`ocr_history` 等 26 张遗留表的 DDL 进了迁移 `001a_legacy_tables`(空库可跑 `alembic upgrade 001a_legacy_tables` 建回来),但 `clients` 这类只有 `ensure_*` 建的表仍在迁移史外,`alembic upgrade head` 也仍走不到头(002/007/0030 引用了生产不存在的 schema),整库还原还是得从 prod 拉 schema-only dump —— 2026-07-11、2026-07-31 各中一次。判据只认 AST 上 execute/executemany 第一实参里的 DDL(f-string 与模块常量跟进一层),**只在 `assertIn` 里出现 DDL 文本的 19 个 migration 守门文件不收**;DELETE/ALTER 刻意不收(收了会把闸淹掉)。跑法见 `tests/integration/README.md`;反证 `tests/unit/test_destructive_db_test_gate.py` |
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
