# 快速通道集成 + 监控埋点对齐设计

> 调研日期:2026-05-18
> 目的:
>   1. **任务 2**:把现有"电子 PDF 文本层快速通道"(`pdf_text_extractor`)集成进新 pipeline,显著降本
>   2. **任务 3**:对齐现有 `ocr_cost_log` / `increment_*_usage` / `insert_ocr_history` 监控埋点,接入 app.py 时不破坏 dashboard

---

## 一、现有快速通道(只读调研)

### 1.1 入口位置

[app.py:1686-1704](../../app.py)(`/api/ocr/recognize` 主路由内):

```python
# v118.20.4 · PDF 文本预筛(电子发票快速通道)
# 命中:0.3s 一张 · 跳过 Gemini · 省时省 API 配额
# 不命中:静默 fallback · 走原 Gemini → Vision 链(零回退副作用)
result = None
chain_info = []
try:
    from pdf_text_extractor import try_text_extraction
    _text_result = try_text_extraction(content)
    if _text_result:
        result = _text_result
        chain_info = ["text_path"]
```

### 1.2 [pdf_text_extractor.py](../../pdf_text_extractor.py) 的工作方式

入口函数:`try_text_extraction(pdf_bytes: bytes, strict: bool = True) -> Optional[Dict[str, Any]]`

判定流程:
1. 用 `pypdf` 读 PDF,逐页 `extract_text()`
2. 计算平均字符数:`total_chars / n_pages`
3. **门槛**:`MIN_TEXT_PER_PAGE = 200` — 平均 < 200 字符视为扫描件,返回 `None` 让上层走 OCR
4. 命中后用正则抽字段(`_extract_fields_from_text`):invoice_no / date / total / subtotal / vat / seller / buyer / items / notes
5. **严格门槛**(`strict=True`,默认):必须抽到 `invoice_no + total + seller_tax + buyer_tax` 四件套
6. 返回结构:
   ```python
   {
     "pages": [{"page": i+1, "fields": {...}, "raw_text": text, ...}],
     "page_count": N, "elapsed_ms": ms, "engine": "text"
   }
   ```

**关键属性**:
- 零 API 成本(全本地 pypdf + 正则)
- 0.3s / 张(实测从 architecture.md 引用)
- 字段抽取是"正则版",**对模板敏感**;非泰国电子发票常见模板可能漏抽
- 4 件套门槛严格,**抽不全就 fallback**(无副作用)

### 1.3 生产实测命中率(从 `chain_info` 字段反推)

Stage 1 审计提到生产 Earn 用户 ~฿0.0161/张,这只能用 text_path 高命中率解释。架构估算的 Gemini 全程 ~$0.005 ≈ ฿0.175/张,差 10 倍。**说明生产里电子发票占比极高,text_path 实际命中率应该 > 80%**。

新 pipeline 没集成 text_path,目前实测 ฿0.072/页 — 比 Gemini 全程便宜但仍比 text_path 贵 ~4 倍。

---

## 二、新 pipeline 集成 text_path 设计

### 2.1 设计原则

**architecture.md §四 ④ 推荐**:"质量好的电子 PDF 直接绕过 OCR — 直接 PDF 文本提取 + Flash-Lite 解析,完全跳过 Vision API,这部分文档成本降到 $0.0005/页"

**关键决策**:不重用 `pdf_text_extractor` 的正则字段抽取(模板敏感、维护负担),只用它的**文本提取部分**,然后:
- 把提取的文本喂给 **Layer 2 Flash-Lite**(AI 抽字段,泛化好)
- **跳过 Layer 1 (Vision)** — 这是省钱的关键
- Layer 3 视情况触发(图像兜底,仍可用)

### 2.2 新模块设计:`services/ocr/text_path.py`

**职责**:
1. 用 pypdf 提取 PDF 每页文本(纯文本,不抽字段)
2. 应用同样的"avg chars per page >= 200"门槛
3. 若命中,把文本包装成 Layer1Result-like(per-page 文本)供 Layer 2 消费
4. 若不命中,返回 None,pipeline fall through 到 Layer 1 (Vision)

