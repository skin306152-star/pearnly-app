# 🤖 后台并行 agent 派工模板（BATCH_AGENT_DISPATCH）

> **这份文档 = 主控窗口「派后台并行 agent 干活」的标准操作模板（copy-paste 即用）。**
> 上级文档：`CLAUDE.md/BATCH_STRATEGY.md`（整套作战手册 · 5 波次 + 进度账本）。
> 本文档只回答一个问题：**主控窗口具体怎么把活拆给后台 agent、怎么收口、什么时候能自动合并。**
>
> 最后更新：2026-05-28（初版）
> 配套铁律：`CLAUDE.md/CLAUDE.md` 铁律 #26（无人值守自动修 bug + 自动合并 · 安全区 / 高敏两档）

---

## 0. 三种并行方式 · 先选对

| 方式 | 什么时候用 | 优点 | 缺点 |
|---|---|---|---|
| **后台并行 agent**（本文档 · 首选） | 拆巨石 copy-out / 补测试网 / 批量文档 | 同一主控窗口统一收口、统一守门、统一提交 · Zihao 零操作 | 拆分活才合适（新增文件） |
| 长跑命令丢后台 | 全量单测 / `npx playwright test` / build | 主线继续干活，跑完通知 | 只是单条命令，不是派工 |
| 开多窗口 | 两条完全独立的线（如 css 窗口 + js 窗口） | 真并行 | **不共享上下文 · 碰同一巨石会撞车** |

> **铁律**：拆同一个巨石（home.js / db.py / home.css）**永远用后台并行 agent**，不要开第二个窗口去碰同一个文件。

---

## 1. 标准三步法

```
① 出承包清单（manifest）  →  ② 派 N 个后台 agent  →  ③ 主控统一收口
   主控研究 + 规划            run_in_background        守门 + 复查 + 提交/合并
   保证零重叠                  每人只碰自己那块新文件     按铁律 #26 判定能否自动合并
```

### ① 出承包清单（manifest）— 派工前必做

主控先把活切成**互不重叠**的小块，每块一行：

| agent | 负责功能 | 巨石来源（行号 · 抽前必 re-grep） | 产出新文件 | 类型 |
|---|---|---|---|---|
| A1 | history 历史页 | home.js L4790-5462 | `src/home/history.js` | copy-out |
| A2 | team 团队管理 | home.js L1316-1770 | `src/home/team.js` | copy-out |
| A3 | 收入对账 E2E | —（纯新增） | `tests/e2e/income-recon.spec.js` | 新增 |

**零重叠铁律**：没有两个 agent 碰同一段行号 / 同一个文件。这是派工前主控的责任。

### ② 派 N 个后台 agent

主控用 Agent 工具 + `run_in_background`，一条消息里同时发多个（并发跑）。每个 agent 用下面 §2 的指令模板，把 `【】` 占位填好。

### ③ 主控统一收口

所有 agent 回报完成后，主控**统一**做（不是各 agent 自己合）：
1. 跑**全套**守门（见 §3，一道都不能漏）
2. 复查每块产出（文件对不对、有没有偷偷碰巨石）
3. 按**铁律 #26** 判定：安全区 → 自动 commit + 合并；碰高敏 → 停下等 Zihao
4. 更新 `BATCH_STRATEGY.md` §10 进度账本 + `STATE_PEARNLY.md`

---

## 2. agent 指令模板（填空即用）

### 模板 A · 新增型（Wave 0 测试网 / Wave 4 文档 · 纯新建文件）

```
你是并行 batch 的一个后台 agent，只负责【一项，如：收入对账 E2E】。
铁律：
- 只新建文件（如 tests/e2e/<name>.spec.js 或 docs/<name>.md），
  绝不改 home.js / db.py / app.py / home.css / home.html。
- 完成后跑全 6 道守门，全绿才算完：
    npm run format:check                        # prettier 格式
    python -m unittest discover -s tests/unit   # 全量单测
    python scripts/check_imports.py --quiet
    python scripts/check_i18n.py --strict
    node --check <你改的.js>                     # 改了 JS 才跑
    npm run build                               # 改了前端才跑
    npx playwright test                         # (按需 E2E)改了前端/E2E 才跑
- 字节级 LF 处理，无 BOM。
- 完成后回报：产出了哪些文件、跑过哪几道门、覆盖哪条路径。
- 不确定 / 要碰巨石 / 触发高敏（登录·计费·OCR热路径·改密·LINE绑定·auth·RLS）
  → 立刻停，回报里标注，绝不硬来。
```

### 模板 B · 拆分型（Wave 1 db.py / Wave 2 home.js · copy-out 不删原文件）

