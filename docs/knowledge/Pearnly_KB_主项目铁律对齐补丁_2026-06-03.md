# Pearnly 知识库 · 主项目铁律对齐补丁

生成日期：2026-06-03
作者：Opus 4.8（设计，非执行）
依据：对主项目 `pearnly-app` 的只读核查（CLAUDE.md/CLAUDE.md 28+ 铁律、ENGINEERING_STANDARD.md、scripts/git-hooks/pre-push、check_*.py、services/startup.py、core/db.py、src/main.js、vite.config.mjs）。
作用：**纠正本项目早先设计文档中与主项目真实规矩不符的地方**，尤其是几处"会让沙盒重犯整顿正在清除的债"的错误。**本补丁优先级高于早先文档的冲突表述。**

---

## 0. 一眼看懂改了什么（早先文档 → 正确做法）

| 早先文档说 | 真实/正确 | 严重度 |
|---|---|---|
| 新表用 Alembic + startup `ensure_*` **双保险** | **只走 Alembic，禁新增 `ensure_*`** | 🔴 会重犯整顿债 |
| 新表主键多用 `uuid`（凭 DDL 猜） | 以 P0 实地核对为准：`ocr_history.id=UUID`、`workspace_clients.id=bigint`、`tenant_id`=`UUID`（见契约事实文档） | 🔴 类型必须实地查 |
| 宿主契约只有 `get_db()` | 必须有 **RLS 感知游标** `get_cursor_rls(tenant_id=...)`（铁律#26） | 🔴 高敏隔离 |
| 守门 6 道 | **本地 pre-push 7 道 + CI 6 道**，另有整顿硬门槛 | 🟡 漏项 |
| 起库用 Docker 最省事 | **本机未装 Docker**，改本地原生 PG（见 §9） | 🟡 环境 |

---

## 1. 🔴 新表只走 Alembic，禁新增 `ensure_*`（最重要·别重犯整顿债）

- **铁律#23 硬门槛**含"无新 `ensure_*`"；**`check_new_debt.py`**（pre-push 第 7 道）会扫 commit diff，发现新增 `ensure_*` 函数或 `app.py` 里 `@app.*` 路由就 **fail**。
- 背景：主项目历史上 schema 逻辑堆在 `services/startup.py` 的一堆 `ensure_*` 里，整顿正在把这债务往 Alembic 迁。**沙盒若再用 `ensure_*` 建表，迁移进主项目时会被守门直接拦下，且正好是整顿要铲的东西。**
- **正确做法**：
  - 所有知识库新表 → **Alembic migration**（`migrations/versions/00X_knowledge_*.py`），`upgrade()` 里 `CREATE TABLE IF NOT EXISTS ...`。
  - 沙盒本地初始化：跑 `alembic upgrade head` 建表，不要写 `ensure_knowledge_*()`。
  - DAL 函数命名仍可用 `get_knowledge_*` / `create_knowledge_*`，但**不要 `ensure_*`**。
- 早先文档（多窗口计划 §3 表格、client_rules 表设计 §1 标题"Alembic + ensure 双保险"、各表"建表 DDL"）凡提"ensure 双保险"的，**一律改为"Alembic only"**。

---

## 2. 🔴 ID 主键类型校准（以 P0 实地核对为权威）

> ⚠️ 修订：本节最初凭间接推断写"history_id=TEXT"，**已被 P0 窗口实地核对推翻**。权威结论以 `docs/Pearnly_KB_主项目契约事实_2026-06-03.md` 为准——该文档是 P0 真去主项目 `\d` 查出来的，本节服从它。

P0 实地核对结论：
- **`ocr_history.id = UUID`**（不是 bigint，也不是 text）。
- **`workspace_clients.id = bigint`**。
- **`tenant_id` / `user_id` = `UUID`**（多租户隔离键）。

**对早先表设计的修正**（knowledge_* 系列 + client_rules + invoice_risk_checks）：
- `tenant_id`：**`UUID NOT NULL`**。
- `workspace_client_id`：**`BIGINT NULL`**（对齐 workspace_clients.id）。
- 引用 OCR 历史的字段（如 `invoice_risk_checks.history_id`）：**对齐 `ocr_history.id = UUID`**（早先写 uuid 这点反而对；先前补丁误改为 TEXT，作废）。
- 各表自身主键 `id` 与外键类型：**以契约事实文档为准**；若该文档未覆盖某表，写 migration 前去主项目 `\d <相关表>` 确认，别凭《融合方案》早先 DDL 猜。
- `knowledge_embeddings.embedding`：`vector(N)`，N 以 P0.5 选定的 embedding 模型为准。

> 教训：ID 类型必须实地查、不能推断。P0 已查 → 一律以契约事实文档为单一事实源。

---

## 3. 🔴 RLS 必须进宿主契约（铁律#26 · 我早先漏了）

