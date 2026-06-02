# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ bank_recon_excel 1397→facade 380 收官 · export_bank_recon_excel 816 单函数分解 · prod 上线**)

- **本窗口 task ✅ 收官**:`bank_recon_excel.py` 唯一巨函数 `export_bank_recon_excel`(816 行 · 18 嵌套闭包)分解。facade 841→**380**(<500)。push `5834f5a..27780e5` 上线、prod /api/version 200 健康。3 模块全 <500:
  - `bank_recon_excel_styles`(44 · 共享调色板 COLOR_* + `_hdr_style`/`_border_range`/`_fmt_date` leaf · Sheet2/5/6 共用)
  - `bank_recon_excel_summary`(465 · `_build_summary_sheet` · Sheet1 全块**含 18 内层闭包原样搬运**)
  - 主 `bank_recon_excel`(380 · facade · Sheet2/5/6 builder + 编排器)
- **巨函数分解(闭包重型版)范式**:捕获 `ws1`+行游标 `r`(nonlocal)的内层闭包**不提模块级**·整块连闭包字节级搬进 `_build_sheetN`(仍作 closure 存活·0 逻辑改);只有吃 `ws` 参数、无捕获的通用样式 helper 才提 leaf。**逐 cell 金标准等价验证**:旧 `_OLD` vs 新 · 4 语 × 5 输入形态(plain/taskinfo/overrides/zeromatch/empty)20 组 · value/number_format/font/fill/alignment/comment/行高/列宽/合并/冻结全 identical。
- **去 AI 味**:删死代码 `_label_style`/`_num_style`(全 repo 0 调用点·删除不影响输出);summary import 去未用 Border/Side。openpyxl 改模块顶层 import(硬依赖·对齐 vat 范式)。⚠️**契约**:`export_bank_recon_excel` 名字/签名不变(含未用的 `anchor_ocr` 参数保留)→ `bank_recon_v2` re-export + 路由 + 3 个 brv2 export 测试 0 改;`_t`/`_layer_label`/`_status_label`/`_USAGE_BLOCKS` re-export 保留。
- **✅ `recon_routes` 2000→460 收官**(路由组拆 8 子模块全 <500 · gl_vat 1423→72 · 详见 STATE_ARCHIVE)。**✅ `vat_excel_export` 1960→55 收官**(build_excel 624 单函数分解·cell-等价·详见 ARCHIVE)。
- **最后 commit**:`27780e5`。**下个 task = `mrerp_xlsx_generator` 1336(纯 xlsx 生成·低风险)→ `report_engine` 1026 → `services/erp/mrerp_customer_sync` 1324 → ERP 周边 → 报表 `vat_report_parser`**。剩 ~13 个 .py >500(check_file_size 仍 warning 模式)。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
