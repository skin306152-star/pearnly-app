# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ mrerp_dms_client 606→47 · DMSClient 巨类 mixin · prod 上线**)

- **本窗口 task ✅ 收官**:`services/erp/mrerp_dms_client.py`(DMS 汽车销售 · 身份证→订车单 · Zihao 拍板"照拆")DMSClient 巨类(27 方法 · ~531 行)mixin 拆分。606→**47**。push `60b05f2..1190966` 上线、prod 200。4 模块全 <500:
  - `mrerp_dms_client_base`(30 · DMSClientError + excel_serial/to_be_date/_EXCEL_EPOCH · 破 facade↔mixin 循环 import 的 leaf)
  - `mrerp_dms_client_ops`(358 · DMSClientOpsMixin · ensure_customer/import/patch/push/fetch/resolve/search)/ `mrerp_dms_client_forms`(204 · DMSClientFormsMixin · 表单 POST/解析 + 地址地理主档级联 + HTML 微解析 · 含 `_GEO_PREFIXES` 类属性)
  - 主(47 · `class DMSClient(Ops, Forms)` · __init__ + base re-export)。
- **本轮 2 个新坑(已写 [[megaclass-mixin-split-playbook]])**:① **扫 class-body 非方法语句**——类级属性 `_GEO_PREFIXES`(小写下划线开头·非 UPPER 常量)被结构 grep 漏掉、geo-resolve 测试 AttributeError 抓到;正解 = AST 扫 ClassDef.body 非 FunctionDef 节点,只被某 mixin 用就放那 mixin。② **check_new_debt ensure_* 闸误报**——正则按前缀把 verbatim 搬家的 `def ensure_customer` 误判成铁律 #5 db 建表;走 commit `NEW-DEBT-EXEMPT:` 官方透明豁免,**绝不 --no-verify**。
- **验证**:OLD vs 新 29 函数 ast.dump 全 identical · `_GEO_PREFIXES` 值全等 · MRO=[DMSClient, Ops, Forms, object] · 假 transport 实例化通过 · test_mrerp_dms_adapter 7 例(geo-resolve 跨 mixin self.* 实测)绿。
- **✅ 本会话连收 7 个**:bank_recon_excel 1397→380 · mrerp_xlsx_generator 1336→381 · mrerp_customer_sync 1324→111 · report_engine 1026→104 · email_ingest 676→46 · mrerp_dms_client 606→47(+ 接力前 recon_routes/vat_excel)。
- **最后 commit**:`1190966`。**下个 task = `erp_routes` 504(路由组拆·用 recon_routes 范式)→ `auth_admin_routes` 501 → `line_client` 561(高敏·Zihao 在场)→ 报表 `vat_report_parser` → `bank_recon_v2` facade 剩余刀**。剩 ~8 个 .py >500(check_file_size warning 模式)。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
