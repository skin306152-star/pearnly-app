# Pearnly OCR 现状审计(阶段 1)

> 调研日期:2026-05-18
> 范围:Pearnly 后端 OCR 相关代码全貌
> 工作纪律:只读不改;发现 bug / 死代码只记录,**本文档不提删除/修复建议**;新引擎落地后另行讨论

---

## 一、OCR 相关文件清单

### A. 核心 OCR 引擎文件(6 个,用户已点名"只读不改")

| 文件 | 一句话作用 |
|---|---|
| [gemini_engine.py](../../gemini_engine.py) | Gemini 2.5 Flash 主 OCR(图像 → 结构化字段),走自建 Cloudflare Worker 代理 |
| [vision_engine.py](../../vision_engine.py) | Google Vision API(REST,DOCUMENT_TEXT_DETECTION),**仅作 Gemini 失败时的文字兜底** |
| [ocr_engine.py](../../ocr_engine.py) | EasyOCR + 正则字段抽取(本地 CPU)。仅工具函数 `count_pdf_pages` 被业务使用;`recognize_pdf` **仅 engine_chain 调用** |
| [typhoon_engine.py](../../typhoon_engine.py) | Typhoon OCR API(SCB 10X,OpenAI 兼容 SDK),仅供 engine_chain 调用作泰文文字提取器 |
| [nvidia_engine.py](../../nvidia_engine.py) | NVIDIA NIM 统一接入层(classify/reasoning/chat/embed/VL,OpenAI 兼容 SDK);其中 `chat()` 仅 engine_chain 用于字段抽取 |
| [engine_chain.py](../../engine_chain.py) | 3 层降级链编排:Gemini → Typhoon+NVIDIA → EasyOCR |

### B. 业务侧 OCR 调用点(不在 6 引擎里,但 import OCR 或直接 import `google.generativeai`)

| 文件 | 一句话作用 |
|---|---|
| [app.py](../../app.py) | FastAPI 主入口:`/api/ocr/recognize` 主路由 + LINE bot OCR 入口 + 1 处 Gemini key 健康检查 |
| [pdf_text_extractor.py](../../pdf_text_extractor.py) | 电子 PDF 文字层抽取(pypdf + 正则),**零 AI 成本快速通道**,主流程的第一道分流 |
| [email_ingest.py](../../email_ingest.py) | 邮件附件自动 OCR(调 `gemini_engine.recognize_pdf`) |
| [recon_routes.py](../../recon_routes.py) | VAT 对账批量 OCR(并行 20 路 `gemini_engine.recognize_pdf` + `pdf_text_extractor` 快速通道) |
| [bank_recon_v2.py](../../bank_recon_v2.py) | 银行对账:**直接 `genai.GenerativeModel`** ×2(对账单用 flash-lite,GL fallback 用 flash) |
| [vat_excel_export.py](../../vat_excel_export.py) | VAT 公式对账:**直接 `genai.GenerativeModel`** ×2(发票 8 字段抽取,flash) |
| [vat_file_classifier.py](../../vat_file_classifier.py) | 屏 B 文件智能分类(invoice/vat_report,**直接 `genai.GenerativeModel`**,flash) |
| [vat_report_parser.py](../../vat_report_parser.py) | VAT 报告多格式解析,扫描件分支用 **直接 `genai.GenerativeModel`**(flash) |
| [vat_ai_analyzer.py](../../vat_ai_analyzer.py) | VAT 差异原因分析(**直接 `genai.GenerativeModel`**,flash);非 OCR,但占用同 API 配额 |

### C. OCR 下游消费者(只用结果,不调 OCR)

| 文件 | 一句话作用 |
|---|---|
| [invoice_grouper.py](../../invoice_grouper.py) | 把 OCR 多页结果按发票号拆分成多张独立发票 |
| [archive.py](../../archive.py) | 从 OCR fields 生成归档名 |
| [pdf_searchable.py](../../pdf_searchable.py) | (4 新模块)拿 OCR 文本生成可搜索 PDF |
| [pdf_storage.py](../../pdf_storage.py) | (4 新模块)PDF 文件存档,注释提到"OCR 不能因为留底失败而失败" |
| [excel_template_th.py](../../excel_template_th.py) | (4 新模块)用 OCR 数据填 Excel 模板 |
| [xero_pusher.py](../../xero_pusher.py) | (4 新模块)用 OCR 历史推送到 Xero |

