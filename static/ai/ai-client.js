/*
 * Pearnly AI · ai-client.js · 客户独立页(收料/工单/审核/交付包四视图壳)
 *
 * 硬约束(M1 拍板):URL 即客户上下文,页内无「客户」切换器(只读标识);
 * 换客户 = 回选客户层。不读/写 localStorage 里的"当前客户"(双标签隔离)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };
    var VIEWS = AI.router.VIEWS;

    // 模块作用域态:每个标签页各自一份 JS 运行时,天然不跨标签共享(无需额外隔离逻辑)。
    var S = { api: null, clientId: null, view: null, client: null, orders: [], periodIdx: 0 };

    function esc(s) {
        return AI.state.esc(s);
    }

    function currentOrder() {
        return S.orders[S.periodIdx] || null;
    }

    function renderHeader() {
        var name = S.client ? S.client.name : S.clientId;
        $('clientName').textContent = name;
        $('clientAvatar').textContent = (name || '?').trim().slice(0, 1).toUpperCase();
    }

    function renderPeriodPicker() {
        var btn = $('periodValue');
        var menu = $('periodMenu');
        if (!S.orders.length) {
            btn.textContent = at('period_empty');
            menu.innerHTML = '';
            menu.classList.remove('on');
            return;
        }
        btn.textContent = S.orders[S.periodIdx].period;
        menu.innerHTML = S.orders
            .map(function (o, i) {
                return (
                    '<button data-i="' +
                    i +
                    '" class="' +
                    (i === S.periodIdx ? 'on' : '') +
                    '">' +
                    esc(o.period) +
                    '</button>'
                );
            })
            .join('');
        menu.querySelectorAll('button').forEach(function (b) {
            b.onclick = function () {
                S.periodIdx = Number(b.getAttribute('data-i'));
                menu.classList.remove('on');
                renderPeriodPicker();
                renderActiveView();
            };
        });
    }

    function renderTabs() {
        VIEWS.forEach(function (v) {
            var el = $('tab' + v.charAt(0).toUpperCase() + v.slice(1));
            el.classList.toggle('on', v === S.view);
        });
        VIEWS.forEach(function (v) {
            $('cv-' + v).classList.toggle('on', v === S.view);
        });
    }

    function renderWo() {
        var body = $('cv-wo');
        var order = currentOrder();
        if (!order) {
            body.innerHTML = AI.state.emptyHtml({ title: at('wo_empty_t'), sub: at('wo_empty_s') });
            return;
        }
        body.innerHTML = AI.state.loadingHtml();
        S.api
            .getOrder(order.id)
            .then(function (d) {
                var numKeys = Object.keys(d.numbers || {});
                var cells = numKeys
                    .map(function (k) {
                        var v = (d.numbers || {})[k];
                        var display = /vat|amount|due/.test(k) ? AI.format.money(v) : esc(v);
                        return (
                            '<div class="cell"><div class="lb">' +
                            esc(AI.format.fieldLabel(k)) +
                            '</div><div class="v num">' +
                            display +
                            '</div></div>'
                        );
                    })
                    .join('');
                var needs = (d.needs || [])
                    .map(function (n) {
                        return '<div class="ni">' + esc(n) + '</div>';
                    })
                    .join('');
                body.innerHTML =
                    '<div class="panel"><div class="hd"><h3>' +
                    esc(at('tab_wo')) +
                    ' ' +
                    AI.format.chipHtml(d.status, d) +
                    '<span class="note">' +
                    esc(at('wo_step')) +
                    ': ' +
                    esc(d.current_step) +
                    '</span></h3></div><div class="bd">' +
                    (cells ? '<div class="wosum">' + cells + '</div>' : '') +
                    (needs ? '<div class="needs-list">' + needs + '</div>' : '') +
                    '</div></div>';
            })
            .catch(function () {
                body.innerHTML = AI.state.errorHtml({
                    title: at('error_t'),
                    sub: at('error_s'),
                    retryLabel: at('retry'),
                });
                var btn = body.querySelector('[data-action="retry"]');
                if (btn) btn.onclick = renderWo;
            });
    }

    function renderIntake() {
        $('cv-intake').innerHTML = AI.state.emptyHtml({
            title: at('intake_soon_t'),
            sub: at('intake_soon_s'),
        });
    }

    function renderReview() {
        var order = currentOrder();
        if (!order) {
            $('cv-review').innerHTML = AI.state.emptyHtml({
                title: at('wo_empty_t'),
                sub: at('wo_empty_s'),
            });
            return;
        }
        AI.review.mount(S.api, order, S.clientId);
    }

    function renderPkg() {
        var body = $('cv-pkg');
        var order = currentOrder();
        if (!order) {
            body.innerHTML = AI.state.emptyHtml({ title: at('wo_empty_t'), sub: at('wo_empty_s') });
            return;
        }
        body.innerHTML = AI.state.loadingHtml();
        S.api
            .listDeliverables(order.id)
            .then(function (r) {
                var rows = r.deliverables || [];
                if (!rows.length) {
                    body.innerHTML = AI.state.emptyHtml({
                        title: at('pkg_empty_t'),
                        sub: at('pkg_empty_s'),
                    });
                    return;
                }
                body.innerHTML =
                    '<div class="panel"><div class="bd">' +
                    rows
                        .map(function (d) {
                            var n = d.numbers || {};
                            var firstKey = Object.keys(n)[0];
                            var v = firstKey ? AI.format.money(n[firstKey]) : '';
                            return (
                                '<div class="dlv-line"><div class="d">' +
                                esc(AI.format.fieldLabel(d.kind)) +
                                '</div><div class="n">' +
                                v +
                                '</div></div>'
                            );
                        })
                        .join('') +
                    '</div></div>';
            })
            .catch(function () {
                body.innerHTML = AI.state.errorHtml({
                    title: at('error_t'),
                    sub: at('error_s'),
                    retryLabel: at('retry'),
                });
                var btn = body.querySelector('[data-action="retry"]');
                if (btn) btn.onclick = renderPkg;
            });
    }

    function renderActiveView() {
        if (S.view === 'wo') renderWo();
        else if (S.view === 'intake') renderIntake();
        else if (S.view === 'review') renderReview();
        else if (S.view === 'pkg') renderPkg();
    }

    function wireChrome() {
        $('periodBtn').onclick = function () {
            $('periodMenu').classList.toggle('on');
        };
        document.addEventListener('click', function (e) {
            if (!$('periodBtn').contains(e.target) && !$('periodMenu').contains(e.target)) {
                $('periodMenu').classList.remove('on');
            }
        });
        VIEWS.forEach(function (v) {
            var el = $('tab' + v.charAt(0).toUpperCase() + v.slice(1));
            el.onclick = function () {
                window.location.hash = AI.router.buildClientHash(S.clientId, v);
            };
        });
    }

    var chromeWired = false;

    // route(clientId, view) 由 ai.js 的路由订阅调用;同一客户内切 tab/切期不重新拉客户身份。
    function mount(api, clientId, view) {
        S.api = api;
        S.view = view;
        if (!chromeWired) {
            wireChrome();
            chromeWired = true;
        }
        if (S.clientId === clientId) {
            renderTabs();
            renderActiveView();
            return;
        }
        S.clientId = clientId;
        S.client = null;
        S.orders = [];
        S.periodIdx = 0;
        renderHeader();
        renderTabs();
        ['intake', 'wo', 'review', 'pkg'].forEach(function (v) {
            $('cv-' + v).innerHTML = AI.state.loadingHtml();
        });
        Promise.all([api.getClient(clientId), api.listOrders({ client_id: clientId })])
            .then(function (r) {
                S.client = r[0].client;
                S.orders = (r[1].orders || []).slice().sort(function (a, b) {
                    return String(b.period).localeCompare(String(a.period));
                });
                S.periodIdx = 0;
                renderHeader();
                renderPeriodPicker();
                renderActiveView();
            })
            .catch(function () {
                renderHeader();
                ['intake', 'wo', 'review', 'pkg'].forEach(function (v) {
                    $('cv-' + v).innerHTML = AI.state.errorHtml({
                        title: at('error_t'),
                        sub: at('error_s'),
                    });
                });
            });
    }

    window.AI = window.AI || {};
    window.AI.client = { mount: mount };
})();
