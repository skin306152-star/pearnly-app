# Pearnly OCR 迁移计划(阶段 2)

> 调研日期:2026-05-18
> 输入:[architecture.md](./architecture.md) 推荐三层架构 + [current-architecture.md](./current-architecture.md) 现状审计
> 工作纪律:**不动任何项目代码**;`bank_recon_v2 / vat_excel_* / vat_file_classifier / vat_report_parser / vat_ai_analyzer` 等 9+ 处直调 `genai` 的模块**不在本次迁移范围**

---

## ✅ 用户已确认决策(2026-05-18)

> 阶段 2 评审后用户拍板的 5 项决策。**所有后续实施按此为准**,不再讨论。其余 8 个非阻塞疑问推迟到阶段 3 触及时再具体讨论。

### 决策 1 · 凭证体系与并存策略(回应 A1/A2/A3)

- **SDK 选择**:用 `google-cloud-vision` SDK + 独立 Service Account,**不**继续走 REST + Gemini key
- **旧 `vision_engine.py`(REST + `GOOGLE_VISION_API_KEY`)保留不动**
- **并存期**:开发期完全并存(旧代码用于对比测试,feature flag 切换);**新 pipeline 开发完成且测试通过后,直接全量切换,旧代码立刻删**(开发阶段无真实用户,无需灰度 / Shadow)
- **Service Account JSON 路径(用户已确认)**:
  - **本机(Windows 开发机)**:`C:\Users\skin3\.gcp\pearnly-vision-key.json`
  - **服务器(`45.76.53.194`,Linux)**:`/etc/pearnly/pearnly-vision-key.json`
- **统一通过 env 变量 `GOOGLE_APPLICATION_CREDENTIALS` 指向**,代码里不出现绝对路径
- **必须先做连通性测试**:新增**前置任务 0**(`connectivity_check.py`),阶段 3 实质开发前先在**本机 + 服务器**都跑通,确认能直连 `vision.googleapis.com`(不走 Cloudflare proxy)。详见 §七

### 决策 2 · 字段 schema 命名(回应 B1)

- **选 `seller_tax / buyer_tax`(完全兼容旧 gemini_engine schema)**
- 理由:下游 [mrerp_xlsx_generator.py](../../mrerp_xlsx_generator.py) 等已用 `seller_tax / buyer_tax` 在生产,改名违反"本次不碰下游"纪律
- `seller_tax_id / buyer_tax_id` 留给**未来统一改造**(本次 architecture.md 推荐的命名暂不采用)
- 落地影响:`services/ocr/schemas.py` 的 `ThaiInvoice` 用 `seller_tax / buyer_tax`(覆盖 architecture.md §7.4 的推荐 schema)
- 选项 A/B/C 中**选 A 完全兼容**

### 决策 3 · 测试样本策略(回应 E1)

- **`storage/pdfs/` 是真实用户数据,绝不进 git**
- **本地阶段 3 调试**:可直接用 `storage/pdfs/` 跑,只在开发机本地
- **正式 fixtures**:阶段 3 第 1 步后期补 — 手动挑 **5-10 张代表性样本**(发票 / 收据 / 扫描件 / 手机照片各类型),**脱敏后**(假姓名 / 假税号 / 假金额)放 `tests/fixtures/`
- **阶段 3 第 1 步先用 `storage/pdfs/` 本地跑通**,正式 fixtures 后期补
- `.gitignore` 必须包含 `storage/`(若未含)

### 决策 4 · 错误处理(开发期 + 全量切换两段,回应 G1)

**核心原则:用户不应因换引擎感到任何异常**(开发阶段虽无真实用户,保留此原则给上生产时复用)

| 阶段 | feature flag | 三层全失败时行为 |
|---|---|---|
| 开发期(旧代码并存) | `OCR_USE_NEW_PIPELINE` 可切 `true/false` 对比测试 | **自动回退到旧 gemini_engine**;同时记日志便于排查 |
| 全量切换后(旧代码已删) | 默认 `true`(实际旧代码已不存在) | 写入**"低置信度队列"**等人工复核,返回**部分结果**给用户(已从前两层拿到的字段先返回) |

落地影响:
- `pipeline.run(...)` 输出带 `needs_manual_review: bool` 标记
- 开发期 app.py 接入代码(伪):
  ```python
  if os.environ.get("OCR_USE_NEW_PIPELINE", "false").lower() == "true":
      try:
          result = pipeline.run(...)
      except Exception:
          result = gemini_engine.recognize_pdf(...)  # 开发期兜底
  else:
      result = gemini_engine.recognize_pdf(...)
  ```
- 全量切换后:删除 else 分支 + try/except 兜底,改为低置信度队列写入(具体 schema 待阶段 3 后期讨论)

### 决策 5 · 死代码清理时机(原决策 6)

