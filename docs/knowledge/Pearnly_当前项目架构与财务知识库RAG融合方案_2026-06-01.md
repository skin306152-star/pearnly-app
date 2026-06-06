# Pearnly 当前项目架构与财务知识库/RAG 融合方案

生成日期：2026-06-01  
分析范围：本地仓库 `C:\Users\skin3\Desktop\pearnly-app` 只读分析。未修改源码，未连接生产数据库，未读取密钥，未执行会产生业务副作用的请求。

## 1. 一句话结论

Pearnly 当前已经不是“OCR 小工具”，而是一个面向泰国财务场景的多租户 SaaS 雏形：以发票 OCR 为入口，向客户/账套管理、ERP 推送、对账、DMS 身份证录入、credits 计费、后台运营和多语言用户体验扩展。下一阶段如果要加入“财务知识库/RAG”，正确定位不是做一个独立聊天机器人，而是把它接到现有 OCR、ERP、对账和事务所多客户工作流中，成为“带引用来源、可审计、按客户隔离的财务判断辅助层”。

我的建议是：先把当前整顿计划中的 `app.py` 和认证/租户边界稳住，再做轻量 RAG V1。V1 用 PostgreSQL/Supabase + pgvector + 对象存储即可，不建议一开始引入 Neo4j、微服务或复杂知识图谱。

## 2. 本次只读检查事实

进入窗口后的项目状态：

- 当前分支：`master`
- 工作区：干净，`master...origin/master`
- 最新提交：`3062b6b docs(state): C3 收官 — app shell 抽 JS 上线 · 状态卡+AGENTS 刷新 · 下个 task=app.py · REFACTOR-WB-C3`
- `scripts/refactor_progress.py` 实时结果：整体 94%
- 当前巨石真实数字：`app.py` 1731 行，目标 500，剩余约 1231 行；`home.html` 397 行，`home.js` 0 行，`db.py` 344 行，`home.css` 0 行
- 代码路由 AST 扫描：约 270 个 HTTP endpoint
- 前端模块：`src/home` 约 106 个 ES module
- 测试文件：`tests` 约 305 个文件
- RAG/vector 代码痕迹：未发现 `pgvector`、embedding 表、知识库表或 RAG 服务模块；历史文档中曾提过 memory/RAG 路线，但尚未产品化落地

核心参考文件：

- `app.py`：FastAPI app 入口，剩余主 OCR/LINE 热路径仍在这里
- `db.py`：Postgres 连接池 + DAL facade/re-export
- `services/startup.py`：启动时 ensure 表/列、worker、部署脚本、健康恢复
- `services/ocr/*`：分层 OCR 管线
- `erp_push.py`、`services/erp/*`：ERP 推送、MR.ERP/Xero/DMS 适配
- `src/main.js`、`src/home/*`、`home.html`：前端 shell 与模块化应用
- `static/admin/*`：独立 admin SPA
- `docs/agent/BUSINESS_GLOSSARY.md`：业务概念权威解释，尤其是 `workspace_client_id` 与 `history.client_id` 的边界

## 3. 当前系统架构

### 3.1 后端形态

后端是 FastAPI 单体应用，已进入“巨石拆分整顿期”。`app.py` 现在主要承担：

- app 初始化、CORS、lifespan、异常处理、静态资源版本和 router include
- 当前仍残留的主业务路由：`POST /api/ocr/recognize`
- LINE 图片/文件 OCR 背景处理路径

大部分业务路由已经拆到独立 `*_routes.py`：

- 认证与账号：`login_routes.py`、`auth_signup.py`、`auth_email_code_routes.py`、`oauth_routes.py`、`line_*_routes.py`
- 用户与团队：`me_routes.py`、`team_routes.py`
- 客户与账套：`clients_routes.py`、`workspace_routes.py`
- OCR/history/export：`ocr_export_routes.py`、`history_routes.py`
- ERP：`erp_routes.py`、`erp_endpoints_routes.py`、`erp_mappings_routes.py`、`erp_push_log_routes.py`、`erp_xero_routes.py`
- 对账/导入/报表：`recon_routes.py`、`recon_jobs_routes.py`、`vat_excel_routes.py`、`bank_recon_routes.py`、`import_routes.py`、`report_routes.py`
- 计费：`billing_credits_routes.py`、`billing_topup_routes.py`
- Admin：`admin_*_routes.py`、`tenant_routes.py`、`admin_diagnostics_routes.py`