```python
# services/ocr/text_path.py(草案,等用户审 fast-path-design.md 后再写代码)

from typing import Optional, List
from .schemas import Page, Layer1Result

MIN_TEXT_PER_PAGE = 200  # 跟 pdf_text_extractor 对齐

def try_extract(pdf_bytes: bytes, max_pages: int = 50) -> Optional[Layer1Result]:
    """如果是有文本层的电子 PDF,返回 Layer1Result-like(no bbox/conf,只有 text)。
    否则 None,让上层走 Vision。
    """
    try:
        import pypdf
    except ImportError:
        return None
    
    import io
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    except Exception:
        return None
    
    n = len(reader.pages)
    if n == 0:
        return None
    
    page_texts: List[str] = []
    total = 0
    for p in reader.pages[:max_pages]:
        try:
            t = p.extract_text() or ""
        except Exception:
            t = ""
        page_texts.append(t)
        total += len(t)
    
    avg = total / max(len(page_texts), 1)
    if avg < MIN_TEXT_PER_PAGE:
        return None  # 扫描件,fallback
    
    # 包装为 Layer1Result(无 bbox / conf,但 Layer 2 只看 full_text 不需要这些)
    pages = [
        Page(
            page_number=i + 1,
            width=0, height=0,
            full_text=text,
            avg_confidence=1.0,  # pypdf 没 conf,我们信
            blocks=[],
        )
        for i, text in enumerate(page_texts)
    ]
    return Layer1Result(
        pages=pages,
        page_count=len(pages),
        elapsed_ms=0,  # 调用方计时
        engine="text_path",
        dpi=0,
    )
```

### 2.3 pipeline.py 集成点

在 `pipeline.run_on_pdf_bytes` 开头插入 text_path 试探:

```python
def run_on_pdf_bytes(pdf_bytes, ..., enable_text_path: bool = True):
    ...
    layer1_result = None
    used_text_path = False
    
    # Layer 0: 电子 PDF 文本路径快速通道
    if enable_text_path:
        from .text_path import try_extract
        layer1_result = try_extract(pdf_bytes, max_pages=max_pages)
        if layer1_result:
            used_text_path = True
            logger.info("pipeline: text_path HIT — %d pages, skipping Vision", layer1_result.page_count)
    
    # Layer 1: Vision OCR(text_path 未命中时)
    if layer1_result is None:
        # 原来的 fitz render + _l1_extract_image 流程
        ...
    
    # 后续 layer 2 / layer 3 不变,但每页 layer_chain 起始为 "text" 或 "L1"
```

### 2.4 PipelinePageResult.layer_chain 含义扩展

新增 chain 元素 `text`(表示走了文本路径,跳过 Vision):

| chain 序列 | 含义 |
|---|---|
| `["text", "L2"]` | 电子 PDF 文本路径 + Flash-Lite(常见情况)|
| `["text", "L2", "L3"]` | 文本路径但 L2 输出有问题,L3 视觉兜底 |
| `["text", "L2", "L3_failed"]` | text 路径 + L3 失败 → 走 L2 结果 + 人工复核 |
| `["L1", "L2"]` | 当前默认(扫描件 / 手机照片)|
| `["L1", "L2", "L3"]` | 当前 L3 触发情况 |
| `["L1", "L2", "L3_failed"]` | 同上 + L3 失败 |

### 2.5 成本变化估算

**当前(无 text_path)** — 实测 ฿0.072/页

**集成 text_path 后** — 估算:

| 场景占比 | 单页成本 | 备注 |
|---|---|---|
| text_path hit | ฿0.018 / 页 | Flash-Lite ($0.0005 ≈ ฿0.018) + L3 ~5% 触发 ฿0.005 均摊 |
| text_path miss(扫描/照片)| ฿0.075 / 页 | 当前 pipeline 单页成本(无变化)|

**混合场景预估**(基于审计推测的生产分布):

| 电子 PDF 占比 | text_path miss 占比 | 平均单页成本 | 对比当前 |
|---|---|---|---|
| 80%(生产估算)| 20% | ฿0.018 × 0.8 + ฿0.075 × 0.2 = **฿0.029** | **-60%** |
| 50%(test fixtures 比例)| 50% | ฿0.018 × 0.5 + ฿0.075 × 0.5 = **฿0.047** | -35% |
| 30% | 70% | ฿0.018 × 0.3 + ฿0.075 × 0.7 = **฿0.058** | -19% |
| 0%(全扫描)| 100% | ฿0.075 | 0% |

**80% 电子 PDF 假设下,1000 页/月成本从 ฿72 → ฿29,省 ~฿43/月**。100k 页/月 ~฿2900/月降本。

### 2.6 边界 case

| Case | 处理 |
|---|---|
| 电子 PDF 但文本层乱码(`■■■`)| pypdf 仍可能给 > 200 字符;layer 2 收到乱码会输出垃圾字段 → L1 conf 触发不到(没 conf 数据)→ 走 missing/math/pattern 触发器拉 L3 兜底 |
| 电子 PDF 但只有 1 页很短 | < 200 字符 → text_path miss → 走 Vision(无副作用)|
| pypdf import 失败 | text_path return None,走 Vision |
| pypdf 解析抛异常 | 同上 |
| max_pages 截断 | text_path 跟 layer 1 一样支持 max_pages,行为一致 |

