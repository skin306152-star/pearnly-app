// REFACTOR-C1-home-batch9g1 · 从 home.js verbatim 抽出(0 逻辑改)
// 集成页顶 tab 切换 + 集成配置抽屉(window.openIntegrationDrawer/closeIntegrationDrawer/activateIntegrationsLogsTab)
/* global loadErpLogs, loadErpTodayStats, loadErpEndpoints */

// A4 (v118.34.19 · Zihao 2026-05-19 拍板) · 集成主页面顶部 tab 切换
// + "看推送日志 →" 链接(从 ERP 卡片 / 也可来自其他地方)
(function () {
    function _activateIntTopTab(targetKey: string) {
        const tabs = document.querySelectorAll('#page-integrations .int-top-tab');
        const panels = document.querySelectorAll('#page-integrations .int-top-panel');
        tabs.forEach((t) => {
            const k = (t as HTMLElement).dataset.intTopTab;
            t.classList.toggle('active', k === targetKey);
        });
        panels.forEach((p) => {
            const k = (p as HTMLElement).dataset.intTopPanel;
            p.classList.toggle('active', k === targetKey);
        });
        // 切到 logs · 触发一次 fetch 让用户立刻看到数据
        if (targetKey === 'logs' && typeof loadErpLogs === 'function') {
            try {
                loadErpLogs();
            } catch (e) {}
            if (typeof loadErpTodayStats === 'function') {
                try {
                    loadErpTodayStats();
                } catch (e) {}
            }
        }
        // 切到 push-exc · 加载 ERP 推送异常块(原在异常页 · 搬来集成页独立 tab)
        if (targetKey === 'push-exc' && typeof window.loadErpExceptions === 'function') {
            try {
                window.loadErpExceptions();
            } catch (e) {}
        }
    }
    // 暴露给 ERP 抽屉「看推送日志 →」按钮调用
    window.activateIntegrationsLogsTab = function () {
        // 如果集成抽屉打开了 · 关掉
        try {
            const drawer = document.getElementById('int-drawer');
            const overlay = document.getElementById('int-drawer-overlay');
            if (drawer) drawer.classList.remove('open');
            if (overlay) overlay.classList.remove('open');
            // 调用现有的关闭逻辑(若存在)清理 panel 归还
            if (typeof window.closeIntegrationDrawer === 'function') {
                window.closeIntegrationDrawer();
            }
        } catch (e) {}
        // 切到集成页 + logs tab
        if (typeof window.navigateTo === 'function') {
            try {
                window.navigateTo('integrations');
            } catch (e) {}
        } else {
            try {
                location.hash = '#/integrations';
            } catch (e) {}
        }
        _activateIntTopTab('logs');
        // 滚顶
        try {
            const page = document.getElementById('page-integrations');
            if (page) page.scrollIntoView({ block: 'start', behavior: 'smooth' });
        } catch (e) {}
    };

    document.addEventListener('click', function (e) {
        // tab 切换
        const tab = (e.target as HTMLElement).closest('#page-integrations .int-top-tab');
        if (tab) {
            const k = (tab as HTMLElement).dataset.intTopTab;
            if (k) _activateIntTopTab(k);
            return;
        }
        // 「看推送日志 →」按钮(集成页 ERP 卡片 OR ERP 抽屉内 ERP 连接卡片)
        const logsBtn = (e.target as HTMLElement).closest(
            '[data-int-action="view-logs"], .int-btn-view-logs'
        );
        if (logsBtn) {
            e.preventDefault();
            e.stopPropagation();
            window.activateIntegrationsLogsTab!();
        }
    });

    // 路由切到 #/integrations 时 · 如果 hash 带 ?tab=logs · 自动切 logs
    function _onRouteToIntegrations() {
        const h = (location.hash || '').toLowerCase();
        if (h.includes('integrations') && h.includes('tab=logs')) {
            setTimeout(() => _activateIntTopTab('logs'), 50);
        }
    }
    window.addEventListener('hashchange', _onRouteToIntegrations);
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        _onRouteToIntegrations();
    } else {
        document.addEventListener('DOMContentLoaded', _onRouteToIntegrations);
    }
})();

