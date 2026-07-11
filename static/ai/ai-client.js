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
                        // N-3 修复:prior_period_check 是对象({status:...}),不能走通用
                        // esc(v) 路径(会字面显示 [object Object])——单独映射成人话文案。
                        var display =
                            k === 'prior_period_check'
                                ? AI.format.priorPeriodCheckText(v)
                                : /vat|amount|due/.test(k)
                                  ? AI.format.money(v)
                                  : esc(v);
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
                    '</div></div>' +
                    '<div id="brxRoot"></div>' +
                    '<div id="shadowRoot"></div>' +
                    '<div id="financialsRoot"></div>';
                // 银行对账区(E2):同一次 getOrder() 已带回 bank_recon,不再二次请求。
                AI.recon.mount(S.api, order.id, S.clientId, d.bank_recon, $('brxRoot'));
                // 影子底稿区(F3):同一次 getOrder() 已带回 shadow_draft,不再二次请求。
                AI.shadow.mount(d.shadow_draft, $('shadowRoot'));
                // 月度报表包区(G1b):同一次 getOrder() 已带回 financials,不再二次请求。
                AI.financials.mount(d.financials, $('financialsRoot'));
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
        var order = currentOrder();
        if (!order) {
            $('cv-intake').innerHTML = AI.state.emptyHtml({
                title: at('intake_empty_t'),
                sub: at('intake_empty_s'),
            });
            return;
        }
        AI.intake.mount(S.api, order, S.clientId);
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
        var order = currentOrder();
        if (!order) {
            $('cv-pkg').innerHTML = AI.state.emptyHtml({
                title: at('wo_empty_t'),
                sub: at('wo_empty_s'),
            });
            return;
        }
        AI.pkg.mount(S.api, order, S.clientId);
    }

    // 画像/别名/义务(B2-e):不像其它四个 tab 那样要求先有工单——客户建档后、开第一张
    // 工单前也该能填画像、加别名,故不早退 emptyHtml,order 可能是 null 原样传下去
    // (AI.profile.mount 内部按 order 有无决定义务清单请求带不带 period)。
    function renderProfile() {
        AI.profile.mount(S.api, currentOrder(), S.clientId);
    }

    function renderActiveView() {
        if (S.view === 'wo') renderWo();
        else if (S.view === 'intake') renderIntake();
        else if (S.view === 'review') renderReview();
        else if (S.view === 'pkg') renderPkg();
        else if (S.view === 'profile') renderProfile();
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
        var prevView = S.view;
        S.api = api;
        S.view = view;
        // 离开交付包 tab 收掉它挂在 document.body 的证据模态框(不在 cv-pkg 的 innerHTML
        // 里,tab 切走不会自动隐藏——见 ai-pkg.js onLeave 注释)。
        if (prevView === 'pkg' && view !== 'pkg' && window.AI.pkg) {
            AI.pkg.onLeave();
        }
        // 离开工单 tab 收掉银行对账区的原图模态(同上,挂 document.body 不随 innerHTML 走)。
        if (prevView === 'wo' && view !== 'wo' && window.AI.recon) {
            AI.recon.onLeave();
        }
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
        ['intake', 'wo', 'review', 'pkg', 'profile'].forEach(function (v) {
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
                ['intake', 'wo', 'review', 'pkg', 'profile'].forEach(function (v) {
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
