# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ vat_report_parser 969→179 + vat_excel_exporter 626→448 · prod 上线**)

- **本窗口连收 2 个 ✅**:① `vat_report_parser.py` 969→**179**(按解析路径切 4 子模块:`vat_parser_common` 89 / `vat_parser_excel` 140 / `vat_parser_pdf` 234 / `vat_parser_gemini` 397 · 聚合 facade)`26c7368`;② `vat_excel_exporter.py` 626→**448**(抽 _LABELS 4 语 + _OVERRIDE 字段映射到 `vat_excel_labels.py` 185 纯数据 · 顺带删死变量 row_count F841)`ba4860c`。两次 pre-push 2176 测试全绿放行。
- **范式(函数堆/数据 facade · [[facade-split-monkeypatch-constant-trap]] / [[app-py-route-split-reexport-contracts]] / [[giant-function-decomposition-playbook]])**:脚本按行 verbatim 字节切(newline='' 保 CRLF · 防手敲丢 `_to_float` 特殊空格)· ast.dump 逐符号全等(vrp 40 / vex 23)· 依赖无环 · 全 <500。
- **⚠️ re-export 契约**:vrp 外部 6 处只 import `parse_vat_report` · 契约测试零 monkeypatch(facade 显式 re-export `_hit/_map_columns/_build_row` noqa);vex 外部/测试只 import `export_recon_task`(字典抽走经它间接验证黄标 · 4 passed)。**自测**:U 盘真实 GL/账单/零用金 文档跑旧vs新 11 项逐字段全一致(Excel 168 行 / PDF 表格 18·43 行)。
- **✅ 本会话连收 10 个**:bank_recon_excel · mrerp_xlsx_generator · mrerp_customer_sync · report_engine · email_ingest · mrerp_dms_client · erp_routes · vat_report_parser · **vat_excel_exporter**(+ 接力前 recon_routes/vat_excel)。
- **最后 commit**:`ba4860c`。**剩 6 个 .py >500**(check_file_size warning 模式):`auth_admin_routes` 501 · `line_client` 561(🔴高敏·Zihao 在场)· `services/erp/mrerp_product_sync` 1118 · `services/ocr/layer1_vision` 514(OCR 高敏)· `services/recon_jobs/handlers` 693 · `usage_report` 574。**下个建议 = `usage_report` 574(低敏)或 `services/recon_jobs/handlers` 693**;高敏(line_client/layer1_vision)留 Zihao 在场。另 src/home/*.js 多个 >500。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
