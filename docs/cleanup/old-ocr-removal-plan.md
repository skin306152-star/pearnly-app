# 旧 OCR 引擎删除计划

> 调研日期:2026-05-18
> 前提:阶段 (a) 接入完成 + 阶段 (b) text_path 接入完成 + 24h dashboard vs Google 偏差 < 10% 观察期通过
> 性质:**纯调研文档,不动手**。等用户确认后才开始按 phase 执行
> 范围:本 OCR 迁移会话遗留的待清理文件 — 屎山清理会话各管各的

---

## 一、Executive Summary

需要清理 6 个旧 OCR 模块,分 **3 个阶段**做。每阶段独立 commit,可分别回滚:

| 阶段 | 内容 | 风险 | 推荐时机 |
|---|---|---|---|
| **Phase 1** | 删 3 个孤儿文件(engine_chain / typhoon / nvidia)| **0**(已确认 0 调用) | 24h 观察 OK 即可 |
| **Phase 2** | 删除 4 个入口的 OLD fallback 分支 + feature flag 检查 | 低 | Phase 1 后 1-2 天 |
| **Phase 3** | 删除 gemini_engine.py / vision_engine.py / 精简 ocr_engine.py | 中 | Phase 2 后 1-3 天 |

**全部完成后**:OCR 代码 minus ~2000 行,新 pipeline 是唯一路径,埋点 100% 准确。

---

## 二、每个旧文件的调用方分析

### 2.1 `engine_chain.py`(降级链编排,~300 行)

**所有引用**:
- 仅自己内部使用 `engine_chain` 字符串
- `app.py:2217` 出现 `"engine_chain": chain_info` — **这是响应 JSON 的字段名,不是 import**

**结论**:**0 真实调用方**。已是死代码自阶段 1 审计起。

**决策**:**Phase 1 立即删**。无依赖,无风险。

---

### 2.2 `typhoon_engine.py`(Typhoon OCR 适配器,~190 行)

**所有引用**:
- `engine_chain.py:69, 148`(import + 调 extract_text_from_pdf_bytes)
- `engine_chain.py:71`(调 is_available)

**结论**:**只被 engine_chain 引用,engine_chain 自身是死代码**。

**决策**:**Phase 1 立即删**(随 engine_chain 一起)。

---

### 2.3 `nvidia_engine.py`(NVIDIA NIM 统一接入,~270 行)

**所有引用**:
- `engine_chain.py:70, 183`(import + 调 chat)
- `engine_chain.py:71`(调 is_available)
- `engine_chain.py:215, 217, 224`(调 chat / MODEL_REASONING / parse_json_response)

**审计 nvidia_engine 提供的所有 public 函数**:
- `chat()` — 只 engine_chain 用
- `embed()` — **0 调用**(原意是重复发票向量检测,从未真接入)
- `embed_batch()` — **0 调用**
- `parse_json_response()` — 只 engine_chain 用
- `health_check()` — **0 调用**
- `MODEL_CLASSIFY / MODEL_REASONING / MODEL_CHAT / MODEL_EMBED / MODEL_VL` — 只 engine_chain 用

**结论**:**整模块 0 外部调用**。`embed` 系列从未接入业务流程 — 阶段 1 审计提到的"非 OCR 用途"实际上是规划而非实现。

**决策**:**Phase 1 立即删**(随 engine_chain 一起)。

---

### 2.4 `gemini_engine.py`(主 OCR 旧实现,~530 行)

**所有引用**:
- `app.py:1734` — `from gemini_engine import recognize_pdf`(主路由 OLD 分支)
- `app.py:1756` — `from gemini_engine import _pdf_to_pil_images, restructure_with_text_hint`(Vision 兜底 OLD 分支)
- `app.py:5611` — `from gemini_engine import recognize_pdf as gemini_recognize, is_gemini_available`(LINE bot OLD 分支)
- `email_ingest.py:317-318` — `import gemini_engine` + `gemini_engine.recognize_pdf`(email OLD 分支)
- `recon_routes.py:641` — `from gemini_engine import recognize_pdf`(recon batch OLD 分支)
- `engine_chain.py:39`(死代码)
- `bank_reconcile.py:5, 508` — **仅注释提及**,无实际 import(bank_reconcile 直接用 `genai.GenerativeModel`,本会话工作纪律明确不碰)
- `services/ocr/layer1_vision.py:15`、`services/ocr/legacy_adapter.py:8, 93` — **仅 docstring/注释**

