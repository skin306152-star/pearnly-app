# bank_reconcile.py 调研报告(任务 A)

> **生成日期**:2026-05-18
> **来源**:重估文档把 `bank_reconcile.py`(905 行)归 🟢 但触发 rule b stop
> **范围**:**只调研,不动手**

---

## 1. 两个调用点是什么 endpoint

### 📍 app.py:3677-3754 · `POST /api/bank-recon/upload`
- **功能**:上传银行对账单 PDF · 同步解析 · 返回 session_id
- **调用**:`br.parse_statement_pdf(pdf_bytes, filename)` (app.py:3700)
- **下游 DB 调用**:
  - `db.create_bank_recon_session(...)`
  - `db.mark_recon_parse_failed(...)`
  - `db.save_bank_recon_parse(...)`
- **返回**:session_id + 对账单元数据(bank_code / account_last4 / period / opening / closing / 流量 / tx_count)

### 📍 app.py:3811-3832 · `POST /api/bank-recon/sessions/{session_id}/match`
- **功能**:触发匹配算法 · 同步等结果(最长 60 秒)
- **调用**:`br.run_matching_for_session(session_id, str(user["id"]))` (app.py:3825)
- **下游 DB 调用**:
  - `db.get_bank_recon_session(...)`(校验)
- **返回**:匹配统计 dict

### 同一文件下其他相关 endpoint(也用同一套 DB)
- `GET /api/bank-recon/sessions`(3757)— 不直接 import bank_reconcile,只调 `db.list_bank_recon_sessions`
- `DELETE /api/bank-recon/sessions/{id}`(3801)— 同上
- `POST /api/bank-recon/tx/{tx_id}/override`(3835)— 同上
- `GET /api/bank-recon/tx/{tx_id}/candidates`(3853)— 同上
- `PATCH /api/bank-recon/sessions/{id}/client`(3865)— 同上

> ⚠ 即使删了 `bank_reconcile.py`,这些"session-based"endpoint 仍依赖 `db.bank_recon_*` 系列 DB 方法(老 schema)。**整个 `/api/bank-recon/*` 路由族都属于老体系**。

---

## 2. bank_reconcile 实际被调的函数

只有 **2 个**:
| 函数 | 调用点 | 用途 |
|---|---|---|
| `parse_statement_pdf(pdf_bytes, filename)` | app.py:3700 | 解析 PDF → ParsedStatement |
| `run_matching_for_session(session_id, user_id)` | app.py:3825 | 跑匹配 → 写回 DB → 返回统计 |

其余 **24 个**函数(`_parse_kbank_text` / `_parse_scb_text` / `score_amount` / `score_date` / `match_one_tx` / 等等)都是这两个的内部 helper,**对外只暴露 2 个**。

---

## 3. bank_recon_v2 有无等价函数

### 函数对照表

| 老 bank_reconcile | 新 bank_recon_v2 | 是否等价 |
|---|---|---|
| `parse_statement_pdf(pdf_bytes, filename)` → `ParsedStatement` | `parse_bank_statement_pdf(file_bytes, filename, ...)` → 别的数据结构 | **❌ 不等价**(返回 shape 完全不同 · 新的有 confidence / balance_ok 字段) |
| `run_matching_for_session(session_id, user_id)` → 统计 dict(stateful · DB-backed) | `reconcile(stmt_rows, gl_rows, ...)` → `(List[BankReconRow], BankReconSummary)`(stateless · 数据进数据出) | **❌ 不等价**(新版没有 session 概念) |

### 数据结构对照
- 老:`BankTransaction` / `ParsedStatement` 类(dataclass)
- 新:`StatementRow` / `GlRow` / `BankReconRow` / `BankReconSummary`(全部不同 dataclass)

### DB 层对照
- 老:`db.create_bank_recon_session` / `db.save_bank_recon_parse` / `db.list_bank_recon_sessions` 等 9+ 个 `bank_recon_*` 方法(老 schema)
- 新:bank_recon_v2 走 `reconciliation_task` 表(新 schema)+ 不复用老 `bank_recon_session` 表

---

## 4. 能否 import 名字一改就切