主项目 `core/db.py` 有行级安全基础设施 `db.get_cursor_rls(tenant_id=..., bypass=..., commit=...)`，高敏操作用它而非普通 `get_cursor()`，事务级 `SET LOCAL app.current_tenant_id`。**铁律#26 列为最高优先，且 RLS 基础设施"永不动"。**

- **宿主契约层 `host/contract.py` 必须暴露 RLS 形状的游标**，例如：
  ```python
  def get_cursor_rls(tenant_id, *, bypass=False, commit=False): ...
  ```
  - 沙盒 `stubs_local.py`：本地 PG 上用普通 cursor + 可选 `SET LOCAL`（或直接普通 cursor，但**接口形状要对**）。
  - 迁移时：直接接到主项目 `db.get_cursor_rls`，知识库代码一行不改。
- **知识库所有 DAL 从第一天就用 `get_cursor_rls(tenant_id=...)`**，且 SQL 仍显式 `WHERE tenant_id = %s AND workspace_client_id ...`（应用层 + RLS 双保险，符合原方案 6.2 的"第一天就强制隔离"）。
- 别在沙盒造一套自己的隔离机制——**接口对齐主项目，实现可简化**。

---

## 4. 守门真相：本地 7 道 + CI 6 道 + 整顿硬门槛

沙盒的 `pre-commit-gate.sh` 应尽量复刻这些，**否则迁移时被主项目守门拦下**。

**本地 pre-push 7 道**（改了对应文件才跑）：
- Python：① ruff（F821/F822 未定义名·漏 import）② black --check ③ `import app` 冒烟 ④ check_imports ⑤ check_i18n --strict ⑥ 全量 unittest ⑦ **check_new_debt（禁新 ensure_/巨石路由）**
- 前端：① prettier --check（按提交内容/LF）② eslint（0 error）③ **check_ai_smell（注释 emoji + console.log）** ④ vite build

**CI 6 道**：format / unit tests / check_imports / check_i18n --strict / build / lint-size（check_file_size + check_line_ratchet）。

**整顿硬门槛（铁律#23 / #27·沙盒照做以免日后被拦）**：
- 新文件 **≥1 测试**（P0 已在写 test_smoke，对）。
- 单文件 **<500 行**（check_file_size，棘轮只降不升）。
- **i18n 4 语完整**（check_i18n --strict 0 missing/extra）。
- **无新 `ensure_*`**（见 §1）。
- 无巨石路由（知识库进独立 `knowledge_routes.py`）。
- 禁单字符提交；单次改动 **<30 文件**；行数棘轮只升不降。

---

## 5. 提交规范与署名

- **格式**：Conventional Commits — `feat(knowledge): ... ` / `refactor(...)` / `chore(...)` / `test(...)` / `docs:`。subject 英文、命令式。
- **署名**：尾部 `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`（强制）。
- **任务标记**：主项目整顿期 commit 必带 `· REFACTOR-<id>`。**沙盒是独立 repo、且做的是新功能（整顿期主项目禁新功能·铁律#18），不套 REFACTOR-**；本沙盒用自己的标记，如 `· KB-P0` / `· KB-P3`，便于追踪。**迁移进主项目那批 commit**（整顿解锁后）用 `feat(knowledge): ... `，按当时主项目规矩定标记。
- **禁 `--no-verify`**（除非人工明确放行）。
- 沙盒阶段 push 到哪：本地或你自建远程皆可，**不 push 到主项目仓库**。

---

## 6. 前端真相（迁移时照此接线）

- **构建产物**：`vite build` → `static/dist/main.js`（无 hash，固定名）；入口 `src/main.js` 用 side-effect import 串起所有 `home/*` 模块。
- **import 顺序有讲究**：`state.js` / `core.js` / 骨架注入模块 / `core-boot.js` 必须靠前（被后续模块依赖）；自包含模块（dashboard/billing 那类）靠后。知识库模块属"自包含+按需挂载"，**排后面**，别插进早期引导段。
- **i18n**：源在 `static/i18n-data.js`（`window.I18N = { zh, en, th, ja }`），四语同步加 key；用 `window.t('key')` 取；提交前 `check_i18n.py --strict` 必 0 missing。
- **缓存破除**：改前端必在 `home.html` 给对应资源 bump `?v=`；`/api/version` 从 home.html 解析该号。迁移那刻必做（铁律）。
- **状态诚实 + 全态 UI**（ENGINEERING_STANDARD §2.4）：rows=0/failed/需映射绝不显成功；加载/空/错误/无权限都要有 UI，不静默吞错（home.js silent=0）。知识库的 ingest 状态、问答无来源、风险检查失败都要如实呈现。

---

## 7. 路由 / services 落点确认