数据访问层是 psycopg2 + SQL，`db.py` 只保留连接池和 facade，真实领域逻辑拆到 `services/**` 后由 `services/dal_reexports.py` 重新暴露给旧调用点。这是过渡期很合理的打法：行为稳定，文件逐步变小。

### 3.2 数据库形态

数据库是 Supabase Postgres。当前生产部署不跑 `alembic upgrade`，而是在启动时通过一组 `ensure_*` 函数保证表和列存在，Alembic 更多承担留档/迁移记录的角色。

核心数据域：

- 身份与租户：`users`、`tenants`、`memberships`、`roles`、`client_assignments`、`user_company_roles`
- 账套与客户：`workspace_clients`、`seller_workspace_routes`、`clients`、`buyer_to_client_memory`、`supplier_categories`
- OCR 历史：`ocr_history`、`ocr_cost_log`、`pdf_storage_path`
- ERP：`erp_endpoints`、`erp_push_logs`、`erp_*_mappings`、`erp_oauth_tokens`、`erp_oauth_states`
- 计费：`tenant_credits`、`credit_transactions`、`monthly_page_usage`、`topup_requests`、`billing_balance_log`
- 异常与通知：`exceptions`、`exception_whitelist`、`notification_rules`、`notification_logs`
- 对账与导入：`vat_report`、`reconciliation_task`、`reconciliation_row`、`vat_recon_tasks`、`gl_vat_task`、`bank_recon_v2_task`、`recon_jobs`、`import_template_mappings`
- 运营与风控：`operation_logs`、`risk_log`、`payment_pending`、`login_failure_log`、`password_reset_log`

当前没有知识库、文档 chunk、embedding 或 answer/source citation 表。

### 3.3 前端形态

前端已经从历史巨石 `home.js` 拆成 Vite 入口 + 多模块应用：

- `home.html` 是薄 shell，负责 auth guard、CSS bundle、app shell placeholder、modal/drawer root、脚本入口
- `src/main.js` 通过 side-effect import 装配完整应用
- `src/home/*` 按功能分成 dashboard、OCR、history、ERP、对账、settings、team、clients、exceptions、notifications、workspace-switcher 等模块
- 管理后台是单独的 `static/admin/admin.html/js/css`，不走 home bundle
- 多语言集中在 `static/i18n-data.js`，覆盖 Thai、English、Chinese、Japanese

前端当前优点是主巨石已拆掉，首屏 shell 足够薄。风险是模块间仍有不少 `window.*` 桥接和全局状态，新增知识库时必须按现有模块化边界新增 `src/home/knowledge-*`，不要塞回大入口。

## 4. 当前核心业务流

### 4.1 OCR 主流程

主入口是 `POST /api/ocr/recognize`。流程大致是：

1. JWT 鉴权，取当前用户、tenant、计划/余额、workspace/client 参数
2. 校验文件类型、大小、PDF 页数、图片/表格格式
3. 先查文件 hash cache，命中则免费返回历史结果，并可触发自动推送/异常检查
4. 未命中则进行 credits 余额预估和准入
5. 执行 OCR pipeline
6. 拒绝非发票页，计算字段置信度，按多页发票聚合
7. 生成归档名、查重、分类学习
8. 写入 `ocr_history`
9. 成功后异步扣费，写 `credit_transactions` 与 `monthly_page_usage`
10. 自动解析 buyer 到 `clients`，解析 seller 到 `workspace_clients`
11. 触发异常检查、可选 ERP 自动推送、成本日志、PDF 留底/可搜索 PDF 回填
12. 返回页面、字段、历史 id、发票数组、duplicate/review warning、quota/credits 信息

这条路径已经是系统价值主轴，也是未来 RAG 最适合插入的地方：在 OCR 结果保存后、ERP 推送前，做带引用的“财务风险/规则/客户政策检查”。

### 4.2 OCR/AI 分层设计

`services/ocr/pipeline.py` 是一条三层流水线：

- Layer 0：PDF 文本层快速路径，或 Excel/CSV/Word/TXT 结构化读取
- Layer 1：Google Cloud Vision OCR，输出文本、词级置信度和 bbox
- Layer 2：Gemini Flash-Lite，把文本转成结构化财务字段
- Layer 3：Gemini Flash 视觉兜底，只在低置信度、金额不平、关键字段缺失、税号格式异常等触发时执行

优点：成本可控、可解释、错误可分层定位。对于 RAG，应该复用这个“低成本优先、必要时升级模型”的思路：检索和引用先行，大模型回答只作为最后一步。