死代码 `engine_chain.py / typhoon_engine.py / nvidia_engine.py / ocr_engine.recognize_pdf` 处置权归本会话。**新 pipeline 开发完成、测试通过、全量切换后立刻清理**(与决策 1 的"直接切换"对齐)。同时清理:
- 旧 `gemini_engine.recognize_pdf`(主 OCR 旧实现)
- 旧 `vision_engine.py`(REST 旧实现)
- app.py 内联兜底链(`/api/ocr/recognize` 70 行 + LINE / email / recon_routes 各入口的 else 分支)

**保留**:
- `ocr_engine.count_pdf_pages`(工具函数)
- `pdf_text_extractor`(被新 `services/ocr/text_path.py` 包装复用)
- `gemini_engine._normalize_thai_date` 等纯函数(搬到 `services/ocr/normalizers.py` 后再删原位置)
- `gemini_engine.py` 中提供 Flash-Lite / Flash 调用基础设施的部分(由 `services/ocr/llm_client.py` 决定是否完全取代)

---

## 一、新架构理解(用自己的话复述)

### 核心思想

**让便宜的引擎做重活,让贵的引擎只在必要时出手**。本质是把"看图像识别字符"和"读文字填表"这两件事拆开——前者是 OCR 真正的难点(Vision API 在泰文上准确率约 84%,但比 LLM 强在能给每个字符的坐标和置信度),后者其实是个"读懂泰文然后填 JSON"的轻量任务,用 Flash-Lite 完全够用。

当前架构的根本毛病是:**用 Gemini Flash(带视觉,贵)做了从字符识别到字段抽取的全流程**,既贵又拿不到独立的字段置信度。

### 三层职责

**第 1 层 · Cloud Vision API · 全量过**
- 输入:图像 / PDF 页(PDF 先 pdf2image 转成图)
- 工具:`google-cloud-vision` SDK,`DOCUMENT_TEXT_DETECTION`(不是 `TEXT_DETECTION` — 后者只适合稀疏文本)
- 输出:每页带 5 层嵌套(`pages → blocks → paragraphs → words → symbols`),**每层都有 confidence 和坐标框**
- 配置:`languageHints=["th","en"]`(泰国发票常见双语)
- 凭证:GCP Service Account JSON,env `GOOGLE_APPLICATION_CREDENTIALS`
- 单页成本:**$0.00150**(前 1000 页/月免费)

**第 2 层 · Gemini 2.5 Flash-Lite · 全量过**
- 输入:第 1 层的纯文本 + 我们定义的 JSON Schema
- 输出:符合 `ThaiInvoice` pydantic 的结构化字段
- 关键约束:**这一步不看图,只看文字**,所以 input token 极小(估 1500 token)
- 凭证:沿用现有 `GEMINI_API_KEY`(AI Studio key)
- 单页成本:**$0.00047**

**第 3 层 · Gemini 2.5 Flash 视觉兜底 · 仅触发时(~10%)**
- 输入:原图 + 第 1 层文本 + 第 2 层 JSON
- 输出:重抽过的字段 JSON
- 触发条件(任一满足):
  1. Vision 关键区域 confidence < 0.85(金额 / 税号 / 日期 附近)
  2. Flash-Lite 输出缺关键字段(`invoice_number` 或 `total_amount` 任一为空)
  3. 金额校验失败(`subtotal + vat_amount ≠ total_amount`,差异 > 0.5 THB)
  4. 税号格式异常(非 13 位数字)
- 凭证:同第 2 层
- 单页成本(按 10% 触发率均摊):**$0.00033**

### 关键设计选择(我的理解)

- **置信度从模型出处直接给**:第 1 层 Vision 给每字符 confidence,第 2 层 Flash-Lite 失败重试,第 3 层覆盖 → 字段级 confidence 0-1 浮点数,**不再用 high/medium/low 启发式**
- **触发兜底的决策是确定性算法**,不是 LLM 自评 — 写成代码可单测
- **可追溯**:每个字段能回到 Vision 原始 word 的坐标和 confidence,审计场景刚需
- **渐进式上线**:Shadow → 5% → 25% → 50% → 100%,每档观察 3+ 天,保留 feature flag 一行回滚

---

## 二、当前 vs 推荐 — 文件 / 函数级对照

### A. 旧引擎文件(6 个 + pdf_text_extractor)