### 2.7 与旧 pdf_text_extractor.py 的关系

- **旧 `pdf_text_extractor.py` 保留不动**(纪律保护)
- 新 `services/ocr/text_path.py` 是独立模块,**不 import 旧的**
- 当新 pipeline 100% 接入 + 稳定后,如果旧 app.py 路径也已删除,旧 `pdf_text_extractor.py` 可作为最后一波清理(决策 5)

### 2.8 配置项

新增 env(可选):
- `OCR_PIPELINE_ENABLE_TEXT_PATH=true/false`(默认 true) — 是否启用快速通道
- `OCR_PIPELINE_TEXT_PATH_MIN_CHARS=200`(默认 200) — 命中门槛

---

## 三、监控埋点对齐(任务 3)

### 3.1 现有 cost 监控基础设施

#### `ocr_cost_log` 表 schema([db.py:3725-3742](../../db.py))

```sql
CREATE TABLE IF NOT EXISTS ocr_cost_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    tenant_id UUID,
    history_id TEXT,                  -- 关联 ocr_history.id(UUID, 字符串存储)
    engine TEXT NOT NULL DEFAULT 'gemini',
    pages INTEGER NOT NULL DEFAULT 1,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost_thb NUMERIC(10, 4) NOT NULL DEFAULT 0,
    elapsed_ms INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- indices: user_id+created_at, created_at, tenant_id+created_at
```

#### 写入函数([db.py:3769](../../db.py))

```python
def log_ocr_cost(
    user_id: str,
    tenant_id: Optional[str],
    history_id: Optional[Any],   # 接受 str/UUID/int
    engine: str,
    pages: int,
    input_tokens: int,
    output_tokens: int,
    cost_thb: float,
    elapsed_ms: int,
) -> bool: ...
```

#### 配额累加函数

- [`increment_user_monthly_usage(user_id, n=1) -> int`](../../db.py)([db.py:459](../../db.py))— 月付用户配额,跨月自动重置,返回新 used_this_month
- [`increment_tenant_monthly_usage(tenant_id, n=1) -> int`](../../db.py)([db.py:3079](../../db.py))— 租户共享配额,同上逻辑

#### history 写入([db.py:599](../../db.py))

```python
def insert_ocr_history(
    user_id: str, filename: str, page_count: int, pages: list, confidence: str,
    elapsed_ms: int, file_size_kb=None, file_hash=None, archive_name=None,
    category_tag=None, source_pdf_id=None, source_page_indices=None,
    source_index=None, source_total=None, source="manual", source_ref=None,
    pdf_storage_path=None, pdf_size_bytes=None, client_id=None,
) -> Optional[str]: ...
```

#### 缓存查找

- [`find_ocr_by_hash(user_id, file_hash, max_age_hours=720, tenant_id=None)`](../../db.py)([db.py:722](../../db.py))— SHA-256 hash 命中 30 天内识别结果可跳过

#### 现有 dashboard 接口(app.py)

- `/admin/cost`(系统总览)— 读 `today_cost / month_cost / total_cost / 各 engine 分组`
- `/admin/tenant/<id>/cost`(单租户)— 类似
- 都基于 `ocr_cost_log` 聚合,只要 engine 字段值能区分,新 pipeline 自动在面板出现

### 3.2 新 pipeline 接入 app.py 时的精确埋点位置

**重要**:新 pipeline 自身不调任何 db 函数。**所有 db 调用都在 app.py 接入层完成**,跟现状一致。这样:
- pipeline 单元可测,无 db 依赖
- db 调用语义和现有路径完全一致,dashboard 不改

接入伪代码(将来在 app.py 第 1689-1798 行附近替换):

```python
# === 替换 app.py:1689-1761(旧 text_path → gemini → vision 链)===
if os.environ.get("OCR_USE_NEW_PIPELINE", "false").lower() == "true":
    from services.ocr.pipeline import run_on_pdf_bytes
    try:
        pipeline_result = run_on_pdf_bytes(
            content,
            max_pages=max_pages,
            api_key=api_key,
            enable_text_path=True,
        )
    except Exception as e:
        # 开发期回退到旧引擎(决策 4)
        logger.warning(f"pipeline failed, falling back to legacy: {e}")
        # ... 旧 gemini_engine.recognize_pdf 调用 ...
    else:
        # 把 PipelineResult 序列化成 app.py 期望的 result 字典
        result = _pipeline_result_to_legacy_dict(pipeline_result)
        chain_info = list(set(c for p in pipeline_result.pages for c in p.layer_chain))
else:
    # 旧链路保留(决策 1 + 5:稳定后删)
    ...

# === 后续 app.py 路径完全不变 ===
# is_not_invoice 检测、配额扣减、置信度评分、invoice_grouper、history 写入、cost log 都不动
```