---

## 二、引擎清单(详细)

### 1. Gemini 主 OCR(实际承担 99%+ 流量)

- **模型**:`gemini-2.5-flash`(可通过 env `GEMINI_MODEL` 覆盖)
- **调用方式**:`google.generativeai` SDK(REST transport)
- **API Key 来源**:env `GEMINI_API_KEY`,或用户自带(`users.gemini_api_key` / `users.custom_gemini_api_key`)
- **关键基础设施**:走自建 Cloudflare Worker 代理 `gemini-proxy.skin306152.workers.dev`([gemini_engine.py:74](../../gemini_engine.py))
- **关键参数**:温度 0.1,max_tokens 8192,response_mime_type=application/json,DPI 150,单 PDF 内 3 页并发
- **核心入口**:
  - [gemini_engine.recognize_pdf](../../gemini_engine.py) — 主入口(图像 → 完整发票 JSON)
  - [gemini_engine.restructure_with_text_hint](../../gemini_engine.py) — 二次结构化(配合 Vision 文字 hint)
  - [gemini_engine._pdf_to_pil_images](../../gemini_engine.py) — PDF → PIL 图像
- **被业务调用位置**:
  - [app.py:1709](../../app.py) — `/api/ocr/recognize` 主路径
  - [app.py:1731](../../app.py) — Vision 兜底后二次结构化
  - [app.py:5553](../../app.py) — LINE bot OCR
  - [email_ingest.py:288](../../email_ingest.py) — 邮件附件自动 OCR
  - [recon_routes.py:641](../../recon_routes.py) — VAT 对账批量 OCR
- **职责**:接受 PDF bytes,输出与统一 schema 兼容的 pages 数组,每页含 fields + items + token 计费 + is_copy 标记

### 2. Vision API 兜底(仅当 Gemini 失败时)

- **服务**:`https://vision.googleapis.com/v1/images:annotate`
- **调用方式**:`requests` 直接 HTTP POST(**不是 google-cloud-vision SDK**)
- **API Key 来源**:env `GOOGLE_VISION_API_KEY` 或 `GEMINI_API_KEY`(**复用 Gemini 同一 GCP project**)
- **关键参数**:`DOCUMENT_TEXT_DETECTION`,`languageHints=["th","en","zh"]`,200 DPI 渲染
- **核心入口**:[vision_engine.extract_text_from_pdf_bytes](../../vision_engine.py)
- **被业务调用位置**:[app.py:1733](../../app.py) — Gemini 失败时的文字兜底
- **职责**:**仅提取纯文本**,不出字段。后续把文本 + 原图丢回 [gemini_engine.restructure_with_text_hint](../../gemini_engine.py) 二次抽字段
- **注意**:当前架构里 Vision API 没用 confidence、没用坐标信息——只取 `fullTextAnnotation.text` 字符串

### 3. EasyOCR 兜底(本地)

- **库**:`easyocr` 单例懒加载,`['th','en']` 双语,gpu=False
- **核心入口**:[ocr_engine.recognize_pdf](../../ocr_engine.py)
- **被业务调用位置**:**仅 [engine_chain.py:94](../../engine_chain.py) 的 Layer 3 调用**(而 engine_chain 本身无人调,见下)
- **附带工具函数**:[ocr_engine.count_pdf_pages](../../ocr_engine.py) — 这是**唯一被业务实际使用**的函数,[app.py:1524](../../app.py) 与 [email_ingest.py:261](../../email_ingest.py) 用它做页数校验
- **状态**:**`recognize_pdf` 疑似未使用,需 OCR 会话后续确认**

### 4. Typhoon OCR(SCB 10X)

- **模型**:`typhoon-ocr-preview`(env `TYPHOON_MODEL_OCR` 可覆盖)
- **服务**:`https://api.opentyphoon.ai/v1` OpenAI 兼容
- **API Key 来源**:env `TYPHOON_API_KEY`
- **核心入口**:[typhoon_engine.extract_text_from_image](../../typhoon_engine.py)、[typhoon_engine.extract_text_from_pdf_bytes](../../typhoon_engine.py)
- **被业务调用位置**:**仅 [engine_chain.py:69-70, 148-150](../../engine_chain.py)** 调用
- **状态**:**疑似未使用,需 OCR 会话后续确认**(注释也写到 v105 已删除 Typhoon 二次增援,见 [app.py:1783](../../app.py))

