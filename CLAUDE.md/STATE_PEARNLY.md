# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ mrerp_xlsx_generator 1336→facade 381 收官 · 拆 5 leaf · prod 上线**)

- **本窗口 task ✅ 收官**:`mrerp_xlsx_generator.py`(MR.ERP xlsx 生成 · 函数堆)facade 切。1336→**381**(<500)。push `8b5e0aa..5440efb` 上线、prod /api/version 200 健康。6 模块全 <500:
  - `mrerp_xlsx_fmt`(102 · fmt_* + 校验上限常量)/ `mrerp_xlsx_lookups`(118 · 商品归一化/映射 + 客户/科目/税种查表 + derive_tax_kind)
  - `mrerp_xlsx_schemas`(292 · 9 sheet schema + 错误码 + sheet 收集/命名)/ `mrerp_xlsx_sharedstrings`(187 · openpyxl→PhpSpreadsheet 兼容后处理)
  - `mrerp_xlsx_sales_credit`(367 · sales_credit row/detail/tail 装配 + Korn 真样本克隆 · 经 `_gen.derive_mrerp_invoice_no` 解析)
  - 主 `mrerp_xlsx_generator`(381 · facade · derive_/validate/generate_xlsx 编排/make_filename + 全 re-export)。
- **⚠️ monkeypatch 双目标陷阱(facade 切 ERP/计费类必查)**:测试/适配器不止 patch `gen.derive_mrerp_invoice_no`(8 处)· 还 patch **`gen.MRERP_INVOICE_NO_MAX` 常量**(1 处 · test_bill_no_too_long 隔离 bill 检查)。grep `(_gen|gen|模块名)\.[A-Za-z_]+ *=` 抓全部 patch 目标(含常量·别只抓函数)。**读 patch 目标的函数(此处 validate)留 facade**(同模块 late binding · 两 patch 自然流入 · 字节 verbatim);**只调 derive_ 不读常量的函数**(build_*/korn)下沉 leaf · 经 `_gen.derive_` 解析(同 mrerp_adapter_masterdata 既有 `_gen.` 范式)。循环 import(facade↔leaf)用 `import 模块 as _gen`(非 from-import)· leaf 只在 facade 之后 import。
- **验证**:OLD vs 新逐 cell/字节 · generate_xlsx[sales_credit] korn 克隆**原始字节 identical** · 其余 sheet_kind openpyxl 路径逐 cell identical · validate/derive/build_*/fmt/lookups 全输出一致 · monkeypatch(derive + MRERP_INVOICE_NO_MAX)流入 validate 实测通过。
- **✅ 前序收官**:`bank_recon_excel` 1397→facade 380(export_bank_recon_excel 816 闭包重函数·cell-等价)· `recon_routes` 2000→460 · `vat_excel_export` 1960→55(详见 ARCHIVE)。
- **最后 commit**:`5440efb`。**下个 task = `services/erp/mrerp_customer_sync` 1324 → `report_engine` 1026 → `email_ingest` 676 → `services/erp/mrerp_dms_client` 606 → `line_client` 561(高敏·Zihao 在场)→ 报表 `vat_report_parser`**。剩 ~12 个 .py >500(check_file_size warning 模式·FAIL 30→剩余)。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
