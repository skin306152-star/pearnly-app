# 机械闸自查手册(每个窗口开工先读 · 左移=别等 push 才第一次见闸)

> 出身:push 即自动部署,CI 事后才红=太晚 → 全部质量检查做成 pre-push 本地硬拦(scripts/git-hooks/pre-push,只认退出码)。
> **本页的用法:① 开工第 0 步把"全套自查"跑一遍拿基线(知道哪些红是别窗口/存量的) ② 干活中途随时跑单道 ③ 收尾跑全套,绿了才 push。**
> 一键全套(等价 pre-push,不用真推):`sh scripts/git-hooks/pre-push`(在 Git Bash)或逐条跑下表命令。

## 22 道闸 · 查什么 · 怎么提前自查 · 豁免法

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
| tsc | 改 .ts | 类型错 | `npm run typecheck` | **已进 CI lint job(2026-07-30 · 硬闸)**;eslint 的 flat config 不收 src/**/*.ts,tsc 是 TS 源唯一的机械闸,别指望 eslint 兜 |
| build+dist 一致 | 改前端 | 改源没重打包=prod 跑旧 bundle | `npm run build` 后 `git add static/dist` + bump `?v=` | main.js/map 的 drift 不算 |
| check_asset_bundling | 改前端 | 源页明文引资源(view-source 退化)· 覆盖 home/login/admin/console/pos | `python scripts/check_asset_bundling.py` | 新资产进打包清单(pos/console 新 JS 逻辑必进 bundle·仅 *-i18n 数据/pos-sw 可独立) |
| ui_design_lint 棘轮 | 改前端 | 裸 hex/emoji 图标/自曝文案等,命中数**只许降** | `node scripts/ui_design_lint.mjs --gate` | **注释里的 hex 也计数**;存量降了跑 `--update-baseline` 收紧;写色一律 var() |
| check_file_size | 任何改动 | 任何监控文件 >500 行 | `python scripts/check_file_size.py --quiet` | 先拆,无豁免 |
| check_line_ratchet | 任何改动 | 监控文件行数净增 | `python scripts/check_line_ratchet.py --base origin/master --head HEAD --quiet` | 合理增长:commit 写 `RATCHET-EXEMPT: <file> +<N> · <理由>`;**新文件一律先豁免** |
| check_ui_consistency | 任何改动 | D1 禁新抽屉(用 .modal)/D2 按钮禁黑底(用 var(--btn-blue)) | `python scripts/check_ui_consistency.py --quiet` | 只导航栏可黑 |
| check_theme_responsive 棘轮 | 任何改动 | 暗夜不翻面的写死色(3位hex/white·black/不透明rgb·补 6 位 hex 闸的漏)+ 入口页 viewport 必须在,命中**只许降** | `python scripts/check_theme_responsive.py --gate --quiet` | 半透明 rgba(阴影/遮罩)豁免;颜色一律 var(--token);存量降了跑 `--update-baseline` 收紧;**手机端"合理"机械保证不了,真机验收见 docs/ui/THEME_RESPONSIVE_VERIFY.md** |
| check_authz_coverage | 任何改动 | 每路由必声明权限或上公开白名单(第 8 道) | `PEARNLY_SKIP_HEAVY_INIT=1 python scripts/check_authz_coverage.py --quiet` | 公开路由进 PUBLIC_ROUTES 带注释;自定义门函数要登记进闸的 helper 清单(`_auth` 误判先例) |
| 视觉照搬闸 | 改 POS/库存/采购照搬页 | 关键令牌 == 设计快照 | `node tests/visual/test_design_fidelity.spec.js` | 改设计=同步更新 tests/visual/design/ 快照 |

## 多窗口并行的三条铁纪律(闸之外最常见的"被拦"原因)

1. **只 add 自己的 pathspec** —— `git add -A` 会把别窗口 WIP 卷进你的 commit。
2. **push 被拦先看红的是谁的文件** —— 闸扫整棵推送链,别窗口 commit 的红会卡住你;别替它修它的 baseline/token 决策,等它收口(worktree 单推自己 commit 是兜底术,见 memory)。
3. **PowerShell 5.1 读 UTF-8 文件必用 Edit 工具**,`Get-Content -Raw` 无编码参数会把中泰文读坏(console.html 乱码先例)。

## 紧急绕过(仅人工,明知故犯)

`git push --no-verify` —— **AI 窗口永远不许用**(家规:禁 --no-verify)。
