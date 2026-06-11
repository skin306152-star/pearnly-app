# 施工窗口 KICKOFF · 银行对账+手工凭证(L档首例) + workers=4 + 做账小尾巴

> 前提:Zihao 已确认本目录五件套(01-05)与桌面稿 `Pearnly_银行对账+手工凭证_UI预览/`。
> 未确认不开工;确认后本文即施工指令,**照单施工,不重新设计,不缩水**。

## 开工前(60 秒纪律)

读 AGENTS.md → 跑 refactor_progress.py → 读 STATE 状态卡 → 读 docs/GATES.md(13 闸左移自查)→ 确认无其他窗口占 src/home/dist/build(有则先做任务 1/2 纯后端)。

## 任务顺序

**任务 1 · workers 2→4(纯后端,先做)**
给全部 ensure_* 启动 DDL 加 pg advisory lock 串行化(上次 4-worker 并发启动撞 ensure_erp_oauth_tables deadlock,见 STATE `cef351bf` 段)。本地起 4-worker 反复起停验证零 deadlock → 改 mrpilot.service workers=4 → 上线盯 journalctl 零 ERROR。改 unit 文件属 prod 写操作,改前知会 Zihao 一句。

**任务 2 · 逐笔审 choice 入参(纯后端小尾巴)**
review 端点加「服务/商品」choice 分叉入参(accounting-phase2 留的口),配单测。前端选择控件并入任务 3 的逐笔审小改。

**任务 3 · 银行对账 + 手工凭证(本目录主任务)**
- 照 04-技术方案逐条建:3 新表(ensure)→ `routes/accounting_bank_routes.py` → services/accounting 内 bank_recon.py 薄层(只 import 复用件,禁止重写解析/评分/过账/学习)→ 手工凭证 draft+模板扩展 → 前端 `acct-bank.ts`/`acct-bank-modals.ts`/`acct-manual.ts`。
- **位置钉死(不许自行决定)**:导航=做账组加子项「银行对账」,排「出账本」**前**;手工凭证**不进导航**,入口=做账主屏「+ 手工凭证」按钮;route 'acct-bank'/'acct-manual';i18n 键 acct-bank-*/acct-mj-* 进 static/i18n-data.js ×4 语;文档归 docs/accounting/bank-recon-mj/;**不碰「对账中心」(事务所工具组)任何文件**——边界见 01-审计 §3.2。
- **交互唯一基准 = 桌面 `Pearnly_银行对账+手工凭证_UI预览/03-交互原型.html`**(已真浏览器自查 0 JS 错):
  状态机/分区/文案/键盘流/二次确认/空载错成态/部分失败兜底/差额门控 **100% 照搬**,不重新设计。
  工程形态不照抄:原型单文件内联 CSS+模拟数据 → 正式实现走 home-01 令牌+acct-common+真 API+4 语 i18n;
  原型右下角「状态切换器」是预览工具,正式版不带。视觉登记视觉照搬闸;全 var() 无裸 hex。
- 每个小阶段完成:列改动文件→说明设计理由→跑测试→对照 05-验收清单→派 5 角色 agent 审查(产品/架构/UX/QA/安全)→修完才进下一阶段。
- 完工判定 = 05-验收清单全勾(V 组价值验收掐表/录屏留证),不是"功能能跑"。

**任务 4 · 丝滑专项+打包收编(若本窗口还有产能,且无他窗占前端)**
完整文案 docs/perf/00-丝滑专项+打包收编_KICKOFF.md;修复清单 docs/perf/INTERACTION_AUDIT.md;顺收 docs/ui/THEME_FOLLOWUP_BACKLOG.md #1-ter/#6/#7。产能不够就留给下一窗口,别压缩任务 3 的验收换它。

## 红线

push 即上线;改前端必 npm run build + git add static/dist + bump ?v=;真账号真浏览器验收;新文件全带测试+RATCHET-EXEMPT 透明记录;凭据走临时文件不落上下文;共享树只 add 自己 pathspec。
