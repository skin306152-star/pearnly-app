# Pearnly OCR 推荐架构方案

> 本文档由 Claude(Anthropic) 在多轮深度调研后整理,基于 2026 年 5 月最新的公开数据、benchmark 和价格。
> 用途:给 Claude Code 阅读,作为 Pearnly 产品 OCR 模块重构的目标架构参考。

---

## 一、当前已完成的基础设施(实施前提)

在阅读架构前,先了解已经准备好的资源:

- **GCP 项目**:`Pearnly`(项目 ID:pearnly)
- **试用额度**:$300 USD(显示为 ฿9,751.36,90 天有效,到 2026-08-17 过期)
- **已启用 API**:Cloud Vision API (`vision.googleapis.com`)
- **Service Account**:`pearnly-ocr-sa@pearnly.iam.gserviceaccount.com`
  - 角色:Cloud Vision AI Service Agent (或 Editor)
  - JSON Key:已下载,存放在本地(路径见环境变量)
- **现有的 Gemini API**:走 Google AI Studio,API Key 在原项目环境变量中,继续保留可用
- **业务场景**:泰国会计产品 Pearnly,主要处理泰国发票(印刷件 / 扫描件 / 手机照片 / 电子 PDF 混合)

---

## 二、推荐架构:三层兜底

给你一个我认为对你这个场景(泰国发票为主、混合格式、要做产品)**最性价比的架构**。核心思想:**让便宜的引擎做重活,让贵的引擎只在必要时出手**。

### 第 1 层 — Vision API 做 OCR(全量走这层)

每张图/PDF 页先过 `DOCUMENT_TEXT_DETECTION`,拿到:
- 原始文本(泰文 + 数字)
- 每个字/词的 confidence(0–1)
- 每个字/词的坐标框

### 第 2 层 — Gemini 2.5 Flash-Lite 做字段提取(全量走这层)

把 Vision 输出的纯文本(不是图像)+ 你的 JSON schema 发给 Flash-Lite。它的任务是"把这堆乱序的泰文文本映射成发票字段"。这一步**不看图像,只看文字**,token 消耗极小。

为什么用 Flash-Lite 不用 Flash?因为字符识别这个最难的活已经被 Vision API 做完了,剩下的工作类似"读懂泰文文本然后填表",Flash-Lite 完全够用,而且便宜 3 倍。

### 第 3 层 — Gemini 2.5 Flash(图像)做兜底(只在触发条件时走)

触发条件(任一满足就走):
- Vision API 关键区域 confidence < 0.85(比如金额、税号、日期附近的字)
- Flash-Lite 输出的 JSON 缺关键字段(发票号、总金额任一为空)
- 金额校验失败(小计 + VAT ≠ 总额,差异 > 0.5 泰铢)
- 文档类型不确定

兜底时把**原图 + 第 1 层文本 + 第 2 层 JSON** 一起发给 Flash,让它用视觉重新看一遍,改正错误。

---

## 三、单页成本估算

按一张典型泰国发票(1 页 A4,中等复杂度,约 200 个泰文字符 + 一张商品表)算:

| 步骤 | 操作 | Token/调用量 | 成本/页 |
|---|---|---|---|
| 第 1 层 | Vision API | 1 次调用 | **$0.00150** |
| 第 2 层 | Flash-Lite 结构化 | 输入 ~1500 token + 输出 ~800 token | **$0.00047** |
| 第 3 层 | Flash 视觉兜底(~10% 触发率) | 输入 ~2500 token + 输出 ~1000 token | $0.00325 × 10% = **$0.00033** |
| 合计 | | | **约 $0.0023/页** |

**换算成你熟悉的单位**:
- 1000 页 ≈ **$2.30**(约 ฿80)
- 10000 页 ≈ **$23**(约 ฿800)
- 100000 页/月 ≈ **$230**(约 ฿8000)

---

## 四、能进一步压成本的杠杆

1. **批处理(Batch API)**:Gemini 的 Flash-Lite 和 Flash 都支持 24 小时批处理模式,**价格打 5 折**。如果你的会计场景不是实时的(夜间批跑很正常),这一刀直接砍下来,总成本降到约 **$1.90/1000 页**。

