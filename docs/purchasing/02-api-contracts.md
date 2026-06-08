# 商户采购 · 02 接口契约(前后端唯一源 · 封板)

> 信封同 POS(`core/pos_api`):成功 `{ok:true,data}` · 失败 `{ok:false,error:{code,message_key}}`,前端先看 ok 再读 data。
> 全接口要 `workspace_client_id`(取自上下文/套账切换器),缺=`workspace.required`(fail-closed)。前缀 `/api/purchase/*`。
> **本版并入 Paypers 对标**:WHT / 替代收据生成 / 审批人 / 两级科目 / 多币种 / 供应商总分公司。

## 0. 统一智能入口与分流(★核心 · 见 product-vision §三-bis)

### POST /api/purchase/intake — 扔进来,AI 判类型+去向(拍照/上传/文字共用)
请求(其一):`{ "workspace_client_id", "image": <multipart> }` 或 `{ "workspace_client_id", "text": "清洁剂 50" }`
成功:`data:`
```json
{ "kind": "purchase_invoice|purchase_order|expense|bank|sales|unknown",
  "confidence": 0.93,
  "route": "purchase|expense|recon|sales|inbox",
  "draft": { "supplier":{"name","tax_id","branch_type"}, "doc_no","doc_date","has_vat","currency",
             "lines":[{"item_type","description","qty","unit_price","vat_rate","category_id","subcategory_id"}],
             "subtotal","vat_amount","wht_amount","grand_total","net_payable" },
  "dedupe_hit": false }
```
> AI 判:文字→expense;图/PDF→OCR→**判方向**(买方=本套账主体税号 → 进项票;卖方=我 → 销项)→ 进项票/采购单(无VAT+PO格式)/小票→expense/银行单→recon。
> `confidence` 低 或 `kind=unknown` → `route=inbox`(落 intake_items 待用户一点,绝不静默丢错)。
> `dedupe_hit=true` → 前端提示"像录过"(防重复抵扣)。

## 1. 进项单据(采购票/采购单/费用)
- **POST /api/purchase/docs** — 从 intake draft 或手录确认建单。
  `{workspace_client_id,doc_kind,supplier{id|name,tax_id,branch_type,branch_no,address},doc_no,doc_date,has_vat,currency,fx_rate,requester,approval_status,lines[],subtotal,discount_total,vat_amount,wht_amount,rounding,grand_total,net_payable,source,dedupe_key}` → `data:{doc}`。
  行:`{item_type,product_id?,description,qty,unit,unit_price,discount,vat_rate,wht_rate,category_id,subcategory_id,batch_no?,expiry_date?}`。
  错误:`purchase.dup_invoice`(409)·`purchase.line_invalid`(422)·`purchase.amount_mismatch`(422·合计反算不符)。
- **GET /api/purchase/docs?workspace_client_id=&kind=&status=&unpaid=&q=** — 列表 + 汇总(本月进货/费用/可抵进项税/未付)。
- **GET /api/purchase/docs/{id}** — 详情(头+行+附件+票图)。
- **PUT /api/purchase/docs/{id}** — 改草稿(posted 不可改,409)。
- **POST /api/purchase/docs/{id}/post** — 入账。进货入库开 → 按行 product_id 写库存(未配先 `match-product`)。`data:{doc,stock_applied}`。
- **POST /api/purchase/docs/{id}/pay** — 记付款 `{amount,method,date,note}` → 更新 payment_status(支持部分付款)。
- **POST /api/purchase/docs/{id}/void** — 作废(已入库的回冲)。
- **DELETE /api/purchase/docs/{id}** — 删草稿(仅 draft·级联删行/附件)。

## 2. 行 ↔ 商品(seam:进货品项↔商品库)
- **POST /api/purchase/lines/{id}/match-product** — 匹配/新建 SKU `{product_id}|{create:{name,unit,barcode?}}`。

## 3. 凭据生成(★Paypers 对标 · 复用销项 reportlab)
- **POST /api/purchase/docs/{id}/substitute-receipt** — 生成「替代收据」PDF(无正规发票时·泰文合规)→ 挂 purchase_attachments(kind=substitute_receipt,generated=true)→ `data:{attachment}`。
- **POST /api/purchase/docs/{id}/wht-cert** — 生成「扣缴凭证」PDF(wht_amount>0 时)→ kind=wht_cert。
- **POST /api/purchase/docs/{id}/attachments** — 附票图/付款凭证 `{kind,file}`;**DELETE /attachments/{aid}**。

## 4. 费用快速记(LINE/一句话)
- **POST /api/purchase/expense** — `{workspace_client_id, text|image, category_id?}` → AI 归类(到子科目)→ 记一笔 expense doc + 自动生成替代收据。LINE bot 复用此入口。`data:{doc, category, substitute_receipt}`。

## 5. 供应商(配置后台)
- GET/POST/PATCH `/api/purchase/suppliers`(owner/会计)· 字段含 branch_type/branch_no/address · 停用=is_active · 删除仅限零单据 · 套账隔离。

## 6. 费用科目 / 采购设置(配置后台)
- GET/POST/PATCH `/api/purchase/categories` — **两级**(parent_id;返回树)· 预设 seed + 增删。
- GET/PUT `/api/purchase/settings`(默认VAT/进货入库/重复票拦/账期/付款审批/服务默认WHT率/本位币)。

## 7. 报表/汇总(联动报税)
- GET `/api/purchase/summary?from=&to=` — 进货/费用/可抵进项税/**WHT 代扣** 按期汇总(喂报税:销项税−进项税;WHT→PND)。

## 鉴权/角色
- owner/会计:全权(录+审付款+改供应商/设置+生成凭据)。员工(采购员角色):可录、不可审付款、不可改供应商。`/pay`、供应商写、settings、凭据生成 = `require_account_owner` 或会计。

## 错误码(进 05 字典 · 4 语)
`purchase.dup_invoice · purchase.line_invalid · purchase.amount_mismatch · purchase.supplier_inactive · purchase.tax_id_invalid · purchase.not_draft · purchase.forbidden · workspace.required · purchase.unexpected`

## 契约测试(每端点 ≥1)
信封一致 · intake 分流(文字→expense/进项票判方向→purchase/低置信→inbox)· dedupe 防重复票 · 合计含 WHT 反算一致 · 入账联动库存 · 替代收据生成挂附件 · 套账隔离(A 拿不到 B)· 角色 403。
