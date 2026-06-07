# 餐厅 POS · 01 数据模型(字段级契约)

> 从定稿 UI(桌面 `Pearnly_餐厅POS_UI预览/` 4 屏)反推。餐厅是 POS 第二业态,后端全新独立,
> 不碰现有零售 POS 表/服务。复用:`products`(菜品=成品)、`pos_sales/lines/payments`(埋单落账)、
> `pos_shifts/terminals/cashiers`(班次/收银员)、`document_number_sequences`(连号)、
> `services/sales/totals.py`(算价)、`promptpay/pdf_thermal`(收款/小票)。
>
> 配套:接口契约见 02;PO 计划见 03。上位通用约定沿用 `docs/pos/03-data-model.md`(外键类型/钱量/隔离/RLS)。

## 0. 设计原则(承接 docs/pos/03 §0,餐厅特有补充)

1. **外键类型对齐现有混合**:`tenant_id`=uuid · `products.id`=uuid · `pos_sales.id`=uuid ·
   `workspace_clients.id`=bigint · 桌台/区域用 `bigserial`(与 terminals/warehouses 一致)。
2. **隔离**:每表 `tenant_id uuid NOT NULL` + `workspace_client_id bigint`(账套=门店),
   每条 SQL `WHERE tenant_id`(+ ws),应用层硬隔离;表纳 RLS policy(BYPASSRLS 下仅兜底,
   见 [[pos-rls-bypass-app-layer-isolation]])。
3. **钱 `numeric(14,2)`、量 `numeric(14,3)`、时间 `timestamptz`(UTC)**。绝不 float。
4. **状态机不存冗余派生态**:桌台显示状态(空闲/就餐/制作/待结)从 session + KOT 实时派生,
   只存权威态 `session.status ∈ {open, billing, closed}` 与逐项 `session_line.kitchen_status`,
   避免денорм 漂移(同零售不另存"当前库存=流水"以外的副本)。
5. **库存原料扣减(BOM)先不做**:菜品当成品,埋单**不扣库存**、不写 `inventory_transactions`。
   将来上 BOM 时在 checkout 追加扣减,不影响本期表结构。
6. **餐厅特性**:开桌 → 多次点单加菜(append)→ 后厨 KOT 逐项制作 → 埋单(整桌/分单/AA + 服务费)。
   埋单时 session 行**结成一张 `pos_sales`**(可分单 → 一个 session 多张),统一进零售同一张报表。

## 1. 复用的现有表(不改)

| 表 | 餐厅用途 |
|---|---|
| `products`(uuid) | 菜品主数据(name_th/en/zh · category_id · unit_price · vat_applicable · base_unit)。菜单=按 category 取 products,复用 `/api/pos/products`。 |
| `pos_sales / pos_sale_lines / pos_payments` | 埋单落账(连号小票/收款/升级税票/进报表)。**仅加列** `service_charge`(见 §7)。 |
| `pos_shifts / pos_terminals / pos_cashiers` | 班次/终端/收银员(餐厅收银也开班)。 |
| `document_number_sequences` | 小票连号(`numbering.next_number`,终端分段)。 |

## 2. pos_areas(就餐区域 · 大厅 A / 包间 / 露台)

| 列 | 类型 | 说明 |
|---|---|---|
| `id` | bigserial PK | |
| `tenant_id` | uuid NOT NULL | |
| `workspace_client_id` | bigint NOT NULL | 哪家门店 |
| `name` | text NOT NULL | 区域名(大厅 A) |
| `sort` | int NOT NULL DEFAULT 0 | 总览排序 |
| `is_active` | boolean NOT NULL DEFAULT TRUE | 关=隐藏不删 |
| `created_at/updated_at` | timestamptz | |

> UNIQUE `(tenant_id, workspace_client_id, name) WHERE is_active`。总览顶部"全部 + 各区"过滤即按此。

## 3. pos_tables(桌台 · A1/A2/露1)

| 列 | 类型 | 说明 |
|---|---|---|
| `id` | bigserial PK | |
| `tenant_id` | uuid NOT NULL | |
| `workspace_client_id` | bigint NOT NULL | |
| `area_id` | bigint REFERENCES pos_areas ON DELETE SET NULL | 无区为 NULL |
| `name` | text NOT NULL | 桌号(A1) |
| `seats` | int NOT NULL DEFAULT 4 | 标准容量(开台默认 party_size 回退) |
| `sort` | int NOT NULL DEFAULT 0 | |
| `is_active` | boolean NOT NULL DEFAULT TRUE | |
| `created_at/updated_at` | timestamptz | |