### 3.3 PipelineResult → 旧 result 格式 mapper(必须实现)

新增 `services/ocr/legacy_adapter.py`(草案):

```python
def pipeline_result_to_legacy_dict(pr: PipelineResult) -> dict:
    """把 PipelineResult 转成 app.py 期望的旧 result 字典。
    
    旧 result 结构(来自 gemini_engine.recognize_pdf):
        {
            "pages": [
                {
                    "page_number": int,
                    "text": str,           # full text (可选)
                    "lines": list,         # 文本按行 (可选)
                    "fields": dict,        # ThaiInvoice fields (核心)
                    "is_copy": bool,       # 来自 is_copy_or_duplicate
                    "elapsed_ms": int,
                    "input_tokens": int,
                    "output_tokens": int,
                    "error": str | None,
                }
            ],
            "page_count": int,
            "elapsed_ms": int,
            "engine": str,
        }
    """
    pages_legacy = []
    for p in pr.pages:
        inv = p.invoice
        # ThaiInvoice 序列化为旧 fields 格式
        fields = inv.model_dump(mode="json")
        # 旧 schema 别名映射(若有,目前 ThaiInvoice 已用 seller_tax,无需别名)
        pages_legacy.append({
            "page_number": p.page_number,
            "text": "",  # 新 pipeline 不传完整 text 到这里
            "lines": [],
            "fields": fields,
            "is_copy": inv.is_copy_or_duplicate,
            "is_duplicate": False,  # invoice_grouper 后续标
            "elapsed_ms": p.total_ms,
            "input_tokens": p.layer2_input_tokens + p.layer3_input_tokens,
            "output_tokens": p.layer2_output_tokens + p.layer3_output_tokens,
            "error": p.error,
            # 新增,旧消费者忽略即可
            "_layer_chain": p.layer_chain,
            "_trigger_reasons": p.trigger_reasons,
            "_needs_manual_review": p.needs_manual_review,
            "_layer1_avg_confidence": p.layer1_avg_confidence,
        })
    return {
        "pages": pages_legacy,
        "page_count": pr.page_count,
        "elapsed_ms": pr.elapsed_ms,
        "engine": pr.engine,  # "pipeline_v1"
    }
```

### 3.4 监控字段对照表(新旧 engine 值)

| engine 字段值 | 含义 | 在新 pipeline 里出现吗 |
|---|---|---|
| `"gemini"` | 旧主引擎(图 + 字段一起)| 否(旧路径)|
| `"cache"` | hash 命中跳过 OCR | 是(app.py 第 4.5 步,不动)|
| `"text"` | 旧 pdf_text_extractor 命中 | 否(旧路径)|
| `"google_vision"` | 旧 Vision 兜底 | 否(旧路径)|
| **`"pipeline_v1"`** | **新三层 pipeline** | ✅(整体)|
| (可选)`"pipeline_v1_text_path"` | text_path hit 子分类 | ✅(若拆分)|
| (可选)`"pipeline_v1_vision"` | text_path miss → Vision 子分类 | ✅(若拆分)|

**决策建议**:**先用单一 `"pipeline_v1"`**,所有新流量统一 engine 值,dashboard 上看总成本最直观。需要细分时再加 `layer_breakdown` JSON 字段(migration-plan.md §3.6 已规划)。

### 3.5 接入时不改任何 db.py 代码

- ✅ `log_ocr_cost`:新 engine 值 `"pipeline_v1"` 用 schema 现有 `engine TEXT` 字段即可
- ✅ `insert_ocr_history`:`pages` 是 JSONB,新增的 `_layer_chain` 等键不影响旧消费者
- ✅ `increment_user_monthly_usage` / `increment_tenant_monthly_usage`:不变,仍按 page_count 累加
- ✅ `find_ocr_by_hash`:不变,SHA-256 文件指纹仍生效
- ✅ `ocr_history.pages.fields.*` 字段命名:用 `seller_tax / buyer_tax`(决策 2 兼容旧名)

**唯一可能需要的改动**:`ocr_cost_log.engine` 字段长度。看 schema 是 `TEXT`,可变长,无限制。**无需 migration**。

### 3.6 dashboard 新 engine 自动可见

`/admin/cost` 当前的聚合查询:

```sql
SELECT engine, COUNT(*) AS cnt, COALESCE(SUM(cost_thb), 0) AS cost
FROM ocr_cost_log
GROUP BY engine
ORDER BY cost DESC
```

新 `"pipeline_v1"` 流量自动出现在结果里。**dashboard 代码零改动**。

---

## 四、阶段 3 第 5 步实施清单(供下一步执行参考)

按依赖顺序:

1. **写 `services/ocr/text_path.py`**(纯 pypdf 文本提取,~80 行)
2. **改 `services/ocr/pipeline.py`**:在 `run_on_pdf_bytes` 开头加 layer 0 试探,Page 序列化路径不变
3. **写 `services/ocr/legacy_adapter.py`**(`pipeline_result_to_legacy_dict`,~40 行)
4. **接入 app.py**:在 `/api/ocr/recognize` 第 1689 行替换为 feature-flag-gated 新 pipeline 调用 + 调 `pipeline_result_to_legacy_dict`;LINE bot / email_ingest / recon_routes 同样接入(决策 4)
5. **db schema 改动**:**无**(`ocr_cost_log.engine = "pipeline_v1"` 用现有字段)
6. **配额 / cost log 调用**:app.py 现有代码完全保留,只是读 `result` 来源改了

**完整接入工作量估算**:
- text_path.py:0.5 天
- pipeline.py 改:0.5 天
- legacy_adapter.py:0.5 天
- app.py 接入 4 个入口:1 天
- 测试(单元 + e2e):1-2 天
- 灰度上线 + 监控对账(决策 4):1-2 天

**总计:5-7 天**,如果 B1/B2 / 准确率 baseline 没有再发现新问题。

---

## 六、🚨 调研 4:埋点漏记排查(2026-05-18 紧急追加)

### 6.1 起因

Google AI Studio 真实账单 vs 系统 dashboard:
- Google 真实已花:**฿129.83**
- 系统 dashboard 显示:**฿17.59**
- 差异:**฿112.24(差 7.4 倍,只记录了 14%)**

**这是上线收费的致命问题。新 pipeline 接入时必须做到 100% 埋点。**

### 6.2 `log_ocr_cost` 调用位置(完整清单 — 只有 3 处)

```
db.py:3769         def log_ocr_cost(...)                        # 函数定义
app.py:1645        engine="cache" 缓存命中路径
app.py:2141        engine="gemini"/"google_vision"/"text_path"  主路径
vat_excel_routes.py:179   engine="gemini-vex"                   VAT 公式对账导出
```

**结论:仅 web 上传主路由 + VAT 公式对账导出有埋点;其他全部漏记。**

### 6.3 API 调用 vs log_ocr_cost 对照表(完整漏记清单)

按"调用模式 → 是否记 cost"分类:

#### A. ✅ 有埋点(2 个调用点)

| 调用点 | 文件 | API 调用 | log_ocr_cost engine 值 |
|---|---|---|---|
| `/api/ocr/recognize` 缓存命中 | [app.py:1645](../../app.py) | 无 API(命中跳过)| `"cache"`,cost=0 |
| `/api/ocr/recognize` 主路径 | [app.py:2141](../../app.py) | `gemini_engine.recognize_pdf` 或 vision 兜底 | `"gemini"` / `"google_vision"` / `"text_path"` |
| `/api/vat-excel/build` 导出 | [vat_excel_routes.py:179](../../vat_excel_routes.py) | `vat_excel_export.extract_invoice_fields` ×N + `vat_report_parser.parse_vat_report` | `"gemini-vex"`(汇总聚合)|

#### B. ❌ 无埋点(10+ 个 API 调用点)

