# CLAUDE.md · Pearnly 项目宪法(轻量版)

> **不用通读。** 开工只要三样:`AGENTS.md` → STATE 顶部状态卡 → 跑 `python scripts/refactor_progress.py`。本页是"坑 + 硬线 + 索引",干活的具体做法在 `.claude/skills/`(按需自动装载)和 `docs/`(用 `@` 引用)。
>
> 2026-07-25 按 Anthropic《The new rules of context engineering for Claude 5 generation models》重写:1470 行 → 本页。删了什么、为什么删得掉 → `docs/context-engineering/2026-07-25-claude-md-simplify.md`;旧全文冻结在 `CLAUDE.md/ARCHIVE_CLAUDE_LEGACY.md`(别照它干活)。

## 1. 这个 repo 是什么

Pearnly = 泰国会计事务所 + SME 老板的 AP 自动化 SaaS。多语言 OCR(泰/中/日)+ 全管道进料(LINE/邮件/文件夹)+ ERP 中立中间件。口号:不让用户换 ERP,让 Pearnly 适配所有 ERP。

FastAPI + 原生 JS/Vite + Supabase Postgres,一个仓库装多个入口壳(主站 `/home`、POS `/pos`、超管 `/earn`、AI `/ai`、DMS `/dms`、控制台 `/console`)。**入口 → 可读源文件的映射唯一权威 = `AGENTS.md` §5-bis**(改对外页面前必看:改错位置 = 新域名永远跑老版本)。

## 2. 坑(只写会咬人的;看代码就知道的不写)

**数据库 / 后端**

- `db.get_cursor()` 默认不 commit,DDL(ALTER/CREATE)在 with 块退出时静默回滚 → 必须 `get_cursor(commit=True)`。日志会骗你说"字段就绪",库里根本没建。
- 改后端返回 dict 的字段(增/删/改名)必须同步改对应 Pydantic `response_model`,否则整个接口 500(`/api/me` 踩过)。删字段先 `Optional + default None` 一版,下版再真删。
- 生产**不跑** `alembic upgrade`:schema 靠启动 `ensure_*` 生效,`alembic/versions` 只留档。
- 前端报"数据空 / 渲染异常 / 早退",第一步 `curl` 那个接口看 HTTP 状态,别 grep CSS —— 500 是后端在喊救命。
- 钱用 `Decimal` 不用 float · 时间存 UTC · SQL 参数化 · 多租户查询必带 tenant 隔离(RLS 已在 ready 域启用)。

**前端**

- 改 `src/**` 必须 `npm run build` + `git add static/dist` **一起提交**;只改源码不提交 dist = 生产跑旧 bundle,改了等于白改。纯 `.css`/`.html` 不用 build。
- 改前端资源必 bump 引用处的 `?v=`(CDN 按旧键回旧文件,这是缓存闸盲区)。
- `home.html` / `login.html` / `static/i18n-data.js` / `static/home-*.css` 是 **CRLF + 在 .prettierignore 里**:禁 `sed`、禁 `prettier --write`、禁 PowerShell `Get-Content -Raw` 读(会毁中泰文)。一律用 Edit 工具。
- 颜色只认令牌 `var(--brand)` / `var(--btn-blue)`,真值在 `static/pearnly-ui.css` + `static/home-01-base.css`(当前主题紫)。老文档里写死的 `#111111`(黑)`#2563EB`(蓝)全是历史,别再当真值引用。
- 状态单一事实源:后端出一个布尔 `body.ok`,前端只读它,**绝不靠 HTTP 状态码判业务成败**(200 + `ok:false` 是有效的失败响应)。

**业务红线(错了是事故)**

- `workspace_client_id`(账套主体)≠ `history.client_id`(发票买方),永不混用同字段。
- `erp_push_logs` 是推送状态唯一源,不建第二套状态表/字段。
- `rows=0` / `needs_mapping` / `failed` / `blocked` / `retrying` / `ERR_*` 一律不许显示"完成/成功"(四态诚实)。
- Pearnly 是核对表生成器,不是判定器:不做 `INV↔IV` 归一化、不做"金额接近算匹配"。系统能算出的硬错(净额+VAT≠总额 / 税号非 13 位 / VAT≠7%)主动标,但只是提醒,改不改用户说了算。
- **不碰真付费用户余额**(mrerp 等真账号)。充值 = 真人银行转账 + 人工审核,系统不自动移动真钱、无自动退款路径;测试只动测试账号台账。

## 3. 硬线(停下来问 Zihao)

- 破坏 git 历史:`push --force` 到 master / `reset --hard` / 删 tag / 删 branch。
- `push --no-verify` 绕闸:永远不许。
- 删表 / 删字段 / `DROP`。
- **其余一切改动**:自己写 → 自己验 → 自己 `git push origin master`(push 即上线),不分高敏低敏、不等任何人在场;改坏了自己 `git revert`,不把红的留在 master。

## 4. 做法在 skills 里(按需装载,不用背)

| 什么时候 | skill |
|---|---|
| 改完要验 / 要 push / 判 CI 是否真绿 | `verification` |
| 动前端或任何用户可见 UI | `frontend-change` |
| 接 ERP / 老 PHP 系统 / 小助手 companion | `erp-integration` |
| 部署 + 写用户看的更新说明 | `deploy-release` |
| 生产 500 / 上传失败 / push 了线上没变 | `debug-prod-500` |
| 加或改任何用户可见文字 | `i18n-4lang` |
| 动手写码之前 | `new-feature-discovery` |
| Zihao 说"收尾 / 换窗口 / 今天到这" | `wrapup` |

机械闸清单 + 逐道自查命令 + 豁免语法:`docs/GATES.md`。棘轮豁免写在 commit message:`RATCHET-EXEMPT: <file> +<N> · <理由>`;新增 `ensure_*` 写 `NEW-DEBT-EXEMPT: <理由>`。

⚠️ **本地 pre-push 钩子目前是关的**(`core.hooksPath` 没指向 `scripts/git-hooks`)→ 真正拦你的只有 CI 事后红,所以 push 前自己手跑:`PYTHONIOENCODING=utf-8 sh scripts/git-hooks/pre-push`(不设编码变量会假红)。为什么还没挂上、要清什么债才能挂:`docs/context-engineering/2026-07-25-claude-md-simplify.md` 文末遗留表。

## 5. 文档地图(用 `@` 引用,别通读)

| 想干啥 | 读哪个 |
|---|---|
| 现在在做什么(活地图) | `CLAUDE.md/STATE_PEARNLY.md` 顶部状态卡(≤30 行)· 历史在 `STATE_ARCHIVE.md` |
| 业务概念 / 状态机 / 验收剧本 | `docs/agent/BUSINESS_GLOSSARY.md` · `ERROR_CODES_AND_STATES.md` · `ACCEPTANCE_PLAYBOOKS.md` |
| 设计系统(令牌 / 按钮 / 四态) | `CLAUDE.md/DESIGN_SYSTEM.md` + `static/pearnly-ui.css` |
| 什么算"完成" / 代码质量 | `docs/ENGINEERING_STANDARD.md` · `docs/CODE_QUALITY_CANON.md` |
| 为什么这么决策 | `docs/refactor/adr-*.md` |
| 远古历史 | `CLAUDE.md/ARCHIVE_CLAUDE_LEGACY.md` · `CLAUDE.md/BACKLOG.md` |

## 6. 数字只信脚本

任何文档里手写的行数、进度、百分比都可能过期。要数字就跑 `python scripts/refactor_progress.py`。