2. **Vision API 前 1000 页/月免费**:小客户免费,大客户也省一点。

3. **Gemini context caching**:如果你的 prompt 和 schema 是固定的(肯定是),把 system prompt 缓存起来,缓存命中部分只要正常价格的 **10%**。每月可以再省 20–30%。

4. **质量好的电子 PDF 直接绕过 OCR**:如果客户上传的是泰国电子发票(e-Tax Invoice,有文本层的 PDF),直接 PDF 文本提取 + Flash-Lite 解析,**完全跳过 Vision API**,这部分文档成本降到 **$0.0005/页**。

加上这些优化,**生产环境真实平均成本可以做到 $1.50–2.00/1000 页**。

---

## 五、对比一下纯方案

| 方案 | 单页成本 | 1000页成本 | 准确率 | 工程量 |
|---|---|---|---|---|
| 纯 Gemini 2.5 Flash(当前) | ~$0.005 | ~$5 | 中(幻觉风险) | 低 |
| 纯 Vision API | $0.0015 | $1.50 | 低(没结构化) | **极高** |
| **推荐混合架构** | **$0.0023** | **$2.30** | **高** | 中 |
| 混合 + Batch + Cache | $0.0017 | $1.70 | 高 | 中 |
| 商业 SaaS(Rossum/Nanonets) | ~$0.05–0.50 | $50–500 | 高 | 极低 |

**关键结论**:混合方案比当前纯 Gemini 方案**便宜一半**、**速度快 3–5 倍**、**准确率更高、可解释**(每个字段都能追溯到 Vision 的坐标和置信度,对会计审计场景很重要)。

---

## 六、几个实战建议

**关于触发兜底的阈值**:刚上线时把第 3 层触发率设到 20–30%(宽松一点),观察数据后再调到 10%。会计场景宁可多花一点钱在兜底上,也别让错误的金额进系统。

**关于人工复核**:即便有第 3 层,建议保留一个"低置信度队列" UI,把第 3 层之后金额校验还是不过的、或者总额超过某个阈值(比如 ฿10000)的发票丢给人复核。会计产品的客户对错误的容忍度是 0,这点工程开销值得。

**关于 Gemini 余额**:不会浪费。第 2 层 Flash-Lite 和第 3 层 Flash 都走原有 AI Studio key,只需要新开 GCP 项目专门做 Vision API,两边各管各的计费。

---

## 七、给 Claude Code 的实施提示

> 以下部分是为辅助实施而补充的工程细节,可与上面的架构方案配合使用。

### 7.1 凭证与环境变量

**Vision API**(走 GCP Service Account):
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/pearnly-vision-key.json
```

**Gemini API**(沿用现有 AI Studio Key,无需变更):
```bash
GOOGLE_API_KEY=<现有的 AI Studio key>
```

两套凭证完全独立,Vision SDK 会自动读 `GOOGLE_APPLICATION_CREDENTIALS`,Gemini SDK 会读 `GOOGLE_API_KEY`,不冲突。

### 7.2 建议的模块结构

```
services/ocr/
├── __init__.py
├── layer1_vision.py        # 第 1 层:Vision API 调用
├── layer2_structure.py     # 第 2 层:Flash-Lite 结构化
├── layer3_fallback.py      # 第 3 层:Flash 视觉兜底
├── pipeline.py             # 编排:调度三层 + 决策何时升级
├── validators.py           # 业务校验:金额一致性、必填字段等
├── schemas.py              # JSON Schema 定义(泰国发票字段)
└── confidence.py           # 置信度计算与触发判断
```

### 7.3 推荐依赖

**Python**:
```
google-cloud-vision>=3.7.0
google-generativeai>=0.8.0       # AI Studio Gemini SDK
pdf2image                         # PDF → 图像(用于 Vision/Flash)
pypdf2 或 pdfplumber              # 电子 PDF 文本层提取(走快速通道)
pydantic>=2.0                     # JSON schema 验证
```

### 7.4 泰国发票字段 Schema(参考起点,根据实际业务调整)

```python
class ThaiInvoice(BaseModel):
    document_type: Literal["tax_invoice", "receipt", "credit_note", "other"]
    invoice_number: str                    # เลขที่ใบกำกับภาษี
    issue_date: date                       # วันที่
    seller_name: str                       # ผู้ขาย
    seller_tax_id: str                     # เลขประจำตัวผู้เสียภาษี (13 位)
    buyer_name: Optional[str] = None
    buyer_tax_id: Optional[str] = None
    line_items: list[LineItem]
    subtotal: Decimal                      # ยอดก่อน VAT
    vat_rate: Decimal                      # 通常 0.07 或 0.00
    vat_amount: Decimal                    # ภาษีมูลค่าเพิ่ม
    total_amount: Decimal                  # รวมทั้งสิ้น
    currency: str = "THB"
    confidence_score: float                # 来自 Vision API 的整体置信度
    needs_review: bool                     # 是否需要人工复核
