# 03 · 接口契约(图纸)

> 全部走 POS 信封(`core/pos_api`):成功 `{"ok":true,"data":{...}}`,失败 `{"ok":false,"error":{"code","message_key"[,"detail"]}}`。前端先看 `ok` 再读 `data`/`error.code`,不裸读顶层、不靠 HTTP 码判业务成败。路由薄层:鉴权 → `get_cursor_rls(tid)` → store → `ok()`。

## 1. GET /api/me/modules(扩 · 已存在)

读当前租户全模块态 + 业态。任意已登录主体可调(导航需要)。

**响应 data**:
```json
{
  "modules": {
    "sales":      {"enabled": true,  "config": {}},
    "expense":    {"enabled": true,  "config": {}},
    "recon":      {"enabled": true,  "config": {}},
    "inventory":  {"enabled": false, "config": {}},
    "pos":        {"enabled": false, "config": {}},
    "receivable": {"enabled": true,  "config": {}},
    "knowledge":  {"enabled": true,  "config": {}}
  },
  "business_type": "retail",
  "gateable": ["sales","expense","recon","inventory","pos","receivable","knowledge"]
}
```
- `modules` 覆盖 `KNOWN_MODULES` 全集(含新增 `receivable`),无显式行回落 `DEFAULT_ENABLED`。
- `business_type`:哨兵行的值;老租户/未 onboarding = `null`。
- `gateable`:可开关模块全集(前端区分底座 vs 可开关;底座不在此列)。
- **扩展位(P 阶段按需)**:`pos` 可附 `provisioned: bool`(账套是否已建终端/收银员),区分 enabled≠provisioned(02 D3)。本期可不返,前端先用 enabled。

## 2. PUT /api/me/onboarding(新 · 应用业态预设)

注册首次「选业态」+ 设置页「切换业态」共用。**owner 专属**(D5)。

**请求体**:`{"business_type": "retail"}`
**行为**:`apply_preset` —— 对 7 个 module 逐个 `set_module(enabled = key∈预设, config=None)` + `set_business_type`,单事务(`get_cursor_rls(tid, commit=True)`)。不建 POS 硬件(D3)。
**响应 data**:同 §1(回写后的 `modules` + `business_type`)。
**错误**:
- 非 owner / 收银员 → `pos.forbidden`(403)。
- `business_type` 不在 canonical 6 个 → `pos.line_invalid`(422,经请求体校验信封)或路由内 `PosError("platform.unknown_business_type",400)`。

## 3. PUT /api/me/modules/{module_key}(新 · 单模块开关)

设置页逐个 toggle。**owner 专属**(D5)。**关=隐藏不删**(D2)。

**路径**:`module_key` ∈ `KNOWN_MODULES`。
**请求体**:`{"enabled": true}`
**行为**:`set_module(enabled=..., config=None)`(只翻开关,保留 config)。
**响应 data**:`{"module_key": "...", "enabled": true, "config": {...}}`
**错误**:
- 非 owner → `pos.forbidden`(403)。
- 未知 `module_key` → `PosError("platform.unknown_module", 404)`(store 抛 `ValueError` → 路由翻)。

## 4. 信封覆盖(core/pos_api)

把模块管理路径纳入请求体校验信封:`_POS_PREFIXES` 增 `"/api/me/modules"`,`_POS_EXACT` 增 `"/api/me/onboarding"`。仅影响这些路径的 422 渲染(其余 `/api/me/*` 行为不变)。

## 5. 错误码(并入 docs/pos/06 错误码本)

| code | http | 含义 |
|---|---|---|
| `pos.forbidden` | 403 | 非 owner / 收银员调管理动作(复用既有) |
| `platform.unknown_business_type` | 400 | 业态 key 不在 canonical 6 |
| `platform.unknown_module` | 404 | toggle 的 module_key 不在 KNOWN_MODULES |

前端 i18n 映射 4 语,绝不裸露 code(P 阶段补 `static/dist/i18n-data.js`,本窗口不碰)。
</content>
