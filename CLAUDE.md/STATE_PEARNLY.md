# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ gl_vat_reconciler 1423→72 收官 · facade 纯 re-export 壳 · recon 引擎全部 <500 · prod 上线**)

- **本窗口 task ✅ 收官**:续拆 `gl_vat_reconciler.py`(929→**72**·纯 re-export 壳)。本窗口 5 刀全 verbatim(AST identical·0 逻辑改·全量 2177 unittest 绿·push `da33542..9eb97e2` 上线)。加前窗口 types+excel 2 刀,gl_vat 共 7 刀 1423→72。子模块全在 `services/recon/`、全 <500:
  - **C3** `gl_vat_parse_common`(137·共享叶子 helper+列名常量)/ **C4** `gl_vat_parse_pdf`(335·`_parse_gl_text_lines`+`parse_gl_pdf`+正则·F821 兜底抓出漏迁 `GlRow`)/ **C5** `gl_vat_parse_excel`(275·`parse_gl_excel`+`parse_gl` dispatch+pipeline·`PARSER_VERSION` 随唯一消费者迁入)
  - **🔴C6 高敏** `gl_vat_reconcile`(177·`reconcile_gl_vat` VAT 判定核心·铁律#26·单独验 160 recon 单测)/ **C7** `gl_vat_serialize`(35·detail/summary to/from json)
  - 前窗口已落:`gl_vat_types`(60·dataclasses)+`gl_vat_excel`(467·i18n+导出)+`gl_vat_store`(195·DAL)
- **拆法范式**(同 bank_recon):AST 顶层节点 (lineno,end_lineno) verbatim 切→AST dump 比对证 0 逻辑改→ruff F401+**F821 兜底抓漏 import**(本轮抓出 `GlRow`)→删「未用」前查 re-export 契约→black 保 CRLF。**⚠️本轮教训:`black --check` 经管道 `tail` 吞 exit code 误判通过·pre-push 机械闸兜住(连续 import 块多空行)·验 gate 必看 exit code 别只看 stdout**。
- **facade `gl_vat_reconciler.py` 72 行** = 纯 re-export 全子模块(契约:`parse_gl`/`reconcile_gl_vat`/`detail_*`/`summary_*`/`GlRow`/`ReconRow`/`GlVatSummary`/`export_gl_vat_excel`/`_to_float` 等 helper·routes+tests 取用)。**本文件收官**。
- **命名**:`gl_vat_reconciler` 改名并进最后目录重组波(铁律#30)·现在只记录。
- **最后 commit**:`9eb97e2`(black 收口)。**下个 task = `recon_routes` 2000(路由组拆·含计费高敏)/ `vat_excel_export` 1960 → ERP 周边 → 报表**。剩 ~14 个 .py >500。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