| 当前(文件:行 / 函数) | 推荐架构对应 | 动作 | 备注 |
|---|---|---|---|
| [vision_engine.py](../../vision_engine.py) 整个文件(REST + Gemini key) | `services/ocr/layer1_vision.py`(SDK + Service Account) | **新写并行**,旧文件保留运行直到 100% 切流量 | 凭证体系完全不同,不能直接改 |
| [vision_engine.py:120](../../vision_engine.py) `text = full_annotation.get("text", "")` 丢弃 conf+坐标 | `layer1_vision.extract()` 返回完整 `pages[].blocks[].paragraphs[].words[].symbols[]` + confidence + bbox | **新代码不丢**,问题不复现 | 阶段 1 痛点 ② 核心修复点 |
| [vision_engine._vision_extract_image](../../vision_engine.py) | `layer1_vision._call_vision_api` | 重写,SDK 调用 + Service Account | |
| [gemini_engine.recognize_pdf](../../gemini_engine.py)(一次 LLM 看图取字段) | 拆分成 layer1 + layer2(+ 可选 layer3) | **保留运行** + 新管道并行 | shadow mode 对照基准 |
| [gemini_engine.restructure_with_text_hint](../../gemini_engine.py)(被 app.py:1731 Vision 兜底后调用) | `services/ocr/layer3_fallback.refine_with_image` | 等价职责,但有完整 confidence 数据可驱动 | 旧函数继续保留 |
| [gemini_engine._pdf_to_pil_images](../../gemini_engine.py) | `services/ocr/pdf_utils.py` 内部复用 | 可考虑直接 import,不重复实现 | 注意 DPI:旧 150,Vision 推荐 200+ |
| [gemini_engine._parse_json_safely](../../gemini_engine.py)(JSON 容错 3 步走) | `services/ocr/json_utils.py` 或 layer2 内嵌 | 可移植 / 重写,逻辑必要 | pydantic 严格 schema 会减少这种需求 |
| [gemini_engine._fallback_regex_extract](../../gemini_engine.py)(JSON 截断兜底) | (不需要) | layer2 用 pydantic 强 schema + Flash-Lite retry,不再写正则兜底 | |
| [gemini_engine._normalize_fields](../../gemini_engine.py)(字段名统一 / 佛历转公历 / items 去重) | 拆三处:`schemas.py` 字段名;`services/ocr/normalizers.py` 佛历;`validators.py` items 去重 | 逻辑要继承,拆开放更清晰 | |
| [gemini_engine._normalize_thai_date](../../gemini_engine.py) | `services/ocr/normalizers.thai_to_gregorian` | 直接搬过去,纯函数 | |
| [pdf_text_extractor.try_text_extraction](../../pdf_text_extractor.py)(pypdf 文字 + 正则字段) | `services/ocr/text_path.py` 包装 | **拆开**:pypdf 文字抽取保留;字段抽取改走 layer2 Flash-Lite | architecture.md §四 ④"电子 PDF 跳过 Vision" 走文本层 |
| [pdf_text_extractor._extract_fields_from_text](../../pdf_text_extractor.py)(正则字段) | (退役) | 替换为 Flash-Lite,但**旧函数保留**做 shadow 期 baseline 对照 | |
| [ocr_engine.count_pdf_pages](../../ocr_engine.py) | 直接 import 复用 | **保留,不动** | 工具函数,无需重复实现 |
| [ocr_engine.recognize_pdf](../../ocr_engine.py)(EasyOCR + 正则) | (将废弃) | 按用户决定 1,阶段 3 收尾时清理 | |
| [engine_chain.recognize_with_fallback](../../engine_chain.py) 整个文件 | `services/ocr/pipeline.run` 完全替代 | 按用户决定 1,阶段 3 收尾时清理 | 死代码 |
| [typhoon_engine.py](../../typhoon_engine.py) 整个文件 | (将废弃) | 按用户决定 1,阶段 3 收尾时清理 | 死代码 |
| [nvidia_engine.py](../../nvidia_engine.py)(OCR 用途 `chat` for 字段抽取) | (将废弃) | 按用户决定 1,阶段 3 收尾时清理 | 死代码;非 OCR 用途(embed)不归本会话 |

### B. 业务侧接入点(app.py 主流程 + 3 个次入口)

| 当前 | 推荐 | 动作 |
|---|---|---|
| [app.py:1689-1761](../../app.py) `/api/ocr/recognize` 主流程内联兜底链(`text_path → gemini → vision_fallback`,约 70 行) | 替换为 `pipeline.run(content, max_pages, api_key, ...)` 单行调用 | **修改 app.py**(必须),feature flag 包裹,旧链路保留可一键回滚 |
| [app.py:5552-5560](../../app.py) `_handle_line_image_ocr` 直接 `gemini_engine.recognize_pdf`(无兜底) | 替换为 `pipeline.run`,获得三层兜底 | 同上,LINE bot 入口同步切 |
| [email_ingest.py:286-296](../../email_ingest.py) 直接 `gemini_engine.recognize_pdf`(无兜底) | 同 LINE | 同上 |
| [recon_routes.py:640-700](../../recon_routes.py) 批量 OCR(`text_path → gemini`,无 vision) | 同 LINE | 同上;并发 20 路要确认 pipeline 抗得住 |
| [app.py:1524](../../app.py) `count_pdf_pages` 校验 | 不变 | 继续用 [ocr_engine.count_pdf_pages](../../ocr_engine.py) |
| [app.py:1693](../../app.py) `pdf_text_extractor.try_text_extraction` 文本路径 | 在 pipeline 内部决策(text path vs vision)| 不再由 app.py 自己判断,pipeline 接管 |
| [app.py:1730-1733](../../app.py) Vision 兜底分支 | 在 pipeline 内部决策(layer3 触发逻辑) | 不再由 app.py 自己判断 |
| [app.py:1722-1782](../../app.py) `is_not_invoice` 检测 + 配额扣减 + 置信度评分 + invoice_grouper + history 写入 + 异常 hook + 自动推送 | **完全保留** | pipeline 只接管"OCR 引擎层",app.py 仍负责"业务编排" |

