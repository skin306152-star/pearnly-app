# Pearnly 知识库/RAG · 本地沙盒 → 迁移主项目 · 多窗口执行计划

生成日期：2026-06-03
作者：Opus 4.8（讨论/设计，非执行）
配套文件：`Pearnly_当前项目架构与财务知识库RAG融合方案_2026-06-01.md`（原始方案，本计划在其之上做修订与落地编排）

---

## 0. 这份文件是给谁、怎么用

- **给谁**：给"做项目的窗口"看。每开一个新窗口，第一件事就是读这份文件 + 沙盒里的 `STATE_KB.md`。
- **解决什么**：原方案讲清了"做什么"，但没讲"在哪做、怎么不违整顿封锁、多窗口怎么接力、最后怎么干净迁回主项目"。这份文件补这一层。
- **一句话工作流**：
  > 在本地开一个**独立 git 仓库**（沙盒），用**和主项目一模一样的技术栈和规矩**把知识库功能做出来并验透 → 整顿封锁解除后，把**第一个最小可用切片**按铁律干净迁进主项目，闭环上线一个功能 → 后续切片同法陆续迁。

---

## 1. 五条总原则（任何窗口都不许破）

1. **本地沙盒，绝不碰主仓库**：主项目现在是整顿封锁期（0 新功能铁律）。知识库的所有开发在独立仓库 `pearnly-knowledge` 里做。整顿没收工前，主项目一行都不为它改。
2. **镜像主项目技术栈**：沙盒用的语言、框架、数据库访问方式、目录命名、文件结构，全部照抄主项目。**目的：最后迁移 ≈ `git mv` + 改 import，而不是重写。**（技术契约见第 3 节）
3. **迁移税最小化**：沙盒里凡是"主项目已经有、迁过去要复用"的东西（鉴权、租户解析、ocr_history、对象存储），一律藏在一层**很薄的"宿主契约"接口**后面，本地用假实现（stub），迁移时换成主项目真实现。新代码只认接口、不认假实现。（见第 4 节）
4. **不是一个窗口能做完**：按"一个窗口 = 一个可独立验收的阶段"来切。每个窗口靠 `STATE_KB.md` 接力，开局知道上一棒做到哪、自己该做什么、收尾留什么。（见第 5、6 节）
5. **最后闭环一个功能**：终点不是"做完整套 RAG"，而是**把风险最低、价值够、能独立上线的那个切片，按主项目全部铁律干净迁回主项目并真上线**。其余切片同法陆续迁。（见第 7 节）

---

## 2. 沙盒项目长什么样

