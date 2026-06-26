# 丝滑专项 + 打包收编 · 窗口 kickoff(2026-06-10 备好 · 等报税前端窗口收尾后启动)

> 复制本页全文开新窗口即可。背景:Zihao 2026-06-10 实测全站按钮交互卡顿;诊断窗口已立项出报告;另 POS/console 仍裸发源码未进打包管线。两件事同属"摸起来像大厂",合一窗。

---

【丝滑专项 + 打包收编窗口 · Zihao 已授权自做自检,自检全绿即 push】

⚠️ 启动条件(缺一不开工):
- 报税前端窗口已收尾 push(本窗口独占 src/home + static/dist + npm build)
- 杂项诊断窗口的 docs/perf/INTERACTION_AUDIT.md 已产出(任务A的修复清单依据;若还没有,先做任务B打包,A 等报告)

第0步:读 docs/GATES.md 并跑全套闸基线(知道哪些红是存量;新债别背锅)

必读:
1. AGENTS.md + CLAUDE.md/CLAUDE.md
2. docs/perf/INTERACTION_AUDIT.md(最慢交互 Top10 + 归因 + 修复清单)
3. docs/ui/THEME_FOLLOWUP_BACKLOG.md 第 8 项(打包收编)
4. memory: frontend-asset-bundling-playbook(E7 范式:CSS 独立 link 防闪/JS 分组保时序/dist 入 git)
   + pos-frontend-final-tax-report-offline(B5 离线 PWA:sw 外壳缓存/IndexedDB outbox/同步引擎)
   + purple-theme-v2-confirmed 施工坑(PS5.1 读 UTF-8 必用 Edit 工具/注释里别写 hex)

任务A · 交互丝滑(数据驱动,照 INTERACTION_AUDIT 清单,不撒胡椒面):
- A1 全局 withLoading(btn, fn) 助手:点击→立即禁用+spinner→完成/失败必恢复;先接报告 Top10 交互,再批量铺(全站 await api 点 ~231 处,可分批,Top 优先)
- A2 乐观更新:toggle/勾选/小写操作先改界面后发请求,失败回滚+toast(四-bis 三态纪律)
- A3 innerHTML 局部化:报告点名的整段重绘改行级更新(只改 Top offenders,别全站重写)
- A4 GET 缓存:切页/切 tab 先显上次数据后台静默刷新(stale-while-revalidate,简单内存缓存即可)
- A5 验收=数字:同口径复测 Top10 交互「点击→首个视觉变化」耗时,before/after 写进报告;目标全部 <100ms 有视觉反馈
- A6 轻量闸:新增 click+await 必须走 withLoading(grep 模式闸进 check_ui_consistency 或独立脚本,存量棘轮)

任务B · 打包收编(view-source 成品化,E7 范式补全):
- B1 console 收编:Vite 加 console 入口→产物进 static/dist→console.html 改引 bundle+bump;console-i18n 数据可仿 i18n-data 保独立
- B2 POS 收编(⚠️高敏,POS 离线链路红线):同法 Vite 入口;但 pos-sw 缓存外壳清单必须同步改(文件名/路径变了)+ 缓存名 bump;**离线 E2E 全量重验**(B5 基准 17/17:断网卖货→outbox→恢复同步→本地算价 pos-totals)+ 餐厅/零售/药房三业态真浏览器回归;离线验不绿 = B2 整体回退,别带病上线
- B3 闸扩面:check_asset_bundling 覆盖范围加 static/pos + static/console(新页面裸发源码 = push 拦);GATES.md 同步更新该行
- B4 顺手:bundle 体积棘轮若杂项窗口没做(E6),在此落地

红线:
- 不改任何业务逻辑/接口契约——本窗口只动"反馈/渲染/打包"层
- POS 离线链路改动必真验,不许"应该没问题"
- 主按钮纯色 var(--accent)/状态色边界(purple-theme memory)不动
- home.html CRLF;共享树只 add 自己 pathspec;改前端必 build+add dist+bump ?v=

自检(全绿才推):
- A:Top10 交互 before/after 数据表(真浏览器测量,标环境);全站抽 20 个按钮点了立刻有反馈
- B:console/pos view-source 只见外壳;POS 离线 E2E 全绿;三业态收银真浏览器回归;视觉闸绿
- 守门全套绿(GATES.md);完成更新 STATE + memory(丝滑专项落地·POS/console 已成品化·闸已扩)
