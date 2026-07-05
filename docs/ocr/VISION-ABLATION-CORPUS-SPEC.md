#  施工单 · Vision 消融实测语料生成

## 你的任务(只做这一件)
生成一套**逼真的泰国票据/发票测试语料**(图片 + 每张的真值 JSON),用于一次 OCR 消融实测:
判断 OCR 管线的 L1(Google Vision)层能否砍掉、改成「图片直喂 Gemini 抽取」。
**你只负责生成文件。不要跑任何评测、不要改管线代码、不要碰服务器。**

评测由另一方(Claude)用项目现成的 `tests/eval/run_invoice_eval.py` + `invoice_scorer.py` 来跑。
所以你产出的真值字段名/格式**必须严格对齐**下面列的项目 schema,否则打不了分。

## 为什么要「误导性 + 退化」组合(重点)
这次要验证的是:Vision 先把字读出来「接地」,到底有没有在防幻觉/保准确上起作用。
只有在**容易读错、容易被带偏**的票上,两条路(有Vision vs 纯Gemini看图)才会分叉。
所以语料的价值全在**陷阱**和**画质退化**,以及**两者的叉乘**。干净漂亮的票没有区分度,少放。

## 必须先读(对齐字段与约定,别自己臆造)
1. `services/ocr/schemas_invoice.py` — `ThaiInvoice`/`LineItem` 全字段 + 约定(金额=字符串无千分位、`document_type` 的 Literal 枚举、泰历/公历日期、13位税号)。**真值字段名以此为准。**
2. `tests/eval/invoice_scorer.py` 的 `_FIELD_SPEC` — 会被打分的字段 + 比对规则(money/id13/invno/date/currency/text/count)。**真值至少要覆盖这些字段。**
3. `tests/eval/ground_truth_local/invoices/*.json` — 现成真值范例(看它的键名和风格)。
4. `services/ocr/layer2_prompts.py` 里 `_SYSTEM_PROMPT` — 抽取器被要求产出什么语义(尤其:`total_amount`=折扣后**实付净额**,不是毛额;VAT included/excluded 的处理)。真值语义要和它一致。

## 产出目录结构
```
tests/eval/vision_ablation/
  images/            # 生成的票据图片,文件名 = <id>.jpg(建议 JPEG,模拟手机拍照)
  ground_truth/      # 每张一个 <id>.json(真值,schema 见下)
  manifest.jsonl     # 索引,每行一条(见下)
  generate.py        # 你的生成脚本(可复现,渲染+退化都在这)
  README.md          # 简述生成方式/场景分布/如何复现
```

## 真值 JSON schema(每张一个 · 字段名严格照此)
```json
{
  "id": "trap_change_blur_007",
  "file": "trap_change_blur_007.jpg",
  "document_type": "simplified_tax_invoice",   // 用 schemas_invoice 的 Literal 枚举值
  "seller_name": "CP ALL, 7-Eleven สาขา...",
  "seller_tax": "0107542000011",               // 13位;无则 ""
  "buyer_name": "",
  "buyer_tax": "",
  "invoice_number": "R#0000472055P1",
  "date": "2026-07-05",                         // ISO 公历(泰历要在此转好)
  "date_raw": "05/07/69 12:55",                // 票面原样(含泰历/格式)
  "subtotal": "167.00",                         // 字符串,无千分位
  "vat": "0.00",
  "discount": "0.00",
  "total_amount": "167.00",                     // 折扣后实付净额(打分权重最高)
  "cash_amount": "200.00",                      // 有则填(找零陷阱要用)
  "change_amount": "33.00",
  "payment_method": "cash",
  "currency": "",                               // 泰铢=空串;外币填 USD/EUR...
  "items": [
    {"name": "สปาเก็ตตี้", "qty": "1", "price": "59.00", "subtotal": "59.00"}
  ],
  "scenario": "cash_change_trap",               // 单一主场景标签(见矩阵)
  "traps": ["cash_gt_total", "change_line"],    // 本张埋的所有陷阱(可多个)
  "degradation": ["motion_blur_mid"],           // 本张的画质退化(可多个/可空=sharp)
  "_note": "现金付200找零33,真实付167。诱模型把200或33当总额。"
}
```
约定细节:金额一律**字符串、无逗号、两位小数**;泰历年(25xx/2位69)在 `date` 里转成公历、`date_raw` 保留原样;税号 13 位纯数字或空。