### 4.3 ERP 与 DMS

ERP 目前有两类主路径：

- 发票推送：`erp_push.py` + `services/erp/auto_push.py` + `services/erp/push_dispatch.py`
- DMS 身份证录入：`dms_routes.py` + `services/ocr/id_card_extract.py` + MR.ERP DMS adapter

关键设计边界：

- `erp_push_logs` 是推送状态唯一源，不应增加第二套状态字段
- MR.ERP 没有稳定 API，实际通过 Playwright 登录网页、上传 xlsx、再查报表验证结果
- `mrerp_dms` 被硬拦截，不能作为发票 endpoint 使用；DMS 只走 `/api/dms/id-card-booking`
- MR.ERP 凭据加密保存，最后一刻解密
- Xero 走 OAuth/token 模式，与 MR.ERP 网页自动化不同

未来 RAG 不应直接推 ERP，也不应替代 `erp_push_logs`。它应该输出“检查结果/建议/引用”，由用户确认后再进入现有 push 流程。

### 4.4 计费与套餐

当前已经迁移到 credits 计费：

- `tenant_credits` 存公司余额
- `credit_transactions` 存充值/扣费/调整流水
- `monthly_page_usage` 存月用量，用于阶梯价
- `topup_requests` 存充值审核申请
- 老套餐概念基本退场，保留 `credits` 和 `admin` 两档兼容

OCR 扣费在 OCR 成功入库后异步触发。PDF 按页扣，Excel/CSV/Word 按字符估算扣。允许余额扣成负数，这是“OCR 已完成，后续补充值”的产品决策。

RAG 计费应沿用 credits，不建议另做一套 billing 表。可以新增 transaction description/type 细分，或在 usage metadata 里记录 `rag_answer`、`rag_ingest`、`rag_risk_check`。

### 4.5 多租户、团队与客户/账套

这是当前系统最重要的业务边界：

- `tenant`：一个事务所/公司账号，老板和员工共享数据
- `workspace_client_id` / `workspace_clients`：账套主体，也就是“正在为哪家公司做账”，决定数据归属、权限范围和 ERP endpoint
- `history.client_id` / `clients`：发票买方，也就是这张发票卖给谁；在 MR.ERP 里对应应收客户/debtor

这两个“客户”不能混用。知识库如果面向会计事务所服务多家公司，默认应按 `tenant_id + workspace_client_id` 隔离。不要用 `history.client_id` 作为知识库主隔离维度，否则会把“发票买方”误当成“事务所服务客户/账套主体”。

当前员工权限主要通过 `client_assignments(user_id, client_id)` 按买方 client 过滤。业务词典里已提示，未来应迁移到 workspace 维度。RAG 落地前最好先明确这一点，否则知识库会产生越权风险。

## 5. 当前优势

1. 核心价值链已经跑通：上传/OCR/历史/客户解析/ERP 推送/计费/后台运营形成闭环。
2. OCR 架构成熟：文本层、Vision、Flash-Lite、Flash 兜底、置信度和金额校验分层明确。
3. ERP 状态模型正确：`erp_push_logs` 单一事实源，避免前端乐观状态造成假成功。
4. 产品域很贴近泰国市场：Thai invoice、Thai ID card、PromptPay/KBank、MR.ERP、Xero、Thai/English/Chinese/Japanese 多语言。
5. 工程整顿方向正确：巨石拆分、CI 守门、行数脚本、E2E、i18n 检查、静态安全检查已经在建。
6. 商业化基础已经有：credits、充值审核、成本统计、admin、用户/租户/员工模型。

## 6. 当前主要风险与缺口

### 6.1 `app.py` 仍是最高风险文件

虽然很多路由已经拆出，但最关键的 OCR 主路径和 LINE OCR 路径仍在 `app.py`。这条路径牵涉认证、计费、数据库写入、PDF 存储、ERP 自动推送、异常检查。下一步拆 `app.py` 必须保持高敏流程不变，确实需要 Zihao 在场。

### 6.2 租户隔离主要靠应用层过滤

代码里已有 tenant/membership/client assignment 过滤，也有 RLS 原型工具，但 RLS 并非全局启用。对于 OCR/ERP 这种系统，应用层过滤可以支撑早期，但对 RAG 来说风险更高，因为知识库会把大量客户合同、税务文件、身份证明、政策文档集中到可检索索引里。一旦检索 filter 漏掉，就是跨客户泄露。

