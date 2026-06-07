# POS 项目 · 03 数据模型(字段级契约)

> 这是地基。库存/POS 的所有表、字段、类型、外键、关系在此钉死。施工(schema 迁移)直接照此写,不二次发明。
> 配套:接口契约见 04;字段"谁写谁读"见 04/05。

## 0. 设计原则(全表通用 · 违反=返工)

1. **外键类型对齐现有**(实扫结论):`tenant_id`=UUID · `products.id`=UUID · `sales_documents.id`=UUID · `workspace_clients.id`=BIGINT · `clients.id`=BIGINT。**新表遵循这套混合,不另起炉灶。**
2. **租户隔离**:每张业务表带 `tenant_id UUID NOT NULL`,纳入 RLS policy(本项目开 RLS,`core/db.py` 基础设施已就绪)。
3. **账套维度**:库存/POS 按 `workspace_client_id BIGINT`(哪家公司的货/收银)隔离 —— 一个事务所 tenant 下可代多公司,但 POS 商户=自己那家。
4. **钱用 `numeric(14,2)`**;**数量用 `numeric(14,3)`**(拆零/称重要小数);时间 `timestamptz`(UTC 存)、日期 `date`(效期/账期)。
5. **离线幂等**:可离线产生的写表(pos_sales / inventory_transactions)带 `client_uuid UUID UNIQUE`(端上生成),服务端按它去重,**重复补传不重复扣库存**。
6. **不可变流水**:库存变动只追加 `inventory_transactions`(immutable),当前库存是它的物化结果;改库存=记一笔冲销,不 UPDATE 历史。
7. **复用优先**:能用现有表/服务(products/totals/numbering/promptpay/sales_documents)不新建。

## 1. 复用的现有表(不改或仅加列)

| 表 | 用途 | 本项目动作 |
|---|---|---|
| `products`(UUID) | 商品主数据(已含 barcode/qr_payload/unit/unit_price/image_url/vat_applicable) | **加列**(见 §2) |
| `workspace_clients`(BIGINT) | 账套主体=卖方(已含 address/branch/vat/promptpay/品牌模板) | 不改(POS 取它当卖方) |
| `clients`(BIGINT) | 会员/记名客户 | 不改(POS 会员挂这) |
| `sales_documents`(UUID) | 正式税票 ใบกำกับภาษีเต็มรูป(连号/冻结快照/合规) | 不改(POS 升级税票时生成一条,引用 pos_sale) |
| `document_number_sequences` | 连号(FOR UPDATE 防跳号) | 复用(POS 小票号 + 简式税票号各一序列) |
| sales `payment_*` 字段 / `promptpay.py` | 收款 | 复用逻辑 |

## 2. 商品主数据扩展(products 加列 + 新表 product_units)

### products 新增列(都 `IF NOT EXISTS` · 默认值保证老数据不破)
| 列 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `base_unit` | text | 'ชิ้น'/件 | 最小计量单位(库存按它记) |
| `track_batch` | boolean | false | 是否管批号 |
| `track_expiry` | boolean | false | 是否管有效期(药/食品) |
| `is_weighed` | boolean | false | 称重品(数量为小数重量) |
| `min_stock` | numeric(14,3) | NULL | 低库存阈值(按 base_unit) |
| `default_cost` | numeric(14,2) | NULL | 参考成本(无批次时用) |

> 现有 `unit`/`unit_price` 保留(默认售价/默认单位);多单位在 product_units 展开。

### product_units(多单位/拆零换算)
| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` | uuid NOT NULL | RLS |
| `product_id` | uuid FK→products | |
| `unit_name` | text | 盒/板/粒、箱/瓶 |
| `factor_to_base` | numeric(14,3) | 1 此单位 = N 个 base_unit(粒=1、板=10、盒=100) |
| `barcode` | text | 该单位独立条码(箱码≠瓶码) |
| `price` | numeric(14,2) | 该单位售价(可空=按 factor 推) |
| `is_default_sell` | boolean | 默认售卖单位 |
| UNIQUE | (tenant_id, product_id, unit_name) | |

> 卖出/扣库存一律换算成 base_unit 落账;UI 让收银选"盒/板/粒"。能力块"多单位"关 → 只用 base_unit。

## 3. 库存域(全新 · services/inventory)

### warehouses(仓库/库位 · 初期每个账套一个默认仓)
| 列 | 类型 | 说明 |
|---|---|---|
| `id` | bigserial PK | (跟 workspace_clients 一样用 BIGINT) |
| `tenant_id` | uuid NOT NULL | |
| `workspace_client_id` | bigint FK→workspace_clients | 哪家公司的仓 |
| `name` | text | 默认"门店" |
| `is_default` | boolean | |
| `is_active` | boolean | |
| `created_at/updated_at` | timestamptz | |

### inventory_stock(当前库存 · 按 商品×仓×批次 · 物化结果)
| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` | uuid NOT NULL | |
| `workspace_client_id` | bigint | |
| `product_id` | uuid FK→products | |
| `warehouse_id` | bigint FK→warehouses | |
| `batch_id` | uuid FK→inventory_batches NULL | 无批次品为 NULL |
| `qty_on_hand` | numeric(14,3) | 在库(base_unit) |
| `qty_reserved` | numeric(14,3) | 预留(挂单/订单) |
| `updated_at` | timestamptz | |
| UNIQUE | (tenant_id, product_id, warehouse_id, batch_id) | 防重复行 |

