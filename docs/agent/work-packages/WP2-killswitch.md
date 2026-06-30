# WP2 · 钥匙闸(platform_settings + 超管开关 + 灰度)

> 给执行窗口:可与 WP1/WP3 **并行**(不碰同文件)。这包让你能"一秒关掉 Agent 回退现状"+"先给指定账号灰度"。

## 背景
- `../MASTER-PLAN.md §3 M0` + `../M1-SOCKET-DESIGN.md §8`(开关是安全阀不是省钱阀)。
- 核心需求:超管("Earn"账号)后台一个开关,关=整个 Agent 层被绕过=用户无感回到现状;支持 allowlist 只对指定用户开。

## 现状事实(已探查)
- 超管守门:`core/route_helpers.py:_require_super_admin()`(L57-65,查 `users.is_super_admin`)。
- **没有 platform_settings 表**;现有 feature flag 全走 env(`OCR_ASYNC_WEB`、`SIGNUP_DISABLED` 是范例)。
- 灰度先例:`is_test_whitelist`(前端)、`exception_whitelist` 表。
- 建表范式:`services/auth/schema.py:_ensure_schema()`(启动期幂等,每条独立事务)。
- 超管前端:`static/admin/admin.{html,js}`,`_verifySuperAdmin()`(admin.js L114)。

## 要建什么
1. `services/platform_settings/schema.py:ensure_platform_settings()` —— 建表(key TEXT UNIQUE, value JSONB, enabled BOOL, updated_at, updated_by)+ allowlist 表(setting_key, user_id)。**不上 RLS**(全局非租户表,应用层超管守门;参考 operation_logs 终态 DISABLE)。挂进启动 ensures。
2. `services/platform_settings/store.py` —— `get_setting(key)` / `set_setting(key,value,enabled,by)` / `is_enabled_for_user(key, user_id)`(查全局 enabled + allowlist)。
3. `routes/admin_settings_routes.py`(新)—— `GET/POST /api/admin/platform-settings`,入口 `_require_super_admin(request)`。
4. `core/feature_flags.py`(新或扩)—— `agent_enabled_for(user_id) -> bool`,供 WP5 入口闸调。**默认关**(表无记录/查失败→False)。
5. 前端:`static/admin/admin.{html,js}` 加"全局设置"tab + `toggle-agent-enabled` 开关 + allowlist 编辑(参考探查给的 UI 范式)。

## 验收
- 集成测试:`agent_enabled=False`(默认)→ `agent_enabled_for(any)` 返 False;`True` 且 user 在 allowlist → True;`True` 但不在 allowlist → 看全局策略(M1 先全开/灰度二选一,默认 allowlist-only)。
- 超管 UI 真能改开关并持久化;非超管访问 `/api/admin/platform-settings` → 403。
- 建表幂等(重启不报错);该表 `\d` 确认无 RLS policy。
- 每新文件 ≥1 测试。

## 不要碰
- ❌ 不碰 `services/agent/*`(WP1)、`services/expense/line_agent.py`(WP5)。
- ✅ 只在 `services/platform_settings/` + `routes/admin_settings_routes.py` + `core/feature_flags.py` + `static/admin/*`。
- 改 admin.js/admin.html 若进 Vite 打包需 `npm run build` + 提交 dist;纯静态则 bump `?v=`。确认 admin 资产的构建方式再动。
