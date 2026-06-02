# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ vat_report_parser/vat_excel_exporter/usage_report 三连拆 · prod 上线**)

- **本窗口连收 3 个 ✅**:① `vat_report_parser.py` 969→**179**(切 4 子模块 vat_parser_{common89/excel140/pdf234/gemini397} 聚合 facade)`26c7368`;② `vat_excel_exporter.py` 626→**448**(抽 _LABELS 4语+_OVERRIDE 到 `vat_excel_labels.py` 185 · 删死变量 row_count)`ba4860c`;③ `usage_report.py` 574→**440**(抽 reportlab 字体注册+泰/CJK 文本渲染到 `usage_report_pdf_text.py` 141 · 删 unused os)`6a15a35`。三次 pre-push 2176 测试全绿放行。
- **范式(函数堆/数据 facade · [[facade-split-monkeypatch-constant-trap]] / [[app-py-route-split-reexport-contracts]] / [[giant-function-decomposition-playbook]])**:脚本按行 verbatim 字节切(newline='' 保 CRLF · 防手敲丢特殊空格)· ast.dump 逐符号全等(vrp40/vex23/usage17)· 依赖无环 · 全 <500。⚠️**可变模块全局**(usage 的 _HAS_CJK/_BASE_FONT)抽走前确认主函数只用 getter 返回值不直读 → 否则 `from x import` 拿快照=bug。
- **⚠️ re-export 契约**:外部只 import 主入口(vrp=`parse_vat_report` / vex=`export_recon_task` / usage=`build_pdf,build_xlsx`)· 契约测试零 monkeypatch(vrp facade 显式 re-export `_hit/_map_columns/_build_row` noqa)· 14+4+8 passed。**自测**:U 盘真实 GL/账单/零用金 跑 vrp 旧vs新 11 项逐字段全一致(Excel 168 行 / PDF 表格 18·43 行)。
- **✅ 本会话连收 11 个**:bank_recon_excel · mrerp_xlsx_generator · mrerp_customer_sync · report_engine · email_ingest · mrerp_dms_client · erp_routes · vat_report_parser · vat_excel_exporter · **usage_report**(+ 接力前 recon_routes/vat_excel)。
- **最后 commit**:`6a15a35`。**剩 5 个 .py >500**(check_file_size warning 模式):`auth_admin_routes` 501(超管·略敏)· `line_client` 561(🔴高敏·Zihao 在场)· `services/erp/mrerp_product_sync` 1118 · `services/ocr/layer1_vision` 514(🔴OCR 高敏)· `services/recon_jobs/handlers` 693。**下个建议 = `services/recon_jobs/handlers` 693 或 `auth_admin_routes` 501(低/中敏)**;高敏(line_client/layer1_vision)留 Zihao 在场。另 src/home/*.js 多个 >500。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
