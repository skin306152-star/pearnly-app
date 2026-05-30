# OCR-core 真重构轮草案(WA · 达 <500 最后一程)· REFACTOR-WA-OCRSPLIT-R2

> **前置**:纯搬家批(P-A/P-C/L2-A/P-B)已全部完成并真账号 E2E 验过(见 `WA_OCR_CORE_SPLIT_PLAN.md`)。
> 现状:`pipeline.py` **751** · `layer2_structure.py` **850**(均 >500·warning-mode 不阻)。
> 本草案 = 达标铁律#27(<500)所需的**真重构刀**(P-D / L2-B / L2-C)。
> **它们与纯搬家批的区别**:不是「整段 verbatim 挪走 + re-export」那么平,牵涉编排面 / prompt 跨域 / 算法段内部切分 → 风险更高 → **请主控交叉验证本草案后我才逐刀自跑自验**(不自行起步)。
> ⚠️ 红线不变:OCR 抽取算法判定 / 扣费 / 对账判定字段**一字不动**;每刀独立 commit;绝不 --no-verify;真账号 field-diff E2E(含 L3 触发票)兜底。

---

## 已核证的事实(写草案前实测)

- **无循环依赖**:`layer1_vision` / `layer2_structure` / `layer3_fallback` / `validators` / `triggers` / `cost` **均不 import pipeline**(grep 实测空)→ 新建 `page_runner.py` import 这些叶子 + `pipeline` import `page_runner` 不成环。
- `pipeline.py` 顶部已把 L1/L2/L3 入口以别名引入:`extract_from_image_bytes as _l1_extract_image`(layer1)、`extract_from_page as _l2_extract_page`(layer2)、`refine_page as _l3_refine_page`(layer3)。
- `_process_one_page`(531-736·206 行)调用面(AST 实测):`_l1_extract_image`/`_l2_extract_page`/`_l3_refine_page` + triggers 4 名(`_aggregate_page_confidence`/`_bucket_confidence`/`_count_invoice_no_candidates`/`_evaluate_triggers`)+ validators 3 名(`validate_invoice`/`validate_gl_document`/`validate_bank_document`)+ `InvoicePatternMemory.record` + 构造 `PipelinePageResult`。**全是已 import 的叶子名** → 搬走后 page_runner 同样 import 即可。
- `_call_gemini_with_retry`(layer2_structure 729-845·117 行)**重度 prompt 耦合**:用 `_SYSTEM_PROMPT`/`_USER_PROMPT_PREFIX`/`_RETRY_TRIM_HINT` + `_DOC_PROMPTS`(→ `_GL_SYSTEM_PROMPT`/`_BANK_STATEMENT_SYSTEM_PROMPT`/`_VAT_REPORT_SYSTEM_PROMPT`/`_GENERIC_TABLE_SYSTEM_PROMPT`/`_SYSTEM_PROMPT`)。这些 prompt 常量本身 ~300 行,是 layer2 抽取算法的「判定语料」。

---

## P-D · `_process_one_page` → `services/ocr/page_runner.py`

| 项 | 内容 |
|---|---|
| 抽出 | `_process_one_page`(531-736·206 行)+ 其私有辅助(若有 page 级 helper 仅它用) |
| 落点 | 新 `services/ocr/page_runner.py`(~210 行) |
| 接线 | page_runner `from .layer1_vision import extract_from_image_bytes as _l1_extract_image`(L2/L3 同)+ `from .triggers import (...)` + `from .validators import (...)` + `from .schemas import Page, PipelinePageResult, BusinessDocumentType`;`pipeline` 顶部 `from .page_runner import _process_one_page  # noqa: F401` re-export → 唯一调用方 `_process_pages` 0 改动 |
| 机制 | **仍是 verbatim 整段挪 + re-export**(与纯搬家同机制)·0 逻辑改 |
| 为何列「真重构 / 谨慎」 | 它是**高敏 per-page 总指挥**(L1→L2→L3→触发→校验→pattern.record→构造结果),import 面跨 5 模块。机制虽平,但「改动即触及整条识别热路径的装配点」→ 主控要求单独轮、不混进搬家 commit。 |
| 收益 | pipeline 751 → **~545**(仍略 >500) |
| E2E | INV2026030010(4页·page2 L3=True·`total_amount missing`)+ INV2026030004(2页·L3=False·3750+262.50=4012.50)逐字段一致 + `_layer_chain` 不变(与 P-B 同两票回归) |
| 风险/回退 | import 漏带 → `import app` 即红(本地拦);`PipelinePageResult` 字段构造须逐字保留;红则 `git revert` |

## L2-B · `_call_gemini_with_retry` + 默认发票 prompt → `services/ocr/layer2_gemini.py`(并入 L2-A 已建模块)

