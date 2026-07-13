/*
 * Pearnly AI · ai-clients.js · 客户目录(EN-clients · 侧栏「客户」转正)编排
 *
 * 顶层导航位(id=v-clients,同 /pool /vatcheck 先例)。数据源复用事务所矩阵聚合端点
 * GET /api/tax-profile/matrix(勘察结论:一次 JOIN 已带客户名/税号/画像完整度/当期
 * 义务格子,零新增后端查询),不为目录另起一份聚合接口。点客户名/整行 → 进单客户
 * 档案页(ai-client-archive.js,#/clients/<id>/<tab>)。
 *
 * 依赖 window.AI.state/api/clientsRender/matrixRender 与全局 at(),排在 ai-matrix.js
 * 之后、ai.js 之前加载(见 scripts/build-home-js.mjs)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var S = { api: null, matrix: null, wired: false };

    function body() {
        return $('clientsBody');
    }

    function renderTable() {
        body().innerHTML = AI.clientsRender.tableHtml(S.matrix);
        applySearch();
        if (!S.wired) {
            AI.clientsRender.wireTable(body(), function (clientId) {
                window.location.hash = AI.router.buildClientArchiveHash(
                    clientId,
                    AI.router.DEFAULT_ARCHIVE_TAB
                );
            });
            S.wired = true;
        }
    }

    function applySearch() {
        AI.clientsRender.applySearch(body(), $('clientsSearchInput').value);
    }

    function wireSearch() {
        var input = $('clientsSearchInput');
        input.value = '';
        input.oninput = applySearch;
    }

    function load(api) {
        S.api = api;
        if (!body().querySelector('.mx-table')) body().innerHTML = AI.state.loadingHtml();
        return api
            .getTaxProfileMatrix()
            .then(function (matrix) {
                S.matrix = matrix;
                renderTable();
                wireSearch();
            })
            .catch(function () {
                body().innerHTML = AI.state.errorHtml({
                    title: at('error_t'),
                    sub: at('error_s'),
                    retryLabel: at('retry'),
                });
                var btn = body().querySelector('[data-action="retry"]');
                if (btn)
                    btn.onclick = function () {
                        load(api);
                    };
            });
    }

    window.AI = window.AI || {};
    window.AI.clients = { load: load };
})();