### C. 不在本次迁移范围(9+ 处直调 genai)

| 文件 | 备注 |
|---|---|
| [bank_recon_v2.py:982, 1830](../../bank_recon_v2.py)(银行对账单 + GL fallback) | 工作纪律明确**不碰**;未来可考虑迁到 `pipeline.run_for_module(...)` 共享路径 |
| [vat_excel_export.py:128, 590](../../vat_excel_export.py)(VAT 公式对账,发票 8 字段抽取) | 同上 |
| [vat_file_classifier.py:121](../../vat_file_classifier.py)(文件类型分类) | 同上 |
| [vat_report_parser.py:627](../../vat_report_parser.py)(VAT 报告扫描件分支) | 同上 |
| [vat_ai_analyzer.py:80](../../vat_ai_analyzer.py)(非 OCR 的差异分析) | 非 OCR,本次不涉及 |
| [app.py:4266](../../app.py)(Gemini key 健康检查,1-2 token) | 微量,本次不涉及 |

> **统一这些 5 处的工程在阶段 3 收尾或更后期单独立项**,本次只确保新 pipeline 的接口设计**支持未来接入**(例如 `pipeline.run(..., output_schema=SchemaB)` 可换 schema)。

### D. OCR 下游消费者(只读 OCR fields,不调 OCR)

| 文件 | 读取来源 | 影响评估 |
|---|---|---|
| [invoice_grouper.py](../../invoice_grouper.py) | `pages[].fields.invoice_number` | 字段名不变则零影响 |
| [archive.py](../../archive.py) | 多个 fields(归档名模板) | 字段名不变则零影响 |
| [pdf_searchable.py](../../pdf_searchable.py)(4 新模块) | `pages[].raw_text` / `pages[].text` | 字段不变零影响 |
| [pdf_storage.py](../../pdf_storage.py)(4 新模块) | 仅 PDF bytes,不读 fields | 零影响 |
| [excel_template_th.py](../../excel_template_th.py)(4 新模块) | `pages[].fields` | 字段名不变则零影响 |
| [xero_pusher.py](../../xero_pusher.py)(4 新模块) | `history.fields` | 字段名不变则零影响 |
| [mrerp_xlsx_generator.py](../../mrerp_xlsx_generator.py)(新拉回,本会话刚发现) | `pages[].fields.invoice_number / invoice_date / items[].name / items[].subtotal / total_amount` 等 | **必须确认字段名兼容**;此模块用 OCR `item_name → ERP product code` 映射 |

---

## 三、迁移变更清单

### 3.1 新增依赖(`requirements.txt`)

```
google-cloud-vision>=3.7.0      # 第 1 层 Vision SDK
pdf2image                        # PDF → 图像(可选,可继续用 fitz/PyMuPDF)
pydantic>=2.0                   # 第 2/3 层 schema 校验(可能项目已有,需 grep 确认)
```

不变 / 保留:
- `google-generativeai`(已有,Flash-Lite + Flash 用)
- `pypdf`(已有,text_path 用)
- `PyMuPDF (fitz)`(已有,PDF 渲染用)
- `requests`(已有,旧 vision_engine.py 仍可保留)
- `openai`(已有,旧 typhoon/nvidia 保留期间不动)

### 3.2 新增环境变量

```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/pearnly-vision-key.json
OCR_USE_NEW_PIPELINE=false       # 唯一开关 · false=旧 gemini · true=新 pipeline · 开发期可手动切换对比
OCR_FLASHLITE_MODEL=gemini-2.5-flash-lite   # 可覆盖
OCR_FLASH_MODEL=gemini-2.5-flash             # 可覆盖
```

保留不变:
- `GEMINI_API_KEY`(第 2/3 层 + 旧 gemini_engine 共用)
- `GOOGLE_VISION_API_KEY`(旧 vision_engine.py 继续可用,过渡期保险)

**注**:不再用灰度百分比 / 白名单 / Shadow 三套机制 — 用户当前是开发阶段无真实用户,**单一 boolean 开关足够**(决策 5)