// v118.32.5.5.37 · 集成配置抽屉核心函数
(function () {
    'use strict';

    // 把 .auto-panel 从 drawer body 归还到 .auto-content
    function _returnPanel() {
        const body = document.getElementById('int-drawer-body');
        if (!body) return;
        const autoContent = document.querySelector('.auto-content');
        if (!autoContent) return;
        Array.from(body.querySelectorAll('.auto-panel')).forEach(function (el: Element) {
            (el as HTMLElement).style.display = '';
            autoContent.appendChild(el);
        });
    }

    window.openIntegrationDrawer = function (tab, title) {
        const drawer = document.getElementById('int-drawer');
        const overlay = document.getElementById('int-drawer-overlay');
        const titleEl = document.getElementById('int-drawer-title');
        const body = document.getElementById('int-drawer-body');
        if (!drawer || !body) return;

        // 先归还上一个 panel
        _returnPanel();

        drawer.dataset.currentTab = tab || '';
        if (titleEl) titleEl.textContent = title || '';
        body.innerHTML = '';

        // anchor → data-auto-panel ID 映射(自动化页面里的 panel 名)
        var _panelIds = {
            line: 'linebot',
            folder: 'folder',
            email: 'email',
            alert: 'alert',
            erp: 'erp',
            bank: 'bank',
        };
        var panelId = _panelIds[tab as keyof typeof _panelIds] || tab;

        // 把对应的 auto-panel 移入抽屉(DOM move · 保留事件监听)
        const panel = document.querySelector('.auto-panel[data-auto-panel="' + panelId + '"]');
        if (panel) {
            (panel as HTMLElement).style.display = 'block';
            body.appendChild(panel);
        } else {
            body.innerHTML =
                '<div style="padding:20px;color:var(--ink-3);font-size:13px;">面板未找到</div>';
        }

        // 打开动画
        drawer.classList.add('open');
        if (overlay) overlay.style.display = 'block';
        document.body.style.overflow = 'hidden';

        // 触发数据加载(panel 已在 DOM 里 · loader 按固定 ID 渲染)
        var loaders = {
            line: window._loadLineBotPanel,
            folder: window._loadFolderWatcherPanel,
            email: window._loadEmailIngestPanel,
            alert: window._loadNotificationsPanel,
            bank: window._loadBankReconPanel,
        };
        if (loaders[tab as keyof typeof loaders]) {
            try {
                loaders[tab as keyof typeof loaders]!();
            } catch (e) {
                console.warn('[int-drawer] loader error', e);
            }
        } else if (tab === 'erp') {
            try {
                if (typeof loadErpEndpoints === 'function') loadErpEndpoints();
                if (typeof loadErpLogs === 'function') loadErpLogs();
            } catch (e) {
                console.warn('[int-drawer] ERP load error', e);
            }
        }
    };

    window.closeIntegrationDrawer = function () {
        _returnPanel();
        var drawer = document.getElementById('int-drawer');
        var overlay = document.getElementById('int-drawer-overlay');
        if (drawer) {
            drawer.classList.remove('open');
            drawer.dataset.currentTab = '';
        }
        if (overlay) overlay.style.display = 'none';
        document.body.style.overflow = '';
    };

    // 绑定关闭事件
    function _initDrawerEvents() {
        var closeBtn = document.getElementById('int-drawer-close');
        var overlay = document.getElementById('int-drawer-overlay');
        if (closeBtn)
            closeBtn.addEventListener('click', window.closeIntegrationDrawer as EventListener);
        if (overlay)
            overlay.addEventListener('click', window.closeIntegrationDrawer as EventListener);
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') window.closeIntegrationDrawer!();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _initDrawerEvents);
    } else {
        _initDrawerEvents();
    }
})();
