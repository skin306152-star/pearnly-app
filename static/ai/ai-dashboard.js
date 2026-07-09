/*
 * Pearnly AI · ai-dashboard.js · 选客户层(工作台首屏)渲染 + 数据编排
 *
 * 三张统计卡从两个真实只读端点现算(客户总数 / 待你处理单数 / AI 处理中单数)——
 * 不假装有 v4 演示的「异常项/缺票家数」,那需要 items 级数据(W2 才有)。
 * 简单卡片列表是 W1 占位(五列看板留给 W2 换皮,DOM 容器 #dashBody 不变)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    function esc(s) {
        return AI.state.esc(s);
    }

    function latestOrderByClient(orders) {
        var byClient = {};
        orders.forEach(function (o) {
            var cur = byClient[o.workspace_client_id];
            if (!cur || String(o.period) > String(cur.period)) byClient[o.workspace_client_id] = o;
        });
        return byClient;
    }

    function cardHtml(client, order) {
        var meta = order ? at('card_period', { p: esc(order.period) }) : at('card_no_order');
        var chip = '';
        if (order) {
            var sc = AI.format.statusChip(order.status);
            chip = '<span class="chip ' + sc.cls + '">' + esc(at(sc.key)) + '</span>';
        }
        return (
            '<div class="ccard" data-client-id="' +
            esc(client.id) +
            '" data-name="' +
            esc((client.name || '').toLowerCase()) +
            '"><div><div class="cname">' +
            esc(client.name) +
            '</div><div class="cmeta">' +
            esc(meta) +
            '</div></div><div class="cstat">' +
            chip +
            '<span class="cgo">›</span></div></div>'
        );
    }

    function renderStats(clients, orders) {
        $('statClientsV').textContent = String(clients.length);
        var pending = orders.filter(function (o) {
            return o.status === 'stuck';
        }).length;
        var running = orders.filter(function (o) {
            return o.status === 'running';
        }).length;
        $('statPendingV').textContent = String(pending);
        $('statRunningV').textContent = String(running);
    }

    function renderList(clients, orders) {
        var body = $('dashBody');
        if (!clients.length) {
            body.innerHTML = AI.state.emptyHtml({
                title: at('empty_clients_t'),
                sub: at('empty_clients_s'),
            });
            return;
        }
        var latest = latestOrderByClient(orders);
        var html =
            '<div class="clist">' +
            clients
                .map(function (c) {
                    return cardHtml(c, latest[c.id]);
                })
                .join('') +
            '</div>';
        body.innerHTML = html;
        body.querySelectorAll('.ccard').forEach(function (el) {
            el.addEventListener('click', function () {
                var id = el.getAttribute('data-client-id');
                window.location.hash = AI.router.buildClientHash(id, AI.router.DEFAULT_VIEW);
            });
        });
    }

    function wireSearch() {
        var input = $('searchInput');
        input.value = '';
        input.oninput = function () {
            var q = input.value.trim().toLowerCase();
            document.querySelectorAll('#dashBody .ccard').forEach(function (el) {
                var name = el.getAttribute('data-name') || '';
                el.style.display = !q || name.indexOf(q) >= 0 ? '' : 'none';
            });
        };
    }

    function load(api) {
        var body = $('dashBody');
        body.innerHTML = AI.state.loadingHtml();
        return Promise.all([api.listClients(), api.listOrders({})])
            .then(function (r) {
                var clients = r[0].clients || [];
                var orders = r[1].orders || [];
                renderStats(clients, orders);
                renderList(clients, orders);
                wireSearch();
            })
            .catch(function (e) {
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
    window.AI.dashboard = { load: load, cardHtml: cardHtml };
})();
