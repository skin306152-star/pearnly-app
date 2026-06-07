# POS 项目 · 04 接口契约(前后端唯一源)

> 前端、后端、E2E 全照这一份写。改接口先改这里。**字段名/嵌套层级/类型/错误码以本文件为准**——这是治"字段读错(body.data)、死按钮、假功能"的根。
> 数据来源见 03;按钮→哪个接口见 05;错误码全集见 06。

## 0. 全局约定(所有 POS/库存接口统一 · 违反=对接错位)

### 0.1 响应信封(只此一种 · 杜绝"读顶层还是读 data"的歧义)
**成功**:HTTP 200 +
```json
{ "ok": true, "data": { ... } }
```
**失败**:对应 HTTP(400/401/403/404/409/422/500)+
```json
{ "ok": false, "error": { "code": "pos.xxx", "message_key": "pos.xxx", "detail": "可选,调试用,不展示" } }
```
**前端铁律**:先看 `body.ok` → true 读 `body.data`,false 读 `body.error.code` 映射 06 的 4 语文案。**绝不靠 HTTP 状态码判业务成败**(200+ok:false 是有效失败)。

### 0.2 鉴权
- 前缀:POS 前台接口 `/api/pos/*`;库存/后台 `/api/inventory/*`、`/api/pos/admin/*`。
- 头:`Authorization: Bearer <token>`。收银员 token 由 PIN 登录签发(见 §1),带 `role=cashier` + `cashier_id` + `workspace_client_id`。
- 后端守门:写库存/小票校验 role ∈ {cashier,owner,super} + 模块 pos/inventory enabled + RLS 租户。
- ⚠️ 取鉴权图片/资源也要带 Bearer(销项踩过 401 坑,见 09 施工规约)。

### 0.3 幂等(离线必须)
- 可离线产生的写(建小票、库存流水)请求体带 `client_uuid`(端上 UUID)。
- 服务端按 `client_uuid` 去重:已存在 → 返回**原结果**(200,`data.deduped=true`),不重复落库/扣库存。

### 0.4 金额/数量/时间
- 金额字符串化小数 `"55.00"`(避免浮点);数量 `"2.000"`;后端按 Decimal 处理。
- 时间 ISO8601 UTC(`2026-06-07T07:32:00Z`);日期 `2026-12-31`。

### 0.5 分页
列表统一 `?limit=&cursor=`,返回 `data.items[]` + `data.next_cursor`(无更多=null)。

---

## 1. 收银员鉴权 / 前台引导

### POST /api/pos/auth/pin — PIN 登录
请求:`{ "workspace_client_id": 12, "cashier_id": "uuid", "pin": "1234" }`
成功:`data: { "token": "...", "cashier": {"id","display_name"}, "shift": null | {open shift}, "offline_ttl_hours": 12 }`
错误:`pos.pin_invalid`(401)· `pos.cashier_inactive`(403)

### GET /api/pos/cashiers?workspace_client_id= — 开班选人列表(店内可匿名拉,仅名字/头像)
`data: { "cashiers": [ {"id","display_name","color"} ] }`

### GET /api/pos/bootstrap — 前台启动包(登录后一次拉全,支撑离线)
`data: { "store": {...}, "modules": {...0.业态能力块...}, "products": [...见 §3...], "terminals": [...], "settings": {"allow_price_edit":false,"allow_discount":true,"near_expiry_days":30} }`

---

## 2. 模块 / 业态开关

### GET /api/me/modules — 当前租户开了哪些模块(主程序导航用)
`data: { "modules": { "pos": {"enabled":true,"config":{...}}, "inventory": {"enabled":true}, "sales": {...} } }`

### PUT /api/pos/admin/onboarding — 开通收银(选业态→批量开模块)
请求:`{ "business_type": "pharmacy", "warehouse_name": "门店", "first_cashier": {"display_name":"Nok","pin":"1234"} }`
成功:`data: { "enabled_modules": ["inventory","pos"], "capabilities": ["track_batch","multi_unit","prescription"], "cashier_id": "uuid" }`

### 设置页「业务/模块」管理(C3 · owner · docs/pos/02 §2.2)
- **GET /api/pos/admin/modules** — 全模块开关视图(含默认回落 + config)。
  `data: { "modules": { "pos":{"enabled":true,"config":{...}}, "inventory":{...}, "sales":{...}, ... } }`
- **PUT /api/pos/admin/modules** — 开/关单模块(**关=隐藏入口·不删数据**)。
  请求:`{ "module_key":"pos", "enabled":false, "config":{...可选} }`(config 省略=只翻开关不动 config)
  成功:`data: { "module": {"module_key","enabled","config"} }`;未知 module_key → `pos.line_invalid`(422)。
- **GET /api/pos/admin/onboarding-state?workspace_client_id=** — 该账套是否已开通 + 当前业态(屏8 判断避免重复开通)。
  `data: { "onboarded":true, "business_type":"pharmacy", "capabilities":["track_batch",...], "pos_enabled":true, "inventory_enabled":true, "has_warehouse":true, "cashier_count":2 }`
  > onboarded = pos 模块开 且 该账套已建仓 + ≥1 名在职收银员。
