# 交接 · OCR/LLM 后端收口网关(OCR_LLM_BACKEND 单一开关)

> 日期:2026-06-29 · 署名 Opus 4.8 · 状态:**引擎完成并实跑验证 · 7/13 调用点已迁 · 余下按本档收尾**
> 一句话:把全产品 ~15 处散落的 Gemini 调用收口到一个**可切后端**的网关,默认 `aistudio`(行为零变化),
> 一拨 `OCR_LLM_BACKEND=vertex` 即整体切 Vertex AI,`=selfhost` 切自托管 Qwen2.5-VL。

---

## 0. 背景与缘起(为什么做这个)

- 起于扒竞品 **paypers.ai**(泰国同赛道 · LINE 拍票记账)。公开面实锤:它用 **Gemini @ Vertex AI**(客户端 JS 里 7 个 gemini 型号 + `vertexbot`),全家桶绑 Google(GCS/Drive/Sheets/OAuth),Stripe+PromptPay,Sentry,PostHog,Mintlify 文档。
- 反观 Pearnly 自己:OCR 的 Gemini 调用**散在 ~15 处**,各自 `genai.configure`,走的是 **AI Studio(api_key)而非 Vertex**,**没有单一开关**——想切后端/上合规要改十几个文件。
- 目标(用户拍板「做完整套」):**收口成一个可切换网关**,使得:
  1. 现在能无痛切 **Vertex**(企业配额 + 数据驻留 + 不训练 → 合规背书,对标 paypers)。
  2. 将来能切 **自托管 Qwen2.5-VL**(数据零出门、量大只付电费 —— 复用已有 `pearnly-local-ocr-stack` 评测栈)。
  3. **质量不降**:开关只换「门」,不换模型/提示词。

### Vertex 可用性(已就绪)
- GCP 项目 `pearnly`,服务账号 `pearnly-ocr-sa@pearnly.iam.gserviceaccount.com`。
- **Vertex AI API 已启用**(Codex 桌面端代操作),SA 已有 `roles/aiplatform.user`。
- 新服务账号密钥:`C:\Users\skin3\Desktop\pearnly-512792782789.json`(⚠ 在桌面明文 · **上线前移进 secret store 并轮换**)。
- **已实测**:`gemini-2.5-flash @ asia-southeast1`,提取测试发票字段全对(seller/tax_id/grand_total),3.35s。

---

## 1. 架构(已建成)

```
业务 ~15 处  ──►  services/ai_gateway/transport.py  ──►  backends.get_provider()  按 OCR_LLM_BACKEND 选
                   4 个统一入口:                          ├─ providers/aistudio.py (默认·google-generativeai + api_key)
                     text_to_json                         ├─ providers/vertex.py   (google-genai · vertexai=True)
                     multimodal_to_json                   └─ providers/selfhost.py (OpenAI 兼容 → Qwen2.5-VL)
                     text_to_text
                     embed
                   (统一计时/估成本/隐私日志 · 复用 costing.py / logging.py)
```

- **后端开关唯一读点**:`services/ai_gateway/backends.py` → `active_backend()`(env `OCR_LLM_BACKEND`,默认 `aistudio`,未知值回落 aistudio,大小写不敏感)。
- **4 种调用形态**覆盖契约里所有用法:
  - `text_to_json`(A 组:L2 抽取 / 分类 / VAT 差异分析 / 导入列映射)
  - `multimodal_to_json`(B 组:L3 视觉 / 身份证 / VAT 发票/批量/报表/分类 / 银行 GL/对账单)
  - `text_to_text`(C 组:知识 RAG 问答)
  - `embed`(D 组:知识 RAG 向量)
- **model_tier 抽象**(`flash`/`flash_lite`/`best`/`fallback`/`escalate`):
  - aistudio/vertex 经 `services/ocr/gemini_models.py` 解析成具体 gemini 名(两后端同名)。
  - selfhost 所有 tier 映射到单一 `SELFHOST_OCR_MODEL`(需要分档再按 env 细分)。
- **薄透传铁律**:`temperature / response_mime / max_tokens / 图字节` 由各调用点原样传入,网关不重塑 prompt → 默认后端行为不变。

### 关键安全策略(贯穿全程)
1. **默认 `aistudio` 字节级一致**:已全迁的站点,默认后端走 aistudio provider,忠实复刻原 `configure+GenerativeModel+generate_content`(同模型/同参数/同 JSON 解析)。
2. **高危站点用 guard 法而非全迁**:base64 载荷 + `try_with_fallback` 模型降级的银行解析、深度测试耦合的 L2/L3 —— 默认分支**原代码一行不动**,仅 `if not backends.is_aistudio()` 时才路由到网关(给 vertex/selfhost 用)。
3. **embedding 向量空间不漂**:`aistudio.embed` 用与旧知识库**同一 REST `batchEmbedContents` + 同模型 `gemini-embedding-001@768`**,默认字节级一致;Vertex 默认 `VERTEX_EMBED_MODEL=gemini-embedding-001` 同空间。