### 5. NVIDIA NIM

- **模型**:多个(`llama-3.1-8b-instruct`、`nvidia/llama-3.1-nemotron-70b-instruct`、`meta/llama-3.1-70b-instruct`、`nvidia/nv-embedqa-e5-v5`、`nvidia/llama-3.1-nemotron-nano-vl-8b-v1`)
- **服务**:`https://integrate.api.nvidia.com/v1` OpenAI 兼容
- **API Key 来源**:env `NVIDIA_API_KEY`
- **核心入口**:[nvidia_engine.chat](../../nvidia_engine.py)、[nvidia_engine.embed](../../nvidia_engine.py)、[nvidia_engine.embed_batch](../../nvidia_engine.py)、[nvidia_engine.parse_json_response](../../nvidia_engine.py)
- **OCR 相关被调用位置**:**仅 [engine_chain.py:183-224](../../engine_chain.py)** 用 `chat()` 做 Layer 2 字段抽取
- **状态**:**OCR 用途疑似未使用,需 OCR 会话后续确认**;非 OCR 用途(embed 重复检测、chat 月度总结等)未在本审计范围内核查

### 6. engine_chain.py(降级链编排)

- **设计意图**:Gemini → Typhoon+NVIDIA → EasyOCR 三层兜底,产出多 `engine_chain` / `fallback_used` 字段
- **公开入口**:[engine_chain.recognize_with_fallback](../../engine_chain.py)
- **全项目调用方搜索结果**:`recognize_with_fallback` 仅在定义点出现 1 次;`from engine_chain` / `import engine_chain` 全项目 0 次
- **状态**:**整个模块疑似未使用,需 OCR 会话后续确认**

> 实际生效的兜底链不是 engine_chain,而是 app.py 内联实现的:`text_path → gemini → vision+gemini_restructure`(详见下节业务流程)

### 7. 业务侧 5 处直接 `genai.GenerativeModel` 绕过引擎层

| 文件 | 行 | 模型 | 用途 |
|---|---|---|---|
| [app.py](../../app.py) | 4266 | gemini-2.5-flash | Gemini key 健康检查(只回 "ok",1-2 token) |
| [bank_recon_v2.py](../../bank_recon_v2.py) | 982 | gemini-2.5-flash-**lite** | 银行对账单 OCR(PDF → 交易行 JSON,带 confidence 字段) |
| [bank_recon_v2.py](../../bank_recon_v2.py) | 1830 | gemini-2.5-flash | GL PDF fallback 解析(pdfplumber 解析失败后兜底) |
| [vat_excel_export.py](../../vat_excel_export.py) | 128 | gemini-2.5-flash | 单张发票 8 字段抽取(独立 prompt) |
| [vat_excel_export.py](../../vat_excel_export.py) | 590 | gemini-2.5-flash | 同上,另一处入口 |
| [vat_file_classifier.py](../../vat_file_classifier.py) | 121 | gemini-2.5-flash | 文档类型分类(invoice / vat_report / unknown) |
| [vat_report_parser.py](../../vat_report_parser.py) | 627 | gemini-2.5-flash | VAT 报告 OCR(扫描件分支) |
| [vat_ai_analyzer.py](../../vat_ai_analyzer.py) | 80 | gemini-2.5-flash | 对账差异原因 + 行动建议 + 客户邮件(非 OCR,但走同 Gemini 配额) |

---

## 三、业务流程

### 主流程:POST `/api/ocr/recognize`(app.py:1497)

调用方:Web 前端发票上传。

1. **入口校验** — JWT 取用户 → 校验文件扩展名 `.pdf` → 读 bytes → 校验非空。
2. **配额上限计算**(`_plan_permissions`)— 按用户 plan 算 `max_pages_per_upload` 与 `max_file_size_mb`。
3. **页数 / 文件大小校验** — `from ocr_engine import count_pdf_pages` 算页数;超限抛 `ocr.too_many_pages` / `ocr.file_too_large`。
4. **配额检查**(双轨)— `auth_signup.check_ocr_quota` 新套餐 + `_check_user_quota` 老逻辑;月付超额拒绝。
5. **文件指纹缓存命中**(`db.find_ocr_by_hash`)— SHA-256(file_bytes) 找 30 天内已识别记录。命中:
   - 不计费、不再 OCR,直接返回缓存 pages
   - 仍触发自动推送(LINE/Xero/MR.ERP)、异常检测、写一条 `engine="cache"` 成本日志
   - 流程到此结束