### inventory_batches(批号 + 有效期 · track_batch/expiry 才用)
| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` | uuid NOT NULL | |
| `product_id` | uuid FK→products | |
| `batch_no` | text | 批号 |
| `expiry_date` | date NULL | 有效期(近效期预警/FEFO 排序键) |
| `received_at` | date | 入库日 |
| `unit_cost` | numeric(14,2) | 该批进货成本(批次级成本核算) |
| UNIQUE | (tenant_id, product_id, batch_no) | |

> **FEFO 先效先出**:卖出时按 `expiry_date ASC` 选批扣减。近效期预警 = `expiry_date <= today + N 天`。

### inventory_transactions(出入库流水 · immutable · 唯一真理)
| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` | uuid NOT NULL | |
| `workspace_client_id` | bigint | |
| `product_id` | uuid FK→products | |
| `warehouse_id` | bigint | |
| `batch_id` | uuid NULL | |
| `txn_type` | text | purchase_in / sale_out / return_in / adjust / count / transfer / damage |
| `qty_delta` | numeric(14,3) | 正=入 负=出(base_unit) |
| `unit_cost` | numeric(14,2) NULL | 出入库成本 |
| `ref_type` | text | pos_sale / purchase / count / manual |
| `ref_id` | uuid NULL | 关联单据(如 pos_sales.id) |
| `client_uuid` | uuid UNIQUE NULL | 离线幂等键 |
| `reason` | text NULL | 备注(报损/调整原因) |
| `created_by` | uuid | 操作人 |
| `created_at` | timestamptz | |

> 写库存=同一事务:写 transaction + upsert inventory_stock(原子)。`client_uuid` 重复=已处理,跳过(离线补传防双扣)。

## 4. POS 域(全新 · services/pos)

### 关键决策:POS 小票用独立表,不直接塞 sales_documents
**理由**:① POS 高频/离线/有班次终端上下文,生命周期跟正式税票不同 ② 泰国零售小票多为**简式税票 ใบกำกับภาษีอย่างย่อ**(自己连号+VAT),跟**全式 ใบกำกับภาษีเต็มรูป**(sales_documents)是两种 ③ 复用 totals/numbering/promptpay 逻辑即可,不必硬挤一张表。
**升级税票**:顾客要全式 → 由 pos_sale 生成一条 `sales_documents`(全式),`sales_documents.references_*` 或新列指回 pos_sale;**同一笔不得既出简式又重复计 VAT**(简式作废/标记被全式取代,合规规则见 16/03-thailand-tax)。

### pos_terminals(收银机/终端)
| 列 | 类型 | 说明 |
|---|---|---|
| `id` | bigserial PK | |
| `tenant_id` | uuid | |
| `workspace_client_id` | bigint | |
| `name` | text | 收银台 1 号 |
| `is_active` | boolean | |

### pos_cashiers(收银员 · PIN 登录 · auth · 按图+PO 施工,Zihao 已授权高敏免在场,仍跑真账号 E2E 闸)
| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` | uuid | |
| `workspace_client_id` | bigint | |
| `user_id` | uuid NULL FK→users | 关联正式账号(老板兼收银可关联自己) |
| `display_name` | text | Nok |
| `pin_hash` | text | PIN 加盐哈希(绝不存明文) |
| `is_active` | boolean | |

> 角色:用户体系加 `role='cashier'`(只能进 /pos);PIN 登录走 pos_cashiers。两者的关系/鉴权细节在 04-api-contracts §鉴权 + 08 离线 ADR(token 离线有效期)定。

### pos_shifts(班次/日结)
| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` / `workspace_client_id` | uuid / bigint | |
| `terminal_id` | bigint | |
| `cashier_id` | uuid FK→pos_cashiers | |
| `opened_at` / `closed_at` | timestamptz | |
| `opening_float` | numeric(14,2) | 备用金 |
| `expected_cash` | numeric(14,2) | 系统应有现金(备用金+现金销售-退款) |
| `counted_cash` | numeric(14,2) NULL | 实际点钞 |
| `cash_diff` | numeric(14,2) NULL | 差异 |
| `status` | text | open / closed |

