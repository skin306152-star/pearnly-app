# Pearnly 知识库 · P3 · `client_rules` 表设计

生成日期：2026-06-03
作者：Opus 4.8（设计，非执行）
配套：《…多窗口执行计划…》第 6 节 P3 / 《…P3 死规则引擎_第一批规则清单…》E、F 类规则
作用：存放所有**按客户（账套主体）定制的规则**，供死规则引擎按 `tenant_id + workspace_client_id` 加载。

---

## 0. 核心设计决定（先读，决定了一切）

1. **一行 = 一条规则**（不是一行存一整套配置）。
   - 理由：① 每条规则能单独记**来源**（人工录入 / 从合同提取 / 从会计修正学来）、**置信度**、**采纳/忽略反馈**；② 学习与审计都按"条"走；③ 增删改互不影响。
   - 代价：白名单 50 个供应商 = 50 行。可接受，且换来可学习、可审计。
2. **全局规则 vs 客户规则分层**：`workspace_client_id = null` 表示"整个事务所(tenant)通用"；非空表示"只对这个账套主体"。引擎加载时**两者都取**，客户级覆盖事务所级。
3. **`rule_body` 用 jsonb 装"参数"，但每个 `rule_type` 的 body 有固定 schema**（见第 3 节）。灵活但不失约束——写入时按类型校验。
4. **隔离铁律**：每行必带 `tenant_id`，客户私有规则必带 `workspace_client_id`，所有查询强制这两个过滤。A 租户的规则绝不作用于 B 租户。
5. **反馈三连**（`hit/accepted/dismissed`）从第一天就记，支撑"采纳率"指标与"自动退役噪声规则"。

---

## 1. 建表 DDL（⚠️只走 Alembic·禁 ensure_·见《铁律对齐补丁》§1）

> **类型约定**（依《契约事实》P0 核对）：本知识库系列新表主键统一 **`BIGSERIAL`**；引用既有主项目表时按其真实类型——`tenant_id`/`created_by`=**UUID**（users/tenant 是 UUID）、`workspace_client_id`=**BIGINT**（workspace_clients.id=bigint）、引用 `ocr_history` 用 **UUID**。

```sql
client_rules (
  id                    bigserial primary key,         -- 本系列统一 BIGSERIAL
  tenant_id             uuid    not null,               -- UUID（多租户隔离键）
  workspace_client_id   bigint  null,                  -- null=事务所通用；非空=该账套专属（=workspace_clients.id bigint）

  rule_type             text    not null,       -- 规则类型，见第 2 节 check
  subject_type          text    not null        -- 规则作用对象：'supplier'|'category'|'contract'|'global'
                        check (subject_type in ('supplier','category','contract','global')),
  subject_key           text    null,           -- 对象标识：supplier=seller_tax_id, category=类别码, contract=合同号; global=null
  rule_body             jsonb   not null default '{}'::jsonb,   -- 按 rule_type 的参数(见第 3 节)
  severity              text    null            -- 覆盖该规则命中时的默认严重度；null=用引擎默认
                        check (severity is null or severity in ('high','medium','low')),

  is_active             boolean not null default true,
  effective_from        date    null,           -- 生效起(含)；null=即时
  effective_to          date    null,           -- 失效止(含)；null=长期

  -- 来源 / 学习（支撑"从修正偷学规则"）
  origin                text    not null default 'manual'      -- 'manual'|'learned'|'imported'|'extracted'
                        check (origin in ('manual','learned','imported','extracted')),
  confidence            numeric null,            -- learned/extracted 规则的置信度 0..1；manual=null
  source_document_id    bigint  null,            -- extracted: 从哪份知识库文档提取(→knowledge_documents.id bigserial)
  source_correction_id  bigint  null,            -- learned: 从哪条人工修正学来(→后续 corrections 表 bigserial)

  -- 审计
  created_by            uuid    null,            -- users.id = UUID
  created_at            timestamptz not null default now(),
  updated_by            uuid    null,
  updated_at            timestamptz not null default now(),

  -- 反馈（采纳率 / 噪声治理）
  hit_count             int     not null default 0,   -- 命中并产出 finding 的次数
  accepted_count        int     not null default 0,   -- finding 被用户采纳
  dismissed_count       int     not null default 0    -- finding 被用户忽略
)
```

**索引**：
```sql
-- 引擎加载：按租户+账套+类型取活跃规则
create index on client_rules (tenant_id, workspace_client_id, rule_type) where is_active;
-- 单点查：某供应商/类别是否命中某规则
create index on client_rules (tenant_id, workspace_client_id, subject_type, subject_key) where is_active;
```

**唯一性（建议）**：同一 `(tenant_id, workspace_client_id, rule_type, subject_type, subject_key)` 通常只该有一条活跃规则。可加部分唯一索引防重复录入：
```sql
create unique index on client_rules (tenant_id, coalesce(workspace_client_id,-1), rule_type, subject_type, coalesce(subject_key,''))
  where is_active;
```

---

## 2. `rule_type` 枚举（对应 P3 规则清单 E/F 类）

```sql
check (rule_type in (
  'supplier_allowlist',        -- R-SUP-01 供应商白名单（在册=允许）
  'supplier_force_review',     -- R-SUP-02 该供应商强制人工复核
  'amount_limit',              -- R-LIMIT-01 金额上限
  'no_auto_push_category',     -- R-CAT-01 该费用类别禁止自动推 ERP
  'wht_rate',                  -- R-WHT-01 预扣税率（按类别）
  'accounting_period',         -- R-DATE-02 允许的会计期间
  'feature_toggle'             -- 开关：某客户是否启用某检查（见第 4 节）
))
```
> 第一批就这 7 种。新增检查时往这里加枚举 + 第 3 节加 body schema + 引擎加 loader，三处同步。

