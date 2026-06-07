# 餐厅 POS · 02 接口契约(前后端唯一源)

> 全照 `docs/pos/04 §0` 信封:成功 `{ok:true,data:{...}}`,失败 `{ok:false,error:{code,message_key,detail?}}`。
> 前缀 `/api/pos/restaurant/*`(前台/后厨)、`/api/pos/admin/restaurant/*`(桌台/区域管理)。鉴权用 `pos_auth`:
> 收银员 token 自带 `workspace_client_id`,老板调需带 `workspace_client_id`。写端单事务(`get_cursor_rls commit=True`)。
> 数据模型见 01;错误码见末节。

## 0. 约定

- 钱 `"55.00"`、量 `"2.000"` 字符串化小数;时间 ISO8601 UTC。
- 写接口均先 `assert_module_enabled(cur, tid, "pos")` + `require_workspace`。
- **桌台/区域管理 = `require_owner`**(收银员不可改桌位布局);前台/后厨 = `require_tenant`(收银员可调)。

---

## 1. 桌台/区域管理(`/api/pos/admin/restaurant/*` · owner)

### GET /api/pos/admin/restaurant/areas?workspace_client_id=
`data: { "areas": [ {"id":1,"name":"大厅 A","sort":0,"is_active":true,"table_count":8} ] }`

### POST /api/pos/admin/restaurant/areas
请求 `{ "workspace_client_id":12, "name":"包间", "sort":1 }` → `data: { "area": {...} }`

### PATCH /api/pos/admin/restaurant/areas/{area_id}
请求 `{ "workspace_client_id":12, "name?":..., "sort?":..., "is_active?":false }`(关=隐藏不删)→ `data:{ "area":{...} }`

### GET /api/pos/admin/restaurant/tables?workspace_client_id=&area_id=
`data: { "tables": [ {"id":3,"name":"A2","area_id":1,"area_name":"大厅 A","seats":4,"sort":0,"is_active":true} ] }`

### POST /api/pos/admin/restaurant/tables
请求 `{ "workspace_client_id":12, "name":"A9", "area_id":1, "seats":4, "sort":8 }` → `data:{ "table":{...} }`
> 桌号重复 → `pos.line_invalid`(detail=`duplicate_table`)。

### PATCH /api/pos/admin/restaurant/tables/{table_id}
请求 `{ "workspace_client_id":12, "name?":..., "area_id?":..., "seats?":..., "sort?":..., "is_active?":false }`
> 桌上有未结 session 时停用 → `pos.void_not_allowed`(detail=`table_busy`)。

---

## 2. 桌台总览(屏 01 · `require_tenant`)

### GET /api/pos/restaurant/tables?workspace_client_id=&area_id=&service_type=dine_in
`data:`
```json
{ "areas":[ {"id":1,"name":"大厅 A"} ],
  "tables":[
    { "id":3,"name":"A2","area_id":1,"seats":4,
      "status":"seat",                // free | seat | cook | bill(01 §6 派生)
      "session_id":"uuid|null",
      "party_size":4,"amount":"680.00","minutes":25 } ] }
```
> `amount` = 该 session 已下单未结行(`kot_id IS NOT NULL AND settled_sale_id IS NULL AND kitchen_status<>'void'`)
> 的 line_total 合计(含税口径)。`minutes` = now − opened_at。空桌 `session_id=null,status="free"`。

---

## 3. 开台 / session(屏 01→02 · `require_tenant`)

### POST /api/pos/restaurant/tables/{table_id}/open — 开台
请求 `{ "workspace_client_id":12, "party_size":4, "service_type":"dine_in" }`(cashier 取自 token)
成功 `data: { "session": {"id","table_id","table_name":"A2","party_size":4,"status":"open","opened_at"} }`
错误:桌已占用 → `pos.line_invalid`(409? 用 422·detail=`table_occupied`);桌停用/不存在 → `pos.product_not_found`(404)。

### GET /api/pos/restaurant/sessions/{session_id} — 本桌当前单(屏 02 右栏 + 屏 04 账单)
`data:`
```json
{ "session":{"id","table_id","table_name":"A2","party_size":4,"status":"open","opened_at","minutes":25},
  "draft_lines":[  {"id","product_id","name":{"th","en","zh"},"sell_unit","qty":"2.000",
                    "unit_price":"15.00","line_discount":"0.00","note":null,"line_total":"30.00"} ],
  "sent_lines":[   {"id",...,"kot_id","ticket_no":3,"kitchen_status":"cooking","settled_sale_id":null} ],
  "totals":{ "ordered_subtotal":"320.00","draft_subtotal":"120.00","unsettled_subtotal":"440.00" } }
```
> `draft_lines`(kot_id NULL · 可加减删)与 `sent_lines`(已下单锁定)分开。屏 02 顶部"3 道已下单 · 2 道待下单"
> = 各自计数;`ordered_subtotal/draft_subtotal` 对应 UI"已下单小计/本次新增"。

