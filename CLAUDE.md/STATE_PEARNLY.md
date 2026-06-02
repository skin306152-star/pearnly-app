# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ 本窗口八连拆 + simplify · 🏆 后端 .py 全部 ≤500 里程碑 · prod 上线**)

- **本窗口连收 8 个 + simplify ✅**:vat_report_parser 969→**179**(切 4 子模块)/ vat_excel_exporter 626→**448** / usage_report 574→**440** / recon_jobs.handlers 693→**314** / auth_admin_routes 502→**221** / mrerp_product_sync 1119→**125**(833 行巨类拆 3 Mixin · 22 integration)/ line_client 562→**319**(抽 i18n→line_i18n)/ layer1_vision 515→**489**(抽常量+异常→layer1_base)。+ /simplify 收口(_map_columns/_build_row 下沉 common · 删死 re-export)。8 次 pre-push 2176 测试全绿 · commit `26c7368..0c72370`。
- **范式(函数堆/数据 facade · [[facade-split-monkeypatch-constant-trap]] / [[app-py-route-split-reexport-contracts]] / [[giant-function-decomposition-playbook]])**:脚本按行 verbatim 字节切(newline='' 保 CRLF · 防手敲丢特殊空格)· ast.dump 逐符号全等(vrp40/vex23/usage17)· 依赖无环 · 全 <500。⚠️**可变模块全局**(usage 的 _HAS_CJK/_BASE_FONT)抽走前确认主函数只用 getter 返回值不直读 → 否则 `from x import` 拿快照=bug。
- **⚠️ re-export + monkeypatch + 嵌套 include 契约**:外部只 import 主入口/router;handlers 拆踩 **monkeypatch 随实现模块走坑**(run_bank_recon 搬 bank_handler → test_s8 `patch.object(_read_inputs)` 改指 bank_handler · worker `assertIs` 靠 re-export 同一对象保);auth_admin 拆用 **多层嵌套 include_router**(主 router.include_router(risk) · auth_signup 再 include 主 · 端到端验 8 路由零丢)。契约测试 14+4+8+26 + 路由集成 passed。**自测**:U 盘真实 GL/账单/零用金 跑 vrp 旧vs新 11 项逐字段全一致。
- **巨类 mixin 范式([[megaclass-mixin-split-playbook]])实证**:mrerp 833 行巨类 → 脚本按 **AST 方法名**提取分 3 Mixin(非手数行号)· dataclass/常量/解析函数下沉 leaf 破循环 · **class-body 属性扫描坑**:LISTING_PATH 等 5 个类级常量必随主类保留(self.X 被各 mixin 引用)· 包内 import 用绝对 `from services.erp.X`(裸名 ModuleNotFoundError)· AST 34 符号(方法+类属性+常量)全等 · MRO 锁。
- **✅ 本会话连收 16 个**:bank_recon_excel · mrerp_xlsx_generator · mrerp_customer_sync · report_engine · email_ingest · mrerp_dms_client · erp_routes · vat_report_parser · vat_excel_exporter · usage_report · recon_jobs.handlers · auth_admin_routes · mrerp_product_sync · line_client · **layer1_vision**(+ 接力前 recon_routes/vat_excel)。
- **最后 commit**:`0c72370`。**🏆 里程碑:所有后端 .py 全部 ≤500 达成!** check_file_size 仅剩 **16 个 `src/home/*.js`**(纯前端 · 改后必 `npm run build` + `git add static/dist` 一起提交 · 铁律 · view-source 只见 minified bundle · 验证链含真浏览器抓 getComputedStyle/截图,与后端不同 · 建议单独窗口开)。整顿「所有后端源文件 <500」目标达成。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
