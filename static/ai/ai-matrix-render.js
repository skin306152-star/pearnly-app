/*
 * Pearnly AI · ai-matrix-render.js · 事务所矩阵的 HTML 拼装 + 事件绑定(C4)
 *
 * 客户行 × 义务列格子;徽章颜色族按 UI-Canon-v4 §1(good=顺畅/完结,warn=缺料/催,
 * crit=等人判/卡点,sage=AI 在做),BADGE_CHIP 是矩阵格子徽章 → chip 类的唯一映射表,
 * 与后端 routes/tax_profile_routes.py::_matrix_badge 的 7 个徽章码一一对应(不在这里
 * 重新判定业务状态,后端已经算好 badge,本文件只管怎么画)。
 *
 * 纯浏览器 IIFE(不进 node 单测——拼 HTML 字符串 + 挂 DOM 事件,过滤/统计等值得单独
 * 断言的逻辑收在 ai-matrix.js 里)。依赖 window.AI.state/format/board/router 与全局
 * at(),故须排在 ai-board.js 之后、ai-matrix.js 之前加载(同 ai-kanban-render.js 先例)。
 */
(function () {
    'use strict';

    function esc(s) {
        return AI.state.esc(s);
    }

    // badge(后端码)→ chip 颜色类(Canon §1 四色族 + neutral)。
    var BADGE_CHIP = {
        no_need: 'g',
        pending_order: 'w',
        missing_materials: 'w',
        in_progress: 's',
        pending_review: 'b',
        frozen: 'g',
        not_evaluated: 'n',
    };

    // 供 ai-matrix.js 的行内筛选(缺料/待审/风险)复用同一份徽章枚举,不各自维护一份。
    var BADGE_MISSING = 'missing_materials';
    var BADGE_REVIEW = 'pending_review';

    function badgeLabel(badge) {
        var key = 'matrix_badge_' + badge;
        return at(key) === key ? badge : at(key);
    }

    function obligationLabel(code, labels, lang) {
        var l = labels && labels[code];
        if (!l) return code;
        return l[lang] || l.zh || code;
    }

    // 列头显官方表号短码(泰文 ภ.ง.ด.1/ภ.พ.30 · 其余语言拉丁码),全名挪 title 悬浮——
    // 五列窄格里全名必截断成同串不可辨。新义务码没补 obl_short_* 键时回落大写义务码,
    // 短码语义丢了但可辨性还在。
    function obligationShortLabel(code) {
        var key = 'obl_short_' + code;
        return at(key) === key ? String(code).toUpperCase() : at(key);
    }

    // 单元格是否「逾期风险」:仍未办结(非无需申报/已冻结)且截止日已过今天。
    // 截止日读顺延后的 due_efiling_deferred(MC2-B G3:周末/假日顺延),缺该字段
    // (老缓存/降级响应)回落原始 due_efiling——周六截止顺延到周一前不算逾期。
    function isOverdue(cell, todayIso) {
        if (!cell) return false;
        var due = cell.due_efiling_deferred || cell.due_efiling;
        if (!due) return false;
        if (cell.badge === 'no_need' || cell.badge === 'frozen') return false;
        return due < todayIso;
    }

    function cellHtml(cell, obligationCode, clientId) {
        if (!cell) {
            return (
                '<td class="mx-cell" data-code="' +
                esc(obligationCode) +
                '"><span class="chip n">' +
                esc(badgeLabel('not_evaluated')) +
                '</span></td>'
            );
        }
        var title = badgeLabel(cell.badge);
        if (cell.due_efiling) title += ' · ' + at('matrix_due_label', { date: cell.due_efiling });
        return (
            '<td class="mx-cell" data-code="' +
            esc(obligationCode) +
            '" data-badge="' +
            esc(cell.badge) +
            '" title="' +
            esc(title) +
            '">' +
            (cell.work_order_id
                ? '<button type="button" class="mx-cellbtn" data-action="open-cell" ' +
                  'data-client-id="' +
                  esc(clientId) +
                  '"><span class="chip ' +
                  (BADGE_CHIP[cell.badge] || 'n') +
                  '">' +
                  esc(badgeLabel(cell.badge)) +
                  '</span></button>'
                : '<span class="chip ' +
                  (BADGE_CHIP[cell.badge] || 'n') +
                  '">' +
                  esc(badgeLabel(cell.badge)) +
                  '</span>') +
            '</td>'
        );
    }

    // P1-5(矩阵新客户行「开首单」高亮):矩阵响应没有"这客户历史上开过几张单"这个字段,
    // 借 profile_completeness===0(建档后从没被人工碰过画像)当"大概率是刚建档的新客户"
    // 的代理判据——比"missing_order"单独判(只说明"本期没单",老客户漏开一期同样命中)
    // 更贴近"真新客户",不新起后端字段。
    function isLikelyNewClient(client) {
        return client.profile_completeness === 0 && !!client.missing_order;
    }

    function rowHtml(client, codes, cellByKey) {
        var rowCells = codes
            .map(function (code) {
                var cell = cellByKey[client.id + ':' + code];
                return cellHtml(cell, code, client.id);
            })
            .join('');
        var checkbox = client.missing_order
            ? '<input type="checkbox" class="mx-check" data-client-id="' +
              esc(client.id) +
              '" aria-label="' +
              esc(at('matrix_checkbox_aria', { name: client.name })) +
              '" />'
            : '';
        var newChip = isLikelyNewClient(client)
            ? '<span class="chip w" title="' +
              esc(at('matrix_new_client_hint')) +
              '">' +
              esc(at('matrix_new_client_chip')) +
              '</span> '
            : '';
        return (
            '<tr class="mx-row" data-client-id="' +
            esc(client.id) +
            '" data-name="' +
            esc((client.name || '').toLowerCase()) +
            '">' +
            '<td class="mx-check-cell">' +
            checkbox +
            '</td>' +
            '<td class="mx-namecell" data-action="open-client" data-client-id="' +
            esc(client.id) +
            '" tabindex="0" title="' +
            esc(client.name) +
            '">' +
            newChip +
            esc(client.name) +
            '</td>' +
            rowCells +
            '</tr>'
        );
    }

    // matrix: 后端 /api/tax-profile/matrix 的原始响应({period, clients, obligation_codes,
    // obligation_labels, cells})。lang: 当前语言,用于取 obligation_labels 的本地化列名。
    function tableHtml(matrix, lang) {
        var codes = matrix.obligation_codes || [];
        var clients = matrix.clients || [];
        if (!clients.length) {
            return AI.state.emptyHtml({ title: at('matrix_empty_t'), sub: at('matrix_empty_s') });
        }
        var cellByKey = {};
        (matrix.cells || []).forEach(function (c) {
            cellByKey[c.client_id + ':' + c.obligation_code] = c;
        });
        var head =
            '<tr><th class="mx-check-cell"></th><th class="mx-namecell">' +
            esc(at('matrix_col_client')) +
            '</th>' +
            codes
                .map(function (code) {
                    return (
                        '<th class="mx-colhead" title="' +
                        esc(obligationLabel(code, matrix.obligation_labels, lang)) +
                        '">' +
                        esc(obligationShortLabel(code)) +
                        '</th>'
                    );
                })
                .join('') +
            '</tr>';
        var body = clients
            .map(function (c) {
                return rowHtml(c, codes, cellByKey);
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

    // 行级筛选(缺料/待审/风险):无激活筛选时全部可见;有则该行只要有一格命中任一
    // 激活筛选就保留整行(矩阵的用途是「这个客户本期有没有事」,不是逐格隐藏)。
    function rowMatchesFilters(matrix, clientId, activeFilters, todayIso) {
        if (!activeFilters.length) return true;
        var rowCells = (matrix.cells || []).filter(function (c) {
            return String(c.client_id) === String(clientId);
        });
        return rowCells.some(function (c) {
            return activeFilters.some(function (f) {
                if (f === 'missing') return c.badge === BADGE_MISSING;
                if (f === 'review') return c.badge === BADGE_REVIEW;
                if (f === 'risk') return isOverdue(c, todayIso);
                return false;
            });
        });
    }

    function applyFilters(container, matrix, activeFilters, searchQuery) {
        var todayIso = new Date().toISOString().slice(0, 10);
        container.querySelectorAll('.mx-row').forEach(function (row) {
            var clientId = row.getAttribute('data-client-id');
            var name = row.getAttribute('data-name') || '';
            var matchesSearch = !searchQuery || name.indexOf(searchQuery) >= 0;
            var matchesFilter = rowMatchesFilters(matrix, clientId, activeFilters, todayIso);
            row.style.display = matchesSearch && matchesFilter ? '' : 'none';
        });
    }

    // 事件委托:点客户名/整行导航进客户页;点格子里的按钮(有工单的格子)同样导航
    // (进客户页比在矩阵里深挖单张义务更符合"矩阵是总览,细节在客户页"的分工);
    // checkbox 变化交调用方(ai-matrix.js)算勾选合计,这里只负责不让它冒泡触发导航。
    function wireTable(container, onOpenClient, onCheckChange) {
        container.addEventListener('click', function (e) {
            if (e.target.closest('.mx-check')) return;
            var trigger = e.target.closest('[data-action="open-client"],[data-action="open-cell"]');
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
        container.addEventListener('change', function (e) {
            if (e.target.classList.contains('mx-check')) onCheckChange();
        });
    }

    window.AI = window.AI || {};
    window.AI.matrixRender = {
        tableHtml: tableHtml,
        applyFilters: applyFilters,
        wireTable: wireTable,
        badgeLabel: badgeLabel,
        // 客户目录(ai-clients-render.js)复用同一份徽章 → chip 色族映射,不重抄一份。
        BADGE_CHIP: BADGE_CHIP,
    };
})();
