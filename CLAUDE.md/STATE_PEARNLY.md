# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ erp_routes 504→61 · 连接/列表路由拆 · prod 上线**)

- **本窗口 task ✅ 收官**:`erp_routes.py` 路由组再拆 —— 连接测试/端点健康检查/客户·商品列表(向导 Step-3)+ listing 缓存 + wizard/products 抽到 `erp_listing_routes`(473)。erp_routes 504→**61**(纯聚合 facade · include_router 三组 + re-export)。push `40c5a26..83d306d` 上线、prod 200。
- **路由组拆范式(recon_routes 同源)**:子模块自建 `router=APIRouter()` → 主 include_router → **erp_routes.router 仍 20 路由(URL/method split-contract 测试锁)** · app.py include_router(erp_router) 不变。7 路由函数 AST identical。
- **⚠️ monkeypatch 随实现模块走(route 拆必踩)**:连接 handler 现在 erp_listing_routes 命名空间解析 `get_current_user_from_request`/`_check_push_access` → dispatch/retry/wizard 测试的 `patch.object(erp_routes, ...)` 改指 `erp_listing_routes`(16 处 · 含多行 `patch.object(\n erp_routes,\n "name")` 形式 · 单行 range-replace 会漏多行形式 · 用 multiline regex)。erp_routes 仍 re-export 这两名 + 3 缓存 + flush + 路由函数(契约零改 · push/endpoint 测试不动)。
- **✅ 本会话连收 8 个**:bank_recon_excel · mrerp_xlsx_generator · mrerp_customer_sync · report_engine · email_ingest · mrerp_dms_client · erp_routes(+ 接力前 recon_routes/vat_excel)。范式 [[megaclass-mixin-split-playbook]] / [[giant-function-decomposition-playbook]] / [[app-py-route-split-reexport-contracts]] / [[facade-split-monkeypatch-constant-trap]]。
- **最后 commit**:`791b496`(含收尾 /simplify:删 erp_routes 死 re-export · 4 路 reuse/简化/效率/altitude 其余全绿 · 验证体 verbatim/facade 薄/无新增重复)。**下个 task = `auth_admin_routes` 501(超管路由·略高敏)→ `line_client` 561(高敏·Zihao 在场)→ 报表 `vat_report_parser` → `bank_recon_v2` facade 剩余刀 → `services/erp/mrerp_product_sync`?**。剩 ~7 个 .py >500(check_file_size warning 模式)。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
