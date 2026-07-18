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

    // 账期候选列表(periodOptions 不随卡片变,算一次全板复用);<option> 串按卡片各自的
    // 默认选中期现拼(J-8:此前整板共用同一份「不选中任何项 → 原生首项当月」的字符串,
    // 卡片本身有工单落在别的账期时,选择器仍默认跳回当月,一点开单容易点错期——现在
    // 每张卡默认落该卡自己工单的账期,没有工单才回落当月)。
    function periodOptions() {
        return AI.board.periodOptions();
    }

    // 开单账期选择器 + 按钮(v4 未画过此场景,按 Canon tokens 延展)。default 有值时选中
    // 该项(J-8:卡片自己工单的账期),没有则原生 <select> 默认选首项=当月。
    function openOrderHtml(clientId, options, defaultPeriod) {
        var optsHtml = AI.state.optionsHtml(options, defaultPeriod || null, function (p) {
            return p;
        });
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

    function cardHtml(entry, options) {
        var hotClass = entry.column === 'review' ? ' hot' : '';
        var summaryVars = entry.summary.vars;
        if (
            entry.summary.key === 'card_needs_list' &&
            entry.detail &&
            Array.isArray(entry.detail.needs)
        ) {
            summaryVars = { list: AI.format.fieldList(entry.detail.needs) };
        }
        var summaryText = at(entry.summary.key, summaryVars);
        // 2026-07-17 Zihao 真机实测拍板(推翻 R2F-R3「常显」):本期已有工单的卡不再渲染
        // 账期下拉+开单——活工单卡上挂开单控件像在邀请再开一张,实测点出第二张单的困惑;
        // 补开历史月的入口是客户档案 → 工单历史(既有),不缺路。无本期工单的卡保留控件,
        // 开单默认当月(periodOptions 首项)。
        var openBtn = entry.order ? '' : openOrderHtml(entry.client.id, options, null);
        // tabindex=0:卡片 Tab 可达(Enter/空格触发同点击,见 wireBoard);
        // title:名称/摘要窄卡被省略号截断时悬停可看全文(Canon §6.2)。
        // P0-2:卡片携带的工单期(entry.order 是该客户最新一期,可能不是当月)——点卡
        // 进客户页要显式带上这一期,不依赖 ai-client.js mount() 的"缺省落最新"隐式默认。
        var cardPeriod = entry.order ? entry.order.period : '';
        return (
            '<div class="kcard' +
            hotClass +
            '" tabindex="0" data-client-id="' +
            esc(entry.client.id) +
            '" data-period="' +
            esc(cardPeriod) +
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

    function columnHtml(col, items, options) {
        var body = items.length
            ? items
                  .map(function (entry) {
                      return cardHtml(entry, options);
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
        var options = periodOptions();
        container.innerHTML =
            '<div class="kanban">' +
            AI.board.COLUMNS.map(function (col) {
                return columnHtml(col, groups[col.key] || [], options);
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
            var cardPeriod = card.getAttribute('data-period');
            window.location.hash = AI.router.buildClientHash(
                id,
                AI.router.DEFAULT_VIEW,
                cardPeriod
            );
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
