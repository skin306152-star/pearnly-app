# 套账隔离 · 05 · PO-1 默认套账回填 执行手册(prod runbook)

> 代码:`services/db_migrations/workspace_backfill.py`(report / apply)。
> 性质:纯加法(建默认套账 + 加可空列 + 回填孤儿)· 不切读路径 · 出问题零影响。
> 铁律:**先 dry-run 给 Zihao 过目影响行数,再 apply**。apply 单事务,失败整体回滚。

## prod 通道(见 STATE「prod 运维通道」)

```
ssh pearnly → cd /opt/mrpilot → source .env(取 DATABASE_URL)
venv:/opt/mrpilot 原生 venv(非 docker)· 需 PYTHONPATH=/opt/mrpilot
```

## 步骤 1 · DRY-RUN(零改动 · 必做)

```bash
PYTHONPATH=/opt/mrpilot python -c \
  "from services.db_migrations import workspace_backfill as w; \
   import json; print(json.dumps(w.report(), ensure_ascii=False, default=str))"
```
`report()` 在单事务内真做一遍再 ROLLBACK,拿到真实影响。看三项:
- `tenants_needing_default`:会给几个"零套账"老租户新建默认套账(B 类)。
- `tables[*].orphans_before / filled`:每表回填前孤儿数 / 能回填数。
- `remaining_null`:回填后仍为 NULL 的(应≈0)。**非 0 = 租户无关的个人模式旧数据**
  (tenant_id IS NULL),需单独决定(给个人用户建 user 级套账 / 或保留 NULL 暂不收 NOT NULL)。

→ **把这份 JSON 给 Zihao 过目**,确认行数合理(无异常放大)再继续。

## 步骤 2 · APPLY(真执行)

```bash
PYTHONPATH=/opt/mrpilot python -c \
  "from services.db_migrations import workspace_backfill as w; \
   import json; print(json.dumps(w.apply(), ensure_ascii=False, default=str))"
```
返回 `default_workspaces_created / columns_added / filled`。单事务,异常自动回滚。

## 步骤 3 · 建索引(事务外 · CONCURRENTLY · 不锁表)

apply 不建索引(CONCURRENTLY 不能在事务内)。逐条手跑(大表不阻塞写):
```sql
-- 有 tenant_id 的表:
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_products_ws              ON products(tenant_id, workspace_client_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_product_units_ws         ON product_units(tenant_id, workspace_client_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_inventory_batches_ws     ON inventory_batches(tenant_id, workspace_client_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_sales_documents_ws       ON sales_documents(tenant_id, workspace_client_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_docnum_seq_ws            ON document_number_sequences(tenant_id, workspace_client_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_etax_submissions_ws      ON etax_submissions(tenant_id, workspace_client_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_etax_channel_ws          ON etax_channel_settings(tenant_id, workspace_client_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_recon_jobs_ws            ON recon_jobs(tenant_id, workspace_client_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_vat_recon_tasks_ws       ON vat_recon_tasks(tenant_id, workspace_client_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_bank_recon_v2_task_ws    ON bank_recon_v2_task(tenant_id, workspace_client_id);
-- 无 tenant_id(按 user_id)的表:
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_bank_recon_sess_ws       ON bank_reconcile_sessions(workspace_client_id);
-- ocr_history 已有 idx_ocr_history_workspace(workspace store 建过)· 不重复。
```
> 列名以 dry-run 实际存在的表为准(introspection 已跳过不存在的表;索引按此清单手核)。

## 步骤 4 · 验证

```bash
# 重跑 report():tenants_needing_default 应为 0;remaining_null 应空(除个人模式旧数据)。
PYTHONPATH=/opt/mrpilot python -c "from services.db_migrations import workspace_backfill as w; print(w.report())"
```
另:抽一个多套账租户,确认其 sales_documents / ocr_history 的 workspace_client_id 已落到默认套账。

## 回滚

- 列可空且无人读 → 留着无害。无需回滚即安全。
- 如确需还原:`ALTER TABLE <t> DROP COLUMN workspace_client_id;`(数据回填值随列一起去除,不影响老读路径)。
- 新建的默认套账可保留(后续模块 PO 正需要它);如要删需先确认无数据指向。

## 完成判据

`tenants_needing_default=0` · 各表 `remaining_null` 仅剩(若有)个人模式旧数据并已记录决定 ·
索引就位 · 老功能真账号冒烟无异常(读路径未变,应零影响)。NOT NULL 收口留各模块 PO。
