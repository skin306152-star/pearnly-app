# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-05 · **✅ 知识库「文档库+问答+悬浮猫+费用+全格式OCR入库+真实计费」整条上线**）

- **客户知识中心整条上线**(master `2732f20` · 版本 `11850605` · prod 活 · `KNOWLEDGE_ENABLED=1` · 全量对所有用户可见含 mrerp · Zihao 拍板全开)。5 前端阶段 `src/home/knowledge-*.ts`(api/center/documents/ask/sources/fab/info + page-knowledge):
  - **文档库**(拖拽上传/状态轮询/删除/四态)、**问答**(带 `[n]` 出处卡 · 点开来源弹窗 `.modal` · 无来源回「资料不足」)、**悬浮猫 FAB**(长按拖拽吸边+卖萌·问答 tab 开关控显隐·素材 `static/brand/kb-cat.png`)、**功能介绍+费用弹窗**。侧栏「客户知识」探针门控(`GET /bases` 200 才显)。i18n 全 4 语。
- **全格式入库**(`services/knowledge/ocr_ingest.py`):文本走纯核心(ingest.py 不动·按字符);**图片/扫描件 PDF 走 OCR Layer1 Vision** 整页 full_text → 切片建索引(按页)。上传走 `asyncio.to_thread`。
- **真实计费接通**(钱路径·Zihao 拍板):`charge.deduct_thb` 通用扣 `tenant_credits.balance_thb`·`host_provider.charge_credits` 取代 log-only(amount=satang)。**上传**图片/扫描件按页(`estimate_pdf` ฿1.50/页起)·文本按字符(`estimate_excel`);**问答**答出扣 ฿0.50(`_RAG_ANSWER_SATANG=50`·no_answer 不扣·余额前置检查 402)。跟 OCR 同池。
- **验证**:前端本地反代真账号 5 阶段全 PASS;**计费 prod 真账号自验通过**(文本฿0.02/图片OCR ready ฿1.50/问答฿0.50/503 不扣)。单测 `test_knowledge_billing` 8 例 + 守门 9 道绿。
- **未提交残留**:无(全 push)。**未闭环**:① 问答出处暂只显文档名+相关度,**原文片段高亮**需加后端「按 chunk_id 取文」接口(留后续)② 问答偶发 **Gemini 503**(瞬时·前端优雅降级显「出错重试」不扣费)。
- **下一步**:等 **Codex 真 prod UI 实测** 出报告(文案已给 Zihao)→ 看报告修问题。原文高亮接口可另起。全貌见 [[kb-rag-sandbox-project]]。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
