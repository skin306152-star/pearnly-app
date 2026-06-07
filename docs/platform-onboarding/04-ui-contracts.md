# 04 · 3 屏 UI 契约(图纸 · 照桌面设计稿)

> 设计稿(已拍板):桌面 `Pearnly_业态套餐_UI预览/{01-注册业态选择,02-各业态导航对比,03-设置-业务模块}.html`。
> 铁律:视觉照搬(令牌逐字搬·作用域隔离防跨屏同名类)· 双语标注 → i18n 单语(4 语字典)· 信封 `body.ok→data` · 失败 `posErrMsg`/统一兜底 · 四态 UI。
> **本窗口只出契约,不实现前端**(撞 POS 屏8 文件,P 阶段做)。

## 屏 A · 注册选业态(01-注册业态选择.html)

- **触发**:新注册租户首次进入(owner)。老租户**不触发**(D1)。入口判据:`GET /api/me/modules` 返 `business_type == null` 且为新租户。
- **布局**:左 = 6 张业态卡(firm/retail/pharmacy/restaurant/service/b2b · 选中 `.type.on` 蓝边);右 = sticky 预览面板「将为你开启」,实时渲染底座(常开灰)+ 业务模块(开/未开)。
- **数据驱动**:前端镜像 02 的预设表(`PRESETS`);点卡片刷新右侧。底文「不确定?先全部开启,以后再调」= 调 onboarding 时可传一个「全开」语义(或跳过 onboarding 走 legacy 全开)。
- **提交**:「进入 Pearnly」→ `PUT /api/me/onboarding {business_type}` → 成功后 `applyModuleNav()` 重渲导航 + 路由进首页。
- **四态**:加载(骨架)/ 正常 / 提交中(按钮 disabled)/ 失败(`posErrMsg` toast,不离页)。

## 屏 B · 导航随业态显隐(02-各业态导航对比.html)

- 这是**效果说明稿**,非独立页面 —— 落地 = `module-nav.ts` 数据驱动改造(P 阶段):
  - 每个 nav-item / 折叠组标 `data-module="<key>"`;按 `GET /api/me/modules` 显隐。
  - 「销项管理」混装组(sales+recon+receivable):**按 item 粒度**显隐,整组隐藏仅当三模块全关(见 01 §四)。
  - 未开模块(owner 可见)显「可开启 →」引导项(`.ni.enroll`),点击 → onboarding/toggle 开通,不彻底藏(原则 #3)。
  - 收编 knowledge:废 `kbProbe` 门控分支,改读 modules(P 阶段)。

## 屏 C · 设置 · 业务/模块(03-设置-业务模块.html)

- **位置**:设置页新增「业务 / 模块」区(owner 可见)。
- **bizbar**:显「当前业态」(`business_type` 回显中文)+「切换业态」按钮(弹屏 A 同款选择 → `PUT /api/me/onboarding`)。
- **底座卡**:商品/客户/工作台/AI 录入 —— `.mod.lock` 常开禁关(纯展示,无接口)。
- **业务模块卡**:7 个 toggle,每个 `PUT /api/me/modules/{key} {enabled}`。关 → tag 显「可开启」、导航收起;数据不删(D2)。乐观更新 + 失败回滚 + `posErrMsg`。
- **四态**:加载 / 正常 / toggle 中(开关禁用)/ 失败(回滚 + toast)。

## i18n 键(P 阶段补 · 4 语)

`onb.title`(你做什么生意?)· `onb.sub` · `biz.firm/retail/pharmacy/restaurant/service/b2b`(业态名+副标)· `mod.sales/expense/recon/inventory/pos/receivable/knowledge`(模块名+一句话)· `mod.base_locked` · `mod.enrollable`(可开启)· `onb.enter`(进入 Pearnly)· `set.switch_biz`(切换业态)· `set.module_section`(业务/模块)· 错误码 `platform.*`。
</content>
