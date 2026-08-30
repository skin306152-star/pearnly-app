# AGENTS.md · Pearnly 唯一入口(所有 AI 窗口先读这一页)

> **这是唯一的"必读"。** 故意保持一页。坑与红线在 `CLAUDE.md/CLAUDE.md`(轻量版约 90 行),干活的具体做法在 `.claude/skills/*`(按需自动装载,别背),业务概念在 `docs/agent/`。**进窗口先把这页 + STATE 状态卡读完 + 跑一次进度脚本**就能开工。
> (2026-07-25:CLAUDE.md 由 1470 行瘦身成轻量版 + 8 个 skill,旧全文冻结在 `CLAUDE.md/ARCHIVE_CLAUDE_LEGACY.md`,逐段对照表见 `docs/context-engineering/2026-07-25-claude-md-simplify.md`。)
> 最后更新:2026-08-30(GitHub CI workflow 281113573 已手动停用 · 本地风险分层验证与真实验收保留 · manual pinned-SHA CD)
>
> **🔴 常驻铁律(Zihao 拍板 · 任何窗口任何任务都执行)**:① 所有源码去 AI 味 + 注释/路数按大厂走(见 §2.6)② **(2026-08-12 改口径)Zihao 说"收尾"→ 轻收口:四角审查外派 DeepSeek worker、发现只记账进交接账本(次日首批修)、push 前 10 秒机械自检,然后 STATE→交接→清树;simplify 只在批次收口边界跑,收尾只兜当天没扫过的尾巴**(细则=`.claude/skills/wrapup`)。③ **(2026-07-01)任何任务自己做→自己检→自己验证闭环**:流程固定为本地风险分层测试(UI可先做本地真实浏览器)→commit/push→手动 pinned-SHA CD→回读生产 HEAD/service/ready→主控在该精确 production SHA 上做真实站点/真实环境/ERP report 预验收→Zihao 最终真机 OK；未完成最终验收不得称完成。**验证绑批次边界·不攒到最后(2026-07-11·vertical slicing)**:每切完一个可独立验证的批次就地验——命中任一=大批次当场验(高敏路径 登录/OCR/计费/推送/POS 收款/多租户/RLS/迁移 · 用户可见 UI · 新 flag/路由/迁移 · ≥~200 行或一个独立功能单元);小批次(纯格式化/docs/测试-only/无运行时面重构/<~50 行机械改)并到批次末或交付前一起兜。④ **(2026-07-11)动手写码前先做 discovery**:每个功能/派单前先写「场景+对标」——JTBD 真实场景 / RICE·Kano 判实用性(警惕 feature creep)/ 便利性(减摩擦·手机优先·危险操作确认·四态诚实)/ 照抄成熟产品 design pattern(Loyverse·Square…·Jakob's Law),别从代码结构倒推(见 [[design-from-real-scenarios-ref-market-leaders]])。
> **📐 通用工程标准(大厂级约束基线)**:见全局 `~/.claude/CLAUDE.md` 挂载的《通用工程标准(任意项目通用)》(正本在 `~/.claude/`·所有项目通用)。本项目铁律 = 它的超集 + Pearnly 特例;冲突以本项目为准。
> **🔒 防屎山闸已切硬门(2026-06-03)**:size+ratchet 进 pre-push 硬拦；GitHub CI workflow `281113573` 已于 2026-08-30 手动停用，`ci.yml` 保留作历史/可恢复配置。新增文件触发 ratchet 净增 → commit 写 `RATCHET-EXEMPT: <file> +<N> · <理由>`。真实用户功能必须在候选 production SHA 上由主控做真实 E2E/真机、截图与 ERP report 回查，不因关闭自动闸降低质量。**

---

## 0. 进窗口 60 秒必做(顺序别乱)

```
1. git branch --show-current        # 不是 master 立刻 git checkout master(铁律 #14)
2. python3 scripts/refactor_progress.py  # ← macOS 默认只有 python3;看【实时】数字!
3. 读 CLAUDE.md/STATE_PEARNLY.md 顶部「状态卡」(分割线以上 · ≤30 行 · 当前 task/最后 commit/未 push)
4. 读本文件 §2(今天敲定的认知)+ §8(文档地图)+ docs/agent/TASK_MODES.md(识别 Zihao 要哪种活)
5. git log --oneline -10 + git status   # 有没有本地未 push 的 commit
```

> **数字只信脚本**:STATE / 主计划 / 任何文档里手写的"home.js 多少行"都可能 stale。要数字 = 跑 `scripts/refactor_progress.py`。这条是治漂移的第一招。

---

## 1. 当前在干啥(2026-07 · 整顿核心已收官 → 正常产品开发)

- **▶ 当前主线(2026-07-14 更新)**:**Pearnly AI(TaxOps 月结 Agent · pearnly.com/ai)**——MC3 端到端金标真跑已收官(pp30 四数逐字命中官方),当前推进 SA-3 银行流水倒推销项及后续队列。施工体系=`桌面 pearnly ai\施工体系-Fable5窗口SOP-2026-07-10.md`(主窗策划验收·子代理施工),任务板=`桌面 pearnly ai\Pearnly-AI-进度.md`。**唯一活地图 = `CLAUDE.md/STATE_PEARNLY.md` 顶部状态卡**。历史主线(对话 Agent M1,2026-07-01 全线收官放量 all)见 `docs/agent/MASTER-PLAN.md`;下面 2026-06-03 一段是整顿收官时的历史快照,已不代表当前主线。

- **当前打法**:**3 窗口并行 loop**(ADR-011 + `docs/refactor/PARALLEL_LOOP_DISPATCH.md`)· A 后端 / B 前端 / C 文档测试 · 按文件 ownership 切不撞车。整顿封锁期(0 新功能)已于 2026-07-01 解除,现在是正常产品开发;拆巨石的范式全在记忆里([[giant-function-decomposition-playbook]] / [[directory-reorg-playbook]] / [[c9-store-centralization-bankrecon]])。
- **找下一个 task**:`REFACTOR_MASTER_PLAN.md` 顶部「当前进度看板」。
- **你的身份**:整顿主控/指挥官 · Zihao 非技术零代码 → 你全包(研究/派工/守门/E2E自测/查CI/上线/更文档)· Zihao 只:① 点权限框 ② 像用户验收 ③ 涉钱/登录拍板。

---

## 2. 今天敲定的认知(2026-05-29 · 防新窗口再踩 / 再讨论)

1. **行数:源码"拆"不"压" · 成品才压。**
   - 大厂(Chrome/Claude)你看到的小行数 = **成品**(HTML 外壳 + minify 后的 bundle)· 真源码是几千个小文件。
   - 目标 = **没有单个源文件 > 500 行**(拆成 50-100 个小模块),**不是**把某个文件写短。
   - "home.js < 200 行"指的是**入口/bootstrap 源文件**,业务全在 `src/home/*`。
   - 成品体积靠 **Vite build + minify**(= 计划 E7),不是手写。**别再问"能不能把 home.js 压到极致"——答案永远是:拆,不压。**
2. **防屎山靠机械闸,不靠自律。** check_file_size + check_line_ratchet(行数只降不升)由本地 pre-push 保留；GitHub CI 当前停用，按风险分层运行 lint/unit/真 PG/HTTP 检查。
3. **改动三标准**:加新功能=新模块(不进巨石,铁律 #17);改旧功能=先有测试再改;推翻重做=`git rm` 旧的不留 `.deprecated/.legacy` 僵尸(铁律 #7)。
4. **机械闸唯一清单 = `docs/GATES.md`**(本地 pre-push 与按风险分层的自查命令、豁免法都在那页；GitHub CI 历史 workflow 当前停用)。别在别处另记一份计数,会漂。
5. **代码像资深工程师写的,不像 AI 生成的**:源码(新旧都要)**去 AI 味** —— 无过度注释/无 emoji/无防御冗余/无泛化命名(`data`/`temp`)/无调试残留(console.log/print)/DRY/用语言惯用法。拆模块时顺手清,I6 收尾审计。**🛡️ 机械闸(2026-06-01 加·别只靠自觉)**:`scripts/check_ai_smell.py` 已挂 pre-push 第 7 道,改前端 src JS 时机械拦【注释里的 emoji】+【console.log 调试残留】(模板内产品 emoji 放行)。它只查本次改动文件——碰到旧模块带 emoji 会拦,顺手清掉再推。**全套大厂标准(源码→产品→流程→审核→测试→CI/CD→验收→安全→文档)= `docs/ENGINEERING_STANDARD.md`**,那是"拿得上台面"的 Definition of Done。

## 3. 五条最高红线(违反=事故)

1. **workspace_client_id ≠ history.client_id**(账套主体 ≠ 发票买方)· 永不混用同字段 · 见 `docs/agent/BUSINESS_GLOSSARY.md`。
2. **`erp_push_logs` 是推送状态唯一源**(铁律 #12)· 不建第二套状态表/字段 · 批次态从它派生。
3. **rows=0 / needs*mapping / failed / blocked / retrying / ERR*\* 绝不显示"完成/成功"** · 见 `docs/agent/ERROR_CODES_AND_STATES.md`。
4. **流程顺序固定**：本地风险分层测试(UI可先本地真实浏览器)→ commit/push → 手动 dispatch `manual-deploy.yml` 做 pinned-SHA CD → 回读生产 HEAD/service/ready → 主控在该精确 production SHA 上做真实站点/真实环境/ERP report 预验收 → Zihao 最终真机 OK。关闭自动 CI 不等于降低验收质量；未完成最终用户验收不得称完成。
5. **schema 改动只走 Alembic + 启动 ensure 双跑**(生产不跑 `alembic upgrade` · 见 §5)。

## 4. 机械闸(改完必跑全绿才 commit)

清单 + 触发条件 + 逐道自查命令 + 豁免语法:**`docs/GATES.md`(道数以那页标题为准,别信这里的手写数字)**。一键全套(等价 pre-push,不用真推):

```bash
sh scripts/git-hooks/pre-push     # Git Bash
```

**本地钩子 2026-07-31 起是开的**(`core.hooksPath` = `scripts/git-hooks`,Zihao 拍板装)→ push 前闸自己会跑,拦不住的才轮到 CI。装法/影响面/代价见 `docs/GATES.md` 顶部「装钩子」。要点:它写在 `.git/config` 里,**共享同一个 `.git` 的所有 worktree 一起生效**;路径按「谁在 push」各自解析(A 跑 A 的那份 `scripts/git-hooks/pre-push`);想空跑不真推用 `git push --dry-run`,一样会触发。

> 2026-07-25 修过这道的两笔债:① authz 覆盖闸此前只挂 pre-push 而钩子从没挂上 = **两边都没跑过** → 已加进 CI 主 job(FAIL mode);报红 85 条逐条读源码后**零真缺口**(68 条有门闸认不出 · 14 条真公开面 · 3 条封死端点),闸改成顺着调用看两层 + `tests/unit/test_authz_gate_detection.py` 锁住"真没门的照样报"。② 闸脚本中文输出撞 Windows cp874 会假红(exit 1)→ 钩子入口已 `export PYTHONIOENCODING=utf-8`;**手跑单个脚本时自己带上这个变量**。详见 `docs/context-engineering/2026-07-25-claude-md-simplify.md`。

## 5. 关键基础设施(少踩坑)

- 服务器 `root@66.42.49.213`(Vultr **新加坡** · 2026-06-11 迁同区 · DB RTT 1ms · 只 SSH key 登录) · `/opt/mrpilot/` · systemd `mrpilot` · uvicorn `--workers 2`。⚠️ 老文档里的东京 `45.76.53.194` 是 2026-06 的回滚兜底,**别再往那台推**。
- DB:Supabase Postgres(Pooler)· **生产不跑 `alembic upgrade`** → schema 靠启动 `ensure_*` 应用 · alembic/versions 仅留档。
- 部署:**本地风险分层验证 → `git push origin master` → 手动 dispatch `.github/workflows/manual-deploy.yml`(pinned SHA)→ `/internal/deploy/manual`→ git-deploy.sh → 回读生产 HEAD/service/ready → 主控真实站点/真实环境/ERP report 预验收 → Zihao 最终真机 OK**。GitHub CI workflow `281113573` 已手动停用，push 不自动部署；Dependabot 保留。服务器 TARGET_SHA 守卫 + flock 串行化双保险。验证通过后才可称功能完成。SSH 别名 `pearnly-prod`。详见 `docs/RUNBOOK.md`。
- gh CLI:直接 `gh`(已在 PATH · WinGet 装的;旧的 `C:\Program Files\GitHub CLI\gh.exe` 路径已失效)· 例 `gh run list --repo skin306152-star/pearnly-app --branch master`。

## 5-bis. 入口/路由地图

⚠️ **改任何对外页面前必看** → `.claude/skills/frontend-change/entry-map.md`(每个 URL → 浏览器实际拿到什么 → 该改哪个可读源 + 各自的坑 + 三条硬规)。改错位置 = 新域名永远跑老版本。`frontend-change` skill 会带你读它。

## 6. 新东西放哪

机械闸已强制(`check_new_debt` / `check_file_size`),写法见 `new-feature-discovery` skill:新路由 → `routes/*_routes.py` · 新业务 → `services/<域>/` · 新前端 → `src/home/*` · 新 CSS → 独立文件。

## 7. 交接 / 长跑上下文(治漂移第二招)

- **收尾铁律(2026-08-26 新口径·Zihao 说"收尾/今天到这/换窗口/下班/总结"时)**:轻收口 —— ① 需要审查时可派 `opencode run --agent worker`(DeepSeek),主控只汇总裁决;代理完成、失败或不再需要后**立即终止本次 opencode 进程树并确认本地模型不再占内存**;② 发现只记账进交接账本,次日首批修(当场只准 ≤几行零风险微修;例外=不修不能 push/会污染生产);③ push 前 10 秒机械自检(前端源→dist 同提交/大净增→RATCHET-EXEMPT/动文案→check_i18n --strict);④ **重写**(不是无脑追加)STATE 顶部「状态卡」→ 交接报告 → 清树。simplify 的正确时机=批次收口边界,收尾只兜当天没扫过的尾巴。细则=`.claude/skills/wrapup`。
- 历史明细往「分割线以下」追加。状态卡保持 ≤30 行,永远最新。
- 长跑 loop:每轮跑脚本看真数字 + 抽代码前 re-grep 真实行号(别信文档行号)+ 每轮写状态卡 → 压缩后重读 = 一页 + 脚本,永不漂。
- **上下文精度铁律(2026-08-13·额度黑洞根治)**:真相落盘(目标/决策/约定 当场写 任务板/状态卡/交接账本,不留在对话)· worker 交摘要+全文落盘 · 压缩//clear 后必先重读状态卡+任务板再干活。**机械强制,不靠自觉**:SessionStart 横幅 + PostCompact 钩子自动注入(`scripts/session_banner.sh` + `scripts/state_reread.sh`)。精度靠磁盘,不靠大上下文。

## 8. 文档地图(别全读 · 按需取)

| 想干啥 | 读哪个 |
|---|---|
| **每窗口必读** | 本文件 + STATE 状态卡 + 跑 `refactor_progress.py` |
| 识别 Zihao 要哪种活 | `docs/agent/TASK_MODES.md` |
| 找下一个整顿 task | `REFACTOR_MASTER_PLAN.md` 进度看板 |
| **大厂全流程标准 / 什么算"完成"** | `docs/ENGINEERING_STANDARD.md`(Definition of Done · 含去 AI 味) |
| 3 窗口并行 loop 指令 | `docs/refactor/PARALLEL_LOOP_DISPATCH.md` |
| 拆巨石作战手册 | `docs/refactor/BATCH_STRATEGY.md` |
| 业务概念 / 状态机 / 验收剧本 | `docs/agent/BUSINESS_GLOSSARY · ERROR_CODES_AND_STATES · ACCEPTANCE_PLAYBOOKS` |
| 销项发票 · 开票模块规格 | `docs/sales-module/docs/15`(买方动态表单)· `16`(后端合规/折扣/纸张/留底/审批/日期/模板)· `13`(逐 PO 计划) |
| **ERP 复核工作簿 / 回导闭环** | `docs/erp/ROUNDTRIP-REVIEW-WORKBOOK.md`(会计导出→改→回导重推 · 方向靠 Sheet 不靠猜 · 四个反复踩的坑) |
| **LINE 进票据(做后端前必读)** | `docs/line-platform/02-procurement-canon.md`(采购进项产品正本·旧讨论冲突裁决·P1E口径)+ `docs/smart-intake/09`(图片识别核心)+ `docs/smart-intake/10`(文本路:回复护栏/意图路由/模糊字段映射)· 两条腿共用字段 schema/确认卡/下游 |
| **对话 Agent(当前主线 · M1 WP1~5 已上线)** | `docs/agent/MASTER-PLAN.md`(全景 + 为啥"插座插头" + 里程碑 + 工作包)· `docs/agent/M1-SOCKET-DESIGN.md`(技术总纲)· `docs/agent/CONVERSATION-SPEC.md`(对话文案规范)· `services/agent/README.md`(每文件职责) |
| **智能管家 steward(/ai 对话入口 · 后端 40 模块 20 工具)** | `docs/ai/STEWARD-MAP.md`(模块地图 + 工具表 + 一条请求的全链 + 两个 flag 的真实可见面 + 本地跑法与 worker 抢单的坑) |
| **产品北极星 · 模块化平台(防跑偏)** | `docs/PRODUCT_VISION_MODULAR.md`(身份一句话 + 底座/模块/出口三层 + 模块化六原则 + 业态套餐)· 加功能前先对一遍 |
| 为啥这么决策 | `docs/refactor/adr-*.md`(ADR-001~011) |
| 坑 / 业务红线 / 硬线 | `CLAUDE.md/CLAUDE.md`(轻量版 · 约 90 行) |
| 干活的具体做法 | `.claude/skills/`:`verification` `frontend-change` `erp-integration` `deploy-release` `debug-prod-500` `i18n-4lang` `new-feature-discovery` `wrapup` |
| 旧 30 铁律全文(已冻结) | `CLAUDE.md/ARCHIVE_CLAUDE_LEGACY.md` · 对照表 `docs/context-engineering/2026-07-25-claude-md-simplify.md` |
| 远古历史 | STATE 分割线以下 / `CLAUDE.md/BACKLOG.md` |
