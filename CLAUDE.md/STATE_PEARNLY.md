# 📊 STATE · Pearnly 项目状态

<!-- ╔═══════════════════════════════════════════════════════════════╗
     ║  状态卡 · 每窗口收尾【重写这一段·别追加】· 保持 ≤30 行         ║
     ║  数字只信 `python scripts/refactor_progress.py`,本卡是快照     ║
     ║  历史明细 → CLAUDE.md/STATE_ARCHIVE.md(按需查·不必每窗口读)   ║
     ╚═══════════════════════════════════════════════════════════════╝ -->

## 🎯 状态卡（2026-06-04 · **Wave2 后端工程化全收官 · B5/B6/B7/B9 上线 + prod 验证**）

- **本窗口:Wave2 后端工程化 5 件全做完 + prod 验证**(用户界面零变化 · 整顿期 0 新功能 · 不发版本通知):
  - **B6 结构化日志 + 全链路 trace**:`90d359d`(JSON 日志 + request_id 纯 ASGI 中间件)+ `2c65768`(part2 · auth 绑 user/tenant)· prod 响应头带 X-Request-ID · 日志已 JSON · /api/me 鉴权零回归。
  - **B5 全局限流**:`7b27167` · `services/ratelimit` 纯 ASGI(默认 600/min · 豁免 health/ready/webhook/static · fail-open)· prod 连发 10 次不误伤。
  - **B9 索引**:`49ea11e` + **prod 已建 3 索引(CONCURRENTLY)** · ocr_history(user,created)+ erp_push_logs(dedup / user,created)· `docs/refactor/b9-index-audit.md`。
  - **B7 错误聚合**:`d9fe896` + **prod 已建 error_events 表** · error_store(fail-open)+ 500 handler 持久化 + GET `/api/admin/diagnostics/errors`(超管时间线)。
  - **B3 决策**(Zihao 选①):forward-looking 达成(往后新 schema 走 Alembic + 闸禁新增 ensure_*)· 旧 19 表 retro 跳过(纯文档零线上价值)· 不改部署模型。
  - **B4 /ready + B10 连接池**:实测早已完成(看板 stale 已更正)。
- **未提交残留**:无(5 提交全 push + CI 绿)。**prod 写**(B9 索引 / B7 表)已 Zihao 授权 ssh 应用 + 验证。
- **下一步候选**:Wave2 前端(C4 组件库 / C5 TS / C9 状态管理)/ Wave3 笔记本 staging([[spare-laptop-staging-then-prod]])/ 或 Zihao 解整顿封锁做真功能/UI。整顿期 B 阶段后端工程化已基本收官(B1/B2 巨石拆分早完成 · B3-B10 本窗口收齐)。

<!-- ═══════════════ 历史明细已移至 CLAUDE.md/STATE_ARCHIVE.md ═══════════════ -->
<!-- 新窗口:读上面状态卡 + 跑 scripts/refactor_progress.py 就能开工 -->
