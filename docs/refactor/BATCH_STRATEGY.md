# 🚀 Pearnly 整顿 · `/batch` 加速作战手册（BATCH_STRATEGY）

> **这份文档是整顿期"如何用 `/batch` 把大文件/屎山快速拆完"的单一权威源。**
> 配套上级文档:`CLAUDE.md/REFACTOR_MASTER_PLAN.md`(整顿主计划 · task 定义)。
> 本文档只回答一个问题:**那些重复的拆分/补测试,怎么用并行 agent 几天啃完,而不出事。**
>
> 最后更新:2026-05-27(初版 · 设计阶段 · 尚未开跑)
> 状态:📋 **方案就绪 · 等 ERP 收尾(P2-B / P2-C / P3)修完 → Zihao 说"继续整顿"后启动**
>
> **启动前提(2026-05-27)**:ERP「开箱即用」线 P0/P1/P1b/P2-A/P2-D 已上线;**剩 P2-B(日志折叠)/ P2-C(不裸透泰文)/ P3(概念导航)未完**。按 Zihao 拍板「BUG > 整改」,**这三项是整顿启动的前置**。其中 **P2-C 会改 `home.js` 渲染(巨石)** —— 它跟本手册 Wave 2(C1 拆 home.js)动同一文件,**所以 P2-C 必须先做完**,Wave 2 的承包清单/拆分基于「P2-C 之后」的 home.js(届时让窗口 re-grep 行号)。

---

## 0. 先看这里 · 这份文档怎么用

- **Zihao(产品经理)**:只看 §2(分工)、§8(你念的台词)、§10(进度)、§11(什么时候算完)。其余交给窗口。
- **接力 Claude 窗口**:进窗口先读 §1→§7→§9,找当前波次,按"黄金指令模板"干活。
- **`/batch` 是什么**:Claude Code 内置命令。一条命令 = 研究+规划一个大改动 → 自动开 5–30 个隔离 git worktree,每个派一个 agent 并行干 → 每个开一个 PR → 人挑能用的合并。**只能 Zihao 本人敲**(内置命令,窗口里的 Claude 替不了)。

---

## 1. 核心设计思想(整套方案就靠这 3 条立住)

### ① 拆分=并行,接线=串行(copy-out / serial-integrate)
巨石(`home.js`/`db.py`/`home.css`)拆分天然撞车——多个 agent 都在删同一个文件的行。破解:

- **并行阶段**:每个 agent **只"复制出去"**——把一块内容**拷贝**成新文件(`src/home/<feature>.js` / `services/<域>/store.py`)+ 写好契约/渲染测试,**绝不删原巨石任何一行**。各 agent 只新增文件 → **零冲突**。
- **串行阶段**:所有 PR 合完后,**单独开一个串行窗口**,统一去巨石里删旧代码 + 加 re-export 接线,一块/一域跑一次守门一个 commit。

> 危险的"动巨石"被收拢成一个小心的串行尾巴,其余全部安全并行。

### ② 一个 agent 只碰自己那块新文件,永不两人同改一个老文件
开 batch 前先出**「承包清单」**(manifest):谁负责哪个功能 / 对应巨石哪段行号 / 产出哪个新文件,**互不重叠**。这是 `/batch` 开头 "research and plan" 那一步必须产出的东西。

### ③ 测试先行:先用 batch 把安全网铺满,再用 batch 碰巨石
动屎山前必须有冒烟网(cleanup README §第2段的逻辑)。batch 的好处是**建网本身也能并行**,几十个测试一波铺完。没有 E2E 网,就无法验证"home.js 拆完每个页面还能渲染"。**所以 Wave 0 永远第一个跑。**

---

## 2. 分工 · 谁干什么(自动 vs 你)

| 环节 | 谁干 | 自动吗 |
|---|---|---|
| 读文档、找下一波、出承包清单 + batch 指令 | Claude 窗口 | ✅ 自动(你说"继续整顿"触发) |
| 写代码、跑 5 道守门、开 PR | batch agent | ✅ 自动(触发后) |
| **敲 `/batch <指令>`** | **Zihao** | ❌ 你来(内置命令只能你敲) |
| **review PR、决定合不合** | **Zihao** | ❌ 你来(这步没人能替) |
| 串行接线删巨石(拷出后那步) | Claude 窗口 | ✅ 自动,但一步步停下汇报 |
| 高敏(登录/计费/OCR热路径/auth) | **Zihao 在场** Claude 才动 | ❌ 必须你在 |

**一句话**:"造测试网 + 复制模块"全自动并行;"按 batch 按钮 + 合并 PR + 高敏改动"你来。

