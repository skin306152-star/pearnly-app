/*
 * Pearnly AI · ai-client-archive-render.js · 单客户档案页(EN-clients)纯逻辑 + HTML 拼装
 *
 * 三 tab 分工:①税务画像(复用 AI.profile 的 form/alias/obligations 三段,见
 * ai-profile.js container/sections 改造)②供应商过账档案(复用 AI.profile 的 supplier 段)
 * ③工单历史(本文件独有——按客户列全部工单,GET /api/workorder/orders?client_id= 已支持,
 * 零新增后端)。①②两个 tab 的表单/面板 HTML 不在本文件重复拼装(见顶注复用铁律)。
 *
 * 上半段(sortOrdersByPeriodDesc)零 DOM/零 i18n 依赖,node
 * (tests/unit/test_ai_client_archive_pure.py)直接 require 断言;下半段依赖
 * at()/AI.state/AI.format/AI.router,只在浏览器根挂载。
 */
(function (root) {
    'use strict';

    // 工单历史按账期倒序(最新在前)——同 ai-client.js renderPeriodPicker 的既有口径,
    // 目录/档案/操作页三处独立现算不共享一份缓存(账期是字符串"YYYY-MM"字典序即时间序)。
    function sortOrdersByPeriodDesc(orders) {
        return (orders || []).slice().sort(function (a, b) {
            return String(b.period).localeCompare(String(a.period));
        });
    }

    var pure = { sortOrdersByPeriodDesc: sortOrdersByPeriodDesc };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state/AI.format/AI.router,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }

    function headerHtml(client, clientId) {
        var name = client ? client.name : clientId;
        return (
            '<div class="chead"><div class="who-ro"><div class="cavatar">' +
            esc((name || '?').trim().slice(0, 1).toUpperCase()) +
            '</div><div><div class="ctitle">' +
            esc(name) +
            '</div><div class="csub">' +
            esc((client && client.tax_id) || '—') +
            '</div></div></div></div>'
        );
    }

    var TAB_LABEL_KEY = {
        profile: 'ca_tab_profile',
        supplier: 'ca_tab_supplier',
        history: 'ca_tab_history',
    };

    function tabsHtml(activeTab) {
        return (
            '<div class="ctabs" id="caTabs">' +
            root.AI.router.ARCHIVE_TABS.map(function (tab) {
                return (
                    '<button data-tab="' +
                    tab +
                    '" class="' +
                    (tab === activeTab ? 'on' : '') +
                    '"><span>' +
                    esc(at(TAB_LABEL_KEY[tab])) +
                    '</span></button>'
                );
            }).join('') +
            '</div>'
        );
    }

    function historyRowHtml(order) {
        return (
            '<div class="dlv-line" data-action="ca-open-order" data-order-period="' +
            esc(order.period) +
            '" tabindex="0">' +
            '<div class="d">' +
            esc(order.period) +
            '</div>' +
            root.AI.format.chipHtml(order.status) +
            '</div>'
        );
    }

    function historyListHtml(orders) {
        var sorted = sortOrdersByPeriodDesc(orders);
        if (!sorted.length) {
            return AI.state.emptyHtml({
                title: at('ca_history_empty_t'),
                sub: at('ca_history_empty_s'),
            });
        }
        return (
            '<div class="panel"><div class="bd">' +
            sorted.map(historyRowHtml).join('') +
            '</div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.clientArchiveRender = {
        sortOrdersByPeriodDesc: sortOrdersByPeriodDesc,
        headerHtml: headerHtml,
        tabsHtml: tabsHtml,
        historyListHtml: historyListHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
