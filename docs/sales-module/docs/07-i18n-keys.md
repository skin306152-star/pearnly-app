# 07 · i18n key 清单(4 语:th / en / zh / ja)

> ⚠️ 铁律:对外功能 **4 语必须全齐 — 中/英/泰/日(zh/en/th/ja)**,缺一个 = bug。
> `check_i18n.py --strict` 是 pre-push + CI 硬闸(0 missing/0 extra)。默认语言 th。
> 新增 key 在各语言块内按 **th→en→zh→ja** 顺序写(存量字典历史顺序 zh→en→th→ja 不动)。
> 动态生成内容必须 `subscribeI18n(...)` 注册,否则切语言不刷新。
> (`adm-*` 超管内部功能才可只 zh+th;本模块对外 → 必 4 语。)

## 导航 / 页面标题

| key | th | en | zh | ja |
|---|---|---|---|---|
| nav-sales-invoices | ใบกำกับภาษี/ใบเสร็จ | Sales Invoices | 销售发票 | 請求書発行 |
| nav-receivables | ลูกหนี้ | Receivables | 应收追踪 | 売掛金 |
| sales-page-title | ออกบิลขาย | Issue Sale | 开销售单 | 売上伝票作成 |

## 开单页

| key | th | en | zh | ja |
|---|---|---|---|---|
| sales-pick-client | เลือกลูกค้า | Select customer | 选客户 | 取引先選択 |
| sales-doc-type | ประเภทเอกสาร | Document type | 单据类型 | 書類種別 |
| sales-doctype-tax-invoice | ใบกำกับภาษี | Tax invoice | 税务发票 | 税額票 |
| sales-doctype-receipt | ใบเสร็จรับเงิน | Receipt | 收据 | 領収書 |
| sales-input-code | คีย์รหัสสินค้า | Enter code | 手输代码 | コード入力 |
| sales-input-barcode | สแกนบาร์โค้ด | Scan barcode | 扫条码 | バーコード |
| sales-input-qr | สแกน QR | Scan QR | 扫二维码 | QR スキャン |
| sales-input-photo | เลือกจากรูป | From photo | 从照片选 | 写真から選択 |
| sales-subtotal | ยอดก่อนภาษี | Subtotal | 税前合计 | 税抜合計 |
| sales-vat | ภาษีมูลค่าเพิ่ม (VAT) | VAT | 增值税 | 付加価値税 |
| sales-wht | ภาษีหัก ณ ที่จ่าย | WHT | 预扣税 | 源泉徴収税 |
| sales-grand-total | ยอดรวม | Total | 合计 | 合計 |
| sales-save-draft | บันทึกร่าง | Save draft | 存草稿 | 下書き保存 |
| sales-issue | ออกเอกสาร | Issue | 正式开出 | 正式発行 |
| sales-void | ยกเลิก | Void | 作废 | 取消 |
| sales-send | ส่งให้ลูกค้า | Send | 发送给客户 | 送信 |

## 应收追踪

| key | th | en | zh | ja |
|---|---|---|---|---|
| ar-aging | อายุหนี้ | Aging | 账龄 | 滞留期間 |
| ar-overdue | เกินกำหนด | Overdue | 逾期 | 延滞 |
| ar-remind | ทวงถาม | Remind | 催收 | 督促 |

## 四态文案

| key | th | en | zh | ja |
|---|---|---|---|---|
| sales-empty-products | ยังไม่มีสินค้า เพิ่ม/นำเข้าก่อน | No products yet — add or import | 还没有商品,先建档/导入 | 商品なし — 登録/取込 |
| sales-loading | กำลังโหลด… | Loading… | 加载中… | 読み込み中… |
| sales-error-retry | เกิดข้อผิดพลาด ลองใหม่ | Something went wrong — retry | 出错了,重试 | エラー — 再試行 |

> 注:th/ja 为初译,**税务用语最终以客户(会计事务所)+ 母语者校对为准**(关键术语用 Gemini 出本地标准词)。