6. **文本路径快速通道**(`pdf_text_extractor.try_text_extraction`)— pypdf 抽文字,平均字符 > 200 视为电子发票:
   - 13 位泰国税号 + `บริษัท` 行 + ลูกค้า 块 + items 正则
   - 严格门槛:`invoice_no + total + seller_tax + buyer_tax` 四件套通过才算
   - 命中:`engine="text"`,0.3 秒一页,**跳过 Gemini**,后续走第 8 步
   - 不命中:静默 fallback Gemini
7. **主引擎 Gemini Flash**(`gemini_engine.recognize_pdf`)
   - 选 key:用户自带 key 优先,否则用系统 `GEMINI_API_KEY`
   - 失败或返回全空 → `gemini_returned_empty` → 进 Vision 兜底:
     - **Vision 兜底**:`vision_engine.extract_text_from_pdf_bytes` 取纯文本
     - 文本 + 原图 一起喂 `gemini_engine.restructure_with_text_hint` 二次抽字段
     - 输出标 `fallback_engine="google_vision"`,chain_info=["gemini_failed","google_vision"]
   - 双失败 → HTTP 500 `ocr.engine_error`
8. **非发票检测** — 所有页 `fields.is_not_invoice=true` → 抛 `ocr.not_invoice`,不入库,不扣配额。
9. **配额扣减** — 多租户走 `db.increment_tenant_monthly_usage`,月付走 `increment_user_monthly_usage`,买断不扣。
10. **置信度评分** — 对每个非副本主页按"发票号+日期+金额+卖方+买方+items"打分,取最高分判定 high/medium/low。副本/重复发票号标 `is_duplicate`。
11. **发票分组**(`invoice_grouper.group_pages_to_invoices`)— 一张 PDF 多张发票时拆分。
12. **写历史 `db.insert_ocr_history`** — 每张发票一条 `ocr_history`:`page_count` / `pages`(JSON) / `confidence` / `elapsed_ms` / `file_size_kb` / `file_hash` / `source="upload"` / `client_id` / `archive_name` / `category_tag` 等。多发票共享 `source_pdf_id`。
13. **成本日志**(`db.log_ocr_cost`)— `engine` / `pages` / `input_tokens` / `output_tokens` / `cost_thb` / `elapsed_ms`,缓存命中也记一条 `engine="cache"` 0 成本。
14. **异步钩子**:
    - `_async_run_exception_checks`(重复发票、异常金额、5 类规则)
    - `_trigger_auto_push_all`(Xero / MR.ERP / 旧 ERP endpoints)
15. **响应** — `{filename, page_count, pages, confidence, history_id, archive_name, quota, from_cache}` 返回前端。

### 次入口 A:LINE bot OCR(app.py:5456 `_handle_line_image_ocr`)

调用方:用户在 LINE 发图给 Pearnly Bot。

1. LINE webhook → 验签 → 取 user_id / 语言
2. 下载图片 bytes → `line_client.image_to_pdf_bytes` 包成 PDF
3. SHA-256 hash → `db.find_ocr_by_hash` 缓存命中处理(同主流程第 5 步)
4. **不走文本路径、不走 Vision 兜底**,直接 `gemini_engine.recognize_pdf(max_pages=1)`
5. 失败:发 `err_ocr` 提示给用户
6. 写 `ocr_history`,`source="line_bot"`
7. 异常检测 + duplicate 检测(同主流程异步钩子)
8. 扣配额(月付)
9. `line_client.format_ocr_result_for_line` 推送结果给用户

**注意**:LINE 入口无 Vision / 文本路径兜底,Gemini 一挂直接失败。

### 次入口 B:邮件附件自动 OCR(email_ingest.py:240+)

调用方:邮箱 ingest 后台任务。

1. 取附件 → 扩展名校验(仅 `.pdf`)
2. `ocr_engine.count_pdf_pages` 校验页数 ≤ 50
3. 优先用 `db.get_user_gemini_key`,否则系统 key;月付检查配额
4. `gemini_engine.recognize_pdf(max_pages=50)`,**无 Vision/文本路径兜底**
5. 扣配额(月付)
6. 写 `ocr_history`,`source="email_ingest"`