建议 RAG 从第一天就强制：`tenant_id + workspace_client_id` 写入每张知识库表、每条向量、每次检索 SQL、每次 answer 记录。

### 6.3 文件存储仍是本地磁盘

当前 PDF 留底用 `PDF_STORAGE_DIR` 本地文件系统，默认 `/opt/mrpilot/storage/pdfs`。本地磁盘适合当前单 VPS，但知识库会引入更多原始文档、切片文本、预览、删除/保留策略。商业化后建议迁移到 Supabase Storage 或 S3 兼容对象存储。

### 6.4 启动 ensure schema 的债务仍存在

启动时 ensure 很适合早期救火和生产兼容，但 RAG 会引入 pgvector extension、索引、文档状态机、较多表约束。⚠️**校准：新 RAG 表只走 Alembic 迁移，禁新增 `ensure_*`**（整顿正在铲除 `ensure_*` 债，`check_new_debt.py` 会拦——早先"ensure 双保险"的建议作废，见《铁律对齐补丁》§1）。

### 6.5 观测与审计需要按 AI 行为补强

当前已有 operation logs、cost logs、admin diagnostics、ready probes。RAG 需要额外记录：谁上传了哪个文档、谁问了什么、模型回答引用了哪些 chunk、是否被用户采纳、是否触发 ERP 推送、是否被删除/撤回。这些不是“聊天记录”，而是财务审计证据。

### 6.6 前端全局桥接仍多

`src/home` 模块化已经成功，但仍有较多全局状态和 `window.*` 兼容桥。新增知识库模块时要克制，不要把“文档库、搜索、问答、风险检查、引用查看器”写成一个大文件。

## 7. 财务知识库/RAG 的产品定位

建议定位：

“面向泰国会计事务所的 AI 财务自动化与客户知识库平台。”

不是：

- 通用 ChatGPT 套壳
- 单纯文档问答
- 单纯 OCR 工具
- 替代会计师做最终判断的自动记账机器人

而是：

- 每个事务所管理多个客户/账套
- 每个客户有自己的合同、发票规则、税务资料、会计政策、ERP 科目映射和历史处理习惯
- Pearnly 先用 OCR 把业务文档结构化，再用客户知识库进行带引用的辅助判断
- AI 只给建议和证据，最终确认、推 ERP、报税、付款仍由人完成

面向泰国会计事务所的关键卖点：

1. 少录入：发票、银行流水、VAT/GL 文件自动读
2. 少查资料：客户合同、税务资料、历史规则可问可查
3. 少出错：推 ERP 前发现税号、金额、供应商、账套、科目、合同规则不匹配
4. 可交接：员工离职后，客户处理习惯留在系统里
5. 可审计：AI 每个结论都带来源，不靠“模型说的”

## 8. RAG 应该接在哪些现有模块上

### 8.1 OCR 结果风险检查

在 `ocr_history` 写入后，进入 RAG 检查：

- 这张发票是否符合客户合同/采购政策
- 供应商是否在客户允许清单或历史常用清单中
- VAT、tax_id、branch、invoice date、amount 是否异常
- 是否应进入某个科目、税码、产品映射
- 是否存在与客户知识库冲突的字段

输出：`risk_level`、`findings`、`sources`、`needs_human_review`。

### 8.2 ERP 推送前检查

ERP push 前追加一个可选 guard：

- 映射缺失：customer/account/tax/product mapping
- 客户特殊规则：某些供应商必须人工复核，某些费用类别不能自动推
- 合同/PO 校验：发票金额或项目是否超合同/订单范围
- 重复风险：结合历史发票与知识库规则判断

注意：RAG 不写 `erp_push_logs` 的业务最终状态，只产生辅助检查记录；真正 push 仍由现有 ERP 流程写日志。

### 8.3 对账/报表解释

在 VAT/GL/bank recon 后，让用户能问：

- 为什么这个 bank transaction 没匹配上？
- 这批 GL/VAT 差异主要来自哪些客户/供应商/科目？
- 哪些差异需要人工补 mapping？

RAG 这里主要结合结构化任务结果 + 客户规则，不一定需要大量外部文档。

### 8.4 客户知识中心

每个 workspace client 一个知识中心：

- 公司证照、VAT registration、branch info
- 合同、报价、PO、采购政策
- 会计处理规则、税务偏好、科目说明
- ERP mapping 说明
- 历史人工修正与例外决策