### pos_sales(小票头 · 可离线产生)
| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` / `workspace_client_id` | uuid / bigint | |
| `client_uuid` | uuid UNIQUE | **离线幂等键(端上生成)** |
| `shift_id` | uuid FK→pos_shifts | |
| `terminal_id` / `cashier_id` | bigint / uuid | |
| `receipt_no` | text | 小票号(联网由 sequences 发;离线临时号→联网回填) |
| `doc_kind` | text | receipt / abbrev_tax_invoice(简式税票) |
| `sale_type` | text | sale / refund(退货为负) |
| `refund_of_sale_id` | uuid NULL | 退货指向原小票 |
| `member_client_id` | bigint NULL FK→clients | 会员(可空=散客) |
| `subtotal` / `discount_total` / `vat_amount` / `grand_total` | numeric(14,2) | 复用 totals.py 计算 |
| `price_includes_vat` | boolean | 价内/价外(复用销项) |
| `paid_total` / `change_amount` | numeric(14,2) | 实收 / 找零 |
| `full_invoice_id` | uuid NULL FK→sales_documents | 升级全式税票后指向 |
| `status` | text | completed / void / synced(离线态) |
| `sold_at` | timestamptz | 成交时间(离线=端上本地时间) |
| `synced_at` | timestamptz NULL | 服务端入库时间 |
| `created_by` | uuid | |

### pos_sale_lines(小票明细)
| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` | uuid | |
| `sale_id` | uuid FK→pos_sales | |
| `product_id` | uuid FK→products | |
| `sell_unit` | text | 售卖单位(盒/板/粒) |
| `unit_factor` | numeric(14,3) | 换算 base_unit 系数(冻结当时值) |
| `qty` | numeric(14,3) | 售卖单位数量 |
| `qty_base` | numeric(14,3) | = qty×factor(扣库存用) |
| `unit_price` | numeric(14,2) | 售卖单位单价 |
| `line_discount` | numeric(14,2) | 行折扣 |
| `vat_applicable` | boolean | |
| `batch_id` | uuid NULL | 批次品记扣的批 |
| `line_total` | numeric(14,2) | |

### pos_payments(一单可多种支付=混合付)
| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` | uuid | |
| `sale_id` | uuid FK→pos_sales | |
| `method` | text | cash / promptpay / card |
| `amount` | numeric(14,2) | |
| `ref` | text NULL | 扫码流水/卡号尾号 |

## 5. 模块开关(全新 · tenant_modules)

| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` | uuid NOT NULL | |
| `module_key` | text | inventory / pos / sales / expense / recon / knowledge |
| `enabled` | boolean | |
| `config` | jsonb | 业态预设 + 能力块开关(track_batch/multi_unit/tables/kitchen/weigh/member…) |
| UNIQUE | (tenant_id, module_key) | |

> 导航/路由/能力块按它显隐。业态预设 = 写一组 module_key + config。

## 6. 关系总览

```
tenants ─┬─ workspace_clients ─┬─ warehouses ─┬─ inventory_stock ── inventory_batches
         │  (账套=卖方,BIGINT)   │              └─ inventory_transactions
         │                       ├─ pos_terminals
         │                       ├─ pos_cashiers ── pos_shifts ── pos_sales ─┬─ pos_sale_lines ── products
         │                       └─ (会员) clients                            ├─ pos_payments
         ├─ products ── product_units                                        └─ full_invoice → sales_documents(全式税票)
         └─ tenant_modules
```

## 7. 外键类型对齐速查

| 引用 | 类型 |
|---|---|
| tenant_id | **uuid** |
| product_id / *_sale.id / sales_documents.id / batch_id / shift_id / cashier_id | **uuid** |
| workspace_client_id / warehouse_id / terminal_id / clients.id(会员) | **bigint** |

## 8. 迁移清单(Alembic · 续现有到 0020)

```
0021_tenant_modules          模块开关表
0022_product_units_and_flags products 加列 + product_units
0023_inventory_core          warehouses + inventory_stock + batches + transactions
0024_pos_core                terminals + cashiers + shifts
0025_pos_sales               pos_sales + lines + payments(+ full_invoice 关联)
```
> prod 经 ssh+psql 授权应用(现状无自动迁移);每张表配 `ensure_*` + `services/startup.py` 注册;每表 ≥1 测试;RLS policy 同步加。

## 9. 关键决策记录(防后人推翻)

1. **POS 小票=独立 pos_sales**,不塞 sales_documents;全式税票才落 sales_documents(升级时生成、互相引用)。简式/全式不得对同一笔重复计 VAT。
2. **批次 FEFO**:有效期升序选批扣减;批次成本独立。无批次品 batch_id=NULL 照常。
3. **拆零**:库存只认 base_unit;售卖单位经 product_units.factor 换算,行上冻结 factor。
4. **库存唯一真理=inventory_transactions(immutable)**;inventory_stock 是物化值,与流水同事务更新。
5. **离线幂等**:pos_sales/inventory_transactions 带 client_uuid UNIQUE,服务端去重,防补传双扣。
6. **收银员鉴权**=role=cashier + pos_cashiers.pin_hash。Zihao 2026-06-07 授权:POS 高敏块按图纸+PO 施工,**不卡"Zihao 在场"**;仍以真账号 E2E 为闸 + 改到共用现有登录流程时自验不破。
7. **库存/POS 按 workspace_client_id 隔离**(代记账多公司场景),全表纳 RLS。
