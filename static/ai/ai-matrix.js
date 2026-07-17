/*
 * Pearnly AI · ai-matrix.js · 事务所矩阵(工作台新默认视图)数据编排(C4)
 *
 * 单一聚合端点 GET /api/tax-profile/matrix?period= 一次喂全矩阵(客户 × 当期义务 ×
 * 关联工单状态),前端零 N+1(不为每格/每客户单独请求)。周期切换/筛选/搜索都是对
 * 同一份已拉到的响应做纯前端过滤——切期才重新打后端。
 *
 * 批量开单(唯一批量动作,主窗拍板:负责人筛选/批量催料/批量冻结不在本单范围):
 * 复用既有 POST /api/workorder/orders(幂等开单),对勾选的「缺单客户」逐个调用,
 * Promise.allSettled 收尾——失败的允许重新勾选重试(幂等,不会重复开单)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var S = {
        api: null,
        matrix: null, // 最近一次成功拉到的矩阵响应
        period: null, // 当前选中账期(佛历 YYYY-MM),null = 用后端缺省(当期)
        filters: [], // 激活的行筛选:missing/review/risk 的子集
        wired: false,
    };

    function esc(s) {
        return AI.state.esc(s);
    }

    function currentLang() {
        return (window.AII18N && window.AII18N.lang) || 'zh';
    }

    // 客户数/AI 处理中仍从矩阵响应现算;「待你处理」不再按「至少一格 pending_review 的
    // 客户数」推——该口径与 #/pool 实测同屏打架(2026-07-17:矩阵数出 0,pool 里却躺着
    // 1 张 stuck 单,用户不知道信谁),废除,改与 #/pool 同源(loadPendingStat)。
    function renderStats(matrix) {
        var running = {};
        (matrix.cells || []).forEach(function (c) {
            if (c.badge === 'in_progress') running[c.client_id] = true;
        });
        $('statClientsV').textContent = String((matrix.clients || []).length);
        $('statRunningV').textContent = String(Object.keys(running).length);
        $('sumPeriodV').textContent = matrix.period || '—';
        $('sumPeriod').style.display = '';
    }

    // 「待你处理」胶囊与 #/pool 同一数据源(review-queue),计数口径在
    // AI.board.pendingReviewCount。拉不到显 '—' 不臆造。
    function loadPendingStat(api) {
        api.getReviewQueue()
            .then(function (queue) {
                $('statPendingV').textContent = String(AI.board.pendingReviewCount(queue));
            })
            .catch(function () {
                $('statPendingV').textContent = '—';
            });
    }

    function periodOptionsHtml(selected) {
        return AI.board
            .periodOptions(14)
            .map(function (p) {
                return (
                    '<button data-p="' +
                    esc(p) +
                    '" class="' +
                    (p === selected ? 'on' : '') +
                    '">' +
                    esc(p) +
                    '</button>'
                );
            })
            .join('');
    }

    function renderPeriodPicker(matrix) {
        var btn = $('matrixPeriodValue');
        var menu = $('matrixPeriodMenu');
        btn.textContent = matrix.period;
        menu.innerHTML = periodOptionsHtml(matrix.period);
        menu.querySelectorAll('button').forEach(function (b) {
            b.onclick = function () {
                S.period = b.getAttribute('data-p');
                menu.classList.remove('on');
                load(S.api);
            };
        });
    }

    function selectedClientIds() {
        return Array.prototype.slice
            .call(document.querySelectorAll('#matrixBody .mx-check:checked'))
            .map(function (el) {
                return el.getAttribute('data-client-id');
            });
    }

    function updateBulkButton() {
        var n = selectedClientIds().length;
        var btn = $('matrixBulkOpenBtn');
        btn.textContent = at('matrix_bulk_open', { n: n });
        btn.disabled = n === 0;
    }

    function applyFiltersAndSearch() {
        if (!S.matrix) return;
        var q = ($('searchInput').value || '').trim().toLowerCase();
        AI.matrixRender.applyFilters($('matrixBody'), S.matrix, S.filters, q);
    }

    function wireFilters() {
        document.querySelectorAll('#matrixFilters .mf-chip').forEach(function (btn) {
            btn.onclick = function () {
                var f = btn.getAttribute('data-filter');
                var idx = S.filters.indexOf(f);
                if (idx >= 0) S.filters.splice(idx, 1);
                else S.filters.push(f);
                btn.classList.toggle('on', idx < 0);
                applyFiltersAndSearch();
            };
        });
    }

    function wireSearch() {
        var input = $('searchInput');
        input.value = '';
        input.oninput = applyFiltersAndSearch;
    }

    function wirePeriodToggle() {
        $('matrixPeriodBtn').onclick = function () {
            $('matrixPeriodMenu').classList.toggle('on');
        };
        // document 级"点外面关闭"监听器只挂一次(S.docWired 守门)——onclick 直接赋值
        // 覆盖天然幂等,但 addEventListener 每次 load() 都调用会无限叠加监听器。
        if (S.docWired) return;
        S.docWired = true;
        document.addEventListener('click', function (e) {
            if (
                !$('matrixPeriodBtn').contains(e.target) &&
                !$('matrixPeriodMenu').contains(e.target)
            ) {
                $('matrixPeriodMenu').classList.remove('on');
            }
        });
        // Esc 关下拉(§2 死路批):点外面能关,键盘也得能关。
        document.addEventListener('keydown', function (e) {
            var menu = $('matrixPeriodMenu');
            if (e.key === 'Escape' && menu.classList.contains('on')) menu.classList.remove('on');
        });
    }

    // 空态「清除筛选」:S.filters、筛选 chip 高亮、搜索框三处一起清——只清数据态留着
    // 高亮 chip 就是状态撒谎。
    function clearAllFilters() {
        S.filters = [];
        document.querySelectorAll('#matrixFilters .mf-chip').forEach(function (btn) {
            btn.classList.remove('on');
        });
        $('searchInput').value = '';
        applyFiltersAndSearch();
    }

    function runBulkOpen() {
        var ids = selectedClientIds();
        if (!ids.length || !S.matrix) return;
        var btn = $('matrixBulkOpenBtn');
        var period = S.matrix.period;
        btn.disabled = true;
        var idleLabel = btn.textContent;
        btn.textContent = at('matrix_bulk_open_busy');
        Promise.allSettled(
            ids.map(function (id) {
                return S.api.createOrder({
                    workspace_client_id: Number(id),
                    period: period,
                    intent: 'monthly_vat',
                });
            })
        ).then(function (results) {
            var ok = results.filter(function (r) {
                return r.status === 'fulfilled';
            }).length;
            var fail = results.length - ok;
            var msg = at('matrix_bulk_open_result_ok', { n: ok });
            if (fail > 0) msg += ' · ' + at('matrix_bulk_open_result_fail', { n: fail });
            var note = $('matrixBulkNote');
            if (note) note.textContent = msg;
            btn.textContent = idleLabel;
            load(S.api);
        });
    }

    function wireBulkOpen() {
        $('matrixBulkOpenBtn').onclick = runBulkOpen;
    }

    function renderTable(matrix) {
        var body = $('matrixBody');
        body.innerHTML = AI.matrixRender.tableHtml(matrix, currentLang());
        applyFiltersAndSearch();
        if (!S.wired) {
            AI.matrixRender.wireTable(
                body,
                function (clientId) {
                    // P0-2:矩阵切到哪期就带哪期进客户页(此前丢了 period,点 6 月格子却
                    // 打开最新一期工单——"矩阵→客户页"看着通了,实际每次都穿越)。
                    window.location.hash = AI.router.buildClientHash(
                        clientId,
                        AI.router.DEFAULT_VIEW,
                        S.matrix && S.matrix.period
                    );
                },
                updateBulkButton
            );
            body.addEventListener('click', function (e) {
                if (e.target.closest('[data-action="clear-filters"]')) clearAllFilters();
            });
            S.wired = true;
        }
        updateBulkButton();
    }

    function load(api) {
        S.api = api;
        loadPendingStat(api);
        var body = $('matrixBody');
        if (!body.querySelector('.mx-table')) body.innerHTML = AI.state.loadingHtml();
        return api
            .getTaxProfileMatrix(S.period)
            .then(function (matrix) {
                S.matrix = matrix;
                renderStats(matrix);
                renderPeriodPicker(matrix);
                renderTable(matrix);
                wireFilters();
                wireSearch();
                wirePeriodToggle();
                wireBulkOpen();
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
    window.AI.matrix = { load: load };
})();