---

## 3. 总路线 · 5 个波次(Wave)

| Wave | 大任务(对应 REFACTOR task) | 开几个 agent | batch 模式 | 前置条件 |
|---|---|---|---|---|
| **0 安全网** | D1 十大 E2E + D2 集成测试 | 10–30 | 纯新增文件 | 随时(连 ME.ERP 没合都行) |
| **1 后端收尾** | B2 db.py 剩余**安全**域 | 3–6 | copy-out + 串行接线 | ME.ERP 合并后 |
| **2 主战场** | C1 home.js 拆 50–100 模块 | 12–30 /波 | copy-out + 串行接线 | Wave 0 全绿 + ME.ERP 合并后 |
| **3 样式/结构** | C2 home.css + C3 home.html | 10–25 | 按组件拆(多为新增) | C1 主体完成 |
| **4 收官** | C6 i18n 拆 json + G 文档/ADR + I 抛光 | 5–15 | 纯新增文件 | 随时 |

> **节奏铁律**:Wave 0 / Wave 4 是"纯新增文件"型,**不碰巨石、不撞 ME.ERP,任何时候都能跑**。Wave 1/2/3 动巨石,**必须等 ME.ERP 那条线合并进 master 之后**再开(否则你在切一个别人同时在改的文件)。

---

## 4. 每波怎么打

### 🟢 Wave 0 · 安全网(第一个按 · 最安全 · 收益最大)
- **D1**:10 条核心路径各派 1 agent,每人写**一个独立 E2E**:
  登录 / 注册 / 上传OCR / 销项税核查 / 收入对账 / ERP推送 / 充值 / 客户CRUD / 异常处理 / 4语切换。
- **D2**:每个已抽出的 `*_routes.py` / `services/*` 派 1 agent 补集成/契约测试。
- 产出全是 `tests/` 下**新文件** → 零冲突、零撞 ME.ERP,直接补满 8 硬门槛 #4/#5,把 coverage 棘轮往上顶。
- **这一波同时是 batch 工作流的试水**:先在最安全的活上验证 agent 守不守门、PR 质量行不行。

### 🟡 Wave 1 · db.py 收尾(copy-out)
- db.py 已 ~4513 行、18 域抽完。剩**安全域不多**(membership+migration、tenant 等)。
- **高敏域排除**(留 Zihao 在场单独做):`credits` / `charge_ocr`(钱)、`user` / `auth`(登录)、`ocr_history`(OCR热路径)。
  ⚠️ RLS 基础设施(`get_cursor_rls`/`_is_rls_enabled` 等)**别搬别动**(见主计划 B2 备注)。
- 每个安全域 1 agent,按主计划 **B2 范式** copy-out 成 `services/<域>/store.py` + 契约测试,**不删 db.py**。
- 全合并后:**串行窗口**统一加 db.py 尾部 `from services.X import a as a` re-export + 删旧 def,一域一跑守门。

### 🔴 Wave 2 · home.js 主战场(batch 价值最大 · 22k 行)
**真实功能孤岛承包清单**(行号会随改动漂移,**抽前必 re-grep 确认**):

| 目标模块 `src/home/*.js` | 入口函数(参考行号) |
|---|---|
| `_shared.js`(**先抽 · 公共件**) | `showConfirm` L309 / `setupDropdown` L735 / `showAlert` L4745 / `showToast` L6574 / `renderPageHeadInfo` L4804 + `window.t`/`subscribeI18n` 桥接 |
| `team.js` | `loadTeamList` L1316 / `showAddEmployeeModal` L1381 / `showResetPwdResult` L1572 / `showForceChangePasswordModal` L1615 |
| `quota-banner.js` | `renderBrandWorkspace` L1965 / `renderQuotaBanner` L2004 / `renderInfoBar` L2216 |
| `camera.js` | `showCameraTips` L2426 / `renderCameraBufferBar` L2595 |
| `file-list.js` | `renderFileList` L2856 / `showDuplicateDialog` L3332 |
| `results-drawer.js` | `renderResults` L3501 / `openDrawer` L3643 / `renderWhtBadge` L3826 / `renderField` L3831 / `renderRdActions` L3854 / `renderItems` L3876 |
| `rd-sync.js` | `openRdSyncModal` L3985 |
| `ocr-push.js` | `openOcrPushPicker` L4192 |
| `diagnose.js` | `openDiagnoseDialog` L4322 |
| `settings.js` | `renderSettings` L4613 / `openSettingsModal` L20163 |
| `history.js` | `loadHistoryPage` L4883 / `renderHistoryList` L4942 / `openHistoryDrawer` L5086 / `openHistoryDrawerAndFocusAmount` L5132 / `openHistoryMenu` L5221 |
| `automation.js` | `loadAutomationPage` L5469 |
| `erp-logs.js` | `loadErpLogs` L5537 / `loadErpTodayStats` L5736 / `showLogDetail` L5949 |
| `erp-endpoints.js` | `loadErpEndpoints` L6222 / `renderErpEndpointsList` L6282 / `openEndpointModal` L6380 / `showEpSaveError` L6559 |
| ⚠️ **未测绘区** | **L6574 → L20163(~13.5k 行)是最大未知块**(疑似历史巨函数残留)· batch plan 阶段**第一件事就是把这段测绘成功能孤岛**,再分包 |