```

### 7.5 Vision API 调用要点

- 使用 `DOCUMENT_TEXT_DETECTION`(不是 `TEXT_DETECTION`),前者专为密集文本/文档优化
- 设置 `languageHints=["th", "en"]`(泰英混合是泰国发票常态)
- 输出会带 `pages[].blocks[].paragraphs[].words[].symbols[]` 层级结构,每个层级都有 confidence
- 关键字段(金额、税号、日期)的判定应基于"该词在原始文本中所在区域的最小 confidence"而非全局平均

### 7.6 触发第 3 层兜底的精确逻辑

```python
def should_trigger_fallback(vision_result, structured_result) -> bool:
    # 1. 关键区域低置信度
    critical_fields_confidence = extract_confidence_for_amount_regions(vision_result)
    if min(critical_fields_confidence) < 0.85:
        return True
    
    # 2. 必填字段缺失
    if not structured_result.invoice_number or not structured_result.total_amount:
        return True
    
    # 3. 金额自洽性校验
    expected_total = structured_result.subtotal + structured_result.vat_amount
    if abs(expected_total - structured_result.total_amount) > 0.5:
        return True
    
    # 4. 税号格式错误(泰国税号严格 13 位数字)
    if structured_result.seller_tax_id and len(structured_result.seller_tax_id) != 13:
        return True
    
    return False
```

### 7.7 渐进式上线策略(强烈建议)

不要一刀切替换现有 Gemini 方案,按以下顺序:

1. **影子模式(Shadow Mode)**:新架构和旧 Gemini 并行运行,只对比结果,不影响用户。运行 1–2 周收集准确率数据。
2. **小流量切换**:5% 流量走新架构,观察错误率和用户反馈。
3. **逐步扩大**:5% → 25% → 50% → 100%,每个档位至少观察 3 天。
4. **保留紧急回滚开关**:配置一个 feature flag,出问题时一行代码切回旧方案。

---

## 八、可观测性建议

每张发票处理后,记录以下指标到数据库(便于后续优化):

- 文档类型(扫描件 / 照片 / 电子 PDF)
- 是否触发第 3 层兜底
- 触发原因(confidence 低 / 字段缺失 / 校验失败)
- 各层处理耗时
- 各层 token / 调用消耗
- 最终 confidence 评分
- 是否进入人工复核队列

这些数据 1 个月后能告诉你:
- 真实成本是否符合预期
- 第 3 层触发率是不是过高(说明阈值需调整)
- 哪种文档类型最难处理(可针对性优化)

---

## 九、参考数据来源(2026 年公开数据)

- Google Cloud Vision 定价:https://cloud.google.com/vision/pricing
- Gemini API 定价:https://ai.google.dev/gemini-api/docs/pricing
- 泰文 OCR 学术基准:IJECE 2022(Vision API 在泰文车辆登记证准确率 84.43%)
- 发票 OCR benchmark:arxiv.org/abs/2509.04469(Gemini 2.5 在 clean invoices 96.5%, scanned 92.71%)
- LLM vs 传统 OCR 对比:OmniAI OCR Benchmark, Parsli, Vellum 各家公开评测

---

*文档生成日期:2026-05-18*
*目标项目:Pearnly(泰国会计 SaaS)*
*架构作者:Claude (Anthropic),基于多轮调研讨论整理*