### 次入口 C:VAT 对账批量(recon_routes.py:640+)

调用方:VAT 对账批量上传(月度复核场景)。

1. 文件分组 / parse VAT 报告(`vat_report_parser`)
2. 创建 recon task
3. **OCR 阶段**:`asyncio.Semaphore(20)` 并发 20 路:
   - 每张发票先查 hash 缓存
   - 缓存未命中 → 文本路径(`pdf_text_extractor.try_text_extraction`)
   - 文本路径未命中 → `gemini_engine.recognize_pdf` 主引擎(**无 Vision 兜底**)
   - 失败计入 `failed_by_task`,继续跑其他
4. 写 `ocr_history`,`source="vat_recon_batch_text"` / `"vat_recon_batch_cached"` / Gemini 默认

### 次入口 D:银行对账(bank_recon_v2.py)

1. **银行对账单 OCR**(`bank_recon_v2._parse_statement_with_gemini`,line 977)— 直接 `genai.GenerativeModel("gemini-2.5-flash-lite")`,strict prompt 防幻觉,SHA-256 缓存,输出 StatementRow 列表
2. **GL PDF 解析**(`bank_recon_v2._gemini_parse_gl`,line 1822)— 优先 pdfplumber 抽文字 → 失败 fallback `gemini-2.5-flash`,输出 GL 交易行

### 次入口 E:VAT 报告解析(vat_report_parser.py)

1. 文件类型分流:`.xlsx/.xls` → openpyxl;`.pdf 电子` → pdfplumber;`.pdf 扫描/jpg/png` → `gemini-2.5-flash` OCR 专用 prompt

### 次入口 F:VAT 公式对账(vat_excel_export.py)

1. 与 OCR 主路径**完全独立**的发票字段抽取分支
2. 单张发票 8 字段独立 prompt(`buyer_tax_id / buyer_name / buyer_branch / invoice_no / invoice_date / period / amount_pre_vat / vat_amount / total_amount`)
3. ThreadPoolExecutor 并行抽取

### 次入口 G:VAT 文件分类(vat_file_classifier.py)

1. 文件名规则快速判断(零成本)
2. 不确定时 → `gemini-2.5-flash` 看首页轻量分类(invoice / vat_report / unknown)

### 次入口 H:VAT 差异 AI 分析(vat_ai_analyzer.py)

**非 OCR**,但占用同 Gemini 配额。对账差异行 → 给 1 句根因 + 行动建议 + 泰文邮件草稿。

---

## 四、痛点分析

### 1. 成本

- **主链路全量过 Gemini Vision**,单页 ~$0.005(默认 DPI 150 后估算)。缓存 + 文本路径有节省,但所有扫描件 / 手机照片 / 无文本层 PDF 都必须过 Gemini,成本下不来。
- **多个旁路也调 Gemini Flash**:bank_recon_v2 对账单(虽然走 flash-lite 较便宜)、bank_recon_v2 GL fallback、vat_excel_export(×2)、vat_file_classifier、vat_report_parser、vat_ai_analyzer、LINE bot、email_ingest — **总共 9+ 个独立 GenerativeModel() 入口**,缓存/配额各自为政。
- 自建 Cloudflare Worker 代理(`gemini-proxy.skin306152.workers.dev`)为绕区域限制,但同样不能降低 Gemini 单价。

### 2. 准确率

- **单 LLM 模型,无独立字段置信度**。当前 confidence 是 app.py 内基于"字段是否非空"打的启发式分数(0-9),不是 Gemini 给的概率值,**与字符识别质量无直接关系**。
- **金额自洽校验缺失**。`gemini_engine._normalize_fields` 把 `total_amount / subtotal / vat / wht_amount` 全部存下来,但**没有做 `subtotal + vat ≈ total` 的校验**;只有 bank_recon_v2 自己做了类似检查。
- **税号格式校验缺失**。13 位 prompt 里要求了,但没有后处理验证;`pdf_text_extractor` 有 `RE_TAX_ID_TH` 正则,gemini_engine 没有。
- **Vision 兜底丢失信息**:Vision API 本可返回每词坐标 + confidence,当前代码只取 `fullTextAnnotation.text` 字符串(`vision_engine.py:120`),再喂回 Gemini 二次识别 — Vision 的优势完全没用上。
- **多入口字段 schema 不一致**:`gemini_engine` 输出 `seller_tax / buyer_tax`,`vat_excel_export` 输出 `buyer_tax_id`,`pdf_text_extractor` 输出 `seller_tax / buyer_tax` — 跨模块字段名漂移,后续合并困难。
- **LINE 入口无任何兜底**:Gemini 挂直接失败提示给用户,无文本路径、无 Vision、无 EasyOCR。
- **email_ingest 也无 Vision 兜底**:Gemini 挂直接放弃这封邮件附件。

