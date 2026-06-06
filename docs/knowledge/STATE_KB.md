# Pearnly 知识库沙盒 · 状态卡 + 一页总览

> 本文件两部分：A 一页总览（很少变·快速搞懂全局）/ B 状态卡（每窗口收尾更新·交接接力棒）。

---

## A. 一页总览

**这是什么**：Pearnly 知识库/RAG 功能的本地独立沙盒（`pearnly-knowledge`，独立 git）。在此做好验透，整顿收工后整块迁回主项目 `pearnly-app`（主项目封锁期·0 新功能，绝不在此期间改主仓库）。

**目标客户**：会计事务所替多家公司做账 → 一切按 `tenant_id + workspace_client_id` 隔离。

**产品一句话**：会计照常做账，Pearnly 在旁默默挑错（死规则）+ 随处能问客户资料（RAG·带出处），拿不准的标人工，绝不替会计拍板。护城河 = 客户规矩/习惯沉淀，员工换人不怕。

**两大引擎分工**：
- 死规则（数字/格式/名单/查重·确定性·不走 LLM·秒出·零成本·可审计）← 先做
- RAG（读合同/政策等文字·带出处·无来源拒答）← 后做

**五份文档（都在 docs/）各管啥**：
1. `…融合方案_2026-06-01` — 原始大方案 / 全景（产品定位、表设计、路线图）
2. `…多窗口执行计划_2026-06-03` — **主纲**：沙盒原则、技术契约、窗口交接、阶段分解、迁移闭环
3. `…P3_死规则引擎_第一批规则清单` — 22 条死规则，细到能编码（后端施工图）
4. `…P3_client_rules_表设计` — 客户规则存储底座（白名单/金额上限/强制复核…）
5. `…UI设计_界面与前端模块映射` — 5 块界面草图（风险panel/悬浮问答/知识中心/推送拦截/管理视角）+ 对应 `knowledge-*.js` 模块；**贴合既有设计语言：磨砂玻璃+品牌猫+既有 token，不另起一套**

**阶段路线**：P0 脚手架 → P0.5 泰文 embedding spike → P1 文档基建 → P2 检索 → P3 死规则 → P4 带出处问答（含悬浮件）→ P5 OCR 风险检查合流 → P-MIG 迁移（首迁选风险最低的 P1）。

**铁律**：不碰主仓库 · 镜像主项目技术栈(FastAPI/psycopg2+SQL/PG+pgvector/Vite ES module·全文件<500) · 知识库代码只经 `host/contract.py` 取主项目东西(沙盒 stub·迁移换真) · 去AI味/注释讲why/英文标识符/中文沟通/无console.log·emoji注释/署名 Opus 4.8 · 收尾先 /simplify。

**开工前必确认**：已于 P0 只读核对完毕 →见 `docs/Pearnly_KB_主项目契约事实_2026-06-03.md`（ID 类型:ocr_history.id=UUID、workspace_clients.id=bigint；鉴权/租户/storage 真实签名,供 contract.py 对齐）。

---

## B. 状态卡（≤30 行 · 历史进 STATE_KB_ARCHIVE.md）

当前 Phase：**P1–P5 后端 + 前端全部落地（待迁移 P-MIG）**
上一棒完成：**一口气做完 P1-b→P1-c→P2→P3→P4→P5**(各自 commit·KB-P*·对真库/真 Gemini 验透)。
  - **P1-b**(dc30c23) 三表(bases/documents/ingest_jobs·Alembic 0001·PK bigserial/tenant UUID/wcid bigint)+`db.get_cursor_rls`(镜像主项目)+DAL(强制 tenant+三态可见性·软删墓碑)+CRUD API。
  - **P2**(ea4341e) `knowledge_chunks/knowledge_embeddings`(0002·`vector(768)`+HNSW cosine)+`embedding.py`(gemini-embedding-001@768 REST)+`search.py`(top-k)+上传即 embed 入库+`POST /search`。
  - **P3**(be6e885) `client_rules`(0003·7 rule_type·toggle·有效期·反馈计数)+`rules/`(24 条死规则·纯函数·泰税号 MOD-11·VAT 算术·查重注入·名单/上限/归属)+`rules_engine.run_rules`+`rules_dal`(覆盖加载·校验)+规则 CRUD API。
  - **P4**(5b1b1e8) `knowledge_answers`(0004)+`generation.py`(gemini-2.5-flash)+`ask.py`(带出处·无来源拒答)+`POST /ask`/`GET /answers/{id}`+计费 stub。
  - **P5**(e664c32) `invoice_risk_checks`(0005)+`risk_check.py`(取 OCR 历史→跑死规则→落库)+风险检查 API+OCR fixtures(查重在沙盒留 no-op·迁移接 ocr_history)。
  - **前端**(6b77034) `src/home/*` ES 模块(api/view/documents/ask/rules/risk/page/main)+四语 i18n+node 单测;无设计系统→迁移时套主项目磨砂玻璃。
本窗口该接(下一棒)：**P-MIG 迁移**——按主纲§7 把 `services/knowledge/`、`routes/knowledge_*`、`migrations/`、`src/home/knowledge-*`、i18n 整块迁回主项目,`host/contract.py` 接真鉴权/workspace/ocr_history/storage/credits。**首迁仍建议 P1 切片**(纯新增·不碰高敏热路径)。
坑/须知：
  - **Docker 起库**:这台是**开发机**(7×24 生产机是另一台备用笔记本·见 [[laptop-production-decision]])。`docker compose up -d` 起、重启不自启·db.py 默认 `localhost:5433`。
  - **Gemini key 在 `eval/.gemini_key`(gitignore)**·沙盒 conftest/app_local 自动载入;⚠️建议 Zihao 轮换(明文出现过)。
  - **已拍板(2026-06-04·Zihao)**:① firm-scope 知识**任何成员都可建**(先放开·不加角色门);② RAG **先不计费·只记用量**(charge_credits 记日志 stub 保留·商业化再设套餐);③ **AI 只做内部参考·不直接面客**(会计核对后回客户·贴合"绝不替会计拍板"定位)+高敏文档"存·可删·随账套走"。见 [[kb-product-decisions]]。
  - **仍待定/技术项**:查重落地(沙盒 no-op·迁移接主项目 ocr_history 真查重)。
  - **泰文语料**:P2 上相似度阈值前扩到 50-100 含易混样本重测(满分=区分度不够)。
已拍板(2026-06-03)：生产机=另一台闲置备用机·7×24 跑 embedding+向量库;生成走云 Gemini。见 [[laptop-production-decision]]。
守门状态：pytest **88 passed** + 前端 node **11 passed** / eval R@1=1.0 / 行数 最大<500 · 守门 4 闸全绿(68 文件)。迁移 0001–0005 全部 `alembic upgrade head` 通。
迁移就绪度：**P1–P5 全栈就位**·待 P-MIG 接线(host/contract.py 换真实现 + 前端套设计系统 + bump 缓存)。

—— 交接规矩：开局读 AGENTS_KB.md → 本卡 B → 干活；收尾跑 /simplify → 守门全绿 → 更新本卡 B → commit（署名 Opus 4.8）→ 一句话报告。本卡 B 保持 ≤30 行，A 段基本不动。