---

## 2. 已完成(可直接用 · 全绿)

### 新建文件(引擎)
| 文件 | 行 | 作用 |
|---|---|---|
| `services/ai_gateway/backends.py` | 45 | 后端开关 + `get_provider()` 懒加载 |
| `services/ai_gateway/transport.py` | 140 | 4 形态统一入口 + 计时/计费/日志包装 |
| `services/ai_gateway/providers/aistudio.py` | 238 | 默认后端(google-generativeai)· embed 走 REST 保向量一致 |
| `services/ai_gateway/providers/vertex.py` | 236 | Vertex(google-genai · vertexai=True)· 已实测 |
| `services/ai_gateway/providers/selfhost.py` | 207 | OpenAI 兼容(自托管)· 多模态走 image_url base64 data URI |
| `tests/unit/test_ai_gateway_transport.py` | — | 9 用例:开关路由 / 4 形态转发 / 无凭据收敛 error_kind |

> 注:旧 `services/ai_gateway/providers/gemini.py`(69 行)保留不动 —— 现有 `router.run_task`(LINE 文本路径)+ 其单测仍用它。它内部包 `layer2_gemini._call_gemini_with_retry`,**会随 L2 guard 一起获得后端切换**(见 §3)。

### 已迁移的 7 个调用点(默认后端字节级一致)
| 站点 | 文件 | 形态 | 备注 |
|---|---|---|---|
| 知识问答 C1 | `services/knowledge/generation.py` | text_to_text | 保 `GenerationError` 契约 |
| 知识向量 D1 | `services/knowledge/embedding.py` | embed | 保 `EmbeddingError`、向量空间不变 |
| VAT 单张 B3 | `services/vat/vat_ocr_extract.py` | multimodal_json | |
| VAT 批量 B4 | `services/vat/vat_ocr_batch.py` | multimodal_json(多图) | |
| VAT 分类 B6 | `services/vat/vat_file_classifier.py` | multimodal_json | |
| VAT 差异分析 A5b | `services/vat/vat_ai_analyzer.py` | text_to_json(temp 0.3) | |
| 导入列映射 A5 | `services/importer/ai_mapping.py` | text_to_json(response_mime=False·去栅栏) | |

### 依赖
- `requirements.txt` 已加 `google-genai`(Vertex 用 · 默认 aistudio 不 import)。本机已 `pip install`,版本 2.10.0。
- ⏳ **`requirements.lock.txt` 未更新**(见 §3 待办)。

### 验证状态
- 网关 9 单测 + 已迁站点回归(知识 183 / VAT+导入若干)= **239 passed**,ruff 全清。
- **Vertex 经 transport 端到端实跑通**(`OCR_LLM_BACKEND=vertex` → 字段全对)。

---

## 3. 待完成 + 怎么完成(逐项可执行)

> 通用做法两种:**全迁**(标准 `{mime: 原始bytes}` 载荷、有 response_mime 的站点)/ **guard**(base64 载荷、自定义 fallback、深测试耦合的站点)。

### ① 银行 GL/对账单 ×2 —— **用 guard 法**(高危:base64 + try_with_fallback)
文件:`services/recon/bank_gl_gemini.py`(`_call_json`)、`services/recon/bank_stmt_gemini.py`(闭包 `_call`)
做法:在最内层「单次 Gemini 调用」函数里加分支:
```python
def _tier_for(model_name):
    from services.ocr import gemini_models
    if model_name == gemini_models.fallback(): return "fallback"
    if model_name == gemini_models.flash_lite(): return "flash_lite"
    return "flash"

def _call_json(model_name, pdf_bytes, prompt):
    from services.ai_gateway import backends
    if not backends.is_aistudio():                       # vertex/selfhost
        from services.ai_gateway import transport
        out = transport.multimodal_to_json(
            prompt, [(pdf_bytes, "application/pdf")], tier=_tier_for(model_name),
            api_key=None, response_mime=False, max_tokens=32768, temperature=0.0,
            max_retries=0, task="bank.gl")
        if not out.ok:
            raise RuntimeError(f"gateway {out.error_kind}")   # 让 try_with_fallback 试下一档
        return out.data
    # —— 默认 aistudio:原 base64 代码原样保留(字节级不变)——
    import google.generativeai as genai
    ...原代码...
```
要点:`try_with_fallback` 保留;guard 分支传**原始 bytes**(provider 自行编码),vertex/selfhost 不需要 api_key;默认分支的 base64 路径**一行不动**。bank_stmt 的 `_call` 闭包能取到 `file_bytes`(用它,别用 b64)。

