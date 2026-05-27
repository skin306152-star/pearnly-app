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

## 10. 进度账本(每波收尾必更新 · 让下个窗口接得上)

> 符号:⚪ 待启动 · 🟡 进行中 · ✅ 已完成

| Wave | 状态 | 起始数字 | 当前数字 | 已合 PR / 备注 |
|---|---|---|---|---|
| 0 安全网(E2E/集成) | 🟡 | unit 872 / E2E 1 | unit **1095** / E2E 1 | 第三十五会话(2026-05-27)**未用 /batch · 在单窗口直接做**:17 个核心纯逻辑模块补行为契约(对账/导出/归档/监控/加密)· +~220 unit · 挖修 3 真 bug · 全守门绿 · 零冲突。**E2E(登录后核心路径)仍 1/10 · 需账号** |
| 1 db.py 收尾 | 🟡 | db.py 4620 行 | db.py 4620(未接线) | 第三十七会话(2026-05-27)**首次用并行 agent**:membership(9 函数)+ tenant(14 函数)两安全域 copy-out → `services/{membership,tenant}/store.py` + 37 契约测试 · 全守门绿 · CI 绿 · `c1a8c8a`。**copy-out 完成 · 串行接线(删 db.py + re-export)未做**。剩余域全高敏(credits/auth/ocr_history)→ Zihao 在场 |
| 2 home.js | 🟡 测绘完 | home.js **22970 行** | — | 第三十七会话测绘完(见 §13)· `_shared` 待抽(串行)· 大块 L6623-20204 已确认 = ~25 个 IIFE 模块(非单巨函数)· **等 Wave 0 E2E 网绿后开大批** |
| 3 css/html | ⚪ | css 16124 / html 6568 | — | — |
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

**① 先抽(串行 · 由主控做):公共件 `src/home/_shared.js`**
- 散落 L190-770:`isSuperAdmin/isOwner/isEmployee/isTrial/isLifetime/shouldHideMoney`(角色)、`t`(L273)、`escapeHtml`(L278)、`svgIcon`(L285)、`showConfirm`(L309)、`apiGet/apiPost/apiPut`(L435-499)、`applyLang`(L541)、`setupDropdown`(L735)、`showToast`(L6577)、`showAlert`(L4745)、`renderPageHeadInfo`(L4804)。
- 几乎所有 feature 模块都依赖它 → 必须第一个抽,之后各模块 import。

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
| export.js | 4392-4610 | 220 | Excel 导出模板系统 |
| history.js | 4790-5462 | 670 | 历史记录页 |
| erp-endpoints-logs.js | 5463-6760 | 1300 | ERP 端点管理/推送日志/批量重推删 |
| email-ingest.js | 6761-7418 | 655 | 邮箱抓取 |
| folder-watcher.js | 7421-7968 | 544 | 文件夹监听(File System Access API) |
| archive-settings.js | 7971-8470 | 497 | 归档命名规则编辑器 |
| bank-recon.js | 8474-9528 | 1052 | 银行对账模块 |
| **(待探)** | 9597-11127 | ~1530 | ⚠️ 无标题块 · 抽前需 agent 先测绘标注 |
| admin-misc.js | 11130-11397 | 267 | 老 admin 残留入口 + 成本追踪面板 |
| clients.js | 11401-12152 | 750 | 客户实体前端全套 |
| ai-balance.js | 12156-12337 | 180 | Google AI 余额追踪 |
| report-templates.js | 12340-12749 | 410 | 报表模板/统一导出弹窗 |
| welcome-wizard.js | 15714-15907 | 190 | 登录后欢迎向导 |
| exceptions.js | 15914-17523 | 1609 | 异常栏 列表 + 抽屉(第二大块) |
| notifications.js | 17527-17823 | 296 | 智能提醒 |
| recon-center.js | 17826-18151 | 325 | 对账中心首页 |
| access-log.js | 18299-18488 | 189 | 客户访问日志 tab |
| assign-clients.js | 18491-18653 | 162 | 客户分配 modal(老板分客户给员工) |
| erp-mappings.js | 18704-19178 + 20143-20190 | ~520 | ERP 字段映射底座 + 高级 toggle |
| erp-xero.js | 19182-19732 | 546 | Xero 连接卡片 + 推按钮 |
| bulk-upload.js | 19735-20204 | ~470 | 大批量上传进度 + 新用户引导 |
| topbar-avatar.js | 21264-22376 | 1100 | 顶栏三件套 / 头像菜单(NAV-IA P1) |
| recon-collapse.js | 22441-22690 | 250 | 销项/收入对账折叠组件 |
| recon-batch.js | 22691-22970 | 280 | 对账历史多选批量删 |

**③ ⚠️ 高敏/勿入 batch(留 Zihao 在场 · 主控亲手做)**
- `plans-plg-line`(L12757-15446 · **2689 行 · 最大块**):商业模式 = 套餐 + 防薅闸 + 升级弹窗 + **LINE 绑定**(碰登录/账号)。
- `password-change`(L15452-15710):修改密码模块(碰认证)。
- `line-email-modal`(L18168-18296):LINE 补邮箱强制 modal(**账号合并**)。
- `session-heartbeat`(L22377-22440):Session 心跳踢设备(auth)。
- 启动/boot 段(L4761-4789)+ routeTo 中枢:接线敏感,串行小心。

**④ 节奏**:`_shared` 先串行抽 → 再放 12-18 个 agent 并行 copy-out 上表安全模块(2-3 轮)→ 串行窗口接线删 home.js → 最后 Zihao 在场处理高敏 4 块。**前置:Wave 0 E2E 网必须先绿**(否则拆完无法验证页面还能渲染)。

---

*本文档作者:Claude(Anthropic) × Zihao · 配套 `REFACTOR_MASTER_PLAN.md` · 整顿搞完即归档。*