这会把 Pearnly 从“处理票据”升级成“事务所客户操作系统”。

## 9. 推荐的 RAG V1 架构

### 9.1 技术选型

推荐 V1：

- 数据库：继续用 Supabase Postgres
- 向量：pgvector
- 文件：Supabase Storage 或 S3 兼容对象存储
- 后台任务：先用现有 app 内 worker/job table；量上来后再换 Redis + RQ/Celery
- Embedding：选一个稳定、多语言/泰文表现好的 embedding 模型
- LLM：沿用 Gemini/OpenAI 中较稳定的模型，回答必须带 citations
- 文档解析：复用现有 PDF/text/table 能力，必要时补 docx/xlsx/pdf OCR ingestion

不建议 V1 使用：

- Neo4j/知识图谱作为主存储
- LangChain/LlamaIndex 全家桶深度绑定
- 单独微服务化 RAG
- 细调模型/fine-tuning
- 自动报税/自动最终记账

### 9.2 新增数据表建议

> ⚠️ **类型已校准（以《Pearnly_KB_主项目契约事实》+《铁律对齐补丁》为准）**：下列 DDL 写于核对前。实际：本系列表主键统一 **`bigserial`**（已批量改）；`tenant_id`/`created_by`=**UUID**；`workspace_client_id`=**bigint**；引用 `ocr_history` 用 **UUID**（`history_id uuid` 保留正确）。**建表只走 Alembic，禁 `ensure_`。**

建议表名保持领域清晰，不与 `clients` 语义冲突：

```sql
knowledge_bases (
  id bigserial primary key,
  tenant_id uuid not null,
  workspace_client_id bigint null,
  scope text not null check (scope in ('firm','workspace_client')),
  name text not null,
  status text not null default 'active',
  created_by uuid,
  created_at timestamptz default now()
)
```

```sql
knowledge_documents (
  id bigserial primary key,
  tenant_id uuid not null,
  workspace_client_id bigint null,
  knowledge_base_id uuid not null,
  source_type text not null,
  filename text not null,
  mime_type text,
  storage_path text,
  checksum text not null,
  status text not null check (status in ('uploaded','extracting','chunking','embedding','ready','failed','deleted')),
  uploaded_by uuid,
  error_code text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
)
```

```sql
knowledge_chunks (
  id bigserial primary key,
  tenant_id uuid not null,
  workspace_client_id bigint null,
  document_id uuid not null,
  chunk_index int not null,
  text text not null,
  token_count int,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
)
```

```sql
knowledge_embeddings (
  id bigserial primary key,
  tenant_id uuid not null,
  workspace_client_id bigint null,
  chunk_id uuid not null,
  embedding vector(1536),
  model text not null,
  created_at timestamptz default now()
)
```

维度 `vector(1536)` 只是示例，应以最终 embedding 模型为准。

```sql
knowledge_ingest_jobs (
  id bigserial primary key,
  tenant_id uuid not null,
  workspace_client_id bigint null,
  document_id uuid not null,
  status text not null check (status in ('queued','running','success','failed','retrying')),
  progress int default 0,
  error_code text,
  retry_count int default 0,
  max_retries int default 3,
  created_at timestamptz default now(),
  finished_at timestamptz
)
```

```sql
ai_answers (
  id bigserial primary key,
  tenant_id uuid not null,
  workspace_client_id bigint null,
  question text not null,
  answer text not null,
  model text not null,
  status text not null default 'success',
  created_by uuid,
  created_at timestamptz default now()
)
```

```sql
ai_answer_sources (
  id bigserial primary key,
  answer_id uuid not null,
  document_id uuid not null,
  chunk_id uuid not null,
  rank int,
  score numeric,
  snippet text,
  created_at timestamptz default now()
)
```

```sql
invoice_risk_checks (
  id bigserial primary key,
  tenant_id uuid not null,
  workspace_client_id bigint null,
  history_id uuid not null,
  status text not null check (status in ('pending','success','failed','skipped')),
  risk_level text not null check (risk_level in ('low','medium','high','unknown')),
  findings jsonb default '[]'::jsonb,
  answer_id uuid null,
  human_status text default 'unreviewed',
  created_at timestamptz default now()
)
```

```sql
client_rules (
  id bigserial primary key,
  tenant_id uuid not null,
  workspace_client_id bigint null,
  rule_type text not null,
  rule_body jsonb not null,
  source_document_id uuid null,
  is_active boolean not null default true,
  created_by uuid,
  created_at timestamptz default now()
)
```

