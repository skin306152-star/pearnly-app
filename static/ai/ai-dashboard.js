/*
 * Pearnly AI · ai-dashboard.js · 选客户层(工作台首屏)渲染 + 数据编排
 *
 * 三张统计卡从两个真实只读端点现算(客户总数 / 待你处理单数 / AI 处理中单数)。
 * 五列看板(M1-W2):list 端点只给 status,没有逐条 needs/blocked_reasons/numbers——
 * 只对「每客户最新一期」里 status=stuck(缺料/挂起判定)或 review(读 tax_due)的订单
 * 额外拉 detail,不对全量历史订单做 N+1;数量上界 = 看板会显示的卡片数。
 * HTML 拼装/事件委托在 ai-kanban-render.js,分列/摘要纯函数在 ai-board.js。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var lastApi = null;
    var boardWired = false;

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
    // (loadPendingStat,口径在 AI.board.pendingReviewCount)。
    function renderStats(clients, orders) {
        $('statClientsV').textContent = String(clients.length);
        var running = orders.filter(function (o) {
            return o.status === 'running';
        }).length;
        $('statRunningV').textContent = String(running);
        // 看板统计跨期现算(每客户最新一期),没有单一账期可言——账期 pill 只归矩阵。
        $('sumPeriod').style.display = 'none';
    }

    function loadPendingStat(api) {
        api.getReviewQueue()
            .then(function (queue) {
                $('statPendingV').textContent = String(AI.board.pendingReviewCount(queue));
            })
            .catch(function () {
                $('statPendingV').textContent = '—'; // 拉不到不臆造
            });
    }

    // 只对「每客户最新一期」里 status=stuck(区分缺料/挂起)或 review(读 tax_due)的那些
    // 订单批量拉 detail——数量上界 = 看板会显示的卡片数,不对全量历史订单做 N+1。单条失败
    // (权限/网络)不拖垮全表:该条退化为"没有 detail"走 mapOrderToColumn/summarizeCard
    // 的保守降级分支,不中断其它卡片渲染。
    function loadDetailsForCards(api, latestOrders) {
        // collecting 也拉 detail(2026-07-17 S4):此前 collecting 卡 detail=null,摘要
        // 永远只报账期——「等待中不知等什么」实测根因;detail.needs 接通后卡片能点名缺什么。
        var needDetail = latestOrders.filter(function (o) {
            return o.status === 'stuck' || o.status === 'review' || o.status === 'collecting';
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
        input.oninput = function () {
            var q = input.value.trim().toLowerCase();
            var visible = 0;
            document.querySelectorAll('#dashBody .kcard').forEach(function (el) {
                var name = el.getAttribute('data-name') || '';
                var show = !q || name.indexOf(q) >= 0;
                el.style.display = show ? '' : 'none';
                if (show) visible += 1;
            });
            renderSearchEmpty(visible);
        };
    }

    // 搜索命中 0 卡时看板只剩五个空列,像坏了(2026-07-17 实测,同矩阵空表头):看板
    // 容器后补标准空态 + 清除按钮(看板没有筛选 chip,这里的「清除」只清搜索框)。
    function renderSearchEmpty(visibleCount) {
        var body = $('dashBody');
        var existing = body.querySelector('.mx-noresults');
        if (visibleCount > 0 || !body.querySelector('.kanban')) {
            if (existing) existing.remove();
            return;
        }
        if (existing) return;
        var node = document.createElement('div');
        node.className = 'mx-noresults';
        node.innerHTML =
            AI.state.emptyHtml({ title: at('mx_no_results'), sub: at('mx_no_results_sub') }) +
            '<button type="button" class="btn sm" data-action="clear-filters">' +
            AI.state.esc(at('mx_clear_filters')) +
            '</button>';
        node.querySelector('[data-action="clear-filters"]').onclick = function () {
            var input = $('searchInput');
            input.value = '';
            if (input.oninput) input.oninput();
        };
        body.appendChild(node);
    }

    function load(api) {
        lastApi = api;
        loadPendingStat(api);
        var body = $('dashBody');
        // 防闪烁(Canon §7):重载(开单后刷新/回到本视图)保留旧看板直到新数据到,
        // 骨架屏只在还没有任何看板时出——不给用户看「内容→骨架→内容」的跳变。
        if (!body.querySelector('.kanban')) body.innerHTML = AI.state.loadingHtml();
        return Promise.all([api.listClients(), api.listOrders({})])
            .then(function (r) {
                var clients = r[0].clients || [];
                var orders = r[1].orders || [];
                renderStats(clients, orders);
                var latest = latestOrderByClient(orders);
                var latestOrders = Object.keys(latest).map(function (k) {
                    return latest[k];
                });
                return loadDetailsForCards(api, latestOrders).then(function (detailsByOrderId) {
                    renderBoard(clients, latest, detailsByOrderId);
                    wireSearch();
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
