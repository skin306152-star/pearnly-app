# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ mrerp_customer_sync 1324→111 · 巨类 mixin 真重构 · prod 上线**)

- **本窗口 task ✅ 收官**:`services/erp/mrerp_customer_sync.py` 巨类 `MRERPCustomerSyncService`(22 方法 · ~1044 行)mixin 拆分。facade 1324→**111**(<500)。push `f70df4c..391d489` 上线、prod 200。7 模块全 <500(沿用 mrerp_adapter mixin 范式 [[megaclass-mixin-split-playbook]]):
  - `_customer_sync_models`(56 · dataclass leaf)/ `_customer_sync_const`(38 · 常量 leaf)/ `_customer_sync_parse`(120 · listing HTML 解析 leaf)
  - `_customer_sync_resolve`(275 · CustomerResolveMixin · L1/L2/L3/seed/upsert)/ `_customer_sync_create`(431 · CustomerCreateMixin · L4 自动建档 Playwright 表单)/ `_customer_sync_fetch`(383 · CustomerFetchMixin · listing/detail 抓取 + verify + delete)
  - 主(111 · `class MRERPCustomerSyncService(三 Mixin)` · __init__/类常量/invalidate + 全 re-export + __all__)。
- **巨类 mixin 范式(实证 2 例:mrerp_adapter 1909→416 + 本次)**:dataclass/常量/纯函数 → leaf 破环;方法按职责分 `class XMixin`(**AST 切片方法体 verbatim**);self.* + 跨 mixin 方法调用经 MRO 回主类;实例属性 + 类常量全留主类。**超集 import → ruff F401 --fix 裁剪(本次 64 项)+ F821=0 兜底漏 import**;**ast.dump 每方法 old vs 新全 identical** + MRO 锁 + __all__ importable。本次测试在 adapter/page 边界 mock(无内部方法 monkeypatch)→ 无命名空间陷阱(比 mrerp_xlsx 简单)。
- **✅ 前序收官**:`mrerp_xlsx_generator` 1336→381(拆 5 leaf · monkeypatch 双目标陷阱 [[facade-split-monkeypatch-constant-trap]])· `bank_recon_excel` 1397→380 · `recon_routes` 2000→460 · `vat_excel_export` 1960→55(详见 ARCHIVE)。
- **最后 commit**:`391d489`。**下个 task = `report_engine` 1026 → `email_ingest` 676 → `services/erp/mrerp_dms_client` 606 → `auth_admin_routes` 501/`erp_routes` 504 → `line_client` 561(高敏·Zihao 在场)→ 报表 `vat_report_parser`**。剩 ~11 个 .py >500(check_file_size warning 模式)。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
