# 🆘 Zihao 救命指南 · 整顿期任何时候打开都能接上

> **写给**:Zihao(产品经理 · 不写代码)
> **场景**:窗口崩了 / 不知道下一步 / 想新开窗口接力 / 想催进度
> **原则**:大白话 · 全是"该做什么"不是"为什么"
> **最后更新**:2026-05-29 · 3 窗口并行(A 后端/B 前端/C 文档测试)· 已上 SessionStart 自动入口 hook + 一页入口 AGENTS.md

---

## 🟢 此刻在跑什么(2026-05-29 · 3 窗口并行)

打法 = 3 个独立 Claude Code 窗口按【文件分工】并行 · 互不撞车(权威:`docs/refactor/PARALLEL_LOOP_DISPATCH.md`):

| 窗口 | 只碰 | 在做啥 | 怎么看进度 |
|------|------|--------|-----------|
| **窗口 A · 后端** | app.py / db.py / services | 拆后端巨石到验收行数(B2/B1) | `git log --oneline \| grep REFACTOR-WA` |
| **窗口 B · 前端** | home.js / home.html / home.css / src/home | 拆前端巨石到地板(C1/C3) | `git log --oneline \| grep REFACTOR-WB` |
| **窗口 C · 文档测试** | docs / 测试 / 脚本 / .github | 文档扫荡 + D3/D4 测试 + 覆盖率 | `git log --oneline \| grep REFACTOR-WC` |
| **对话窗口**(可有可无) | — | 跟 Claude 商讨策略 · 不在 loop 里 | 崩了不影响 A/B/C |

**关键**:A/B/C 在独立进程里跑 · 对话窗口崩了 100% 不影响它们。「Loop 1」= A+B 一起把巨石拆到地板这个阶段。
**新机制(2026-05-29)**:每个新窗口启动会被 SessionStart hook 自动塞「入口 + 真数字 + 当前 task」· 不用你贴长说明。

---

## 📌 日常怎么开窗口操作(2026-05-29 · 治漂移后最常用 · 先看这段)

> **定心丸**:项目「大脑」已搬进 git 仓库(`AGENTS.md` / STATE 状态卡 / `PARALLEL_LOOP_DISPATCH.md` / `ENGINEERING_STANDARD.md`)· **不在任何聊天窗口里**。窗口随便关 · 新窗口开了照样接上。**不再需要专门留一个"指挥窗口"。**

每次开窗口 · 就三种情况:

| 你想干啥 | 你怎么操作(就一两步) |
|---|---|
| **① 跑整顿拆巨石(无人值守长跑)** | 开窗 → 说一句「读 docs/refactor/PARALLEL_LOOP_DISPATCH.md · 按窗口 A 跑 loop」(B/C 同理)→ Shift+Tab 切 auto-accept → 它自己跑。**长指令已存那文件 · 不用 Claude 重新生成 · 也不用你贴一大段。** |
| **② 做件具体的事(修 bug / 加功能 / 问问题)** | 开窗 → 一句话说要干啥(「修 X bug」「客户页加搜索」)→ hook 已自动塞现状 · 它直接照大厂标准(`ENGINEERING_STANDARD.md`)干。**不用贴长说明 · 不用先解释项目。** |
| **③ 看进度 / 聊策略(像跟我现在这样)** | 开窗 → 「现在整顿到哪了?下一步?」→ 它有真数字 + 状态卡 · 直接答。 |

- **关了窗口怎么办**:毫无影响 · 大脑在仓库不在窗口 · 新窗口 hook 自动接上。
- **还需要长指令吗**:不用了 · 降级成「一句话」。长 loop 指令存在 `PARALLEL_LOOP_DISPATCH.md` · 要用就让窗口去读那文件,或复制粘贴。

---

## 🆘 我(对话窗口)崩了怎么办

### 第 1 步:别慌 · 先看 A 和 C 还在不在

打开你电脑上**另外 2 个 Claude Code 窗口**(窗口 A · 窗口 C):
- 还在显示 "✽ 思考中..." / "Brewed for X min" → 它们在跑 · 没事
- 显示"等待输入"或闪烁光标 → 它们 dynamic 自调度睡眠中 · 没事 · 会自动醒
- **完全黑屏 / 没反应** → 也别慌 · 它们写的代码已经 push 到 GitHub · 进度都在文件里

