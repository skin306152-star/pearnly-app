/*
 * Pearnly AI · ai-clients-render.js · 客户目录(EN-clients)纯逻辑 + HTML 拼装
 *
 * 数据源与事务所矩阵(C4 · GET /api/tax-profile/matrix)同一份响应——客户目录是矩阵的
 * "改个视角"投影(按客户为主的表格,不是按义务为主的表格),不另起后端聚合查询
 * (勘察结论:矩阵响应已带 tax_id/profile_completeness,见 routes/tax_profile_routes.py)。
 *
 * 上半段(completenessPercent/matchesSearch/clientBadges/obligationsCount)零 DOM/零
 * i18n 依赖,node(tests/unit/test_ai_clients_pure.py)直接 require 断言;下半段依赖
 * at()/AI.state,只在浏览器根挂载——同 ai-matrix-render.js 的先例(纯拼装无独立
 * node 测试,靠 E2E 覆盖;本文件把可测的那一半单独摘出来)。
 */
(function (root) {
    'use strict';

    // 0..1 → 0..100 整数(四舍五入,不截断——0.995 应显示 100% 不是 99%)。
    function completenessPercent(fraction) {
        return Math.round((Number(fraction) || 0) * 100);
    }

    // 目录搜索:客户名/税号任一命中即算(税号常是会计记的比名字准的检索键)。
    function matchesSearch(client, query) {
        var q = String(query || '')
            .trim()
            .toLowerCase();
        if (!q) return true;
        var name = String((client && client.name) || '').toLowerCase();
        var taxId = String((client && client.tax_id) || '').toLowerCase();
        return name.indexOf(q) >= 0 || taxId.indexOf(q) >= 0;
    }

    // 该客户在矩阵里的全部义务格子(过滤 cells,不新建第二份聚合——矩阵已经算好)。
    function clientBadges(matrix, clientId) {
        var cells = (matrix && matrix.cells) || [];
        return cells.filter(function (c) {
            return String(c.client_id) === String(clientId);
        });
    }

    // 当期义务收成一枚计数标签(v5 §六:目录行不再平铺逐义务徽章)——只数已物化的
    // 格子,未评估=从没物化过,逐格核对是矩阵页的分工。
    function obligationsCount(matrix, clientId) {
        return clientBadges(matrix, clientId).filter(function (c) {
            return c.badge !== 'not_evaluated';
        }).length;
    }

    var pure = {
        completenessPercent: completenessPercent,
        matchesSearch: matchesSearch,
        clientBadges: clientBadges,
        obligationsCount: obligationsCount,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state/AI.matrixRender,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }

    // 目录行(v5 §六 行内分层):客户名最大/税号次之/完成度小环+百分比/义务计数标签/
    // 行尾箭头。整行可点(data-action 挂行根)。
    function rowHtml(client, matrix) {
        var pct = completenessPercent(client.profile_completeness);
        var n = obligationsCount(matrix, client.id);
        var oblHtml = n
            ? '<span class="chip n cl-obl">' +
              esc(at('clients_obligations_n', { n: n })) +
              '</span>'
            : '<span class="cl-obl-empty">—</span>';
        return (
            '<div class="cl-row" data-action="open-client" tabindex="0" data-client-id="' +
            esc(client.id) +
            '" data-name="' +
            esc((client.name || '').toLowerCase()) +
            '" data-tax-id="' +
            esc((client.tax_id || '').toLowerCase()) +
            '">' +
            '<div class="cl-main">' +
            '<span class="cl-name" title="' +
            esc(client.name) +
            '">' +
            esc(client.name) +
            '</span>' +
            '<span class="cl-taxid">' +
            esc(client.tax_id || '—') +
            '</span>' +
            '</div>' +
            '<span class="cl-prog num" style="--p: ' +
            pct +
            '"><i class="cl-ring"></i>' +
            pct +
            '%</span>' +
            oblHtml +
            '<svg class="cl-arrow" viewBox="0 0 24 24" fill="none" stroke-width="2">' +
            '<path d="m9 18 6-6-6-6" /></svg>' +
            '</div>'
        );
    }

    // matrix:GET /api/tax-profile/matrix 原始响应(客户目录只读 clients/cells 两个键,
    // period/obligation_codes/obligation_labels 是矩阵自己的关切,这里不用)。
    function listHtml(matrix) {
        var clients = (matrix && matrix.clients) || [];
        if (!clients.length) {
            return AI.state.emptyHtml({ title: at('clients_empty_t'), sub: at('clients_empty_s') });
        }
        return (
            '<div class="cl-list">' +
            clients
                .map(function (c) {
                    return rowHtml(c, matrix);
                })
                .join('') +
            '</div>'
        );
    }

    // 复用同一份 matchesSearch(不是重抄一份子串匹配)——行的 data-name/data-tax-id
    // 已是小写(rowHtml 拼装时转过),这里传给 matchesSearch 的 client 影子对象原样带过去。
    function applySearch(container, query) {
        container.querySelectorAll('.cl-row').forEach(function (row) {
            var shadow = {
                name: row.getAttribute('data-name') || '',
                tax_id: row.getAttribute('data-tax-id') || '',
            };
            row.style.display = matchesSearch(shadow, query) ? '' : 'none';
        });
    }

    // 事件委托同矩阵先例(ai-matrix-render.js::wireTable):点整行进档案页,Enter/空格同。
    function wireList(container, onOpenClient) {
        container.addEventListener('click', function (e) {
            var trigger = e.target.closest('[data-action="open-client"]');
            if (!trigger) return;
            onOpenClient(trigger.getAttribute('data-client-id'));
        });
        container.addEventListener('keydown', function (e) {
            if (e.key !== 'Enter' && e.key !== ' ') return;
            var row = e.target.closest('.cl-row');
            if (!row) return;
            e.preventDefault();
            onOpenClient(row.getAttribute('data-client-id'));
        });
    }

    root.AI = root.AI || {};
    root.AI.clientsRender = {
        completenessPercent: completenessPercent,
        matchesSearch: matchesSearch,
        clientBadges: clientBadges,
        obligationsCount: obligationsCount,
        listHtml: listHtml,
        applySearch: applySearch,
        wireList: wireList,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
