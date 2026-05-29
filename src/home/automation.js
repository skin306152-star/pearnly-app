// ============================================================
// REFACTOR-WB-C1 (2026-05-29) · 自动化子 tab 切换 switchAutomationTab 从 home.js 抽出为 ES module
//
// 来源:home.js 自动化页(v0.6.1)。switchAutomationTab 切 .auto-nav-item / .auto-panel 并按 tab
//   懒加载对应面板(window._loadEmailIngestPanel / _loadBankReconPanel / _loadLineBotPanel /
//   _loadNotificationsPanel / _loadFolderWatcherPanel · 均已抽出为 module 经 window 暴露)。
// 入口 window.switchAutomationTab:erp-integration.js(.auto-nav-item 点击委托)/ folder-watcher.js /
//   email-ingest.js 经全局 bare 调 · 抽成 defer module 后仍安全(用户点 tab 远晚于模块加载)。
// 只用 document + window.* · 无 home.js 裸全局依赖。verbatim 搬迁 · 0 改逻辑(仅 prettier)。
// 同 PR 删 home.js 死码 loadAutomationPage(automation route 不在 VALID_ROUTES · 全仓 0 外部调用点)。
// ============================================================

function switchAutomationTab(tabKey) {
    document.querySelectorAll('.auto-nav-item').forEach((item) => {
        item.classList.toggle('active', item.dataset.autoTab === tabKey);
    });
    document.querySelectorAll('.auto-panel').forEach((panel) => {
        panel.classList.toggle('active', panel.dataset.autoPanel === tabKey);
    });
    // v0.17 · M6 · 邮箱抓取 tab 首次进入时拉数据
    if (tabKey === 'email' && typeof window._loadEmailIngestPanel === 'function') {
        window._loadEmailIngestPanel();
        // v95 · 进入邮箱 tab · 启动 30s 自动刷新日志
        if (typeof window._startEmailLogAutoRefresh === 'function') {
            window._startEmailLogAutoRefresh();
        }
    } else if (typeof window._stopEmailLogAutoRefresh === 'function') {
        // 离开邮箱 tab · 停止自动刷新
        window._stopEmailLogAutoRefresh();
    }
    // v0.18 · M10 · 银行对账 tab 首次进入时拉数据
    if (tabKey === 'bank' && typeof window._loadBankReconPanel === 'function') {
        window._loadBankReconPanel();
    }
    // v0.19 · T1 · LINE Bot tab 首次进入时拉数据
    if (tabKey === 'linebot' && typeof window._loadLineBotPanel === 'function') {
        window._loadLineBotPanel();
    }
    // v118.22.2 · 智能提醒 tab 首次进入时拉数据
    if (tabKey === 'alert' && typeof window._loadNotificationsPanel === 'function') {
        window._loadNotificationsPanel();
    }
    // v95 · 文件夹监听 tab 首次进入时初始化
    if (tabKey === 'folder' && typeof window._loadFolderWatcherPanel === 'function') {
        window._loadFolderWatcherPanel();
    }
}

window.switchAutomationTab = switchAutomationTab;