### 3.3 新增文件(`services/ocr/` 目录)

| 文件 | 职责 | 优先级 |
|---|---|---|
| `services/__init__.py` | 包标记 | 必需 |
| `services/ocr/__init__.py` | 包标记 + 导出 `pipeline` | 必需 |
| `services/ocr/layer1_vision.py` | Vision API DOCUMENT_TEXT_DETECTION 调用,返回完整 pages[].words[].symbols[] + confidence + bbox | **阶段 3 第 1 个原子任务** |
| `services/ocr/layer2_structure.py` | Flash-Lite 接受文本 + 默认 schema,输出 `ThaiInvoice` | 阶段 3 第 2 步 |
| `services/ocr/layer3_fallback.py` | Flash 视觉兜底,接受原图 + layer1 text + layer2 fields | 阶段 3 第 3 步 |
| `services/ocr/pipeline.py` | 三层编排 + 触发决策 + 错误处理 + cost 累计 | 阶段 3 第 4 步 |
| `services/ocr/schemas.py` | pydantic `ThaiInvoice`、`LineItem`、`PageConfidence`、`PipelineResult` | 阶段 3 第 2 步前置 |
| `services/ocr/validators.py` | 金额自洽、税号 13 位、必填字段、items 去重(从 gemini_engine 搬过来) | 阶段 3 第 3 步前置 |
| `services/ocr/confidence.py` | 关键区域置信度计算(金额 / 税号 / 日期 附近 word 的 min conf);Vision pages → bbox → 字段映射 | 阶段 3 第 3 步前置 |
| `services/ocr/text_path.py` | 复用 [pdf_text_extractor](../../pdf_text_extractor.py) 文字抽取,字段抽取改走 layer2 | 阶段 3 后期(主路径接入后) |
| `services/ocr/normalizers.py` | 佛历→公历(从 [gemini_engine._normalize_thai_date](../../gemini_engine.py) 搬)、数字 / 税号清洗 | 阶段 3 第 2 步前置 |
| `services/ocr/pdf_utils.py` | PDF→PIL/bytes(可考虑直接 import 旧 `_pdf_to_pil_images`) | 工具,可后置 |
| `services/ocr/llm_client.py`(可选) | Flash-Lite + Flash 共享客户端,带 context cache / batch / retry | 性能优化,可后置 |
| `tests/test_vision_layer.py` | 用 storage/pdfs/ 脱敏后样本测 layer1 | 阶段 3 第 1 步配套 |
| `tests/test_pipeline_e2e.py` | end-to-end:输入 PDF → 输出 ThaiInvoice + confidence + 触发记录 | 阶段 3 第 4 步配套 |
| `tests/fixtures/` | 脱敏后的样本 PDF / 图片 | 阶段 3 第 1 步前 |

### 3.4 修改文件(必须改)

| 文件 | 改动概要 | 估算行数 |
|---|---|---|
| `requirements.txt` | 加 3 个依赖 | 3 行 |
| `.env` / 部署 env | 加 5 个环境变量 | 5 行 |
| [app.py](../../app.py) `/api/ocr/recognize` 主路由(`1689-1761`) | 用 `OCR_USE_NEW_PIPELINE` 包裹:`if env_flag: result = pipeline.run(...) else: 旧 70 行` | ~80 行变 ~15 行(加 if/else) |
| [app.py](../../app.py) `_handle_line_image_ocr`(`5552-5560`) | 同上 feature flag | ~10 行 |
| [email_ingest.py](../../email_ingest.py)(`286-296`) | 同上 feature flag | ~10 行 |
| [recon_routes.py](../../recon_routes.py)(`640-700`) | 同上 feature flag(并发 20 路保持) | ~15 行 |
| [db.py](../../db.py) `log_ocr_cost` | engine 字段接受新值,可能加 `layer_breakdown` JSON 列 | 视决策而定 |

### 3.5 不修改的文件(纪律保护)

- 6 个旧 OCR 引擎(gemini_engine / vision_engine / ocr_engine / typhoon_engine / nvidia_engine / engine_chain)
- bank_recon_v2.py / vat_excel_*.py / vat_file_classifier.py / vat_report_parser.py / vat_ai_analyzer.py
- auth_signup.py / db.py 核心结构(只可能加列)
- pdf_text_extractor.py(新 text_path.py 包装它,不改它本身)

### 3.6 DB schema 改动

**最小改动方案**(推荐起步):
- `ocr_history.pages[].fields` JSONB 内**新增**`_confidence`子字典:`{invoice_number: 0.94, total_amount: 0.87, ...}`
  - 旧消费者不读这个键,**零兼容性问题**
  - 新前端可读它做"低置信度高亮"
- `log_ocr_cost.engine` 字段接受新值:`"pipeline_v1"`
  - 表本身不变,只是值多了

