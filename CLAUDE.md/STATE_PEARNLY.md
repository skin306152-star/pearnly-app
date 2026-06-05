# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-05 · **✅ 知识库报告4修复(P1a已补全)+ 出处原文片段高亮上线 `11850608` · 等 Codex 第2轮复验**）

- **最新一批**(master `9fc3362` · 版本 `11850608` · prod 活)：① 出处**原文片段高亮**(对齐桌面设计预览)② 补全报告 **P1a**。守门全绿 · 全量单测 **2293 OK**。
- **原文片段高亮**:点问答出处卡 → 后端 `GET /api/knowledge/chunks/{id}`(`search.get_chunk_context`·RLS+账套隔离·取命中 chunk + 邻段)→ 前端 `knowledge-sources.ts` 弹窗(`.modal` 非抽屉·守 D1 闸)黄底高亮命中段 + 上下文 +「可核对」脚注。i18n 4 语。**数据现实**:chunk 不存页码/章节(切片时页边界丢)→ 不显「第X页」(设计预览的页码是 mock·要做需改入库管线另议)。
- **P1a 补全**(Codex 实测发现上批只修一半):坏 PDF 在 prod 走"OCR 抽不到文字"分支仍返回 `ERROR_UNSUPPORTED`。改:支持类型但 OCR 抽空 → `ERROR_PROCESSING`(显"文件无法解析,可能已损坏或加密")。
- **Codex 实测**:上批 11850607 报告 `桌面\知识库修复验证报告_2026-06-05.md` — 5 PASS · 唯一 FAIL=P1a 错误码(本批已修)。**第2轮清单已交**:`桌面\knowledge_fix_verify_2026-06-05\验证清单_第2轮_2026-06-05.md`(A 组复验 P1a 文案 / B 组实测原文高亮·坏PDF+种子文档都现成)。
- **⚠️ 交接补漏**:知识库 UI 设计预览在 **`桌面\Pearnly知识库UI预览\index.html`**(全套设计稿)。**改知识库 UI 先翻这个**。见 [[kb-ui-design-preview-desktop]]。
- **未提交残留**:无(全 push)。**未闭环 / deferred**:① 页码/章节标(需入库管线存 page→chunk)② 问答偶发 Gemini 503(瞬时·已降级不扣)③ **/simplify 待办**(本窗口审出·故意没改怕打断 Codex 复验):`ocr_ingest.py` P1a 分支 `if suffix != ".pdf"` 判两次+`ProcessOutcome(DOC_FAILED,ERROR_PROCESSING)` 建两次,可让 except 只赋值、由后面统一 early-return(等价更干净)。
- **下一步(下个窗口)**:**先看 Codex 第2轮报告**(A 坏PDF 新文案 / B 原文黄底高亮)→ 都过=知识库整条闭环;顺手收掉上面 /simplify 待办。全貌见 [[kb-rag-sandbox-project]] / [[knowledge-frontend-ocr-billing-shipped]] / [[kb-ui-design-preview-desktop]]。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
