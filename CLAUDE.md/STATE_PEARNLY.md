# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **bank_recon_v2 6745→2341 · facade 切 8 刀全 verbatim 上线 · prod 健康**)

- **本窗口 task**:拆全项目最大文件 `bank_recon_v2.py`(6745·**纯函数堆+dataclasses·非巨类→facade 切**,非 mixin)。已落 8 刀全 verbatim(AST identical·0 逻辑改·全量 2174 unittest 绿·push 上线·commit `ac742c9..1a20d29`):
  - **C1** dataclasses → `services/recon/bank_recon_types.py`(leaf 破循环)
  - **C2** Excel 导出(~1380·纯呈现)→ `bank_recon_excel.py`
  - **C3** 共享常量+OCR缓存+基础utils → `bank_recon_utils.py`(`DATE_TOL_DAYS` 蓄意留 facade·见下)
  - **C4** 账单余额校验/自修复(PDF+xlsx 共用)→ `bank_stmt_balance.py`(307)
  - **C5** 账单解析叶子拆 3 模块:`bank_stmt_text`(330)/`bank_stmt_extract`(454)/`bank_stmt_gemini`(248)。**orchestrator `parse_bank_statement_pdf` 蓄意留 facade**(还调 pipeline 适配 + GL 助手 `_pdf_extract_text_safe`/`_is_summary_row`·移走会循环)。
  - **C6** legacy ParsedStatement 子系统(BankTransaction/各行模板/pipeline 适配,840行)→ 拆 3 模块:`bank_stmt_legacy_fields`(170·leaf)/`bank_stmt_legacy_parsers`(467 行解析+dataclasses)/`bank_stmt_legacy`(264 orchestrator)。re-export `parse_statement_pdf`+`parsed_from_pipeline_legacy`(`bank_recon_routes.br.*`)。
  - **C7** 共享 table/PDF I/O leaf 层 → `bank_table_io.py`(152·`_SUMMARY_ROW_KW`/`_is_summary_row`/`_hit`/`_load_excel_all_sheets`/`_load_csv_sheets`/`_pdf_extract_text_safe`)。**stmt-xlsx/GL/orchestrator 三方共享·这步是解锁 GL 与 stmt-xlsx 干净切分的 keystone**。
  - **C8** xlsx/csv 流水直读块 → `bank_stmt_xlsx.py`(474·`_STMT_*` 词典/`_map_bank_stmt_cols`/`_find_stmt_header`/`_parse_stmt_sheet`/`parse_bank_stmt_xlsx_direct`)。共享 I/O 取自 `bank_table_io`·余额助手取自 `bank_stmt_balance`(F821 兜底抓到补 import)。re-export `parse_bank_stmt_xlsx_direct`(recon_jobs/probes/facade pipeline)+`_map_bank_stmt_cols`/`_STMT_DEPOSIT_H`(测试)。
- **拆法范式(给后续 recon 刀)**:AST 取顶层节点 (lineno,end_lineno)·gap 注释归属后随节点(块交错/非连续也能精确切)→ AST dump 比对证 0 逻辑改 → ruff F401 --fix + **F821 兜底抓漏 import**(C8 抓到 bank_stmt_balance 3 助手)→ 删「未用」前查 re-export 契约(纯 re-export 加 `# noqa: F401`)→ black 保 CRLF → import + 全量 unittest + 契约 assertIs。子模块全 <500。
- **🔴 高敏 `DATE_TOL_DAYS` 全局名冲突(对账容差地雷·记忆 [[date-tol-days-shadowing]])**:行 30 `=3`(注释写 ±3 天)是**死代码**,被 scoring 段 `=7` 加载时覆盖 → reconcile L2 **运行时实际 7 天**。重构保 verbatim=7,**不顺手改**。拆 reconcile/scoring 必把它绑同一刀。改不改 = 另开非重构任务·Zihao 拍板。
- **剩余(facade 2341→目标 <500·下窗口)**:① **GL 解析块 ~1100**(804-1900:`parse_gl_excel`/`_parse_gl_mrerp_table`/`parse_gl_pdf`/`_parse_gl_text_lines`/`_gemini_parse_gl`/`parse_gl`·**C7 已解锁**·需再拆 2-3 模块:gl_excel / gl_pdf_mrerp / gl_pdf_text+gemini·`_norm_thai`/`_is_numeric_tok` GL 专属随 PDF 走)② pipeline 适配(`_parse_bank_stmt_via_pipeline`/`_parse_gl_via_pipeline`)③ merge ④ JSON 序列化 ~98 ⑤ **🔴高敏 reconcile + scoring/run_matching(对账判定核心·铁律#26)**:连 `DATE_TOL_DAYS` 一刀·**做前单独发 Zihao 方案 + 真账号 field-diff E2E**。
- **命名决策(Zihao 拍 · 选 A)**:`bank_recon_v2` 的 "v2" 改名**并进最后目录重组波**(铁律#30)·现在只记录。新拆子模块已全正规名。
- **最后 commit**:`1a20d29`(C8)。本窗口 recon 8 刀全 push 上线。**下个 task = 拆 GL 解析块(C7 已解锁·分 gl_excel/gl_pdf)→ pipeline 适配/merge/序列化 → 高敏 reconcile/scoring 单独报 → 再 `recon_routes` 2000 / `gl_vat_reconciler` 1423 → ERP 周边 → 报表**。剩 ~16 个 .py >500。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
