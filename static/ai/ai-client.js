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
    var S = {
        api: null,
        clientId: null,
        view: null,
        client: null,
        orders: [],
        periodIdx: 0,
        deepLinkPeriod: null, // J-B/J-8:深链带的 ?period=,零工单空态开单控件据此默认(而非恒回当月)
    };
    var woPoll = null; // 工单页自动刷新轮询句柄(J-B/J-10):离开 wo 视图/换单/归档终态时停

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
        // 身份未拉到时回落占位符,不拿裸 clientId 冒充客户名(S2 §6 · 真跑实测加载态糊数字)。
        var name = S.client ? S.client.name : '…';
        $('clientName').textContent = name;
        $('clientAvatar').textContent = (name || '?').trim().slice(0, 1).toUpperCase();
        // 面包屑尾节点补真实客户名(清单 #6):setCrumb 在路由时先挂「客户」占位
        // (首访客户名未必在手),身份拉到后在这里写回。
        var crumbCur = $('crumbClientCur');
        if (crumbCur && S.client) crumbCur.textContent = S.client.name;
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

    // 开单 + 重拉订单列表 + 定位到新开的那期(wo 空态「开当期工单」/ intake 空态「开单账期
    // 选择器」共用同一段联网时序,只是各自的按钮态字/落定期不同)。
    function createOrderAndReload(period, btn, idleLabel, onDone) {
        if (btn) {
            if (btn.disabled) return;
            btn.disabled = true;
            btn.textContent = at('card_open_order_busy');
        }
        S.api
            .createOrder({
                workspace_client_id: Number(S.clientId),
                period: period,
                intent: 'monthly_vat',
            })
            .then(function () {
                return S.api.listOrders({ client_id: S.clientId });
            })
            .then(function (r) {
                S.orders = AI.clientArchiveRender.sortOrdersByPeriodDesc(r.orders);
                S.periodIdx = periodIndexOf(period);
                renderPeriodPicker();
                if (onDone) onDone();
            })
            .catch(function () {
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = idleLabel;
                }
            });
    }

    function openFirstOrder() {
        var btn = $('cv-wo').querySelector('[data-action="wo-open-first"]');
        createOrderAndReload(AI.board.currentPeriodBE(), btn, at('wo_open_first_btn'), renderWo);
    }

    // 零工单空态的开单账期选择器(J-8/J-B):默认账期不再恒回当月——深链带了 ?period=
    // (如从看板/客户档案页历史点进来)就该默认那一期,否则用户正在跑的是 2569-05、
    // 控件却默认冒出 2569-07,点错一次就多开一张不该开的工单。default 落最新已知深链
    // 期,没有才回落当月(既有行为不变)。
    function intakeEmptyHtml() {
        var defaultPeriod = S.deepLinkPeriod || AI.board.currentPeriodBE();
        var optsHtml = AI.state.optionsHtml(AI.board.periodOptions(), defaultPeriod, function (p) {
            return p;
        });
        return (
            AI.state.emptyHtml({ title: at('intake_empty_t'), sub: at('intake_empty_s') }) +
            '<div class="kopen"><select class="period-sel" id="ikEmptyPeriodSel" aria-label="' +
            esc(at('card_period_select_label')) +
            '">' +
            optsHtml +
            '</select><button type="button" class="btn pri" data-action="intake-open-order">' +
            esc(at('card_open_order')) +
            '</button></div>'
        );
    }

    function openIntakeOrder() {
        var container = $('cv-intake');
        var sel = container.querySelector('#ikEmptyPeriodSel');
        var period = (sel && sel.value) || AI.board.currentPeriodBE();
        var btn = container.querySelector('[data-action="intake-open-order"]');
        createOrderAndReload(period, btn, at('card_open_order'), renderIntake);
    }

    // 工单页活着就自动刷(J-10):5s 一轮只重画顶部摘要(chip/进度/需料/引导条)——不重挂
    // corrob/recon/shadow/financials 子件,那些各自持有自己的展开态/模态框,每 5s 强拆
    // 会把用户正在看的东西震掉,超出这次要修的范围。maxTries 传 Infinity:这不是"重跑后
    // 盯一阵"的有限等待,是"页面开着就该一直活"的常驻刷新,没有到期就装死的道理;归档
    // (终态)后自己停,数字不会再变(archive.py 只读收口)。
    function startWoPoll(order) {
        var session = S;
        stopWoPoll();
        woPoll = AI.poll.create({
            maxTries: Infinity,
            fetch: function () {
                return session.api.getOrder(order.id);
            },
            onTick: function (d) {
                if (S !== session || S.view !== 'wo') return;
                if (!currentOrder() || currentOrder().id !== order.id) return;
                var panel = $('woSummaryPanel');
                if (panel) panel.innerHTML = AI.clientWoRender.woSummaryHtml(d, S.clientId);
                if (d.status === 'archive') stopWoPoll();
            },
        });
        woPoll.start();
    }

    function stopWoPoll() {
        if (woPoll) {
            woPoll.stop();
            woPoll = null;
        }
    }

    function renderWo() {
        var body = $('cv-wo');
        var order = currentOrder();
        stopWoPoll();
        if (!order) {
            body.innerHTML = woEmptyHtml();
            return;
        }
        body.innerHTML = AI.state.loadingHtml();
        var session = S;
        S.api
            .getOrder(order.id)
            .then(function (d) {
                if (S !== session || S.view !== 'wo') return; // 已切走
                if (!currentOrder() || currentOrder().id !== order.id) return; // 已切期/切客户
                body.innerHTML =
                    '<div id="woSummaryPanel"></div>' +
                    '<div id="corrobRoot"></div>' +
                    '<div id="brxRoot"></div>' +
                    '<div id="shadowRoot"></div>' +
                    '<div id="financialsRoot"></div>';
                $('woSummaryPanel').innerHTML = AI.clientWoRender.woSummaryHtml(d, S.clientId);
                // 销项佐证区(MC1-c.1 / SA-2b):同一次 getOrder() 已带回 sales_corroboration
                // 与 edc_corroboration,两卡并排渲染,不再二次请求。
                AI.corrob.mount(d.sales_corroboration, $('corrobRoot'), d.edc_corroboration);
                // 银行对账区(E2):同一次 getOrder() 已带回 bank_recon,不再二次请求。
                AI.recon.mount(S.api, order.id, S.clientId, d.bank_recon, $('brxRoot'));
                // 影子底稿区(F3):同一次 getOrder() 已带回 shadow_draft,不再二次请求。
                AI.shadow.mount(d.shadow_draft, $('shadowRoot'));
                // 月度报表包区(G1b):同一次 getOrder() 已带回 financials,不再二次请求。
                AI.financials.mount(d.financials, $('financialsRoot'));
                if (d.status !== 'archive') startWoPoll(order);
            })
            .catch(function () {
                if (S !== session) return;
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
            $('cv-intake').innerHTML = intakeEmptyHtml();
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
            // 引导链②(J-B):工单页「有 N 件事等你」→ 待我处理聚合队列(D2-S8/MC1-b2,
            // 同看板 col_review「等你审」跳的同一个地方,不另造第二个"审核入口")。
            else if (e.target.closest('[data-action="wo-goto-pool"]')) {
                window.location.hash = AI.router.buildPoolHash();
            }
        });
        $('cv-intake').addEventListener('click', function (e) {
            if (e.target.closest('[data-action="intake-open-order"]')) openIntakeOrder();
        });
        $('periodBtn').onclick = function () {
            $('periodMenu').classList.toggle('on');
        };
        document.addEventListener('click', function (e) {
            if (!$('periodBtn').contains(e.target) && !$('periodMenu').contains(e.target)) {
                $('periodMenu').classList.remove('on');
            }
        });
        // Esc 关账期下拉(§2 死路批,与矩阵 wirePeriodToggle 同款):点外面能关,键盘也得能关。
        document.addEventListener('keydown', function (e) {
            var menu = $('periodMenu');
            if (e.key === 'Escape' && menu.classList.contains('on')) menu.classList.remove('on');
        });
        VIEWS.forEach(function (v) {
            var el = $('tab' + v.charAt(0).toUpperCase() + v.slice(1));
            el.onclick = function () {
                // R2F-R3:tab 切换必须带上当前选中账期,否则新 hash 丢 ?period=——
                // 刷新时 mount() 走"不同客户"分支重新 periodIndexOf(null) 落回最新期,
                // 账期角标就会跟切走前实际展示的那期对不上(见 periodIndexOf 注释)。
                var order = currentOrder();
                window.location.hash = AI.router.buildClientHash(
                    S.clientId,
                    v,
                    order ? order.period : undefined
                );
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
            // 不重新拉一遍客户身份(同分支既有的"只切 tab 不重拉"精神一致)。J-8:period
            // 带了就更新记住的深链期(覆盖上一次),没带则沿用同客户会话内已记住的那份
            // (换 tab 常常不重新带 period,不该把刚深链进来的期悄悄忘掉)。
            if (period) S.deepLinkPeriod = period;
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
        S.deepLinkPeriod = period || null; // 换客户:不带 period 就不留上一个客户的深链期
        renderHeader();
        renderTabs();
        ['intake', 'wo', 'review', 'pkg', 'profile'].forEach(function (v) {
            $('cv-' + v).innerHTML = AI.state.loadingHtml();
        });
        Promise.all([api.getClient(clientId), api.listOrders({ client_id: clientId })])
            .then(function (r) {
                S.client = r[0].client;
                S.orders = AI.clientArchiveRender.sortOrdersByPeriodDesc(r[1].orders);
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

    // crumbName:同客户回访(切 tab/切期)时面包屑即刻显真名;身份没拉到或不是这个
    // 客户给 null,setCrumb 回落「客户」占位(ai.js)。
    function crumbName(clientId) {
        return S.client && String(S.clientId) === String(clientId) ? S.client.name : null;
    }

    window.AI = window.AI || {};
    window.AI.client = { mount: mount, crumbName: crumbName };
})();