### 第 2 步:新开一个对话窗口接力(可选)

如果你想继续找 Claude 商讨,新开一个 Claude Code 窗口 · 跟它说:

```
读 docs/refactor/ZIHAO_RECOVERY_GUIDE.md(就是本文件)+ CLAUDE.md/STATE_PEARNLY.md 头部 ·
帮我看下窗口 A 和窗口 C 现在跑到哪了 · 告诉我下一步该做什么。
```

它会自动接上 · 跟我说的一样。

### 第 3 步:啥也别动 · 等窗口 A / C 跑完

- 电脑保持开机 + 联网就行
- 不需要你操作
- 跑完它们会在 STATE_PEARNLY.md 头部写「BC 阶段全部完成」或「窗口 C 全部完成」

---

## 📋 整顿期全图 · 3 个 Loop 路线

```
现在 ────────────────────────────────────────────► 整顿期完成
[Loop 1 · 拆 BC 巨石]   [Loop 2 · 加固]   [Loop 3 · 性能+收尾]
       ↑ 正在跑              ↑ 等 Loop 1 完成    ↑ 等 Loop 2 完成
       1-3 天                 1-2 周               1-2 周
       窗口 A 在做             你新开窗口贴指令     你新开窗口贴指令

       同时:窗口 C 在做防屎山闸+文档+测试(独立轨道 · 跟 Loop 1 不撞)
```

**总时间**:3 个 loop 并行 · 1.5-2.5 周整顿期收官(原本单 loop 串行要 3-5 周)

---

## 🎯 Loop 1 跑完后(窗口 A 报"BC 完成"时) · 你要做的

### 怎么判断 Loop 1 真跑完了

打开窗口 A · 看 STATE_PEARNLY.md 头部 · 如果出现:

> **BC 阶段全部完成 · 17 E2E 全绿 · 等 Zihao 验收**

或者满足这 4 个数字:
- `wc -l app.py` < 500
- `wc -l db.py` < 500
- `wc -l home.js` < 200
- `wc -l home.html` < 1000

= Loop 1 跑完了 ✅

### 立刻做的事 · 2 步

**步骤 1** · 关掉窗口 A(或让它停)· 新开一个 Claude Code 窗口 · 把下面整段贴进去:

```
/loop 自主整顿 Loop 2 · 核心加固 + 防屎山闸激活 + B 后端剩 + C 前端剩 + D 测试剩 · 无人值守 · 你自己跑到完别等我:

【身份】
你是整顿主控/指挥官。Zihao 不在键盘前。你全包:研究 / 派工 / 接线 / 跑守门 / 真账号 E2E 自测 / 查 CI / 上线 / 更新文档。不要问任何问题 · 不要等任何确认。

【开工前 60 秒必读】
1. CLAUDE.md/CLAUDE.md(铁律 #14/#16/#19/#20/#25/#26/#27/#28)
2. CLAUDE.md/STATE_PEARNLY.md 头部
3. CLAUDE.md/REFACTOR_MASTER_PLAN.md(找当前 task)
4. docs/refactor/BATCH_STRATEGY.md §9.5 + §10 + §13
5. docs/refactor/AUTONOMOUS_LOOP.md + adr-009 + adr-010(防屎山闸设计)
6. docs/refactor/ZIHAO_RECOVERY_GUIDE.md(看 Loop 2 范围)
7. echo $env:PEARNLY_E2E_USER 确认账号在环境变量

【范围 · 按 4 块顺序】

第一块 · 激活防屎山闸(0.5 天 · 优先)
1. 跑 wc -l app.py db.py home.js home.html · 确认全部 < 验收行数 · 否则停下报告"Loop 1 没跑完"
2. 改 .github/workflows/ci.yml · lint-size job 把 continue-on-error: true 改成 false(切 fail 模式 · 真挡 push)
3. 跑一次假超行 commit 验真挡(模拟一个超行 commit · CI 必须红)
4. 改 CLAUDE.md/CLAUDE.md 加一条 · 防屎山闸已激活

第二块 · B 后端剩 8 项(3-5 天)
B3: 所有 ensure_* 迁 Alembic(25 个 · 一次一个 · git-deploy.sh 加 alembic upgrade head 钩子)
B4: /health + /ready 端点(DB / Gemini / SMTP / LINE 各 check)
B5: API 全局限流(slowapi · 每 IP/每用户/每 endpoint)
B6: 结构化日志(logger JSON · request_id / user_id / tenant_id 全链路)
B7: 错误日志聚合(自建简单版 · 写 errors 表 + admin 后台时间线)
B8: 多租户 RLS 加强(Supabase RLS · DB 层强制 · spec 12 升回 5/5)
B9: DB 索引审计(EXPLAIN 慢查询 · 加缺索引 · 删没用)
B10: DB 连接池调优(psycopg2 pool size + lifecycle)

第三块 · C 前端剩 5 项(3-5 天)
C4: Design System 组件库(按钮 / 输入框 / Modal / Toast / Card / Table 至少 8 个)
C5: TypeScript 化前端(src/home/*.js → .ts · 目标 80%+)
C6: i18n 拆 .json(home.js 4 个翻译块 → i18n/<lang>.json + 按模块再拆)
C7: 可访问性 a11y(WCAG 2.1 AA · 屏幕阅读器 + 键盘 + 对比度)
C8: 移动端真适配(iPhone/Pixel chrome devtools 真测 + Playwright 视口测试)

第四块 · D 测试剩 4 项(2-3 天)
D2: Integration tests 20+(API + 真 DB + Mock 外部 Gemini/LINE/Gmail)
D3: 死灰复燃守门(扫死代码清单 · 每条加 1 个 CI 守门 · 复活即红)
D4: 测试覆盖率达 70%(pytest-cov · fail_under=70 棘轮)
D5: Visual regression(Playwright screenshot diff · 10 个核心页面 baseline)

【铁律】
沿用 Loop 1:re-grep 真实行号 / 6 道门 / 单独 push / gh run watch CI 真绿 / 高敏块 E2E 闸 / 红即 revert / 每轮写 STATE + 主计划 + BATCH §10。

【完成判定】
CLAUDE.md/REFACTOR_MASTER_PLAN.md 进度看板上 B/C/D 阶段全部 ✅ + 防屎山闸 fail 模式上线 + 写 docs/refactor/LOOP2_COMPLETE.md 总结成果。

到这才停。不许问 · 不许等。
```

**步骤 2** · 关窗口 · 让它跑 1-2 周 · 偶尔回来看看 STATE_PEARNLY.md 头部

---

## 🎯 Loop 2 跑完后(看到「LOOP2_COMPLETE」)· 你要做的

### 立刻做 · 同样 2 步

**步骤 1** · 新开 Claude Code 窗口 · 贴下面整段:

```
/loop 自主整顿 Loop 3 · HTML/CSS minify + 状态管理 + Cloudflare CDN 收尾 + E/F/G/H/I 剩 · 无人值守:

【前置确认】
1. 跑 cat docs/refactor/LOOP2_COMPLETE.md · 确认 Loop 2 已收官
2. 跑 git log --oneline -5 · 确认 master 干净
3. echo $env:PEARNLY_E2E_USER 确认账号在
不满足任一 → 停下报告 Zihao

【范围 · 按顺序】

第一块 · HTML/CSS minify(A10 新增 · 1 天)
1. 装 vite-plugin-html-minifier-terser + cssnano
2. vite.config.js 加 home.html 作为 entry + plugins
3. 部署改为提供 dist/ 产物(改 FastAPI 静态路径 · git-deploy.sh 同步)
4. 守门:生产 view-source < 10 行 · gzip 后体积下降 ≥ 40%

第二块 · 简单状态管理(1 周)
5. 写 src/home/_store.js(几百行 · pub/sub + immutable update · 不用 Redux)
6. _userInfo / _quota / _results / currentRoute 迁进 store
7. 各模块改 store.subscribe(刷新) + store.update(改)
8. 测试:充值后所有显示余额的地方 0.5 秒内全自动同步

第三块 · E 性能 5 项(2 天)
E1: 性能基线(p95 / LCP 测量)
E2: 前端测速(Lighthouse CI)
E3: 修慢 API(EXPLAIN + 索引 + N+1 解)
E4: 修慢前端(打包分析 + 懒加载 + 防抖)
E6: 图片/PDF 预处理(Sharp 压缩 + PDF 缩略图)
(E5 Cloudflare CDN 单独由 Zihao 点开关 · 见下)

第四块 · F 数据 3 项(1-2 天)
F1: Supabase Storage 接入(替代服务器本地存 PDF)
F2: 备份策略(每天 Supabase backup + 异地)
F3: 数据导出(GDPR 合规 · 用户自助下载所有数据)

第五块 · G 文档剩 5 项 + H 合规可自动部分(2-3 天)
G3-G7: ONBOARDING / OpenAPI / PR 模板 / CHANGELOG / CODEOWNERS(窗口 C 没做的)
H2: Cookie 同意横幅(4 语)
H3: 数据真删 GDPR API
H6: API key 轮换机制

第六块 · I 抛光 5 项(1-2 天)
I2: 死代码清理(扫零引用)
I3: 性能 review(整顿前 vs 整顿后对比报告)
I4: 文档 review(全文档 link check + typo)

【完成判定】
所有 A-I 阶段 ✅(H1/H4/I5 留 Zihao) + 写 docs/refactor/REFACTOR_COMPLETE.md
"Pearnly 整顿期完成 · Google 级 90%+ · 解禁新功能开发"

到这才停。
```

**步骤 2** · 关窗口 · 等 1-2 周

---

## 🧑 你必须亲自做的 5 件事(整顿期里穿插)

这些 loop 干不了 · 因为要点鼠标 / 登第三方网站 / 法律事 / 你拍板 ·**总共耗时 1-2 天**:

### 1. 装 Docker Desktop(可选 · 1 小时 · 0 元)
- 用于 REFACTOR-A3 本地化 docker dev 环境
- 不装 loop 也能跑 · 装了对其他人协作有用
- 下载:https://www.docker.com/products/docker-desktop
- 装完跑 `docker --version` 验证

### 2. 装 Doppler CLI(可选 · 30 分钟 · 个人免费)
- 用于 REFACTOR-A4 密钥统一管理(替代 .env)
- 现在不装 loop 也能跑
- 下载:https://docs.doppler.com/docs/install-cli

### 3. 打开 Cloudflare CDN proxy(必做 · 10 分钟 · 免费)

- 登 https://dash.cloudflare.com
- 选 pearnly.com 域名
- 进 DNS 标签
- 找到 **pearnly.com** 和 **www.pearnly.com** 两行(Type 是 A 和 CNAME)
- 每行点 Edit → Proxy status 切到橙色云朵 → Save
- **只点这 2 行 · MX 和 TXT 都不要动**(否则邮件挂)
- 切完打开 pearnly.com 看能不能访问
  - 能访问 = OK
  - 报 ERR_TOO_MANY_REDIRECTS → 去 SSL/TLS → Overview → 改 Full (strict) → 等 30 秒重试

### 4. 找律师审隐私政策(可选 · 1 周等律师 · 5000-30000 baht)
- 用于 REFACTOR-H1
- 4 语(中/英/泰/日)隐私政策审稿
- Pearnly 在泰国卖 SaaS · 建议至少有泰语 + 英语合规版
- 现金充裕再做 · 不影响主流程

### 5. 触发另一个 AI 跑只读体检(必做 · 1 小时 · 0 元)
- 用于 REFACTOR-I5(整顿期最后一步)
- 打开 Claude 网页版(claude.ai)或 GPT
- 让它读完整顿后的代码 · 给"独立第三方意见"(不是这个 Claude 自我评分)
- 模板:"我整顿完了一个 Python+JS SaaS · 你帮我读 app.py / db.py / home.js / 测试目录 · 评分 Google 级 0-100% · 找出还没整顿到位的"

---

## 🚨 紧急情况怎么办

### 情况 1 · 某个窗口的 loop 跑 24 小时没动静

打开那个窗口看 STATE_PEARNLY.md 头部最后一条时间:
- 24 小时内有更新 = 还在跑 · 别动
- 24 小时没动 = 可能卡死 · 跟那个窗口说一句"现在跑到哪了 · 报告状态" · 它会重新启动