审计建议复用 `operation_logs`。如果字段不够，再扩展 `operation_logs`，不要一开始新增另一套审计事实源。

### 9.3 API 设计建议

新增 router：`knowledge_routes.py`。不要放进 `app.py`。

建议 endpoints：

- `GET /api/knowledge/bases`
- `POST /api/knowledge/documents`
- `GET /api/knowledge/documents`
- `GET /api/knowledge/documents/{document_id}`
- `DELETE /api/knowledge/documents/{document_id}`
- `GET /api/knowledge/documents/{document_id}/ingest-status`
- `POST /api/knowledge/search`
- `POST /api/knowledge/ask`
- `GET /api/knowledge/answers/{answer_id}`
- `POST /api/knowledge/risk-checks/from-history/{history_id}`
- `GET /api/knowledge/risk-checks/{history_id}`
- `GET /api/knowledge/rules`
- `POST /api/knowledge/rules`
- `PATCH /api/knowledge/rules/{rule_id}`
- `DELETE /api/knowledge/rules/{rule_id}`

每个 endpoint 第一行都应做：

- 鉴权
- tenant 解析
- workspace_client 权限检查
- role/assignment 检查
- 所有 SQL filter 带 `tenant_id` 和 `workspace_client_id`

### 9.4 前端模块设计

新增页面建议叫“Knowledge”或“Client Knowledge”。不要做营销页，直接做工作台。

建议模块拆分：

- `src/home/page-knowledge.js`：页面装配
- `src/home/knowledge-documents.js`：文档列表、上传、删除、状态
- `src/home/knowledge-ask.js`：问答输入、答案、引用来源
- `src/home/knowledge-sources.js`：来源抽屉/预览
- `src/home/knowledge-rules.js`：客户规则管理
- `src/home/knowledge-risk.js`：OCR 结果页里的风险检查 panel/drawer
- `src/home/knowledge-api.js`：fetch 封装

页面交互：

- 顶部先选账套主体，不允许在“未选 workspace client”时上传客户私有文档
- 文档列表展示 ingest 状态：uploaded/extracting/embedding/ready/failed
- 问答答案必须展示 citations，不能只有自然语言答案
- OCR 结果页增加“客户规则检查”区块：低/中/高风险、原因、来源、人工确认按钮
- 员工权限不够时隐藏上传/删除，只允许查看已授权客户的知识

### 9.5 RAG 检索流程

建议流程：

1. 用户选择 workspace client
2. 上传文档到对象存储
3. 生成 `knowledge_documents` 与 `knowledge_ingest_jobs`
4. Worker 提取文本：PDF text first，必要时 OCR，Excel/CSV/Docx 结构化读取
5. 规范化、分 chunk、写 `knowledge_chunks`
6. 调 embedding 模型，写 `knowledge_embeddings`
7. 用户提问或 OCR 触发 risk check
8. SQL 先 filter：`tenant_id = current_tenant` 且 `workspace_client_id in (selected_workspace, firm_scope)`
9. pgvector top-k 检索，必要时 rerank
10. LLM 只基于检索片段回答
11. 如果没有足够来源，回答“资料不足，无法判断”
12. 保存 answer 与 sources

### 9.6 OCR + RAG 的产品级数据流

推荐的最终数据流：

1. 会计事务所员工选择账套主体
2. 上传发票/银行流水/GL/VAT 文件
3. OCR/解析产生结构化数据
4. 系统写 `ocr_history` 或 recon task
5. RAG 检索该账套主体的知识库
6. 系统生成风险检查和建议：字段异常、税务疑点、合同/PO 不匹配、科目建议、ERP mapping 建议
7. 用户人工确认或修正
8. 系统进入现有 ERP push 流程
9. `erp_push_logs` 记录真实推送状态
10. 用户后续可以追溯：这个字段为什么这么建议、引用了哪份合同/规则、谁确认的

## 10. 安全与合规设计

### 10.1 最低安全原则

RAG 必须从第一天实现：

- 所有知识库表带 `tenant_id`
- 客户私有知识带 `workspace_client_id`
- 所有查询强制 tenant/workspace filter
- 文档原文不放公共 URL，只用签名 URL 或后端代理下载
- answer 必须保存 source citation
- 删除文档时要标记 deleted，并停止继续检索；是否物理删除按保留策略执行
- 所有上传、删除、提问、回答、risk check、ERP push 前确认都写审计
- 后台/admin 可看成本和状态，但敏感原文访问要分级控制

