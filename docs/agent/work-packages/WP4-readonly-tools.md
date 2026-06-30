# WP4 · A 档只读工具(executor 方法)

> 给执行窗口:**依赖 WP1** 的 manifest/executor/contracts 接口落地后才起跑(否则接口对不上要返工)。把 5~8 个只读能力做成可调工具。

## 背景
- `../M1-SOCKET-DESIGN.md §6`(executor 范式)+ `§3`(manifest)。
- A 档 = 只读,最安全,无需确认。先把这些插稳,验证插座通电。

## 现状事实(可直接调的现成 service)
- 查历史:`db.list_ocr_history(user_id, tenant_id, keyword, status_filter, workspace_client_id, limit, offset, retention_days, restrict_client_ids)`(routes/history_routes.py:62 是调用样本)。
- 查余额:`db.get_billing_status_combined(user_id, tenant_id)` → {allowed,balance_thb,pages_used_this_month,subscription}。
- 对账概览:`bank_recon_routes.py` 的 `GET /api/bank-recon/stats`(L189)对应 service。
- 端点列表:erp listing 相关(`agent_registry` 里 erp_listing_routes = A)。
- 推送日志:`erp_push_log_routes` 的查询侧(list_push_logs)。
- 租户隔离:全程 `get_cursor_rls(tenant_id, user_id)`,executor 传 `ctx.tenant_id` / `ctx.user["id"]`。

## 要建什么
1. 在 `services/agent/executor.py`(或 `executor_readonly.py`)实现 5~8 个 A 档方法,签名 `(self, ctx: AgentContext, **slots) -> ToolResult`。
2. 每个方法:调现成 service(带租户隔离)→ 包成 `ToolResult(ok, data, receipt)`;receipt 用 WP3 的 i18n 渲染。
3. 在 `manifest.py` 给每个工具补 `ToolSpec`(若 WP1 没占全)。
4. 在 `agent_registry.json` 确认对应功能区是 A 档(已是)。

## 验收
- 每个工具一个单测:mock ctx(含 user_id/tenant_id)→ 断言调对了 service + 隔离参数传对 + receipt 非空。
- 故意传别的 tenant_id → 断言查不到别人数据(隔离不破)。
- 工具清单与 registry A 档交叉核对绿。

## 不要碰
- ❌ 不做 B 档写工具(M3);不碰 LINE 链路(WP5);不改 manifest 以外的现有 service 逻辑。
- ✅ 只在 `services/agent/executor*.py` + `manifest.py` + 测试。
- ✅ 只"调"现成 service,不改它们的签名/行为。