### 情况 2 · GitHub Actions CI 一直红

- 打开窗口 A 或 C · 跟它说:"最新 CI 红了 · 你查一下 gh run list · 看为啥 · 修好再说"
- 它会自己查 + 修 + revert

### 情况 3 · pearnly.com 访问不了

- 第一反应查磁盘满了没(铁律 #24):
  - 跟任意一个 Claude 窗口说:"ssh root@45.76.53.194 跑 df -h / · 看磁盘满了没 · 满了清 /tmp/pip-*"
- 第二反应查服务挂了没:
  - 跟它说:"ssh 跑 systemctl status mrpilot · 没活就 systemctl restart mrpilot"

### 情况 4 · 你想催 loop 快点跑

- 跟那个 loop 窗口说:
> 别再 ScheduleWakeup 等 25 分钟 · 做完一刀立刻接下一刀 · 直到完成判定才停。

### 情况 5 · 你想让 loop 停下来

- 跟那个 loop 窗口说:
> 停下 · 在 STATE 头部写"Zihao 手动暂停 · 当前进度:X" · 等我下一步指令。

### 情况 6 · 测试账号被锁(5 失败/30 分钟限流)

- E2E spec 跑多了会触发
- 等 30 分钟自动解
- 或者跟 loop 说:"妈的账号锁了 · 跳过 E2E 阶段 · 继续做不依赖 E2E 的活 · 30 分钟后再回来跑 E2E"

---

## 📊 进度看板 · 你怎么看(不用懂代码)

任何窗口跑 1 行命令:

```powershell
python scripts/refactor_progress.py
```

会输出像这样:
```
代码规模:    █████████░ 87%
测试覆盖:    ████████░░ 78%
基础设施:    ██████████ 100%
综合进度:    █████████░ 88%
```

90%+ = 整顿期收官 · 解禁新功能。

---

## 🎯 整顿期完成后 · 你能做啥

(估计 2026-06-中 到 2026-07-初)

1. **解禁新功能开发** — Phase 6 进项管理 / 回 P0-VAT 主线 / 任何你想做的
2. **AI 偷不了懒** — 防屎山闸激活后 · AI 想塞巨石 push 会失败 · 永远不会再变屎山
3. **加载快 1 秒** — minify + CDN 上线
4. **看起来很专业** — view-source 几行 minified · 跟 Claude.ai / Google 一样
5. **bug 少 10 倍** — 状态管理 + 17 个 E2E + 70% 单测覆盖 · AI 改代码不会再连环爆

---

## 🆘 最简版"我啥都忘了"指南

如果你某天打开电脑 · 完全不知道自己在干啥:

1. 打开任何一个 Claude Code 窗口
2. 复制这一句话发过去:
> 读 docs/refactor/ZIHAO_RECOVERY_GUIDE.md 全文 + CLAUDE.md/STATE_PEARNLY.md 头部 · 告诉我现在整顿期跑到哪一步了 · 我下一步该做什么 · 用大白话别讲技术。

它会读完这份文档 · 把你状态完整回报。

---

## 💾 别动的文件 / 永远别删

- `CLAUDE.md/*.md` — 项目宪法 · 永远别删
- `docs/refactor/*.md` — 整顿计划 + ADR · 永远别删
- `tests/e2e/.auth/state.json` — 这个**可以删**(里面是测试账号 token · loop 跑完会自己删)
- `.claude/scheduled_tasks.lock` — loop dynamic 调度锁 · 别动

---

## 📞 你只需要记住的 3 件事

1. **别打断在跑的 loop** — 它们 dynamic 调度睡眠是正常的 · 不是卡死
2. **STATE_PEARNLY.md 头部 = 唯一真相** — 任何时候打开看头部就知道状态
3. **任何窗口崩了 → 新开一个窗口让它读本文件** — 100% 能接上

---

*本文档由 Claude(对话窗口)在 2026-05-28 撰写 · 为防 Zihao 找不到接力路径。*
*如果你看到这里还在迷茫 · 直接把整份文档发给任何一个 Claude · 说"我不知道下一步" · 它会告诉你。*