### 10.2 PDPA/隐私

泰国客户会涉及公司证照、税号、身份证、地址、银行流水。建议：

- 上传前告知数据用途
- 客户维度支持导出与删除
- Thai ID card 文档只用于 DMS 场景，默认不进通用知识库，除非明确授权
- 个人身份字段加 masking，不在普通列表里裸露
- 管理员操作留审计
- 对外模型调用要在条款中声明；企业版可选私有模型/私有部署

### 10.3 防幻觉规则

必须硬编码产品规则：

- 没有引用来源，不给确定结论
- 答案里每个关键判断必须能点开 source
- 不允许 AI 自称“已完成报税/已推送 ERP/已付款”
- 不允许 AI 自动改 ERP mapping、自动推送、自动删除客户数据
- 高风险结论进入人工复核
- 模型回答只能作为建议，不作为会计最终意见

## 11. 商业化设计

建议保留 credits 计费主线，不要过早引入复杂套餐矩阵。可以在商业包装上分层：

### Starter

适合小事务所试用。

- OCR 按量计费
- 少量账套主体
- 基础历史和导出
- 可选少量知识库文档和问答额度

### Pro

适合稳定处理多个客户的事务所。

- 更多 OCR 额度/更低单价
- 多员工
- 客户知识库
- 带引用问答
- ERP 推送
- 基础规则检查

### Business

适合中型事务所。

- 多账套/多员工权限
- OCR + RAG 风险检查
- 高级审计与日志
- 更高文档存储/问答额度
- 多 ERP connector
- 优先支持

### Enterprise

适合大型事务所或集团。

- 私有存储/私有模型选项
- SSO/SAML
- SLA
- 专属部署或专属 worker
- 数据保留策略定制
- API 集成

### 可计费维度

- OCR 页数/表格字符
- 知识库文档存储量
- 文档 ingestion 页数
- RAG ask 次数或 token 成本
- 风险检查次数
- 员工 seat
- 账套主体数量
- ERP push 成功量或 connector 数量

最容易被客户理解的组合：OCR 按用量 + 知识库/AI 检查按月包或 credits 消耗。

## 12. 部署与环境建议

当前生产形态：

- 服务器：VPS，`/opt/mrpilot/`
- systemd：`mrpilot`
- uvicorn：2 workers
- DB：Supabase Postgres Pooler
- 部署：push master → GitHub webhook → `git-deploy.sh` pull/cp/restart
- 健康验证：`/api/version`、`/api/ready`

RAG V1 增量需要：

- Supabase Postgres 启用 pgvector extension
- 对象存储：Supabase Storage 或 S3-compatible bucket
- embedding API key/model 配置
- 后台 ingestion worker
- 文档/embedding 成本日志
- 任务重试和失败队列
- 文档删除/保留策略

本地开发机器可以继续开发和验证，但商业生产不建议依赖本地机器。商业化 RAG 的最低生产配置建议：

- Web app：至少 2 vCPU/4GB 起步，当前 OCR/ERP 已能跑
- RAG/ingestion worker：建议独立进程，4 vCPU/8GB 更稳
- DB：继续托管 Postgres/Supabase，监控 vector index 体积和查询延迟
- Storage：对象存储，不再靠单机磁盘长期保存全部知识文档

## 13. 实施路线图

### Phase 0：先完成当前整顿红线

目标：不在高敏巨石上叠新功能。

- 完成 `app.py` 1731 → 500 的拆分
- 保持 OCR/计费/认证/ERP 主路径 E2E 绿
- 明确 workspace 权限维度，不再混用 `clients`
- 保持 `erp_push_logs` 单一事实源

### Phase 1：知识库基础设施

目标：能上传、解析、存储、检索。

- 新增 knowledge schema 和 router
- 对象存储接入
- ingest job 表和 worker
- PDF/text/docx/xlsx/csv extraction
- chunk + embedding + pgvector search
- 前端文档库页面

### Phase 2：带引用问答

目标：用户能针对某个账套主体问问题。

- `/api/knowledge/ask`
- source citation 保存与展示
- answer history
- 权限与审计
- no-source abstain 策略

### Phase 3：OCR 风险检查

目标：让知识库真正融入现有价值链。

- `invoice_risk_checks`
- OCR 结果页风险 panel
- ERP push 前可选 guard
- 高风险人工确认
- 与 exceptions/notifications 联动