### POST /api/pos/restaurant/sessions/{session_id}/lines — 加菜(append 草稿)
请求 `{ "workspace_client_id":12, "lines":[ {"product_id":"uuid","qty":"1","sell_unit":null,"note":"加辣"} ] }`
> `unit_price/vat_applicable/unit_factor/sell_unit` 服务端按 product 快照(不信前端价)。同品同 note 合并加量(可选)。
成功 `data: { "draft_lines":[...更新后的草稿全集...] }`。session 非 open/billing → `pos.void_not_allowed`(409)。

### PATCH /api/pos/restaurant/sessions/{session_id}/lines/{line_id} — 改草稿(量/备注)
请求 `{ "workspace_client_id":12, "qty?":"3", "note?":"去冰" }`。**仅草稿(kot_id NULL)可改**;
已下单行改 → `pos.line_invalid`(detail=`line_locked`)。`qty<=0` 视为删。

### DELETE /api/pos/restaurant/sessions/{session_id}/lines/{line_id} — 删草稿
仅草稿可删 → `data:{ "draft_lines":[...] }`;已下单 → `pos.line_invalid`(detail=`line_locked`)。

### POST /api/pos/restaurant/sessions/{session_id}/cancel — 取消空台(开错台)
仅当**无任何已下单行**(全是草稿/空)时可取消 → 删草稿 + session closed,桌转空闲。
有已下单行 → `pos.void_not_allowed`(detail=`session_has_orders`)。

---

## 4. 送厨房 / KOT(屏 02→03 · `require_tenant`)

### POST /api/pos/restaurant/sessions/{session_id}/send-kitchen — 送厨房(草稿 → KOT)
请求 `{ "workspace_client_id":12 }`(默认送本桌全部草稿;可选 `line_ids:[...]` 只送部分)
> 一个事务:取草稿行 → 发 `ticket_no`(ws 当日递增)→ 建 `pos_kot` → 草稿行 `kot_id=新KOT, kitchen_status='pending'`。
成功 `data: { "kot": {"id","ticket_no":4,"sent_at","items":[ {"line_id","name","qty","note","kitchen_status":"pending"} ]} }`
无草稿可送 → `pos.line_invalid`(detail=`no_draft_lines`)。

### GET /api/pos/restaurant/kitchen?workspace_client_id=&late_minutes=15 — 后厨板(屏 03)
`data:`
```json
{ "stat":{"pending":2,"cooking":3,"late":1},
  "tickets":[
    { "id","ticket_no":3,"table_name":"A5","sent_at","minutes":14,"late":true,
      "status":"cooking",                        // new|cooking|done|void(01 §6 派生)
      "items":[ {"line_id","name":{"th","en","zh"},"qty":"2.000","note":"不要香菜","kitchen_status":"cooking"} ] } ] }
```
> 只列**未完成**KOT(派生 status ≠ done/void)。`late = minutes >= late_minutes`(默认 15)。每 KOT 一独立查询取 items。

### POST /api/pos/restaurant/kot/{kot_id}/status — 整单流转(屏 03 按钮)
请求 `{ "workspace_client_id":12, "status":"cooking" }`(cooking=开始制作 → 把该单 pending 行置 cooking + `started_at`;
done=全部完成 → 把 pending/cooking 行置 done + `done_at`)。`status ∈ {cooking,done}`,其它 → `pos.line_invalid`。
成功 `data:{ "kot":{"id","status","items":[...]} }`。KOT 不存在 → `pos.product_not_found`(404)。

### POST /api/pos/restaurant/kot/items/{line_id}/status — 逐项流转(单菜先出/退菜)
请求 `{ "workspace_client_id":12, "status":"done" }`(`status ∈ {cooking,done,void}`)。
> 满足"逐项状态机"。整单按钮是逐项的批量糖衣。

---

## 5. 埋单结账(屏 04 · `require_tenant`)

### POST /api/pos/restaurant/sessions/{session_id}/request-bill — 请结(open→billing)
请求 `{ "workspace_client_id":12 }` → `data:{ "session":{"id","status":"billing"} }`(桌台转"待结账"红)。幂等。

