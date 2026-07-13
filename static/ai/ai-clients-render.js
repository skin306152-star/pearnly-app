/*
 * Pearnly AI · ai-clients-render.js · 客户目录(EN-clients)纯逻辑 + HTML 拼装
 *
 * 数据源与事务所矩阵(C4 · GET /api/tax-profile/matrix)同一份响应——客户目录是矩阵的
 * "改个视角"投影(按客户为主的表格,不是按义务为主的表格),不另起后端聚合查询
 * (勘察结论:矩阵响应已带 tax_id/profile_completeness,见 routes/tax_profile_routes.py)。
 *
 * 上半段(completenessPercent/completenessChipClass/matchesSearch/clientBadges)零 DOM/零
 * i18n 依赖,node(tests/unit/test_ai_clients_pure.py)直接 require 断言;下半段依赖
 * at()/AI.state/AI.matrixRender,只在浏览器根挂载——同 ai-matrix-render.js 的先例
 * (矩阵表格纯拼装无独立 node 测试,靠 E2E 覆盖;本文件把可测的那一半单独摘出来)。
 */
(function (root) {
    'use strict';

    // 0..1 → 0..100 整数(四舍五入,不截断——0.995 应显示 100% 不是 99%)。
    function completenessPercent(fraction) {
        return Math.round((Number(fraction) || 0) * 100);
    }

    // chip 色族(Canon §1):100% 已答=好,部分已答=待催,0%(全默认值未确认)=中性。
    function completenessChipClass(pct) {
        if (pct >= 100) return 'g';
        if (pct > 0) return 'w';
        return 'n';
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

    var pure = {
        completenessPercent: completenessPercent,
        completenessChipClass: completenessChipClass,
        matchesSearch: matchesSearch,
        clientBadges: clientBadges,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state/AI.matrixRender,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }

    // 义务徽章:复用矩阵的色族映射(AI.matrixRender.BADGE_CHIP)+ 文案(badgeLabel),
    // 目录行密度高,不逐格铺开——只列出非「未评估」的格子(未评估=从没物化过,列出来
    // 反而是噪音,矩阵页本身才是逐格核对的地方)。
    function badgesHtml(matrix, clientId) {
        var cells = clientBadges(matrix, clientId).filter(function (c) {
            return c.badge !== 'not_evaluated';
        });
        if (!cells.length) return '<span class="cl-badges-empty">—</span>';
        return (
            '<div class="cl-badges">' +
            cells
                .map(function (c) {
                    var cls = root.AI.matrixRender.BADGE_CHIP[c.badge] || 'n';
                    return (
                        '<span class="chip ' +
                        cls +
                        '" title="' +
                        esc(root.AI.matrixRender.badgeLabel(c.badge)) +
                        '">' +
                        esc(c.obligation_code.toUpperCase()) +
                        '</span>'
                    );
                })
                .join('') +
            '</div>'
        );
    }

    function rowHtml(client, matrix) {
        var pct = completenessPercent(client.profile_completeness);
        return (
            '<tr class="mx-row" data-client-id="' +
            esc(client.id) +
            '" data-name="' +
            esc((client.name || '').toLowerCase()) +
            '" data-tax-id="' +
            esc((client.tax_id || '').toLowerCase()) +
            '">' +
            '<td class="mx-namecell" data-action="open-client" data-client-id="' +
            esc(client.id) +
            '" tabindex="0" title="' +
            esc(client.name) +
            '">' +
            esc(client.name) +
            '</td>' +
            '<td class="mx-cell cl-taxid">' +
            esc(client.tax_id || '—') +
            '</td>' +
            '<td class="mx-cell">' +
            '<span class="chip ' +
            completenessChipClass(pct) +
            '">' +
            pct +
            '%</span></td>' +
            '<td class="mx-cell">' +
            badgesHtml(matrix, client.id) +
            '</td>' +
            '</tr>'
        );
    }

    // matrix:GET /api/tax-profile/matrix 原始响应(客户目录只读 clients/cells 两个键,
    // period/obligation_codes/obligation_labels 是矩阵自己的关切,这里不用)。
    function tableHtml(matrix) {
        var clients = (matrix && matrix.clients) || [];
        if (!clients.length) {
            return AI.state.emptyHtml({ title: at('clients_empty_t'), sub: at('clients_empty_s') });
        }
        var head =
            '<tr><th class="mx-namecell">' +
            esc(at('clients_col_name')) +
            '</th><th class="mx-colhead">' +
            esc(at('clients_col_tax_id')) +
            '</th><th class="mx-colhead">' +
            esc(at('clients_col_completeness')) +
            '</th><th class="mx-colhead">' +
            esc(at('clients_col_obligations')) +
            '</th></tr>';
        var body = clients
            .map(function (c) {
                return rowHtml(c, matrix);
            })
            .join('');
        return (
            '<div class="mx-scroll"><table class="mx-table">' +
            '<thead>' +
            head +
            '</thead><tbody>' +
            body +
            '</tbody></table></div>'
        );
    }

    // 复用同一份 matchesSearch(不是重抄一份子串匹配)——行的 data-name/data-tax-id
    // 已是小写(rowHtml 拼装时转过),这里传给 matchesSearch 的 client 影子对象原样带过去。
    function applySearch(container, query) {
        container.querySelectorAll('.mx-row').forEach(function (row) {
            var shadow = {
                name: row.getAttribute('data-name') || '',
                tax_id: row.getAttribute('data-tax-id') || '',
            };
            row.style.display = matchesSearch(shadow, query) ? '' : 'none';
        });
    }

    // 事件委托同矩阵先例(ai-matrix-render.js::wireTable):点客户名/整行进档案页。
    function wireTable(container, onOpenClient) {
        container.addEventListener('click', function (e) {
            var trigger = e.target.closest('[data-action="open-client"]');
            if (!trigger) return;
            onOpenClient(trigger.getAttribute('data-client-id'));
        });
        container.addEventListener('keydown', function (e) {
            if (e.key !== 'Enter' && e.key !== ' ') return;
            var cell = e.target.closest('.mx-namecell');
            if (!cell) return;
            e.preventDefault();
            onOpenClient(cell.getAttribute('data-client-id'));
        });
    }

    root.AI = root.AI || {};
    root.AI.clientsRender = {
        completenessPercent: completenessPercent,
        completenessChipClass: completenessChipClass,
        matchesSearch: matchesSearch,
        clientBadges: clientBadges,
        tableHtml: tableHtml,
        applySearch: applySearch,
        wireTable: wireTable,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