## 场景矩阵(全方位覆盖 · 两轴叉乘)

### 轴 A:内容/版式陷阱(误导性——这是重点,尽量密集)
1. **找零陷阱**:现金付款 > 总额,含找零行(诱把现金/找零当总额)。
2. **数量×单价**:`3 แก้ว` / `2 ชิ้น ชิ้นละ 50`,只有数量没总价 / 数量像金额。
3. **长数字干扰**:电话号(08x-xxxxxxx)、13位税号、POS/单据流水号、会员卡号——都别被当金额。
4. **积分/优惠诱导**:`สะสมแต้ม 560`、`ประหยัด ฿26`、`了25元`(积分/省了多少,别当折扣或总额)。
5. **多个金额并列**:毛额/小计/前税额/VAT/合计/四舍五入尾差——哪个才是 grand total。
6. **VAT 三态**:VAT included(内含)、VAT excluded(外加)、无 VAT(0)。
7. **预扣税 WHT(หัก ณ ที่จ่าย)**:含 3%/5% 预扣,考 `wht_rate`/`wht_amount` 与 total 的关系。
8. **折扣行**:毛额 - 折扣 = 净额,`total_amount` 要取净额。
9. **泰历/公历日期陷阱**:2567/2569/69 泰历,和公历混排。
10. **外币**:USD/€ 标价(`currency` 非空,下游会拦,不能当泰铢)。
11. **单图多票 / 多页**:一张图里 2~3 张独立税票(不同买家/单号);多页同一票。
12. **非发票诱饵**:采购订单(PO)、报价单(quotation)、送货单(delivery_note)、COPY/ซ้ำ 副本章 —— `is_not_invoice`/`document_type` 要判对。
13. **密集多行 + 微字**:15+ 明细行、小字号(考漏行/串行)。
14. **手写金额/手写总额**:手写数字的总额或单价。
15. **竖排/堆叠版式**:类银行GL的按列堆叠(金额与余额易粘连)。
16. **0 บาท 促销行混入**:赠品/慈善 0 元行,别塞进明细也别影响合计。

### 轴 B:图像退化(画质——Vision 读字优势最可能体现的地方)
`sharp`(基线) · `motion_blur_low/mid/high` · `defocus_blur` · `thermal_fade`(热敏褪色/渐变浅) ·
`glare`(反光亮斑) · `shadow`(阴影) · `crease`(折痕) · `crumple`(揉皱) ·
`rotate_90` · `skew_±15` · `perspective`(透视歪) · `low_res`(降分辨率) ·
`jpeg_artifact`(重压) · `torn`(撕缺/截断) · `dark`(欠曝) · `overexposed`(过曝) ·
`bg_clutter`(桌面纹理背景)。

### 叉乘要求(价值所在)
**每一类陷阱都要出现在 至少 2~3 个退化档**(尤其 blur / thermal_fade / glare / crease)。
例:找零陷阱×模糊、手写总额×褪色、外币×反光、单图多票×透视歪、微字密集×低分辨率。
**这些「误导 + 糊」的组合是本次实测的核心样本。**

## 规模与分布(建议)
- **总量 ≥ 80 张**(越多越好,别怕多)。
- 干净基线(sharp,无陷阱)约 10 张作对照;其余 **70+ 张都要带陷阱**,其中 **一半以上叠加退化**。
- 覆盖:每个轴A陷阱 ≥ 4 张(不同退化);每个轴B退化 ≥ 3 张;单图多票 ≥ 5 张;非发票诱饵 ≥ 6 张;外币 ≥ 4 张;手写 ≥ 4 张。
- 真值必须**逐字亲填、可复核**(因为图是你渲染的,内容你完全掌握——这正是合成语料的优势:真值零误差 + 陷阱可控注入)。

## 逼真度要求
- 真实泰国商户风格:7-Eleven / Tops / Makro / Lotus's / PTT / Cafe Amazon / 本地小店/餐馆。
- 泰文字体(Sarabun / 热敏点阵风),真实票据版式(店头/税号/明细/合计/付款/页脚二维码)。
- 合理的 13 位税号、THB 金额格式、泰历日期。
- 退化用程序化施加(高斯/运动模糊、JPEG 压缩、旋转/透视矩阵、亮度/对比、热敏渐变、折痕阴影、噪声),模拟真实手机拍摄。