**可选改动**(待用户决定):
- 新增 `ocr_pipeline_audit` 表:每张发票记录走了哪几层、各层 confidence、触发原因
  - 优点:细粒度对照分析、阈值调参依据
  - 缺点:多写一份数据,实施复杂度+

### 3.7 API 接口改动

**对外接口零变化**:
- `/api/ocr/recognize` 响应结构不变
- `pages[].fields` 字段名不变(见疑问 C)
- 仅在 `pages[].fields._confidence` **新增**可选键

**内部接口**:
- 新增 `pipeline.run(pdf_bytes: bytes, max_pages: int, api_key: Optional[str]) -> PipelineResult`
- `PipelineResult` 与 `gemini_engine.recognize_pdf` 返回结构高度兼容,**额外**多 `_audit` 字典(走了哪几层、各层成本、触发原因)

---

## 四、切换策略(开发完直接全量,无灰度 / 无 Shadow)

> 用户当前**处于开发阶段,无真实用户**。原 architecture.md §7.7 的 5 步灰度方案不适用。

### 切换流程(3 步)

**步骤 1 · 开发期**(`OCR_USE_NEW_PIPELINE=false`)
- 旧 gemini_engine 继续生效,所有 OCR 入口走旧链路
- 新 `services/ocr/` 代码独立开发,不接入业务流程
- 开发到任何节点想实测新链路:把 env 切到 `true`,所有入口走 pipeline;有问题切回 `false`
- 两套并存,**没有时间窗口约束**,开发到满意为止

**步骤 2 · 开发完成 + 测试通过**
- 把 `OCR_USE_NEW_PIPELINE=true` 设为默认(本机 + 服务器都改)
- 一次性切换所有 OCR 入口(主路由 / LINE / email / recon batch)到新 pipeline
- **立刻删除旧 OCR 代码**(决策 1 + 5):
  - app.py 内联兜底链(70 行 `text_path → gemini → vision_fallback`)
  - app.py LINE / email / recon_routes 接入点的 else 旧分支
  - 文件级删除:`engine_chain.py`、`typhoon_engine.py`、`nvidia_engine.py`、`ocr_engine.recognize_pdf`、`vision_engine.py`(REST 旧实现)
  - `gemini_engine.py` 的 `recognize_pdf` 主入口 + `restructure_with_text_hint` 删除;Flash-Lite/Flash 基础设施部分**视 `services/ocr/llm_client.py` 设计决定**是否完全取代
- feature flag `OCR_USE_NEW_PIPELINE` **保留作为开发自检**,但实际旧代码已删,切到 `false` 时报错或 NotImplementedError(可读性 > 静默失败)

**步骤 3 · 回滚预案**
- 开发期:切回 `OCR_USE_NEW_PIPELINE=false`,旧代码仍在,一行配置切回
- 切完后(步骤 2 旧代码已删):feature flag 形同摆设,**真要回滚需 git revert + 重新部署**

### 测试通过的标准(待用户定义,可阶段 3 后期讨论)

建议但不强制:
- `tests/fixtures/` 5-10 张脱敏样本 100% pass
- `storage/pdfs/` 本地 50+ 张真实样本对比新旧两套结果,字段一致率 > 95%
- 三层各自单测覆盖 + pipeline 整体 e2e 测试
- `connectivity_check.py` 在本机 + 服务器都跑通(前置任务 0)

---

## 五、疑问跟踪

### 阻塞问题(已确认,4/4)

| 编号 | 主题 | 状态 | 决策位置 |
|---|---|---|---|
| A1+A2+A3 | 凭证 + 并存 + 连通性 | ✅ 已确认 | 见顶部「决策 1」 |
| B1 | 字段 schema 命名 | ✅ 已确认 | 见顶部「决策 2」 |
| E1 | 测试样本 | ✅ 已确认 | 见顶部「决策 3」 |
| G1 | 错误处理 | ✅ 已确认 | 见顶部「决策 4」 |
| ~~H1~~ | ~~灰度规则~~ | ❌ 已废弃 | 决策 5 用单一 feature flag 替代灰度 |

### 非阻塞问题(5 项,推迟到阶段 3 触及时再具体讨论)

按用户指示,先不展开讨论,避免过度预设。**只列存档**:

- **B2** · 内部 Decimal 对外序列化(字符串 vs number)
- **C1** · 4 个入口(主路由 / LINE / email / recon batch)接入顺序
- **C2** · recon_routes batch 并发 20 是否需降
- **F1** · cost log 粒度(每张 1 条 vs 每层 1 条)
- **J1** · 下游消费者(invoice_grouper / archive / pdf_searchable / xero_pusher / mrerp_xlsx_generator)字段兼容性测试方式

已废弃的非阻塞问题:
- ~~**D1** · Shadow 期 API 额度翻倍~~ — 无 Shadow 期
- ~~**D2** · Shadow 结果落库~~ — 无 Shadow 期
- ~~**I1** · 死代码清理具体时机~~ — 决策 5 已完全明确(切完立刻删)

