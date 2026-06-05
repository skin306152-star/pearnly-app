# 08 · 迁回主仓库指南(逐文件落点 + 守门处理)

> 两闸都过才迁:① 整顿收官 ② 客户拍板(TBD 定型)。见 `README.md`。
> 原则:迁回 = 把沙盒文件**放进主仓库对应包目录** + 走迁移应用 + 配测试 + 处理守门 + bump 缓存。

## 后端落点(`routes/` + `core/` + `services/`)

| 沙盒产出 | 主仓库落点 | 说明 |
|---|---|---|
| 商品 API | `routes/products_routes.py` | 仿 `clients_routes.py` 结构(APIRouter + RLS) |
| 销项单据 API | `routes/sales_routes.py` | issue/void/pdf/send |
| 智能录入 API | `routes/intake_routes.py` | extract/verify/validate,内部调现有 OCR/RD/knowledge |
| 业务逻辑 | `services/sales/` (新域) | 取号、金额计算、不可变写保护、PDF 生成 |
| LINE intent | 改 `routes/line_webhook_routes.py` | 挂现有 webhook,不新开端点 |
| ภ.พ.30 扩展 | 改 `services/vat/` + `routes/vat_excel_routes.py` | 加销项数据源 |
| 路由注册 | `app.py` include_router | 仿现有注册方式 |

每个**新代码文件配 ≥1 测试**(铁律)·销项金额/取号/不可变这类核心逻辑,仿 `test_*_safety_net.py` 加纯函数等价/边界测试。

## 数据库迁移(走 Alembic · 不是 scripts/sql)

- `migrations/0001_sales_core.sql`(草案)→ 转写为 **Alembic 版本** `alembic/versions/NNNN_sales_core.py`
  (见既有 `0001_knowledge_p1_tables.py` 等范式)· **禁新增 `ensure_*`**。
- 每张表 + `ENABLE ROW LEVEL SECURITY` + tenant policy(`tenant_id::text = current_setting('app.current_tenant_id', true)`)+ `(tenant_id,...)` 索引。
- **FK 类型先核实**:`\d clients` 看 `id` 真实类型(INTEGER/BIGSERIAL)· `client_id` 与之一致 · 别照搬草案 UUID。
- 热路径索引微调(非建表)可单独走 `scripts/sql/*.sql` 手动 psql(`CREATE INDEX CONCURRENTLY` 须 autocommit 逐条 · 见 b9)。

## 前端落点(`src/home/`)

| 沙盒产出 | 主仓库落点 |
|---|---|
| 销售发票页 | `src/home/page-sales-invoices.ts`(替占位)|
| 应收追踪页 | `src/home/page-receivables.ts`(替占位)|
| 选品/扫码组件 | `src/home/sales-*.ts`(单文件 <500,单一职责)|
| i18n key | 并入 `i18n-data`(th/zh/en)|

- **改源码必 `npm run build` + `git add static/dist`**(prod 不重建 dist)。
- **改前端必 bump `home.html ?v=`**(main.js/css 是 immutable 30d 缓存)。
- ⚠️ UI 落地前必须先过设计评审(死规则),`docs/06` 只是方案稿。

## 写代码前先过「4 问」(铁律 #28 · 见 `docs/10` §2)

领域=sales / 新建什么文件(确切路径) / 测试在哪(路径+用例名) / 删什么旧文件。答不全不许写。

## 高敏流程(开票=钱/合规 · 铁律 #16/#26)

取连号、开出不可改、生成税务凭证 = 关键路径 → **先报方案 + Zihao 在场 + 真账号 E2E 验**,
**不走无人值守自动合并**。每次部署写 4 语 release_notes(铁律 #6)。

## 守门处理(关键:别被整顿闸误伤 · 完整闸清单见 `docs/10` §1)

- 新功能文件是**净新增**,会被 size/ratchet 闸盯上。按 [[gates-hardened-post-refactor]] 的
  **RATCHET-EXEMPT 豁免法**登记新文件,避免 pre-push/CI 把正常新增判红。
- 单文件 **<500 行**硬门:大模块(如 PDF 生成)按职责拆多文件,别堆一个巨文件。
- 提交走 **Conventional Commits**,署名 `Co-Authored-By: Claude Opus 4.8`。
- `.github/workflows/` 若要加 CI step,需 `gh auth refresh -s workflow`(token 缺 workflow scope,见记忆)。

## 验收(迁回后)

- 真浏览器验 UI(isVisible + getComputedStyle + 截图),grep 类名不算数。
- 开票主路径(选客户→开出→取号→PDF→发送)属高敏(计费/合规),**先报方案再动**。
- ภ.พ.30 进销汇总数字与手工对账核对一致。
