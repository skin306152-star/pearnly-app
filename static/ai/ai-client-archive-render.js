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

    // 工单历史按账期倒序(最新在前)——账期是字符串"YYYY-MM",字典序即时间序。
    // ai-client.js(操作页 orders 列表)也调这份,不再各写一遍比较器。
    function sortOrdersByPeriodDesc(orders) {
        return (orders || []).slice().sort(function (a, b) {
            return String(b.period).localeCompare(String(a.period));
        });
    }

    // P1-5:0% 画像 CTA 的完整度判据由后端 GET tax-profile 出参(completeness)权威给出,
    // 前端不再手抄一份 6 字段集合(此前 Python/JS 双实现靠人肉同步,2026-07-14 收敛)。

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
            '</div></div></div>' +
            // P1-1:档案页 → 工单操作页(反向已有,历史 tab 点行进对应期)。header 按钮
            // 不带 data-order-period,onClick 里读到 null 自然回落"打开最新一期"。
            '<button type="button" class="btn sm" data-action="ca-open-order">' +
            esc(at('ca_open_order_btn')) +
            '</button>' +
            '</div>'
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

    // P1-5:新客户 0% 画像提示条——直达即"这就是画像表单所在的 tab",无需再来一次页面
    // 跳转(CTA 本身就是当前 tab 内容的引导语,不是外部链接)。
    function profileCtaHtml() {
        return (
            '<div class="fc-banner w"><span class="chip w">' +
            esc(at('ca_profile_cta_chip')) +
            '</span><span>' +
            esc(at('ca_profile_cta_s')) +
            '</span></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.clientArchiveRender = {
        sortOrdersByPeriodDesc: sortOrdersByPeriodDesc,
        headerHtml: headerHtml,
        tabsHtml: tabsHtml,
        historyListHtml: historyListHtml,
        profileCtaHtml: profileCtaHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
