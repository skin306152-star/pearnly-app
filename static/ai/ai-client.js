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

    // P0-2:深链带的 period → S.orders 里的下标。找不到(该期确实没单/期已过滤掉)
    // 诚实落最新期(下标 0,S.orders 已按期倒序),不是静默忽略也不是报错整页——降级到
    // "打开这个客户能打开的最新一期",比空白页更可用。
    function periodIndexOf(period) {
        if (!period) return 0;
        for (var i = 0; i < S.orders.length; i++) {
            if (S.orders[i].period === period) return i;
        }
        return 0;
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

    // 零数据首跑旅程收口(方案 §5:"填画像 → 开当期工单 → 传料",零死路):brand-new
    // 客户第一次进工单 tab 时 S.orders 为空,此前是纯空态死胡同(矩阵/看板批量开单是
    // 唯一入口,但那要求先回工作台再找到这个客户)——就地给一个"开当期工单"按钮,
    // 复用现成 createOrder(),period 取 AI.board.currentPeriodBE()(同矩阵/看板的
    // "当期"权威口径,不自造第二套)。
    function woEmptyHtml() {
        return (
            AI.state.emptyHtml({ title: at('wo_empty_t'), sub: at('wo_empty_s') }) +
            '<button type="button" class="btn pri" data-action="wo-open-first">' +
            esc(at('wo_open_first_btn')) +
            '</button>'
        );
    }

    function openFirstOrder() {
        var btn = $('cv-wo').querySelector('[data-action="wo-open-first"]');
        if (btn) {
            if (btn.disabled) return;
            btn.disabled = true;
            btn.textContent = at('wo_open_first_busy');
        }
        S.api
            .createOrder({
                workspace_client_id: Number(S.clientId),
                period: AI.board.currentPeriodBE(),
                intent: 'monthly_vat',
            })
            .then(function () {
                return S.api.listOrders({ client_id: S.clientId });
            })
            .then(function (r) {
                S.orders = (r.orders || []).slice().sort(function (a, b) {
                    return String(b.period).localeCompare(String(a.period));
                });
                S.periodIdx = 0;
                renderPeriodPicker();
                renderWo();
            })
            .catch(function () {
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = at('wo_open_first_btn');
                }
            });
    }

    function renderWo() {
        var body = $('cv-wo');
        var order = currentOrder();
        if (!order) {
            body.innerHTML = woEmptyHtml();
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
                    '<div id="corrobRoot"></div>' +
                    '<div id="brxRoot"></div>' +
                    '<div id="shadowRoot"></div>' +
                    '<div id="financialsRoot"></div>';
                // 销项佐证区(MC1-c.1):同一次 getOrder() 已带回 sales_corroboration,不再二次请求。
                AI.corrob.mount(d.sales_corroboration, $('corrobRoot'));
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
        // P1-1:工单操作页 → 客户档案页互跳(此前只有档案页→工单单向)。
        $('clientArchiveLink').onclick = function () {
            window.location.hash = AI.router.buildClientArchiveHash(
                S.clientId,
                AI.router.DEFAULT_ARCHIVE_TAB
            );
        };
        $('cv-wo').addEventListener('click', function (e) {
            if (e.target.closest('[data-action="wo-open-first"]')) openFirstOrder();
        });
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

    // route(clientId, view, period) 由 ai.js 的路由订阅调用;period 由 P0-2 深链带入
    // (缺省 = 落最新期,既有行为不变)。同一客户内切 tab/切期不重新拉客户身份。
    function mount(api, clientId, view, period) {
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
            // 同客户内的深链切期(如工单历史点了另一行):orders 已在手,直接定位,
            // 不重新拉一遍客户身份(同分支既有的"只切 tab 不重拉"精神一致)。
            if (period && S.orders.length) S.periodIdx = periodIndexOf(period);
            renderTabs();
            renderPeriodPicker();
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
                S.periodIdx = periodIndexOf(period);
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
