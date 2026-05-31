// REFACTOR-A1.3 (2026-05-22) · Vite entry · side-effect imports
//
// 把已抽出的 ES module 集中到这里 · Vite bundle 成 static/dist/main.js
// 加载顺序:home.html <script src=home.js> 同步 → <script type=module src=/static/dist/main.js> defer
// 所以 dashboard / billing 执行时 · home.js 提供的全局(t/showToast/escapeHtml/...)已就绪
//
// 后续阶段 C 持续从 home.js 抽模块 → 都进 src/home/ → 在这里 import

import './home/page-reconcile.js'; // REFACTOR-WB-C3 · 对账中心骨架运行期注入(home.html section 抽出 · 须最前 · 6 模块在其后绑定)
import './home/page-integrations.js'; // REFACTOR-WB-C3 · 集成页骨架运行期注入(home.html section 抽出 · 早于 erp-integration 等模块)
import './home/page-settings.js'; // REFACTOR-WB-C3 · 设置页骨架运行期注入(home.html section 抽出 · 须早于 recon-subtab-settings DOM-move 及所有 settings 模块)
import './home/page-automation.js'; // REFACTOR-WB-C3 · 自动化页骨架运行期注入(home.html section 抽出 · 须早于 notifications/folder-watcher/email-ingest/bank-recon 等 panel 模块 + openIntegrationDrawer DOM-move)
import './home/page-placeholders.js'; // REFACTOR-WB-C3 · 7 个静态占位页(coming-soon)骨架运行期注入(integration/templates/api-keys/vouchers/sales-invoices/receivables/cloud)
import './home/page-dashboard.js'; // REFACTOR-WB-C3 · 首页 section 骨架运行期注入(home.html 空壳 · 须在 dashboard.js 前)
import './home/ocr-results.js'; // REFACTOR-C1-home-batch1 · OCR 结果表+抽屉渲染(从 home.js 抽出 · window 桥 renderResults/openDrawer/closeDrawer)
import './home/ocr-push.js'; // REFACTOR-C1-home-batch2 · OCR 抽屉推 ERP 三件套(从 home.js 抽出 · window 桥 injectOcrPushButton · ocr-results.js openDrawer 调它)
import './home/dashboard.js';
import './home/billing.js';
import './home/test-center.js'; // REFACTOR-C1 · 测试中心(skin only)
import './home/workspace-switcher.js'; // B4 · workspace 工作模式切换器(取代旧 ClientSwitcher)
import './home/recon-center.js'; // REFACTOR-C1 · 对账中心首页(loadReconcilePage)
import './home/modal-assign-clients.js'; // REFACTOR-WB-C3 · 客户分配弹窗 inner 注入(assign-clients.js _bindOnce 用户开时绑 · 置其前)
import './home/assign-clients.js'; // REFACTOR-C1 · 客户分配 modal(openAssignClientsModal)
import './home/access-log.js'; // REFACTOR-C1 · 客户访问日志 tab(自绑 · owner only)
import './home/modal-notif-new.js'; // REFACTOR-WB-C3 · 智能提醒新建规则弹窗 inner 注入(home.html 空壳 · 须在 notifications.js 前 · _bindOnce eval 期绑)
import './home/notifications.js'; // REFACTOR-C1 · 智能提醒(_loadNotificationsPanel)
import './home/recon-batch.js'; // REFACTOR-C1 · 对账历史多选批量删(自绑 · 事件委托)
import './home/welcome-wizard.js'; // REFACTOR-C1 · 登录后欢迎向导(自绑 · 暂下架)
import './home/modal-archive-rule.js'; // REFACTOR-WB-C3 · 归档命名规则弹窗 inner 注入(home.html 空壳 · archive-settings.js 文档委托 · 置其前稳妥)
import './home/modal-archive-token.js'; // REFACTOR-WB-C3 · 归档字段编辑弹窗 inner 注入(archive-settings.js 文档委托 · 置其前稳妥)
import './home/archive-settings.js'; // REFACTOR-C1 · 归档命名规则编辑器(设置页 tab)
import './home/big-batch-progress.js'; // REFACTOR-C1 · 大批量上传进度条(_bigBatchStart/_bigBatchStop)
import './home/erp-xero.js'; // REFACTOR-C1 · Xero 连接卡片
import './home/report-templates.js'; // REFACTOR-C1 · 报表模板/统一导出弹窗(openReportModal)
import './home/folder-watcher.js'; // REFACTOR-C1 · 文件夹监听(_loadFolderWatcherPanel)
import './home/email-ingest.js'; // REFACTOR-C1 · 邮箱抓取(_loadEmailIngestPanel)
import './home/bank-recon.js'; // REFACTOR-C1 · 银行对账模块(M10)
import './home/page-clients.js'; // REFACTOR-WB-C3 · 客户页骨架运行期注入(home.html section 抽出 · 须在 clients.js 前)
import './home/clients.js'; // REFACTOR-C1 · 客户实体前端
import './home/page-exceptions.js'; // REFACTOR-WB-C3 · 异常栏页骨架运行期注入(home.html section 抽出 · 须在 exceptions.js 前)
import './home/exceptions.js'; // REFACTOR-C1 · 异常栏列表页
import './home/erp-exceptions.js'; // REFACTOR-WB-C1 · ERP 推送异常块(从 exceptions.js 抽出 · window 桥接 loadErpExceptions/_erpExcState)
import './home/topbar-avatar.js'; // REFACTOR-C1 · 顶栏三件套/头像菜单
import './home/recon-collapse.js'; // REFACTOR-C1 · 对账折叠组件
import './home/recon-subtab-settings.js'; // REFACTOR-C1 · 对账子tab+设置弹窗
import './home/excel-formula-recon.js'; // REFACTOR-C1 · Excel公式对账内测(skin-only)
import './home/gl-vat-recon.js'; // REFACTOR-C1 · GL vs 销项税报告对账
import './home/erp-mappings.js'; // REFACTOR-C1 · ERP 字段映射底座(客户/科目/税码 sub-tab)
import './home/unified-push.js'; // REFACTOR-C1 · ERP 统一推送按钮/连接器下拉
import './home/erp-map-advanced.js'; // REFACTOR-C1 · ERP 字段映射高级 sub-tab toggle
import './home/erp-onboard.js'; // REFACTOR-C1 · ERP 对接新用户引导 modal
import './home/recon-job-poll.js'; // REFACTOR-C1 · 对账异步任务前端轮询(window._reconPollJob)· 须在 bank-recon-v2 前
import './home/bank-recon-v2.js'; // REFACTOR-C1 · 银行对账 v2(Statement vs GL)· 用 window._reconPollJob
import './home/settings-general.js'; // REFACTOR-C1 · 设置→通用面板(语言 select + tz/date/number)
import './home/sidebar-nav-group.js'; // REFACTOR-C1 · 侧栏可折叠业务流分组(window.expandNavGroupForRoute)
import './home/modal-help.js';
import './home/help-modal.js'; // REFACTOR-C1 · Help modal 关闭绑定
import './home/integration-config.js'; // REFACTOR-C1 · 集成页「配置」按钮→抽屉
import './home/erp-endpoints.js'; // REFACTOR-WB-C1 · ERP 端点管理(从 erp-integration 抽出 · window 桥接 · 须在 erp-integration 前)
import './home/erp-log-detail.js'; // REFACTOR-WB-C1 · ERP 推送日志详情弹窗+复制单号(从 erp-integration 抽出 · window 桥接)
import './home/erp-integration.js'; // REFACTOR-C1 · ERP 推送日志列表(loadErpLogs/initAutomationPage · 持有 window._erpSelected · 端点/详情/批量已抽出)
import './home/erp-batch.js'; // REFACTOR-WB-C1 · ERP 推送日志批量栏/重推/删除(从 erp-integration 抽出 · 共享 window._erpSelected · 须在 erp-integration 后)
import './home/line-email-modal.js'; // REFACTOR-WB-C1 · LINE 用户补邮箱强制 modal(自包含 IIFE · 自启动)
import './home/change-password.js'; // REFACTOR-WB-C1 · 修改密码模块(设置→账户 · 自包含 IIFE)
import './home/session-heartbeat.js'; // REFACTOR-WB-C1 · Session 心跳 15s 踢设备(自包含 IIFE · window._sessionCheck)
import './home/team.js'; // REFACTOR-WB-C1 · 团队管理(老板侧:员工增删/启停/重置密码 · window.loadTeamList)
import './home/automation.js'; // REFACTOR-WB-C1 · 自动化子 tab 切换(window.switchAutomationTab)

if (typeof console !== 'undefined' && typeof console.info === 'function') {
    console.info(
        '[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings'
    );
}
