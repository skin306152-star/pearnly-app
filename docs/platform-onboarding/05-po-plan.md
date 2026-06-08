# 05 · PO 计划(施工顺序)

> ⚠️ 状态更正(2026-06-08):B 阶段(后端 PO-PB1/PB2)+ P 阶段(前端 PO-PP1~PP4 导航数据驱动/注册选业态屏/
> 设置模块管理页/i18n)均【已施工并上线 prod】。下面的"本窗口先做 B、P 等 POS 收完再起"是旧排期、已过时,以代码为准。
> 唯一仍未做:老模块 sales/expense/recon/receivable/knowledge 的【后端门控】(见 01-module-gating-map,独立 workstream)。

> 防撞铁律:**P 阶段(前端导航数据驱动)动 `app-shell-html.ts`/`core-boot.ts`/`module-nav.ts`/`i18n-data.js`,与 POS 屏8 前端窗口同批 → 必须等 POS 前端窗口收完 push 后再起。** 本窗口先做 B 阶段(后端,不碰这些文件)。

## B 阶段 · 后端(本窗口 · 不碰 POS 前端文件)

- **PO-PB1 模块全集 + 预设底座**(`services/modules/store.py` 扩 + `services/modules/presets.py` 新)
  - `KNOWN_MODULES` 增 `receivable`;`DEFAULT_ENABLED` 增 `receivable: True`(D1 老租户不破坏)。
  - `presets.py`:`BUSINESS_PRESETS`(02 表)+ `apply_preset(cur, tenant_id, business_type)`。
  - `store.py`:`set_business_type` / `get_business_type`(哨兵行 `__business_type__`)。
  - 测试:扩 `test_modules_store.py`(receivable 默认 / 哨兵读写 / apply_preset 翻 7 开关 + 不动 config)+ 新 `test_presets.py`。

- **PO-PB2 接口**(`routes/modules_routes.py` 扩 + `core/pos_api.py` 扩信封覆盖)
  - 扩 `GET /api/me/modules`(加 `business_type` + `gateable`)。
  - 新 `PUT /api/me/onboarding`(owner · apply_preset)。
  - 新 `PUT /api/me/modules/{module_key}`(owner · toggle)。
  - `core/pos_api`:`_POS_PREFIXES` 增 `/api/me/modules`,`_POS_EXACT` 增 `/api/me/onboarding`。
  - 测试:扩 `test_modules_routes_contract.py`(3 路由契约 + app 挂载)+ 路由级 owner 守门 / 信封。
  - 真账号 E2E:各业态 onboarding → GET 校验开关组合 + 切换业态覆盖 + toggle 关再开 + 非 owner 403 + 跨租户隔离。

## P 阶段 · 前端(等 POS 前端窗口收完 · 另起)

- **PO-PP1 导航数据驱动**:`module-nav.ts` 扩认全 7 模块 + 混装组按 item 显隐 + 「可开启 →」引导 + 收编 knowledge;各 nav-item 标 `data-module`。
- **PO-PP2 注册选业态页**(屏 A):照 01 设计稿,接 `PUT /api/me/onboarding`。
- **PO-PP3 设置模块管理页**(屏 C):照 03 设计稿,接 toggle + 切换业态。
- **PO-PP4 i18n**:`i18n-data.js` 补 4 语键(04 §i18n)。
- 收尾:`npm run build` + `git add static/dist` + bump `?v=` + 真账号 E2E(每业态登录看导航)。

## 验收闸(每 PO)

守门 6 道(size/ratchet/ai-smell/prettier-crlf/lint-ui/全量 unittest) + 真账号 E2E + 跨租户隔离断言 + push 即上线前未验收不 push master。
</content>