**结论**:**5 个 OLD 路径分支真依赖**(主路由 + LINE + email + recon + engine_chain)。

**决策**:
- Phase 2 删除 5 个 OLD 路径分支后,Phase 3 可删整个文件
- **不能在 Phase 1 删**

---

### 2.5 `vision_engine.py`(Vision REST 旧实现,~130 行)

**所有引用**:
- `app.py:1157-1158` — **`/api/health` 公开端点调用 `vision_engine.health_check()`** ⚠️
- `app.py:1755, 1758` — Vision 兜底 OLD 分支(主路由 except 块内)

**结论**:除了 OLD 路径,还有 `/api/health` 公共健康检查依赖。

**Phase 3 删除时需要 1 处额外修复**:`/api/health` 端点的 vision_status 字段:
- 选项 A:删除 vision_status 字段(简洁)
- 选项 B:改成检查新 pipeline 凭证(`GOOGLE_APPLICATION_CREDENTIALS` 文件是否存在)
- 选项 C:保留 `vision_engine.py` 但简化为只剩 health_check 一个函数

**推荐**:选项 B — 检查 `GOOGLE_APPLICATION_CREDENTIALS` env + 文件存在性,符合新架构语义。

**决策**:Phase 3 删除,但需先改 `/api/health` 端点。

---

### 2.6 `ocr_engine.py`(EasyOCR + count_pdf_pages,~230 行)

**所有引用**:
- `app.py:1524-1525` — `from ocr_engine import count_pdf_pages` ⚠️**工具函数仍在用**
- `email_ingest.py:261-262` — 同上 ⚠️
- `engine_chain.py:94` — `from ocr_engine import recognize_pdf as easy_recognize`(死代码)
- `gemini_engine.py:7, 355` — **仅 docstring 提及**

**结论**:`recognize_pdf` 是死代码,`count_pdf_pages` 仍在两处使用。

**决策**:
- 不能整文件删
- **Phase 3 重构**:把 `count_pdf_pages` 搬到 `services/ocr/pdf_utils.py`(新文件),改 app.py / email_ingest 的 import,然后删整个 `ocr_engine.py`
- 或:保留 `ocr_engine.py` 但精简到只剩 `count_pdf_pages` + 删 EasyOCR 相关代码(~200 行减到 ~30 行)

**推荐**:**搬到 `services/ocr/pdf_utils.py`** — 跟新架构对齐,不留旧文件名残骸。

---

### 2.7 `pdf_text_extractor.py`(电子 PDF 文本路径,~430 行)

**所有引用**:
- `app.py:1693`(OLD 分支)
- `recon_routes.py:676`(OLD 分支)
- `vat_excel_export.py:73-74` — **vat_excel 模块在用**(`vat_excel_export.extract_invoice_fields` 内部)
- `services/ocr/text_path.py` — **完全独立的新实现,不 import 旧的**

**结论**:本 OCR 会话工作纪律明确**不碰 vat_excel_***,所以 pdf_text_extractor 必须**保留**(vat_excel_export 还在用)。

**决策**:**保留**。pdf_text_extractor 可在未来 vat_excel_* 也迁移到新 pipeline 时再清理(不在本会话范围)。

---

## 三、其他相关清理项(顺手发现)

### 3.1 OLD fallback 分支(在 Phase 2 删)

新 pipeline 接入时为了安全,4 个入口都保留了 `if result is None: # OLD PATH`。Phase 2 删除后:

