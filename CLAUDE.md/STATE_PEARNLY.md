# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ 本窗口五连拆 vat_report_parser/vat_excel_exporter/usage_report/recon_jobs.handlers/auth_admin_routes · prod 上线**)

- **本窗口连收 5 个 ✅**:① `vat_report_parser.py` 969→**179**(切 4 子模块 facade)`26c7368`;② `vat_excel_exporter.py` 626→**448**(抽 _LABELS 到 `vat_excel_labels.py` 185)`ba4860c`;③ `usage_report.py` 574→**440**(抽字体/文本到 `usage_report_pdf_text.py` 141)`6a15a35`;④ `services/recon_jobs/handlers.py` 693→**314**(run_bank_recon→`bank_handler.py` · 辅助→`_handler_common.py`)`461fc16`;⑤ `auth_admin_routes.py` 502→**221**(风控组→`auth_admin_risk_routes.py` 277 · helper→`auth_admin_common.py` · 主 include_router)`3ddb5cd`。五次 pre-push 2176 测试全绿放行。
- **范式(函数堆/数据 facade · [[facade-split-monkeypatch-constant-trap]] / [[app-py-route-split-reexport-contracts]] / [[giant-function-decomposition-playbook]])**:脚本按行 verbatim 字节切(newline='' 保 CRLF · 防手敲丢特殊空格)· ast.dump 逐符号全等(vrp40/vex23/usage17)· 依赖无环 · 全 <500。⚠️**可变模块全局**(usage 的 _HAS_CJK/_BASE_FONT)抽走前确认主函数只用 getter 返回值不直读 → 否则 `from x import` 拿快照=bug。
- **⚠️ re-export + monkeypatch + 嵌套 include 契约**:外部只 import 主入口/router;handlers 拆踩 **monkeypatch 随实现模块走坑**(run_bank_recon 搬 bank_handler → test_s8 `patch.object(_read_inputs)` 改指 bank_handler · worker `assertIs` 靠 re-export 同一对象保);auth_admin 拆用 **多层嵌套 include_router**(主 router.include_router(risk) · auth_signup 再 include 主 · 端到端验 8 路由零丢)。契约测试 14+4+8+26 + 路由集成 passed。**自测**:U 盘真实 GL/账单/零用金 跑 vrp 旧vs新 11 项逐字段全一致。
- **✅ 本会话连收 13 个**:bank_recon_excel · mrerp_xlsx_generator · mrerp_customer_sync · report_engine · email_ingest · mrerp_dms_client · erp_routes · vat_report_parser · vat_excel_exporter · usage_report · recon_jobs.handlers · **auth_admin_routes**(+ 接力前 recon_routes/vat_excel)。
- **最后 commit**:`3ddb5cd`。**剩 3 个 .py >500**(check_file_size warning 模式):`line_client` 561(🔴高敏·Zihao 盯)· `services/erp/mrerp_product_sync` 1118(ERP·中敏·最大)· `services/ocr/layer1_vision` 514(🔴OCR 高敏)。**下个建议 = `mrerp_product_sync` 1118(中敏·Zihao 授权拆敏感)**;高敏(line_client/layer1_vision)留 Zihao 盯。另 src/home/*.js 多个 >500。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