阶段 3 实施到对应任务节点时,具体提出再讨论。

---

## 六、风险评级(主观,已根据决策更新)

| 风险 | 等级 | 缓解 |
|---|---|---|
| Vision API 网络连通性(中国大陆 / 部署机房) | **高** | **决策 1 已要求前置任务 0 在本机 + 服务器都跑通连通性测试**,详见 §七 |
| 字段 schema 漂移影响下游(尤其 mrerp_xlsx_generator) | ~~中~~ → **低** | **决策 2 已选 `seller_tax`(完全兼容旧名)**,下游零改动 |
| GCP 试用额度 $300 / 91 天耗尽 | ~~中~~ → **低** | 无 Shadow 期(决策 1 简化),开发期 API 消耗仅来自手动测试,无双倍流量风险 |
| Cloudflare proxy 与新 SDK 配置冲突 | **中** | Vision 走 Service Account 直连官方端点(决策 1);Flash-Lite/Flash 是否走 proxy 推到阶段 3 第 2 步触及时讨论 |
| 三层全失败时用户感知异常 | **低** | **决策 4 两阶段策略**:开发期自动回退旧 gemini,切换后进低置信度队列 |
| 真实样本进 git 泄露隐私 | **低** | **决策 3 明确 `storage/pdfs/` 不进 git**,正式 fixtures 脱敏后才用 |
| 9+ 处直调 genai 的模块未来统一时阻力 | **低** | 本次不动,留接口预备;架构稳定后另立项 |
| 死代码切完立刻删 → 回滚困难 | **低** | 测试通过才切;切前充分跑 `storage/pdfs/` 对照;真要回滚 `git revert` 重新部署 |
| 老 ocr_history 数据兼容(没有 _confidence 子字典) | **低** | 新键可选,旧消费者不读则无影响 |

---

## 七、阶段 3 任务排序

按用户决策 1,**前置任务 0** 在第 1 个原子任务前先做:

### 前置任务 0 · 连通性测试(决策 1 强制要求)

- **文件**:`services/ocr/connectivity_check.py`(独立工具,可命令行运行;不依赖业务代码)
- **配套测试**:`tests/test_connectivity.py`(可选,主要是 connectivity_check.py 自带 main 函数)
- **职责**:跑一遍下面 6 项检查,每项独立报告 pass/fail + 详细诊断:
  1. **env 检查**:`GOOGLE_APPLICATION_CREDENTIALS` 已设置,且文件路径存在 + 可读
  2. **JSON 格式检查**:文件能 parse,含 `type=service_account`、`project_id`、`client_email` 等关键字段
  3. **SDK 导入**:`from google.cloud import vision` 不抛错
  4. **客户端初始化**:`vision.ImageAnnotatorClient()` 能成功创建(隐式使用 env 凭证)
  5. **网络连通**:对 `vision.googleapis.com` 做一次最小调用(1 像素白图 DOCUMENT_TEXT_DETECTION),测延迟 + 错误码
  6. **额度检查**(可选):报告 Service Account 是否能访问 `pearnly` 项目、API 是否启用
- **运行方式**:`python -m services.ocr.connectivity_check`(或 `python services/ocr/connectivity_check.py`)
- **运行环境**:**必须在本机 + 服务器(`45.76.53.194`)各跑一次**,两边都通过才进第 1 个原子任务
- **失败诊断输出格式**:明确指出问题(JSON 文件缺失 / 网络不通 / API 未启用 / 权限不足 / etc.)+ 修复建议
- **重要约束**:此工具**不接入业务流程,不改任何现有代码**

### 阶段 3 第 1 个原子任务 · `layer1_vision.py`

按 [3-start-impl.md](./3-start-impl.md):

- **文件**:`services/ocr/layer1_vision.py`
- **职责**:接受 `pdf_bytes: bytes` 或 `image_bytes: bytes`,调 Vision API DOCUMENT_TEXT_DETECTION,返回:
  ```python
  {
    "pages": [
      {
        "page_number": int,
        "full_text": str,
        "blocks": [...],  # 完整层级 + confidence + bbox
        "avg_confidence": float,
      }
    ],
    "engine": "layer1_vision",
    "elapsed_ms": int,
  }
  ```
- **凭证**:env `GOOGLE_APPLICATION_CREDENTIALS`(决策 1)
- **测试样本**:决策 3 — 阶段 3 第 1 步先用 `storage/pdfs/` 本地跑通(开发机 only,绝不入 git);正式 fixtures(`tests/fixtures/`,5-10 张脱敏样本)后期补
- **测试脚本**:`tests/test_vision_layer.py`
- **不接入业务流程,不改任何现有代码**

### 进阶段 3 前 Checklist(逐项打勾,全绿才能进)

