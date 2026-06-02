# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ 本窗口四连拆 vat_report_parser/vat_excel_exporter/usage_report/recon_jobs.handlers · prod 上线**)

- **本窗口连收 4 个 ✅**:① `vat_report_parser.py` 969→**179**(切 4 子模块 vat_parser_{common89/excel140/pdf234/gemini397} facade)`26c7368`;② `vat_excel_exporter.py` 626→**448**(抽 _LABELS 4语+_OVERRIDE 到 `vat_excel_labels.py` 185)`ba4860c`;③ `usage_report.py` 574→**440**(抽 reportlab 字体+泰/CJK 文本到 `usage_report_pdf_text.py` 141)`6a15a35`;④ `services/recon_jobs/handlers.py` 693→**314**(run_bank_recon→`bank_handler.py` 304 · 辅助下沉 `_handler_common.py` 78)`461fc16`。四次 pre-push 2176 测试全绿放行。
- **范式(函数堆/数据 facade · [[facade-split-monkeypatch-constant-trap]] / [[app-py-route-split-reexport-contracts]] / [[giant-function-decomposition-playbook]])**:脚本按行 verbatim 字节切(newline='' 保 CRLF · 防手敲丢特殊空格)· ast.dump 逐符号全等(vrp40/vex23/usage17)· 依赖无环 · 全 <500。⚠️**可变模块全局**(usage 的 _HAS_CJK/_BASE_FONT)抽走前确认主函数只用 getter 返回值不直读 → 否则 `from x import` 拿快照=bug。
- **⚠️ re-export + monkeypatch 契约**:外部只 import 主入口(vrp=`parse_vat_report` / vex=`export_recon_task` / usage=`build_pdf,build_xlsx`);handlers 拆**踩 monkeypatch 随实现模块走坑**——run_bank_recon 搬 `bank_handler` 后 test_s8_review_gate 的 `patch.object(_read_inputs)` 须改指 bank_handler(实现所在),worker `assertIs` 注册契约靠 facade re-export 同一对象保住。契约测试 14+4+8+26 passed。**自测**:U 盘真实 GL/账单/零用金 跑 vrp 旧vs新 11 项逐字段全一致。
- **✅ 本会话连收 12 个**:bank_recon_excel · mrerp_xlsx_generator · mrerp_customer_sync · report_engine · email_ingest · mrerp_dms_client · erp_routes · vat_report_parser · vat_excel_exporter · usage_report · **recon_jobs.handlers**(+ 接力前 recon_routes/vat_excel)。
- **最后 commit**:`461fc16`。**剩 4 个 .py >500**(check_file_size warning 模式):`auth_admin_routes` 501(超管·中敏)· `line_client` 561(🔴高敏·Zihao 在场)· `services/erp/mrerp_product_sync` 1118(ERP·中敏)· `services/ocr/layer1_vision` 514(🔴OCR 高敏)。**下个建议 = `auth_admin_routes` 501 或 `mrerp_product_sync` 1118(中敏·Zihao 授权拆敏感)**;高敏(line_client/layer1_vision)仍留 Zihao 盯。另 src/home/*.js 多个 >500。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
