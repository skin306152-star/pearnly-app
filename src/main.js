// REFACTOR-A1.3 (2026-05-22) · Vite entry · side-effect imports
//
// 把已抽出的 ES module 集中到这里 · Vite bundle 成 static/dist/main.js
// 加载顺序:home.html <script src=home.js> 同步 → <script type=module src=/static/dist/main.js> defer
// 所以 dashboard / billing 执行时 · home.js 提供的全局(t/showToast/escapeHtml/...)已就绪
//
// 后续阶段 C 持续从 home.js 抽模块 → 都进 src/home/ → 在这里 import

import './home/state.js'; // REFACTOR-C1-home-batch9g2 · 应用引导/全局状态(错误拦截IIFE + i18n总线 + window.* 状态 init)· 【必第 1 个】早于所有 sibling · 取代已删的 home.js
import './home/core.js'; // REFACTOR-C1-home-batch9f · 真核心叶子层(t/escapeHtml/svgIcon/鉴权API🔴/_showSessionRevokedModal🔴/getMax*)· 【必第 1 个】保证 sibling 模块 eval 期 window.t/apiGet 等已就绪
import './home/format-date.js'; // 共享日期格式化(formatDate/历法偏好)· window 桥 · 须早于消费方
import './home/ui-templates.js'; // 6 页面模板骨架(uiTpl.*)· window 桥 · 供新屏/迁移屏对号套用
import './home/app-shell-html.js'; // REFACTOR-WB-C3 · app shell(顶栏 .topbar + 侧栏 #sidebar)inner 注入(home.html 空壳 · ⚠️须在 core-boot 前·其 bootstrap eval 期 routeTo→querySelectorAll(.nav-item) + sidebar-nav.js eval 期 getElementById(sidebar-toggle) 无守卫;漏则 boot 崩·全 app 导航瘫)
import './home/workspace-gate-boot.js'; // 套账硬门早期壳 · 先于 core-boot 注册,避免登录后业务页先闪出
import './home/core-boot.js'; // REFACTOR-C1-home-batch9f · 真核心编排+引导(applyLang/setupDropdown/routeTo/loadAll/render助手 + bootstrap)· 【必第 2 个】紧随 core.js · bootstrap 尾部自执行 · 先于其余 sibling
import './home/boot-ui-extras.js'; // REFACTOR-WB-modularize · 顶栏工作台名 + 断网横幅(从 core-boot 拆出 · window 桥 · 须早于 misc-bindings 的 installNetworkBanner 调用)
import './home/sidebar-nav.js'; // REFACTOR-C1-home-batch9g1 · 侧栏折叠/汉堡/遮罩 + hashchange + nav-item 点击(从 home.js 抽出)
import './home/integration-drawer.js'; // REFACTOR-C1-home-batch9g1 · 集成顶tab + 集成配置抽屉(window.openIntegrationDrawer 等 · integration-config/page-automation 用)
import './home/settings-bind.js'; // REFACTOR-C1-home-batch9g1 · 设置页 tab/保存按钮绑定(从 home.js 抽出)
import './home/drawer-events.js'; // REFACTOR-C1-home-batch9g1 · 识别抽屉事件委托/关闭/ESC(从 home.js 抽出)
import './home/misc-bindings.js'; // REFACTOR-C1-home-batch9g1 · 杂项绑定(data-upgrade/自定义模板/断网横幅装载)
import './home/confirm-modals-html.js'; // REFACTOR-WB-C3 · 两个全局确认弹窗 inner 注入(home.html 空壳 · 须在 pearnly-confirm.js/confirm-modal.js 前 · 二者均 on-demand 调用时读·带守卫)
import './home/pearnly-confirm.js'; // REFACTOR-C1-home-batch9g1 · 全局确认弹窗 window.pearnlyConfirm(从 home.js 抽出)
import './home/page-reconcile.js'; // REFACTOR-WB-C3 · 对账中心骨架运行期注入(home.html section 抽出 · 须最前 · 6 模块在其后绑定)
import './home/page-integrations.js'; // REFACTOR-WB-C3 · 集成页骨架运行期注入(home.html section 抽出 · 早于 erp-integration 等模块)
import './home/page-settings.js'; // REFACTOR-WB-C3 · 设置页骨架运行期注入(home.html section 抽出 · 须早于 recon-subtab-settings DOM-move 及所有 settings 模块)
import './home/page-automation.js'; // REFACTOR-WB-C3 · 自动化页骨架运行期注入(home.html section 抽出 · 须早于 notifications/folder-watcher/email-ingest/bank-recon 等 panel 模块 + openIntegrationDrawer DOM-move)
import './home/page-placeholders.js'; // REFACTOR-WB-C3 · 7 个静态占位页(coming-soon)骨架运行期注入(integration/templates/api-keys/vouchers/sales-invoices/receivables/cloud)
import './home/page-dashboard.js'; // REFACTOR-WB-C3 · 首页 section 骨架运行期注入(home.html 空壳 · 须在 dashboard.js 前)
import './home/toast.js'; // REFACTOR-C1-home-batch6 · Toast/提示条/错误人话化(从 home.js 抽出 · window 桥 showToast/showAlert/hideAlerts/humanizeError/_humanizeBackendError · 被 ~38 模块裸调)
import './home/with-loading.js'; // 丝滑专项 · 按钮即时反馈 withLoading(btn, fn)(window 桥 · 被各事件 handler 裸调)
import './home/confirm-modal.js'; // REFACTOR-C1-home-batch9e · 自定义确认对话框(从 home.js 抽出 · window 桥 showConfirm · 被 ~18 模块裸调 · 早 import 防 eval 期未就绪)
import './home/settings-core.js'; // REFACTOR-C1-home-batch7 · 设置页/个人资料/公司信息(从 home.js 抽出 · window 桥 switchSettingsTab/fillSettingsForms/saveProfile/saveCompany/renderSettings · home.js IIFE+引导期裸调)
import './home/permissions.js'; // REFACTOR-C1-home-batch8 · 用户角色原子判断(从 home.js 抽出 · window 桥 isSuperAdmin/isOwner/isEmployee/isTrial/isLifetime/shouldHideMoney/canManageTeam/canManageApiKey · 全局唯一来源 · 被多模块裸调)
import './home/layout.js'; // REFACTOR-C1-home-batch8 · 顶栏配额chip/配额预警banner/sidebar权限显隐(从 home.js 抽出 · window 桥 renderQuotaBanner/applySidebarVisibility/renderInfoBar · 依赖 permissions.js)
import './home/recon-drawer.js'; // REFACTOR-C1-home-batch9a · 泰国RD税务API核验/同步(从 home.js 抽出 · window 桥 callRdVerify/callRdSync · drawer-body 事件代理裸调)
import './home/ocr-fields.js'; // REFACTOR-C1-home-batch9b · OCR多页字段合并+抽屉字段编辑(从 home.js 抽出 · window 桥 mergeFields/onFieldEdit/updateDrawerEditCount · ocr模块+recon-drawer裸调)
import './home/line-panel.js'; // REFACTOR-C1-home-batch9d · LINE Bot 绑定面板 IIFE(🔴高敏·从 home.js 抽出 · import 自执行暴露 window._loadLineBotPanel · 集成抽屉/automation.js 触发)
import './home/ocr-results.js'; // REFACTOR-C1-home-batch1 · OCR 结果表+抽屉渲染(从 home.js 抽出 · window 桥 renderResults/openDrawer/closeDrawer)
import './home/ocr-push.js'; // REFACTOR-C1-home-batch2 · OCR 抽屉推 ERP 三件套(从 home.js 抽出 · window 桥 injectOcrPushButton · ocr-results.js openDrawer 调它)
import './home/page-history.js'; // REFACTOR-WB-C3 · 历史页骨架运行期注入(home.html section 抽出 · 须在 history-list.js 前 · 顶层自举/bootstrap 守卫调用都在其后)
import './home/history-list.js'; // REFACTOR-C1-home-batch4 · 发票记录页列表侧(从 home.js 抽出 · 桥 loadHistoryPage 等 · _historyState 共享态留 home.js)
import './home/history-drawer.js'; // REFACTOR-C1-home-batch4 · 发票记录页抽屉+菜单+事件绑定(从 home.js 抽出 · 桥 openHistoryDrawer · 与 history-list.js 互调)
import './home/history-drawer-tabs.js'; // 销项重做 · 抽屉重排 4-tab+汇总条(history 模式 · 桥 historizeDrawer · openHistoryDrawer 调)
import './home/dms-intake.js'; // 录入工作台(发票OCR + 身份证→DMS)· window.loadDmsIntake(invoice/core/confirm 子模块经它 import)
import './home/dashboard.js';
import './home/billing.js';
import './home/workspace-switcher.js'; // B4 · workspace 工作模式切换器(取代旧 ClientSwitcher)
import './home/access-log.js'; // REFACTOR-C1 · 客户访问日志 tab(自绑 · owner only)
import './home/modal-notif-new.js'; // REFACTOR-WB-C3 · 智能提醒新建规则弹窗 inner 注入(home.html 空壳 · 须在 notifications.js 前 · _bindOnce eval 期绑)
import './home/notifications.js'; // REFACTOR-C1 · 智能提醒(_loadNotificationsPanel)
import './home/welcome-wizard.js'; // REFACTOR-C1 · 登录后欢迎向导(自绑 · 暂下架)
import './home/modal-archive-rule.js'; // REFACTOR-WB-C3 · 归档命名规则弹窗 inner 注入(home.html 空壳 · archive-settings.js 文档委托 · 置其前稳妥)
import './home/modal-archive-token.js'; // REFACTOR-WB-C3 · 归档字段编辑弹窗 inner 注入(archive-settings.js 文档委托 · 置其前稳妥)
import './home/archive-settings.js'; // REFACTOR-C1 · 归档命名规则编辑器(设置页 tab)
import './home/settings-panels.js'; // REFACTOR-WB-modularize · 设置页联系我们 + 首选项面板(从 archive-settings 拆出)
import './home/big-batch-progress.js'; // REFACTOR-C1 · 大批量上传进度条(_bigBatchStart/_bigBatchStop)
import './home/erp-global-push-mode.js'; // 账户级 ERP 自动处理方式 select(adapter 无关)
import './home/erp-mrerp-dms-connect.js'; // DMS集成 · MR.ERP DMS 汽车销售连接卡+向导(渲染 #erp-connect-cards · adapter=mrerp_dms)
import './home/report-templates.js'; // REFACTOR-C1 · 报表模板/统一导出弹窗(openReportModal)
import './home/folder-watcher.js'; // REFACTOR-C1 · 文件夹监听(_loadFolderWatcherPanel)
import './home/chrome-banner.js'; // REFACTOR-WB-modularize · 非 Chromium 浏览器提示 banner(从 folder-watcher 拆出 · 自触发 + window._refreshChromeBanner)
import './home/email-modal-html.js'; // REFACTOR-WB-C3 · 邮箱抓取绑定弹窗 inner 注入(home.html 空壳 · 须在 email-ingest.js 前 · wire() eval 期带守卫绑 email-modal-*·非高敏·≠line-email-modal)
import './home/email-ingest.js'; // REFACTOR-C1 · 邮箱抓取(_loadEmailIngestPanel)
import './home/bank-cand-drawer-html.js'; // REFACTOR-WB-C3 · 银行对账候选匹配抽屉 inner 注入(home.html 空壳 · 须在 bank-recon.js 前 · load() 按需绑定 [data-bank-cand-close]/btn-bank-cand-ignore)
import './home/bank-client-picker-html.js'; // REFACTOR-WB-C3 · 银行对账 session 客户绑定弹窗 inner 注入(home.html 空壳 · 须在 bank-recon.js 前 · bindEvents 按需绑 [data-bank-client-picker-close]/btn-bank-client-picker-save)
import './home/bank-recon.js'; // REFACTOR-C1 · 银行对账模块(M10)
import './home/page-clients.js'; // REFACTOR-WB-C3 · 客户页骨架运行期注入(home.html section 抽出 · 须在 clients.js 前)
import './home/modal-client-edit.js'; // REFACTOR-WB-C3 · 客户/账套主体编辑弹窗 inner 注入(home.html 两空壳 · 须在 clients.js 前 · clients.js DOMContentLoaded 守卫绑定 client-modal-*/wsclient-modal-*)
import './home/clients.js'; // REFACTOR-C1 · 客户实体前端
import './home/client-assign.js'; // 用户引导闭环 · 客户管理「分派会计」弹窗(window.openClientAssign · 复用 /api/team/members + scope)
import './home/page-exceptions.js'; // REFACTOR-WB-C3 · 异常栏页骨架运行期注入(home.html section 抽出 · 须在 exceptions.js 前)
import './home/exceptions.js'; // REFACTOR-C1 · 异常栏列表页
import './home/erp-exceptions.js'; // REFACTOR-WB-C1 · ERP 推送异常块(从 exceptions.js 抽出 · window 桥接 loadErpExceptions/_erpExcState)
import './home/erp-exceptions-edit.js'; // REFACTOR-WB-modularize · ERP 异常单条编辑弹窗(从 erp-exceptions 拆出 · window._erpExcOpenEdit)
import './home/rules-settings.js'; // KNOWLEDGE · 客户风险规矩设置弹窗(window.openRulesSettings · 异常页「规矩设置」按钮调 · flag-gated 后端)
import './home/page-knowledge.js'; // KNOWLEDGE · 客户知识中心页骨架注入(home.html #page-knowledge 空壳 · 须在 knowledge-center 前)
import './home/knowledge-center.js'; // KNOWLEDGE · 知识中心页逻辑(tab 切换 + 账套上下文 + 探针门控侧栏入口 · window.loadKnowledgePage)
import './home/knowledge-documents.js'; // KNOWLEDGE · 文档库 tab(上传/列表/删除 · window._kbRenderDocs · 须在 knowledge-center 后)
import './home/knowledge-sources.js'; // KNOWLEDGE · 来源出处弹窗(.modal · window._kbOpenSource · 须在 knowledge-ask 前)
import './home/knowledge-ask.js'; // KNOWLEDGE · 问答 tab + 可复用问答接线(window._kbRenderAsk/_kbWireAsk · 接 /api/knowledge/ask)
import './home/knowledge-fab.js'; // KNOWLEDGE · 悬浮猫问答助手(拖拽吸边+卖萌·复用 _kbWireAsk·问答 tab 开关控显隐·须在 knowledge-ask 后)
import './home/knowledge-info.js'; // KNOWLEDGE · 功能介绍+费用弹窗(.modal · window._kbOpenInfo · 页头按钮触发)
import './home/sales-common.js'; // 销项 PO-10 · 共享叶子(类型/格式化/带鉴权 fetch · 无副作用)
import './home/sales-detail.js'; // 销项 PO-10 · 发票详情弹窗(window.openSalesDetail · #sales-detail-mask)
import './home/sales-workbench.js'; // 销项 PO-10 · 发票工作台(window.loadSalesWorkbench · 接 GET /api/sales/documents)
import './home/sales-products.js'; // 销项 PO-10 · 商品管理(主数据 · window.loadSalesProducts · CRUD+import)
import './home/sales-account.js'; // 销项 PO-10 · 账套·开票资料(window.loadSalesAccount · 卖方+品牌+模板 · PUT sellers)
import './home/sales-settings.js'; // 销项 PO-10 · 开票设置弹窗(window.openSalesSettings · GET/PUT /api/sales/settings · §M7)
import './home/sales-wizard.js'; // 销项 PO-10 · 开票向导(window.openSalesWizard · 5步 · 接 sellers/products/rd/create+issue · 自含计算/预览/i18n/io)
import './home/module-nav.js'; // POS PO-A1 配套 · 导航按 GET /api/me/modules 显隐(收银业务组默认隐藏 · inventory/pos 开才显)
import './home/inventory.js'; // POS PO-A4 · 库存后台主页(屏7 · window.loadInventoryPage · 接 GET /api/inventory/stock · 四态)
import './home/inventory-modals.js'; // POS PO-A4 · 入库/盘点弹窗(window.openInventoryIn/openInventoryCount · POST /api/inventory/in|count · .modal)
import './home/pos-onboarding.js'; // POS PO-B1 · 开通收银(屏8 · window.loadPosOnboardingPage · PUT /api/pos/admin/onboarding · 选业态/建收银员)
import './home/onboarding-business.js'; // 平台业态套餐 PO-PP2 · 业态选择器弹窗(window.openBusinessPicker · PUT /api/me/onboarding · 可开启功能/切换业态)
import './home/onboarding-flow.js'; // 用户引导闭环 · 注册后向导(window.startOnboardingFlow · 业态→主体→账务→完成清单 · 复用 onboarding-business/subject-create)
import './home/company-profile.js'; // 用户引导闭环 · 公司资料页(window.loadCompanyProfile · GET/PATCH /api/workspace/clients/{id} · 行内编辑)
import './home/workspace-gate.js'; // 套账硬门 · 每次登录必选套账(window.showWorkspaceGate/enforceWorkspaceGate · 0套账→新建专屏 · 不可绕开)
import './home/module-settings.js'; // 平台业态套餐 PO-PP3 · 设置·业务/模块页(window.loadModuleSettings · 7 toggle PUT /api/me/modules/{key} · bizbar 切换业态)
import './home/pos-tables.js'; // 餐厅 POS · 桌台管理(window.openPosTables · 区域/桌台 CRUD · /api/pos/admin/restaurant/* · owner·餐厅·弹窗)
import './home/pos-payment-settings.js'; // POS · 收款设置(window.openPosPayment · 现金/PromptPay/刷卡+服务费/VAT · owner·弹窗)
import './home/sales-report.js'; // POS 屏9 · 销售报表(window.loadSalesReport · GET /api/pos/admin/report · KPI/图/榜 · 四态)
import './home/pos-cashiers.js'; // POS · 收银员管理(window.loadPosCashiers · GET/POST/PUT /api/pos/admin/cashiers · owner · 加人/改名换色/重设PIN/启停)
// 商户采购(进项)Phase 1 · 屏1 主屏 / 屏10 录入 / 屏6 详情 / 屏7-9+3 弹窗 / 屏4 供应商 / 屏5 设置(docs/purchasing)
// mock 兜底先行(purchase-mock)· 后端 /api/purchase/* 上线自动切真 · 全屏照搬设计稿 Pearnly_采购_UI预览/。
import './home/purchase-list.js'; // 屏1 采购/进项主屏(window.loadPurchaseList · 桌面表格/手机卡片 + KPI + chip + 四态)
import './home/purchase-form.js'; // 屏10 录入(window.loadPurchaseForm/openPurchaseForm · 商品服务联动 WHT · 即时重算)
import './home/purchase-detail.js'; // 屏6 详情(window.loadPurchaseDetail/openPurchaseDetail · 记付款/作废/编辑)
import './home/purchase-modals.js'; // 屏7 记付款 / 屏8 商品匹配 / 屏9 供应商选择器 / 屏3 LINE 说明(桌面居中/手机底抽屉)
import './home/purchase-suppliers.js'; // 屏4 供应商管理(window.loadPurchaseSuppliers · CRUD · 套账隔离)
import './home/purchase-settings.js'; // 屏5 采购设置(window.loadPurchaseSettings · 默认VAT/进货入库/重复票拦/两级科目/账期/审批)
import './home/purchase-google.js'; // 集成中心 Google Drive/Sheets 授权卡(window.loadIntegrationGoogle/highlightGoogleCard · 外流归档 OAuth)
import './home/purchase-export.js'; // 外流收拢面板(window.openPurchaseExport · Excel 免授权 / Drive 归档 / Sheet 同步 · 412 未连跳集成中心)
import './home/purchase-capture.js'; // 采集屏(window.loadPurchaseCapture · 记一笔采购 · 桌面上传/手工 · 手机拍照/相册/文件/手工 · 智能入口分流)
import './home/purchase-liff.js'; // Phase 3 LIFF 复核屏入口(/home?liff=purchase&doc= → 签 token → 开 purchase-form · 真验留用户配 LIFF ID)
// 自动做账 Phase 2 · 屏1 主屏(路由 vouchers)/ 屏2 逐笔审 / 屏3 科目表 / 屏5 设置 / 屏4 出账本(docs/accounting)
import './home/acct-list.js'; // 屏1 主屏(window.loadAcctList · 北极星+待审行动卡+凭证列表行内展开借贷)
import './home/acct-review.js'; // 屏2 逐笔审(window.loadAcctReview · 队列逐笔 · 确认/改科目/跳过 · 记忆)
import './home/acct-accounts.js'; // 屏3 科目表(window.loadAcctAccounts · 泰标预置 · 类型筛/搜 · 加改=.modal)
import './home/acct-settings.js'; // 屏5 做账设置(window.loadAcctSettings · 自动过账粒度+门槛+映射+可见规则)
import './home/acct-books.js'; // 屏4 出账本/报税包(window.loadAcctBooks · 月末结账+账本/VAT/WHT/财报 PDF+打包)
import './home/acct-modals.js'; // 共享弹窗(改科目选择器/加改科目 · 站内 .modal 禁原生 prompt)
// 银行对账 + 手工凭证(docs/accounting/bank-recon-mj · /api/accounting/bank/* · 交互基准=03-交互原型)
import './home/acct-bank.js'; // 银行对账(window.loadAcctBank · 导入/匹配/收割/差额门控 · 做账组排出账本前)
import './home/acct-bank-modals.js'; // 银行对账弹窗(组合匹配/改科目/新建卡 · 站内 .modal)
import './home/acct-manual.js'; // 手工凭证(window.loadAcctManual · 配平门控+全键盘+模板 · 做账主屏按钮入)
// 自动报税 Phase 3 · 屏1 报税中心 / 屏2 PP30 复核 / 屏3 PND 复核 / 屏4 报税设置(docs/tax-filing · /api/tax/*)
import './home/tax-center.js'; // 屏1 报税中心(window.loadTaxCenter · 北极星本月要交税 + 最近截止行动卡 + 税种列表)
import './home/tax-pp30.js'; // 屏2 PP30 复核(window.loadTaxPp30 · 销−进可追溯 + 体检 + 提交/导出)
import './home/tax-pnd.js'; // 屏3 PND 复核(window.loadTaxPnd · PND53/PND3 tab + 逐笔 + 扣缴凭证态 + 缺税号拦)
import './home/tax-settings.js'; // 屏4 报税设置(window.loadTaxSettings · VAT登记/总分公司/提醒/0税额也报)
import './home/cmdk-mask-html.js'; // REFACTOR-WB-C3 · 命令面板(Cmd+K · #cmdk-mask)inner 注入(home.html 空壳 · 须在 topbar-avatar.js 前 · _initCmdk DOMContentLoaded 带守卫绑 cmdk-input/body/esc-btn · openCmdk 按需)
import './home/topbar-avatar.js'; // REFACTOR-C1 · 顶栏三件套/头像菜单
import './home/recon-subtab-settings.js'; // REFACTOR-C1 · 对账子tab+设置弹窗
import './home/erp-mappings.js'; // REFACTOR-C1 · ERP 字段映射底座(客户/科目/税码 sub-tab)
import './home/unified-push.js'; // REFACTOR-C1 · ERP 统一推送按钮/连接器下拉
import './home/erp-map-advanced.js'; // REFACTOR-C1 · ERP 字段映射高级 sub-tab toggle
import './home/erp-onboard.js'; // REFACTOR-C1 · ERP 对接新用户引导 modal
import './home/recon-job-poll.js'; // REFACTOR-C1 · 对账异步任务前端轮询(window._reconPollJob)· 须在 bank-recon-v2 前
import './home/recon-center-x.js'; // 2026-06-14 · 对账中心重设计(统一三类型 · 覆盖旧 loadReconcilePage · 须在 recon-center/recon-job-poll/bank-recon-v2 之后)
import './home/settings-general.js'; // REFACTOR-C1 · 设置→通用面板(语言 select + tz/date/number)
import './home/sidebar-nav-group.js'; // REFACTOR-C1 · 侧栏可折叠业务流分组(window.expandNavGroupForRoute)
import './home/modal-help.js';
import './home/help-modal.js'; // REFACTOR-C1 · Help modal 关闭绑定
import './home/integration-config.js'; // REFACTOR-C1 · 集成页「配置」按钮→抽屉
import './home/erp-endpoints.js'; // REFACTOR-WB-C1 · ERP 端点管理(从 erp-integration 抽出 · window 桥接 · 须在 erp-integration 前)
import './home/erp-log-detail.js'; // REFACTOR-WB-C1 · ERP 推送日志详情弹窗+复制单号(从 erp-integration 抽出 · window 桥接)
import './home/endpoint-modal-html.js'; // REFACTOR-WB-C3 · ERP 端点配置弹窗 inner 注入(home.html 空壳 · ⚠️须在 erp-integration.js 前 · 其 initAutomationPage IIFE eval 期无守卫绑 endpoint-modal-close/btn-ep-*/ep-url)
import './home/erp-log-card.js'; // 销项重做 · 推送日志卡片渲染(从 erp-integration 表格行抽出 · 桥 buildErpLogCard)
import './home/erp-integration.js'; // REFACTOR-C1 · ERP 推送日志列表(loadErpLogs/initAutomationPage · 持有 window._erpSelected · 端点/详情/批量已抽出)
import './home/erp-batch.js'; // REFACTOR-WB-C1 · ERP 推送日志批量栏/重推/删除(从 erp-integration 抽出 · 共享 window._erpSelected · 须在 erp-integration 后)
import './home/line-email-modal.js'; // REFACTOR-WB-C1 · LINE 用户补邮箱强制 modal(自包含 IIFE · 自启动)
import './home/change-password.js'; // REFACTOR-WB-C1 · 修改密码模块(设置→账户 · 自包含 IIFE)
import './home/session-heartbeat.js'; // REFACTOR-WB-C1 · Session 心跳 15s 踢设备(自包含 IIFE · window._sessionCheck)
import './home/automation.js'; // REFACTOR-WB-C1 · 自动化子 tab 切换(window.switchAutomationTab)

if (typeof console !== 'undefined' && typeof console.info === 'function') {
    console.info(
        '[pearnly] vite bundle loaded · dashboard + billing + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings'
    );
}
