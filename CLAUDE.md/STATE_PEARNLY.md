# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ bank_recon_v2 6745→422 · 全项目最大文件首次 <500 达标 · facade 切 18 刀全 verbatim 上线 · prod 健康**)

- **本窗口 task ✅ 收官**:拆全项目最大文件 `bank_recon_v2.py`(6745→**422**·**纯函数堆+dataclasses·非巨类→facade 切**)。18 刀全 verbatim(AST identical·0 逻辑改·全量 2177 unittest 绿·push 上线·commit `ac742c9..0dede0f`)。子模块全在 `services/recon/`、全 <500(唯 `bank_recon_excel` 1397 待再拆·纯呈现·非阻塞):
  - **C1** types(leaf 破循环)/ **C2** Excel 导出 `bank_recon_excel`/ **C3** 常量+缓存+utils `bank_recon_utils`(`DATE_TOL_DAYS` 蓄意留 facade)/ **C4** 余额校验自修复 `bank_stmt_balance`/ **C5** 账单解析叶子 3 模块 `bank_stmt_{text,extract,gemini}`(orchestrator `parse_bank_statement_pdf` 留 facade)
  - **C6** legacy ParsedStatement 子系统 → `bank_stmt_legacy{,_parsers,_fields}`(re-export `parse_statement_pdf`/`parsed_from_pipeline_legacy`)
  - **C7** 共享 table/PDF I/O leaf `bank_table_io`(`_hit`/`_load_*`/`_is_summary_row`/`_pdf_extract_text_safe`·**stmt-xlsx/GL/orchestrator 三方共享·解锁后续的 keystone**)
  - **C8** xlsx/csv 流水直读 `bank_stmt_xlsx`(474)
  - **C9-C12** GL 解析拆 4 模块:`bank_gl_common`(56·共享列识别 leaf)→ `bank_gl_excel`(346)→ `bank_gl_pdf_mrerp`(266)→ `bank_gl_pdf`(469)。`parse_gl` 调度留 facade。
  - **C13** JSON 序列化 `bank_recon_serialize`(103)/ **C14** merge `bank_recon_merge`(111)/ **C15** pipeline 适配 `bank_recon_pipeline`(206)。
  - **🔴高敏 S1-S3(Zihao 批方案后执行)**:S1 `DATE_TOL_DAYS` 收口 utils 单一来源=7(消地雷·删死的=3)→ S2 `reconcile`(账单-GL 对账核心)→ `bank_recon_reconcile`(275)→ S3 打分+会话匹配(score_*/match_one_tx/run_matching)→ `bank_recon_scoring`(257)。验证:AST identical + `test_reconcile_golden`(合成数据全字段锚)+ `test_run_matching_contract`(mock db 验候选查询用 DATE_TOL_DAYS=7 + match→save 接线)。**⚠️撞名教训:`bank_recon_match` 名已被 v1 tx↔发票 DAL 占用·裸 open('w') 静默覆盖致 db 动态 import 全崩(118 收集错)·已恢复改名 reconcile。新建模块前必 `git cat-file -e`/`ls` 验路径空闲·别用裸 open('w')**。
- **拆法范式**:AST 取顶层节点 (lineno,end_lineno)·gap 注释归属后随(块交错/非连续也能精确切)→ AST dump 比对证 0 逻辑改 → ruff F401 --fix + **F821 兜底抓漏 import**(屡建功:C11 Optional/date=真 latent bug·C15 _BANK_SIGNATURES)→ 删「未用」前查 re-export 契约·**⚠️行范围切取会卷走夹在区间内的 ImportFrom 行(C13 误把 `export_bank_recon_excel` re-export 卷进 serialize → facade 丢 re-export·全量测试才抓到·已修)** → black 保 CRLF + **noqa 放 `from(` 开括号行**(放 `)` 行不抑制 F401)→ import + 全量 unittest + 契约 assertIs。**⚠️教训:commit 前必查 ruff/black exit(C11 曾误提交·已 amend);per-cut 只跑 ruff+contract·全量 unittest 至少收尾跑一次(C13 漏的 re-export 靠它兜住)**。
- **🔴 `DATE_TOL_DAYS` 地雷已拆除([[date-tol-days-shadowing]])**:原 facade 定义两次(=3 死代码被 scoring 段 =7 加载时覆盖→运行时 7)·S1 已收口到 `bank_recon_utils.DATE_TOL_DAYS=7` 单一来源·reconcile/scoring 两模块都 import 它·运行时恒 7 不变·不再可能分叉。
- **facade `bank_recon_v2.py` 422 行现存** = imports(全 re-export 子模块)+ orchestrator `parse_bank_statement_pdf`(~220·蓄意留·走 pipeline+pdfplumber+gemini)+ `parse_gl` 调度(~52·留)。已 <500·**本文件收官**。
- **命名**:`bank_recon_v2` "v2" 改名并进最后目录重组波(铁律#30)·现在只记录。
- **最后 commit**:`0dede0f`(高敏 S3)。本窗口 recon 18 刀全 push 上线·全项目最大文件从 6745 拆到 422。**下个 task = `recon_routes` 2000 / `gl_vat_reconciler` 1423 / `vat_excel_export` 1960 / `bank_recon_excel` 1397(纯呈现)→ ERP 周边 → 报表**。剩 ~16 个 .py >500。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
