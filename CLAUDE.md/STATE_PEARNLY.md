# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-04 · **整顿核心已收官 · 进入 Wave2 后端工程化 · B6 结构化日志上线**）

- **本窗口：Wave2 后端工程化启动**。复盘确认整顿核心（全文件<500 + 包结构 + E7 + 目录重组 + 防屎山硬门）全收官。**B4（/ready 真探活）+ B10（连接池 2/30）实测早已做完**（看板 stale 已更正）。
- **B6 结构化日志 + request_id 全链路上线** `90d359d`：新增 `services/observability/`（log_context contextvar + JSON logging_config + 纯 ASGI request_context 中间件）· `basicConfig`→`configure_logging()` · prod 实测 `/api/ready` 响应头带 `X-Request-ID`（入站沿用/否则 uuid4）· 日志已变 JSON · 13 新测 + 全量 2185 unit 绿 · 新模块走 RATCHET-EXEMPT 豁免。**纯 ASGI 中间件（非 BaseHTTPMiddleware）才能让 contextvar 传到 handler**。
- **下一步（Wave2 剩余 · 我自主不花钱）**：B7 错误聚合（errors 表 + admin 时间线 · 接 B6）/ B5 全局限流（碰热路径 · 保守限额 + 豁免健康检查/webhook）/ B9 索引审计 / **B3 Alembic 迁 25 个 ensure_*（最大 · 碰 schema 红线「生产不跑 alembic upgrade」· 单独立窗口 + 先报方案）**。
- **待 Zihao**：B6-part2（user_id/tenant_id 绑定到 `core/auth.py:get_current_user_from_request` · 🔴高敏 · 纯加日志 0 逻辑改 · 你在场时一行接入）。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
