# 04 · API 契约(草案)

> 对齐主仓库 `routes/*_routes.py` 约定:FastAPI `APIRouter`、`get_current_user_from_request` 取用户、
> `_tid`/RLS 游标做租户隔离、Pydantic 请求模型、response shape 稳定。所有写操作走参数化 SQL。
> 这是契约草案,字段随客户拍板(`docs/09`)收敛。

## 商品主数据 · /api/products

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/products | 列商品(租户过滤 + 搜索 q + 分页) |
| POST | /api/products | 建商品 |
| PATCH | /api/products/{id} | 改商品 |
| DELETE | /api/products/{id} | 软删(is_active=false) |
| GET | /api/products/lookup | 按 code/barcode/qr 精确查(扫码/手输录入命中)|
| POST | /api/products/import | Excel 批量导入(Q4=Excel 时)|

`GET /api/products/lookup?by=barcode&value=...` → 命中返回单个商品;未命中 404(前端引导建档)。

## 销项单据 · /api/sales/documents

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/sales/documents | 列单(状态/客户/日期过滤 + 分页) |
| POST | /api/sales/documents | 建草稿(draft,不占号) |
| GET | /api/sales/documents/{id} | 取单详情(含明细) |
| PATCH | /api/sales/documents/{id} | 改草稿;**issued 后拒改**(409) |
| POST | /api/sales/documents/{id}/issue | 正式开出 → **事务内取连号** → status=issued,issued_at=now |
| POST | /api/sales/documents/{id}/void | 作废(留记录,不回收号) |
| GET | /api/sales/documents/{id}/pdf | 生成合规 PDF(ใบกำกับภาษี/ใบเสร็จ) |
| POST | /api/sales/documents/{id}/send | 发送(email / LINE,body 指定渠道) |

红冲/补开(Q3 gated):
| POST | /api/sales/documents/{id}/credit-note | 开 ใบลดหนี้ |
| POST | /api/sales/documents/{id}/debit-note | 开 ใบเพิ่มหนี้ |

## 智能录入 · /api/intake(引擎入口 · 两个方向共用)

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/intake/extract | 多模态提取:图片/PDF→复用 Gemini OCR;文本一句话→解析金额+品名 |
| POST | /api/intake/verify-tax-id | 校验对方税号真伪 → 复用 `routes/rd_routes.py` |
| POST | /api/intake/validate | 录入前规则校验 → 复用 `services/knowledge`(算术/完整/查重) |

`extract` 返回结构化候选(金额/对方/明细/税号),前端预填表单,人确认后再落库——**AI 提取不直接成单**(状态诚实)。

## LINE 录入/发单 · 复用 line_webhook

- 进 `routes/line_webhook_routes.py` 现有 webhook,新增 intent:
  - 文本 "ค่าน้ำ 50" / 发图 → 调 `/api/intake/extract` → 回结构化卡片让用户确认
  - 确认 → 落库(进项记一笔 / 销项开一单)→ 回 PDF 链接
- 不新开 webhook 端点,挂在现有消息分发上(避免重复 LINE 通道)。

## ภ.พ.30 汇入 · 复用 vat_excel

- `vat_excel` 现汇进项;扩 query 把 `sales_documents`(issued)的销项税额一并纳入。
- 不新建报表引擎,只扩数据源 + 报表模板加销项列。

## 错误约定(对齐现有)

- 401 未登录 / 403 无权限(plan 闸)/ 404 未命中 / 409 状态冲突(改已开出单)/ 422 校验失败。
- 金额一律字符串化 decimal 传输,前端不做 float 运算。