### Phase 4：客户规则与学习

目标：从文档问答变成事务所操作系统。

- 客户规则管理
- 历史人工修正变规则候选
- ERP mapping 建议
- 科目/税码建议
- 员工交接视图

### Phase 5：高级自动化与商业化

目标：企业客户可规模化使用。

- 更细权限模型
- RLS 强化
- usage/cost dashboard
- 企业版私有存储/私有模型
- 批量客户导入和 API

## 14. 优先级排序

P0：不能拖的基础

- `app.py` 拆分和高敏主路径稳定
- tenant/workspace/client 语义统一
- RAG 表设计时强制 tenant/workspace filter
- 文档存储从本地磁盘规划迁移路径

P1：最小可卖 RAG

- 客户知识库文档上传
- 文档解析、chunk、embedding
- 带引用问答
- 基础审计
- 按 credits 计费

P2：真正差异化

- OCR 后风险检查
- ERP 推送前检查
- 客户规则库
- 科目/税码/mapping 建议
- 与 exceptions/notifications 联动

P3：规模化

- RLS 全域落地
- 独立 worker/queue
- 高级审计与合规
- 企业版模型/存储/SSO

## 15. 当前不建议做的事

- 不建议先做 Neo4j。当前核心是文档检索和财务流程证据链，pgvector 足够。
- 不建议先拆微服务。单体还在整顿期，过早拆会增加部署和事务复杂度。
- 不建议 fine-tune。财务场景更需要可引用、可更新、可撤销的 RAG。
- 不建议让 AI 自动推 ERP 或自动做最终会计分录。
- 不建议把 Thai ID card 默认放入通用知识库。
- 不建议新增第二套 ERP 状态表。
- 不建议用 `history.client_id` 当事务所客户隔离维度。
- 不建议把 RAG UI 做成聊天页孤岛，应该嵌进 OCR/ERP/客户工作流。

## 16. 需要 Zihao 拍板的问题

1. Pearnly 未来主客户是谁：小企业自己用，还是会计事务所服务多家公司？如果是后者，workspace/client 权限要优先做扎实。
2. 知识库是否允许上传身份证、银行流水、合同等高敏文档？默认保留多久？谁可以删除？
3. AI 回答是否可以用于客户交付，还是仅内部辅助？需要怎样的免责声明？
4. RAG 成本怎么收费：按 answer、按 token、按文档页数，还是打包进套餐？
5. 是否需要企业版“数据不出境/不出私有模型”的路线？
6. Thai 会计事务所最痛的前三个 RAG 场景是什么：问合同、查税务资料、推 ERP 前检查、对账解释，还是员工交接？
7. 是否接受“AI 没有来源就拒答”的产品体验？这是可靠性底线，但会让某些用户觉得 AI 不够“聪明”。

## 17. 建议的第一张 RAG PR 范围

当 `app.py` 整顿完成后，第一张 RAG PR 不要做完整问答。建议只做基础设施骨架：

- 新增 `knowledge_routes.py`
- 新增 `services/knowledge/` 目录
- 新增 Alembic migration（⚠️禁 `ensure_`·见《铁律对齐补丁》§1）
- 表：`knowledge_bases`、`knowledge_documents`、`knowledge_ingest_jobs`
- API：上传/list/status/delete
- 前端：文档库页面，只展示状态，不做回答
- 守门：tenant/workspace 权限单测、上传状态机单测、i18n、build

第二张 PR 再加 chunk/embedding/search。第三张 PR 做 ask with citations。第四张 PR 才接 OCR risk check。

这样不会把新功能一次性压到 OCR/认证/计费/ERP 高敏路径上。

## 18. 最终判断

Pearnly 现在已经具备做“泰国会计事务所 AI 财务平台”的基础：OCR、ERP、账套、计费、后台、多语言、对账都已经有骨架和实战痕迹。RAG 应该作为“客户知识与财务判断层”加入，而不是另起炉灶。

最关键的设计原则只有三条：

1. 知识库按 `tenant_id + workspace_client_id` 隔离，不混用发票买方 `history.client_id`。
2. AI 所有结论必须带来源，可审计，可人工确认。
3. RAG 不替代现有 OCR/ERP/计费事实源，只增强它们。

如果按这个方向走，Pearnly 的产品边界会从“帮你读票和推 ERP”升级成“帮事务所管理每个客户的财务知识、规则和操作记忆”。这条路商业价值更大，也更符合当前代码已经长出来的形状。
