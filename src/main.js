// REFACTOR-A1.3 (2026-05-22) · Vite entry · side-effect imports
//
// 把已抽出的 ES module 集中到这里 · Vite bundle 成 static/dist/main.js
// 加载顺序:home.html <script src=home.js> 同步 → <script type=module src=/static/dist/main.js> defer
// 所以 dashboard / billing 执行时 · home.js 提供的全局(t/showToast/escapeHtml/...)已就绪
//
// 后续阶段 C 持续从 home.js 抽模块 → 都进 src/home/ → 在这里 import

import './home/dashboard.js';
import './home/billing.js';
import './home/test-center.js'; // REFACTOR-C1 · 测试中心(skin only)
import './home/workspace-switcher.js'; // B4 · workspace 工作模式切换器(取代旧 ClientSwitcher)
import './home/recon-center.js'; // REFACTOR-C1 · 对账中心首页(loadReconcilePage)
import './home/assign-clients.js'; // REFACTOR-C1 · 客户分配 modal(openAssignClientsModal)
import './home/access-log.js'; // REFACTOR-C1 · 客户访问日志 tab(自绑 · owner only)
import './home/notifications.js'; // REFACTOR-C1 · 智能提醒(_loadNotificationsPanel)
import './home/recon-batch.js'; // REFACTOR-C1 · 对账历史多选批量删(自绑 · 事件委托)
import './home/welcome-wizard.js'; // REFACTOR-C1 · 登录后欢迎向导(自绑 · 暂下架)
import './home/archive-settings.js'; // REFACTOR-C1 · 归档命名规则编辑器(设置页 tab)
import './home/big-batch-progress.js'; // REFACTOR-C1 · 大批量上传进度条(_bigBatchStart/_bigBatchStop)
import './home/erp-xero.js'; // REFACTOR-C1 · Xero 连接卡片
import './home/report-templates.js'; // REFACTOR-C1 · 报表模板/统一导出弹窗(openReportModal)
import './home/folder-watcher.js'; // REFACTOR-C1 · 文件夹监听(_loadFolderWatcherPanel)
import './home/email-ingest.js'; // REFACTOR-C1 · 邮箱抓取(_loadEmailIngestPanel)
import './home/bank-recon.js'; // REFACTOR-C1 · 银行对账模块(M10)
import './home/clients.js'; // REFACTOR-C1 · 客户实体前端
import './home/exceptions.js'; // REFACTOR-C1 · 异常栏列表页
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
import './home/help-modal.js'; // REFACTOR-C1 · Help modal 关闭绑定
import './home/integration-config.js'; // REFACTOR-C1 · 集成页「配置」按钮→抽屉
import './home/erp-integration.js'; // REFACTOR-C1 · ERP 集成页(推送日志+端点管理 · loadErpLogs/loadErpEndpoints/...)

if (typeof console !== 'undefined' && typeof console.info === 'function') {
    console.info(
        '[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings'
    );
}
