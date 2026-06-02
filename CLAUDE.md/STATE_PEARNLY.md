# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡(2026-06-02 · **✅ email_ingest 676→46 · 函数堆 facade 切 · prod 上线**)

- **本窗口 task ✅ 收官**:`email_ingest.py`(邮箱附件抓取 IMAP→OCR→推送)facade 切。676→**46**(纯 re-export 壳)。push `a510c1f..c11e5f0` 上线、prod 200。4 模块全 <500:
  - `email_ingest_crypto`(83 · 密码 Fernet 加解密 + is_available · _FERNET 模块缓存随之下沉)
  - `email_ingest_imap`(139 · IMAP_PRESETS/常量 + MIME 解码 + 连接/搜索/抓取/标记已读 helper)
  - `email_ingest_pipeline`(460 · 单附件 OCR 摄取 + 自动推送 + run_account_ingest 编排 + test_connection)
- **验证**:OLD vs 新 14 函数 ast.dump 全 identical · 7 模块级常量值全等 · 契约 `email_ingest._SUPPORTED_EXTS is entrypoints.SUPPORTED_OCR_EXTENSIONS` 保持 True。无 monkeypatch 目标。**F821 兜底再次抓漏**(补回 imap 的 os/email/datetime/timedelta + pipeline 的 os/imaplib/Optional/is_available)——超集 import + ruff --fix 后必跑 F821。
- **✅ 本会话连收 6 个**:bank_recon_excel 1397→380 · mrerp_xlsx_generator 1336→381 · mrerp_customer_sync 1324→111(巨类 mixin)· report_engine 1026→104 · email_ingest 676→46(+ 接力前 recon_routes/vat_excel)。范式 [[megaclass-mixin-split-playbook]] / [[giant-function-decomposition-playbook]] / [[app-py-route-split-reexport-contracts]] / [[facade-split-monkeypatch-constant-trap]]。
- **最后 commit**:`c11e5f0`。**下个 task = `services/erp/mrerp_dms_client` 606 → `erp_routes` 504 → `auth_admin_routes` 501 → `line_client` 561(高敏·Zihao 在场)→ 报表 `vat_report_parser`**。剩 ~9 个 .py >500(check_file_size warning 模式)。
- ⚠️ 旁注:`static/pearnly-cat-laptop.webp` + `pearnly-logo-full.png` 未跟踪(非本人改动·疑 Zihao 加的素材)· 未动。


<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