---

## 3. 每种 `rule_type` 的 `rule_body` schema 与用法

| rule_type | subject_type / subject_key | rule_body 字段 | 引擎怎么用 | 默认 severity |
|---|---|---|---|---|
| `supplier_allowlist` | `supplier` / `seller_tax_id` | `{supplier_name, note}` | 启用白名单时，来票供应商**不在册**→命中(R-SUP-01) | medium |
| `supplier_force_review` | `supplier` / `seller_tax_id` | `{reason}` | 来票供应商在册→置 `needs_human_review`(R-SUP-02) | high |
| `amount_limit` | `supplier`\|`category`\|`contract` / 对应 key | `{limit:number, currency:'THB', basis:'total'\|'net', period:'per_invoice'\|'monthly'}` | 票额(按 basis)超 limit→命中(R-LIMIT-01)。monthly 需累计当月 | high |
| `no_auto_push_category` | `category` / 类别码 | `{reason}` | 票归此类→标"禁止自动推 ERP"(R-CAT-01)，阻断 auto-push guard | medium |
| `wht_rate` | `category` / 类别码 | `{expected_rate:number}` | 票声明 WHT 且类别匹配→校验率(R-WHT-01) | medium |
| `accounting_period` | `global` / null | `{mode:'fixed'\|'current_month'\|'prev_month', period_start?, period_end?, grace_days?:int}` | `invoice_date` 不在期内→命中(R-DATE-02) | medium |
| `feature_toggle` | `global` / 开关名(如 `supplier_allowlist`) | `{enabled:bool}` | 引擎据此决定某检查开/关(见第 4 节) | — |

**写入校验**：每个 rule_type 配一个 body 校验器（`subject_key` 该有就必须有、数值字段类型对、currency 合法等），写入 API 先校验再落库。

---

## 4. "检查是否启用"怎么表达（重要的边界设计）

部分检查是"客户开了才查"（如白名单）。**不要用"有没有数据"来隐式判断启用**（会导致"想启用空白名单"表达不出来）。显式用 `feature_toggle`：

- 行：`rule_type='feature_toggle', subject_type='global', subject_key='supplier_allowlist', rule_body={enabled:true}`
- 引擎逻辑：
  ```
  if toggle('supplier_allowlist').enabled:        # 没这行 = 默认关
      若来票供应商不在 supplier_allowlist 集合 → 命中 R-SUP-01
  ```
- 同理 `accounting_period` 等"可选检查"都先查 toggle。
- 全局硬检查（税号校验、VAT 算术、查重、必填项）**不受 toggle 控制**，永远跑。

---

## 5. 引擎加载（`services/knowledge/rules_engine.py` 用法）

```
def load_client_rules(db, tenant_id, workspace_client_id) -> ClientRuleSet:
    # 取该租户下：① 事务所通用(workspace_client_id is null) ② 该账套专属，且 is_active
    #            且在有效期内(effective_from/to 包含今天)
    # 客户专属覆盖同 (rule_type,subject) 的事务所通用项
    # 返回结构：按 rule_type 索引，supplier/category 类再按 subject_key 建 dict，供 O(1) 查
```
- 引擎对每张票跑规则时，命中即 `hit_count += 1`（异步/批量回写，别拖慢主路径）。
- 用户在风险报告里点"采纳/忽略"→ `accepted_count`/`dismissed_count += 1`。
- 衍生指标：`precision = accepted / (accepted + dismissed)`，可做"某规则太吵自动建议停用"。

---

## 6. 与"学习"和"提取"的衔接（为想法二/三铺底）

- **extracted（RAG 提取）**：P4 让 RAG 从合同 PDF 读出"金额上限 30000"→ 写一条 `amount_limit`，`origin='extracted'`、`source_document_id` 指向该合同、`confidence` 记检索置信度。之后比大小仍是死规则（职责分清）。
- **learned（从修正偷学）**：P5 起记录会计的每次手动修正；攒够后把高频模式提成 `client_rules`，`origin='learned'`、`source_correction_id` 可回溯、`confidence` 标可信度。**learned 规则建议先 `is_active=false` 走人工确认，再启用**，避免机器瞎学污染。
- `origin` 字段让你随时能区分"人定的"和"机器学的"，出问题能精确回溯、能批量回滚某来源。

---

## 7. 验收（并入 P3 done gate）

1. 7 种 rule_type 各有写入校验单测（合法过、非法拒）。
2. 引擎按 `tenant_id+workspace_client_id` 加载，**跨租户取不到别家规则**（必测）。
3. 客户专属规则正确覆盖事务所通用规则。
4. `feature_toggle` 开/关切换即时改变对应检查行为。
5. 命中后 `hit_count` 增长；模拟采纳/忽略，`accepted/dismissed` 正确累加。
6. `effective_from/to` 边界（生效前/失效后不命中）覆盖。

---

## 8. 第一批不做（留后）

- 规则之间的优先级/互斥编排（先靠 severity + 人工）。
- 规则版本历史表（先靠 updated_at/by；要审计快照再加 `client_rules_history`）。
- 跨账套共享规则模板库（事务所级"标准规则包"一键套用）——商业化阶段再做。
- 复杂条件规则（AND/OR 组合、字段表达式 DSL）——第一批只做"按对象单条匹配"，够覆盖 E/F 类。
