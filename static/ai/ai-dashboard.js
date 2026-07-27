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
        // 客户 id → 这张卡脸上那个状态胶囊的词条 key(与 ai-kanban-render.js 渲染出来的
        // 是同一个 AI.format.statusChip 结果)。状态类筛选拿它当准,不拿粗粒度徽章当准
        // ——点「待审」必须只留下写着「待审」的卡,见 AI.boardTools.matchesFilters。
        cardStateByClient: {},
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
        S.cardStateByClient = {};
        clients.forEach(function (c) {
            var order = latest[c.id] || null;
            var detail = order ? detailsByOrderId[order.id] : null;
            var mapped = AI.board.mapOrderToColumn(order, detail);
            // 没有工单的卡上没有状态胶囊(渲染层不给),不登记 → 筛选退回按矩阵格子判,
            // 免得"还没开单"的卡被「缺料」chip 一并捞进来。
            if (order) {
                S.cardStateByClient[String(c.id)] = AI.format.statusChip(order.status, detail).key;
            }
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
            // 空态给按钮,不用一句话描述「那个入口在哪儿」——原来的副文案正是那种写法。
            body.innerHTML = AI.state.emptyHtml({
                title: at('empty_clients_t'),
                actionLabel: at('clients_new_title'),
                actionHref: AI.router.buildClientsHash(),
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

    // chip 三处状态归零(数据态 + .on 高亮 + aria-pressed)。收起工具条与「清除筛选」
    // 共用这一份:只清数据态、留着亮起来的 chip,就是状态撒谎——而且后果不对称,用户
    // 看见亮着的 chip 会去点它想关掉,indexOf 是 -1 反而把筛选打开,卡片当场少一半。
    function resetChips() {
        S.filters = [];
        $('boardTools')
            .querySelectorAll('.kb-chip')
            .forEach(function (btn) {
                btn.classList.remove('on');
                btn.setAttribute('aria-pressed', 'false');
            });
    }

    // 三个筛选 chip(缺料/待审/风险)—— 判据在 ai-board-tools-render.js,状态类筛选按
    // 卡片脸上写的那个词判(S.cardStateByClient),不按粗粒度徽章判。
    // 拿不到矩阵响应时整条工具条收起:给个点不动的筛选比没有筛选更糟。
    function wireFilters() {
        var tools = $('boardTools');
        tools.style.display = S.matrix ? '' : 'none';
        if (!S.matrix) resetChips();
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
                AI.boardTools.matchesFilters(
                    cells[id] || [],
                    S.filters,
                    today,
                    S.cardStateByClient[id]
                );
            el.style.display = show ? '' : 'none';
            if (show) visible += 1;
        });
        updateColumnStates(!!q || S.filters.length > 0);
        renderNoResults(visible);
    }

    // 列头计数 + 列级空态一起改。空态必须跟着筛选走:天生为空的列写「这一步现在没有
    // 客户」,被筛空的列若不补一句,同屏就是"一半列有说明一半列只剩个数字"的坏相
    // (2026-07-17 空态规范:空了要说一句话,而且要说对是哪种空)。
    function updateColumnStates(filtering) {
        document.querySelectorAll('#dashBody .kcol').forEach(function (col) {
            var n = 0;
            col.querySelectorAll('.kcard').forEach(function (card) {
                if (card.style.display !== 'none') n += 1;
            });
            var badge = col.querySelector('h4 [data-role="col-count"]');
            if (badge) badge.textContent = String(n);
            var empty = col.querySelector('[data-role="col-empty"]');
            if (!empty) return;
            // 筛选态下不再逐列写一句「这一列没有符合筛选的客户」:列头的 0 计数徽章已经
            // 说了,五列一起印就是同一句话在一屏里重复五遍,而真正要说的「为什么全空、
            // 现在点哪」由容器级空态那一处说。天生为空的列照旧说明白它为什么空。
            empty.style.display = n || filtering ? 'none' : '';
            if (!n && !filtering) empty.textContent = at('col_empty');
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
            // 「换个筛选或清掉试试」删掉:清除按钮就在下一行,用文字描述按钮该怎么点是废话。
            AI.state.emptyHtml({ title: at('mx_no_results') }) +
            '<button type="button" class="btn sm" data-action="clear-filters">' +
            AI.state.esc(at('mx_clear_filters')) +
            '</button>';
        node.querySelector('[data-action="clear-filters"]').onclick = clearAllFilters;
        body.appendChild(node);
    }

    function clearAllFilters() {
        resetChips();
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