### ② L2/L3 核心 + 身份证 —— **用 guard 法**(深测试耦合)
- **L2**:`services/ocr/layer2_gemini.py` 的 `_call_gemini_with_retry`(文本→json)。在 `model.generate_content` 处加 guard:非 aistudio 时用 `transport.text_to_json(base_prompt, tier=<按 model_name 映射>, api_key=api_key, response_mime=True, max_tokens=16384, temperature=0, max_retries=0)`,返回 `(data, meta)` 形状。**注意保留 `record_gemini_call` 监控埋点 + 返回元组契约**。一处 guard 即覆盖 A1/A2/A3/A4/A4b(都经此核心)。
- **L3**:`services/ocr/layer3_fallback.py` 的 `_call_gemini_with_retry`(多模态)。同法,非 aistudio 时 `transport.multimodal_to_json`,图来自它现有的 PIL Image → 需 `img.tobytes()`/`save 到 BytesIO` 转 bytes+mime(PIL 不是 bytes,转一下)。
- **身份证 B2**:`services/ocr/id_card_extract.py:_gemini_vision_extract`(多模态,载荷已是 `{mime,data:bytes}`)→ 可**全迁** `transport.multimodal_to_json`(它是标准 bytes 载荷,低危),保 `IdCardExtractError` 契约。

### ③ VAT 报表 parser B5 —— **全迁 + 保超时重试**
文件:`services/vat/vat_parser_gemini.py:parse_with_gemini`(标准 `{mime,bytes}`,temp **0.1**,自带「超时/5xx 单次重试」)。
做法:替换 genai 块为 `transport.multimodal_to_json(prompt, [(file_bytes, mime_type)], tier="flash", api_key=key, temperature=0.1, response_mime=True, max_tokens=16384, timeout_s=60, max_retries=0, task="vat.report_parse")`;**在外面保留它的 2 次循环**:`if out.error_kind=="timeout" and attempt==0: sleep(2); continue`。后续 `re.sub` 去栅栏 + `json.loads` 改为直接用 `out.data`(已是 dict)。

### ④ requirements.lock.txt + pip-audit(task #2)
- 锁文件按惯例**手改**(避免 py3.11 churn,见过往 pymupdf 教训):把 `google-genai==2.10.0` 及其传递依赖加进 lock。`google-genai` 拉的传递依赖需 `pip show google-genai` 看 Requires(大致 google-auth/pydantic/websockets/httpx 等,多数已在 lock)。
- 跑 `pip-audit` 确认零新 CVE(6 闸之一)。

### ⑤ 跑全 6 道闸 + 清死代码(task #10)
- 死代码:`vat_*`/`importer` 里迁移后变孤儿的 `_AI_MAPPING_MODEL`、个别 `_flash`(ruff 已清大部分;`ruff check services/` 复查)。
- 6 闸:`black`、`ruff(lint-size + lint-ui 无关)`、`pytest 全量`、`pip-audit`、体积闸(全 <500 已满足)。
- 跑全量 `pytest`(本机 charmap 坑:命令前置 `PYTHONUTF8=1`)。重点回归:`tests/unit/test_layer2_gemini_contract.py`、`test_ocr_*`、`test_bank_*`、`test_ai_gateway*`。

### ⑥ 开关文档 + .env.example(task #10)
`.env.example` 加:
```
OCR_LLM_BACKEND=aistudio            # aistudio(默认) | vertex | selfhost
# vertex:
GCP_PROJECT=pearnly
VERTEX_LOCATION=asia-southeast1
# GOOGLE_APPLICATION_CREDENTIALS 指向服务账号 JSON(已用于 Layer1 Vision)
VERTEX_EMBED_MODEL=gemini-embedding-001   # 与 aistudio 同向量空间·勿随意改(会废知识库索引)
# selfhost(自托管 Qwen2.5-VL · vLLM OpenAI 兼容):
SELFHOST_OCR_URL=                   # 如 http://host:8000/v1
SELFHOST_OCR_KEY=                   # 可选 Bearer
SELFHOST_OCR_MODEL=                 # 如 Qwen2.5-VL-32B-Instruct
SELFHOST_EMBED_MODEL=
AISTUDIO_EMBED_MODEL=gemini-embedding-001
```

### ⑦ Vertex 经网关跑真票(收尾验证)
切 `OCR_LLM_BACKEND=vertex` + 上面 env,把 `scripts/_gen_adversarial_invoices.py` 那批对抗发票跑一遍主管线,与 `compare_summary.json` 同口径对照(确认迁移后端到端无回归 + Vertex 质量)。

---

## 4. 完成后是什么样(End State)

