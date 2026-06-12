# 机械闸自查手册(每个窗口开工先读 · 左移=别等 push 才第一次见闸)

> 出身:push 即自动部署,CI 事后才红=太晚 → 全部质量检查做成 pre-push 本地硬拦(scripts/git-hooks/pre-push,只认退出码)。
> **本页的用法:① 开工第 0 步把"全套自查"跑一遍拿基线(知道哪些红是别窗口/存量的) ② 干活中途随时跑单道 ③ 收尾跑全套,绿了才 push。**
> 一键全套(等价 pre-push,不用真推):`sh scripts/git-hooks/pre-push`(在 Git Bash)或逐条跑下表命令。

## 13 道闸 · 查什么 · 怎么提前自查 · 豁免法

| 闸 | 触发条件 | 查什么 | 提前自查命令 | 豁免/注意 |
|---|---|---|---|---|
| ruff | 改 .py | F821 未定义名/F822 漏 import(502 元凶) | `ruff check <你的.py>` | 无豁免,修 |
| black | 改 .py | Python 格式 | `black --check <你的.py>`(直接 `black <file>` 修) | 无 |
| import 冒烟 | 改 .py | 启动即崩(语法错/漏 import) | `python -c "import app"` | 无 |
| check_imports | 改 .py | import 结构 | `python scripts/check_imports.py --quiet` | 无 |
| check_i18n | 改 .py | 4 语翻译完整 | `python scripts/check_i18n.py --strict --quiet` | 加键必四语齐 |
| 全量 unittest | 改 .py | 改一处崩别处 | `python -m unittest discover -s tests/unit -p "test_*.py"` | 无;**新文件≥1测试**是另一条家规 |
| check_new_debt | 改 .py | 禁新增 ensure_*/app.py 巨石路由 | `python scripts/check_new_debt.py` | 真要新 ensure:commit 写 `NEW-DEBT-EXEMPT: <理由>` |
| prettier | 改前端 | 格式(按**提交内容**校验,非工作区) | `npx prettier --check <file>`(home.html/home.js 在 .prettierignore,**禁 prettier --write 它们**) | CRLF 巨石文件别碰格式化 |
| eslint | 改前端 | 前端真 bug | `npm run lint` | 无 |
| check_ai_smell | 改前端 | 注释 emoji/console.log 残留 | `python scripts/check_ai_smell.py <files>` | 无,去 AI 味是家规 |
| tsc | 改 .ts | 类型错 | `npm run typecheck` | 无 |
| build+dist 一致 | 改前端 | 改源没重打包=prod 跑旧 bundle | `npm run build` 后 `git add static/dist` + bump `?v=` | main.js/map 的 drift 不算 |
| check_asset_bundling | 改前端 | 源页明文引资源(view-source 退化)· 覆盖 home/login/admin/console/pos | `python scripts/check_asset_bundling.py` | 新资产进打包清单(pos/console 新 JS 逻辑必进 bundle·仅 *-i18n 数据/pos-sw 可独立) |
| ui_design_lint 棘轮 | 改前端 | 裸 hex/emoji 图标/自曝文案等,命中数**只许降** | `node scripts/ui_design_lint.mjs --gate` | **注释里的 hex 也计数**;存量降了跑 `--update-baseline` 收紧;写色一律 var() |
| check_file_size | 任何改动 | 任何监控文件 >500 行 | `python scripts/check_file_size.py --quiet` | 先拆,无豁免 |
| check_line_ratchet | 任何改动 | 监控文件行数净增 | `python scripts/check_line_ratchet.py --base origin/master --head HEAD --quiet` | 合理增长:commit 写 `RATCHET-EXEMPT: <file> +<N> · <理由>`;**新文件一律先豁免** |
| check_ui_consistency | 任何改动 | D1 禁新抽屉(用 .modal)/D2 按钮禁黑底(用 var(--btn-blue)) | `python scripts/check_ui_consistency.py --quiet` | 只导航栏可黑 |
| check_authz_coverage | 任何改动 | 每路由必声明权限或上公开白名单(第 8 道) | `PEARNLY_SKIP_HEAVY_INIT=1 python scripts/check_authz_coverage.py --quiet` | 公开路由进 PUBLIC_ROUTES 带注释;自定义门函数要登记进闸的 helper 清单(`_auth` 误判先例) |
| 视觉照搬闸 | 改 POS/库存/采购照搬页 | 关键令牌 == 设计快照 | `node tests/visual/test_design_fidelity.spec.js` | 改设计=同步更新 tests/visual/design/ 快照 |

## 多窗口并行的三条铁纪律(闸之外最常见的"被拦"原因)

1. **只 add 自己的 pathspec** —— `git add -A` 会把别窗口 WIP 卷进你的 commit。
2. **push 被拦先看红的是谁的文件** —— 闸扫整棵推送链,别窗口 commit 的红会卡住你;别替它修它的 baseline/token 决策,等它收口(worktree 单推自己 commit 是兜底术,见 memory)。
3. **PowerShell 5.1 读 UTF-8 文件必用 Edit 工具**,`Get-Content -Raw` 无编码参数会把中泰文读坏(console.html 乱码先例)。

## 紧急绕过(仅人工,明知故犯)

`git push --no-verify` —— **AI 窗口永远不许用**(家规:禁 --no-verify)。