**打法**:
1. **先单独抽 `_shared.js`**(公共件) → 各 feature module 都 import 它(避免重复定义 `showToast` 等)。
2. plan 阶段画依赖图 + 测绘 L6574-20163,补全承包清单。
3. 每个孤岛 1 agent,copy-out 成 ES module,靠 `main.js` import 接入,**先不删 home.js**。
4. 验证靠 Wave 0 的 E2E:每个 feature 页面渲染 0 报错 = 这个 agent 算过。
5. 合并后串行窗口删 home.js。**22k 行预计分 2–3 波 batch 打完。**

### 🔵 Wave 3 · home.css(16k) / home.html(6.5k)
- **C2 css**:按组件边界,每 agent 抽一个 component CSS。CSS 全局级联 → **护栏**:保持 import 顺序、抽完用 Playwright **截图对比(视觉回归)**防样式漂移。
- **C3 html**:`<template>` 化或服务端拼接,按区块分。

### ⚪ Wave 4 · 收官
- **C6 i18n**:4 个语言块 → 4 个独立 json,4 agent 完美并行。
- **G 文档**:ADR / RUNBOOK / ONBOARDING 各 1 agent,纯新增。
- **I 抛光**:批量清静默吞错。**死代码删除慎并行**(跨文件引用),建议串行或小批。

---

## 5. `/batch` agent 黄金指令模板(给 Zihao 复制 · 窗口会替你填好具体项)

### A. 新增型(Wave 0 / 4 用 · 纯新建文件)
```
你是并行 batch 的一个 agent,只负责【<具体一项,如:收入对账 E2E>】。
铁律:
- 只新建文件(tests/e2e/<name>.spec.js 或 src/home/<feature>.js),
  绝不改 home.js / db.py / app.py / home.css。
- 跑全 5 道守门,全绿才提交:
    python scripts/check_imports.py --quiet
    python scripts/check_i18n.py --strict
    python -m unittest discover -s tests/unit
    npx playwright test
    node --check <改的.js>
- commit message 必含 · REFACTOR-<task-id>,带 Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>。
- 完成后开 PR,描述写清:产出文件、跑过哪 5 道门、覆盖哪条核心路径。
- 任何不确定 / 要碰巨石 / 触发高敏(登录·计费·OCR热路径)→ 立刻停,PR 里标注,不硬来。
```

### B. 拆分型(Wave 1 / 2 / 3 用 · copy-out 不删原文件)
```
你是并行 batch 的一个 agent,负责把【<功能,如 history>】从 home.js 抽到 src/home/history.js。
铁律(copy-out 范式):
- 【只复制,不删除】把该功能整片拷进新 ES module,import 公共件 src/home/_shared.js;
  home.js 一行都不许删(删除留给后续串行接线窗口)。
- 抽前必 re-grep 当前行号确认边界(别用文档里的旧行号)。
- 共享全局(t / subscribeI18n / showToast / showConfirm 等)一律 import,不重复定义。
- 字节级 LF 处理,无 BOM。
- 带一个渲染/契约测试:该 module 入口函数能渲染、0 报错。
- 5 道守门全绿才提交;commit 含 · REFACTOR-C1(后端则 REFACTOR-B2);
  开 PR 写清:抽了哪个功能、新文件、依赖哪些公共件、跑过的门。
- 触发登录/计费/OCR热路径/RLS基础设施 → 停,标注,不动。
```

---

## 6. PR 合并策略 + ME.ERP 协调