- **位置**：`C:\Users\skin3\Desktop\pearnly-knowledge\`
- **是独立 git 仓库**（`git init`，和 pearnly-app 无任何关联），第一个窗口负责建。
- **核心理念**：沙盒 = **真·知识库代码** + **假·宿主**。真代码将来整包迁走；假宿主迁移时丢弃，换成主项目真实接线。

```
pearnly-knowledge/                  ← 独立 git 仓库（本地沙盒）
  AGENTS_KB.md                      唯一一页入口·文档地图（镜像主项目 AGENTS.md）
  STATE_KB.md                       状态卡 ≤30 行·窗口交接核心（镜像 STATE_PEARNLY.md）
  README.md                         怎么本地起服务、起数据库

  app_local.py                      仅沙盒用的极小 FastAPI 入口（迁移时丢弃）
  knowledge_routes.py               ★迁移目标：routes/knowledge_routes.py
  db.py                             连接池 + DAL facade（镜像主项目 db.py 写法）

  host/                             ★宿主契约层（隔离迁移税的关键）
    contract.py                     接口定义：identity / workspace / ocr_history / storage / db
    stubs_local.py                  沙盒假实现（迁移时丢弃，换主项目真接线）

  services/
    knowledge/                      ★迁移目标：整包落主项目 services/knowledge/
      __init__.py
      schema.py                     Alembic migration 配套的表定义/DDL（⚠️禁 ensure_·见铁律对齐补丁）
      models.py                     dataclass（领域模型）
      ingest.py                     文档解析 → 规范化 → 分 chunk
      embedding.py                  embedding 调用 + 写库
      search.py                     pgvector 检索 + rerank
      rules_engine.py               ★死规则检查（确定性·不走 LLM）
      ask.py                        RAG 问答（检索 → LLM → 带 citation）
      risk_check.py                 OCR 后风险检查编排（规则 + RAG 合流）

  migrations/                       Alembic（镜像主项目；迁移时并入主 alembic）

  src/home/                         前端模块（镜像主项目 src/home/* 命名）
    page-knowledge.js
    knowledge-api.js
    knowledge-documents.js
    knowledge-ask.js
    knowledge-sources.js
    knowledge-rules.js
    knowledge-risk.js
  static/i18n-data.js               4 语言（th/en/zh/ja·镜像主项目）

  eval/                             ★验收考卷（原方案缺·本计划新增）
    golden_set.jsonl                标准问答集：问题+标准答案+正确出处
    run_eval.py                     回归跑分·不过线不许迁移
  fixtures/                         本地测试用假数据（泰文发票/合同样本·脱敏）

  tests/
    test_knowledge_*.py             单测（镜像主项目 tests/ 风格）
  scripts/
    kb_progress.py                  行数/进度脚本（镜像 refactor_progress.py）
    pre-commit-gate.sh              守门（镜像主项目 6 道闸）
```

**为什么这么摆**：迁移那天，`services/knowledge/`、`knowledge_routes.py`、`src/home/knowledge-*.js`、`migrations/`、`tests/test_knowledge_*.py` 这几块是**整块搬过去**的；`app_local.py`、`host/stubs_local.py`、`fixtures/` 是沙盒专用、丢弃。剩下要做的只有：把 `host/contract.py` 的接口接到主项目真实的鉴权/租户/存储上。

---

## 3. 技术兼容性契约（迁移能不能干净，全看这一节）

任何窗口写代码前先核对这张表。**偏离任何一条 = 给未来迁移埋雷。**

| 维度 | 主项目的做法 | 沙盒必须照做 |
|---|---|---|
| 语言/框架 | Python + FastAPI 单体 | 同 |
| 数据库 | Supabase Postgres | 本地 Postgres + **pgvector 扩展**（Docker 最省事） |
| DB 访问 | **psycopg2 + 手写 SQL**，`db.py` 连接池 + DAL facade，领域逻辑在 `services/**` | 同。**不许引 SQLAlchemy ORM / asyncpg**（写法不一致＝迁移要重写） |
| 建表 | 历史靠 `ensure_*`，整顿正迁向 Alembic | ⚠️**新表只走 Alembic，禁新增 `ensure_*`**（`check_new_debt.py` 会拦·见《铁律对齐补丁》§1）。沙盒本地 `alembic upgrade head` 建表 |
| 路由 | 业务路由拆成独立 `*_routes.py`，不塞 `app.py` | `knowledge_routes.py` 独立文件 |
| 目录归属 | 已定**方案B**：顶层 `routes/`+`core/`，业务进现有 `services/<域>/` | 沙盒按 `services/knowledge/` 写，迁移后即落主项目 `services/knowledge/` |
| 前端 | Vite + `src/home/*` ES module，`home.html` 薄壳 | 同；新模块叫 `knowledge-*`，**不塞大入口** |
| i18n | `static/i18n-data.js`，th/en/zh/ja 四语 | 文案进同一结构，四语齐全 |
| 单文件行数 | **所有源文件 < 500 行**（铁律目标） | 同。`kb_progress.py` 实时盯 |
| 注释/风格 | 去 AI 味·注释讲 why 不讲 what·无 emoji 注释·无 `console.log` 残留·命名结构按大厂 | 同（铁律#常驻1）。沙盒 `pre-commit-gate.sh` 含 AI 味检查 |
| 换行符 | `home.html`/`home.js` 是 **CRLF + .prettierignore**，禁 `prettier --write` 整文件 | 沙盒前端文件**新建即用 LF**（新文件无历史包袱）；迁移进主项目时按主项目目标文件的换行符走 |
| 标识符语言 | 代码标识符/commit 用英文；沟通用中文 | 同（铁律·全程中文沟通） |
| 署名 | commit 署名 Opus 4.8 | 同 |
| 缓存破除 | 改前端必 bump `?v=` | 沙盒本地可忽略；**迁移进主项目时必 bump**（铁律） |

**两个开工前必须先确认的事实（写进第一个窗口任务）**：
1. **ID 类型**：✅ P0 已实地核对，权威结论见 `docs/Pearnly_KB_主项目契约事实_2026-06-03.md`：**`ocr_history.id = UUID`、`workspace_clients.id = bigint`**。`tenant_id`/`user_id` = UUID。新表的 PK 与 FK 类型一律以那份契约事实文档为准，别再凭《融合方案》早先 DDL 的 uuid 猜。
2. **embedding 模型**：泰文表现是最大未验证假设（泰文不空格分词、财税术语难）。第一个窗口先做泰文检索小实验（见第 6 节 Phase 1 的前置 spike）。

---

## 4. 宿主契约层（隔离迁移税的核心机制）

知识库代码**只能通过 `host/contract.py` 这一层**去拿"主项目才有的东西"。沙盒里用假实现，迁移时换真实现，知识库代码本身一行不改。

`host/contract.py` 至少定义这些接口（签名按主项目真实情况微调）：

```python
# 谁在操作（鉴权 + 租户解析的结果）
def get_current_identity(request) -> Identity:        # {user_id, tenant_id, role}
    ...

# 这个人能访问哪些账套主体（权限边界）
def get_accessible_workspace_clients(identity) -> list[int]:
    ...

# 取一条 OCR 历史（风险检查要用）
def get_ocr_history(history_id, identity) -> OcrHistoryRow | None:
    ...

# 原始文件存取（沙盒=本地磁盘；prod=Supabase Storage / S3）
def storage_put(key, data) -> str: ...
def storage_get(key) -> bytes: ...
def storage_delete(key) -> None: ...

# 数据库游标（RLS 感知·铁律#26）——知识库 DAL 从第一天就用这个，SQL 仍显式带 tenant/workspace 过滤
# 沙盒 stub 可简化（普通 cursor + 可选 SET LOCAL），迁移时接主项目 db.get_cursor_rls，知识库代码不改
def get_cursor_rls(tenant_id, *, bypass=False, commit=False): ...

# 计费（沙盒=记账到本地表；prod=主项目 credits）
def charge_credits(tenant_id, kind, amount, meta): ...
```

- **沙盒**：`stubs_local.py` 给假实现——`get_current_identity` 直接返回一个测试租户；`get_ocr_history` 从 `fixtures/` 读样本；`storage_*` 走本地磁盘；`charge_credits` 只打日志。
- **迁移**：删掉 `stubs_local.py`，把 `contract.py` 的每个函数接到主项目真实的鉴权中间件、`workspace` 权限、`ocr_history` DAL、Supabase Storage、credits。
- **铁律映射**：原方案强调的"每个 endpoint 第一行做鉴权+租户+workspace 权限+SQL 带 tenant_id/workspace_client_id"——在沙盒里就是"每个 endpoint 第一行调 `get_current_identity` + `get_accessible_workspace_clients`，所有 SQL 用它们的返回值过滤"。这条从第一天就硬性写进每个 route。

---

## 5. 窗口交接协议（"接得住"的机制）

每个窗口都遵守同一套开局/收尾动作。靠 `STATE_KB.md`（≤30 行状态卡，镜像主项目）做交接介质。

### 5.1 开局（任何窗口进来先做）
1. 读 `AGENTS_KB.md`（一页入口）+ 本计划文件。
2. 读 `STATE_KB.md` 顶部状态卡：上一棒做完什么、当前在哪个 Phase、本窗口该接什么、有什么坑/阻塞。
3. 跑 `python scripts/kb_progress.py`：看实时行数和阶段勾选（别信文档手写数字）。
4. 跑一遍测试 + eval：`pytest -q && python eval/run_eval.py`，确认接手时是绿的（红的先问清楚再动）。

### 5.2 干活（窗口内）
- 一个窗口只推进**一个 Phase**（或 Phase 内一个明确切片），不贪多。
- 严守第 3 节技术契约 + 第 4 节宿主契约。
- 每个新文件、每次改动当下就做到大厂级（去 AI 味、注释讲 why、<500 行）。

### 5.3 收尾（窗口结束前，雷打不动）
1. **跑 `/simplify`**：扫本窗口改动做简化/复用/去重收口（铁律·常驻2）。
2. 跑全部守门：`pytest`、`kb_progress.py`、`pre-commit-gate.sh`、`eval/run_eval.py`，**全绿才算完**。
3. **更新 `STATE_KB.md`**：勾掉本窗口完成项，写清"下一棒该做什么 + 任何坑/决策/阻塞"。状态卡保持 ≤30 行（历史进 `STATE_KB_ARCHIVE.md`）。
4. commit（署名 Opus 4.8，英文 commit message，中文沟通）。
5. 一句话收尾报告给 Zihao。

### 5.4 STATE_KB.md 模板（第一个窗口建好）
```
# KB 沙盒状态卡（≤30 行·历史进 ARCHIVE）
当前 Phase：P0 脚手架
上一棒完成：__
本窗口该接：__
阻塞/待 Zihao 拍板：__
守门状态：pytest __ / eval __ / 行数 __
迁移就绪度：未开始 | 切片A 可迁 | ...
```

---

## 6. 阶段分解（每个 Phase ≈ 一个窗口能验收的量）

> 顺序原则：**先脚手架 → 先死规则（便宜可靠立刻有价值）→ 再文档/检索 → 再 RAG 问答 → 最后合流成 OCR 风险检查**。规则引擎排在 RAG 前，是本计划对原方案的核心修订（理由见第 8 节 / 下面深聊）。

| Phase | 目标（一个窗口的活） | 完成闸（done gate） |
|---|---|---|
| **P0 脚手架** | 建仓库、`AGENTS_KB.md`/`STATE_KB.md`、本地 PG+pgvector 起来、`host/contract.py`+`stubs_local.py`、`app_local.py` 能跑、`scripts/` 守门、确认 ID 类型 | `curl /health` 通；空 pytest 绿；守门脚本能跑 |
| **P0.5 泰文 spike** | 拿 fixtures 里 20 份泰文样本，试 2-3 个 embedding 模型，量检索命中率 | 出一页结论：选哪个模型、泰文是否够用、维度多少 |
| **P1 文档基建** | `knowledge_bases/documents/ingest_jobs` 三表 **走 Alembic（禁 ensure_）**；上传/list/状态/删除 API；解析 PDF/text/docx/xlsx/csv → chunk；前端文档库页（只显状态，不做回答） | 上传一份 → 看到 ingest 状态走到 ready；删除标 deleted；tenant/workspace 过滤单测绿 |
| **P2 检索** | `knowledge_chunks/embeddings` + embedding 写入 + pgvector top-k 检索 + `POST /search` | 检索返回带 score 的 chunk；跨租户检索测试**取不到别家数据** |
| **P3 规则引擎** | `client_rules` 表 + `rules_engine.py`：供应商白名单/金额超限/税号格式/重复票等**确定性**检查；规则增删改查 API + 前端 `knowledge-rules.js` | 喂构造发票 → 命中预期规则；0 调用 LLM；结果可解释（每条 finding 带触发的规则 id） |
| **P4 带出处问答** | `ai_answers/ai_answer_sources` + `ask.py`：检索→LLM→带 citation；无来源则拒答；前端问答 + 来源抽屉 | eval 跑分过线；无来源问题返回"资料不足"；每个答案能点开 source |
| **P5 OCR 风险检查（合流）** | `invoice_risk_checks` + `risk_check.py`：规则引擎 + RAG 合流，输出 risk_level/findings/sources/needs_human_review；前端 `knowledge-risk.js` panel | 用 fixtures 跑一条 OCR 历史 → 出风险报告；高风险标人工复核；**采纳/忽略**被记录 |
| **P-MIG 迁移闭环** | 选定切片，按第 7 节迁进主项目，真上线一个功能 | 主项目 E2E 绿 + prod 真浏览器验 + 全铁律过 |

每个 Phase 内若太大，窗口可再切（如 P1 拆"表+API"和"解析+前端"两窗口），但每次收尾都按第 5 节交接。

---

## 7. 迁移闭环剧本（整顿收工后做）

**前置**：① 主项目整顿收工（`app.py` 等全 <500、方案B 目录重组落地）；② 沙盒目标切片 eval/测试全绿。

**选哪个切片先迁**：按**风险最低**选，不是按价值最高选——
- **首迁 = P1 文档基建**。理由：纯新增，完全不碰 OCR/计费/ERP 高敏热路径，是最安全的"第一张 PR"（与原方案第 17 节一致）。
- 次迁 = P3 规则引擎（价值高、确定性、仍不碰热路径）。
- 再迁 = P2/P4 检索与问答。
- 最后才迁 = P5 OCR 风险检查（要插进 OCR 主路径，最高敏，必须 Zihao 在场，按"改主路径先报方案"铁律走）。

**迁移动作（首迁切片为例）**：
1. 主项目开 feature 分支（不直接 master）。
2. 整包 `git mv` 等价搬入：`services/knowledge/`（去掉沙盒专用文件）、`knowledge_routes.py`（落 `routes/`）、`migrations/`、`tests/test_knowledge_*.py`、`src/home/knowledge-*.js`、i18n 文案并入 `static/i18n-data.js`。
3. **接线宿主契约**：把 `host/contract.py` 各函数接到主项目真鉴权/租户/workspace 权限/Supabase Storage/credits；删 `stubs_local.py`。
4. 改 import 路径（沙盒包名 → 主项目包名），跑 ruff `F821`/`F401` 兜底。
5. 前端：`main.js` 挂载新模块；`home.html` 加知识库入口；**bump `?v=`**（铁律）；`npm run build` + commit `static/dist`（铁律）。
6. schema：**只走 Alembic migration 入主项目**（禁新增 `ensure_*`·`check_new_debt.py` 会拦）。
7. 守门 6 道全过；E2E 绿；**真浏览器验**（isVisible+getComputedStyle+截图，grep 类名不算数）。
8. 上线策略：feature flag 默认关 → 灰度 → 真浏览器 prod 验 → 开。
9. `/api/version` bump，prod `/api/ready` 绿。

**闭环判据**：一个完整功能（如"客户文档库")在 prod 真能用、0 console error、全铁律过、回滚路径清晰（feature flag 一关即退）。

---

## 8. 对原方案的 4 条修订（已并入上面阶段）

1. **拆"规则引擎"与"RAG 问答"，且规则先做**（P3 在 P4 前）：精确比对（税号/金额/重复/白名单）走**确定性死规则**，不走 LLM；开放问答（读合同/政策）才走 RAG。详见下面深聊。
2. **从第一天记录"采纳/忽略"**：每条 AI 建议被接受还是被否，落库。**采纳率 = 衡量好不好用的北极星指标**，也是日后让系统自学规则的训练料。
3. **冷启动靠"偷学"**：P5 起就埋数据采集——把会计每次手动改字段/打回/归科目记下来，攒够了反推"按老规矩？"提示。让知识库不靠人喂也能长。
4. **补验收考卷（eval/）**：top 用例做"问题+标准答案+正确出处"金标集，每次改动回归跑分，不过线不许迁移。财务错一次代价大，没考卷=拿真客户试错。

---

## 9. 第一个窗口现在就做什么（启动指令）

把下面这段丢给新窗口当任务：

> 你在为 Pearnly 知识库功能搭**本地独立沙盒**（不碰主项目 pearnly-app，主项目整顿封锁中）。先读桌面《Pearnly_知识库RAG_本地沙盒到迁移_多窗口执行计划_2026-06-03.md》全文。本窗口做 **P0 脚手架**：
> 1. 在 `C:\Users\skin3\Desktop\pearnly-knowledge\` `git init` 建独立仓库。
> 2. 按计划第 2 节建目录骨架；写 `AGENTS_KB.md`、`STATE_KB.md`（用第 5.4 模板）、`README.md`。
> 3. 本地起 Postgres + pgvector（Docker 最省事），`db.py` 镜像主项目 psycopg2 连接池写法。
> 4. 写 `host/contract.py` 接口 + `host/stubs_local.py` 假实现；`app_local.py` 极小 FastAPI 入口，`/health` 通。
> 5. 建 `scripts/kb_progress.py`、`scripts/pre-commit-gate.sh`（镜像主项目守门：行数<500、AI 味、无 console.log/emoji 注释）。
> 6. **去主项目只读确认两件事并记进 STATE**：`ocr_history`/`workspace_clients` 主键类型；现有 storage/鉴权/租户解析的真实函数签名（供 contract.py 对齐）。
> 严守计划第 3 节技术契约。收尾按第 5.3：跑 /simplify、守门全绿、更新 STATE_KB.md、commit 署名 Opus 4.8、一句话报告。

---

## 10. 待 Zihao 拍板（沿用原方案第 16 节，已知答案先填）

1. 主客户：**会计事务所替多家公司做账**（已确认）→ workspace/client 权限优先做扎实，知识库默认按 `tenant_id + workspace_client_id` 隔离。✅
2. 高敏文档（身份证/银行流水/合同）是否允许进知识库？保留多久？谁能删？——**待定**。
3. AI 回答能否用于客户交付，还是仅内部辅助？免责声明？——**待定**。
4. RAG 怎么收费（按 answer / token / 文档页 / 打包套餐）？——**待定**（计划默认沿用 credits）。
5. 是否要企业版"数据不出境/私有模型"？——**待定**。
6. 泰国事务所最痛的前三个场景？——**待定**（影响 P3 规则和 P4 问答的优先级）。
7. 接受"AI 无来源就拒答"的体验底线？——**计划默认接受**，待你确认。
```
