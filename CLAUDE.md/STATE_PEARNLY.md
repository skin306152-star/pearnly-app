# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ recon_routes 2000→460 收官 · 路由组拆 8 子模块全 <500 · gl_vat 1423→72 收官 · prod 上线**)

- **本窗口 task ✅ 收官**:拆 `recon_routes.py`(2000→**460**·FastAPI 路由组拆·**含计费主路径·Zihao 拍板 3-way 全拆**)。verbatim(handler body AST identical·仅换装饰器对象名)·全量 2177 unittest 绿·push `bd450d9..2a9d449` 上线。8 子模块全 <500:
  - `recon_routes_shared`(20·_user_key+_pdf_billing_units 跨组共享 leaf)/ `recon_routes_progress`(45·进度子系统 leaf·_progress_store 单实例)
  - `recon_routes_glvat`(404·/gl-vat/* 6 路由·🔴计费 gl_vat_run)/ `recon_routes_v1_batch`(349·batch_process 屏B + 删除 trio)
  - **🔴bank-v2 三模块**:`_helpers`(280·bank_recon_v2 接入+i18n+完整度/锚点·except 加 None 绑定保降级)/ `_run`(410·计费 bank_v2_run)/ `_bankv2`(219·CRUD + include run 子路由)
  - 主 `recon_routes` 460 = v1 核心(run_recon/_run_match_and_save 等)+ 全 re-export + 3 include。
- **路由拆范式**:子模块各建 `APIRouter()` 无 prefix → 主 `include_router` → **路由表 24 条 sorted diff 拆前后逐字一致**(拆路由必验此)。⚠️ **AST lineno 指 def 不含装饰器**·块首 handler 的 `@router` 在区间外会丢→没注册(已被 6→4 路由数抓到·起点取 `min(decorator_list.lineno)`)。
- **契约**:`recon_jobs/handlers.py` 运行时 `from recon_routes import ...` 拉 bank/gl 函数 + handler·全 re-export(否则 worker import 崩 + monkeypatch 失效)·静态审计测试改读子模块并集·monkeypatch 命名空间改指实现模块([[wa-ocr-core-split-entangled]])。F811 抓 hashlib/asyncio 嵌套 import 撞模块头。
- **⚠️ CRLF 坑**:footer 拼接时块尾已自带回车、再补换行=双回车(乱码)·按换行符 split 切行后须收尾把双回车折叠回单换行(replace 双 CR→单 CR)。**black --check 经管道 tail 会吞掉退出码误判通过**·pre-push 机械闸兜住·验 gate 必看退出码不只看 stdout。
- **最后 commit**:`2a9d449`。**下个 task = `vat_excel_export` 1960(纯导出·无计费·低风险)→ `bank_recon_excel` 1397 / `mrerp_xlsx_generator` 1336 → ERP 周边(customer/product_sync)→ 报表**。剩 16 个 .py >500。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