### 🔴 不能。原因:

1. **函数签名不同**:`parse_statement_pdf(bytes, str)` vs `parse_bank_statement_pdf(bytes, str, ...)`
2. **返回类型不同**:`ParsedStatement` 一个类 vs `(rows, opening, closing, bank_code)` 一个 tuple
3. **业务模型不同**:
   - 老:stateful · 先 upload → DB 建 session → 再 match → 写候选到 DB
   - 新:stateless · 一次性把 stmt + gl 一起喂进去 · 直接出对账行 + 汇总
4. **DB schema 不同**:老一组 `bank_recon_*` 表,新一组 `reconciliation_task` 类。**两套表都还活着**。
5. **HTTP 路由不同**:
   - 老:`/api/bank-recon/upload` + `/api/bank-recon/sessions/{id}/match`(2 步)
   - 新:`/api/recon/bank-v2/run`(1 步)

### ⚠ 关键判断

**bank_reconcile.py + 整套 `/api/bank-recon/*` 路由族 + `db.bank_recon_*` 系列函数 = 一个完整的"老体系"**,不是孤立的一个文件。

要真正"删 bank_reconcile.py",需要:
- 删 app.py 整段 `/api/bank-recon/*` 路由(7 个 endpoint · 估 200+ 行)
- 删 db.py 里 `bank_recon_session` / `bank_recon_tx` / `bank_recon_candidate` 等表的 9+ 个 CRUD 函数
- 跑 DB 迁移把老 `bank_recon_session` 表 drop 掉(或保留作历史)
- 改前端 `home.js` 把 bank-recon UI 切到 `/api/recon/bank-v2/run`(可能 0-500 行,看现状)

---

## 5. 当前用户/前端 vs 老体系的关系

⚠ 未深入调研以下问题(超出本任务调研范围,需用户判断):
- 前端 `home.js` 现在还有没有调用 `/api/bank-recon/upload` / `/api/bank-recon/sessions/*` 的代码?
- 如果有,是 v2 已替代 + 前端没切?还是双轨制并存?
- 老 `bank_recon_session` 表里是否有真实业务数据(开发阶段可清,但要确认)

---

## 6. 建议(供用户决策)

按"扁平 → 复杂"列 3 个可选路径:

### 选项 A · 最稳:**不动**
- 留 bank_reconcile.py + 整套老路由 · 不增任何风险
- 不省任何维护成本(代码常驻 905 + 200+ 行)
- 适合"先不管 · 等以后再说"

### 选项 B · 中:**只删 bank_reconcile.py + 老路由(保留 DB schema)**
- 删 `bank_reconcile.py`(905 行)
- 删 app.py 3673-3886 整段 `# v0.18 · M10 · 银行对账 API`(估 200+ 行)
- 保留 db.py 里 `bank_recon_*` 函数和表(暂留 · DB 迁移另说)
- 前端 `home.js` 调老 endpoint 的地方 → 改 404 / 改打 v2
- **风险**:前端如果还在调老 endpoint,清完即刻报错
- **前置**:必须先 grep `home.js` 看 `/api/bank-recon/` 用了多少处

### 选项 C · 重:**整套 strangler 完整收尾**
- 选项 B 的所有 + 删 db.py 9+ 个 `bank_recon_*` 函数 + DB drop 老表 + 前端完整改造到 v2
- 跨多文件 · 多日工程
- 适合"想彻底干净"

### 我的看法(供参考,不代表你必须采纳)
- 选项 B 看似省事但留 DB schema 孤儿,**反而更乱**
- 选项 A 最省力但债没还
- 选项 C 是"真正完成 strangler",但工作量大
- **折中**:先做选项 B 的 grep 前置(确认前端是否还在调),再决定整体路径

---

## 7. 触发本次 stop 的关键信号

按用户 rule b("跨多文件 + >50 行")**继续触发**。即使按选项 B 也是 ~1100 行 + 跨 2 文件 + 涉及业务路由判断。

**本调研不动手 · 等你决策 A / B / C 哪条路径,或开新专门窗口处理**。

---

*调研报告 · 2026-05-18 · 阶段 3 任务 A · 不动手*