- **GET /api/pos/admin/business-presets** — 业态预设(业态 → 能力块清单)· 给开通向导渲染。
  `data: { "presets": { "pharmacy":["multi_unit","track_batch","track_expiry","prescription"], ... } }`

---

## 3. 商品(POS 选品 · 复用 products + units + 实时库存)

### GET /api/pos/products?workspace_client_id=&q=&category= — 选品列表
`data.items[]`:
```json
{ "id":"uuid","name":{"th":"โค้ก","zh":"可乐","en":"Coke"},"category_id":1,
  "base_unit":"瓶","image_url":null,"vat_applicable":true,
  "units":[{"unit_name":"瓶","factor":"1.000","barcode":"...","price":"15.00","default_sell":true},
           {"unit_name":"箱","factor":"24.000","barcode":"...","price":"340.00","default_sell":false}],
  "track_batch":false,"is_weighed":false,
  "stock":{"qty_base":"48.000","near_expiry":false} }
```
### GET /api/pos/products/by-barcode?code= — 扫码取单品(枪扫=键盘输入聚焦后回车)
`data: { ...同上单条..., "matched_unit":"箱" }`(条码命中的是哪个单位)
错误:`pos.product_not_found`(404)

---

## 4. 库存(/api/inventory/* · 后台 · owner/会计)

### GET /api/inventory/stock?workspace_client_id=&filter=low|out|all&q=
`data.items[]`:`{ "product_id","name","barcode","base_unit","qty_on_hand":"9.000","min_stock":"10.000","avg_cost":"18.00","status":"low|ok|out","batches":[{"batch_no","expiry_date","qty":"9.000"}] }`
`data.summary`:`{ "sku_count":128,"stock_value":"84260.00","low_count":7,"out_count":2 }`

### POST /api/inventory/in — 入库(进货)
请求:`{ "client_uuid","workspace_client_id","warehouse_id","lines":[{"product_id","unit_name","qty":"10","unit_cost":"18.00","batch_no":"L2406","expiry_date":"2027-06-01"}],"ref_type":"purchase","ref_id":null }`
成功:`data: { "txn_ids":[...],"updated_stock":[{"product_id","qty_on_hand"}] }`

### POST /api/inventory/count — 盘点(实际数→生成差异调整)
请求:`{ "workspace_client_id","warehouse_id","lines":[{"product_id","batch_id":null,"counted_qty":"7"}] }`
成功:`data: { "adjustments":[{"product_id","system_qty","counted_qty","delta"}] }`

### POST /api/inventory/adjust — 手动调整/报损
请求:`{ "client_uuid","workspace_client_id","warehouse_id","product_id","batch_id":null,"qty_delta":"-2","reason":"damage" }`

### GET /api/inventory/near-expiry?workspace_client_id=&days=30 — 近效期清单
`data.items[]`:`{ "product_id","name","batch_no","expiry_date","qty","days_left":12 }`

### GET /api/inventory/report?workspace_client_id=&from=&to=&near_expiry_days=30 — 库存报表(C1 · owner/会计)
进销存 + 周转 + 近效期看板聚合。默认期间=本月 1 号至今天。数据从 inventory_transactions 聚合(签名量 qty_delta)。
`data:`
```json
{ "period":{"from":"2026-06-01","to":"2026-06-07"},
  "movement":[ {"product_id","name":{"th","en","zh"},"base_unit":"粒",
    "opening":"100.000","in":"50.000","out":"30.000","sold":"28.000","closing":"120.000",
    "turnover_ratio":"0.25","days_on_hand":"28.0"} ],
  "near_expiry":{ "near_expiry_days":30,
    "buckets":[ {"label":"expired","batches":1,"qty":"5.000"},
                {"label":"le_7d","batches":2,"qty":"12.000"},
                {"label":"le_30d","batches":4,"qty":"30.000"} ],
    "value_at_risk":"840.00" } }
```
> 进销存:期初=期初前累计净额、期末=含 to 当天累计净额(半开窗口);周转率=售出量(txn sale_out)/平均库存。
> SQL 每分区独立聚合(防笛卡尔积);turnover_ratio/days_on_hand 平均库存为 0 时返 null。

---

## 5. 班次

### POST /api/pos/shifts/open
请求:`{ "workspace_client_id","terminal_id","opening_float":"500.00" }`(cashier 来自 token)
成功:`data: { "shift": {"id","opened_at","opening_float"} }`
错误:`pos.shift_already_open`(409)

### POST /api/pos/shifts/{id}/close — 交班日结
请求:`{ "counted_cash":"7730.00" }`
成功:`data: { "shift":{"id","closed_at","expected_cash":"7730.00","counted_cash","cash_diff":"0.00"},
  "summary":{"sales_count":86,"gross":"12480.00","by_method":{"cash":"7230.00","promptpay":"4650.00","card":"600.00"}} }`

---

## 6. 小票(核心 · /api/pos/sales)