### 3. 速度

- Gemini Flash 单页延迟典型 3-8 秒,单 PDF 内 3 页并发(`gemini_engine.recognize_pdf` 用 `ThreadPoolExecutor(3)`)。
- recon_routes 批量做到 20 路 asyncio 并发,但每路仍受 Gemini 单页延迟约束。
- 自建 Cloudflare Worker 代理引入额外 1-2 跳延迟。
- EasyOCR 首次加载模型 5-10 分钟(目前用不上,但代码里仍有 `_reader_loading` 状态机)。

### 4. 校验与兜底缺失

- **engine_chain.py 整个文件死代码,但仍存在于代码库**(疑似未使用,需 OCR 会话后续确认)。注释提到"v103 · OCR 引擎降级链" — 历史设计未落地或被替换。
- **Typhoon、NVIDIA(OCR 用途)、ocr_engine.recognize_pdf 全部疑似未使用**(需 OCR 会话后续确认)。
- 主流程 `chain_info` 字段(`["text_path"]` / `["gemini"]` / `["gemini_failed","google_vision"]`)记录走了哪条路,但**没有上报到任何监控/数据库** — 失败模式无聚合可见性。
- 没有"低置信度人工复核队列"机制(architecture.md 推荐的)。

### 5. 重复实现

- **正则字段抽取至少出现 3 套**:
  - `ocr_engine.extract_fields`(EasyOCR 配套,基础 4 字段)
  - `pdf_text_extractor._extract_fields_from_text`(电子 PDF 路径,泰文优化、含 items)
  - `gemini_engine._fallback_regex_extract`(JSON 截断兜底)
- **PDF → 图像 转换至少 3 套**:
  - `gemini_engine._pdf_to_pil_images`(150 DPI PIL)
  - `vision_engine._pdf_to_images`(2x matrix PNG bytes)
  - `ocr_engine.pdf_to_images`(200 DPI PNG bytes)
- **页数计数至少 2 处**:`ocr_engine.count_pdf_pages` 用 fitz,`pdf_text_extractor` 用 pypdf
- **JSON 解析容错至少 2 套**:`gemini_engine._parse_json_safely`、`nvidia_engine.parse_json_response`

### 6. 凭证管理

- **现状混乱**:
  - `GEMINI_API_KEY`(系统默认)
  - `GOOGLE_VISION_API_KEY`(可选,fallback 用 Gemini key)
  - `TYPHOON_API_KEY`、`NVIDIA_API_KEY`
  - 用户自带:`users.gemini_api_key` / `users.custom_gemini_api_key`(优先于系统 key)
  - 新方案要引入 `GOOGLE_APPLICATION_CREDENTIALS`(Service Account JSON)— 与现有 `GOOGLE_VISION_API_KEY`(用 GEMINI_API_KEY 兜底)是不同认证体系,需在阶段 2 厘清是替代还是并存

---

## 五、数据库存储结构(从代码观察)

`ocr_history` 表(`db.insert_ocr_history`,`db.find_ocr_by_hash` 调用观察)字段约:

- `id`(主键)
- `user_id`,`tenant_id`(多租户)
- `filename`,`file_size_kb`,`file_hash`(SHA-256,缓存键)
- `page_count`,`pages`(JSON 数组:每页含 `page_number / text / lines / fields / is_copy / is_duplicate / elapsed_ms / input_tokens / output_tokens / error?`)
- `confidence`(high/medium/low,见主流程第 10 步打分)
- `elapsed_ms`
- `source`(upload / line_bot / email_ingest / vat_recon_batch_text / vat_recon_batch_cached / cache)
- `source_ref`(LINE user id / recon task id 等)
- `source_pdf_id`(多发票拆分时同一 PDF 共享)
- `client_id`(右上角客户切换器归属)
- `archive_name`,`category_tag`(归档信息)

