# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-05 · **✅ 知识库「文档库+问答+悬浮猫+费用+全格式OCR入库+真实计费」整条上线**）

- **客户知识中心整条上线**(master `f73c42e` · 版本 `11850606` · prod 活 · `KNOWLEDGE_ENABLED=1` · 全量对所有用户可见含 mrerp · Zihao 拍板全开)。5 前端阶段 `src/home/knowledge-*.ts`(api/center/documents/ask/sources/fab/info + page-knowledge):
  - **文档库**(拖拽上传/状态轮询/删除/四态)、**问答**(带 `[n]` 出处卡 · 点开来源弹窗 `.modal` · 无来源回「资料不足」)、**悬浮猫 FAB**(长按拖拽吸边+卖萌·问答 tab 开关控显隐·素材 `static/brand/kb-cat.png`)、**功能介绍+费用弹窗**。侧栏「客户知识」探针门控(`GET /bases` 200 才显)。i18n 全 4 语。
- **全格式入库**(`services/knowledge/ocr_ingest.py`):文本走纯核心(ingest.py 不动·按字符);**图片/扫描件 PDF 走 OCR Layer1 Vision** 整页 full_text → 切片建索引(按页)。上传走 `asyncio.to_thread`。
- **真实计费接通**(钱路径·Zihao 拍板):`charge.deduct_thb` 通用扣 `tenant_credits.balance_thb`·`host_provider.charge_credits` 取代 log-only(amount=satang)。**上传**图片/扫描件按页(`estimate_pdf` ฿1.50/页起)·文本按字符(`estimate_excel`);**问答**答出扣 ฿0.50(`_RAG_ANSWER_SATANG=50`·no_answer 不扣·余额前置检查 402)。跟 OCR 同池。
- **验证**:前端本地反代真账号 5 阶段全 PASS;**计费 prod 真账号自验通过**(文本฿0.02/图片OCR ready ฿1.50/问答฿0.50/503 不扣)。单测 `test_knowledge_billing` 8 例 + 守门 9 道绿。
- **prod 实测 3 修复**(Zihao 验·已上线 `11850606`):① **猫图裂** = Cloudflare 缓存了部署前的 404(本地反代验证时请求过裸 URL)→ `KB_CAT` 加 `?v=2` 破缓存(文件本身在服务器好好的)② 聊天气泡 🐱 emoji → 全统一真猫图(共享常量 `KB_CAT` in knowledge-api.ts)③ 侧栏「客户知识」入口挪到「客户管理」正下方(原在「异常」后)。**坑记**:pearnly.com 走 Cloudflare·新静态资源若部署前被请求过会缓存 404·**新增 static 资源引用带 `?v=`**。
- **未提交残留**:无(全 push)。**未闭环**:① 问答出处暂只显文档名+相关度,**原文片段高亮**需加后端「按 chunk_id 取文」接口(留后续)② 问答偶发 **Gemini 503**(瞬时·前端优雅降级显「出错重试」不扣费)。
- **/simplify 发现(故意留下个窗口·跟 Codex 修复一起做=一次部署·别为纯DRY单独重部署稳定线)**:① 5 个 knowledge-*.ts 各自定义 i18n helper(`aT/dT/sT/iT/fT`)→ 抽 `knowledge-api.ts` 导出 `kbT` ② 4× `esc`(escapeHtml 包装)→ 抽 `kbEsc`(且 fab 里 citation JSON 没转义=小隐患)③ `deduct_thb` 与 `charge_ocr` 逐字复制 11 行余额 SQL → 抽私有 `_execute_balance_transaction` ④ satang 转换两处硬编码 → `charge.py` 加 `thb_to_satang`/`SATANG_PER_THB` ⑤ `knowledge-sources`/`knowledge-info` 两套 modal mask → 抽工厂。
- **下一步(下个窗口)**:**等 Codex 真 prod UI 实测报告**(文案已给 Zihao)→ 看报告再决定做什么 · 顺手把上面 /simplify 5 条收口 + 原文高亮后端接口一起做。全貌见 [[kb-rag-sandbox-project]] / [[knowledge-frontend-ocr-billing-shipped]]。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
