# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **bank_recon_v2 6745→922 · facade 切 15 刀全 verbatim 上线 · 非高敏块清完 · prod 健康**)

- **本窗口 task**:拆全项目最大文件 `bank_recon_v2.py`(6745·**纯函数堆+dataclasses·非巨类→facade 切**,非 mixin)。已落 15 刀全 verbatim(AST identical·0 逻辑改·全量 2174 unittest 绿·push 上线·commit `ac742c9..aca5bda`)。子模块全在 `services/recon/`、全 <500(唯 `bank_recon_excel` 1397 待再拆·纯呈现·非阻塞):
  - **C1** types(leaf 破循环)/ **C2** Excel 导出 `bank_recon_excel`/ **C3** 常量+缓存+utils `bank_recon_utils`(`DATE_TOL_DAYS` 蓄意留 facade)/ **C4** 余额校验自修复 `bank_stmt_balance`/ **C5** 账单解析叶子 3 模块 `bank_stmt_{text,extract,gemini}`(orchestrator `parse_bank_statement_pdf` 留 facade)
  - **C6** legacy ParsedStatement 子系统 → `bank_stmt_legacy{,_parsers,_fields}`(re-export `parse_statement_pdf`/`parsed_from_pipeline_legacy`)
  - **C7** 共享 table/PDF I/O leaf `bank_table_io`(`_hit`/`_load_*`/`_is_summary_row`/`_pdf_extract_text_safe`·**stmt-xlsx/GL/orchestrator 三方共享·解锁后续的 keystone**)
  - **C8** xlsx/csv 流水直读 `bank_stmt_xlsx`(474)
  - **C9-C12** GL 解析拆 4 模块:`bank_gl_common`(56·共享列识别 leaf)→ `bank_gl_excel`(346)→ `bank_gl_pdf_mrerp`(266)→ `bank_gl_pdf`(469)。`parse_gl` 调度留 facade。
  - **C13** JSON 序列化 `bank_recon_serialize`(103·`rows_to_json` 等)/ **C14** 多文件 merge `bank_recon_merge`(111)/ **C15** pipeline 适配 `bank_recon_pipeline`(206·`_parse_*_via_pipeline`)。
- **拆法范式**:AST 取顶层节点 (lineno,end_lineno)·gap 注释归属后随(块交错/非连续也能精确切)→ AST dump 比对证 0 逻辑改 → ruff F401 --fix + **F821 兜底抓漏 import**(屡建功:C11 Optional/date=真 latent bug·C15 _BANK_SIGNATURES)→ 删「未用」前查 re-export 契约·**⚠️行范围切取会卷走夹在区间内的 ImportFrom 行(C13 误把 `export_bank_recon_excel` re-export 卷进 serialize → facade 丢 re-export·全量测试才抓到·已修)** → black 保 CRLF + **noqa 放 `from(` 开括号行**(放 `)` 行不抑制 F401)→ import + 全量 unittest + 契约 assertIs。**⚠️教训:commit 前必查 ruff/black exit(C11 曾误提交·已 amend);per-cut 只跑 ruff+contract·全量 unittest 至少收尾跑一次(C13 漏的 re-export 靠它兜住)**。
- **🔴 高敏 `DATE_TOL_DAYS` 名冲突([[date-tol-days-shadowing]])**:行 23 `=3` 是死代码·被 scoring 段 `=7` 覆盖→运行时实际 7 天。保 verbatim=7·拆 reconcile/scoring 必绑同一刀。改不改=另开任务·Zihao 拍。
- **剩余(facade 922→目标 <500)**:**非高敏块已全部清完**。facade 现存 = imports + orchestrator `parse_bank_statement_pdf`(~220·蓄意留)+ `parse_gl` 调度(~52·留)+ **🔴高敏 `reconcile`(~265)+ scoring/`run_matching`(~250)(对账判定核心·铁律#26)**。**降到 <500 必须抽高敏块·连 `DATE_TOL_DAYS` 一刀 → 做前单独发 Zihao 方案 + 真账号 field-diff E2E·不擅动**。另:`bank_recon_excel`(1397·纯呈现)可再拆 sheet builders·非阻塞。
- **命名**:`bank_recon_v2` "v2" 改名并进最后目录重组波(铁律#30)·现在只记录。
- **最后 commit**:`aca5bda`(C15)。本窗口 recon 15 刀全 push 上线。**下个 task = 🔴高敏 reconcile/scoring 单独报 Zihao(facade <500 卡这步)→ 或转 `recon_routes` 2000 / `gl_vat_reconciler` 1423 → ERP 周边 → 报表**。剩 ~16 个 .py >500。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
