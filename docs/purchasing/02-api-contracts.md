# 商户采购 · 02 接口契约(前后端唯一源)

> 信封同 POS(`core/pos_api`):成功 `{ok:true,data}` · 失败 `{ok:false,error:{code,message_key}}`,前端先看 ok 再读 data。
> 全接口要 `workspace_client_id`(取自上下文/套账切换器),缺=`workspace.required`(fail-closed)。前缀 `/api/purchase/*`。

## 0. 统一智能入口与分流(★核心 · 见 product-vision §三-bis)

### POST /api/purchase/intake — 扔进来,AI 判类型+去向(拍照/上传/文字共用)
请求(其一):`{ "workspace_client_id", "image": <multipart> }` 或 `{ "workspace_client_id", "text": "清洁剂 50" }`
成功:`data:`
```json
{ "kind": "purchase_invoice|purchase_order|expense|bank|sales|unknown",
  "confidence": 0.93,
  "route": "purchase|expense|recon|sales|inbox",
  "draft": { ...按 kind 预填字段:supplier{name,tax_id}/doc_no/date/subtotal/vat/lines[]/category... },
  "dedupe_hit": false }
```
> AI 判:文字→expense;图/PDF→OCR→进项票(供应商税号+买方=我+VAT)/采购单(无VAT+PO格式)/小票→expense/银行单→recon。
> `confidence` 低 或 `kind=unknown` → `route=inbox`(落 intake_items 待用户一点,绝不静默丢错)。
> `dedupe_hit=true` → 前端提示"像录过"(防重复抵扣)。

## 1. 进项单据(采购票/采购单)
- **POST /api/purchase/docs** — 从 intake draft 确认建单。`{workspace_client_id,doc_kind,supplier{id|name,tax_id},doc_no,doc_date,has_vat,lines[],subtotal,vat_amount,grand_total,source,image_url,dedupe_key}` → `data:{doc}`。错误:`purchase.dup_invoice`(409·重复票)·`purchase.line_invalid`(422)。
- **GET /api/purchase/docs?workspace_client_id=&kind=&status=&unpaid=&q=** — 列表 + 汇总(本月进货/费用/可抵进项税/未付)。
- **GET /api/purchase/docs/{id}** — 详情(头+行+票图)。
- **POST /api/purchase/docs/{id}/post** — 入账。进货入库开 → 按行 product_id 写库存(匹配不上的行先 `match_product`)。`data:{doc,stock_applied}`。
- **POST /api/purchase/docs/{id}/pay** — 记付款 `{amount,method,date}` → 更新 payment_status。
- **POST /api/purchase/docs/{id}/void** — 作废(已入库的回冲)。
- **POST /api/purchase/lines/{id}/match-product** — 行匹配/新建 SKU `{product_id}|{create:{name,unit,...}}`。

## 2. 费用快速记(LINE/一句话)
- **POST /api/purchase/expense** — `{workspace_client_id, text|image, category_id?}` → AI 归类 → 记一笔 expense doc。LINE bot 复用此入口。`data:{doc, category}`。

## 3. 供应商(配置后台)
- GET/POST/PATCH `/api/purchase/suppliers`(owner/会计)· 停用=is_active · 删除仅限零单据 · 套账隔离。

## 4. 费用科目 / 采购设置(配置后台)
- GET/POST/PATCH `/api/purchase/categories`(预设 + 增删)。
- GET/PUT `/api/purchase/settings`(默认VAT/进货入库/重复票拦/账期/付款审批)。

## 5. 报表/汇总(联动报税)
- GET `/api/purchase/summary?from=&to=` — 进货/费用/可抵进项税 按期汇总(喂报税:销项税−进项税)。

## 鉴权/角色
- owner/会计:全权(录+审付款+改供应商/设置)。员工(若开 cashier/采购员角色):可录、不可审付款、不可改供应商。`/pay`、供应商写、settings = `require_account_owner` 或会计。

## 错误码(进 06 字典风格 · 4 语)
`purchase.dup_invoice · purchase.line_invalid · purchase.supplier_inactive · purchase.tax_id_invalid · purchase.forbidden · workspace.required · purchase.unexpected`

## 契约测试(每端点 ≥1)
信封一致 · intake 分流(文字→expense/进项票→purchase/低置信→inbox)· dedupe 防重复票 · 入账联动库存 · 套账隔离(A 套账拿不到 B)· 角色 403。
