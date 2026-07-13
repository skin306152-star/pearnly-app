/*
 * Pearnly AI · ai-reports.js · 跨客户报表中心(EN-clients · 侧栏「报表」转正)编排
 *
 * 选客户 + 选期间 → GET /api/workorder/orders?client_id=&period= 定位该期工单(已支持
 * period 过滤,零新增后端)→ 有工单则 getOrder() 取一次详情,BS/PL/TB 直接喂给既有
 * AI.financials.mount()/影子底稿喂给既有 AI.shadow.mount()(两者原生接受容器参数,
 * 不重拼一份 HTML)+ listDeliverables 取下载清单;没有工单则四语空态 + 去开单
 * (复用 createOrder,同 ai-matrix.js 批量开单先例的单条版)。
 *
 * 依赖 window.AI.state/api/format/financials/shadow/pkgRender/reportsRender 与全局
 * at(),排在 ai-payroll.js 之后、ai.js 之前加载(见 scripts/build-home-js.mjs)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var S = null;
    var wired = false;

    function body() {
        return $('rptBody');
    }

    function freshState(api) {
        return {
            api: api,
            clients: [],
            clientId: '',
            period: AI.payrollRender.defaultPeriod(),
            order: null,
            deliverables: [],
            downloading: null,
            loading: false,
        };
    }

    function renderPicker() {
        $('rptPicker').innerHTML = AI.reportsRender.pickerHtml(S);
    }

    function renderPrompt() {
        body().innerHTML = AI.state.emptyHtml({
            title: at('reports_prompt_t'),
            sub: at('reports_prompt_s'),
        });
    }

    function renderNoOrder() {
        body().innerHTML = AI.reportsRender.noOrderHtml();
    }

    function renderReport() {
        body().innerHTML =
            '<div id="rptFinancials"></div><div id="rptShadow"></div><div id="rptDeliverables"></div>';
        AI.financials.mount(S.order.financials, $('rptFinancials'));
        AI.shadow.mount(S.order.shadow_draft, $('rptShadow'));
        renderDeliverables();
    }

    function renderDeliverables() {
        var el = $('rptDeliverables');
        if (el)
            el.innerHTML = AI.reportsRender.deliverablesPanelHtml(S.deliverables, S.downloading);
    }

    function isReady() {
        return !!S.clientId && /^\d{4}-\d{2}$/.test(String(S.period || ''));
    }

    function load() {
        if (!isReady()) {
            renderPrompt();
            return;
        }
        var session = S;
        S.loading = true;
        body().innerHTML = AI.state.loadingHtml();
        S.api
            .listOrders({ client_id: S.clientId, period: S.period })
            .then(function (r) {
                if (S !== session) return null;
                var order = AI.reportsRender.pickOrderForPeriod(r.orders || [], S.period);
                if (!order) {
                    S.order = null;
                    renderNoOrder();
                    return null;
                }
                return Promise.all([S.api.getOrder(order.id), S.api.listDeliverables(order.id)]);
            })
            .then(function (r) {
                if (S !== session || !r) return;
                S.order = r[0];
                S.deliverables = r[1].deliverables || [];
                renderReport();
            })
            .catch(function () {
                if (S !== session) return;
                body().innerHTML = AI.state.errorHtml({
                    title: at('error_t'),
                    sub: at('error_s'),
                    retryLabel: at('retry'),
                });
                var btn = body().querySelector('[data-action="retry"]');
                if (btn) btn.onclick = load;
            })
            .then(function () {
                if (S !== session) return;
                S.loading = false;
            });
    }

    function loadClients() {
        S.api
            .listClients()
            .then(function (r) {
                if (!S) return;
                S.clients = (r && r.clients) || [];
                renderPicker();
            })
            .catch(function () {
                /* 客户下拉加载失败不阻断本页其余功能,选择器留空重试即可 */
            });
    }

    function openOrder() {
        if (!isReady() || S.loading) return;
        S.loading = true;
        body().innerHTML = AI.state.loadingHtml();
        S.api
            .createOrder({
                workspace_client_id: Number(S.clientId),
                period: S.period,
                intent: 'monthly_vat',
            })
            .then(load)
            .catch(load);
    }

    function download(kind) {
        if (S.downloading || !S.order) return;
        var session = S;
        S.downloading = kind;
        renderDeliverables();
        S.api
            .downloadDeliverable(S.order.id, kind)
            .then(function (r) {
                if (S !== session) return;
                var url = URL.createObjectURL(r.blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = r.filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                URL.revokeObjectURL(url);
            })
            .catch(function () {
                /* 下载失败不额外报错态,按钮解禁即可再点(同 ai-pkg.js download() 先例) */
            })
            .then(function () {
                if (S !== session) return;
                S.downloading = null;
                renderDeliverables();
            });
    }

    function onClick(e) {
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var a = el.getAttribute('data-action');
        if (a === 'reports-open-order') openOrder();
        else if (a === 'reports-download') download(el.getAttribute('data-kind'));
    }

    function onChange(e) {
        if (e.target.id === 'rptClientSel') {
            S.clientId = e.target.value;
            load();
        } else if (e.target.id === 'rptPeriodInput') {
            S.period = e.target.value.trim();
            load();
        }
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        $('v-reports').addEventListener('click', onClick);
        $('v-reports').addEventListener('change', onChange);
    }

    function mount(api) {
        S = freshState(api);
        wireOnce();
        renderPicker();
        renderPrompt();
        loadClients();
    }

    window.AI = window.AI || {};
    window.AI.reports = { mount: mount };
})();