### POST /api/pos/sales — 建小票(收款完成时调 · 可离线后补)
请求:
```json
{ "client_uuid":"端上uuid","workspace_client_id":12,"shift_id":"uuid","terminal_id":1,
  "doc_kind":"receipt","sale_type":"sale","member_client_id":null,
  "price_includes_vat":true,
  "lines":[ {"product_id":"uuid","sell_unit":"粒","qty":"100","unit_price":"1.00","line_discount":"0","batch_id":null} ],
  "header_discount":{"type":"none|pct|amount","value":"0"},
  "payments":[ {"method":"cash","amount":"100.00"} ],
  "sold_at":"2026-06-07T07:32:00Z" }
```
成功:`data:`
```json
{ "sale":{"id":"uuid","receipt_no":"RCP-2026-00123","grand_total":"55.00","vat_amount":"3.60",
          "paid_total":"100.00","change_amount":"45.00","status":"completed"},
  "stock_applied":true, "deduped":false }
```
错误:`pos.out_of_stock`(409,`error.detail` 带哪个品)· `pos.shift_closed`(409)· `pos.line_invalid`(422)
> 服务端一个事务:发号(连号)→ 算总额(totals.py·价内外)→ 按 FEFO 扣批次库存(写 inventory_transactions)→ 落 pos_sales/lines/payments。`client_uuid` 命中=返原结果 deduped=true。

### POST /api/pos/sales/sync — 离线批量补传
请求:`{ "sales":[ {…单张 POST 的请求体…}, … ] }`
成功:`data: { "results":[ {"client_uuid","ok":true,"sale_id","receipt_no","deduped":false} | {"client_uuid","ok":false,"error":{...}} ] }`
> 逐张幂等处理;部分失败不影响其余;失败项端上保留重试。

### GET /api/pos/sales/{id} — 小票详情(打印/退货取原单)
`data: { "sale":{…header…},"lines":[…],"payments":[…] }`

### GET /api/pos/sales/by-receipt?no=RCP-2026-00123 — 扫小票号取单(退货用)

### POST /api/pos/sales/{id}/refund — 退货
请求:`{ "client_uuid","lines":[{"sale_line_id","qty":"1"}],"refund_method":"cash" }`
成功:`data: { "refund_sale":{"id","receipt_no":"RFD-...","grand_total":"-15.00"},"stock_returned":true }`
> 生成一张 sale_type=refund 的负额小票;按行回补库存(原批次);写红冲。

### POST /api/pos/sales/{id}/void — 作废(未交班当班错单)
错误:`pos.void_not_allowed`(409,已交班/已退货)

### GET /api/pos/sales/{id}/promptpay-qr — 收款二维码(复用 promptpay.py)
`data: { "qr_payload":"00020101...","png_base64":"..." ,"amount":"55.00" }`

### GET /api/pos/sales/{id}/receipt-pdf — 热敏小票 PDF(复用 pdf_thermal.py · 58/80mm)

### POST /api/pos/sales/{id}/full-tax-invoice — 小票升级正式税票
请求:`{ "buyer":{"party_type":"company|individual","name","tax_id","branch_type":"head|branch","branch_no","address"} }`
成功:`data: { "document":{"id","doc_number","doc_type":"tax_invoice"} }`(落 sales_documents·复用销项合规连号/冻结/不可改)
> 同一笔不重复计 VAT:简式小票标记被全式取代(`pos_sales.full_invoice_id` 回填);合规规则见 03 §9 + 销项 docs/16。
错误:`pos.tax_id_invalid`(422)· `pos.already_upgraded`(409)

---

## 7. 销售报表(/api/pos/admin/report)

### GET /api/pos/admin/report?workspace_client_id=&from=&to=
`data:`
```json
{ "kpi":{"gross":"86420.00","sales_count":612,"avg_ticket":"141.00","refund":"1240.00"},
  "by_day":[{"date":"2026-06-01","gross":"11200.00"}],
  "by_method":{"cash":"49800.00","promptpay":"32100.00","card":"4520.00"},
  "top_products":[{"product_id","name","qty":"412","gross":"6180.00"}],
  "by_cashier":[{"cashier_id","name","sales_count":238,"gross":"34200.00"}] }
```

---

## 8. 错误码(全集 + 4 语文案见 06)
本文件出现的:`pos.pin_invalid · pos.cashier_inactive · pos.product_not_found · pos.out_of_stock · pos.shift_already_open · pos.shift_closed · pos.line_invalid · pos.void_not_allowed · pos.tax_id_invalid · pos.already_upgraded · pos.module_disabled · pos.forbidden`。06 给每个配 th/en/zh/ja + 用户可读文案(绝不裸露 code)。

## 9. 契约测试要求(每个端点 ≥1)
- 信封一致性:成功 `ok:true+data`、失败 `ok:false+error.code`。
- 幂等:同 `client_uuid` 二次 POST 不双扣(`deduped:true`)。
- 鉴权:无/错 token 401;非 cashier 调写 403;模块关 `pos.module_disabled`。
- 库存:扣减走 FEFO + 不足 `pos.out_of_stock`;退货回补原批。
- RLS:A 租户拿不到 B 的小票/库存。