### GET /api/pos/restaurant/sessions/{session_id}/bill?mode=whole|by_item|aa&line_ids=&ways= — 账单预览(算价不落库)
`data:`
```json
{ "mode":"whole","lines":[ {"line_id","name","qty","unit_price","line_total"} ],
  "subtotal":"440.00","service_charge":"44.00","service_rate":"10",
  "vat_amount":"31.66","price_includes_vat":true,"grand_total":"484.00",
  "split":{"ways":4,"per_share":"121.00"} }   // mode=aa 才有
```
> 预览复用 checkout 同一算价(02 §埋单算价),只读不写。`by_item` 传 `line_ids`;`aa` 传 `ways`。

### POST /api/pos/restaurant/sessions/{session_id}/checkout — 埋单(落 pos_sale)
请求:
```json
{ "workspace_client_id":12, "shift_id":"uuid","terminal_id":1,
  "mode":"whole",                       // whole 整桌 | by_item 按项分单 | aa 平均
  "line_ids":["uuid"],                  // mode=by_item 必填:本次结哪些未结行
  "ways":4,                             // mode=aa:几人均摊(记录,出 per_share)
  "price_includes_vat":true,            // 缺省取门店/业态配置(默认价内 true)
  "service_rate":"10",                  // 服务费率(默认 10;0=免服务费)
  "header_discount":{"type":"none|pct|amount","value":"0"},
  "payments":[ {"method":"cash","amount":"484.00"} ],
  "client_uuid":"端上uuid", "sold_at":"...Z" }
```
> **一个事务**:取本次结算行(whole/aa=该 session 全部未结行;by_item=`line_ids` ∩ 未结)→ `compute_totals`
> 算菜品净额 → 服务费 = round(菜品小计 × rate) → VAT 在(菜品+服务费)上单次取整(价内反算/价外外加)→
> 发连号(`numbering` receipt)→ `sales_store.insert_sale/insert_line/insert_payment`(**复用零售小票表/连号/报表**)
> → UPDATE `pos_sales.service_charge` → 结算行 `settled_sale_id=新sale` → 若该 session 已无未结行 → session closed +
> 桌台空闲。**不扣库存**(菜品=成品)。`client_uuid` 命中 → 返原结果 `deduped:true`。
成功 `data:`
```json
{ "sale":{"id","receipt_no":"RCP-T1-2026-00123","subtotal":"440.00","service_charge":"44.00",
          "vat_amount":"31.66","grand_total":"484.00","paid_total":"484.00","change_amount":"0.00","status":"completed"},
  "session":{"id","status":"open|closed"},   // 分单未结完=open;结清=closed
  "split":{"ways":4,"per_share":"121.00"},    // aa
  "deduped":false }
```
错误:无可结行 → `pos.line_invalid`(detail=`no_billable_lines`);班次已交 → `pos.shift_closed`(409)。

### 复用的小票后置接口(直接走零售 `/api/pos/sales/*`,不另造)
- 热敏小票:`GET /api/pos/sales/{sale_id}/receipt-pdf`
- 收款二维码:`GET /api/pos/sales/{sale_id}/promptpay-qr`
- 升级正式税票:`POST /api/pos/sales/{sale_id}/full-tax-invoice`(屏 04"开税票")
> 餐厅埋单产出的 `sale_id` 即零售同款小票,后置全复用,统一进 B6 报表。

---

## 6. 错误码(本期复用既有 `pos.*`,见 docs/pos/06)

| 场景 | 复用码(HTTP) | error.detail |
|---|---|---|
| 桌已占用 / 无草稿可送 / 已下单行被改 / 无可结行 / 重复桌号 | `pos.line_invalid`(422) | `table_occupied` / `no_draft_lines` / `line_locked` / `no_billable_lines` / `duplicate_table` |
| 桌/session/KOT/sale 不存在 | `pos.product_not_found`(404) | — |
| session 非可点单态 / 取消有单的台 / 停用占用中的桌 | `pos.void_not_allowed`(409) | `session_not_open` / `session_has_orders` / `table_busy` |
| 班次已交班 | `pos.shift_closed`(409) | — |
| 权限/账套/模块 | `pos.forbidden` / `pos.module_disabled`(403) | — |

> **前端窗口接屏时**建议新增专用码并补 4 语(`pos.table_occupied` 409 / `pos.session_has_orders` 409 /
> `pos.no_billable_lines` 422 等),那时 i18n 不再撞别窗口 WIP。后端先用上表通用码 + detail,前端按 detail 给具体人话。

## 7. 契约测试要求(每端点 ≥1)
信封一致 · 鉴权(收银员调管理 403 · 模块关 module_disabled)· 幂等(checkout 同 client_uuid 不双开票)·
状态机(开台→点单→送厨房→KOT 流转→分单 → 桌转空闲)· 隔离(A 租户取不到 B 的桌/单)· **不扣库存**(埋单后库存不变)。