| 调用点 | 文件 | API 调用 | 量级估算 |
|---|---|---|---|
| **LINE bot OCR** | [app.py:5560](../../app.py)(`_handle_line_image_ocr`)| `gemini_engine.recognize_pdf`(每张 LINE 上传一次)| LINE 是手机用户主入口,日活 N x 每人多张 |
| **邮件附件自动 OCR** | [email_ingest.py:293](../../email_ingest.py) | `gemini_engine.recognize_pdf`(每个邮箱附件)| 后台轮询邮箱,可能每小时若干张 |
| **VAT 批量对账 OCR** | [recon_routes.py:702](../../recon_routes.py) | `gemini_engine.recognize_pdf` × **20 路 asyncio.Semaphore** 并发 | **量最大** — 月底一次批量处理可能成百上千张 |
| **银行对账单 OCR** | [bank_recon_v2.py:1017](../../bank_recon_v2.py) | 直接 `model.generate_content` (gemini-2.5-flash-lite) | 银行对账每周 / 每月,单次 PDF 可几十页 |
| **GL PDF 解析 fallback** | [bank_recon_v2.py:1844](../../bank_recon_v2.py) | 直接 `model.generate_content` (gemini-2.5-flash) | pdfplumber 失败时兜底 |
| **VAT 报告扫描 OCR** | [vat_report_parser.py:639](../../vat_report_parser.py) | 直接 `model.generate_content` (gemini-2.5-flash) | VAT 报告 PDF 扫描分支 |
| **VAT 发票字段抽取** ×2 | [vat_excel_export.py:135, 592](../../vat_excel_export.py) | 直接 `model.generate_content` (gemini-2.5-flash) | vat-excel/build 内部子调用 |
| **VAT 文件分类** | [vat_file_classifier.py:128](../../vat_file_classifier.py) | 直接 `model.generate_content` (gemini-2.5-flash) | VAT 批量工作流前置 |
| **VAT 差异 AI 分析** | [vat_ai_analyzer.py:88](../../vat_ai_analyzer.py) | 直接 `model.generate_content` (gemini-2.5-flash) | 用户点开差异行才调,但若 row 多则成本累加 |
| **Gemini key 健康检查** | [app.py:4266](../../app.py) | 直接 `model.generate_content` (1-2 token "ok") | 微量,但每次 admin 测试 key 都触发 |

#### C. ⚠️ 有埋点但**漏计 Vision 单页成本**

[app.py:2131](../../app.py) 的成本公式:
```python
cost_usd = (total_input_tokens * input_per_m_usd + total_output_tokens * output_per_m_usd) / 1_000_000
```

**问题**:Vision API 按"每页 $0.00150"计费,**不是按 token**。当 `chain_info[0] == "google_vision"`(Vision 兜底)时,Vision 的固定每页成本完全没进公式 — 只有后续 `restructure_with_text_hint` 的 token 进了。

每次 Vision 兜底 = 漏记 $0.00150 ≈ ฿0.05 / 页。

#### D. ⚠️ 校准系数 calibration_factor = 1.10 远远不够

[app.py:2128](../../app.py) 用 `calibration_factor = 1.10`(只 +10%)补救公式不准。
但实测 Google 真账单 / 系统记录 = **7.4 倍**(740% 偏差,1.10 是 110%)。
**这个系数本身就是错的,而且方向不对** — 应该解决漏记问题,不是后置乘个系数。

#### E. ⚠️ Gemini 内部重试 / 多次调用不另外计费

`gemini_engine.recognize_pdf` 单次调用内部对每页并发 3 路 + 失败重试,但只回报最终 `total_input_tokens / total_output_tokens` 汇总。**重试次数不可见**,如果某页重试 N 次,每次都算 token,但日志里看不出 retry 次数 — 这部分本身就在 Gemini 的回传里,所以**不漏记**,只是不可观测。

### 6.4 7.4 倍偏差的可能解释(假设分布)

| 漏记来源 | 估算占比 | 备注 |
|---|---|---|
| VAT 批量对账(recon_routes,20 路并发,量最大)| **~50-60%** | 月底处理几百张 |
| LINE bot OCR | **~10-15%** | 日均活跃 LINE 用户量 |
| email_ingest | ~5-10% | 后台轮询频率决定 |
| bank_recon_v2(银行对账 + GL fallback)| ~5-10% | 单次 PDF 可几十页 |
| Vision 单页成本漏算 | ~5% | 取决于 Vision 兜底触发率 |
| VAT 子调用(file_classifier + report_parser + ai_analyzer)| ~3-5% | 用户交互行为决定 |
| 其他(key 健康检查等)| < 1% | 微量 |

**这些都需要新 pipeline 接入时全部覆盖。**

### 6.5 旧代码漏埋点是否要补?

**用户工作纪律**:旧 OCR 引擎文件只读不改,vat_excel_* / bank_recon_v2 / vat_file_classifier 等 9+ 处直调 genai 的模块**不在本次迁移范围**。

**结论**:**不去修旧代码的漏记**。这是 OCR 迁移之外的另一个独立问题(可由屎山清理会话或单独立项处理)。本次 OCR 会话**只确保新 pipeline 100% 埋点**,避免新增漏记 + 在新流量上线后,新 pipeline 的真实成本能反映 Google 真账单 1:1。

---

## 七、调研 5:新 pipeline 100% 埋点设计

### 7.1 设计原则

