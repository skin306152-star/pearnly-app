# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ vat_report_parser 969→179 · facade 切 4 子模块 · prod 上线**)

- **本窗口 task ✅ 收官**:`vat_report_parser.py` 按解析路径拆 —— `vat_parser_common`(工具/列名·垃圾行常量 89)· `vat_parser_excel`(openpyxl 140)· `vat_parser_pdf`(pdfplumber 文本/表格+regex 234)· `vat_parser_gemini`(扫描件 OCR·拆页/切块并行 397)。vat_report_parser 969→**179**(聚合 facade:parse_vat_report 入口 + _parse_vat_via_pipeline + re-export)。push `26c7368` 上线(pre-push 2176 测试全绿放行)。
- **范式(函数堆 facade · [[facade-split-monkeypatch-constant-trap]] / [[app-py-route-split-reexport-contracts]])**:① 脚本按行 verbatim 字节切(newline='' 保 CRLF · 防手敲丢 `_to_float` 特殊空格)· 原 **40 符号(函数+常量)逐个 ast.dump 全等**;② 依赖无环 common←excel←pdf / gemini←common;③ 全 <500。
- **⚠️ re-export 契约**:外部 6 处只 import `parse_vat_report`(facade 仍导出);**契约测试零 monkeypatch** · `vp._hit/_to_float/_filter_garbage_rows/_map_columns/_build_row/parse_excel` 直接调 → facade 显式 re-export `_hit/_map_columns/_build_row`(noqa F401)· 14 passed。
- **✅ 本会话连收 9 个**:bank_recon_excel · mrerp_xlsx_generator · mrerp_customer_sync · report_engine · email_ingest · mrerp_dms_client · erp_routes · **vat_report_parser**(+ 接力前 recon_routes/vat_excel)。
- **最后 commit**:`26c7368`。**剩 7 个 .py >500**(check_file_size warning 模式):`auth_admin_routes` 501 · `line_client` 561(🔴高敏·Zihao 在场)· `services/erp/mrerp_product_sync` 1118 · `services/ocr/layer1_vision` 514(OCR 高敏)· `services/recon_jobs/handlers` 693 · `usage_report` 574 · `vat_excel_exporter` 626。**下个建议 = `vat_excel_exporter` 626(报表·同域·低敏)或 `usage_report` 574**;高敏(line_client/layer1_vision)留 Zihao 在场。另 src/home/*.js 多个 >500。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
