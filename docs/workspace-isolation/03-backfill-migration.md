# 套账隔离 · 03 默认套账回填与连号改造

> 有真实生产数据 + 涉钱,迁移必须:可回滚、幂等、老用户零感知、零丢数据。
> 迁移机制按本仓既有范式:alembic 版本留档 + 生产靠 ensure_*/手动 apply(见 STATE prod 运维通道)。

## 核心难点:不是所有租户都已有套账

`workspace_clients` 是用户配账套时才建的。现实存在三类租户:
- **A. 已有 ≥1 套账**(配过账套主体 / 开过 POS):有归属落点。
- **B. 零套账但有运营数据**(纯进项/对账老用户,只用过买方 client_id):**无落点,必须先造默认套账**。
- **C. 零套账零运营数据**(新注册没动):无需回填。

→ 回填前先分类,B 类是关键。

## 回填三步(每步独立可验、可回滚)

### 步骤 1 · 为每租户确定/创建"默认套账"

```
对每个 tenant:
  若已有 active workspace_clients:
      选"主"套账作默认 = 最早创建的一条(created_at ASC LIMIT 1)
  否则(B 类):
      INSERT workspace_clients(tenant_id, user_id=租户owner, name=<租户名 或 "默认账套">,
              is_active=TRUE)   ← 造默认套账
记下映射 tenant_id → default_workspace_client_id(回填用)
```
- 幂等:重跑不重复建(先查后建 / ON CONFLICT)。
- POS/零售租户:onboarding 已建过套账主体,落 A 类,直接复用。

### 步骤 2 · 加列(可空)+ 回填孤儿行

对每张"待回填"表(products / sales_documents / document_number_sequences / etax_* / inventory_batches / bank_reconcile_sessions / recon_jobs / vat_recon_tasks / bank_recon_v2_task):

```
ALTER TABLE <t> ADD COLUMN IF NOT EXISTS workspace_client_id BIGINT;   -- 先可空
UPDATE <t> SET workspace_client_id = <该行租户的 default_workspace_client_id>
  WHERE workspace_client_id IS NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_<t>_ws
  ON <t>(tenant_id, workspace_client_id);
```

特例:
- `ocr_history`:列已存在,大量历史行 `workspace_client_id IS NULL` → 同样回填到默认套账(让老识别记录归默认套账,不丢)。
- `bank_reconcile_sessions`:现按 user_id;回填时 default 套账取"该 user 所属 tenant"的默认套账。tenant_id 若该表没有需一并补。
- 子表(lines/transactions):不加列,不回填(经 FK 派生)。

### 步骤 3 · 收口为 NOT NULL(每模块读写切换后)

```
ALTER TABLE <t> ALTER COLUMN workspace_client_id SET NOT NULL;
```
- **时机**:该模块的读写全切到带 workspace_client_id、且回填确认无残留 NULL 之后(随对应 PO,不在回填 PO 一次性收)。
- 收口前留一道校验:`SELECT count(*) FROM <t> WHERE workspace_client_id IS NULL` 必须 0。

## 回滚策略

- 步骤 1/2 是纯加法(建套账 + 加可空列 + 回填值 + 加索引),**不破坏现有读路径**(老查询不读新列照跑)→ 出问题直接停在这,读路径还没切,零影响。
- 步骤 3(NOT NULL)+ 读路径切换随 PO,每 PO 独立 E2E 验过再上;回滚 = revert 该 PO 代码,列保持可空无害。
- 严禁:边加列边改读路径一把梭。回填(数据)与切读(代码)分 PO。

## 连号按主体改造(销项 · 高敏 · 合规)

**问题**:`document_number_sequences` 现按 tenant 计号。多主体下,事务所给 A、B 两公司开票会共用一条连号 → 每家公司账上连号有跳号 → 泰国 RD(ภ.พ.30)合规风险。每个 VAT 登记主体必须各自连续。

**目标**:连号键 = (tenant_id, **workspace_client_id**, doc_type[, 期间])。每个套账(经营主体)独立计号。

**施工注意(高敏,放销项 PO 内,Zihao 在场/先报方案)**:
1. **先核现状**:确认 `document_number_sequences` 真实唯一键 + `issue_document` 取号逻辑(FOR UPDATE 那段),确认现在是不是真按 tenant 单条。
2. **历史已开票不可动**:已 issue 的 sales_documents 连号是冻结快照,**绝不重编**。改造只影响**新取号**。
3. **迁移**:为每个 (tenant, 既有套账, doc_type) 建独立 sequence 行,**初值 = 该主体已开票的当前最大号**(避免与历史撞号)。回填默认套账的历史票后,默认套账的 sequence 也要对齐其最大号。
4. **跨主体撞号自检**:迁移后断言"任意两套账的同 doc_type 连号空间不重叠"。
5. etax 连号/通道同理按主体。

## 验收(回填 PO 专属)

- 每租户恰好一个默认套账(A 类不多建,B 类已建,C 类不建)。
- 每张待回填表零 `workspace_client_id IS NULL`(收口前)。
- 老用户登录:默认套账上下文下,看到的运营数据 = 回填前看到的全部(零丢、零变少)。
- 回填脚本幂等:连跑两次结果一致、不重复建套账、不重复改值。
- 真账号在 prod 库 dry-run(事务内跑完 rollback,零残留 · 见 STATE prod 通道范式)。