## manifest.jsonl 每行格式
```json
{"id":"trap_change_blur_007","file":"images/trap_change_blur_007.jpg","gt":"ground_truth/trap_change_blur_007.json","scenario":"cash_change_trap","traps":["cash_gt_total"],"degradation":["motion_blur_mid"]}
```

---

# Part 2 · 对账三类文档语料(银行对账单 / 总账GL / 销项税报告)

## 为什么这部分对「砍Vision」最关键
对账中心三条:银行对账(银行账单 + 总账GL)、销项税报告核查、收入对账。这些文档平时多是
**电子PDF**——会走 pypdf 文字层、**跳过 Vision**。但真实用户经常是**拍照/扫描**上传(把打印出来
的对账单拍一张),扫描件**没有文字层 → 回落到 Vision**。所以:
- **必须生成「扫描件 / 拍照」版**(不是干净电子PDF),这才落在 Vision 路上、才测得出 Vision 该不该砍。
- 表格类文档(密集行、堆叠列、借贷余额三列易粘连)是 OCR 最难的场景,也是最能分出「Vision 接地
  vs 纯 Gemini 看图」的地方。项目历史上就栽过「GL 竖排堆叠版式本地解析0行」「余额千分位粘成百亿」。
- 你们一直缺这三类真实测试件——这次一并补上,既服务本次 Vision 实测,也成永久回归资产。

## 必须先读(这三类 schema 与发票不同)
- `services/ocr/schemas_documents.py` — `BankStatementDocument` / `GeneralLedgerDocument` /
  `VatReportDocument` 及其行 schema(`BankStatementEntry`/`GLEntry`)全字段。
- `services/ocr/layer2_prompts.py` — `_BANK_STATEMENT_SYSTEM_PROMPT` / `_GL_SYSTEM_PROMPT` /
  `_VAT_REPORT_SYSTEM_PROMPT`(抽取语义:direction 由余额涨跌/借贷列判、透支负余额尾缀 '-' 等)。
- `tests/eval/ground_truth_local/BBL_2645.json` / `KTB_6694.json` — 银行真值范例(**勾稽汇总数**风格)。
- 可参考 `scripts/_gen_test_invoices.py`(已有的发票生成脚本,风格可借)。

## 产出目录(与 Part 1 并列)
```
tests/eval/vision_ablation/
  bank/        images/ + ground_truth/    # 银行对账单(扫描/拍照)
  gl/          images/ + ground_truth/    # 总账 GL(扫描/拍照)
  vat/         images/ + ground_truth/    # 销项/进项税报告(扫描/拍照)
  manifest_recon.jsonl
```

## 真值 schema(合成语料给「全明细 + 勾稽汇总」两级 → 我两级都能打分)

### 银行对账单 <id>.json
```json
{
  "id": "bank_kbank_stacked_photo_03", "file": "bank/images/....jpg", "doc_type": "bank_statement",
  "bank_name": "ธนาคารกสิกรไทย", "bank_code": "kbank",
  "account_name": "...", "account_number": "102-3-08264-5", "account_last4": "2645",
  "period_start": "2025-12-01", "period_end": "2025-12-31",
  "opening_balance": "1141561.05", "closing_balance": "0.00",   // 透支负数就写负号
  "entry_count": 42, "total_deposit": "34801342.07", "total_withdrawal": "34801342.07",
  "entries": [
    {"transaction_date":"2025-12-03","description":"โอนเงิน...","reference":"KPLUS",
     "deposit":"5000.00","withdrawal":"","balance":"1146561.05","direction":"deposit"}
  ],
  "scenario":"stacked_columns", "traps":["overdraft_negative","thousand_sep_stick"],
  "degradation":["phone_photo_skew","shadow"], "_note":"透支账户末行余额0.00=期末;竖排堆叠列"
}
```
勾稽汇总(必填,银行对账真正核的就这些):`opening_balance` `closing_balance` `entry_count`
`total_deposit` `total_withdrawal` + `period_*` + `account_number/last4` + `bank_code`。

### 总账 GL <id>.json
同构:`period_start/end` `account_name` `account_number` `opening_balance` `closing_balance`
`entry_count` `total_debit` `total_credit` + `entries[]`(每行 `transaction_date` `voucher_no`
`account_code` `description` `debit` `credit` `balance` `direction`)。

### 销项/进项税报告 <id>.json
`report_type`(sales/purchase) `period` `row_count` `total_pre_vat` `total_vat` `total_amount`
+ `rows[]`(每行 `seq_no` `transaction_date` `invoice_no` `customer_name`/`seller_name`
`seller_tax`/`buyer_tax` `pre_vat_amount` `vat` `total`)。