| 文件 | 行号(估)| 行数 | 删什么 |
|---|---|---|---|
| `app.py` `/api/ocr/recognize` 主路由 | 1689-1789 | ~100 行 | OLD 分支 + 旧 cost 公式 |
| `app.py` LINE bot `_handle_line_image_ocr` | 5573-5582 | ~20 行 | OLD `if result is None` 块 |
| `email_ingest.py` | 316-322 | ~10 行 | OLD `if result is None` 块 |
| `recon_routes.py` `_ocr_one` | 698-748(text_path + Gemini)| ~70 行 | OLD text_path + Gemini fallback |

合计约 **200 行 OLD fallback** 删除。

### 3.2 Feature flag 检查(在 Phase 2 删或保留)

4 处都有 `if os.environ.get("OCR_USE_NEW_PIPELINE", "false").strip().lower() == "true"`。

**选项 A**:Phase 2 一并删除 flag 检查(代码彻底简化)
**选项 B**:Phase 2 保留 flag,但默认 true,留作未来紧急 kill switch(尽管 fallback 已删,flag 仅作 NotImplementedError 信号)

**推荐**:**选项 A**。Phase 3 删除旧文件后,flag 已无功能价值。

### 3.3 `OCR_FAST_PATH_ENABLED` flag(Phase 2 保留或不变)

text_path 是新功能,flag 仍有意义(临时关闭排查问题用)。**保留**。

---

## 四、分阶段删除计划

### Phase 1 — 删 3 孤儿文件(零风险)

**触发条件**:24h 观察 dashboard vs Google 偏差 < 10% 通过。

**单 commit**:
```
chore(ocr cleanup): remove orphan engine_chain + typhoon + nvidia modules

These modules were already dead code:
- engine_chain.py: 0 callers, defined but never invoked anywhere
- typhoon_engine.py: only engine_chain imports it
- nvidia_engine.py: only engine_chain imports it (chat); embed/embed_batch 0 callers
```

**删除文件**:
- `engine_chain.py`
- `typhoon_engine.py`
- `nvidia_engine.py`

**影响**:
- 代码 -800 行
- ~10 行 docstring/注释里的引用(`bank_reconcile.py:5, 508`、`gemini_engine.py:7, 355`)— 这些是注释,**保留 OK,不影响功能**(也可顺手清,$0 风险)

**风险**:**0**。这些文件从未在任何业务流程里运行过。

**回滚**:`git revert <commit>` 即可。

---

### Phase 2 — 删 OLD fallback 分支 + feature flag(Phase 1 之后 1-2 天)

**触发条件**:Phase 1 部署 + 1-2 天稳定 + dashboard 偏差仍 < 10%(说明 100% 流量真的走新 pipeline,OLD 分支确实没被回退过)。

**单 commit**:
```
chore(ocr cleanup): remove OLD OCR fallback paths from 4 entry points

After Phase 1 confirmed new pipeline is stable. Removes the
`if result is None: # OLD PATH` blocks from /api/ocr/recognize,
LINE bot, email_ingest, and recon_routes.

Also removes OCR_USE_NEW_PIPELINE feature flag (was always-true after
this commit anyway).

OCR_FAST_PATH_ENABLED flag retained — useful as text_path emergency
disable switch.
```

**修改文件**:
- `app.py` 主路由(line 1689-1789)— 删 OLD 分支 + 简化 cost log
- `app.py` LINE bot(line 5573-5582)— 删 OLD 分支
- `email_ingest.py`(line 316-322)— 删 OLD 分支
- `recon_routes.py`(line 698-748)— 删 OLD text_path + Gemini fallback

**影响**:
- 代码 -200 行
- 4 入口现在**完全依赖新 pipeline**

**风险**:**中**(只在新 pipeline 100% 稳定的前提下才安全)
- 如果新 pipeline 突然出 bug,**无 fallback**
- 监控:依赖 dashboard 实时报警
- 缓解:Phase 1 之后留 1-2 天观察期

**回滚**:`git revert <commit>` 恢复 OLD 分支即可。

---

### Phase 3 — 删 gemini_engine + vision_engine + 精简 ocr_engine(Phase 2 之后 1-3 天)

**触发条件**:Phase 2 部署 + 1-3 天稳定 + dashboard 偏差仍 < 10%。

**单 commit**:
```
chore(ocr cleanup): remove gemini_engine + vision_engine, migrate
  count_pdf_pages to services/ocr/pdf_utils

