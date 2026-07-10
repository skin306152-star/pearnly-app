/*
 * Pearnly AI · ai-kanban-render.js · 五列看板的 HTML 拼装 + 事件绑定(M1-W2)
 *
 * 纯浏览器 IIFE(不进 node 单测——拼 HTML 字符串 + 挂 DOM 事件,无值得单独断言的
 * 逻辑分支;分列/摘要的真实逻辑在 ai-board.js 里已被单测覆盖)。依赖 window.AI.state/
 * format/board/router 与全局 at(),故必须排在 ai-board.js 之后、ai-dashboard.js 之前加载。
 */
(function () {
    'use strict';

    function esc(s) {
        return AI.state.esc(s);
    }

    // 胶囊拼装收在 AI.format.chipHtml——跟客户详情页工单头共用同一判定,不再各拼一遍
    // (此前这里硬编码"materials 列+stuck→缺料",绕开真实 detail.needs,能跟详情页文案对不上)。
    function chipFor(entry) {
        if (!entry.order) return '';
        return AI.format.chipHtml(entry.order.status, entry.detail);
    }

    // 账期 <option> 串:整块看板一次算好(periodOptions 不随卡片变),各开单卡复用同一串。
    function periodOptionsHtml() {
        return AI.board
            .periodOptions()
            .map(function (p) {
                return '<option value="' + esc(p) + '">' + esc(p) + '</option>';
            })
            .join('');
    }

    // 开单账期选择器 + 按钮(v4 未画过此场景,按 Canon tokens 延展)。当月排第一,原生
    // <select> 不设 selected 属性即默认选中首项——无需另外读写状态。
    function openOrderHtml(clientId, optsHtml) {
        return (
            '<div class="kopen">' +
            '<select class="period-sel" data-role="period-select" aria-label="' +
            esc(at('card_period_select_label')) +
            '">' +
            optsHtml +
            '</select>' +
            '<button class="btn sm" data-action="open-order" data-client-id="' +
            esc(clientId) +
            '">' +
            esc(at('card_open_order')) +
            '</button></div>'
        );
    }

    function cardHtml(entry, optsHtml) {
        var hotClass = entry.column === 'review' ? ' hot' : '';
        var summaryText = at(entry.summary.key, entry.summary.vars);
        var openBtn = entry.order ? '' : openOrderHtml(entry.client.id, optsHtml);
        // tabindex=0:卡片 Tab 可达(Enter/空格触发同点击,见 wireBoard);
        // title:名称/摘要窄卡被省略号截断时悬停可看全文(Canon §6.2)。
        return (
            '<div class="kcard' +
            hotClass +
            '" tabindex="0" data-client-id="' +
            esc(entry.client.id) +
            '" data-name="' +
            esc((entry.client.name || '').toLowerCase()) +
            '"><b title="' +
            esc(entry.client.name) +
            '">' +
            esc(entry.client.name) +
            '</b><small title="' +
            esc(summaryText) +
            '">' +
            esc(summaryText) +
            '</small>' +
            chipFor(entry) +
            openBtn +
            '</div>'
        );
    }

    function columnHtml(col, items, optsHtml) {
        var body = items.length
            ? items
                  .map(function (entry) {
                      return cardHtml(entry, optsHtml);
                  })
                  .join('')
            : '<div class="kempty">' + esc(at('col_empty')) + '</div>';
        return (
            '<div class="kcol"><h4><span class="dot ' +
            col.dot +
            '"></span>' +
            esc(at(col.titleKey)) +
            '<span class="n">' +
            items.length +
            '</span></h4>' +
            body +
            '</div>'
        );
    }

    // groups: { materials: [entry...], working: [...], review: [...], sign: [...], archived: [...] }
    // entry: { client, order, detail, column, unknownStatus, summary }
    function renderBoard(container, groups) {
        var optsHtml = periodOptionsHtml();
        container.innerHTML =
            '<div class="kanban">' +
            AI.board.COLUMNS.map(function (col) {
                return columnHtml(col, groups[col.key] || [], optsHtml);
            }).join('') +
            '</div>';
    }

    // 事件委托到看板容器,一次绑定覆盖全部卡片(重渲染后无需重新逐卡片绑定)。
    // onOpenOrder(clientId, period) 返回 Promise;resolve 后调 onReloaded() 刷新整个看板。
    function activate(e, onOpenOrder, onReloaded) {
        // 账期选择器点开/选值不算「点卡进客户页」——卡片整体可点导航,选择器是里面的
        // 独立控件,不能被外层点击语义吞掉。
        if (e.target.closest('[data-role="period-select"]')) {
            e.stopPropagation();
            return;
        }
        var openBtn = e.target.closest('[data-action="open-order"]');
        if (openBtn) {
            e.stopPropagation();
            if (openBtn.disabled) return;
            var clientId = openBtn.getAttribute('data-client-id');
            var periodSel = openBtn.closest('.kopen').querySelector('[data-role="period-select"]');
            var period = periodSel ? periodSel.value : undefined;
            var idleLabel = openBtn.textContent;
            // loading 态 + 禁双击(Canon §7):失败恢复原文案可重试,成功由整板刷新收尾。
            openBtn.disabled = true;
            openBtn.textContent = at('card_open_order_busy');
            onOpenOrder(clientId, period)
                .then(onReloaded)
                .catch(function () {
                    openBtn.disabled = false;
                    openBtn.textContent = idleLabel;
                });
            return;
        }
        var card = e.target.closest('.kcard');
        if (card) {
            var id = card.getAttribute('data-client-id');
            window.location.hash = AI.router.buildClientHash(id, AI.router.DEFAULT_VIEW);
        }
    }

    function wireBoard(container, onOpenOrder, onReloaded) {
        container.addEventListener('click', function (e) {
            activate(e, onOpenOrder, onReloaded);
        });
        // 键盘可达(Canon §7):聚焦卡片上 Enter/空格 = 点击。
        container.addEventListener('keydown', function (e) {
            if (e.key !== 'Enter' && e.key !== ' ') return;
            if (!e.target.closest || !e.target.closest('.kcard')) return;
            e.preventDefault();
            activate(e, onOpenOrder, onReloaded);
        });
    }

    window.AI = window.AI || {};
    window.AI.kanban = { renderBoard: renderBoard, wireBoard: wireBoard };
})();
