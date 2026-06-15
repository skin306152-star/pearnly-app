# 09 · LINE 进票据识别 · 识别核心规格(施工单)

> **状态**:施工单 · 给 code 窗口"一步做对",附 prod 实测数据(§1)当依据。
> **前置读**:`14-line-quick-entry-spec`(流程外壳:Flex 卡/草稿/文本解析)+ 本文(识别核心 —— 外壳 spec **没有**覆盖"识别本身怎么又快又准")。
> **高敏**:OCR 主路径 + 计费(铁律 #26)→ 改触发/超时/模型先自跑真账号 E2E 验过再 push。
> **升级臂 env 五处共用**(见 §3.4),改模型默认要五处一起回归。

---

## 0. 为什么有这份(背景)

LINE 图片票走的是**完整 pipeline**(L1 Google Vision → L2 Flash-Lite 从文本抽字段 → L3 Flash 视觉兜底),已上线:`services/ocr/line_image_ocr.py` → `services.ocr.entrypoints.run_pipeline_for_file`。

原计划(spec 14)只写了"流程外壳"。**"识别本身又快又准"这层核心逻辑,计划里一个字都没有。** 照外壳建好后,一接真实热敏小票就会慢且(偶尔)不准。本文锁住这层逻辑,防丢。

---

## 1. prod 实测(2026-06-15 · SG 真机 · 真 pipeline 端到端 · 5 张真实泰国票)

票样:1 张电子完整税票(SINCERE)+ 4 张手机拍的热敏小票(7-11 / Kodtalay / Punthai / Bangchak)。

| 票 | 总耗时 | 走的链 | L3 触发原因 | 最终字段是否对 |
|---|---|---|---|---|
| SINCERE(完整税票·电子) | **70.3s** | L1→L2→**L3(61.5s)** | 发票号词置信 0.722<0.85 | 全对(发票号/日期/金额) |
| 7-11(简式 อย่างย่อ) | **21.2s** | L1→L2→**L3(18.5s)** | invoice_number missing | 全对(L3 补回了号) |
| Kodtalay(收据) | **2.1s** | L1→L2 | (未触发) | 全对 |
| Punthai(简式 ABB) | **17.8s** | L1→L2→**L3(15.7s)** | 金额不平(L2 把 56.07 读成 55.07)+ 低置信 | L3 修对了金额+号 |
| Bangchak(加油刷卡 slip·非税票) | **12.1s** | L1→L2→**L3(9.0s)** | invoice_number missing + 税号非法 | 号=None(本就没有) |

**核心读数**:5 张里 **4 张触发 L3,单张 9–61 秒**,只有 Kodtalay 没触发(2.1s)。**→ L3 对真实小票是常态,且慢到不可用。**

**关键结论(纠正早前判断)**:
- **问题是速度,不是准确率。** 字段最终都对;佛历→公历转换 **pipeline 里已正常**(28/2/2569→2026、09/06/69→2026、24/08/25→2025)。
- 早前一个"直接喂图(image-first)"的基准曾显示 2.5-flash 读残小发票号、认错年份 —— 那**不代表 LINE 实际路径**。LINE 走 Vision 文本路,发票号来自 Vision(实测 Vision 读小字 4/4 对),是准的。**所以:别换主模型、别走 image-first、别重写日期。**

---

## 2. 诊断:L3 为什么白触发(逐条)

触发逻辑在 `services/ocr/triggers.py::_evaluate_triggers`。

- **SINCERE(白触发)**:Rule 4「字段词级置信 < 0.85」触发,但 Vision/L2 **已读对** `IV69/00179`。热敏/小字置信天然偏低 → 这条让几乎每张小票都白跑一次 L3。**最该改。**
- **7-11(过度触发)**:Rule 1「invoice_number missing」。但这是**简式税票**(ใบกำกับภาษีอย่างย่อ),那个 `R#...` 是 POS 收据流水号、**不是法定发票号**,简式票不能抵进项 VAT、号只作参照 → 不该为"缺号"跑 L3。
- **Bangchak(过度触发)**:加油刷卡 slip,**根本不是税票**(TID/BATCH/TRACE/REF),`28232536` 是卡 TID 被当税号 → 不该跑 L3 找不存在的发票号。
- **Punthai(合理触发)**:Rule 2「金额不平」—— L2 真读错(56.07→55.07),L3 视觉复读修对了。**这是 L3 该干的活,保留。**

---

## 3. 要做的(按杠杆排序 · 附改哪里)

### 3.1 触发器收紧 —— `services/ocr/triggers.py::_evaluate_triggers`  ★最大杠杆(救速度)
- **Rule 4(低词置信,行 174–200)移出 L3 触发**:词置信低、但该值**确实出现在 L1 OCR 文本里**(`check_field_in_l1_text` 通过)→ 只降级为 `yellow_confirm`(UI 让用户确认),**不跑 L3**。低置信+值不在文本里(疑似幻觉,Rule 5)才升级。
- **Rule 1(invoice_number missing,行 157)按文档类型门控**:简式/收据/非税票 缺号 **不触发**(见 3.2)。完整税票缺号仍触发。
- 保留:Rule 2 金额不平、Rule 5 幻觉(值不在 L1 文本)、Rule 7 同页多票候选。

### 3.2 文档类型分流 —— L2 prompt(`services/ocr/layer2_prompts.py`)+ `ThaiInvoice.document_type` / `is_not_invoice`
- 分三类:**完整税票**(เต็มรูปแบบ)/ **简式**(อย่างย่อ / "ABB")/ **非税票**(加油卡 slip:有 TID/BATCH/TRACE、无 13 位卖家税号)。
- **简式 / 非税票**:不为"缺法定发票号"触发 L3;发票号**原样保留(含 `R#`/`Slip`/`REF` 前缀)当去重键,不强制、不校验**。
- **完整税票**:发票号 `เลขที่` + 卖家 13 位税号较真(下游可抵进项 VAT)。
- Bangchak 这类应被判 `is_not_invoice` 或 doc_type=receipt/non-tax → 直接跳 L3。

### 3.3 L3 超时 + 兜底 —— `services/ocr/layer3_fallback.py`
- **⚠️ 修正(2026-06-15 第二轮):15s 太狠,误伤正经 L3 救场 → 已调回 45s。**
  - 90s = 放任(SINCERE 跑 61s);但 15s 又把真该救的票掐断:Punthai 金额修正昨天就跑了 **15.7s>15s**,「总额缺失」的热敏票 L3 也常要 15–60s → 超时兜回 L2 错值/空值 + needs_review = **准确率回退**(用户报「OCR 又不准」真因)。
  - 触发器已收紧(多数票根本不跑 L3),所以**宽松超时只影响少数真救场的票,不拖慢大盘** → `DEFAULT_TIMEOUT_SECONDS=45`(env `OCR_L3_TIMEOUT_SECONDS` 可调)。
- 超时/失败:`fallback_to_layer2_on_layer3_error`(已有)兜回 L2 结果 + 标 `needs_review`,绝不静默。

### 3.4 升级臂模型(次要)—— `services/ocr/gemini_models.py::fallback()/escalate()`(`OCR_FALLBACK_MODEL` 默认 `gemini-3.5-flash`)
- 触发收紧后 L3 很少跑,模型选择影响变小。**保持 `gemini-3.5-flash`**(实测它读小字发票号最准)+ 上面超时即可。
- 可选 A/B:Haiku 4.5 / `gemini-2.5-flash` 当升级臂(需 Anthropic 余额;2026-06-15 测时那把 key 余额为 0 → Haiku 速度/识别率**未实测**)。
- ⚠️ **此 env 五处共用,改默认要五处回归**:① pipeline L3(`layer3_fallback.DEFAULT_MODEL`)② `services/recon/bank_stmt_gemini.py` ③ `services/recon/bank_gl_gemini.py` ④ `services/ocr/image_first.py`(escalate 臂)。

---

## 4. 别做(防跑偏)

- ❌ 别把主识别换成 image-first / 直接喂图:Vision 文本路才准,直接喂图会把小发票号读残(实测 2.5-flash Punthai → `17818`)。
- ❌ 别重写日期 BE→CE:`date_raw` + 转换**已正常**,别动。
- ❌ 别剥发票号前缀(`R#`/`Slip`/`REF`):是去重键,剥了会误判重复。
- ❌ 别静默给错值:真糊到机器认不出 → `needs_review` 人工兜底。
- ❌ 别碰 firm 路径 / LINE 主 webhook 业务逻辑(铁律 #26)。

---

## 5. 泰国税务规则(影响字段逻辑·别漏)

- **完整税票 vs 简式**:泰国 VAT 法下,**只有完整税票(ใบกำกับภาษีเต็มรูป)能抵进项 VAT**;简式(อย่างย่อ)不能。→ 文档类型决定下游能不能抵税、发票号要不要较真。
- LINE 收到的多是**简式/收据/非税票** → 主要当**费用凭证**收,别强制完整税票的字段(买方税号、法定发票号)。
- `R#` 这种 = POS 收据流水号,非法定税票号;留作去重/溯源,不当必填。

---

## 6. 验收(改完必过)

- 5 张实测票回归:除 Punthai(金额不平·合理触发)外,**L3 不应触发**;快路目标 **<5s/张**。
- Punthai 类(L2 真读错):L3 触发但 **≤15s**,结果修对。
- Bangchak 类:判为 receipt/non-tax,**不跑 L3** 找号。
- 准确率不回退:发票号/金额/卖家税号/日期对照本文 §1「最终字段」。
- 若改升级臂模型:§3.4 五处回归全绿。
- 真账号 LINE 端 E2E + prod 验(铁律 #26)。

---

## 7. 复现实测(给施工窗口自验)

实测脚本思路(prod SG,`/opt/mrpilot/venv` 已含 vision+genai+fitz+PIL):

```
GOOGLE_APPLICATION_CREDENTIALS=/etc/pearnly/pearnly-vision-key.json
PYTHONPATH=/opt/mrpilot  → from services.ocr.pipeline import run_on_image_bytes / run_on_pdf_bytes
逐张打印 pg.layer_chain / pg.trigger_reasons / pg.invoice 字段 / pg.layer3_ms / 总耗时 / estimated_cost_thb
```

票样在 `C:\Users\skin3\Desktop\单据`(4 张热敏)+ `D:\测试PDF\3.69\...SINCERE.pdf`(电子完整票)。
