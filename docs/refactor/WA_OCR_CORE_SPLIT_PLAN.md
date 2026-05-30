# OCR-core 拆分草案(WA)· REFACTOR-WA-OCRSPLIT

> **进度**:✅ **L2-A 已落地+真账号 E2E 验过**(commit `5ba582c`·layer2_structure 981→850·新 layer2_gemini.py 169·AST 精切 verbatim·re-export 身份不变·契约 4 测+COV4 14 测经 facade 绿·部署后 INV2026030007 字段全对 2160+151.20=2311.20 VAT7%·L3 不变·prod 200)。下一刀:P-A cost.py(最小最纯)→ P-C/P-B → L2-B(prompt-coupled·真重构·单独轮)。

> 目标:`services/ocr/pipeline.py`(1044)+ `services/ocr/layer2_structure.py`(981)→ 各 <500(铁律#27)。
> 方法:**纯结构搬家(copy-out + 文件尾 re-export 回原命名空间 → 调用方 0 改动 + 契约 assertIs 锁同一对象)** 为主;
> 碰到 prompt-coupled 的 `_call_gemini_with_retry` 标记为「真重构/谨慎」后做或拆细。
> 安全网:每刀 push 后真账号 OCR field-diff E2E(pearnly_e2e_1·额度 999999)。**不一次切到 <500**——先定哪几刀本轮做。
> ⚠️ 0 逻辑改:绝不动 OCR 抽取算法/扣费/对账判定字段;只挪函数位置 + 接线。

---

## A. pipeline.py(1044 → 目标 <500)

| 刀 | 抽出内容(现行号) | 落新模块 | ~行 | 类型 | 跨模块接线 |
|---|---|---|---|---|---|
| **P-A** | `_compute_total_cost`(1020-1044)+ COST_* 5 常量(155-159)+ `COST_VISION_PER_PAGE_USD`/`THB_PER_USD` | `services/ocr/cost.py` | ~55 | **纯搬家** | pipeline `from .cost import _compute_total_cost, *COST*`;无外部 caller(私有) |
| **P-B** | 触发/置信纯逻辑:`_evaluate_triggers`(850-962)·`_count_invoice_no_candidates`(963-992)·`_check_amount_math`(993-1019)·`_aggregate_page_confidence`(813-836)·`_bucket_confidence`(837-849)+ 相关常量(CONFIDENCE_THRESHOLD/AMOUNT_TOLERANCE_THB/CRITICAL_FIELDS/CONFIDENCE_AUTO_THRESHOLD/CONFIDENCE_REVIEW_THRESHOLD) | `services/ocr/triggers.py` | ~200 | **纯搬家**(纯决策·不调 L1/L2/L3) | 依赖 `.confidence`(已是 leaf)+ `.schemas`;pipeline import 回;无外部 caller |
| **P-C** | `InvoicePatternMemory` class(187-272)+ `MIN_INSTANCES_BEFORE_FLAGGING` | `services/ocr/pattern_memory.py` | ~95 | **纯搬家**(自洽 class·跨页 pattern 学习态) | pipeline + 调用方拿 `InvoicePatternMemory` → pipeline 顶部 `from .pattern_memory import InvoicePatternMemory` re-export(调用方 `from services.ocr.pipeline import InvoicePatternMemory` 0 改动) |
| **P-D** | `_process_one_page`(602-812·~210)+ per-page L1→L2→L3 编排 | `services/ocr/page_runner.py` | ~210 | **真重构/谨慎** | 它是指挥(调 `_l1_extract_image`/`_l2_extract_page`/`_l3_refine_page`/triggers/cost)→ import 多·需防循环(page_runner import 各 layer + triggers + cost;pipeline import page_runner)。**最后做·单独交叉验证** |

**P-A+P-B+P-C(全纯搬家)**:1044 → **~700**。**+P-D**:~700 → **~490 <500 ✓**(但 P-D 是真重构)。
本轮建议:**做 P-A / P-B / P-C(纯搬家·安全)**;P-D 留下一轮单独交叉验证(它把 `_process_one_page` 整段挪走·虽 0 逻辑但 import 编排面大)。

## B. layer2_structure.py(981 → 目标 <500)

| 刀 | 抽出内容(现行号) | 落新模块 | ~行 | 类型 | 跨模块接线 |
|---|---|---|---|---|---|
| **L2-A** | Gemini 纯传输 helper:`Layer2Error`+3 子类(100-115)·`_parse_json`(853-878)·`_classify_gemini_exception`(881-928)·`_model_cache`/`_model_lock`(934-935)·`_get_model`(938-981)+ `DEFAULT_TEMPERATURE`/`DEFAULT_MAX_OUTPUT_TOKENS`(74,78·仅 _get_model 用) | `services/ocr/layer2_gemini.py` | ~165 | **纯搬家**(无 prompt/抽取依赖) | layer2_structure 顶部 re-import 全部 7 名(异常×4+_parse_json+_classify+_get_model)→ COV4 `test_ocr_gemini_helpers`(测 l2._parse_json/_classify/Layer2*)+ 抽取段 `raise Layer2AuthError`/`_call_gemini_with_retry` 都经 re-import 名·0 改动 |
| **L2-B** | `_call_gemini_with_retry`(734-851·~118)+ prompt 常量 `_SYSTEM_PROMPT`/`_USER_PROMPT_PREFIX`/`_RETRY_TRIM_HINT` | 并入 `layer2_gemini.py`(成「layer2 Gemini 调用」模块) | ~150 | **搬家但跨 extraction-domain**(函数烤进了默认发票 prompt)→ 谨慎·L2-A 稳后做 | _call_gemini_with_retry 用 _get_model/_parse_json/_classify(同模块)+ 2 prompt 常量(一并搬)·extraction 段 import 回 `_call_gemini_with_retry` |
| **L2-C** | 抽取算法 `extract_from_text/page/layer1`·`_extract_doc_internal`·`_extract_internal`(402-733·~330) | 留 layer2_structure(这就是 layer2 的本职) | — | — | — |

**L2-A**:981 → **~820**。**+L2-B**:~820 → **~670**。仍 >500 → 到 <500 需再拆抽取段(L2-C 内部·**真重构**·算法编排面大)→ **留后·单独交叉验证**。
本轮建议:**做 L2-A(纯搬家·安全·已被 COV4 单测覆盖那两个 helper)**;L2-B 次轮;<500 达标需 L2-C 真重构(再议)。

---

## C. 本轮建议执行集(全「纯搬家」· 拿 999999 额度 OCR E2E 兜底)

按风险从低到高、各独立 commit:
1. **P-A cost.py**(最小最纯)
2. **P-C pattern_memory.py**(自洽 class)
3. **P-B triggers.py**(纯决策逻辑·~200 行)
4. **L2-A layer2_gemini.py**(Gemini 传输 helper)

每刀:契约 assertIs 单测(锁 `pipeline.X is cost.X` 等同一对象)+ 全量 unittest + import app → push → 部署 → **真账号 field-diff E2E**(下方)→ 绿才下一刀;红则 revert。
4 刀后:pipeline 1044→~700 · layer2 981→~820(均仍 >500·warning-mode 闸不阻)·但**结构显著解耦 + 0 风险**。
<500 达标的最后几刀(P-D `_process_one_page` 真重构 / L2-B prompt-coupled / L2-C 抽取段)= **下一份草案单独交叉验证**。

## D. 每刀 E2E 验证点(field-diff·额度管够)

- **票样**:① 数字 PDF 单票 `D:/测试PDF/3.69/*INV2026030004*`(2页·1票)② hires 图 `D:/测试图片/hires/hires_INV2026030002.png`(4678px·走 Step3 压缩路径)。**用唯一文件名/重存避 file-hash 缓存**(铁律#25.4)。
- **比对**:`invoice_number/date/seller_tax/buyer_tax/subtotal/vat/total_amount/items 数` 逐项一致(改前在 origin 上跑一次存基线·改后再跑对比;或与已知值对:030004=3750+262.50=4012.50·VAT7%)。
- **L3 触发**:读响应 `pages[]._layer_chain` 是否含 L3 → 不应变化(纯搬家不动触发逻辑)。
- 绿 = 该刀完成;任一字段差/报错/L3 异常 = revert 查根因。

## E. 不做 / 红线

- 绝不动:OCR 抽取算法判定、扣费(charge_ocr*)、对账判定字段。
- P-D/L2-B/L2-C(真重构/prompt-coupled)本轮**不做**·等本草案 C 节 4 刀稳 + 下份草案交叉验证。
- 绝不无 field-diff E2E 盲拆·绝不 --no-verify。

> **请主控 review:确认本轮做 C 节哪几刀(默认全 4 刀)、接线/re-export 口径无误、E2E 票样够。验过我按 AUTONOMOUS_LOOP 自主逐刀执行。**
