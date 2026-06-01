# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **bank_recon_v2 6745→3745 · facade 切 5 刀全 verbatim 上线 · prod 健康**)

- **本窗口 task**:拆全项目最大文件 `bank_recon_v2.py`(6745·**纯函数堆+dataclasses·非巨类→facade 切**,非 mixin)。已落 5 刀全 verbatim(AST identical·0 逻辑改·全量 2176 unittest 绿·push 上线·commit `ac742c9..cbc0075`):
  - **C1** dataclasses → `services/recon/bank_recon_types.py`(leaf 破循环)
  - **C2** Excel 导出(~1380·纯呈现)→ `bank_recon_excel.py`
  - **C3** 共享常量+OCR缓存+基础utils → `bank_recon_utils.py`(`DATE_TOL_DAYS` 蓄意留 facade·见下)
  - **C4** 账单余额校验/自修复(PDF+xlsx 共用)→ `bank_stmt_balance.py`(307)
  - **C5** 账单解析叶子拆 3 模块:`bank_stmt_text`(330)/`bank_stmt_extract`(454 表格+坐标)/`bank_stmt_gemini`(248)。**orchestrator `parse_bank_statement_pdf` 蓄意留 facade**(它还调 pipeline 适配 `_parse_bank_stmt_via_pipeline` + GL 助手 `_pdf_extract_text_safe`/`_is_summary_row`·那些块未拆·移走会循环·F821 兜底验证后定的边界)。
- **拆法范式(给后续 recon 刀)**:Python 字节切片(探测 LF/CRLF·边界 assert)→ AST/literal 比对证 0 逻辑改 → ruff F401 --fix 裁剪 + **F821 兜底抓 facade/子模块漏 import**(C3 抓到 `_BANK_SIGNATURES`、C5 抓到 orchestrator 跨块依赖)→ 删「未用」import 前查 re-export 契约(纯 re-export 加 `# noqa: F401`·本地用的不加)→ black 保 CRLF(按首行)→ import app + 全量 unittest + 契约。子模块全 <500。
- **🔴 高敏发现 `DATE_TOL_DAYS` 全局名冲突(对账容差地雷·记忆 [[date-tol-days-shadowing]])**:行 32 `=3`(注释/文档写 L2 ±3 天)是**死代码**,被 scoring 段 `=7` 模块加载时覆盖 → reconcile L2 匹配**运行时实际 7 天**(实测 `import bank_recon_v2;print(DATE_TOL_DAYS)`=7)。重构保 verbatim=7,**不顺手改**。拆 reconcile/scoring 必把它绑同一刀别分模块(否则悄改容差=判定级事故)。7-vs-3 是否要改 = 另开非重构修复任务·Zihao 拍板。
- **剩余(facade 3745→目标 <500·下窗口)**:① **GL 解析块 ~1700**(含账单 xlsx/csv·误挂 GL 标题下)+ pipeline 适配 + 共享助手 `_pdf_extract_text_safe`/`_is_summary_row`/`_norm_thai` → 抽共享层后 orchestrator+GL 才能干净移出 ② legacy ParsedStatement 适配 ~730 ③ JSON 序列化 ~98 ④ merge ⑤ **🔴高敏 reconcile + scoring/run_matching(对账判定核心·铁律#26)**:连 `DATE_TOL_DAYS` 一刀·**做前单独发 Zihao 方案 + 真账号 field-diff E2E**。
- **建议待办(simplify altitude 提·非必须)**:`bank_stmt_extract`(454)可再拆 tables / coords 两正交模块(已<500 故非阻塞·下窗口顺手)。
- **命名决策(Zihao 拍 · 选 A)**:`bank_recon_v2` 的 "v2" 有真实含义(配 `bank_recon_v2_store`·区别 v1 遗留),但改名(→ `bank_recon_engine` 或进 `services/recon/`)**并进最后的目录重组波**(铁律#30·import 只改一遍)·现在只记录·不单独动。新拆子模块已全正规名(无 v2)。
- **最后 commit**:`cbc0075`(C5)。本窗口 recon 5 刀 + docstring 收口(simplify)全 push 上线。`git log --oneline -8` 查。**下个 task = 继续拆 bank_recon_v2 剩余(GL→legacy→序列化)→ 高敏 reconcile/scoring 单独报 → 再 `recon_routes` 2000 / `gl_vat_reconciler` 1423 → ERP 周边 → 报表**。剩 ~17 个 .py >500。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