- 命名习惯核对结果：**`services/knowledge/`（子域文件夹小写）+ `routes/knowledge_routes.py`** 完全符合主项目现有 57 个 `*_routes.py` 与 services 子域（erp/ocr/recon/billing/auth/exceptions/membership/workspace…）的命名习惯。早先文档的命名**正确，无需改**。
- 路由注册：迁移后在 `app.py` 加 `from routes.knowledge_routes import router as knowledge_router; app.include_router(knowledge_router)`。
- 鉴权/租户解析：用主项目 `core/route_helpers.py` 的依赖 `_tid`（解析 JWT 得 tenant_id）、`_plan_permissions`（权限）。沙盒 `host/contract.py` 的 `get_current_identity` 迁移时接到这两个依赖。
- DAL 暴露：若旧调用点需要，迁移时在 `services/dal_reexports.py` 的 re-export 字典补条目（参考主项目既有做法）。
- 目录重组方案B：业务路由最终是否从 root `routes/` 再移位，主项目铁律#30 说"最后做、暂未定"——**沙盒按 `routes/knowledge_routes.py` 写即可**，跟随主项目最终落点。

---

## 8. 去 AI 味：标准 13 条 vs 机械闸实查项

- **ENGINEERING_STANDARD 列了 13 种 AI 味**（过度注释复述代码、emoji/叙事腔、防御性冗余、泛化命名 data/result、docstring 套话、调试残留、AI 自述 as requested/I added、==/=== 混用、过度抽象、复制粘贴、魔法数、样板膨胀）。写代码当下就避免。
- **但机械闸 `check_ai_smell.py` 目前只硬查两类**：注释里的 emoji + `console.log` 残留（只扫 `src/`）。其余靠自觉 + lint + review。
- 沙盒 `pre-commit-gate.sh` 至少复刻这两项机械检查；其余 13 条作为写码纪律。

---

## 9. Docker 未装 → 本地 PG + pgvector 方案

P0 窗口实测 `docker: command not found`。`scripts/db_init.sql`（`CREATE EXTENSION vector`）保留没问题，但执行方式改为本地原生 PG：

- **推荐**：本机装 PostgreSQL（含 pgvector）。Windows 上可用 EDB 安装包 + 自编/预编 pgvector，或用带 pgvector 的便携发行版。装好后 `psql -f scripts/db_init.sql` 启用扩展，`alembic upgrade head` 建表。
- **P0 解耦得好**：窗口已把 `test_smoke.py` 设计成"无 DB 也能起、host 契约默认走 stub"——所以 **P0 不被 DB 阻塞**，真实 PG 可推迟到 P1（要落表/检索时）再就位。
- 备选：装不动本地 PG 时，临时用一个带 pgvector 的托管 PG（仅本地开发用，别放真客户数据）。
- 此项不影响迁移：生产是 Supabase Postgres 启用 pgvector，沙盒只是本地等价物。

---

## 10. 别重犯的整顿债（汇总·钉在墙上）

整顿正在主项目铲下面这些债。**沙盒从第一天就不许产生同类债**，否则迁移=把债又搬回去：

1. ❌ 新增 `ensure_*` 建表 → ✅ Alembic only。
2. ❌ 把逻辑堆进巨石文件（app.py/db.py 式）→ ✅ 独立 `services/knowledge/*`、`routes/knowledge_routes.py`，每文件 <500 行。
3. ❌ 静默吞错（空 except / silent 失败）→ ✅ 全态 UI + logger，状态诚实。
4. ❌ 注释 emoji / console.log / AI 自述 / 死代码残留 → ✅ check_ai_smell + 写码纪律。
5. ❌ i18n 缺语 → ✅ 四语齐全，--strict 通过。
6. ❌ 魔法数 / 泛化命名 / 复制粘贴 → ✅ 具名常量、自解释名、DRY。
7. ❌ 状态多处持久化 → ✅ 单一 source of truth（铁律#12）；知识库不写 `erp_push_logs` 等既有事实源。
8. ❌ 应用层裸过滤当唯一隔离 → ✅ RLS（get_cursor_rls）+ 显式 tenant/workspace 过滤双保险。

---

## 附：需要回改的早先文档（待迁移前清账）

以下早先文档与本补丁冲突处，**以本补丁为准**；有空时回改正文以免误导后续窗口：
- 《多窗口执行计划》§3 技术契约表："Alembic + 启动 ensure 双保险" → "Alembic only，禁新 ensure_"。
- 《client_rules 表设计》§1 标题与 DDL：主键 uuid → BIGSERIAL；"双保险" → Alembic only。
- 《融合方案》§9.2 各表 DDL：PK/FK 类型以《契约事实》为准（`ocr_history.id=UUID`、`workspace_clients.id=bigint`、`tenant_id=UUID`）；未覆盖的表 `\d` 现查。
- 《多窗口执行计划》§4 宿主契约：`get_db()` 已改为 `get_cursor_rls(tenant_id=...)`。✅已改
