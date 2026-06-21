# 10 · LINE 记账测试要求(来源于领域调研 · 2026-06-22)

> 用途:测试要求**不拍脑袋编**,从泰国 SME 记账/票据/泰语 NLP 这块的真实标准与研究里推导。
> 本页 = 调研结论 → 测试要求 → 跑法。配套:用例 `09`、语料 `tests/fuzz/line_fuzz_corpus.py`。

---

## 1. 调研来源(四个方向)

| 方向 | 关键结论 | 来源 |
|---|---|---|
| 泰国税票字段 | 全票(ใบกำกับภาษี)13 必填(税法§86):卖家/买家名+13位税号、序列发票号、**VAT 7% 与金额分列**、日期;另有简式票(ย่อ·免买家信息)。缺字段=不能抵进项+罚 2000 | [Thailand Tax Invoice Requirements](https://invoicedataextraction.com/blog/thailand-tax-invoice-requirements) · [VBA Partners](https://vbapartners.com/how-to-issue-a-tax-invoice-receipt-in-thailand/) |
| 泰语数字 | 万进制 ร้อย/พัน/หมื่น/แสน/ล้าน;泰数字 ๐-๙ 在正式/会计文档常用;佛历 +543 | [thai-language.com](http://www.thai-language.com/ref/numbers) |
| 泰语 NLP 分词 | **连写无空格(scriptio continua),分词是核心难题**;歧义+OOV(เห็นชอบ=เห็น+ชอบ);正规需 PyThaiNLP/DeepCut,正则"简单词法"不够 | [NLP for Thai](https://nlpforthai.com/tasks/word-segmentation/) · [Syllable-based Thai WS (COLING'20)](https://aclanthology.org/2020.coling-main.407.pdf) |
| 票据抽取评测 | 行业标准 = **字段级 F1**(SROIE:company/date/total/address 逐字段 precision/recall/F1 + tree-edit-distance)·不是笼统对错 | [SROIE survey](https://www.researchgate.net/publication/358405430_A_Survey_on_Scanned_Receipts_OCR_and_Information_Extraction) · [KIEval](https://arxiv.org/pdf/2503.05488) |

---

## 2. 由调研推导的测试要求

### R1 · 评测口径 = 字段级 F1(取代笼统 pass/fail)
不再只问"记没记对",按**每个字段**算 precision/recall/F1。文本路的规范字段:
`amount(total)` / `vendor(company)` / `date` / `invoice_number` / `tax_id` / `vat` / `category` / `line_items`。
- 每条用例标注**期望字段值**(可为空);跑完算每字段 F1 + 漏报/误报。
- `amount` 的 F1 是护城河(伤账),单列;`vendor/date/invoice` 容许略低。

### R2 · 泰国税票字段覆盖(§86 13 字段)
- **VAT 分列**:`ราคา 100 vat 7%` → amount=100/107,**绝不把税率 7 当金额**(已修)。`รวม vat 107`→107。
- **13 位税号**不当金额(已修)·序列发票号(IV68/0091)单列不当额(已修)。
- **全票 vs 简式票**:简式票(ใบกำกับภาษีอย่างย่อ·7-11 小票)免买家信息+可不拆 VAT → `invoice_number/buyer` 可空不算错;全票要求 13 位税号+VAT 分列。测试按票型分别判,不能拿全票标准卡简式票。
- **佛历日期**(2567)→ 公历 −543(已修)·泰文月(15 ม.ค. 68)(已修)。

### R3 · 泰语数字体系
- **泰数字 ๐-๙**:`๕๐`→50(已做·数字符号非词子串·安全)。
- **量级词**:`Nร้อย/Nพัน/Nหมื่น/Nแสน/Nล้าน`(数字+量级·已做)。
- **拼写数字**(ห้าสิบ/สองร้อย):见 R4 —— 分词难题,**不用正则**。

### R4 · 泰语分词边界(调研定的"做不到的诚实线")
调研结论:`ห้า`(5)是 `ห้าง`(商场)子串、`สาม`(3)是 `สามารถ`(能够)子串、`เก้า`(9)是 `เก้าอี้`(椅子)子串。
**正则做拼写数字/型号数字(M150·100พลัส)会把词拆错** → 归 **Tier B 真大脑**(或将来接 PyThaiNLP 分词),
不在确定性层硬解。测试里这两类标 `expect=brain`(确定性层判 SKIP,真大脑层判对错)。

### R5 · 对抗/合规(承接 04/08)
噪声数字不当金额、问句/否定/假设不记、伪造票据/逃税拒绝、外币不当 THB、引导贴身 —— 已落地,进回归。

---

## 3. 跑法(按要求落到 harness)

1. **确定性层(Tier A)**:对每条用例算字段级值,与期望比 → 输出字段 F1 表(R1)。`expect=brain` 的跳过。
2. **真大脑层(Tier B)**:跑 `expect=brain`(拼写数字/型号)+ 回复内容侧(诚实/语言/引导)。
3. **报告**:字段 F1 表(amount 单列)+ 按票型(全票/简式)分组 + 残留(brain 类)清单。

字段 F1 模板:
```
字段        precision  recall  F1    样本
amount        0.99      0.98   0.985  N    ← 护城河·最高
vendor        0.92      0.85   0.88
date          0.95      0.90   0.92
invoice_no    0.88      0.80   0.84   (简式票豁免后)
tax_id        0.97      0.95   0.96
vat           0.99      0.97   0.98   ← 税率不混进金额
残留(brain):拼写数字 K 条 · 型号数字 M 条 → 交 Tier B
```

---

## 4. 残留的研究背书(为什么不在确定性层做)

| 残留 | 调研定性 | 处置 |
|---|---|---|
| 拼写数字 ห้าสิบ→50 | 分词歧义(ห้า⊂ห้าง)·正则不安全 | Tier B 大脑 / 将来 PyThaiNLP |
| 型号数字 M150/100พลัส→记型号 | 同上(数字粘词·分词问题) | Tier B 大脑 / 型号词典 |
| 倒签 สร้างบิลย้อนหลัง | 语义歧义(正当补开 vs 造假) | Tier B 大脑判语境 |

> 这些不是"没做",是**调研证明确定性层做不对**。硬上正则会制造新 bug(把商场名/能力词转成数字),
> 比漏掉更糟。正确路径 = 真大脑(已有 Gemini 通道)或接 PyThaiNLP 分词器。
