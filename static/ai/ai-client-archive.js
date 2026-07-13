/*
 * Pearnly AI · ai-client-archive.js · 单客户档案页(EN-clients)编排
 *
 * URL 即客户+tab 上下文(同 ai-client.js 硬约束:页内无客户切换器,换客户回目录)。
 * 三 tab 懒加载(切到哪个 tab 才拉哪个 tab 的数据,不像客户独立页那样一次拉四视图——
 * 档案页三 tab 数据源互不重叠,没有"同一次请求顺带拿到"的捷径)。①②两 tab 直接复用
 * AI.profile(container/sections 参数化改造见 ai-profile.js 顶注),不重抄表单/面板;
 * ③工单历史点行进现有工单详情路由(#/client/<id>/wo),不在档案页里重开一套操作面板。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var S = { api: null, clientId: null, tab: null, client: null, completeness: null };
    var wired = false;

    function renderHeader() {
        $('caHeader').innerHTML = AI.clientArchiveRender.headerHtml(S.client, S.clientId);
    }

    // P1-5:0% 画像提示条只在「画像」tab 且完整度确实为 0 时出现——完整度未知(还没
    // 拉到 profile)不误报 0%,other tab 也不该被这条与自己无关的 CTA 打扰。
    function renderProfileCta() {
        var el = $('caProfileCta');
        if (!el) return;
        el.innerHTML =
            S.tab === 'profile' && S.completeness === 0
                ? AI.clientArchiveRender.profileCtaHtml()
                : '';
    }

    function renderTabs() {
        $('caTabsWrap').innerHTML = AI.clientArchiveRender.tabsHtml(S.tab);
        ['profile', 'supplier', 'history'].forEach(function (tab) {
            var el = $('cav-' + tab);
            el.classList.toggle('on', tab === S.tab);
            // 切走的 tab 清空内容(不留隐藏的旧表单——画像/供应商两 tab 都靠 AI.profile
            // 渲染带唯一 id 的 <form>,留着不清白占一份 DOM,下次切回来也会被
            // loadActiveTab() 整个重渲染覆盖,不清白留没有好处)。
            if (tab !== S.tab) el.innerHTML = '';
        });
    }

    function loadProfileTab() {
        var container = $('cav-profile');
        var clientId = S.clientId;
        container.innerHTML = AI.state.loadingHtml();
        AI.profile.mount(S.api, null, clientId, {
            container: container,
            sections: ['form', 'alias', 'obligations'],
            // P1-5:0% 画像 CTA 的完整度旁听自 AI.profile 同一次 GET tax-profile
            // (completeness 由后端出),不再为 CTA 单独重复请求一次画像。
            onProfile: function (r) {
                if (S.clientId !== clientId) return;
                S.completeness = r.completeness;
                renderProfileCta();
            },
        });
    }

    function loadSupplierTab() {
        var container = $('cav-supplier');
        container.innerHTML = AI.state.loadingHtml();
        AI.profile.mount(S.api, null, S.clientId, {
            container: container,
            sections: ['supplier'],
        });
    }

    function loadHistoryTab() {
        var container = $('cav-history');
        container.innerHTML = AI.state.loadingHtml();
        var session = S;
        S.api
            .listOrders({ client_id: S.clientId })
            .then(function (r) {
                if (S !== session) return;
                container.innerHTML = AI.clientArchiveRender.historyListHtml(r.orders || []);
            })
            .catch(function () {
                if (S !== session) return;
                container.innerHTML = AI.state.errorHtml({
                    title: at('error_t'),
                    sub: at('error_s'),
                    retryLabel: at('retry'),
                });
                var btn = container.querySelector('[data-action="retry"]');
                if (btn) btn.onclick = loadHistoryTab;
            });
    }

    function loadActiveTab() {
        renderProfileCta();
        if (S.tab === 'profile') loadProfileTab();
        else if (S.tab === 'supplier') loadSupplierTab();
        else if (S.tab === 'history') loadHistoryTab();
    }

    function onClick(e) {
        var tabBtn = e.target.closest('[data-tab]');
        if (tabBtn) {
            window.location.hash = AI.router.buildClientArchiveHash(
                S.clientId,
                tabBtn.getAttribute('data-tab')
            );
            return;
        }
        var orderRow = e.target.closest('[data-action="ca-open-order"]');
        if (orderRow) {
            // P0-2:点历史行必须进那一行对应的账期(此前恒落最新期,历史列表形同虚设)。
            // data-order-period 只有历史行才有;P1-1 页头"打开当期工单"链接复用同一个
            // data-action 但不带该属性,取到 null 时 buildClientHash 自然回落"最新期"
            // ——同一处代码路径服务两个入口,不必分叉。
            var period = orderRow.getAttribute('data-order-period');
            window.location.hash = AI.router.buildClientHash(S.clientId, 'wo', period || undefined);
        }
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        $('v-client-archive').addEventListener('click', onClick);
    }

    // route(clientId, tab) 由 ai.js 的路由订阅调用。
    function mount(api, clientId, tab) {
        S.api = api;
        S.tab = tab;
        wireOnce();
        if (S.clientId === clientId) {
            renderTabs();
            loadActiveTab();
            return;
        }
        S.clientId = clientId;
        S.client = null;
        S.completeness = null;
        renderHeader();
        renderTabs();
        loadActiveTab();
        api.getClient(clientId)
            .then(function (r) {
                if (S.clientId !== clientId) return;
                S.client = r.client;
                renderHeader();
            })
            .catch(function () {
                /* 头部展示降级用 clientId 本身(renderHeader 已处理 client=null),不阻断三 tab */
            });
    }

    window.AI = window.AI || {};
    window.AI.clientArchive = { mount: mount };
})();