| 项 | 内容 |
|---|---|
| 抽出 | `_call_gemini_with_retry`(729-845·117)+ `_SYSTEM_PROMPT`(319-)/`_USER_PROMPT_PREFIX`(391)/`_RETRY_TRIM_HINT`(90-) |
| 落点 | 并入 `services/ocr/layer2_gemini.py`(L2-A 建·现 Gemini 传输层)→ 成「layer2 Gemini 调用 + 默认发票 prompt」模块 |
| 机制 | 函数 verbatim 挪 + **仅带默认 invoice prompt 三常量**(`_SYSTEM_PROMPT`/`_USER_PROMPT_PREFIX`/`_RETRY_TRIM_HINT`)。**调用图已实测厘清边界(2026-05-31)**:<br>• 函数签名有 `system_prompt_override: Optional[str]=None` — 默认走 module-global `_SYSTEM_PROMPT`,GL/bank/vat 由调用方传 `_DOC_PROMPTS[...]` 作 override。<br>• **AST 实测函数体只引用那 3 个默认常量,不引用 `_DOC_PROMPTS`** → `_DOC_PROMPTS` + 5 个 doc-type prompt **留 layer2_structure**(它们由调用方 `_extract_doc_internal`655/`_extract_internal`713 持有并以参数传入,不随函数走·无反向依赖)。<br>• `layer3_fallback.py:375` 有**自己独立的同名** `_call_gemini_with_retry`(非 layer2 这个)→ 不受影响。<br>⇒ 边界干净:只搬 1 函数 + 3 常量,比草案初判风险低。 |
| 为何「真重构」 | 跨 extraction-domain(传输 helper 与「默认发票判定语料」纠缠)·非自洽 |
| 收益 | layer2_structure 850 → **~620**(仍 >500 → 需 L2-C) |
| E2E | 同两票 + 一张数字 PDF 多票/GL 或 bank 文档(确认非发票路径 prompt 未受影响) |

## L2-C · 抽取算法段内部再拆(layer2_structure → <500)

| 项 | 内容 |
|---|---|
| 现状 | L2-B 后 layer2_structure 剩 ~620:`extract_from_text/page/layer1`(397-591)+ `_extract_doc_internal`/`_extract_internal`(612-726)+ `_DOC_PROMPTS` + GL/BANK/VAT/TABLE prompt 常量(~300 行 prompt) |
| 候选 | (a) prompt 常量族(`_*_SYSTEM_PROMPT`×5 + `_DOC_PROMPTS`)→ `services/ocr/layer2_prompts.py`(纯数据·最安全·~300→挪后 layer2_structure 立降 <500);(b) 抽取编排 `_extract_doc_internal`/`_extract_internal` 另置 |
| 建议 | **优先 (a) prompt 常量外提**——纯字符串数据搬家、0 逻辑、风险最低,且单刀即可能把 layer2_structure 砍到 <500,可能让 L2-B 都不必做。**这一刀其实接近纯搬家** → 若主控同意,可并回纯搬家节奏 |
| 为何谨慎 | prompt 是抽取算法的判定语料,「一字不动」尤其关键;外提后 `extract_*` 改 `from .layer2_prompts import ...` |
| E2E | 发票 + GL + bank + vat 各一,确认四类 prompt 行为不变 |

---

## 建议执行序(请主控裁定)

1. **L2-C(a) prompt 常量 → layer2_prompts.py**(最低风险·可能单刀达标 layer2 <500·近纯搬家)→ 若同意,我按纯搬家节奏自跑自验。
2. **P-D `_process_one_page` → page_runner.py**(机制平·但高敏装配点·单独 commit + 两票 E2E)。
3. **L2-B**(仅当 L2-C(a) 后 layer2 仍 >500 才需;先读 `_call_gemini_with_retry` 全调用图定边界)。

**达标预估**:L2-C(a) → layer2 ~550 或更低;P-D → pipeline ~545。两者仍可能略 >500 → 是否再切一刀(P-D 后 pipeline 残留 `run_on_*` 编排 / L2 残留抽取段)由主控定;warning-mode 不阻线上,**不为凑行数硬切高敏编排**。

## 请主控交叉验证
- [ ] 接线 / re-export 口径无误(尤其 P-D import 面、L2-B 的 `_DOC_PROMPTS` 边界)。
- [ ] 执行序认可(默认:先 L2-C(a) prompt 外提)。
- [ ] E2E 票样够(两票回归 + GL/bank/vat 各一覆盖非发票 prompt)。
- [ ] 哪几刀算「可并回纯搬家自跑自验」(我判 L2-C(a) 接近纯搬家),哪几刀必须逐刀报。

> 验过我按 AUTONOMOUS_LOOP 逐刀自跑自验(契约 assertIs + 功能锁 + 全量 unittest + import app → push → 部署 → 真账号 field-diff E2E 含 L3 触发票 → 绿才下一刀 · 红 revert)。
