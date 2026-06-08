# 01 · 模块门控位置地图(勘测产出 · 只读)

> ✅ 状态确认(2026-06-08 复核,本表仍准确):后端门控 `assert_module_enabled` 经代码核查【只加在 pos / inventory】
> (routes/pos_*、inventory_*);本表所列 `sales`/`expense`/`recon`/`receivable` 仍为 ❌无后端门控、`knowledge` 仍为独立探针——
> 全部属实,是【尚未施工】的独立 workstream(注册选业态/模块开关切换那一套已上线,但"给老模块补后端门控"这摊没做)。
> 测试含义:关掉 sales/recon 等只会在前端导航隐藏,直接打后端 API 仍可用——这是当前已知范围,不是 bug。

> 本窗口 2026-06-07 勘测。目的:把 7 个可开关模块「导航在哪、路由叫什么、后端入口在哪、当前怎么门控」一次说清,作为「导航数据驱动改造」(P 阶段前端)+「后端 gating 全覆盖」的施工底图。**纯事实勘测,不含决策**(决策见 02+)。

## 一、底座 vs 可开关(对齐 PRODUCT_VISION_MODULAR + 00-plan)

- **底座(常开 · 不进 tenant_modules · 不门控)**:首页 dashboard · 商品 sales-products · 客户 clients · 异常栏 exceptions · 集成 integrations · 设置 settings · AI 录入/上传 · 多语言。
- **可开关(7 个 · tenant_modules.module_key)**:
  `sales`(开票/销项)· `expense`(进项)· `recon`(对账)· `inventory`(库存)· `pos`(收银)· `receivable`(应收)· `knowledge`(知识库)。

## 二、模块 → 导航元素 → 路由 → 后端入口(逐模块)

导航源:`src/home/app-shell-html.ts`(SIDEBAR_HTML)。路由源:`src/home/core-boot.ts`(`VALID_ROUTES` + `routeTo`)。

| module_key | 侧栏导航元素(app-shell-html.ts) | 路由 key(core-boot) | 后端入口 | 当前门控 |
|---|---|---|---|---|
| `sales` | 「销项管理」组内:`data-route="ocr"`(上传识别)、`data-route="history"`(单据记录)、`.nav-sales-head`(销售发票)+ `data-route="sales-invoices"`、`data-route="sales-account"` | `ocr` `history` `sales-invoices` `sales-account` | `routes/sales_routes.py` `routes/sales_seller_routes.py` `routes/sales_send_routes.py` `services/sales/*` | ❌ 无(对所有租户默认全开) |
| `recon` | 「销项管理」组内:`data-route="reconcile"`(对账中心) | `reconcile` | `routes/recon_routes.py` `routes/recon_jobs_routes.py` | ❌ 无 |
| `receivable` | 「销项管理」组内:`data-route="receivables"`(应收追踪) | `receivables` | (前端页 · 后端待接) | ❌ 无 |
| `expense` | 「进项管理」组 `data-collapsible="expense"`:`data-route="vouchers"`(凭证中心) | `vouchers` | (进项录入 · 复用 OCR/单据栈) | ❌ 无 |
| `inventory` | 「收银业务」组 `#nav-group-pos` 内:`data-route="inventory"`(库存) | `inventory` | `routes/inventory_routes.py` `routes/inventory_report_routes.py` `services/inventory/*` | ✅ `assert_module_enabled(cur,tid,"inventory")` + 前端 `module-nav.ts` |
| `pos` | 「收银业务」组 `#nav-group-pos`:`#nav-pos-onboard`(开通收银台)、`data-route="sales-report"`(销售报表)、`#nav-pos-switch data-href="/pos"`(切到收银台) | `pos-onboarding`(主程序内)+ `/pos`(独立 SPA) | `routes/pos_*` `services/pos/*` | ✅ `assert_module_enabled` + 前端 `module-nav.ts` |
| `knowledge` | 主数据区下:`#nav-knowledge data-route="knowledge"`(客户知识) | `knowledge` | `routes/`(知识库)· 前端 `knowledge-center.ts` | ⚠️ 独立**探针门控**(`kbProbe()`,**不走** `/api/me/modules`) |

## 三、当前两套门控机制(现状 · 不统一)

1. **POS/库存(inventory/pos)**:后端 `core/pos_api.assert_module_enabled` 逐路由断言;前端 `src/home/module-nav.ts` 调 `GET /api/me/modules`,按 `inventory`/`pos` 开关显隐「收银业务」整组 + 组内项。这是**目标范式**。
2. **知识库(knowledge)**:前端 `knowledge-center.ts` 用独立 `kbProbe()` 探针,开了才 `display=''` 显示 `#nav-knowledge`。**与 /api/me/modules 平行,未统一**。
3. **sales/expense/recon/receivable**:**完全无门控**——导航硬编码常显,后端不断言。这是「最大工作量」缺口。

## 四、关键结构难点(留给 P 阶段前端)

- **「销项管理」折叠组是混装组**:同一 `data-collapsible="sales"` 组里混了 `sales`(ocr/history/销售发票)+ `recon`(reconcile)+ `receivable`(receivables)三个模块的项。
  → 数据驱动显隐必须**按 nav-item 粒度**标 `module_key`,而非按组;**整组隐藏**仅当组内所有模块项都关。
- **`module-nav.ts` 现仅认 inventory/pos**:P 阶段要扩成认全部 7 个 + knowledge 收编进 `/api/me/modules`(废 kbProbe 门控分支或令其改读 modules)。
- **POS 引导项耦合**:`module-nav.ts` 的 `showOnboard = !anyOn && owner` 是 POS 专属逻辑;`pos` 模块「已开关但未开通(无终端/收银员)」需要区分 enabled-flag 与 provisioned-state(见 03 决策 D3)。

## 五、本窗口可安全改的文件(不碰 POS 前端文件)

- ✅ 后端:`services/modules/store.py`(扩)、`services/modules/presets.py`(新)、`routes/modules_routes.py`(扩)、`core/pos_api.py`(扩门控覆盖)、`app.py`(注册不变/微调)、`tests/unit/*`、`alembic/`(如需)。
- ⛔ **P 阶段(等 POS 前端窗口收完再做)**:`src/home/app-shell-html.ts`、`src/home/core-boot.ts`、`src/home/module-nav.ts`、`static/dist/i18n-data.js` — 与 POS 屏8 前端窗口同批,会撞。
</content>
</invoke>