#### ☐ 1. 本机 JSON key 放置

目标路径:`C:\Users\skin3\.gcp\pearnly-vision-key.json`

操作步骤:
1. 若 `C:\Users\skin3\.gcp\` 目录不存在,先创建:
   - PowerShell:`New-Item -ItemType Directory -Path "C:\Users\skin3\.gcp" -Force`
2. 复制 Service Account JSON key 到该目录,改名为 `pearnly-vision-key.json`
3. 验证:`Test-Path C:\Users\skin3\.gcp\pearnly-vision-key.json` 应返回 True

#### ☐ 2. 服务器 JSON key 放置

目标路径:`/etc/pearnly/pearnly-vision-key.json`

操作步骤(SSH 上服务器 `45.76.53.194`):
1. `sudo mkdir -p /etc/pearnly`
2. 从本机 scp 上去:`scp C:\Users\skin3\.gcp\pearnly-vision-key.json root@45.76.53.194:/etc/pearnly/`
3. 设置权限(防其他用户读):
   ```
   sudo chown root:root /etc/pearnly/pearnly-vision-key.json
   sudo chmod 0640 /etc/pearnly/pearnly-vision-key.json
   ```
4. 若应用以非 root 用户运行,把那个用户加到 root 组,或改成对应 `chown app_user:app_user` + `0400`
5. 验证:`ls -l /etc/pearnly/` 应看到文件 + 正确权限

#### ☐ 3. 本机环境变量

目标:`GOOGLE_APPLICATION_CREDENTIALS=C:\Users\skin3\.gcp\pearnly-vision-key.json`

任选一种(推荐 A):
- **A · 用户级持久变量**(推荐):PowerShell 执行:
  ```powershell
  [Environment]::SetEnvironmentVariable("GOOGLE_APPLICATION_CREDENTIALS", "C:\Users\skin3\.gcp\pearnly-vision-key.json", "User")
  ```
  之后**重启 PowerShell 终端** + Claude Code,新会话才会读到
- **B · GUI**:Win+R → `sysdm.cpl` → 高级 → 环境变量 → 用户变量 → 新建
- **C · 临时(仅当前 PowerShell 会话有效)**:`$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\Users\skin3\.gcp\pearnly-vision-key.json"`

验证:重启 PowerShell 后跑 `echo $env:GOOGLE_APPLICATION_CREDENTIALS` 应输出完整路径

#### ☐ 4. 服务器环境变量

目标:`GOOGLE_APPLICATION_CREDENTIALS=/etc/pearnly/pearnly-vision-key.json`

需要根据 Pearnly 在服务器上的运行方式选择(请用户确认运行方式后挑一种):

- **A · 若用 systemd service**(常见生产部署):
  - 编辑 unit 文件(常见路径 `/etc/systemd/system/pearnly.service` 或类似)
  - 在 `[Service]` 节加:`Environment="GOOGLE_APPLICATION_CREDENTIALS=/etc/pearnly/pearnly-vision-key.json"`
  - `sudo systemctl daemon-reload && sudo systemctl restart pearnly`(服务名按实际改)
- **B · 若用 supervisord / pm2 / 其他 process manager**:在对应配置文件加 env 块
- **C · 若直接在 shell 里启动 Python**:在启动脚本顶部 `export GOOGLE_APPLICATION_CREDENTIALS=/etc/pearnly/pearnly-vision-key.json`
- **D · 系统全局(慎用)**:加到 `/etc/environment`,所有进程可见,需要 reboot

验证:在服务器跑 `systemctl show pearnly -p Environment`(若 systemd)或直接 `python3 -c "import os; print(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'))"`

#### ☑ 5. `.gitignore` 检查报告(已完成,无需操作)

- ✅ `storage/` 已含(第 38 行)
- ✅ `payments/` 已含(第 37 行)
- ❌ `.secrets/` 未含 — **本次决策 1 选了项目外路径,不影响**;若未来要在项目内放敏感文件,用户自行添加
- ⚠️ 软提示:`.gitignore` 第 27 行的 `secrets.json` 是具体文件名,**不会**覆盖 `pearnly-vision-key.json`。若误把 JSON key 拖进项目根目录有泄露风险,但本次路径在项目外,本次不受影响

---

### Checklist 状态

完成 1 / 2 / 3 / 4 后告诉我"进阶段 3",我会从前置任务 0(`connectivity_check.py`)开始。
- 5 已自动完成(读 .gitignore 报告)
- ~~6 tenant_id 核实~~ — 已废弃(决策 5 用单一 feature flag 替代灰度,不再需要 tenant_id 白名单)

---

*阶段 2 已完成 + 5 项阻塞决策已确认(原 H1 灰度规则废弃) + 4 项 checklist 待用户操作。等用户完成 1-4 后说"进阶段 3"。*