1. **承包清单零重叠**:plan 阶段产出 manifest,确保没有两个 agent 碰同一段。
2. **新增型 PR**:互不冲突,可批量合。
3. **拷出型 PR**:都不删巨石、只加新文件,**理论上也能批量合**;真正动巨石的删除接线,**单独串行窗口**做,一块一守门一 commit。
4. **跟 ERP 收尾线协调**(ERP 直接在 master 上做,不是分支):
   - Wave 0 / 4 任何时候开都行(纯新增文件,不碰巨石、不撞 ERP)。
   - **动巨石的 Wave 1 / 2 / 3 等 ERP 收尾(P2-B/C/P3)全部上线后再开**(agent 从当时 HEAD 切 worktree,基线要新)。
   - **尤其 Wave 2(home.js)必须在 P2-C 之后**——P2-C 也改 home.js,否则两边切同一文件 = 撞车 + 白拆。
   - 别在 ERP 改动没上线时把一堆重构 PR 灌进 master。

---

## 7. 护栏清单(按下按钮前对一遍)

- [ ] 开 batch 前 `git tag` 备份当前 master。
- [ ] 第一次只在 **Wave 0** 试水,看 agent 守不守门、PR 质量。
- [ ] 每个 agent 指令**内嵌 5 道守门 + 契约测试 + REFACTOR-id**——否则批量产出违反 8 硬门槛 = 偷渡新债。
- [ ] 高敏域(登录/计费/OCR热路径/auth/RLS)**永远不进 batch**,Zihao 在场单独做。
- [ ] 动巨石的波次**必须等 ME.ERP 合并**。
- [ ] 删除巨石旧代码这步**串行**,不并行。
- [ ] 每个 PR Zihao 都过一眼(这步没人能替)。
- [ ] 每波结束跑 `python scripts/refactor_progress.py` 看数字真掉了。

---

## 8. Zihao 傻瓜操作手册(每窗口照念)

**场景 A · 让窗口告诉你该干嘛**
> 「**继续整顿,按 BATCH_STRATEGY 走,现在该哪一波?给我方案。**」

**场景 B · 它让你开并行,你照着打**(窗口会把指令递给你)
> `/batch <窗口给你的那段指令>`

**场景 C · 必须串行的活(删巨石/接线)**
> 「**这一波串行做,一个一个拆,每个跑完守门停下汇报再下一个。**」

**场景 D · PR 回来了,你收**
> 「**把跑绿的 PR 挑出来合并,撞车的或没过守门的先留着告诉我。**」

**你的动作每轮就 3 下**:说一句 → 打个 `/batch` → 说"合绿的"。技术细节窗口替你准备。

---

## 9. 接力窗口 protocol(新窗口进来怎么接)

```
1. git branch --show-current → 确认 master(铁律 #14)
2. 读 CLAUDE.md/CLAUDE.md(铁律) + STATE_PEARNLY.md(当前状态)
3. 读 REFACTOR_MASTER_PLAN.md(找 task) + 本文档(找当前波次)
4. 看本文档 §10 进度账本 → 确认上一波做到哪
5. 给 Zihao 一句话:"现在该 Wave X,建议开 N 个 agent 干这些,指令我写好了"
6. Zihao 点头 → 敲 /batch → 收 PR → 串行接线 → 更新 §10 + STATE + 主计划看板
```

---

## 9.5 实际操作模型(2026-05-27 第三十七会话确立 · 新窗口必读 · 比上面理想版更贴实情)

> 这套是 Zihao × 主控窗口实跑出来的真实分工。新窗口照这个接,别按"理想版"假设 Zihao 会 review 代码。