```
你是并行 batch 的一个后台 agent，负责把【功能，如 history】从 home.js
抽到 src/home/history.js。
铁律（copy-out 范式）：
- 【只复制，不删除】：把该功能整片拷进新 ES module；
  home.js 一行都不许删（删除留给主控的串行接线步）。
- 抽前必 re-grep 当前真实行号确认边界（别用文档里的旧行号）。
- 共享全局（t / subscribeI18n / showToast / showConfirm / apiGet 等）
  直接 bare 调用即可——home.js 已暴露成全局，勿重定义、勿 import。
  （样板见已上线的 src/home/test-center.js）
- 搬完在 src/main.js 加一行 import。
- 顶部按需补 /* global ... */ 给 eslint；verbatim 死码触发 no-unreachable
  等 error 时加 /* eslint-disable <rule> -- verbatim */（0 改逻辑）。
- 字节级 LF 处理，无 BOM。
- 带一个渲染/契约测试：该 module 入口函数能渲染、0 报错。
- 跑全 6 道守门(format/unit/imports/i18n/node/build · E2E 按需)，全绿才算完。
- 回报：抽了哪个功能、新文件路径、删除锚点行号（给主控接线用）、跑过的门。
- 触发高敏（登录·计费·OCR热路径·改密·LINE绑定·auth·RLS基础设施）
  → 停，回报里标注，不动。
```

> **db.py 后端版**：把「home.js → src/home/x.js」换成「db.py → services/<域>/store.py」，
> 范式换成 `import db` + 运行时 `db.get_cursor()`（保 patch 生效），commit 用 `· REFACTOR-B2`。

---

## 3. 收口守门 checklist（主控每批必跑全 · 血泪：局部守门会漏）

> 来源：`BATCH_STRATEGY.md` §9.5 第 8 点。窗口只跑自己改的那几个会报假绿 → CI 实红。

- [ ] ① `npm run format:check`（prettier · **最易漏！**）
- [ ] ② `python -m unittest discover -s tests/unit`（**全量** · 不是只跑改的）
- [ ] ③ `python scripts/check_imports.py --quiet`
- [ ] ④ `python scripts/check_i18n.py --strict`
- [ ] ⑤ `node --check <改的.js>`
- [ ] ⑥（前端改）`npm run build`
- [ ] ⑦ 主控独立 `gh run list` 查 **CI 真绿**——不只信 agent 报告

**prettier 配套**：新 `static/home-*.css` 切片在 `.prettierignore` 豁免；新 `src/home/*.js` 模块**要** `npx prettier --write`（不豁免）。
**守门测试读巨石的要改并集**：测试里 `open("home.js")` 找内容的，拆分后改读 `home.js + src/home/*.js` 拼接。

---

## 4. 能不能自动合并？—— 按铁律 #26 判定

收口守门全绿后，主控判定这批属于哪档：

| | 🟢 安全区 | 🔴 高敏区 |
|---|---|---|
| 范围 | 文案 / 翻译 / 样式 / 普通业务逻辑 / 测试 / 文档 / 依赖绿 PR | 登录·注册 / 计费充值扣费 / OCR 热路径 / auth·JWT·session / RLS 基础设施 / LINE 绑定 / 改密码 / 账号合并 |
| 涉及文件（命中即高敏） | 其余 | `auth.py` `auth_signup.py` `billing_routes.py` `services/billing/*` `line_binding_routes.py` `line_client.py` · db 的 credits/charge_ocr/RLS · app.py 的 recognize 路由 · `services/ocr/*` · home.js 的 plans-plg-line/password-change/line-email-modal/session-heartbeat |
| 无人值守时 | **自动 commit + `git push origin master`** | **停**，开 PR / 留草稿 + 标「待 Zihao 在场」，**绝不自动合并** |
| 额外硬条件 | CI 5 关全绿 + < 30 文件 + 无 schema/删字段 | 同上 + Zihao 在场 + 当轮真账号 E2E 验 |

> **永不松动的硬线**：测试绝不触发真实扣钱 / 退款（充值 E2E 是「绝不真付」设计）。

---

## 5. 护栏（开干前对一遍）

- [ ] 派工前 `git tag` 备份当前 master。
- [ ] 承包清单零重叠（没有两 agent 碰同一段）。
- [ ] 每个 agent 指令内嵌 6 道守门 + 契约测试 + REFACTOR-id（否则违反 8 硬门槛）。
- [ ] 高敏域永不进无人看管的并行 batch（铁律 #26 · §9.5 #4）。
- [ ] 删巨石旧代码这步**串行**，不并行（一块一守门一 commit）。
- [ ] 每波结束跑 `python scripts/refactor_progress.py` 看数字真掉了。

---

*本文档作者：Claude（Anthropic） × Zihao · 配套 `BATCH_STRATEGY.md` + 铁律 #26 · 整顿搞完即归档。*