1. **每次 API 调用都记一条 ocr_cost_log** — 包括失败的、被重试的、缓存命中的
2. **Vision 单页成本进公式** — 修复§6.3.C 的漏算
3. **多层调用聚合一条 vs 每层一条** — 优先**每张文件一条**(主条目),detail 写入 `layer_breakdown` JSON 字段(可选)
4. **失败时仍要记** — 哪怕只跑到 L1 就挂了,L1 的 Vision 调用费已经发生,必须记
5. **测试流量与生产流量分开** — 通过 engine 字段后缀或独立 env / user_id 隔离

### 7.2 强制埋点点位 — 三层 + pipeline 出口

```
┌──────────────────────────────────────────────────────────────────┐
│  pipeline.run_on_path(...)                                        │
│    │                                                              │
│    ├──► [Layer 0: text_path] ────► 0 API call, 0 cost            │
│    │                                                              │
│    ├──► [Layer 1: Vision] ────► +1 Vision call per page          │
│    │       └─► track: pages, $0.00150/page                       │
│    │                                                              │
│    ├──► [Layer 2: Flash-Lite] ────► +1 Gemini call per page      │
│    │       └─► track: input_tokens, output_tokens, retries       │
│    │                                                              │
│    └──► [Layer 3: Flash (conditional)] ────► +1 Gemini call      │
│            └─► track: input_tokens, output_tokens, retries       │
│                                                                   │
│    Return PipelineResult with EXACT cost breakdown               │
│      pages[].layer1_vision_pages_billed                           │
│      pages[].layer2_input_tokens / output_tokens / retries        │
│      pages[].layer3_input_tokens / output_tokens / retries        │
└──────────────────────────────────────────────────────────────────┘

   ▼ app.py adapter MUST call:

   db.log_ocr_cost(
       user_id, tenant_id, history_id,
       engine="pipeline_v1",         # or "pipeline_v1_test"
       pages=result.page_count,
       input_tokens=Σ(L2 in) + Σ(L3 in),
       output_tokens=Σ(L2 out) + Σ(L3 out),
       cost_thb=result.estimated_cost_thb,  # ← MUST include Vision $/page
       elapsed_ms=result.elapsed_ms,
   )
```

### 7.3 失败 / 重试调用的记录策略

**问题**:当前 pipeline 设计在 Layer2AuthError / Layer3FallbackError 时**抛异常**,调用方拿不到 PipelineResult。但 L1 已经花了 Vision 钱,L2 也可能花了 Gemini 钱。

**解决方案**:**改 pipeline 永远返回 PipelineResult,即使中途失败**。

具体修改(留给阶段 3 实施):
- `pipeline.run_on_path` 内部 catch 所有 Layer 异常
- 失败时仍构造 PipelineResult,字段填:
  - `pages = [PipelinePageResult(error="LayerXError: ...", layer1_billed=True/False, layer2_billed=True/False, ...)]`
  - `estimated_cost_thb = 已实际消费的成本(L1 已billed × $0.0015 + L2 used tokens cost)`
- 调用方仍能正常 log_ocr_cost,只是 engine 后缀 `_failed`

新 engine 值:
- `"pipeline_v1"` — 全程成功
- `"pipeline_v1_partial"` — L1 + L2 通过,L3 失败但有 L2 兜底
- `"pipeline_v1_failed"` — L1/L2 失败,pages 可能空但 Vision 已 billed

dashboard 自动分组,失败的也能看到成本占比。

### 7.4 缓存命中也要记(0 成本,但有量)

**沿用现有约定**([app.py:1645](../../app.py)):
- engine = `"cache"`(不变)
- pages = N(虚拟,跟原识别一致)
- input_tokens = 0,output_tokens = 0
- cost_thb = 0
- 这样 dashboard 能看到"缓存省了多少次"

新 pipeline 不在自己内部判缓存(那是 app.py 的责任,见现有逻辑),所以缓存命中**仍由 app.py 调 log_ocr_cost**,跟现状一样。

### 7.5 测试 vs 生产隔离 — 3 个选项

| 方案 | 实现 | 优 | 缺 |
|---|---|---|---|
| **A. engine 字段后缀** | env `OCR_PIPELINE_MODE=test` → engine = `"pipeline_v1_test"` | 简单,dashboard 自动隔离;原表无需 schema 改动 | 测试数据仍在生产表,长期会污染聚合 |
| **B. 独立 ocr_cost_log_test 表** | 测试模式写到 `ocr_cost_log_test`(同 schema)| 数据完全隔离 | 需要 db migration,dashboard 要双查询 |
| **C. 测试 user_id 白名单 + 默认排除** | dashboard query 默认 WHERE user_id NOT IN (test_users) | 零代码改动 | 依赖 dashboard 实现自觉,容易漏掉 |

