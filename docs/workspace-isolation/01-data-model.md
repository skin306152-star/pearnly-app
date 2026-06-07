# 套账隔离 · 01 数据模型与改造面

> 前后端唯一源。每张运营表的归属、现状、目标、改造工作量。

## 隔离列命名(全项目统一)

- 隔离列名:`workspace_client_id`(BIGINT,外键逻辑指向 `workspace_clients.id`)。**不新造 `workspace_id`。**
- 复合索引统一前缀:`(tenant_id, workspace_client_id, ...)`。
- `tenant_id` 保留(归属/计费/越级校验仍需);套账是 tenant **之下**的更细边界,不替代它。每句运营查询同时带 `tenant_id AND workspace_client_id`(双重保险:套账归属必属本租户)。

## 表清单:现状 → 目标

图例:✅ 已隔离 · ❌ 缺列+缺过滤 · ⚠️ 有列但读不滤

### 已对(✅ · 施工时仅复核,不动)

| 表 | 现隔离列 | 备注 |
|---|---|---|
| `inventory_stock` | tenant + workspace_client_id | |
| `inventory_transactions` | tenant + workspace_client_id | |
| `warehouses` | tenant + workspace_client_id | |
| `pos_terminals` / `pos_cashiers` / `pos_shifts` | tenant + workspace_client_id | |
| `pos_sales` | tenant + workspace_client_id | lines/payments 经 FK 派生(见下"派生表") |
| 餐厅 POS 5 表(区/桌/session/order_line/kot) | 推定 tenant + workspace_client_id | **施工时复核**:与 0024/0025 同波建,需确认列齐全 |
| `workspace_clients` | 套账主体表本身 | id 即 workspace_client_id |
| `seller_profile`(开票资料) | tenant + workspace_client_id | |

### 缺隔离(❌ / ⚠️ · 本项目要改)

| 模块 | 表 | 现隔离 | 目标 | 改造动作 |
|---|---|---|---|---|
| 商品 | `products` | tenant | tenant + ws | 加列+回填+读写过滤 |
| 商品 | `product_units` | tenant | tenant + ws(或经 product FK 派生) | 同上 / 派生 |
| 进项 | `ocr_history` | tenant + 买方client | + ws **读过滤** | 列已有、写已对,**仅加读侧过滤** |
| 库存 | `inventory_batches` | tenant | tenant + ws | 加列+回填(批次主数据归主体) |
| 销项 | `sales_documents` | tenant(ws列只存不滤) | tenant + ws 过滤 | 启用 `seller_workspace_client_id` 做过滤键 |
| 销项 | `sales_document_lines` | tenant | 经 document FK 派生 | 读随头表;复核直查点 |
| 销项 | `document_number_sequences` | tenant | **tenant + ws**(连号按主体·合规) | 见 03 · 高敏 |
| 销项 | `etax_submissions` / `etax_channel_settings` | tenant | tenant + ws | 电子税票按主体 |
| 对账 | `bank_reconcile_sessions` | user_id(+可选client_id) | tenant + ws | 面大·涉钱 |
| 对账 | `bank_reconcile_transactions` | user_id(经session) | 经 session FK 派生 | 读随 session |
| 对账 | `recon_jobs` | user_id + tenant | tenant + ws | |
| 对账 | `vat_recon_tasks` | tenant + user | tenant + ws | |
| 对账 | `bank_recon_v2_task` | tenant | tenant + ws | |

## "派生表"原则(避免列冗余)

明细/子表(`sales_document_lines`、`pos_sale_lines`、`pos_payments`、`bank_reconcile_transactions`)**不必各加 workspace_client_id 列**——它们经 FK 锁定到已隔离的头表(document / sale / session)。规则:

1. 子表查询**必须**与头表 JOIN 或先查头表拿到归属,**不允许**脱离头表直查子表(否则绕过隔离)。
2. 施工时逐子表复核:有没有"只按 tenant + 子表自身条件"直查、不挂头表的点 → 这种是漏洞,改成挂头表。
3. 性能权衡:JOIN 比冗余列稍慢,但少一份回填、少一处漂移风险。对账子表量大,若 EXPLAIN 退化再考虑冗余列(届时 ADR 记录)。

## 改造面量化(query 站点数 · 工作量真实依据)

非测试/迁移的生产查询站点(grep `FROM/UPDATE/INTO <表>`,2026-06-07):

| 模块 | 主要落点 | 量级 | 风险 |
|---|---|---|---|
| 商品 | sales/products.py(8)· pos/catalog.py(5)· products/units.py(3)· inventory/pos 若干 | ~25 | 低 |
| 进项识别 | ocr_history/queries.py(10)· mutations.py(10) | ~20(读侧为主) | 中 |
| 销项 | sales/document.py(15)· credit_note(3)· share(3)· quotation(2)· approval(2)· archive(1) | ~30 | **高(连号/税票/合规)** |
| 对账 | bank_recon_v1_store(20)· bank_recon_v2_store(26)· vat_recon_tasks_store(26)· recon_jobs/store(23)· bank_recon_match(7)· handlers/worker 等 | **~130+** | **最高(面最大·涉钱·最缠)** |

→ 排序印证 04 的施工顺序:商品(练手)→ 进项(读侧改动小)→ 库存批次 → **对账(最大块,单独多 PO)** → **销项(最敏感,压最后)**。

## 商品共享 = 例外,显式化

默认商品归套账。连锁/加盟想跨套账共享:

- **不**回到租户层堆商品。
- 提供"从模板/另一套账复制商品"动作(后续功能,本项目只留接口余量,不实现)。
- 即:共享是一次性 copy,不是 live 共享同一行。

## 术语表(代码 ↔ 文案)

| 代码 | 文案(中) | 文案(泰/英) | 说明 |
|---|---|---|---|
| `workspace_client_id` / `workspace_clients` | 套账 / 账套主体 | กิจการ / Entity(Organisation) | 隔离硬边界。表名暂不改 |
| `client_id` / `clients` | 买方 / 客户 / 对方 | ลูกค้า / Customer | 套账内部维度 |
| `tenant_id` | 账号 / 租户 | บัญชีผู้ใช้ / Account | 计费+授权层 |