After Phase 2 removed all OLD path callers. These modules have 0
remaining business callers.

- gemini_engine.py: deleted (recognize_pdf / restructure_with_text_hint
  / _pdf_to_pil_images / is_gemini_available / _normalize_thai_date /
  _normalize_fields all unused — new pipeline has its own
  implementations in services/ocr/)
- vision_engine.py: deleted; /api/health endpoint vision_status check
  replaced with GOOGLE_APPLICATION_CREDENTIALS env check
- ocr_engine.py: deleted; count_pdf_pages migrated to
  services/ocr/pdf_utils.count_pdf_pages
- app.py:1524 + email_ingest.py:261 import paths updated
```

**修改文件**:
- 删 `gemini_engine.py`
- 删 `vision_engine.py`
- 删 `ocr_engine.py`
- 新建 `services/ocr/pdf_utils.py`(把 `count_pdf_pages` 搬过来,~10 行)
- 改 `app.py:1524` `from ocr_engine import count_pdf_pages` → `from services.ocr.pdf_utils import count_pdf_pages`
- 改 `email_ingest.py:261` 同上
- 改 `app.py:1157-1158` `/api/health` 端点:用 `GOOGLE_APPLICATION_CREDENTIALS` env + 文件存在性检查替代 vision_engine.health_check
- 顺手清 `bank_reconcile.py:5, 508` 旧 docstring/TODO 注释(可选)
- 顺手清 `gemini_engine.py / ocr_engine.py` 在 docstring/注释里的 cross-reference(已删文件,无意义)

**影响**:
- 代码 -1000 行
- 整个项目根目录少 3 个 *_engine.py 文件,结构清爽
- 新工具函数 `services/ocr/pdf_utils.count_pdf_pages` 跟新架构一致

**风险**:**中低**
- 主风险:有些没扫到的地方仍引用(尽管 grep 全覆盖了)
- 缓解:删除前先 `grep -r "from gemini_engine|from vision_engine|from ocr_engine" .` 二次确认
- `/api/health` 改动需要前端不依赖 vision_status 字段(可前端兼容,无 vision_status 时不渲染)

**回滚**:`git revert <commit>` 恢复全部 + import 路径

---

## 五、时序建议

| 时间 | 动作 | 依赖 |
|---|---|---|
| 2026-05-18 晚 | 阶段 (a) + (b) 部署完成,用户开始 24h 偏差观察 | — |
| **2026-05-19 上午** | **用户确认 dashboard vs Google 偏差 < 10% → 给 OCR 会话 green light** | 24h 数据 |
| 2026-05-19 中午 | Phase 1 commit + push(删 3 孤儿)| green light |
| 2026-05-19 整天 | 服务器观察:正常流量,无报错 | — |
| 2026-05-20 上午 | 用户复核 24h 偏差仍 OK → Phase 2 commit | Phase 1 + 24h |
| 2026-05-20 整天 | 服务器观察 | — |
| 2026-05-21 上午 | 用户复核偏差 → Phase 3 commit | Phase 2 + 24h |
| 2026-05-21 之后 | OCR 迁移整体完成 | — |

**最快路径**:如果用户对偏差数据非常有信心,Phase 1 + Phase 2 + Phase 3 可压缩到同一天,但**不推荐** — 3 个 commit 之间各留 24h 给生产观察是最稳的做法。

---

## 六、风险评估

### 6.1 总风险表

| 风险 | 等级 | 缓解 |
|---|---|---|
| Phase 1 后某地方仍 import 已删文件 | **极低** | grep 已确认 0 调用方;就算遗漏,服务起不来很快暴露 |
| Phase 2 后新 pipeline 出 bug 无 fallback | **中** | 24h 偏差 < 10% 已说明 100% 流量稳跑;`git revert` 1 分钟恢复 |
| Phase 3 后 `/api/health` 前端坏 | **低** | `/api/health` 是非关键接口(仅监控/管理后台用);前端通常 graceful degrade |
| Phase 3 后 count_pdf_pages 调用路径错 | **低** | 改 2 处 import,grep 复检即可 |
| `bank_reconcile.py:5, 508` 注释引用残留 | **极低** | 仅注释,无功能影响;可顺手清也可留着 |
| 屎山清理会话同期改了相关文件造成冲突 | **中** | 删除时先 `git pull` + check 冲突;用户协调两个会话的时序 |

### 6.2 不能 / 不该删的清单(防误清)

**保留(本会话范围)**:
- `services/ocr/*` — 全部保留(新架构)
- `pdf_text_extractor.py` — 保留(vat_excel_* 用)
- `ocr_engine.count_pdf_pages` — 保留(搬到 pdf_utils.py)

**不动(纪律保护)**:
- `bank_recon_v2.py` — 直调 genai,本会话不碰
- `vat_excel_*.py` — 同上
- `vat_file_classifier.py` / `vat_report_parser.py` / `vat_ai_analyzer.py` — 同上
- `db.py` — 只读
- `auth_signup.py` — 只读

**屎山清理会话领地**:
- `docs/cleanup/` 下其它文件不动(本计划是新增,不修改既有)

---

## 七、对屎山清理会话的协作说明

本计划与屎山清理会话的潜在协作点:

1. **engine_chain / typhoon / nvidia 删除时机** — OCR 会话已在 migration-plan.md 决策 5 中明确"处置权归本会话"。**屎山清理会话不应触碰这 3 个文件**,等本会话 Phase 1 删完即可。
2. **gemini_engine / vision_engine / ocr_engine 删除** — 同上,本会话 Phase 3 处理。
3. **bank_reconcile.py / vat_excel_*.py 等** — 屎山清理会话仍可继续清理这些文件的非 OCR 部分(去除空 except / 重复代码等)— 本计划不影响它们。
4. **`/api/health` 改动** — Phase 3 本会话改;若屎山清理会话同期也想改,需协调。

建议两边在删除文件**前**先 `git pull` + 看 git status 确认无未推送的对方修改。

---

## 八、统计:删完之后的收益

| 项 | 删除前 | 删除后(Phase 3 完成)| 节省 |
|---|---|---|---|
| OCR 相关代码文件(项目根)| 6 个 `*_engine.py` + 1 `pdf_text_extractor.py` | 1 个 `pdf_text_extractor.py` + 7 个 `services/ocr/*.py`(新)| -5 个根目录旧文件 |
| 旧 OCR 代码总行数 | ~1860 行(engine_chain 300 + typhoon 190 + nvidia 270 + gemini 530 + vision 130 + ocr_engine 230 + ~210 老 fallback)| 0(全部新架构里实现)| **-1860 行** |
| 死代码 / 重复实现 | 3 个 PDF→图像 函数 + 2 套正则字段抽取 + 3 套 JSON 解析容错 | 各 1 套(在 services/ocr/)| 减少 ~70% |
| 埋点漏记率 | 86%(只 14% 记录)| **预期 < 10%**(100% 埋点设计 + Vision per-page 入公式)| -76 pp |
| `/api/ocr/recognize` 主路由代码行 | ~110 行(三层兜底链)| ~10 行(`pipeline.run + adapter`)| -100 行 |

---

## 九、用户决策点(请明天上午确认)

收到偏差数据后,请回我:

- ✅ **偏差 < 10%** → 进 Phase 1
- ⚠️ **偏差 10-30%** → 暂停,先排查漏记(可能某入口我漏接了)
- 🚨 **偏差 > 30% 或新 pipeline 报错率 > 1%** → 立即把 `OCR_USE_NEW_PIPELINE=false` 切回旧路径

Phase 1 / Phase 2 / Phase 3 是否要等 24h 间隔 / 是否压缩 / 是否调整顺序 — 也请明天告诉我。

---

*本文档纯调研,无任何代码动作。等用户明天上午看完偏差数据后决定何时执行各 Phase。*