## 场景/陷阱矩阵(对账专属误导性——比发票更狠)
- **银行对账单**:透支账户**负余额尾缀 '-'**(极易丢负号)· 借/贷/余额**三列堆叠粘连** ·
  **千分位与余额粘成天文数字**(123.37 vs 余额)· **多页**(只给第8/8页→无真期初) ·
  direction 全靠**余额涨跌**推 · 利息/手续费/0.00 行 · 不同银行版式(KBANK/SCB/BBL/TTB/กรุงศรี/ออมสิน) ·
  泰历日期 · 外币账户 · **横排 vs 竖排堆叠**两种版式。
- **总账 GL**:竖排堆叠版式(历史雷点·本地解析0行) · voucher/科目号像金额 · 借贷不平尾差 ·
  期初被千分位截断 · 跨页小计/累计余额 · 中英泰混排科目名。
- **销项税报告**:多页行级 + 末页合计(小计 vs 总计) · 零税率/免税行 · 税号13位当金额干扰 ·
  行级 VAT 之和 = 报告合计的勾稽 · 泰历。

## 退化(必须是「扫描/拍照」真实场景,别给干净电子件)
A4 文档的真实上传形态:`phone_photo_skew`(手机斜拍A4) · `flatbed_scan`(平板扫描·轻噪) ·
`shadow`/`glare`(拍照阴影/反光) · `fold_crease`(折过的打印件) · `low_res`(压缩小图) ·
`partial_page`(只拍到一部分/多页只传一页) · `dark`/`overexposed` · `moire`(屏摄摩尔纹) ·
`bg_clutter`(桌面背景)。**每种银行/GL 版式 × 至少 3 种退化。**

## 规模(对账部分)
- 银行对账单 ≥ 24 张(≥5家银行 × 多退化,含 ≥6 张透支负余额、≥4 张竖排堆叠、≥3 张多页片段)。
- 总账 GL ≥ 12 张(含 ≥4 张竖排堆叠、≥3 张借贷不平尾差)。
- 销项/进项税报告 ≥ 12 张(含 ≥4 张多页合计、≥3 张零税率混入)。
- 真值逐行亲填、勾稽数自洽(sum(明细)=汇总,借贷平,余额链连续)——合成的优势就在此。

---

## 工具与依赖(逼真度命门 · 光有文案不够真)
文案说的是「要什么场景」,下面这些库决定「渲染/退化得像不像真扫描件」。**Thai字体 + Augraphy 是两个命门。**
- **泰文字体(必装,否则泰文=方块)**:Noto Sans Thai、TH Sarabun New / Sarabun;热敏点阵风可配等宽。
- **渲染引擎(挑最逼真的)**:优先 HTML/CSS + **Playwright**(headless Chromium)截图——真排版/表格/
  热敏CSS,最像真票;次选 reportlab(PDF)→光栅化,或 Pillow 直绘(最省但最假,仅兜底)。
- **退化库(核心·别手搓高斯模糊,一眼假)**:
  - **Augraphy** —— 专为「扫描/拍照文档」退化而生的库(墨渗/热敏褪色/折痕/阴影/污点/摩尔纹/低对比/
    印章),让扫描件像真扫描件。**这是逼真度最大杠杆。**
  - **OpenCV(cv2)** —— 透视变形 / 旋转 / 光照不均 / 桌面背景合成。
  - **Pillow + numpy** —— 噪声 / 亮度对比 / JPEG 重压 / 热敏渐变。
- **条码/二维码**:qrcode + python-barcode(票据/对账单页脚的条码/QR)。
- 一键装:`pip install playwright pillow opencv-python numpy augraphy qrcode python-barcode` +
  `playwright install chromium` + 下载 Noto Sans Thai 字体。generate.py 里把渲染与 Augraphy 退化管线串好、参数可复现。

## 交付即完成(整份 spec)
产出 Part 1(发票 ≥80)+ Part 2(对账三类 ≥48)的图片 + 真值 + manifest 即可。
**不要跑评测、不要改 `services/ocr/` 或任何管线、不要连服务器。**
所有真值必须与图片内容 100% 一致、勾稽自洽(合成语料的全部价值就在这)。
生成脚本 `generate.py` 要可复现(渲染 + 退化参数都在里面),附 `README.md` 说明场景分布。