> UNIQUE `(tenant_id, workspace_client_id, name)`。**桌台不存状态**——状态由 open session + KOT 派生(§6)。

## 4. pos_table_sessions(开台挂账 · 一桌一次用餐周期)

| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` | uuid NOT NULL | |
| `workspace_client_id` | bigint NOT NULL | |
| `table_id` | bigint NOT NULL REFERENCES pos_tables ON DELETE RESTRICT | |
| `service_type` | text NOT NULL DEFAULT 'dine_in' | dine_in / takeaway / delivery(总览顶部段) |
| `party_size` | int NOT NULL DEFAULT 1 | 几位 |
| `status` | text NOT NULL DEFAULT 'open' | **open**(就餐)/ **billing**(已请结)/ **closed**(已结清) |
| `opened_at` | timestamptz NOT NULL DEFAULT now() | 用餐计时起点(总览"N 分钟") |
| `closed_at` | timestamptz | |
| `cashier_id` | uuid REFERENCES pos_cashiers ON DELETE SET NULL | 开台收银员 |
| `note` | text | 整桌备注 |
| `created_by` | uuid | |
| `created_at` | timestamptz NOT NULL DEFAULT now() | |

> **一桌至多一活动 session**:`CREATE UNIQUE INDEX uq_table_open ON pos_table_sessions (tenant_id, table_id) WHERE status <> 'closed'`。
> 开台 = 插一行 open;请结 = open→billing;结清 = →closed(`closed_at`)。一个 session 可拆多张
> `pos_sales`(按项分单),故 sale 关联落在**行级**(§5 `settled_sale_id`),session 不存单一 sale_id。

## 5. pos_session_lines(本桌累积点单行 · 多次点单 append · 兼作 KOT 明细)

| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` | uuid NOT NULL | |
| `session_id` | uuid NOT NULL REFERENCES pos_table_sessions ON DELETE CASCADE | |
| `kot_id` | uuid REFERENCES pos_kot ON DELETE SET NULL | **NULL=待下单(草稿)**;送厨房后指向所属 KOT |
| `product_id` | uuid NOT NULL REFERENCES products ON DELETE RESTRICT | 菜品 |
| `sell_unit` | text | 售卖单位(默认 base_unit) |
| `unit_factor` | numeric(14,3) NOT NULL DEFAULT 1 | 冻结换算(成品多为 1) |
| `qty` | numeric(14,3) NOT NULL | 份数 |
| `unit_price` | numeric(14,2) NOT NULL | 下单时冻结单价(快照,菜单调价不影响在台单) |
| `line_discount` | numeric(14,2) NOT NULL DEFAULT 0 | 行折扣 |
| `vat_applicable` | boolean NOT NULL DEFAULT TRUE | |
| `note` | text | 去冰/少辣/加辣/不要香菜(进 KOT 给后厨) |
| `kitchen_status` | text NOT NULL DEFAULT 'pending' | **pending**(待制作)/ **cooking**(制作中)/ **done**(完成)/ **void**(退菜)。仅 kot_id 非空时有意义 |
| `settled_sale_id` | uuid REFERENCES pos_sales ON DELETE SET NULL | 已结进哪张小票(NULL=未结)。分单据此 |
| `created_by` | uuid | |
| `created_at` | timestamptz NOT NULL DEFAULT now() | append 顺序 |

> **草稿 vs 已下单**:`kot_id IS NULL` = 右栏可加减/删的待下单行;送厨房后 `kot_id` 落定即锁(不可改量,
> 要改走退菜/重下)。**未结 vs 已结**:`settled_sale_id IS NULL` = 仍挂在桌上待结;分单只结选中行,
> 其余留台。索引:`(tenant_id, session_id)`、`(tenant_id, kot_id)`。

## 6. pos_kot(厨房单头 · 一次"送厨房"= 一张 KOT)

| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` | uuid NOT NULL | |
| `workspace_client_id` | bigint NOT NULL | |
| `session_id` | uuid NOT NULL REFERENCES pos_table_sessions ON DELETE CASCADE | 反查桌号 |
| `ticket_no` | int NOT NULL | 当班/当日顺序号(后厨叫号,按 ws 当日递增) |
| `sent_at` | timestamptz NOT NULL DEFAULT now() | 出单时间(后厨计时/超时起点) |
| `started_at` | timestamptz | 首次"开始制作" |
| `done_at` | timestamptz | "全部完成" |
| `created_by` | uuid | |
| `created_at` | timestamptz | |

> KOT 不存 status 列——**整单态由其行 `kitchen_status` 派生**(防漂移):
> 全 void→void;非 void 全 done→done;有 cooking→cooking;否则 new。`started_at/done_at` 仅审计/计时。
> 索引:`(tenant_id, workspace_client_id, session_id)`。

### 桌台总览状态派生(单一真理 = session.status + 行 kitchen_status)

| 显示态(UI 色) | 派生条件 |
|---|---|
| `free` 空闲(绿) | 该桌无 `status <> 'closed'` 的 session |
| `bill` 待结账(红) | session.status = `billing` |
| `cook` 制作中(黄) | session.status = `open` 且存在 `kot_id IS NOT NULL AND kitchen_status IN ('pending','cooking')` 的行 |
| `seat` 就餐中(蓝) | session.status = `open` 且无在制行(全 done 或仅草稿) |

> 总览每桌还需:`party_size`(位)、`amt`(已下单未结行的 line_total 合计 · 含税口径见 §7)、
> `min`(now − opened_at 分钟)。每态独立子查询/聚合,**绝不 lines × payments 同句**(防笛卡尔积,见
> [[pos-pob4-b5-b6-shipped]])。

## 7. pos_sales 加列:service_charge(服务费)

埋单 UI:`小计 440 + 服务费 10% 44 = 应收 484`,`含 VAT 7% 31.66`(价内反算 484×7/107)。
服务费是餐厅特有的整单加收项,落进统一小票需一列记录:

| 列 | 类型 | 说明 |
|---|---|---|
| `service_charge` | numeric(14,2) NOT NULL DEFAULT 0 | 服务费金额(零售恒 0,不破坏) |

> **加法迁移**`ALTER TABLE pos_sales ADD COLUMN IF NOT EXISTS service_charge ...`(0027 + 餐厅 ensure 双跑),
> 零售默认 0 不受影响。算价:`grand_total` 已含服务费;`vat_amount` 在(菜品净额+服务费)上一次算(单次取整,
> 对齐 UI 31.66)。报表(B6)读 `grand_total` 故天然正确;`service_charge` 仅供小票/账单分行展示。
> 不改 `pos_sales` 其余列、不改 `sales_store._SALE_COLS`(服务费经 checkout 自有 UPDATE 写,详见 02 §埋单)。

## 8. 关系总览

```
workspace_clients(门店, bigint)
 ├─ pos_areas ── pos_tables ── pos_table_sessions ─┬─ pos_session_lines ── products(菜品)
 │                                                  │        └ settled_sale_id → pos_sales(埋单, 复用)
 │                                                  └─ pos_kot(厨房单, 行 kitchen_status 逐项)
 └─ pos_cashiers ── pos_shifts (埋单挂 shift_id, 复用)
```

## 9. 迁移清单(Alembic · 续 0026)

```
0027_restaurant_core   pos_areas + pos_tables + pos_table_sessions + pos_session_lines + pos_kot
                       + ALTER pos_sales ADD service_charge  (+ RLS policy 5 表)
```

> prod 经 ssh+psql 授权应用;配 `services/pos/restaurant/schema.ensure_restaurant_schema()` 双跑
> + 进 `services/pos_schema.bootstrap_pos_schema()` + `startup`。每表 ≥1 测试,RLS 同步。

## 10. 关键决策(防后人推翻)

1. **桌台/KOT 不存派生状态**;总览态实时从 session.status + 行 kitchen_status 算,单一真理零漂移。
2. **一 session 多 sale**:分单/AA 在行级 `settled_sale_id` 记账,session 不持单一 sale_id;
   全行已结 → session closed → 桌台转空闲。
3. **菜品=成品,埋单不扣库存**(BOM 后做);故餐厅 checkout 不走零售 `sale.create_sale`(那条扣库存),
   另起 `restaurant/checkout.py`复用 totals/numbering/收款/税票,但跳过 FEFO。
4. **服务费**=`pos_sales.service_charge` 加列(零售 0),VAT 在(菜品+服务费)上单次取整,统一进报表。
5. **错误码**:本期后端**复用既有 `pos.*` 码 + `error.detail`**(桌占用/无可结行等),不新增 i18n 键
   (避让别窗口 i18n WIP);专用码(`pos.table_occupied` 等)留前端窗口接屏时补(见 02 §错误码)。
