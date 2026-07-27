/*
 * Pearnly AI · ai-dashboard.js · 选客户层(工作台首屏)渲染 + 数据编排
 *
 * 三张统计卡从两个真实只读端点现算(客户总数 / 待你处理单数 / AI 处理中单数)。
 * 五列看板(M1-W2):list 端点只给 status,没有逐条 needs/blocked_reasons/numbers——
 * 只对「每客户最新一期」里 status=stuck(缺料/挂起判定)或 review(读 tax_due)的订单
 * 额外拉 detail,不对全量历史订单做 N+1;数量上界 = 看板会显示的卡片数。
 * HTML 拼装/事件委托在 ai-kanban-render.js,分列/摘要纯函数在 ai-board.js。
 *
 * 筛选/批量开单/「本期缺哪几张单」三样(2026-07-27 从矩阵搬来)吃同一个聚合端点
 * GET /api/tax-profile/matrix:一次请求拿全「客户 × 当期义务 × 徽章 × 截止日」,不为
 * 每张卡各问一次。该请求失败不拖垮看板——工具条整条收起,看板退回搬迁前的样子。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var lastApi = null;
    var boardWired = false;
    var S = {
        matrix: null, // 最近一次成功拉到的矩阵响应(筛选判据/缺单义务名/批量开单账期的来源)
        filters: [], // 激活的筛选:missing/review/risk 的子集
        filtersWired: false,
    };

    function latestOrderByClient(orders) {
        var byClient = {};
        orders.forEach(function (o) {
            var cur = byClient[o.workspace_client_id];
            if (!cur || String(o.period) > String(cur.period)) byClient[o.workspace_client_id] = o;
        });
        return byClient;
    }

    // 「待你处理」不再数本视图 status=stuck 的订单——该口径与 #/pool 实测同屏打架
    // (2026-07-17:两边一个 0 一个 1,用户不知道信谁),废除,改与 #/pool 同源
    // (AI.loadPendingStat 共享取数,口径在 AI.board.pendingReviewCount)。
    function renderStats(clients, orders) {
        $('statClientsV').textContent = String(clients.length);
        var running = orders.filter(function (o) {
            return o.status === 'running';
        }).length;
        $('statRunningV').textContent = String(running);
        // 看板统计跨期现算(每客户最新一期),没有单一账期可言——账期 pill 只归矩阵。
        $('sumPeriod').style.display = 'none';
    }

    // 只对「每客户最新一期」里 status=stuck(区分缺料/挂起)或 review(读 tax_due)的那些
    // 订单批量拉 detail——数量上界 = 看板会显示的卡片数,不对全量历史订单做 N+1。单条失败
    // (权限/网络)不拖垮全表:该条退化为"没有 detail"走 mapOrderToColumn/summarizeCard
    // 的保守降级分支,不中断其它卡片渲染。
    function loadDetailsForCards(api, latestOrders) {
        // collecting 也拉 detail(2026-07-17 S4):此前 collecting 卡 detail=null,摘要
        // 永远只报账期——「等待中不知等什么」实测根因;detail.needs 接通后卡片能点名缺什么。
        var needDetail = latestOrders.filter(function (o) {
            return AI.board.needsDetail(o.status);
        });
        if (!needDetail.length) return Promise.resolve({});
        return Promise.all(
            needDetail.map(function (o) {
                return api
                    .getOrder(o.id)
                    .then(function (d) {
                        return [o.id, d];
                    })
                    .catch(function () {
                        return [o.id, null];
                    });
            })
        ).then(function (pairs) {
            var byOrderId = {};
            pairs.forEach(function (p) {
                if (p[1]) byOrderId[p[0]] = p[1];
            });
            return byOrderId;
        });
    }

    function buildGroups(clients, latest, detailsByOrderId) {
        var groups = {};
        AI.board.COLUMNS.forEach(function (col) {
            groups[col.key] = [];
        });
        var lang = (window.AII18N && window.AII18N.lang) || 'zh';
        var missing = AI.boardTools.missingByClient(S.matrix, lang);
        clients.forEach(function (c) {
            var order = latest[c.id] || null;
            var detail = order ? detailsByOrderId[order.id] : null;
            var mapped = AI.board.mapOrderToColumn(order, detail);
            var entry = {
                client: c,
                order: order,
                detail: detail,
                column: mapped.column,
                unknownStatus: !!mapped.unknown,
                summary: AI.board.summarizeCard(order, detail),
                // 本期一张单都没开的客户才有这一条(缺哪几张义务单 + 批量勾选)。卡片显示的
                // 是该客户最新一期的工单,可能是上一期的——「本期还缺什么」正是那张卡看不出
                // 的东西,所以条上写死账期,不让人拿上期的状态当本期读。
                missing: missing[String(c.id)] || null,
            };
            (groups[mapped.column] || groups.materials).push(entry);
        });
        return groups;
    }

    // period 由卡片上的账期选择器带来(见 ai-kanban-render.js);缺省(未渲染选择器的老
    // 调用方/测试)时回落当月,不破坏既有行为。
    function createOrderForClient(api, clientId, period) {
        return api.createOrder({
            workspace_client_id: clientId,
            period: period || AI.board.currentPeriodBE(),
            intent: 'monthly_vat',
        });
    }

    function renderBoard(clients, latest, detailsByOrderId) {
        var body = $('dashBody');
        if (!clients.length) {
            body.innerHTML = AI.state.emptyHtml({
                title: at('empty_clients_t'),
                sub: at('empty_clients_s'),
            });
            return;
        }
        var groups = buildGroups(clients, latest, detailsByOrderId);
        AI.kanban.renderBoard(body, groups);
        // #dashBody 的节点本身不随重渲染换掉(只换 innerHTML)——事件委托只挂一次,
        // 避免每次 load() 都在同一节点上叠加监听器(否则「开单」会被重复触发)。
        if (!boardWired) {
            AI.kanban.wireBoard(
                body,
                function (clientId, period) {
                    return createOrderForClient(lastApi, clientId, period);
                },
                function () {
                    load(lastApi);
                }
            );
            boardWired = true;
        }
    }

    function wireSearch() {
        var input = $('searchInput');
        input.value = '';
        input.oninput = applyFiltersAndSearch;
    }

    // 三个筛选 chip(缺料/待审/风险)—— 判据吃矩阵格子徽章,见 ai-board-tools-render.js。
    // 拿不到矩阵响应时整条工具条收起:给个点不动的筛选比没有筛选更糟。
    function wireFilters() {
        var tools = $('boardTools');
        tools.style.display = S.matrix ? '' : 'none';
        if (!S.matrix) S.filters = [];
        if (S.filtersWired) return;
        S.filtersWired = true;
        tools.querySelectorAll('.kb-chip').forEach(function (btn) {
            btn.onclick = function () {
                var f = btn.getAttribute('data-filter');
                var idx = S.filters.indexOf(f);
                if (idx >= 0) S.filters.splice(idx, 1);
                else S.filters.push(f);
                btn.classList.toggle('on', idx < 0);
                btn.setAttribute('aria-pressed', idx < 0 ? 'true' : 'false');
                applyFiltersAndSearch();
            };
        });
    }

    // 筛选 + 搜索一起作用在卡片上(看板按阶段分列,筛完各列只留命中的卡),列头计数随之
    // 改写——不改的话"等你审 7"配着两张可见卡,数字当场撒谎。
    function applyFiltersAndSearch() {
        var q = ($('searchInput').value || '').trim().toLowerCase();
        var cells = AI.boardTools.cellsByClient(S.matrix);
        var today = AI.boardTools.todayIsoBangkok();
        var visible = 0;
        document.querySelectorAll('#dashBody .kcard').forEach(function (el) {
            var name = el.getAttribute('data-name') || '';
            var id = el.getAttribute('data-client-id');
            var show =
                (!q || name.indexOf(q) >= 0) &&
                AI.boardTools.matchesFilters(cells[id] || [], S.filters, today);
            el.style.display = show ? '' : 'none';
            if (show) visible += 1;
        });
        updateColumnCounts();
        renderNoResults(visible);
    }

    function updateColumnCounts() {
        document.querySelectorAll('#dashBody .kcol').forEach(function (col) {
            var n = 0;
            col.querySelectorAll('.kcard').forEach(function (card) {
                if (card.style.display !== 'none') n += 1;
            });
            var badge = col.querySelector('h4 [data-role="col-count"]');
            if (badge) badge.textContent = String(n);
        });
    }

    // 命中 0 卡时看板只剩五个空列,像坏了(2026-07-17 实测):容器后补标准空态 + 清除
    // 按钮。清除三处一起清(筛选态、chip 高亮、搜索框)——只清数据态留着高亮 chip 就是
    // 状态撒谎(照矩阵 clearAllFilters 的先例)。
    function renderNoResults(visibleCount) {
        var body = $('dashBody');
        var existing = body.querySelector('.kb-noresults');
        if (visibleCount > 0 || !body.querySelector('.kanban')) {
            if (existing) existing.remove();
            return;
        }
        if (existing) return;
        var node = document.createElement('div');
        node.className = 'kb-noresults';
        node.innerHTML =
            AI.state.emptyHtml({ title: at('mx_no_results'), sub: at('mx_no_results_sub') }) +
            '<button type="button" class="btn sm" data-action="clear-filters">' +
            AI.state.esc(at('mx_clear_filters')) +
            '</button>';
        node.querySelector('[data-action="clear-filters"]').onclick = clearAllFilters;
        body.appendChild(node);
    }

    function clearAllFilters() {
        S.filters = [];
        $('boardTools')
            .querySelectorAll('.kb-chip')
            .forEach(function (btn) {
                btn.classList.remove('on');
                btn.setAttribute('aria-pressed', 'false');
            });
        $('searchInput').value = '';
        applyFiltersAndSearch();
    }

    // 批量开单条:选择态与执行在 ai-board-bulk.js,这里只递上下文(它每次重渲染后要
    // 重新对齐 DOM 上的勾选态)。没有矩阵响应就没有"本期缺单"卡,也就没有可批的对象。
    function mountBulk() {
        var bar = $('boardBulkBar');
        if (!S.matrix) {
            bar.style.display = 'none';
            return;
        }
        AI.boardBulk.mount({
            bar: bar,
            body: $('dashBody'),
            getApi: function () {
                return lastApi;
            },
            getPeriod: function () {
                return S.matrix.period;
            },
            onDone: function () {
                load(lastApi);
            },
        });
    }

    // 矩阵聚合端点失败(权限/网络/该期无数据)不算看板失败:整块看板照旧渲染,只是工具条
    // 收起、卡上不出「本期缺单」条——退化成搬迁前的看板,不给半真半假的筛选。
    function loadMatrix(api) {
        return api.getTaxProfileMatrix().catch(function () {
            return null;
        });
    }

    function load(api) {
        lastApi = api;
        AI.loadPendingStat(api);
        var body = $('dashBody');
        // 防闪烁(Canon §7):重载(开单后刷新/回到本视图)保留旧看板直到新数据到,
        // 骨架屏只在还没有任何看板时出——不给用户看「内容→骨架→内容」的跳变。
        if (!body.querySelector('.kanban')) body.innerHTML = AI.state.loadingHtml();
        return Promise.all([api.listClients(), api.listOrders({}), loadMatrix(api)])
            .then(function (r) {
                var clients = r[0].clients || [];
                var orders = r[1].orders || [];
                S.matrix = r[2];
                renderStats(clients, orders);
                var latest = latestOrderByClient(orders);
                var latestOrders = Object.keys(latest).map(function (k) {
                    return latest[k];
                });
                return loadDetailsForCards(api, latestOrders).then(function (detailsByOrderId) {
                    renderBoard(clients, latest, detailsByOrderId);
                    wireSearch();
                    wireFilters();
                    applyFiltersAndSearch();
                    mountBulk();
                });
            })
            .catch(function () {
                body.innerHTML = AI.state.errorHtml({
                    title: at('error_t'),
                    sub: at('error_s'),
                    retryLabel: at('retry'),
                });
                var btn = body.querySelector('[data-action="retry"]');
                if (btn)
                    btn.onclick = function () {
                        load(api);
                    };
            });
    }

    window.AI = window.AI || {};
    window.AI.dashboard = { load: load };
})();
