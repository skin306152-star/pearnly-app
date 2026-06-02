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
- **✅ `vat_excel_export` 1960→55 收官**(8 刀上线 `1be4296..3ee46c6`·纯 re-export 壳):`vat_excel_i18n`(323)/`vat_recon_core`(337·配对/差异/归一化 leaf)/`vat_ocr_extract`(319·单张 OCR)/`vat_ocr_batch`(248·批量)/`vat_report_merge`(125)/`vat_excel_styles`(56·样式 leaf)/`vat_excel_build`(256·编排+Sheet1/2/4)/`vat_excel_sheet3`(397·一对一对账)。**`build_excel` 624 单函数分解**(给税局 Excel):样式无运行时依赖→提模块级·sheet body 保 4 空格缩进搬进 `_build_sheetN`(字节级 0 逻辑改)·只 Sheet3 产出返回数据·**旧 vs 新逐 cell+task_summary 跨 4 语完全一致**(金标准验证)。命名空间坑:merge 的 parse_vat_report monkeypatch 改指 vat_report_merge;normalize_* 保 re-export(safety-net 测试)。⚠️教训:`git show | python - <<'PY'` heredoc 抢 stdin 管道不进 python·改先写文件再读。
- **`bank_recon_excel` 1397→841 进行中**(i18n+usage 2 刀 verbatim 上线 `4ef8115`):`bank_recon_excel_i18n`(407·_I18N_EXPORT+_t/_layer_label/_status_label)/`bank_recon_excel_usage`(170·_USAGE_BLOCKS)。⚠️**剩 `export_bank_recon_excel` 816 单函数**=facade 还 841>500·**比 build_excel 难**:函数内 ~18 个嵌套闭包 helper(`_title_row`/`_anchor_row`/`_detail_row`/`_hdr_style` 等)全靠 closure 捕获 ws/行游标/样式常量·提模块级要把这些全串成参数=大面积非 verbatim 改造·数据关键(银行对账 Excel)·**留专注新窗口带 Plan 做**(同 build_excel 范式但先规划闭包→参数映射 + cell-等价验证)。
- **最后 commit**:`4ef8115`。**下个 task = `export_bank_recon_excel` 816 分解(facade <500)→ `mrerp_xlsx_generator` 1336(纯生成·低风险)→ ERP 周边 → 报表 `report_engine`/`vat_report_parser`**。剩 ~14 个 .py >500。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