`ocr_cost_log` 表(`db.log_ocr_cost`):

- `user_id`,`tenant_id`,`history_id`
- `engine`(gemini / text / cache / google_vision / 未来新引擎)
- `pages`,`input_tokens`,`output_tokens`,`cost_thb`,`elapsed_ms`

**fields JSON 内部 schema**(以 gemini_engine 输出为准,见 `_normalize_fields`):
`invoice_number / date / date_raw / total_amount / subtotal / vat / wht_rate / wht_amount / seller_name / seller_tax / seller_addr / buyer_name / buyer_tax / buyer_addr / notes / items[] / tax_ids[] / is_copy_or_duplicate / is_not_invoice / category`

---

## 六、待后续处理的标注(本文档**不做修复建议**)

记录在此供阶段 2 / 阶段 3 决策参考:

1. **engine_chain.py** 整个文件 — 疑似未使用,需 OCR 会话后续确认
2. **typhoon_engine.py** OCR 主入口 — 疑似未使用,需 OCR 会话后续确认
3. **nvidia_engine.py** OCR 相关用途(`chat` 用于字段抽取)— 疑似未使用,需 OCR 会话后续确认;非 OCR 用途(embed / chat 其他场景)本审计未核查
4. **ocr_engine.py `recognize_pdf`** — 疑似未使用,需 OCR 会话后续确认;`count_pdf_pages` 仍在使用,**继续保留**
5. **Vision API 当前用法仅取 `fullTextAnnotation.text`**,丢弃了 confidence 与坐标信息([vision_engine.py:120](../../vision_engine.py))— 新架构第 1 层的核心增值点正是这两个;待后续处理
6. **LINE 入口无兜底链** — 新架构里如何挂兜底待阶段 2 决策
7. **email_ingest 无 Vision 兜底** — 同上
8. **vat_* 系列 5 处直接 `genai` 调用绕过引擎层** — 是否纳入新架构第 2 层 Flash-Lite 共享路径,需阶段 2 决策(注意:本会话工作纪律明确"vat_excel_* 不碰",所以这部分大概率维持原状,待 OCR 会话后续单独评估)
9. **bank_recon_v2 直接 `genai` 调用** — 同上,工作纪律明确"bank_recon_v2.py 不碰",大概率维持原状
10. **Cloudflare Worker 代理 `gemini-proxy.skin306152.workers.dev`** — 新架构 Vision API 不走代理(直连 vision.googleapis.com),Gemini Flash-Lite 路径是否继续走代理待阶段 2 决策
11. **fields schema 跨模块不一致** — 新架构 pydantic `ThaiInvoice` 应作为统一约定;旧调用方迁移工作量待阶段 2 评估
12. **置信度评分目前是启发式打分**,不是模型给的概率 — 新架构第 1 层 Vision confidence 应直接落到 `pages[].fields[].confidence` 字段,需 schema 扩展

---

## 七、扫描方法学(供复核)

为确保覆盖完整,使用以下 Grep 模式:

1. 引擎模块互调:`engine_chain|gemini_engine|ocr_engine|vision_engine|nvidia_engine|typhoon_engine|report_engine`
2. 三方 AI SDK import:`import google\.|from google\.|import openai|from openai|import anthropic|google\.generativeai|google\.cloud`
3. Gemini 直接调用:`GenerativeModel\(`
4. 引擎降级链调用方:`recognize_with_fallback|from engine_chain|import engine_chain`
5. 各引擎被调位置:`from typhoon_engine`、`from nvidia_engine`、`from ocr_engine`(分别 Grep)
6. FastAPI 路由:`@app\.(post|get|put|delete).*\b(ocr|upload|recognize|extract|invoice|vat|bank|recon)`
7. 4 个新模块 OCR 调用:在 `{pdf_storage,pdf_searchable,excel_template_th,xero_pusher}.py` 内 Grep `vision|gemini|ocr|google\.generativeai|extract_text|recognize_pdf`

扫描范围:项目根 `*.py`,排除 `.git/`、`__pycache__/`、`_pkg/`(旧版本归档)。

---

*阶段 1 完成。等用户审阅后决定是否进阶段 2(对比方案)。*
