# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **bank_recon_v2 6745→2915 · facade 切 6 刀全 verbatim 上线 · prod 健康**)

- **本窗口 task**:拆全项目最大文件 `bank_recon_v2.py`(6745·**纯函数堆+dataclasses·非巨类→facade 切**,非 mixin)。已落 6 刀全 verbatim(AST identical·0 逻辑改·全量 2174 unittest 绿·push 上线·commit `ac742c9..ebab188`):
  - **C1** dataclasses → `services/recon/bank_recon_types.py`(leaf 破循环)
  - **C2** Excel 导出(~1380·纯呈现)→ `bank_recon_excel.py`
  - **C3** 共享常量+OCR缓存+基础utils → `bank_recon_utils.py`(`DATE_TOL_DAYS` 蓄意留 facade·见下)
  - **C4** 账单余额校验/自修复(PDF+xlsx 共用)→ `bank_stmt_balance.py`(307)
  - **C5** 账单解析叶子拆 3 模块:`bank_stmt_text`(330)/`bank_stmt_extract`(454)/`bank_stmt_gemini`(248)。**orchestrator `parse_bank_statement_pdf` 蓄意留 facade**(还调 pipeline 适配 + GL 助手 `_pdf_extract_text_safe`/`_is_summary_row`·移走会循环)。
  - **C6** legacy ParsedStatement 子系统(BankTransaction/各行模板/pipeline 适配,840行)→ 拆 3 模块:`bank_stmt_legacy_fields`(170 字段/金额/泰历助手·leaf)/`bank_stmt_legacy_parsers`(467 KBank/SCB/BBL/generic 行解析+dataclasses)/`bank_stmt_legacy`(264 orchestrator+adapters)。DAG: fields←parsers←orchestrator·无环。facade re-export `parse_statement_pdf`+`parsed_from_pipeline_legacy`(`bank_recon_routes.br.*` 契约·`assertIs` 验)。
- **拆法范式(给后续 recon 刀)**:Python 字节切片(探测 LF/CRLF·边界 assert·块交错用 AST 取节点 lineno gap 归属后随)→ AST/literal 比对证 0 逻辑改 → ruff F401 --fix 裁剪 + **F821 兜底抓漏 import** → 删「未用」import 前查 re-export 契约(纯 re-export 加 `# noqa: F401`)→ black 保 CRLF(按首行)→ import app + 全量 unittest + 契约 assertIs。子模块全 <500。
- **🔴 高敏 `DATE_TOL_DAYS` 全局名冲突(对账容差地雷·记忆 [[date-tol-days-shadowing]])**:行 32 `=3`(注释写 L2 ±3 天)是**死代码**,被 scoring 段 `=7` 加载时覆盖 → reconcile L2 **运行时实际 7 天**。重构保 verbatim=7,**不顺手改**。拆 reconcile/scoring 必把它绑同一刀(否则悄改容差=判定级事故)。改不改 = 另开非重构任务·Zihao 拍板。
- **剩余(facade 2915→目标 <500·下窗口)**:① **GL 解析块 ~1700**(含账单 xlsx/csv·误挂 GL 标题下)+ pipeline 适配 + 共享助手 `_pdf_extract_text_safe`(stmt入口119+GL1586 真共享·先提共享层)/`_is_summary_row`/`_norm_thai` → 抽共享层后 orchestrator+GL 才能干净移出 ② JSON 序列化 ~98 ③ merge ④ **🔴高敏 reconcile + scoring/run_matching(对账判定核心·铁律#26)**:连 `DATE_TOL_DAYS` 一刀·**做前单独发 Zihao 方案 + 真账号 field-diff E2E**。
- **命名决策(Zihao 拍 · 选 A)**:`bank_recon_v2` 的 "v2" 有真实含义(配 `bank_recon_v2_store`),改名**并进最后目录重组波**(铁律#30·import 只改一遍)·现在只记录。新拆子模块已全正规名。
- **最后 commit**:`ebab188`(C6)。本窗口 recon 6 刀全 push 上线。**下个 task = 继续拆剩余(GL 共享层→GL→序列化→merge)→ 高敏 reconcile/scoring 单独报 → 再 `recon_routes` 2000 / `gl_vat_reconciler` 1423 → ERP 周边 → 报表**。剩 ~17 个 .py >500。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