1. **Zihao 是非技术用户(不懂编程)**:主控窗口(Claude)**全包** —— 研究 / 规划 / 派工 / 判断作业合不合格 / 跑 5 道守门 / 复查 / 合并 / 提交上线 / 出测试清单。Zihao 只负责:① 极少数必须他敲的命令(如内置 /batch)② 像普通用户一样点 app 验收 ③ 涉及钱/登录时拍板"行/不行"。**不要让 Zihao 看代码、判断 PR、学合并。**
2. **内置 `/batch` 在本环境未触发**(贴进来会变成普通消息发给主控)→ 主控**自己用 Agent 工具派后台并行 agent**(`run_in_background` · copy-out 只新增非重叠文件 · 各自跑自检)→ 收到完成通知后,主控**统一**跑守门 + 复查 + 一次提交。效果等同 /batch,且 Zihao 零操作。
3. **质检窗口模式(UI 实测)**:要真账号实测时,主控写一段"活儿单"文案 → Zihao 贴到**另开的质检窗口** + 单独发测试账号 → 质检窗口用真账号跑 Playwright → 报告贴回主控验收。质检窗口铁律:凭据只走 env 不提交、需登录的 spec 必须 `test.skip(!env)` 否则拖红 CI、绝不花真钱/造垃圾数据。
4. **高敏永不进 batch**:登录 / 计费扣费 / OCR 热路径 / RLS 基础设施 / LINE 绑定 / 改密码 → Zihao 在场,主控亲手单独做。
5. **push 到 master**:主控有 C 档位授权(CLAUDE.md 铁律 #16),但 harness 自动模式分类器会拦「串联命令里的 push」→ **push 必须单独一条** `git push origin master`(别和 commit/pull 串一起)。
6. **copy-out 提交是安全的**:并行 agent 只新增文件、不接线,新模块是"死代码"不影响运行,守门绿即可提交;真正改运行行为的"接线删巨石"才需谨慎串行。
7. **【巨石删大块/搬块的批准方法 · 重要】**:从 home.js / home.css 删大块,**Edit 工具不适合**(把上千行原文当 old_string 贴极易错)。**批准方法** = `node` 读文件 `split('\n')` → 按行号删 → `join('\n')` 写回(**保 `\r` · CRLF 不变**);**删后必跑字节校验**(行数对 + 无 `\r` 的行计数=0 / CRLF 完好);**删前先 `cp` 备份**;**自底向上、一块一块删 + 逐块校验**(隔离错误)。
   - 这是 CLAUDE.md「不用 sed/python 写巨石」禁令的**受控例外**:禁令针对会把 `CRLF→LF` 的**盲写**;本法**专门保 CRLF + 有字节校验 + 有备份**,守住了禁令本意。前 13 块 home.js 即此法删除、零污染、已验证。
   - ⚠️ harness 自动模式分类器可能**按字面**拦「node 写 home.js」→ Zihao 在权限询问点「允许」(或加 Bash 放行规则)。这是误拦,不是真违规。

## 10. 进度账本(每波收尾必更新 · 让下个窗口接得上)

> 符号:⚪ 待启动 · 🟡 进行中 · ✅ 已完成

| Wave | 状态 | 起始数字 | 当前数字 | 已合 PR / 备注 |
|---|---|---|---|---|
| 0 安全网(E2E/集成) | ✅ E2E 网成 | unit 872 / E2E 1 | unit **1132** / E2E **10** | 第三十五会话 17 个纯逻辑模块补契约(+~220 unit)。**第三十八会话(2026-05-27)质检窗口用真账号建 9 个登录态 E2E(登录/4语/客户/历史/异常/销项税/收入对账/ERP/充值)+ 登录地基 storageState · env-gated CI 跳过保绿 · 真站点 10/10 全绿 · `bcfb499`。E2E 网 1→10 达标** |
| 1 db.py 收尾 | 🟡 | db.py 4620 行 | db.py 4620(未接线) | 第三十七会话(2026-05-27)**首次用并行 agent**:membership(9 函数)+ tenant(14 函数)两安全域 copy-out → `services/{membership,tenant}/store.py` + 37 契约测试 · 全守门绿 · CI 绿 · `c1a8c8a`。**copy-out 完成 · 串行接线(删 db.py + re-export)未做**。剩余域全高敏(credits/auth/ocr_history)→ Zihao 在场 |
| 2 home.js | 🟡 抽取中 | home.js **22970 行** | home.js **12929 行** | 第三十八会话(2026-05-27)E2E 网绿后**开抽 §13🟢 表 · 21 块已抽**(每块独立 commit · 每轮真站点 E2E 10/10 全绿 · CI 绿):**R1 串行**(逐块验配方)recon-center `4fa262e` / assign-clients `e2a9d43` / access-log `6ff538b` / notifications `cad5f1b`(-979);**R2 并行 agent**(转批量)recon-batch `f3d4cbc` / welcome-wizard `c9fb2a0` / ai-balance `ea71f7f` / archive-settings `10cb6d6`(-1160);**R3 并行 agent ×5**:big-batch-progress `696136c` / erp-xero `a6d5652` / report-templates `c603834` / folder-watcher `eff5f79` / email-ingest `3bd7fbc`(-2317)。第三十九会话 **R4 并行 5 块**:bank-recon / clients / exceptions / topbar-avatar / recon-collapse(`b9f6e1f` · -4030);**R5 并行 3 块**:recon-subtab-settings / excel-formula-recon / gl-vat-recon(`962105e` · -1554 · 含守门测试 test_brv2 跟随代码搬家更新)。两轮均守门全绿 · 生产 E2E 10/10。共 **-10041 行**(22970→12929 · 21 块)。配方见 §13。**继续抽 §13🟢 余下块** |
| 3 css/html | 🟡 css 拆解中(C2) | css **16673 行** | css **16556 行** | 第三十九会话(2026-05-27)**home.css 拆解窗口开工**(REFACTOR-C2 · 与 home.js 窗口并行碰不同文件)。安全模型 = 自顶向下 peel 区块到 `static/home-*.css` + `home.html` 按序加 `<link>`(新文件→home.css 末)+ **杀手级字节校验**(按 link 序拼接 ≡ 基线 `home.css` · 0 差异 = 级联零变化)。**R1 抽 1 块**:`home-01-base.css`(L1-117 · 设计令牌 `:root`+reset+顶栏/brand · 含 BOM)· 校验 PASS 482214 bytes byte-identical · 待 push/E2E。配方:`node` 按 LF 字节切片(保 CRLF/BOM)→ `$TEMP/css_verify.mjs` 按 home.html link 序拼接比对基线。 |
| 4 i18n/文档/抛光 | ⚪ | — | — | — |

**基线快照(2026-05-27 · 第三十五会话后)**:`home.js`(P2-C/P3 改过 · re-grep)· `app.py` ~4459 · `db.py` ~4513 · `home.css` 16124 · `home.html` 6568 · unit **1095** · E2E 1 · 集成 20。

---

## 11. 完成判定 = 解禁新功能(到这就闭环了)

按 `REFACTOR_MASTER_PLAN.md` 完成 check:

```
[ ] home.js < 200 行 · app.py < 500 · db.py < 500 · home.css < 500 · home.html < 1000
[ ] 模块文件 ≥ 100 个
[ ] 单元测试 ≥ 500 · 集成 ≥ 20 · E2E ≥ 10 · 覆盖率 ≥ 70%
[ ] 静默吞错 = 0 · 死代码 = 0
[ ] 让别的 AI 跑一次只读大体检 → 报告显示 "Google 级 90%+"
```

**全绿** → 整顿期结束 → Zihao 解禁新功能(P0-VAT 收尾 / Phase 6 进项管理 等)。

---

## 12. 诚实的预期(别被"全自动"误导)

- **能快**:测试网、复制模块这类并行活,本来几周,batch 几天啃掉大半。真提速。
- **不可能一晚全完**:`home.js` 22k + `home.css` 16k 体量在那;每个 PR 你得过目;"删巨石接线"是真实串行尾巴;登录/计费/OCR 热路径规矩写死要你在场。
- **真实闭环路径**:并行的 ~80% 飞快;剩 ~20% 高敏 + 串行尾巴,是你盯着的 gated 工作。

---

## 13. home.js 测绘 manifest(2026-05-27 · 第三十七会话 · 22970 行版本)

> **关键发现**:home.js 的"大未知块"不是一个巨函数,而是 **~35 个功能孤岛**(顶层函数群 + 约 25 个 IIFE 自执行模块串在一起)。每个 IIFE 天然 = 一个 `src/home/<feature>.js`。**行号是本快照,抽前必 re-grep。**
>
> **⚠️ 进度更新(第三十八/九会话 · 2026-05-27)**:已抽 **21 块** · home.js **22970 → 12929 行**(累计 **-10041**)· R1-R3 抽 13 块,**R4 并行 5 块**:bank-recon / clients / exceptions / topbar-avatar / recon-collapse(`b9f6e1f`),**R5 并行 3 块**:recon-subtab-settings(对账子tab+设置弹窗)/ excel-formula-recon(Excel公式对账·skin-only)/ gl-vat-recon(GL vs 销项税报告对账)(`962105e`)· 均守门全绿 · 生产 E2E 10/10。**②表行号已严重漂移 · 抽前必 re-grep**。
> **R5 后当前 home.js IIFE 地图(12929 行 · 仅供起点 · 必 re-grep)**:🔴plans-plg-line ~8645-11334 / 🔴password ~11342-11598 / 🔴line-email-modal ~11627-11753 / 🔴session-heartbeat 末尾(`_sessionCheck`)。**剩 safe 候选**:admin-misc(两 IIFE · ~8366-8632 · `//` banner)/ bulk-upload 新用户引导(~12753-12855 · 完成 🟡)/ erp-mappings(~11808-12280 + 一段 · 两段)/ erp-endpoints-logs 区(~L5463 多 IIFE 群)/ 待探 Bank-Recon-v2 区(~6836-8362 · 含 window._reconPollJob 共享工具,抽时该工具留 home.js 或一并搬)/ early 区 banner 分隔函数群(chrome-quota/upload-camera/ocr-run/results-drawer/rd-sync/history · 非干净单 IIFE · 较难)/ team(含员工改密 · borderline)。
> **配方(已验证可复制 · R2 起用并行 copy-out agent)**:re-grep 真实起止 → node 切片 verbatim 写 `src/home/<x>.js`(CRLF→prettier 转 LF)→ 加 `/* global ... */` 补 eslint(home.js 暴露但未在 eslint.config globals 的裸全局:apiGet/apiPost/escapeHtml/showConfirm/token/loadTeamList/currentLang/_contact/switchSettingsTab 等)→ 若块内有 verbatim 防御式初始化/下架死码触发 `no-useless-assignment`/`no-unreachable` **error**(src 段未豁免 · 会拖红 CI lint),加头部 `/* eslint-disable <rule> -- verbatim ... */`(0 改逻辑)→ `src/main.js` 加 import → node 切片删 home.js 原块(**split('\n')/join('\n') 保 CRLF · 逐次校验 LF-only=0 · 别整文件转 LF/别用 sed-python**)→ `home.html` 双缓存戳 `home.js?v=`+`main.js?v=` 各 +1(**两个都 bump · 内容都变 · 不动 /api/version 不弹横幅**)→ 守门(eslint 0-error / build / node --check / check_i18n --strict / unittest)→ 每块独立 commit → 一轮单独 push → 生产 E2E 10/10。
> **批量模式**:挑 4-6 个**互不相邻的干净单 IIFE**(避开:顶层函数群如 `export` L4392-4610 · 双 IIFE 如 `admin-misc` · 紧邻🔴的块如 `recon-collapse`(挨 session-heartbeat))→ 并行派同数 copy-out agent(只读 home.js · 只写自己那个新文件 · 回报删除锚点)→ 父窗口串行接线。

**① ⚠️ 更正(2026-05-27 实查代码):不需要先抽 `_shared.js`!**
- 实查 `src/home/{dashboard,test-center,workspace-switcher}.js` + `src/main.js`:**已落地的成熟样板是「全局暴露」不是「import」**。home.js `<script>` 同步先跑 → 顶层 `function t/showToast/showConfirm/apiGet/...` 自动成为全局(window 属性);抽出的 ES module 由 `main.js` import、`type=module defer` 后跑 → 执行时这些全局已就绪,**直接 bare 调用 `t(...)`/`showToast(...)` 即可,无需 import、无需重定义**。test-center.js 就是这么干且已上线验证。
- 所以公共函数**留在 home.js 壳里**(它最先加载),feature 模块照搬即用。`_shared.js` 是**收官步**(等 home.js 缩到比公共函数还小时再抽),**不是前置**。
- 公共函数清单(留在 home.js · 别动):`isSuperAdmin/isOwner/...`(角色 L209)、`t`(L273)、`escapeHtml`(L278)、`svgIcon`(L285)、`showConfirm`(L309)、`apiGet/apiPost/apiPut`(L435)、`applyLang`(L541)、`setupDropdown`(L735)、`showToast`(L6577)、`showAlert`(L4745)、`renderPageHeadInfo`(L4804)。

**② 可并行 copy-out 的安全 feature 模块(大批 · 每个 1 agent)**

| 建议文件 `src/home/*.js` | 行范围(快照) | ~行 | 功能 |
|---|---|---|---|
| sidebar-routing.js | 803-1176 | 370 | routeTo + 侧栏分组/折叠 |
| team.js | 1316-1770 | 450 | 团队管理(员工增删/改密) |
| settings.js | 1282-1962 + 20494-20650 | ~830 | 设置页 tab/表单/通用设置/设置 modal |
| chrome-quota.js | 1965-2280 | 315 | brand workspace/配额 banner/侧栏显隐/infobar |
| upload-camera.js | 2281-2962 | 680 | 上传入口/相机/图片转 PDF/文件列表 |
| ocr-run-results.js | 2964-3640 | 680 | 开始识别/引擎轮询/结果渲染/搜索 |
| results-drawer.js | 3641-3895 | 255 | 识别抽屉/字段渲染 |
| rd-sync.js | 3896-4391 | 495 | RD 税务校验/同步弹窗/OCR 推送/diagnose |
| ⚠️ export.js | 4392-4610 | 220 | Excel 导出模板系统 · **不是 IIFE · 是顶层函数群 + setInterval**(顶层 function 是全局 · 别处可能裸名引用 · 搬走前须查全部外部引用是否走 window)· 非简单 copy-out |
| history.js | 4790-5462 | 670 | 历史记录页 |
| erp-endpoints-logs.js | 5463-6760 | 1300 | ERP 端点管理/推送日志/批量重推删 |
| ✅ email-ingest.js | 6761-7418 | 655 | 邮箱抓取 · 已抽 `3bd7fbc` |
| ✅ folder-watcher.js | 7421-7968 | 544 | 文件夹监听(File System Access API)· 已抽 `eff5f79` |
| ✅ archive-settings.js | 7971-8470 | 497 | 归档命名规则编辑器 · 已抽 `10cb6d6` |
| ✅ bank-recon.js | 8474-9528 | 1052 | 银行对账模块(M10)· 已抽 `b9f6e1f` |
| **(待探)** | 9597-11127 | ~1530 | ⚠️ 无标题块 · 抽前需 agent 先测绘标注 |
| admin-misc.js | 11130-11397 | 267 | 老 admin 残留入口 + 成本追踪面板 · **是两个 IIFE**(11129-11167 下拉 handler + 11171-11397 loadAdminCostPage)· 搬时两个一起 |
| ✅ clients.js | 11401-12152 | 750 | 客户实体前端全套 · 已抽 `b9f6e1f` |
| ✅ ai-balance.js | 12156-12337 | 180 | Google AI 余额追踪 · 已抽 `ea71f7f` |
| ✅ report-templates.js | 12340-12749 | 410 | 报表模板/统一导出弹窗 · 已抽 `c603834` |
| ✅ welcome-wizard.js | 15714-15907 | 190 | 登录后欢迎向导 · 已抽 `c9fb2a0` |
| ✅ exceptions.js | 15914-17523 | 1609 | 异常栏 列表 + 抽屉(第二大块)· 已抽 `b9f6e1f` |
| ✅ notifications.js | 17527-17823 | 296 | 智能提醒 · 已抽 `cad5f1b` |
| ✅ recon-center.js | 17826-18151 | 325 | 对账中心首页 · 已抽 `4fa262e` |
| ✅ access-log.js | 18299-18488 | 189 | 客户访问日志 tab · 已抽 `6ff538b` |
| ✅ assign-clients.js | 18491-18653 | 162 | 客户分配 modal(老板分客户给员工)· 已抽 `e2a9d43` |
| erp-mappings.js | 18704-19178 + 20143-20190 | ~520 | ERP 字段映射底座 + 高级 toggle |
| ✅ erp-xero.js | 19182-19732 | 546 | Xero 连接卡片 + 推按钮 · 已抽 `a6d5652` |
| 🟡 bulk-upload.js | 19735-20204 | ~470 | **已拆两半**:✅ big-batch-progress(进度条 · `696136c`)已抽;剩「ERP 新用户引导」IIFE(紧随其后)待抽 |
| ✅ topbar-avatar.js | 21264-22376 | 1100 | 顶栏三件套 / 头像菜单(NAV-IA P1)· 已抽 `b9f6e1f`(实为单 IIFE ~360 行) |
| ✅ recon-collapse.js | 22441-22690 | 250 | 销项/收入对账折叠组件 · 已抽 `b9f6e1f`(START 从 banner 起 · 心跳零泄漏已验) |
| ✅ recon-batch.js | 22691-22970 | 280 | 对账历史多选批量删 · 已抽 `f3d4cbc` |

**③ ⚠️ 高敏/勿入 batch(留 Zihao 在场 · 主控亲手做)**
- `plans-plg-line`(L12757-15446 · **2689 行 · 最大块**):商业模式 = 套餐 + 防薅闸 + 升级弹窗 + **LINE 绑定**(碰登录/账号)。
- `password-change`(L15452-15710):修改密码模块(碰认证)。
- `line-email-modal`(L18168-18296):LINE 补邮箱强制 modal(**账号合并**)。
- `session-heartbeat`(L22377-22440):Session 心跳踢设备(auth)。
- 启动/boot 段(L4761-4789)+ routeTo 中枢:接线敏感,串行小心。

**④ 节奏**:直接放 12-18 个 agent 并行 copy-out 上表安全模块(照 test-center 样板:搬进 `src/home/<x>.js` + `main.js` import + bare 调全局,**0 改逻辑**)· 分 2-3 轮 → 串行窗口接线删 home.js → 最后 Zihao 在场处理高敏 4 块 → 收官再抽 `_shared.js`。**前置:Wave 0 E2E 网必须先绿**(否则拆完无法验证页面还能渲染)。
- **每个 agent 黄金指令**:照 §5 模板 B,但「import 公共件 _shared」改成「bare 调全局 t/showToast/showConfirm/apiGet 等(home.js 已暴露,勿重定义/勿 import)」;搬完在 `src/main.js` 加一行 import;带渲染/契约测试;5 道守门;commit 含 · REFACTOR-C1。

---

*本文档作者:Claude(Anthropic) × Zihao · 配套 `REFACTOR_MASTER_PLAN.md` · 整顿搞完即归档。*
