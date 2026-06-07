# 商户采购 · 03 逐 PO 施工单

> 风险低→高。每 PO 独立可上 + 独立 E2E(跨套账 A/B 互不串)+ 守门全绿。
> **前置地基**:① 套账隔离(workspace_client 上下文 + ocr_history 套账·PO-4)② OCR 扩 schema 认进项票。涉钱/改注册无,但碰 OCR/LINE 主路径处先报方案。

## 依赖
```
套账隔离地基(在跑) + OCR扩schema
        │
PO-1 主数据/配置 ─► PO-2 进项单据(手录+列表) ─► PO-3 拍照OCR识别确认
                                                      │
                          PO-4 智能分流(intake·AI判类型+去向) ─► PO-5 LINE一句话+分流接入
                                                      │
                          PO-6 联动(进货入库 / 进项税→报税 / 付款应付)
                                                      │
                          PO-7 前端 5 屏(照桌面稿·等地基+窗口)─► PO-8 闸 + 全链路E2E
```

## PO-1 · 主数据 + 配置(低风险 · 练手)
- `suppliers` 表 + CRUD(套账隔离)· `expense_categories`(预设 seed)· `purchase_settings`。
- 出口:供应商/科目/设置能配,套账隔离;无前端也能契约测。

## PO-2 · 进项单据核心(手录先通)
- `purchase_docs` + `purchase_lines` 表 + 建单/列表/详情/post/pay/void + dedupe 防重复票。
- 先支持手动录(不依赖 OCR),把"单据→入账→付款"主干跑通 + 跨套账 E2E。

## PO-3 · 拍照 OCR 识别确认(★智能)
- **扩 OCR schema 认进项票/小票**(现 OCR 只识销项):抽 供应商/税号/日期/金额/VAT/品项。
- 拍照/上传 → OCR → 预填 draft → 确认建单(屏2)。复用现有 OCR 引擎 + 计费。
- 行品项 `match-product`(匹配 SKU / 一键建商品)。
- ⚠️ 碰 OCR 主路径 → 先报方案。

## PO-4 · 智能分流(统一入口 · product-vision §三-bis)
- `POST /api/purchase/intake`:AI 判 kind(进项票/采购单/费用/银行/销项/unknown)+ confidence + route + draft。
- 低置信/unknown → `intake_items` 待归类(不静默丢错)。dedupe 检测。
- 与 PO-3 可合做(识别即分流)。

## PO-5 · LINE 一句话 + 分流接入
- LINE bot 文字"清洁剂 50" → `/api/purchase/expense`(AI 归类)。
- LINE 拍图 → 走 intake 分流(进项票→采购,小票→费用),归当前绑定套账。
- ⚠️ 改现有 `services/ocr/line_image_ocr.py`(LINE 主路径)+ 套账分流 → 先报方案;与套账隔离 PO-4 协调。

## PO-6 · 联动(seam 接实)
- 进货 `post` → `inventory_transactions` 入库(进货入库开时)。
- `/api/purchase/summary` 进项税汇总 → 报税(销项−进项)。
- 付款 → 应付 aging(完整应付归应收应付模块,本期出基础聚合)。
- 做账凭证 hook 留给 Phase 2。

## PO-7 · 前端 5 屏(照桌面 `Pearnly_采购_UI预览`)
- 主屏 / 拍照识别确认 / LINE记费用入口 / 供应商管理 / 采购设置。
- **手机优先适配**(拍照主场景)。视觉照搬稿(双语标注→i18n 单语)· 信封 · posErrMsg。
- ⚠️ 老板配置(供应商/设置)走**平铺页**(同收银设置教训:点导航进页面,不弹窗;页内动作才弹窗)。
- 等套账隔离前端(顶栏切换器)+ src/home 窗口腾出再上。

## PO-8 · 机械闸 + 全链路 E2E
- `test_purchase_sql_isolation`(套账隔离)+ dedupe + intake 分流 进 CI。
- 全链路:拍进项票→AI分流→确认入账→进库存→进项税进汇总→付款 跨套账 E2E。

## 每 PO 验收
守门 6 道 + 单测 + 真账号跨套账 E2E + (碰 OCR/LINE)先报方案。手机端真机/视口验。
