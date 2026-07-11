/*
 * Pearnly AI · ai-financials.js · 月度报表包(G1b)区块编排:折叠开关挂载
 *
 * 挂在工单详情(wo 视图)影子底稿区之下,数据源是 ai-client.js renderWo() 已取到的
 * order_detail().financials(不再发第二次网络请求)。只读区,唯一交互是五个分区的
 * 折叠开关——同 ai-shadow.js 的折叠机制。
 */
(function () {
    'use strict';

    var S = null;

    function freshState(financials) {
        return {
            financials: financials,
            // 五分区默认展开——报表包是会计要核对的主内容,账龄/折旧的「未接入」占位
            // 也要一进页面就可见(不能靠点击才发现降级状态),同 ai-shadow.js 的取舍。
            open: { bs: true, pl: true, tb: true, aging: true, depreciation: true },
        };
    }

    function render(container) {
        if (!S) return;
        container.innerHTML = AI.financialsRender.pageHtml(S.financials, S);
    }

    function toggleFold(kind, container) {
        if (!(kind in S.open)) return;
        S.open[kind] = !S.open[kind];
        render(container);
    }

    function onClick(e, container) {
        var el = e.target.closest('[data-action="fin-fold"]');
        if (!el) return;
        toggleFold(el.getAttribute('data-kind'), container);
    }

    // container 由调用方(ai-client.js renderWo)传入,financials 是已取到的 order_detail
    // 字段——同一次 getOrder() 复用,不重复发请求。
    function mount(financials, container) {
        S = freshState(financials);
        container.onclick = function (e) {
            onClick(e, container);
        };
        render(container);
    }

    window.AI = window.AI || {};
    window.AI.financials = { mount: mount };
})();