- **一个开关治全局**:`OCR_LLM_BACKEND` 一处 env,LINE 拍票 / Web 上传 / VAT / 银行对账 / 导入 / 知识 RAG 的**所有 Gemini 调用**整体在 aistudio↔vertex↔selfhost 间切,业务代码零改。
- **Vertex 上线**:数据驻留新加坡 + 不训练 + 企业配额/SLA → 可对外讲合规(对标 paypers 的 CASA),且复用现成 GCP 项目/服务账号。
- **自托管随时可接**:L40S 重启 + 配 `SELFHOST_OCR_*` → 切 `selfhost`,数据零出门;可按文档类型/比例灰度(简单票走自托管省钱,难票走 Vertex 兜底)。
- **质量不变**:同模型同提示词,默认 aistudio 字节级一致;切后端前用对抗集 + 评测护栏(已有 `compare_summary.json` 口径)确认达标再灰度。
- **不动的非目标**:Layer1 = Google Cloud Vision(取字,另一产品,不并入)、付款 slip = SLIPOK(第三方,非 LLM)—— 设计上独立,保持现状。

---

## 5. 坑 / 风险清单(务必读)

1. **base64 vs 原始 bytes**:银行解析旧代码给 genai 传的是 **base64 字符串**(`{"data": b64}`),其它站点传**原始 bytes**。`transport`/各 provider 统一收**原始 bytes**,内部各自编码。→ 银行**只能 guard**,默认分支保留 base64,别全迁(否则可能动账)。
2. **embedding 向量空间**:切 Vertex/selfhost 的 embedding 若换了模型,**整个知识库索引作废需重建**。默认已锁 `gemini-embedding-001@768` 同空间;改 `*_EMBED_MODEL` 前必须想清楚重建索引。
3. **两套 api_key 优先级**:OCR 层是 `GOOGLE_API_KEY→GEMINI_API_KEY`,VAT/recon/knowledge 是 `GEMINI_API_KEY→GOOGLE_API_KEY`。迁移**保留各站点原解析顺序**再把 key 传给 transport(aistudio 用,vertex/selfhost 忽略)。已迁站点都照此。
4. **`RECON_AI_MAPPING_MODEL` 行为微变**:导入列映射原用该 env 选模型,迁后改用 `flash_lite` tier(默认值同为 gemini-2.5-flash-lite,**默认无差**;若线上设过该自定义 env 则失效)。可接受/已文档化。
5. **lock 升级**:加 `google-genai` 必同步 lock,否则 CI 干净 venv 装不全 → import 挂。
6. **Windows 本机 charmap**:跑任何带中文/泰文输出的 py 必前置 `PYTHONUTF8=1 PYTHONIOENCODING=utf-8`,否则 cp874 编码崩。
7. **密钥安全**:`pearnly-512792782789.json` 在桌面明文 → 上线移入 secret store + 轮换;旧 key 也建议轮换(见 selfhost 评测档记录的明文 key 提醒)。
8. **共享树 git**:提交只 `add` 自己 pathspec;commit 即 push 中间别插别的 git 操作;ratchet/RATCHET-EXEMPT 逐文件列;提交后立刻跑 ratchet。

---

## 6. 任务盘对照(本会话 TaskList)

| # | 任务 | 状态 |
|---|---|---|
| 1 | 设计统一网关接口 | ✅ 完成 |
| 3 | Provider aistudio | ✅ 完成 |
| 4 | Provider vertex | ✅ 完成(实测) |
| 5 | Provider selfhost | ✅ 完成(待真端点) |
| 6 | 路由+开关+model_tier+embed | ✅ 完成 |
| 9 | 迁知识 RAG | ✅ 完成 |
| 8 | 迁 VAT×5+银行×2+导入×1 | 🔶 **部分**:VAT 4/5(差 parser B5)+ 导入✅;银行×2 待 guard |
| 7 | 迁 L2/L3 核心 | ⬜ 待做(guard + 身份证全迁) |
| 2 | google-genai lock + pip-audit | 🔶 requirements.txt✅ · lock/audit 待做 |
| 10 | 全 6 闸 + Vertex 真票 + 文档 | 🔶 部分单测✅ · 全闸/真票/.env 文档 待做 |

## 7. 复跑/接力入口
- 引擎冒烟(Vertex 实跑):
  ```bash
  cd ~/Desktop/pearnly-app
  PYTHONUTF8=1 OCR_LLM_BACKEND=vertex \
    GOOGLE_APPLICATION_CREDENTIALS="C:/Users/skin3/Desktop/pearnly-512792782789.json" \
    GCP_PROJECT=pearnly python -c "from services.ai_gateway import transport,backends; print(backends.active_backend())"
  ```
- 网关单测:`PYTHONUTF8=1 python -m pytest tests/unit/test_ai_gateway_transport.py -q`
- 迁移模式参考:看本档 §3 + 已迁的 `services/vat/vat_ocr_extract.py`(全迁范式)。
