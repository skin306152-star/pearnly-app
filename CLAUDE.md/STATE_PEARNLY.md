# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **bank_recon_v2 6745→1281 · facade 切 12 刀全 verbatim 上线 · prod 健康**)

- **本窗口 task**:拆全项目最大文件 `bank_recon_v2.py`(6745·**纯函数堆+dataclasses·非巨类→facade 切**,非 mixin)。已落 12 刀全 verbatim(AST identical·0 逻辑改·全量 2174 unittest 绿·push 上线·commit `ac742c9..ab14d83`)。子模块全在 `services/recon/`、全 <500:
  - **C1** types(leaf 破循环)/ **C2** Excel 导出 `bank_recon_excel`/ **C3** 常量+缓存+utils `bank_recon_utils`(`DATE_TOL_DAYS` 蓄意留 facade)/ **C4** 余额校验自修复 `bank_stmt_balance`/ **C5** 账单解析叶子 3 模块 `bank_stmt_{text,extract,gemini}`(orchestrator `parse_bank_statement_pdf` 留 facade)
  - **C6** legacy ParsedStatement 子系统 → `bank_stmt_legacy{,_parsers,_fields}`(re-export `parse_statement_pdf`/`parsed_from_pipeline_legacy`)
  - **C7** 共享 table/PDF I/O leaf `bank_table_io`(`_hit`/`_load_*`/`_is_summary_row`/`_pdf_extract_text_safe`·**stmt-xlsx/GL/orchestrator 三方共享·解锁后续的 keystone**)
  - **C8** xlsx/csv 流水直读 `bank_stmt_xlsx`(474)
  - **C9** GL 列识别共享 leaf `bank_gl_common`(56·`_GL_*`/`_ACCT_RE`/`_map_gl_cols`/`_extract_acct_code`·GL excel+pdf 双方共享)→ **C10** GL excel `bank_gl_excel`(346·re-export `parse_gl_excel`)→ **C11** GL pdf mrerp 表 `bank_gl_pdf_mrerp`(266)→ **C12** GL pdf 编排 `bank_gl_pdf`(469·`parse_gl_pdf`+text-lines+gemini+方向校验)。`parse_gl` 调度留 facade。
- **拆法范式**:AST 取顶层节点 (lineno,end_lineno)·gap 注释归属后随(块交错/非连续也能精确切)→ AST dump 比对证 0 逻辑改 → ruff F401 --fix + **F821 兜底抓漏 import**(C8 抓 balance 3 助手·C10 抓 io·C11 抓 Optional/date=真 latent bug·C12 抓 io/re/json/_is_gl_skip_row)→ 删「未用」前查 re-export 契约(纯 re-export 加 `# noqa: F401`)→ black 保 CRLF → import + 全量 unittest + 契约 assertIs。**⚠️教训:commit 前必查 ruff exit(C11 曾带错误误提交·已 amend)**。
- **🔴 高敏 `DATE_TOL_DAYS` 名冲突([[date-tol-days-shadowing]])**:行 30 `=3` 是死代码·被 scoring 段 `=7` 覆盖→运行时实际 7 天。保 verbatim=7·拆 reconcile/scoring 必绑同一刀。改不改=另开任务·Zihao 拍。
- **剩余(facade 1281→目标 <500·下窗口)**:① pipeline 适配 `_parse_bank_stmt_via_pipeline`/`_parse_gl_via_pipeline`(~190)② merge_statements/merge_gl_files(~120)③ JSON 序列化 `rows_to_json` 等(~110)④ **🔴高敏 reconcile + scoring/run_matching(对账判定核心·铁律#26)**:连 `DATE_TOL_DAYS` 一刀·**做前单独发 Zihao 方案 + 真账号 field-diff E2E**。注:orchestrator `parse_bank_statement_pdf` + `parse_gl` 调度蓄意留 facade。
- **命名**:`bank_recon_v2` "v2" 改名并进最后目录重组波(铁律#30)·现在只记录。
- **最后 commit**:`ab14d83`(C12)。本窗口 recon 12 刀全 push 上线。**下个 task = 拆 pipeline 适配/merge/序列化(非高敏·清掉再到高敏)→ 高敏 reconcile/scoring 单独报 → 再 `recon_routes` 2000 / `gl_vat_reconciler` 1423 → ERP 周边 → 报表**。剩 ~16 个 .py >500。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