**推荐 A**:engine 字段后缀,零 schema 改动,后期可清理。

实施细节:
```python
# 在 pipeline.run_with_cost_logging 包装层
mode = os.environ.get("OCR_PIPELINE_MODE", "prod")
engine = "pipeline_v1" if mode == "prod" else f"pipeline_v1_{mode}"
db.log_ocr_cost(..., engine=engine, ...)
```

测试时:`OCR_PIPELINE_MODE=test python tests/run_pipeline_batches.py`
生产时:env 不设 / 设 prod,默认 engine="pipeline_v1"。

### 7.6 OCR_PRICING 常数对齐

[db.py](../../db.py) 已定义 `OCR_PRICING`(在 `app.py:2131` 被引用):
- `input_per_m_usd`(input tokens / 1M)
- `output_per_m_usd`
- `usd_thb`(汇率)

**漏的**:Vision per-page 价格。建议:
```python
# db.py 内 OCR_PRICING 扩展
OCR_PRICING = {
    "input_per_m_usd": 0.10,       # Flash-Lite 输入
    "output_per_m_usd": 0.40,      # Flash-Lite 输出
    "flash_input_per_m_usd": 0.30, # Flash 输入(L3 用)
    "flash_output_per_m_usd": 2.50,# Flash 输出
    "vision_per_page_usd": 0.00150, # Vision per page  ← 新增
    "usd_thb": 35.0,
}
```

`pipeline.py` 内 `_compute_total_cost` 用同一套常数,确保 dashboard 和 pipeline 计算一致。

更好:**pipeline.py 内部根本不算 cost,只汇报 raw(pages_with_vision, l2_tokens, l3_tokens),由调用方 / db.log_ocr_cost 统一算**。这样汇率 / 单价改动只改 db.py 一处,不用动 pipeline。

### 7.7 接入 app.py 时的强制 checklist(供阶段 3 第 5 步实施)

每个 OCR 入口接入新 pipeline 时,**必须**:

- [ ] try / finally 包裹 `pipeline.run(...)` 调用
- [ ] **不论成功失败**,finally 块调 `db.log_ocr_cost(...)`(engine 区分 `pipeline_v1` / `_partial` / `_failed`)
- [ ] cost_thb 算入 Vision per-page 成本(L1 跑过的页数 × $0.00150 × usd_thb × calibration)
- [ ] input_tokens = L2 in + L3 in,output_tokens = L2 out + L3 out
- [ ] pages = 真实处理过的页数(不是 PDF 总页数)
- [ ] history_id = `insert_ocr_history` 返回的 id(失败也 None)
- [ ] 缓存命中不走新 pipeline(继续走 app.py:1645 旧路径,engine="cache",不变)

四个入口都要按这个 checklist 接:主 `/api/ocr/recognize` / LINE bot / email_ingest / recon_routes。**这一次接入就把现有 3 个漏记的入口顺手补上**(LINE + email + recon_routes,bank_recon_v2 + vat_* 不在本次范围)。

### 7.8 接入后的"真账单 vs 系统 dashboard"自检

接入完成 + 灰度上线 1-2 天后,**强制核对**:
```sql
-- 系统视角:新 pipeline 总成本
SELECT SUM(cost_thb) FROM ocr_cost_log
WHERE engine LIKE 'pipeline_v1%'
  AND created_at >= '<切流量起点>'
  AND created_at < '<核对时刻>';

-- Google 真账单(手工对比 GCP Cloud Vision + AI Studio 同期消费)
-- 若两个数字差 > 10% → 排查埋点漏点
```

校准:计算 `calibration_factor_new = Google真账单 / 系统记录`,把这个值写入 `db.balance_logs` 表(已有 `calibration_factor` 字段),后续 dashboard 自动用新值显示。**目标:1.00 ± 0.05**(误差 < 5%)。

**如果接入后这个比值仍 > 1.5**,说明还有埋点漏掉,**回到 §6.3 表逐个检查**。

---

## 五、不在范围 / 留给后续

- 把 ocr_cost_log.engine 拆成 `pipeline_v1_text_path / pipeline_v1_vision / pipeline_v1_l3` 细分子类
- 加 `ocr_pipeline_audit` 表(详细记录每页走了哪些层、各层成本、触发原因)— migration-plan.md §3.6 提及
- 把 word-level confidence 数据写到 `ocr_history.pages.fields._confidence` 子字典 — migration-plan.md 决策 2 已规划
- 把"低置信度队列"(needs_manual_review)做成真实 DB schema + 人工复核 UI

---

*fast-path-design.md 完成,等用户审 + 决定下一步是否开始实施。*
